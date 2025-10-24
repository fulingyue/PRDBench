"""
MCP Connection Retry and Error Handling Wrapper
Solves MCP service connection failures, timeouts and cancellation errors
"""

import asyncio
import logging
import time
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager
import httpx
# Compatible import for different named SessionManager classes
try:
    from google.adk.tools.mcp_tool.mcp_session_manager import MCPSessionManager as _BaseSessionManager
except Exception:  # pragma: no cover - Environment difference tolerance
    from google.adk.tools.mcp_tool.mcp_session_manager import McpSessionManager as _BaseSessionManager

# Compatible import for different named MCPToolset classes
try:
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset as _BaseMCPToolset
except Exception:  # pragma: no cover - Environment difference tolerance
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset as _BaseMCPToolset

logger = logging.getLogger(__name__)


class RetryConfig:
    """Retry configuration class"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_backoff: bool = True,
        timeout: float = 30.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff
        self.timeout = timeout


class RobustMcpSessionManager(_BaseSessionManager):
    """MCP session manager with retry mechanism"""
    
    def __init__(self, *args, retry_config: Optional[RetryConfig] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.retry_config = retry_config or RetryConfig()
        self._connection_cache = {}
        
    async def create_session_with_retry(self, headers: Optional[Dict[str, str]] = None):
        """Session creation with retry mechanism (compatible with headers)"""
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                logger.info(f"MCP connection attempt {attempt + 1}/{self.retry_config.max_retries + 1}")
                
                # Set timeout
                async with asyncio.timeout(self.retry_config.timeout):
                    # Call base class real creation method, avoid recursion
                    session = await super().create_session(headers=headers)
                    logger.info("MCP connection successfully established")
                    return session
                    
            except asyncio.CancelledError as e:
                logger.warning(f"MCP connection cancelled (attempt {attempt + 1}): {e}")
                last_exception = e
                
            except asyncio.TimeoutError as e:
                logger.warning(f"MCP connection timeout (attempt {attempt + 1}): {e}")
                last_exception = e
                
            except httpx.ConnectError as e:
                logger.warning(f"MCP network connection error (attempt {attempt + 1}): {e}")
                last_exception = e
                
            except Exception as e:
                logger.warning(f"MCP connection unknown error (attempt {attempt + 1}): {e}")
                last_exception = e
            
            # If not the last attempt, wait and retry
            if attempt < self.retry_config.max_retries:
                delay = self._calculate_delay(attempt)
                logger.info(f"Waiting {delay:.2f} seconds before retry...")
                await asyncio.sleep(delay)
        
        # All retries failed
        logger.error(f"MCP connection failed, retried {self.retry_config.max_retries} times")
        raise last_exception

    async def create_session(self, headers: Optional[Dict[str, str]] = None):
        """Override base class create_session, use retry version by default."""
        return await self.create_session_with_retry(headers=headers)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay time"""
        if self.retry_config.exponential_backoff:
            delay = self.retry_config.base_delay * (2 ** attempt)
        else:
            delay = self.retry_config.base_delay
        
        return min(delay, self.retry_config.max_delay)


class RobustMcpToolset(_BaseMCPToolset):
    """MCP toolset with retry and fault tolerance mechanism"""
    
    def __init__(self, *args, retry_config: Optional[RetryConfig] = None, **kwargs):
        # First initialize normally with base class, get _connection_params / _errlog
        super().__init__(*args, **kwargs)
        self.retry_config = retry_config or RetryConfig()
        self._fallback_tools = []
        self._last_error: Optional[str] = None
        # Use same connection_params/errlog to build robust session manager, replace base class
        try:
            self._mcp_session_manager = RobustMcpSessionManager(
                connection_params=self._connection_params,
                errlog=self._errlog,
                retry_config=self.retry_config,
            )
        except Exception as e:
            logger.warning(f"Failed to build RobustMcpSessionManager, fallback to original manager: {e}")
    
    async def get_tools(self, readonly_context=None):
        """Override original method, ensure even if MCP fails no exception is thrown, return degradable result.
        This way upper FastAPI won't 500, client can get JSON normally.
        """
        try:
            return await super().get_tools(readonly_context)
        except BaseException as e:
            logger.error(f"Failed to get MCP tools (get_tools): {e}")
            self._last_error = str(e)
            # Return fallback tools or empty list, avoid throwing causing 500
            if self._fallback_tools:
                logger.info("Using fallback tool list")
                return self._fallback_tools
            logger.warning("Returning empty tool list")
            return []
    
    async def get_tools_with_retry(self, ctx):
        """Get tools with retry and fallback"""
        try:
            # Try to get MCP tools normally
            return await self.get_tools(ctx)
            
        except Exception as e:
            logger.error(f"Failed to get MCP tools: {e}")
            
            # Return fallback tools or empty list
            if self._fallback_tools:
                logger.info("Using fallback tool list")
                return self._fallback_tools
            else:
                logger.warning("Returning empty tool list")
                return []
    
    def set_fallback_tools(self, tools: List[Any]):
        """Set fallback tool list"""
        self._fallback_tools = tools


