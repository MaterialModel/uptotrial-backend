"""OpenAI Responses API client for LLM integration."""

import logging
from typing import Any, Literal

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from app.api.errors import LLMError
from app.core.config import Settings

logger = logging.getLogger(__name__)


class MessageContent(BaseModel):
    """Pydantic model for OpenAI API message content."""
    
    content: str
    role: str
    tool_calls: list[dict[str, Any]] | None = None
    function_call: dict[str, str] | None = None


class UsageInfo(BaseModel):
    """Pydantic model for token usage information."""
    
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


class ResponseModel(BaseModel):
    """Pydantic model for LLM API response data."""
    
    message: MessageContent
    conversation_id: str
    usage: UsageInfo | None = None


class ClinicalTrialSearchResults(BaseModel):
    """Pydantic model for clinical trial search results."""
    
    results: str | dict[str, Any]
    conversation_id: str


class ResponsesClient:
    """Client for interacting with OpenAI Responses API."""
    
    def __init__(self, settings: Settings) -> None:
        """Initialize the Responses API client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def create_response(
        self,
        input_text: str,
        conversation_id: str | None = None,
        message_id: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        images: list[str] | None = None,
    ) -> ResponseModel:
        """Create a response using the OpenAI Responses API.
        
        The Responses API provides a stateful conversation experience with native
        support for tools and multimodal interactions.
        
        Args:
            input_text: User input text
            conversation_id: Optional ID of an existing conversation
            message_id: Optional ID of a specific message to fork from
            model: Model to use (defaults to settings)
            temperature: Controls creativity (0.0-1.0)
            tools: Optional tools to make available
            max_tokens: Maximum tokens to generate
            images: Optional list of image URLs or base64 encoded images
            
        Returns:
            ResponseModel: Response data including message content,
                           conversation ID, and tool outputs
            
        Raises:
            LLMError: If an error occurs during API call
        """
        try:
            # Prepare API request parameters
            params: dict[str, Any] = {
                "model": model or self.model,
                "input": input_text,
                "temperature": temperature,
            }
            
            logger.debug("Creating response with model: %s, temperature: %s", 
                         params["model"], temperature)
            
            # Add optional parameters
            if conversation_id:
                params["conversation_id"] = conversation_id
                logger.debug("Using existing conversation ID: %s", conversation_id)
                
            if message_id:
                params["message_id"] = message_id
                
            if max_tokens:
                params["max_tokens"] = max_tokens
                
            if tools:
                params["tools"] = tools
                
            if images:
                # Convert images to the format expected by the API
                formatted_images = []
                for img in images:
                    formatted_images.append({"type": "image_url", "image_url": img})
                params["input"] = formatted_images
            
            # Call the Responses API
            logger.debug("Calling OpenAI Responses API")
            response = await self.client.responses.create(**params)
            
            # Log the response received
            logger.debug("Response received with conversation ID: %s", response.conversation_id)
            
            # Convert usage data if present
            usage_data = None
            if hasattr(response, "usage"):
                usage_dict = response.usage.dict() if hasattr(response, "usage") else None
                if usage_dict:
                    usage_data = UsageInfo(**usage_dict)
                    logger.debug("Token usage: %s", usage_dict)
            
            # Create a message content model
            message_data = MessageContent(
                content=response.message.content,
                role=response.message.role,
                tool_calls=response.message.tool_calls,
                function_call=response.message.function_call,
            )
            
            # Return a Pydantic model instead of a dictionary
            return ResponseModel(
                message=message_data,
                conversation_id=response.conversation_id,
                usage=usage_data,
            )
            
        except OpenAIError as e:
            logger.error("OpenAI API error: %s", str(e))
            raise LLMError(f"Error from OpenAI Responses API: {e!s}") from e
        except Exception as e:
            logger.error("Unexpected error in LLM client: %s", str(e))
            raise LLMError(f"Unexpected error: {e!s}") from e
    
    async def search_clinical_trials(
        self,
        query: str,
        conversation_id: str | None = None,
        format_type: Literal["json", "text"] = "json",
    ) -> ClinicalTrialSearchResults:
        """Search for clinical trials using natural language.
        
        This method combines the capabilities of the Responses API with specialized
        tools for clinical trial search.
        
        Args:
            query: Natural language query about clinical trials
            conversation_id: Optional conversation ID for context
            format_type: Response format (json or text)
            
        Returns:
            ClinicalTrialSearchResults: Structured search results
            
        Raises:
            LLMError: If an error occurs during search
        """
        tools = [
            {
                "type": "web_search",  
                # In a real implementation, we would use a custom clinical trials
                # search tool instead of web_search
            },
        ]
        
        # Setup response format for structured data
        response_format = None
        if format_type == "json":
            response_format = {"type": "json_object"}
        
        try:
            logger.info("Searching clinical trials with query: %s", query)
            
            # We can't use system_message directly with the API
            # Instead, we need to use messages parameter or make it part of the input
            search_prompt = (
                "You are a clinical trials search assistant. "
                "Search for relevant clinical trials based on the following query: " + query
            )
            
            params: dict[str, Any] = {
                "model": self.model,
                "input": search_prompt,
                "temperature": 0.3,  # Lower temperature for more factual responses
                "tools": tools,
            }
            
            logger.debug("Using model: %s with temperature: 0.3", self.model)
            
            if conversation_id:
                params["conversation_id"] = conversation_id
                
            if response_format:
                params["response_format"] = response_format
            
            # Call the Responses API
            logger.debug("Calling OpenAI Responses API for clinical trials search")
            response = await self.client.responses.create(**params)
            
            logger.info("Clinical trials search completed successfully")
            logger.debug("Response received with conversation ID: %s", response.conversation_id)
            
            # Return a Pydantic model instead of a dictionary
            return ClinicalTrialSearchResults(
                results=response.message.content,
                conversation_id=response.conversation_id,
            )
            
        except OpenAIError as e:
            logger.error("OpenAI API error during clinical trials search: %s", str(e))
            raise LLMError(f"Error searching clinical trials: {e!s}") from e
        except Exception as e:
            logger.error("Unexpected error during clinical trials search: %s", str(e))
            raise LLMError(f"Unexpected error during search: {e!s}") from e