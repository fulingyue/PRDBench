"""
Example usage of LiteLlm with sleep functionality.
This demonstrates how to add delays between LLM responses without modifying the library.
"""

import asyncio
import os
from pydantic import Field
from google.adk.models.llm_request import LlmRequest
from google.genai import types
from lite_llm_wrapper import LiteLlmWithSleep, SleepDecorator, TemporarySleep


async def main():
    """Main example function demonstrating different approaches."""
    
    # Example 1: Using inheritance approach
    print("=== Example 1: Inheritance Approach ===")
    model_with_sleep = LiteLlmWithSleep(
        model="gpt-3.5-turbo",  # or any litellm supported model
        sleep_duration=2.0  # 2 seconds between responses
    )
    
    # Create a simple request
    request = LlmRequest(
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text("Hello, how are you?")]
            )
        ],
        config=types.GenerateContentConfig()
    )
    
    print("Generating responses with 2-second delays...")
    async for response in model_with_sleep.generate_content_async(request, stream=True):
        if response.content and response.content.parts:
            for part in response.content.parts:
                if part.text:
                    print(f"Response chunk: {part.text}")
                    print("(sleeping for 2 seconds...)")
    
    print("\n=== Example 2: Decorator Approach ===")
    
    # Create original model
    from google.adk.models.lite_llm import LiteLlm
    original_model = LiteLlm(model="gpt-3.5-turbo")
    
    # Wrap with sleep decorator
    decorated_model = SleepDecorator(original_model, sleep_duration=1.0)
    
    print("Generating responses with 1-second delays...")
    async for response in decorated_model.generate_content_async(request, stream=True):
        if response.content and response.content.parts:
            for part in response.content.parts:
                if part.text:
                    print(f"Response chunk: {part.text}")
                    print("(sleeping for 1 second...)")
    
    print("\n=== Example 3: Context Manager Approach ===")
    
    model = LiteLlm(model="gpt-3.5-turbo")
    
    # Use context manager for temporary sleep
    async with TemporarySleep(model, sleep_duration=0.5) as temp_model:
        print("Generating responses with 0.5-second delays...")
        async for response in temp_model.generate_content_async(request, stream=True):
            if response.content and response.content.parts:
                for part in response.content.parts:
                    if part.text:
                        print(f"Response chunk: {part.text}")
                        print("(sleeping for 0.5 seconds...)")
    
    print("\nOutside context manager - no sleep")
    # Model works normally here without sleep


async def advanced_example():
    """Advanced example with dynamic sleep adjustment."""
    
    class AdaptiveSleepLlm(LiteLlmWithSleep):
        """LLM with adaptive sleep based on response length."""
        
        base_sleep: float = Field(default=1.0, description="Base sleep duration for adaptive calculation")
        
        def __init__(self, model: str, base_sleep: float = 1.0, **kwargs):
            super().__init__(model, sleep_duration=base_sleep, base_sleep=base_sleep, **kwargs)
        
        async def generate_content_async(self, llm_request, stream=False):
            async for response in super(LiteLlmWithSleep, self).generate_content_async(llm_request, stream):
                yield response
                
                # Adaptive sleep based on response length
                if response.content and response.content.parts:
                    total_length = sum(len(part.text or "") for part in response.content.parts)
                    # Longer responses get longer sleep
                    adaptive_sleep = self.base_sleep + (total_length / 100)
                    await asyncio.sleep(min(adaptive_sleep, 5.0))  # Cap at 5 seconds
    
    print("=== Advanced Example: Adaptive Sleep ===")
    adaptive_model = AdaptiveSleepLlm(
        model="gpt-3.5-turbo",
        base_sleep=0.5
    )
    
    # Test with different request lengths
    short_request = LlmRequest(
        contents=[types.Content(role="user", parts=[types.Part.from_text("Hi")])],
        config=types.GenerateContentConfig()
    )
    
    long_request = LlmRequest(
        contents=[types.Content(
            role="user", 
            parts=[types.Part.from_text("Please write a detailed explanation about machine learning")]
        )],
        config=types.GenerateContentConfig()
    )
    
    print("Short request (shorter sleep):")
    async for response in adaptive_model.generate_content_async(short_request):
        print("Response received with adaptive sleep")
    
    print("\nLong request (longer sleep):")
    async for response in adaptive_model.generate_content_async(long_request):
        print("Response received with adaptive sleep")


if __name__ == "__main__":
    # Set up environment variables if needed
    # os.environ["OPENAI_API_KEY"] = "your-api-key"
    
    # Run examples
    print("Running sleep examples...")
    asyncio.run(main())
    
    print("\nRunning advanced example...")
    asyncio.run(advanced_example())
