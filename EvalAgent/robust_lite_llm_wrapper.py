import asyncio
import json
import logging
from typing import AsyncGenerator, Union, Optional
from pydantic import Field
from google.adk.models.lite_llm import LiteLlm, _message_to_generate_content_response
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from litellm import ChatCompletionAssistantMessage

logger = logging.getLogger(__name__)


def _safe_json_loads(json_str: str, fallback_value: dict = None) -> dict:
    """
    Safely parse JSON with fallback handling for malformed JSON.
    
    Args:
        json_str: The JSON string to parse
        fallback_value: Value to return if parsing fails
        
    Returns:
        Parsed dictionary or fallback value
    """
    if fallback_value is None:
        fallback_value = {}
    
    if not json_str or json_str.strip() == "":
        return fallback_value
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {e}. Original string: {json_str[:200]}...")
        
        # Try to fix common JSON issues
        fixed_attempts = [
            _try_fix_unterminated_string(json_str),
            _try_fix_trailing_comma(json_str),
            _try_fix_unescaped_quotes(json_str),
            _try_extract_partial_json(json_str),
        ]
        
        for fixed_json in fixed_attempts:
            if fixed_json:
                try:
                    result = json.loads(fixed_json)
                    logger.info(f"Successfully fixed JSON: {fixed_json[:100]}...")
                    return result
                except json.JSONDecodeError:
                    continue
        
        logger.error(f"Could not fix JSON: {json_str}")
        return fallback_value


def _try_fix_unterminated_string(json_str: str) -> Optional[str]:
    """Try to fix unterminated string by adding closing quote."""
    try:
        # Find the last quote and see if it's properly closed
        if json_str.count('"') % 2 == 1:  # Odd number of quotes
            return json_str + '"}'
    except Exception:
        pass
    return None


def _try_fix_trailing_comma(json_str: str) -> Optional[str]:
    """Try to fix trailing comma in JSON."""
    try:
        # Remove trailing comma before closing brace
        import re
        fixed = re.sub(r',\s*}', '}', json_str)
        fixed = re.sub(r',\s*]', ']', fixed)
        return fixed
    except Exception:
        pass
    return None


def _try_fix_unescaped_quotes(json_str: str) -> Optional[str]:
    """Try to fix unescaped quotes in JSON values."""
    try:
        # This is a simple attempt - in practice you might need more sophisticated logic
        import re
        # Replace unescaped quotes in values (this is very basic)
        fixed = re.sub(r'([^\\])"([^:,}\]]*)"', r'\1\"\2\"', json_str)
        return fixed
    except Exception:
        pass
    return None


