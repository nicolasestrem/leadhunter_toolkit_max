"""
Pytest configuration and fixtures for Lead Hunter Toolkit tests
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return "This is a mock LLM response for testing purposes."


@pytest.fixture
def mock_openai_client(mock_llm_response):
    """Mock OpenAI client for testing without live API calls"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()

    # Setup mock chain
    mock_message.content = mock_llm_response
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response

    return mock_client


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for testing"""
    return {
        'llm': {
            'base_url': 'https://lm.leophir.com/',
            'api_key': 'test-key',
            'model': 'openai/gpt-oss-20b',
            'temperature': 0.2,
            'max_tokens': 2048,
            'timeout': 60
        },
        'locale': {
            'language': 'en',
            'country': 'de',
            'city': 'Berlin'
        },
        'search': {
            'engine': 'google',
            'max_sites': 10,
            'max_pages': 3
        },
        'scoring': {
            'email_weight': 2.0,
            'phone_weight': 1.0,
            'social_weight': 0.5
        }
    }


@pytest.fixture
def sample_model_config() -> Dict[str, Any]:
    """Sample model configuration for testing"""
    return {
        'id': 'openai/gpt-oss-20b',
        'endpoint': 'https://lm.leophir.com/',
        'temperature': 0.2,
        'max_tokens': 2048,
        'description': 'Test model'
    }


@pytest.fixture
def sample_lead() -> Dict[str, Any]:
    """Sample lead data for testing"""
    return {
        'name': 'Test Restaurant GmbH',
        'domain': 'test-restaurant.de',
        'website': 'https://test-restaurant.de',
        'emails': ['info@test-restaurant.de', 'reservations@test-restaurant.de'],
        'phones': ['+49 30 12345678'],
        'social': {
            'facebook': 'https://facebook.com/testrestaurant',
            'instagram': 'https://instagram.com/testrestaurant'
        },
        'city': 'Berlin',
        'country': 'de',
        'tags': ['restaurant', 'german-cuisine'],
        'score': 7.5,
        'notes': 'High quality lead with complete contact info'
    }


@pytest.fixture
def sample_markdown_content() -> str:
    """Sample markdown content for testing extraction"""
    return """
# Test Restaurant Berlin

Welcome to Test Restaurant, your finest dining experience in Berlin.

## Contact Us

- **Email**: info@test-restaurant.de
- **Phone**: +49 30 12345678
- **Address**: Musterstraße 123, 10115 Berlin

### Follow Us

Connect with us on social media:
- Facebook: https://facebook.com/testrestaurant
- Instagram: @testrestaurant
- Twitter: https://twitter.com/testrestaurant

---

For reservations, call us or email reservations@test-restaurant.de
"""


@pytest.fixture
def sample_html_content() -> str:
    """Sample HTML content for testing extraction"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Test Restaurant - Berlin's Best Dining</title>
    <meta name="description" content="Experience fine dining at Test Restaurant">
</head>
<body>
    <h1>Test Restaurant</h1>
    <p>Contact: <a href="mailto:info@test-restaurant.de">info@test-restaurant.de</a></p>
    <p>Phone: <a href="tel:+493012345678">+49 30 12345678</a></p>
    <div class="social">
        <a href="https://facebook.com/testrestaurant">Facebook</a>
        <a href="https://instagram.com/testrestaurant">Instagram</a>
    </div>
</body>
</html>
"""


def pytest_addoption(parser):
    parser.addoption(
        "--run-playwright",
        action="store_true",
        default=False,
        help="run tests marked with 'playwright'",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "playwright: mark tests that require Playwright and a Chromium install",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-playwright"):
        return

    skip_marker = pytest.mark.skip(reason="use --run-playwright to execute Playwright tests")
    for item in items:
        if "playwright" in item.keywords:
            item.add_marker(skip_marker)
