"""Tests for the Responses API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.uptotrial.api.errors import LLMError
from src.uptotrial.core.config import Settings
from src.uptotrial.infrastructure.llm.client import ResponsesClient


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    settings = Settings(
        openai_api_key="test_key",
        openai_model="gpt-4o-mini",
    )
    return settings


@pytest.fixture
def mock_response() -> MagicMock:
    """Create a mock response from the OpenAI API."""
    response = MagicMock()
    response.message.content = "This is a test response"
    response.conversation_id = "test_conversation_id"
    response.usage.dict.return_value = {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
    }
    return response


@pytest.mark.asyncio
async def test_create_response_success(mock_settings: Settings, mock_response: MagicMock) -> None:
    """Test successful response creation."""
    with patch("openai.AsyncOpenAI") as mock_openai:
        # Setup the mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses.create = AsyncMock(return_value=mock_response)
        
        # Create the client and call the method
        client = ResponsesClient(mock_settings)
        result = await client.create_response("Test input")
        
        # Assert results
        assert result["message"] == mock_response.message
        assert result["conversation_id"] == "test_conversation_id"
        assert "usage" in result
        
        # Verify API was called with correct parameters
        mock_client.responses.create.assert_called_once()
        call_args = mock_client.responses.create.call_args[1]
        assert call_args["model"] == "gpt-4o-mini"
        assert call_args["input"] == "Test input"


@pytest.mark.asyncio
async def test_create_response_error(mock_settings: Settings) -> None:
    """Test error handling in response creation."""
    with patch("openai.AsyncOpenAI") as mock_openai:
        # Setup the mock to raise an exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses.create = AsyncMock(side_effect=Exception("API error"))
        
        # Create the client
        client = ResponsesClient(mock_settings)
        
        # Call the method and expect an exception
        with pytest.raises(LLMError) as exc_info:
            await client.create_response("Test input")
        
        # Verify error message
        assert "error" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_search_clinical_trials(mock_settings: Settings, mock_response: MagicMock) -> None:
    """Test clinical trials search functionality."""
    with patch("openai.AsyncOpenAI") as mock_openai:
        # Setup the mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses.create = AsyncMock(return_value=mock_response)
        
        # Create the client and call the method
        client = ResponsesClient(mock_settings)
        result = await client.search_clinical_trials("Find cancer trials")
        
        # Assert results
        assert result["results"] == "This is a test response"
        assert result["conversation_id"] == "test_conversation_id"
        
        # Verify API call included tools and appropriate settings
        mock_client.responses.create.assert_called_once()
        call_args = mock_client.responses.create.call_args[1]
        assert "tools" in call_args
        assert call_args["temperature"] < 0.7  # Lower temperature for factual responses