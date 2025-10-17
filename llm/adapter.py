"""
Unified LLM adapter for OpenAI-compatible endpoints
Supports LM Studio, Ollama, and OpenAI with consistent interface
Includes vision/multimodal support for image analysis
"""

import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from openai import OpenAI, AsyncOpenAI
from retry_utils import retry_with_backoff, async_retry_with_backoff
from logger import get_logger

logger = get_logger(__name__)


def mask_api_key(api_key: str) -> str:
    """Mask an API key for safe logging.

    This function takes an API key and returns a masked version, showing only the first
    and last four characters. This is crucial for preventing sensitive credentials
    from being exposed in logs.

    Args:
        api_key (str): The API key to mask.

    Returns:
        str: The masked API key.
    """
    if not api_key or api_key == "not-needed":
        return "not-needed"

    if len(api_key) <= 8:
        return "***"

    return f"{api_key[:4]}...{api_key[-4:]}"


class LLMAdapter:
    """A unified adapter for OpenAI-compatible LLM endpoints.

    This class provides a consistent interface for interacting with various LLM providers,
    including LM Studio, Ollama, and the official OpenAI API. It standardizes the
    process of sending chat completion requests and is designed to be easily configurable.

    Supported Endpoints:
        - LM Studio (e.g., 'https://lm.leophir.com/')
        - Ollama (e.g., 'http://oll.leophir.com/')
        - OpenAI API
        - Any other OpenAI-compatible endpoint
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-oss-20b",
        temperature: float = 0.2,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = 2048,
        timeout: int = 60,
        supports_system_role: Optional[bool] = None,
    ):
        """Initializes the LLM adapter.

        Args:
            base_url (Optional[str]): The base URL for the API endpoint. It auto-appends '/v1'
                                      if not present for OpenAI compatibility.
            api_key (Optional[str]): The API key. Defaults to the 'LLM_API_KEY' environment
                                     variable, then 'not-needed'.
            model (str): The name or ID of the model to use.
            temperature (float): The sampling temperature, between 0.0 and 2.0.
            top_k (Optional[int]): The Top-K sampling parameter.
            top_p (Optional[float]): The nucleus sampling parameter.
            max_tokens (Optional[int]): The maximum number of tokens in the response.
            timeout (int): The request timeout in seconds.
            supports_system_role (Optional[bool]): Specifies if the endpoint supports the
                                                   "system" role. If None, it defaults to
                                                   False for Mistral models and True otherwise.
        """
        # API key fallback chain: param -> env var -> default
        self.api_key = api_key or os.environ.get('LLM_API_KEY', "not-needed")

        # Validate API key is not exposed in plain text
        if self.api_key and self.api_key != "not-needed":
            if len(self.api_key) < 8:
                logger.warning("API key appears to be too short (< 8 chars). May be invalid.")

        # Ensure base_url ends with /v1 for OpenAI compatibility
        if base_url:
            base_url = base_url.rstrip('/')
            if not base_url.endswith('/v1'):
                base_url = f"{base_url}/v1"

        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Most OpenAI-compatible endpoints support the system role. Some (e.g. certain
        # Mistral templates) only accept user/assistant roles, so allow opting out.
        if supports_system_role is None:
            supports_system_role = "mistral" not in (model or "").lower()
        self.supports_system_role = supports_system_role

        # Log configuration with masked API key
        logger.debug(
            f"Initialized LLMAdapter: endpoint={base_url}, model={model}, "
            f"api_key={mask_api_key(self.api_key)}, temp={temperature}, "
            f"top_k={top_k}, top_p={top_p}, max_tokens={max_tokens}"
        )

    @retry_with_backoff(max_retries=2, initial_delay=2.0, exceptions=(Exception,))
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Send a chat completion request to the LLM.

        This method handles the synchronous communication with the LLM endpoint. It includes
        a retry mechanism with exponential backoff to handle transient network issues.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries, each with 'role' and 'content'.
            temperature (Optional[float]): A specific temperature to override the default.
            max_tokens (Optional[int]): A specific max_tokens value to override the default.
            **kwargs: Additional parameters to be passed to the API.

        Returns:
            str: The content of the response from the LLM as a string.
        """
        if not self.base_url:
            logger.error("No LLM base URL configured")
            return "Error: No LLM base URL configured. Please set it in settings."

        try:
            logger.debug(f"Sending chat request with {len(messages)} messages")

            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )

            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
                **kwargs
            }

            # Add max_tokens if specified
            max_tok = max_tokens if max_tokens is not None else self.max_tokens
            if max_tok and max_tok > 0:
                request_params["max_tokens"] = max_tok

            # Add top_p if specified (nucleus sampling - OpenAI API standard)
            if self.top_p is not None:
                request_params["top_p"] = self.top_p

            # Note: top_k is NOT part of OpenAI API standard and not supported by LM Studio's OpenAI-compatible endpoint
            # Configure top_k directly in LM Studio's model settings instead

            logger.info(f"Calling LLM: {self.base_url} with model {self.model}")
            response = client.chat.completions.create(**request_params)

            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    logger.info(f"LLM response received ({len(content)} chars)")
                    return content
                else:
                    logger.warning("LLM returned empty content")
                    return ""

            logger.warning("LLM returned no choices")
            return ""

        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            return f"Error calling LLM: {str(e)}"

    def chat_with_system(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """A simplified method for chats that include an optional system message.

        This is a convenience wrapper around the 'chat' method. It automatically handles
        the formatting of system messages, even for models that do not natively support
        the 'system' role.

        Args:
            user_message (str): The user's message or prompt.
            system_message (Optional[str]): An optional system message to provide context.
            **kwargs: Additional parameters to be passed to the 'chat' method.

        Returns:
            str: The content of the response from the LLM.
        """
        if system_message and not self.supports_system_role:
            combined_message = f"{system_message}\n\n{user_message}"
            messages = [{"role": "user", "content": combined_message}]
        else:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": user_message})

        return self.chat(messages, **kwargs)

    @async_retry_with_backoff(max_retries=2, initial_delay=2.0, exceptions=(Exception,))
    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """The asynchronous version of the 'chat' method.

        This method is designed for use in asynchronous applications. It performs the same
        functionality as 'chat' but in a non-blocking manner.

        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries.
            temperature (Optional[float]): A specific temperature to override the default.
            max_tokens (Optional[int]): A specific max_tokens value to override the default.
            **kwargs: Additional parameters to be passed to the API.

        Returns:
            str: The content of the response from the LLM.
        """
        if not self.base_url:
            logger.error("No LLM base URL configured")
            return "Error: No LLM base URL configured."

        try:
            logger.debug(f"Sending async chat request with {len(messages)} messages")

            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )

            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.temperature,
                **kwargs
            }

            max_tok = max_tokens if max_tokens is not None else self.max_tokens
            if max_tok and max_tok > 0:
                request_params["max_tokens"] = max_tok

            # Add top_p if specified (nucleus sampling - OpenAI API standard)
            if self.top_p is not None:
                request_params["top_p"] = self.top_p

            # Note: top_k is NOT part of OpenAI API standard and not supported by LM Studio's OpenAI-compatible endpoint
            # Configure top_k directly in LM Studio's model settings instead

            logger.info(f"Calling LLM async: {self.base_url}")
            response = await client.chat.completions.create(**request_params)

            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    logger.info(f"Async LLM response received ({len(content)} chars)")
                    return content
                else:
                    logger.warning("Async LLM returned empty content")
                    return ""

            logger.warning("Async LLM returned no choices")
            return ""

        except Exception as e:
            logger.error(f"Error calling async LLM: {e}", exc_info=True)
            return f"Error calling LLM: {str(e)}"

    async def chat_with_system_async(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """The asynchronous version of the 'chat_with_system' method.

        This method provides a non-blocking way to interact with the LLM when a system
        message is needed, making it suitable for asynchronous applications.

        Args:
            user_message (str): The user's message or prompt.
            system_message (Optional[str]): An optional system message.
            **kwargs: Additional parameters for the 'chat_async' method.

        Returns:
            str: The content of the response from the LLM.
        """
        if system_message and not self.supports_system_role:
            combined_message = f"{system_message}\n\n{user_message}"
            messages = [{"role": "user", "content": combined_message}]
        else:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": user_message})

        return await self.chat_async(messages, **kwargs)

    @classmethod
    def from_config(cls, config: Dict[str, Any], model_override: Optional[str] = None) -> 'LLMAdapter':
        """Create an LLMAdapter instance from a configuration dictionary.

        This class method is a factory that simplifies the creation of an adapter by
        using a pre-structured configuration dictionary, typically loaded from a file.

        Args:
            config (Dict[str, Any]): A configuration dictionary.
            model_override (Optional[str]): An optional model name to override the one in the config.

        Returns:
            LLMAdapter: A configured instance of the LLMAdapter.
        """
        llm_config = config.get('llm', {})

        return cls(
            base_url=llm_config.get('base_url'),
            api_key=llm_config.get('api_key'),
            model=model_override or llm_config.get('model', 'openai/gpt-oss-20b'),
            temperature=llm_config.get('temperature', 0.2),
            top_k=llm_config.get('top_k'),
            top_p=llm_config.get('top_p'),
            max_tokens=llm_config.get('max_tokens', 2048),
            timeout=llm_config.get('timeout', 60),
            supports_system_role=llm_config.get('supports_system_role')
        )

    @classmethod
    def from_model_config(cls, model_config: Dict[str, Any]) -> 'LLMAdapter':
        """Create an LLMAdapter instance from a model-specific configuration.

        This factory method is tailored for creating an adapter from a configuration
        that is specific to a single model, often sourced from 'models.yml'.

        Args:
            model_config (Dict[str, Any]): A model-specific configuration dictionary.

        Returns:
            LLMAdapter: A configured instance of the LLMAdapter.
        """
        return cls(
            base_url=model_config.get('endpoint'),
            model=model_config.get('id'),
            temperature=model_config.get('temperature', 0.2),
            top_k=model_config.get('top_k'),
            top_p=model_config.get('top_p'),
            max_tokens=model_config.get('max_tokens', 2048),
            supports_system_role=model_config.get('supports_system_role')
        )

    def chat_with_image(
        self,
        prompt: str,
        image_data: Union[str, Path],
        detail: str = "auto",
        **kwargs
    ) -> str:
        """Send a chat completion request with an image to a vision-capable model.

        This method allows for multimodal interactions by sending an image along with a
        text prompt. It can accept either a file path to an image or a base64-encoded string.

        Args:
            prompt (str): The text prompt or question about the image.
            image_data (Union[str, Path]): A base64-encoded image string or a path to the image file.
            detail (str): The level of detail for the image ('low', 'high', 'auto').
            **kwargs: Additional parameters for the 'chat' method.

        Returns:
            str: The content of the response from the LLM.
        """
        try:
            # If image_data is a path, encode it
            if isinstance(image_data, (str, Path)) and Path(image_data).exists():
                from multimodal.image_utils import encode_image_to_base64
                logger.debug(f"Encoding image from path: {image_data}")
                image_base64 = encode_image_to_base64(image_data, format='JPEG', max_size=(2048, 2048))
                image_url = f"data:image/jpeg;base64,{image_base64}"
            else:
                # Assume it's already base64
                if not image_data.startswith('data:'):
                    image_url = f"data:image/jpeg;base64,{image_data}"
                else:
                    image_url = image_data

            # Build vision message
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": detail
                            }
                        }
                    ]
                }
            ]

            logger.info(f"Sending vision request with image ({len(image_url)} chars)")
            return self.chat(messages, **kwargs)

        except Exception as e:
            logger.error(f"Error in vision chat: {e}", exc_info=True)
            return f"Error analyzing image: {str(e)}"

    def chat_with_images(
        self,
        prompt: str,
        images: List[Union[str, Path]],
        detail: str = "auto",
        **kwargs
    ) -> str:
        """Send a chat completion request with multiple images.

        This method extends the vision capabilities to handle multiple images in a single
        request, which is useful for comparison or context-rich queries.

        Args:
            prompt (str): The text prompt or question about the images.
            images (List[Union[str, Path]]): A list of base64-encoded images or file paths.
            detail (str): The level of detail for the images.
            **kwargs: Additional parameters for the 'chat' method.

        Returns:
            str: The content of the response from the LLM.
        """
        try:
            # Build content array with text and all images
            content = [{"type": "text", "text": prompt}]

            for i, image_data in enumerate(images):
                # Encode image if it's a path
                if isinstance(image_data, (str, Path)) and Path(image_data).exists():
                    from multimodal.image_utils import encode_image_to_base64
                    logger.debug(f"Encoding image {i+1} from path: {image_data}")
                    image_base64 = encode_image_to_base64(image_data, format='JPEG', max_size=(2048, 2048))
                    image_url = f"data:image/jpeg;base64,{image_base64}"
                else:
                    if not image_data.startswith('data:'):
                        image_url = f"data:image/jpeg;base64,{image_data}"
                    else:
                        image_url = image_data

                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                        "detail": detail
                    }
                })

            messages = [{"role": "user", "content": content}]

            logger.info(f"Sending vision request with {len(images)} images")
            return self.chat(messages, **kwargs)

        except Exception as e:
            logger.error(f"Error in multi-image vision chat: {e}", exc_info=True)
            return f"Error analyzing images: {str(e)}"

    async def chat_with_image_async(
        self,
        prompt: str,
        image_data: Union[str, Path],
        detail: str = "auto",
        **kwargs
    ) -> str:
        """The asynchronous version of the 'chat_with_image' method.

        This method provides a non-blocking way to send an image and a text prompt to a
        vision-capable model.

        Args:
            prompt (str): The text prompt about the image.
            image_data (Union[str, Path]): A base64-encoded string or a path to the image.
            detail (str): The level of detail for the image.
            **kwargs: Additional parameters for the 'chat_async' method.

        Returns:
            str: The content of the response from the LLM.
        """
        try:
            # Prepare image URL
            if isinstance(image_data, (str, Path)) and Path(image_data).exists():
                from multimodal.image_utils import encode_image_to_base64
                image_base64 = encode_image_to_base64(image_data, format='JPEG', max_size=(2048, 2048))
                image_url = f"data:image/jpeg;base64,{image_base64}"
            else:
                if not image_data.startswith('data:'):
                    image_url = f"data:image/jpeg;base64,{image_data}"
                else:
                    image_url = image_data

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": detail
                            }
                        }
                    ]
                }
            ]

            logger.info(f"Sending async vision request")
            return await self.chat_async(messages, **kwargs)

        except Exception as e:
            logger.error(f"Error in async vision chat: {e}", exc_info=True)
            return f"Error analyzing image: {str(e)}"

    def analyze_screenshot(
        self,
        url: str,
        analysis_prompt: Optional[str] = None,
        capture_full_page: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Capture and analyze a screenshot of a website.

        This high-level method automates the process of taking a screenshot of a given URL
        and then sending it to a vision model for analysis.

        Args:
            url (str): The URL of the website to analyze.
            analysis_prompt (Optional[str]): An optional custom prompt for the analysis.
            capture_full_page (bool): If True, captures the entire page.
            **kwargs: Additional parameters for the 'chat' method.

        Returns:
            Dict[str, Any]: A dictionary containing the screenshot path, analysis, and URL.
        """
        try:
            from multimodal.image_utils import capture_screenshot
            import tempfile

            # Default analysis prompt
            if not analysis_prompt:
                analysis_prompt = """Analyze this website screenshot and provide:
1. Overall design quality and professionalism
2. Key visual elements and branding
3. User experience observations
4. Mobile responsiveness indicators
5. Call-to-action visibility
6. Any technical or design issues spotted"""

            # Capture screenshot to temp file
            logger.info(f"Capturing screenshot of {url}")
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                screenshot_path = tmp.name

            capture_screenshot(url, output_path=screenshot_path, full_page=capture_full_page)

            # Analyze with vision
            logger.info("Analyzing screenshot with vision model")
            analysis = self.chat_with_image(
                prompt=f"{analysis_prompt}\n\nWebsite: {url}",
                image_data=screenshot_path,
                **kwargs
            )

            return {
                'url': url,
                'screenshot_path': screenshot_path,
                'analysis': analysis,
                'full_page': capture_full_page
            }

        except Exception as e:
            logger.error(f"Error analyzing screenshot: {e}", exc_info=True)
            return {
                'url': url,
                'error': str(e),
                'analysis': f"Error capturing/analyzing screenshot: {str(e)}"
            }