def apply_mcp_monkey_patches(retry_config: Optional[RetryConfig] = None):
    """Replace ADK's MCP classes with robust versions, avoid throwing exceptions causing /run to return 500.
    - Replace McpSessionManager with RobustMcpSessionManager, create_session with retry
    - Replace McpToolset with RobustMcpToolset, get_tools catches exceptions and returns fallback result
    """
    try:
        import google.adk.tools.mcp_tool.mcp_session_manager as mcp_session_module
        import google.adk.tools.mcp_tool.mcp_toolset as mcp_toolset_module

        # Patch SessionManager: ensure create_session uses retry version
        original_manager_lower = getattr(mcp_session_module, 'McpSessionManager', None)
        original_manager_upper = getattr(mcp_session_module, 'MCPSessionManager', None)

        class PatchedMcpSessionManager(RobustMcpSessionManager):
            def __init__(self, *args, **kwargs):
                # Pass through required parameters connection_params, errlog; retry_config optional
                super().__init__(*args, retry_config=retry_config or RetryConfig(), **kwargs)
            async def create_session(self):
                return await self.create_session_with_retry()

        # Apply SessionManager patch
        if original_manager_lower is not None:
            mcp_session_module.McpSessionManager = PatchedMcpSessionManager  # type: ignore[attr-defined]
        if original_manager_upper is not None:
            mcp_session_module.MCPSessionManager = PatchedMcpSessionManager  # type: ignore[attr-defined]

        # Patch Toolset: point original McpToolset to robust version
        original_toolset_lower = getattr(mcp_toolset_module, 'McpToolset', None)
        original_toolset_upper = getattr(mcp_toolset_module, 'MCPToolset', None)

        class PatchedMcpToolset(RobustMcpToolset):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, retry_config=retry_config or RetryConfig(), **kwargs)

        # If lowercase class name exists then override
        if original_toolset_lower is not None:
            mcp_toolset_module.McpToolset = PatchedMcpToolset  # type: ignore[attr-defined]
        # If uppercase class name exists then override
        if original_toolset_upper is not None:
            mcp_toolset_module.MCPToolset = PatchedMcpToolset  # type: ignore[attr-defined]

        logger.info("✅ MCP monkey patch applied: McpSessionManager and McpToolset use robust versions")
        return {
            "patched": True,
            "original_manager_lower": str(original_manager_lower),
            "original_manager_upper": str(original_manager_upper),
            "original_toolset_lower": str(original_toolset_lower),
            "original_toolset_upper": str(original_toolset_upper)
        }
    except Exception as e:
        logger.error(f"Failed to apply MCP monkey patch: {e}")
        return {"patched": False, "error": str(e)}


@asynccontextmanager
async def robust_mcp_connection(
    mcp_config: Dict[str, Any],
    retry_config: Optional[RetryConfig] = None
):
    """
    Robust MCP connection context manager
    
    Args:
        mcp_config: MCP configuration dictionary
        retry_config: Retry configuration
    """
    session_manager = None
    session = None
    
    try:
        # Create session manager with retry
        session_manager = RobustMcpSessionManager(
            retry_config=retry_config or RetryConfig()
        )
        
        # Try to create session
        session = await session_manager.create_session_with_retry()
        
        yield session
        
    except Exception as e:
        logger.error(f"MCP connection completely failed: {e}")
        # Can implement fallback logic here
        yield None
        
    finally:
        # Clean up resources
        if session:
            try:
                await session.close()
            except Exception as e:
                logger.warning(f"Error closing MCP session: {e}")


