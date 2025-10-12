"""
Tests for LLM adapter
"""

import pytest
from unittest.mock import patch, MagicMock
from llm.adapter import LLMAdapter


def test_llm_adapter_initialization():
    """Test LLMAdapter initialization with default values"""
    adapter = LLMAdapter(
        base_url="https://lm.leophir.com",
        model="openai/gpt-oss-20b"
    )

    assert adapter.base_url == "https://lm.leophir.com/v1"
    assert adapter.model == "openai/gpt-oss-20b"
    assert adapter.temperature == 0.2
    assert adapter.api_key == "not-needed"


def test_llm_adapter_auto_append_v1():
    """Test that /v1 is automatically appended to base URL"""
    # Without /v1
    adapter1 = LLMAdapter(base_url="https://lm.leophir.com")
    assert adapter1.base_url == "https://lm.leophir.com/v1"

    # With /v1 already present
    adapter2 = LLMAdapter(base_url="https://lm.leophir.com/v1")
    assert adapter2.base_url == "https://lm.leophir.com/v1"

    # With trailing slash
    adapter3 = LLMAdapter(base_url="https://lm.leophir.com/")
    assert adapter3.base_url == "https://lm.leophir.com/v1"


def test_llm_adapter_no_base_url():
    """Test adapter behavior when no base URL is provided"""
    adapter = LLMAdapter()
    response = adapter.chat([{"role": "user", "content": "test"}])

    assert "Error" in response or "No LLM base URL configured" in response


def test_llm_adapter_from_config(sample_config):
    """Test creating adapter from config dict"""
    adapter = LLMAdapter.from_config(sample_config)

    assert adapter.base_url == "https://lm.leophir.com/v1"
    assert adapter.model == "openai/gpt-oss-20b"
    assert adapter.temperature == 0.2
    assert adapter.max_tokens == 2048


def test_llm_adapter_from_model_config(sample_model_config):
    """Test creating adapter from model-specific config"""
    adapter = LLMAdapter.from_model_config(sample_model_config)

    assert adapter.base_url == "https://lm.leophir.com/v1"
    assert adapter.model == "openai/gpt-oss-20b"
    assert adapter.temperature == 0.2


@patch('llm.adapter.OpenAI')
def test_llm_adapter_chat(mock_openai_class, mock_llm_response):
    """Test chat method with mocked OpenAI client"""
    # Setup mock
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    mock_message.content = mock_llm_response
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    # Test
    adapter = LLMAdapter(base_url="https://lm.leophir.com")
    messages = [{"role": "user", "content": "Hello"}]
    response = adapter.chat(messages)

    assert response == mock_llm_response
    mock_openai_class.assert_called_once()
    mock_client.chat.completions.create.assert_called_once()


@patch('llm.adapter.OpenAI')
def test_llm_adapter_chat_with_system(mock_openai_class, mock_llm_response):
    """Test chat_with_system convenience method"""
    # Setup mock
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    mock_message.content = mock_llm_response
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    # Test
    adapter = LLMAdapter(base_url="https://lm.leophir.com")
    response = adapter.chat_with_system(
        user_message="Hello",
        system_message="You are a helpful assistant"
    )

    assert response == mock_llm_response

    # Check that both system and user messages were sent
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs['messages']
    assert len(messages) == 2
    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'user'


@patch('llm.adapter.OpenAI')
def test_llm_adapter_temperature_override(mock_openai_class, mock_llm_response):
    """Test temperature override in chat call"""
    # Setup mock
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    mock_message.content = mock_llm_response
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    # Test
    adapter = LLMAdapter(base_url="https://lm.leophir.com", temperature=0.2)
    messages = [{"role": "user", "content": "Hello"}]
    adapter.chat(messages, temperature=0.8)

    # Check that temperature was overridden
    call_args = mock_client.chat.completions.create.call_args
    assert call_args.kwargs['temperature'] == 0.8


@patch('llm.adapter.OpenAI')
def test_llm_adapter_max_tokens_handling(mock_openai_class, mock_llm_response):
    """Test max_tokens parameter handling"""
    # Setup mock
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    mock_message.content = mock_llm_response
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    # Test with max_tokens set
    adapter = LLMAdapter(base_url="https://lm.leophir.com", max_tokens=1024)
    messages = [{"role": "user", "content": "Hello"}]
    adapter.chat(messages)

    call_args = mock_client.chat.completions.create.call_args
    assert 'max_tokens' in call_args.kwargs
    assert call_args.kwargs['max_tokens'] == 1024


@patch('llm.adapter.OpenAI')
def test_llm_adapter_error_handling(mock_openai_class):
    """Test error handling in chat method"""
    # Setup mock to raise exception
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    mock_openai_class.return_value = mock_client

    # Test - should handle exception gracefully after retries
    adapter = LLMAdapter(base_url="https://lm.leophir.com")
    messages = [{"role": "user", "content": "Hello"}]
    response = adapter.chat(messages)

    assert "Error" in response
    assert "API Error" in response


def test_llm_adapter_model_prefixes():
    """Test that model prefixes are handled correctly"""
    # Test various model naming formats
    models = [
        "openai/gpt-oss-20b",
        "qwen/qwen3-4b-2507",
        "mistral",
        "llama3"
    ]

    for model in models:
        adapter = LLMAdapter(base_url="https://lm.leophir.com", model=model)
        assert adapter.model == model
