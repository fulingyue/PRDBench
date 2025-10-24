import asyncio
from typing import AsyncGenerator, Dict, Optional
from pydantic import Field
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
import tiktoken
from datetime import datetime
import threading
import hashlib
import time

current_time = lambda: int(time.time())


class EarlyStopException(Exception):
    """Custom exception for forcing agent execution to stop"""
    def __init__(self, reason: str = "Early stop triggered"):
        self.reason = reason
        super().__init__(reason)

class LiteLlmWithSleep(LiteLlm):
    """
    Wrapper around LiteLlm that adds configurable sleep between responses.
    
    This allows you to control the rate of LLM responses without modifying
    the original library code.
    """
    
    sleep_duration: float = Field(default=2.0, description="Time to sleep between responses in seconds")
    enable_compression: bool = Field(default=False, description="Whether to enable compression")
    max_tokens_threshold: int = Field(default=None, description="Token threshold to trigger compression")
    tokenizer: object = Field(default=None, description="Tokenizer for token counting")
    max_total_tokens: int = Field(default=5_000_000, description="Max total tokens for truncate")
    warning_threshold: float = Field(default=0.8, description="Warning threshold for total tokens")
    max_session_time: int = Field(default=1800, description="Max session time in seconds")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize session-level token management
        self._session_tokens: Dict[str, int] = {}
        self._session_times: Dict[str, int] = {}
        self._session_early_stop: Dict[str, bool] = {}
        self._session_early_stop_reason: Dict[str, str] = {}
        self._lock = threading.Lock()
        
        # Initialize tokenizer
        if self.tokenizer is None:
            try:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
            except:
                self.tokenizer = None
    
    def _get_session_id(self, llm_request: LlmRequest) -> str:
        """Get or generate session ID"""
        # Get session_id from request's custom_metadata, if not available generate one
        # ADK doesn't support getting session ID, using first round prompt as substitute for now
        # TODO: Update to ADK-supported session ID later
        first_prompt = str(llm_request.contents[0].parts[0].text)
        session_id = hashlib.md5(first_prompt.encode()).hexdigest()[:8]
        return session_id
    
    def _get_session_tokens(self, session_id: str) -> int:
        """Get token count for specified session"""
        with self._lock:
            return self._session_tokens.get(session_id, 0)
    
    def _set_session_tokens(self, session_id: str, tokens: int):
        """Set token count for specified session"""
        with self._lock:
            self._session_tokens[session_id] = tokens
    
    def _add_session_tokens(self, session_id: str, tokens: int):
        """Add token count for specified session"""
        with self._lock:
            current = self._session_tokens.get(session_id, 0)
            self._session_tokens[session_id] = current + tokens


    def _get_session_times(self, session_id: str) -> int:
        """Get start time count for specified session"""
        with self._lock:
            s_time = self._session_times.get(session_id, current_time())
            self._session_times[session_id] = s_time 
            return s_time
    
    def _set_session_times(self, session_id: str, times: int):
        """Set start time count for specified session"""
        with self._lock:
            self._session_times[session_id] = times
    

    
    def _get_session_early_stop(self, session_id: str) -> bool:
        """Get early stop status for specified session"""
        with self._lock:
            return self._session_early_stop.get(session_id, False)
    
    def _set_session_early_stop(self, session_id: str, triggered: bool, reason: str = None):
        """Set early stop status for specified session"""
        with self._lock:
            self._session_early_stop[session_id] = triggered
            self._session_early_stop_reason[session_id] = str(reason)
    
    def reset_session_tokens(self, session_id: str):
        """Reset token count for specified session"""
        with self._lock:
            self._session_tokens[session_id] = 0
            self._session_early_stop[session_id] = False

    def get_session_token_info(self, session_id: str) -> dict:
        """Get token usage information for specified session"""
        current_tokens = self._get_session_tokens(session_id)
        start_time = self._get_session_times(session_id)
        return {
            "session_id": session_id,
            "current_tokens": current_tokens,
            "start_time": start_time,
            "max_tokens": self.max_total_tokens,
            "usage_ratio": current_tokens / self.max_total_tokens if self.max_total_tokens else 0,
            "early_stop_triggered": self._get_session_early_stop(session_id),
        }

    def set_new_response_info(self, old_request, new_request):
        # Set old session's token count and start time to new session
        old_session_id = self._get_session_id(old_request)
        new_session_id = self._get_session_id(new_request)
        old_token_count = self._get_session_tokens(old_session_id)
        self._set_session_tokens(new_session_id, old_token_count)
        old_start_time = self._get_session_times(old_session_id)
        self._set_session_times(new_session_id, old_start_time)

    def count_tokens_with_tiktoken(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.tokenizer.encode(text))


 
    
    def _update_token_count(self, llm_request: LlmRequest, response: LlmResponse, session_id: str):
        """Update token count for specified session"""
        import logging
        logger = logging.getLogger(__name__)
        request_tokens = response.usage_metadata.prompt_token_count
        response_tokens = response.usage_metadata.candidates_token_count
        total_tokens = request_tokens + response_tokens
        logger.info(f"Session {session_id}: Request tokens: {request_tokens}, Response tokens: {response_tokens}, Total tokens: {total_tokens}")


        self._add_session_tokens(session_id, total_tokens)
        
        
        # Check if limit exceeded
        current_total = self._get_session_tokens(session_id)
        
        if self.max_total_tokens and current_total >= self.max_total_tokens:
            self._set_session_early_stop(session_id, True, reason=f"Token usage has reached limit ({current_total}/{self.max_total_tokens})")
            logger.warning(f"Session {session_id}: Token usage has reached limit ({current_total}/{self.max_total_tokens})")
        else:
            logger.info(f"Session {session_id}: Current tokens: {current_total}, Max tokens: {self.max_total_tokens}")
        if current_time() >= self._get_session_times(session_id) + self.max_session_time:
            self._set_session_early_stop(session_id, True, reason=f"Session time has reached limit ({ current_time() - self._get_session_times(session_id)}s/{self.max_session_time}s)")
            logger.warning(f"Session {session_id}: Session time has reached limit ({ current_time() - self._get_session_times(session_id)}s/{self.max_session_time}s)")
        else:
            logger.info(f"Session {session_id}: Session time: {current_time() - self._get_session_times(session_id)}s, Max session time: {self.max_session_time}s")
    
    def _create_exit_loop_response(self, session_id: str = None, reason=None) -> LlmResponse:
        """Create response containing exit_loop tool call"""
        # Mark early stop triggered
        if session_id:
            self._set_session_early_stop(session_id, True, reason=reason)
        if reason:
            reason = f"reason: {reason}"
        
        # Get current session's token information
        current_tokens = self._get_session_tokens(session_id) if session_id else 0
        
        # Create a more explicit stop response
        return LlmResponse(
            content=types.Content(
                role="assistant",
                parts=[
                    types.Part(text=f"{reason}, exiting...")
                ]
            ),
            partial=False,  # Indicates this is a complete response
            turn_complete=True,  # Indicates conversation turn is complete
            error_code="TOKEN_LIMIT_EXCEEDED" if reason is None else reason,  # Use error code
            error_message=f"reason: {reason}",
            interrupted=True,  # Mark as interrupted
            custom_metadata={
                "early_stop": True,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
                "force_stop": True,
                "stop_immediately": True,
                "no_more_responses": True,  # Mark no more responses
                "session_should_end": True,  # Explicitly mark session should end
                "session_id": session_id  # Add session_id
            }
        )
    
    def _force_early_stop(self, reason: str = "Token limit exceeded"):
        """Force trigger early stop and raise exception"""
        self.early_stop_triggered = True
        raise EarlyStopException(reason)

    def reset_token_count(self):
        """Reset token count (maintain backward compatibility)"""
        # This method now resets token count for all sessions
        with self._lock:
            self._session_tokens.clear()
            self._session_early_stop.clear()
    
    def force_reset_early_stop(self):
        """Force reset early stop status (maintain backward compatibility)"""
        # This method now resets early stop status for all sessions
        with self._lock:
            self._session_early_stop.clear()
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Early stop status for all sessions has been reset")
    
    def is_early_stop_triggered(self) -> bool:
        """Check if early stop has been triggered (maintain backward compatibility)"""
        # This method now checks if any session has triggered early stop
        with self._lock:
            return any(self._session_early_stop.values())
    
    def get_token_usage_info(self) -> dict:
        """Get token usage information (maintain backward compatibility)"""
        # This method now returns total token usage information for all sessions
        with self._lock:
            total_tokens = sum(self._session_tokens.values())
            total_early_stop = sum(self._session_early_stop.values())
        
        return {
            "total_sessions": len(self._session_tokens),
            "total_tokens": total_tokens,
            "max_tokens": self.max_total_tokens,
            "usage_ratio": total_tokens / self.max_total_tokens if self.max_total_tokens else 0,
            "early_stop_sessions": total_early_stop,
            "session_details": {
                session_id: self.get_session_token_info(session_id)
                for session_id in self._session_tokens.keys()
            }
        }
    
    def _add_token_warning_to_request(self, llm_request: LlmRequest, session_id: str) -> LlmRequest:
        """Add token warning information to request"""
        current_tokens = self._get_session_tokens(session_id)
        
        if self.max_total_tokens and self.warning_threshold:
            usage_ratio = current_tokens / self.max_total_tokens
            if usage_ratio >= self.warning_threshold:
                warning_message = f"\n⚠️ Warning: Current token usage has reached {usage_ratio:.1%} ({current_tokens}/{self.max_total_tokens}), please control response length."
                
                # Add warning at the beginning of first content's parts
                if llm_request.contents and llm_request.contents[0].parts:
                    # Create new parts list, add warning at the beginning
                    new_parts = [types.Part(text=warning_message)]
                    new_parts.extend(llm_request.contents[0].parts)
                    
                    # Create new content
                    new_content = types.Content(
                        role=llm_request.contents[0].role,
                        parts=new_parts
                    )
                    
                    # Create new request
                    new_request = LlmRequest(
                        contents=[new_content] + llm_request.contents[1:],
                        config=llm_request.config
                    )

                    # Compressed request needs to inherit previous token count
                    self.set_new_response_info(llm_request, new_request)


                    return new_request
        
        return llm_request
    
    def string_to_contents(self, compressed_string: str) -> list[types.Content]:
        """Convert compressed string back to Content list"""
        # Compressed content uses "summary" role, more accurately representing this is summary content
        
        return [types.Content(
            role="summary",  # Use "summary" instead of "user"
            parts=[types.Part.from_text(text=compressed_string)]
        )]
        
    def content_to_string(self, content: types.Content) -> str:
        """Convert single Content to string"""
        if not content.parts:
            return ""
        
        parts_text = []
        for part in content.parts:
            if part.text:
                parts_text.append(f"[{content.role}]: {part.text}")
            elif part.function_call:
                parts_text.append(f"[{content.role} function_call]: {part.function_call}")
            elif part.function_response:
                parts_text.append(f"[{content.role} function_response]: {part.function_response}")
        
        return "\n".join(parts_text)

    def contents_to_string(self, contents: list[types.Content]) -> str:
        """Convert contents list to string"""
        return "\n\n".join(self.content_to_string(content) for content in contents)
    
    def should_compress(self, llm_request: LlmRequest) -> bool:
        """Determine if compression is needed"""
        if not self.enable_compression:
            return False
        
        # Calculate token count for contents
        content_string = self.contents_to_string(llm_request.contents)
        content_tokens = self.count_tokens_with_tiktoken(content_string)
        import logging
        logger = logging.getLogger(__name__)
        if content_tokens > self.max_tokens_threshold:
            logger.info(f"content_tokens: {content_tokens}, max_tokens_threshold: {self.max_tokens_threshold}")
            # logger.info(f"Enabling compression tokens")
        return content_tokens > self.max_tokens_threshold
    
    async def compress_with_llm_async(self, llm_request: LlmRequest) -> LlmRequest:
        """Asynchronously compress LlmRequest contents using LLM"""
        # not in use
        # Separate historical content and current user question
        if len(llm_request.contents) <= 2:
            # If only two contents, no need to compress
            return llm_request
        
        # Keep first and last content (usually current user question)
        first_content = llm_request.contents[0]
        historical_contents = llm_request.contents[1:]
    
        # 1. Convert contents to string
        content_string = self.contents_to_string(historical_contents)
        compression_prompt = f"""You are the component that summarizes internal chat history into a given structure.
When the conversation history grows too large, you will be invoked to distill the entire history into a concise, structured XML snapshot. This snapshot is CRITICAL, as it will become the agent's *only* memory of the past. The agent will resume its work based solely on this snapshot. All crucial details, plans, errors, and user directives MUST be preserved.

First, you will think through the entire history in a private <scratchpad>. Review the user's overall goal, the agent's actions, tool outputs, file modifications, and any unresolved questions. Identify every piece of information that is essential for future actions.

After your reasoning is complete, generate the final <state_snapshot> XML object. Be incredibly dense with information. Omit any irrelevant conversational filler.

The structure MUST be as follows:
<state_snapshot>
    <overall_goal>
        <!-- A single, concise sentence describing the user's high-level objective. -->
    </overall_goal>
    <key_knowledge>
        <!-- Crucial facts, conventions, and constraints the agent must remember based on the conversation history and interaction with the user. Use bullet points. -->
    </key_knowledge>
    <file_system_state>
        <!-- List files that have been created, read, modified, or deleted. Note their status and critical learnings. -->
    </file_system_state>
    <recent_actions>
        <!-- A summary of the last few significant agent actions and their outcomes. Focus on facts. -->
    </recent_actions>
    <current_plan>
        <!-- The agent's step-by-step plan. Mark completed steps. -->
    </current_plan>
</state_snapshot>
"""
        
        # 2. Create compression request, use compression instruction as system prompt
        compression_request = LlmRequest(
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=content_string)]
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=compression_prompt,
                temperature=0.1,
                max_output_tokens=2000
            )
        )


        import logging
        logger = logging.getLogger(__name__)
        # logger.info(f"Before compression, first prompt: {llm_request.contents[0].parts[0].text}")
        logger.info(f"Before compression, first prompt length: {len(llm_request.contents[0].parts[0].text.strip())}")
        if len(llm_request.contents[0].parts[0].text.strip()) < 5:
            logger.info(f"Before compression, first prompt length is abnormal")
        
        
        # 3. Temporarily disable compression to avoid recursion
        original_enable_compression = self.enable_compression
        try:
            self.enable_compression = False
            
            # 4. Call LLM for compression
            compressed_content = ""
            async for response in super().generate_content_async(compression_request, stream=False):
                if response.content and response.content.parts:
                    for part in response.content.parts:
                        if part.text:
                            compressed_content += part.text
            

            llm_request.contents = [
                first_content,
                types.Content(
                    role="summary",
                    parts=[types.Part.from_text(text=compressed_content)]
                )
            ]
            # self.set_new_response_info(llm_request, compressed_request)

            logger.info(f"After compression, content length: {len(compressed_content)}")

            
        finally:
            self.enable_compression = original_enable_compression
    
    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False, retry_count: int = 0, max_retries: int = 4
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        Generates content asynchronously with sleep between responses.
        
        Args:
            llm_request: The request to send to the model
            stream: Whether to stream the response
            retry_count: Current retry count
            max_retries: Maximum retry count
            
        Yields:
            LlmResponse: The model response with sleep between yields
        """
        session_id = self._get_session_id(llm_request)
        # Check if early stop has already been triggered
        if self._get_session_early_stop(session_id):
            yield self._create_exit_loop_response(session_id, reason=self._session_early_stop_reason.get(session_id))
            return
            
        # Check token limit
        if self.max_total_tokens and self._get_session_tokens(session_id) >= self.max_total_tokens:
            yield self._create_exit_loop_response(session_id, f"Token usage has reached limit: {self.max_total_tokens}")
            return 
        
        # Check time limit
        if current_time() >= self._get_session_times(session_id) + self.max_session_time:
            yield self._create_exit_loop_response(session_id, f"Session time has reached limit: {self.max_session_time}s")
            return

            
        
        # Add token warning information to request (if warning threshold exceeded)
        llm_request = self._add_token_warning_to_request(llm_request, session_id)
        if self.should_compress(llm_request):
            # 2. Prompt model for compression,
            llm_request.contents.append(types.Content(
                role="warning",
                parts=[types.Part.from_text(text="Your conversation history token usage has reached limit. In subsequent interactions, earlier parts of the conversation may be truncated. It is recommended that you summarize your conversation history and save it to a file for future reference.")]
            ))
            # assert len(llm_request.contents) == 3
        # Get the original generator from the parent class
        try:
            import logging
            logger = logging.getLogger(__name__)
            # logger.info('--------------------------------')
            # logger.info(f"prompt now:{llm_request}")
            async for response in super().generate_content_async(llm_request, stream):
                # Update token count
                self._update_token_count(llm_request, response, session_id)
                # Yield the response
                yield response
                
                # Add sleep after each response (except the last one if needed)
                if self.sleep_duration > 0:
                    await asyncio.sleep(self.sleep_duration)
                    
        except Exception as e:
            # If exception occurs, check if retry is possible
            import logging
            logger = logging.getLogger(__name__)
            
            if retry_count < max_retries:
                # Can retry, increment retry count
                retry_count += 1
                logger.warning(f"Exception occurred while generating content: {e}, retrying for the {retry_count}th time...")
        
                # Wait briefly before retry
                await asyncio.sleep(1)

                # Recursively call self for retry
                async for response in self.generate_content_async(llm_request, stream, retry_count, max_retries):
                    yield response
                return
            else:
                # Reached maximum retry count, trigger early stop
                logger.error(f"Exception occurred while generating content: {e}, reached maximum retry count {max_retries}")
                self._set_session_early_stop(session_id, True, reason=f"Exception occurred while generating content: {e}, retried {max_retries} times")
                yield self._create_exit_loop_response(session_id, reason=f"Exception occurred while generating content: {e}, retried {max_retries} times")
                return

        # Final check to ensure nothing was missed
        if self._get_session_early_stop(session_id):
            yield self._create_exit_loop_response(session_id, reason=self._session_early_stop_reason.get(session_id))
            return
