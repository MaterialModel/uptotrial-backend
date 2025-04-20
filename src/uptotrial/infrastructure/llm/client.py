"""OpenAI Responses API client for LLM integration."""

from typing import Any, Literal

from openai import AsyncOpenAI, OpenAIError

from uptotrial.api.errors import LLMError
from uptotrial.core.config import Settings


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
    ) -> dict[str, Any]:
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
            dict[str, Any]: Response data including message content,
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
            
            # Add optional parameters
            if conversation_id:
                params["conversation_id"] = conversation_id
                
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
            response = await self.client.responses.create(**params)
            
            # Format the response
            return {
                "message": response.message,
                "conversation_id": response.conversation_id,
                "usage": response.usage.dict() if hasattr(response, "usage") else None,
            }
            
        except OpenAIError as e:
            raise LLMError(f"Error from OpenAI Responses API: {str(e)}")
        except Exception as e:
            raise LLMError(f"Unexpected error: {str(e)}")
    
    async def search_clinical_trials(
        self,
        query: str,
        conversation_id: str | None = None,
        format_type: Literal["json", "text"] = "json",
    ) -> dict[str, Any]:
        """Search for clinical trials using natural language.
        
        This method combines the capabilities of the Responses API with specialized
        tools for clinical trial search.
        
        Args:
            query: Natural language query about clinical trials
            conversation_id: Optional conversation ID for context
            format_type: Response format (json or text)
            
        Returns:
            dict[str, Any]: Structured search results
            
        Raises:
            LLMError: If an error occurs during search
        """
        tools = [
            {
                "type": "web_search",  
                # In a real implementation, we would use a custom clinical trials
                # search tool instead of web_search
            }
        ]
        
        # Setup response format for structured data
        response_format = None
        if format_type == "json":
            response_format = {"type": "json_object"}
        
        try:
            system_message = (
                "You are a clinical trials search assistant. "
                "Search for relevant clinical trials based on the user's query. "
                "Focus on providing accurate information about trial eligibility, "
                "locations, and contact information."
            )
            
            params: dict[str, Any] = {
                "model": self.model,
                "input": query,
                "temperature": 0.3,  # Lower temperature for more factual responses
                "tools": tools,
                "system_message": system_message,
            }
            
            if conversation_id:
                params["conversation_id"] = conversation_id
                
            if response_format:
                params["response_format"] = response_format
            
            # Call the Responses API
            response = await self.client.responses.create(**params)
            
            return {
                "results": response.message.content,
                "conversation_id": response.conversation_id,
            }
            
        except OpenAIError as e:
            raise LLMError(f"Error searching clinical trials: {str(e)}")
        except Exception as e:
            raise LLMError(f"Unexpected error during search: {str(e)}")