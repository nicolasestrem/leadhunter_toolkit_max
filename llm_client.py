from typing import List, Optional
from openai import OpenAI
from retry_utils import retry_with_backoff
from logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    OpenAI-compatible LLM client with support for local models (LM Studio, Ollama, etc.)

    Optimized for:
    - Qwen models (qwen/qwen3-4b-2507, etc.)
    - GPT-OSS-20B and other local models
    - OpenAI API
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize LLM client

        Args:
            api_key: API key (default "not-needed" for local LLMs)
            base_url: Base URL for API endpoint (auto-appends /v1 if needed)
            model: Model name/ID
            temperature: Sampling temperature (0.0-2.0, default 0.2)
            max_tokens: Maximum tokens in response (None = unlimited)
        """
        self.api_key = api_key or "not-needed"  # Default for local LLMs like LM Studio

        # Ensure base_url ends with /v1 for OpenAI compatibility
        if base_url:
            base_url = base_url.rstrip('/')
            if not base_url.endswith('/v1'):
                base_url = f"{base_url}/v1"
        self.base_url = base_url or None
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @retry_with_backoff(max_retries=2, initial_delay=2.0, exceptions=(Exception,))
    def summarize_leads(self, leads: List[dict], instruction: str = "Summarize the top opportunities in 10 bullets.") -> str:
        """
        Summarize leads or process custom instructions via LLM.

        Args:
            leads: List of lead dictionaries (can be empty for custom instructions)
            instruction: Custom instruction or prompt for the LLM

        Returns:
            LLM response as string
        """
        if not self.base_url:
            logger.warning("No LLM base URL configured")
            return "No LLM base URL configured. Please set it in Settings."

        try:
            logger.debug(f"Calling LLM with model: {self.model}, temp: {self.temperature}")
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            # If leads provided, format them; otherwise use instruction as-is
            if leads:
                logger.debug(f"Summarizing {len(leads)} leads")
                text = "\n".join([f"- {l.get('name') or l.get('domain')} | {', '.join(l.get('emails', [])[:2])} | {l.get('city') or ''}" for l in leads[:50]])
                prompt = f"{instruction}\n\nLeads:\n{text}"
            else:
                logger.debug("Processing custom instruction (no leads)")
                prompt = instruction

            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature
            }

            # Add max_tokens if specified (important for local models)
            if self.max_tokens:
                request_params["max_tokens"] = self.max_tokens

            logger.info(f"Calling LLM endpoint: {self.base_url}")
            resp = client.chat.completions.create(**request_params)

            if resp and resp.choices and len(resp.choices) > 0:
                response_text = resp.choices[0].message.content
                if response_text:
                    logger.info(f"LLM response received ({len(response_text)} chars)")
                    return response_text
                else:
                    logger.warning("LLM returned empty content")
                    return "No response from LLM."

            logger.warning("LLM returned no choices")
            return "Empty response from LLM."

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return f"Error calling LLM: {str(e)}"
