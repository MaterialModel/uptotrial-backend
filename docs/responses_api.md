# OpenAI Responses API Integration

## Overview

The UpToTrial application uses OpenAI's Responses API to handle natural language search for clinical trials. The Responses API provides enhanced capabilities compared to the standard Completions API, including stateful conversations, built-in tool support, and multimodal capabilities.

## Key Features

### Stateful Conversations

The Responses API automatically maintains conversation state, allowing for contextual interactions without manually managing conversation history:

- Each API call returns a `conversation_id` that can be used in subsequent calls
- Messages can be forked from specific points using the `message_id` parameter
- The API maintains full conversation history, enabling more natural and context-aware interactions

### Tool Integration

The API supports tools that can be called by the model during a conversation:

- Native support for `web_search` which we use for gathering current information
- Custom tools can be implemented for specialized functionality
- The model automatically decides which tool to use based on the context

### Multimodal Support

The API handles multiple types of input and output:

- Text inputs and outputs for standard interactions
- Image analysis for reviewing medical images or diagrams
- Combined workflows like analyzing an image and then searching for related information

## Implementation in UpToTrial

### ResponsesClient Class

The `ResponsesClient` class in `app/infrastructure/llm/client.py` provides a clean interface to the Responses API:

```python
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
    # Implementation...
```

The client handles request preparation, error management, and response formatting, making it easy to use the Responses API throughout the application.

### Clinical Trials Search

The client provides a specialized method for clinical trials search that configures the Responses API for this use case:

```python
async def search_clinical_trials(
    self,
    query: str,
    conversation_id: str | None = None,
    format_type: Literal["json", "text"] = "json",
) -> dict[str, Any]:
    # Implementation...
```

This method:
- Configures appropriate tools for the search
- Sets a lower temperature for more factual responses
- Provides a clinical trials-specific system message
- Offers structured JSON output for programmatic use

## Usage Examples

### Basic Query

```python
client = ResponsesClient(settings)
result = await client.search_clinical_trials(
    "Find phase 3 breast cancer trials in New York"
)
```

### Continuing a Conversation

```python
# Initial query
result = await client.search_clinical_trials(
    "Find phase 3 breast cancer trials in New York"
)
conversation_id = result["conversation_id"]

# Follow-up question using the same conversation context
follow_up = await client.search_clinical_trials(
    "Which ones are recruiting?",
    conversation_id=conversation_id
)
```

## Configuration

The Responses API client is configured through the application settings:

- `openai_api_key`: API key for authentication
- `openai_model`: Model to use (default: gpt-4o)

These settings can be updated in the `.env` file or through environment variables.

## Error Handling

The client implements proper error handling with custom exceptions:

- `LLMError`: Base exception for all LLM-related errors
- Detailed error messages from the OpenAI API are included in the exceptions

## Future Enhancements

Planned improvements to the Responses API integration:

1. Custom tools for direct clinical trials database search
2. Response caching for common queries
3. Streaming support for long-running searches
4. Fine-tuned model specialization for clinical terminology