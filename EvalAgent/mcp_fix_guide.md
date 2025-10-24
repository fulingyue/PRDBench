# MCP Connection Issue Fix Guide

## Problem Symptoms
```
asyncio.exceptions.CancelledError: Cancelled by cancel scope
```
MCP connection fails during Agent initialization.

## Solutions

### 1. Immediate Fix - Monkey Patch Method

Add this before your Agent initialization code:

```python
import asyncio
import logging
from mcp_retry_wrapper import RetryConfig, RobustMcpSessionManager

# Set up logging to observe retry process
logging.basicConfig(level=logging.INFO)

# Global patch MCP session manager
def patch_mcp_session_manager():
    """Globally replace MCP session manager with retry version"""
    import google.adk.tools.mcp_tool.mcp_session_manager as mcp_module
    
    # Save original class
    original_manager = mcp_module.McpSessionManager
    
    # Create retry configuration
    retry_config = RetryConfig(
        max_retries=3,
        base_delay=2.0,
        max_delay=15.0,
        timeout=30.0,
        exponential_backoff=True
    )
    
    # Replace with robust version
    class PatchedMcpSessionManager(RobustMcpSessionManager):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, retry_config=retry_config, **kwargs)
        
        async def create_session(self):
            # Use retry version
            return await self.create_session_with_retry()
    
    # Apply patch
    mcp_module.McpSessionManager = PatchedMcpSessionManager
    print("✅ MCP retry patch applied")

# Call before Agent creation
patch_mcp_session_manager()

# Then create your Agent normally
# agent = Agent(...)
```

### 2. Configuration Optimization Method

Modify your Agent configuration:

```python
from mcp_retry_wrapper import MCP_PRODUCTION_CONFIG, RetryConfig

# 1. Increase MCP connection timeout
mcp_config = {
    "connection_timeout": 45.0,  # Increase to 45 seconds
    "read_timeout": 60.0,        # Read timeout 60 seconds
    "max_retries": 3,            # Maximum 3 retries
}

# 2. Set more lenient asyncio timeout
asyncio_config = {
    "default_timeout": 120.0,    # Default timeout 2 minutes
    "mcp_timeout": 60.0,         # MCP specific timeout 1 minute
}

# 3. Apply configuration when creating Agent
agent = Agent(
    model=your_model,
    tools=your_tools,
    # Add MCP related configuration
    **mcp_config
)
```

### 3. Environment Variable Configuration

Set environment variables to control retry behavior:

```bash
# In startup script or .env file
export MCP_MAX_RETRIES=5
export MCP_CONNECTION_TIMEOUT=45
export MCP_BASE_DELAY=2.0
export MCP_MAX_DELAY=30.0
export MCP_ENABLE_FALLBACK=true
```

Then read in code:

```python
import os

retry_config = RetryConfig(
    max_retries=int(os.getenv("MCP_MAX_RETRIES", 3)),
    timeout=float(os.getenv("MCP_CONNECTION_TIMEOUT", 30.0)),
    base_delay=float(os.getenv("MCP_BASE_DELAY", 1.0)),
    max_delay=float(os.getenv("MCP_MAX_DELAY", 15.0)),
)
```

### 4. Complete Agent Wrapper

Create a robust Agent wrapper:

```python
from mcp_retry_wrapper import RobustMcpSessionManager, RetryConfig
import asyncio
import logging

class RobustAgent:
    """Agent wrapper with MCP retry mechanism"""
    
    def __init__(self, original_agent, retry_config=None):
        self.agent = original_agent
        self.retry_config = retry_config or RetryConfig(
            max_retries=3,
            timeout=30.0,
            base_delay=2.0
        )
        self._setup_mcp_retry()
    
    def _setup_mcp_retry(self):
        """Set up MCP retry mechanism"""
        # Add more retry logic here
        pass
    
    async def run_with_retry(self, *args, **kwargs):
        """Run Agent with retry"""
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                return await self.agent.run(*args, **kwargs)
            except asyncio.CancelledError as e:
                if attempt < self.retry_config.max_retries:
                    delay = self.retry_config.base_delay * (2 ** attempt)
                    logging.warning(f"Agent run failed, retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise e
            except Exception as e:
                logging.error(f"Agent run error: {e}")
                raise e

# Usage
# original_agent = Agent(...)
# robust_agent = RobustAgent(original_agent)
# result = await robust_agent.run_with_retry(your_request)
```

## Diagnostic Tools

### 1. MCP Connection Test Script

```python
import asyncio
import httpx
from mcp_retry_wrapper import McpHealthChecker

async def diagnose_mcp_connection(mcp_url: str):
    """Diagnose MCP connection issues"""
    
    print(f"🔍 Diagnosing MCP connection: {mcp_url}")
    
    # 1. Basic network connectivity test
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(mcp_url)
            print(f"✅ HTTP connection normal: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTP connection failed: {e}")
        return False
    
    # 2. MCP health check
    health_checker = McpHealthChecker(mcp_url)
    is_healthy = await health_checker.is_healthy()
    print(f"{'✅' if is_healthy else '❌'} MCP service health status: {is_healthy}")
    
    # 3. Latency test
    try:
        import time
        start_time = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(mcp_url)
        latency = (time.time() - start_time) * 1000
        print(f"📊 Connection latency: {latency:.2f}ms")
    except Exception as e:
        print(f"❌ Latency test failed: {e}")
    
    return True

# Usage
# asyncio.run(diagnose_mcp_connection("http://your-mcp-server:port"))
```

### 2. Log Monitoring

```python
import logging

# Set up detailed MCP logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Specifically monitor MCP related logs
mcp_logger = logging.getLogger('mcp_retry_wrapper')
mcp_logger.setLevel(logging.INFO)

# Add file logging
file_handler = logging.FileHandler('mcp_connections.log')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
mcp_logger.addHandler(file_handler)
```

## Common Issues and Solutions

### Q: How many retries should be set?
**A:** 
- Development environment: 1-2 retries sufficient
- Production environment: 3-5 retries
- Unstable network environment: Can increase to 10

### Q: How to set timeout time?
**A:**
- Local MCP service: 10-15 seconds
- Remote MCP service: 30-45 seconds
- Public network MCP service: 60 seconds or more

### Q: How to handle completely unconnectable situations?
**A:** Use fallback mode:
```python
# Set up fallback tools or skip MCP tools
if not mcp_available:
    agent.tools = [basic_tool1, basic_tool2]  # Use basic tools
    logger.warning("MCP unavailable, using basic tool set")
```

### Q: How to determine if it's a temporary failure or configuration issue?
**A:** 
- Check error type: `CancelledError` is usually temporary
- Check retry pattern: If all retries fail at the same location, it might be a configuration issue
- Check network: Use diagnostic script to test basic connectivity

## Recommended Configurations

**Production Environment**:
```python
RetryConfig(
    max_retries=3,
    base_delay=2.0,
    max_delay=15.0,
    exponential_backoff=True,
    timeout=45.0
)
```

**Development Environment**:
```python
RetryConfig(
    max_retries=1,
    base_delay=1.0,
    max_delay=5.0,
    exponential_backoff=False,
    timeout=15.0
)
```