def _try_extract_partial_json(json_str: str) -> Optional[str]:
    """Try to extract a valid JSON object from partial JSON."""
    try:
        # Find the first { and try to match braces
        start = json_str.find('{')
        if start == -1:
            return None
        
        brace_count = 0
        for i, char in enumerate(json_str[start:], start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return json_str[start:i+1]
        
        # If we couldn't match braces, try to close them
        if brace_count > 0:
            return json_str[start:] + '}' * brace_count
            
    except Exception:
        pass
    return None


def _robust_message_to_generate_content_response(message, is_partial: bool = False) -> LlmResponse:
    """
    Robust version of _message_to_generate_content_response that handles JSON errors.
    """
    parts = []
    if message.get("content", None):
        parts.append(types.Part.from_text(text=message.get("content")))

    if message.get("tool_calls", None):
        for tool_call in message.get("tool_calls"):
            if tool_call.type == "function":
                # Use safe JSON parsing
                try:
                    args = _safe_json_loads(tool_call.function.arguments or "{}")
                    part = types.Part.from_function_call(
                        name=tool_call.function.name,
                        args=args,
                    )
                    part.function_call.id = tool_call.id
                    parts.append(part)
                except Exception as e:
                    logger.error(f"Error creating function call part: {e}")
                    # Add a text part with error information instead
                    error_text = f"[Function call error: {tool_call.function.name} - malformed arguments]"
                    parts.append(types.Part.from_text(text=error_text))

    return LlmResponse(
        content=types.Content(role="model", parts=parts), partial=is_partial
    )


class RobustLiteLlmWithSleep(LiteLlm):
    """
    Robust wrapper around LiteLlm that handles JSON parsing errors and adds sleep.
    
    This wrapper:
    1. Adds configurable sleep between responses
    2. Handles malformed JSON in function calls gracefully
    3. Provides detailed logging for debugging
    """
    
    sleep_duration: float = Field(default=1.0, description="Time to sleep between responses in seconds")
    enable_json_fixing: bool = Field(default=True, description="Whether to attempt fixing malformed JSON")
    
    def __init__(self, model: str, sleep_duration: float = 1.0, enable_json_fixing: bool = True, **kwargs):
        """
        Initialize the robust wrapper.
        
        Args:
            model: The name of the LiteLlm model
            sleep_duration: Time to sleep between responses in seconds
            enable_json_fixing: Whether to attempt fixing malformed JSON
            **kwargs: Additional arguments passed to LiteLlm
        """
        super().__init__(
            model=model, 
            sleep_duration=sleep_duration, 
            enable_json_fixing=enable_json_fixing,
            **kwargs
        )
    
    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        Generates content asynchronously with robust error handling and sleep.
        """
        try:
            # Get the original generator from the parent class
            async for response in super().generate_content_async(llm_request, stream):
                # Yield the response
                yield response
                
                # Add sleep after each response
                if self.sleep_duration > 0:
                    await asyncio.sleep(self.sleep_duration)
                    
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in LiteLLM: {e}")
            
            if self.enable_json_fixing:
                # Try to recover by calling the original method with our robust parsing
                try:
                    # This is a more complex recovery - you might need to implement
                    # custom streaming logic here if needed
                    error_response = LlmResponse(
                        content=types.Content(
                            role="model", 
                            parts=[types.Part.from_text(
                                text="[Error: The model response contained malformed JSON. Please try again.]"
                            )]
                        )
                    )
                    yield error_response
                except Exception as recovery_error:
                    logger.error(f"Recovery failed: {recovery_error}")
                    raise e
            else:
                raise e
        except Exception as e:
            logger.error(f"Unexpected error in generate_content_async: {e}")
            raise e


# Monkey patch the original function if needed
def apply_robust_json_parsing():
    """
    Apply robust JSON parsing to the original LiteLLM module.
    This monkey patches the _message_to_generate_content_response function.
    """
    import google.adk.models.lite_llm as lite_llm_module
    
    # Store original function
    original_function = lite_llm_module._message_to_generate_content_response
    
    def patched_function(message, is_partial: bool = False):
        try:
            return original_function(message, is_partial)
        except json.JSONDecodeError as e:
            logger.warning(f"Using robust JSON parsing due to error: {e}")
            return _robust_message_to_generate_content_response(message, is_partial)
    
    # Replace the function
    lite_llm_module._message_to_generate_content_response = patched_function
    logger.info("Applied robust JSON parsing patch to LiteLLM")


# Configuration helper
class LiteLLMConfig:
    """Helper class for configuring LiteLLM to reduce JSON errors."""
    
    @staticmethod
    def get_robust_config():
        """Get configuration that reduces JSON parsing errors."""
        return {
            "temperature": 0.1,  # Lower temperature for more consistent output
            "max_tokens": 2048,  # Ensure responses aren't cut off
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
    
    @staticmethod
    def get_function_call_config():
        """Get configuration optimized for function calls."""
        return {
            "temperature": 0.0,  # Deterministic for function calls
            "max_tokens": 1024,
            "top_p": 0.95,
        }


# Example usage
async def example_robust_usage():
    """Example of using the robust wrapper."""
    
    # Apply the global patch for all LiteLLM instances
    apply_robust_json_parsing()
    
    # Use the robust wrapper
    model = RobustLiteLlmWithSleep(
        model="gpt-3.5-turbo",
        sleep_duration=1.0,
        enable_json_fixing=True,
        **LiteLLMConfig.get_robust_config()  # Use robust configuration
    )
    
    # Your request code here...
    # The model will now handle JSON errors gracefully