class McpHealthChecker:
    """MCP service health checker"""
    
    def __init__(self, mcp_url: str, check_interval: float = 60.0):
        self.mcp_url = mcp_url
        self.check_interval = check_interval
        self._is_healthy = False
        self._last_check = 0
    
    async def is_healthy(self) -> bool:
        """Check if MCP service is healthy"""
        current_time = time.time()
        
        # If less than check_interval seconds since last check, return cached result
        if current_time - self._last_check < self.check_interval:
            return self._is_healthy
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.mcp_url)
                self._is_healthy = response.status_code == 200
                
        except Exception as e:
            logger.warning(f"MCP health check failed: {e}")
            self._is_healthy = False
        
        self._last_check = current_time
        return self._is_healthy


# Agent configuration helper
class AgentConfigHelper:
    """Agent configuration helper, handles MCP tool configuration"""
    
    @staticmethod
    def create_robust_mcp_config(
        mcp_url: str,
        max_retries: int = 3,
        timeout: float = 30.0,
        enable_fallback: bool = True
    ) -> Dict[str, Any]:
        """Create robust MCP configuration"""
        
        retry_config = RetryConfig(
            max_retries=max_retries,
            timeout=timeout,
            base_delay=1.0,
            max_delay=10.0,
            exponential_backoff=True
        )
        
        return {
            "mcp_url": mcp_url,
            "retry_config": retry_config,
            "enable_fallback": enable_fallback,
            "health_check_interval": 60.0
        }
    
    @staticmethod
    async def setup_robust_agent_tools(agent, mcp_configs: List[Dict[str, Any]]):
        """Set up robust MCP tools for Agent"""
        robust_tools = []
        
        for config in mcp_configs:
            try:
                # Create robust MCP toolset
                mcp_toolset = RobustMcpToolset(
                    retry_config=config.get("retry_config")
                )
                
                # Set fallback tools (if needed)
                if config.get("enable_fallback"):
                    fallback_tools = []  # Can add fallback tools here
                    mcp_toolset.set_fallback_tools(fallback_tools)
                
                robust_tools.append(mcp_toolset)
                
            except Exception as e:
                logger.error(f"Failed to set up MCP tools: {e}")
                continue
        
        # Add tools to agent
        if robust_tools:
            agent.tools.extend(robust_tools)
        
        return robust_tools


# Usage examples and configuration
async def example_robust_mcp_usage():
    """Robust MCP usage example"""
    
    # 1. Basic retry configuration
    retry_config = RetryConfig(
        max_retries=5,          # Maximum 5 retries
        base_delay=2.0,         # Base delay 2 seconds
        max_delay=30.0,         # Maximum delay 30 seconds
        exponential_backoff=True, # Use exponential backoff
        timeout=45.0            # Single connection timeout 45 seconds
    )
    
    # 2. Use robust connection manager
    mcp_config = {
        "url": "http://your-mcp-server:port",
        "headers": {"Authorization": "Bearer your-token"}
    }
    
    async with robust_mcp_connection(mcp_config, retry_config) as mcp_session:
        if mcp_session:
            logger.info("MCP connection successful, can use normally")
            # Use MCP session
        else:
            logger.warning("MCP connection failed, using fallback mode")
            # Fallback logic
    
    # 3. Health check
    health_checker = McpHealthChecker("http://your-mcp-server:port/health")
    if await health_checker.is_healthy():
        logger.info("MCP service healthy")
    else:
        logger.warning("MCP service unhealthy, recommend checking")


# Actual application configuration recommendations
MCP_PRODUCTION_CONFIG = {
    "retry_config": RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=15.0,
        exponential_backoff=True,
        timeout=30.0
    ),
    "enable_health_check": True,
    "health_check_interval": 60.0,
    "enable_fallback": True,
    "log_level": "INFO"
}

MCP_DEVELOPMENT_CONFIG = {
    "retry_config": RetryConfig(
        max_retries=1,
        base_delay=0.5,
        max_delay=5.0,
        exponential_backoff=False,
        timeout=10.0
    ),
    "enable_health_check": False,
    "enable_fallback": False,
    "log_level": "DEBUG"
}
