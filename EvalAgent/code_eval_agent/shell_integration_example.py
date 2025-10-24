"""
Interactive Shell Tool Integration Example
Demonstrates how to use the run_interactive_shell tool in Agent
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

class InteractiveShellClient:
    """Interactive Shell Client for communicating with MCP server"""
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        
    async def run_shell(self, cmd: str = None, session_id: str = None, user_input: str = None) -> Dict[str, Any]:
        """Call interactive shell tool"""
        async with aiohttp.ClientSession() as session:
            data = {}
            if cmd:
                data['cmd'] = cmd
            if session_id:
                data['session_id'] = session_id  
            if user_input:
                data['user_input'] = user_input
                
            async with session.post(f"{self.base_url}/interactive-shell/run", json=data) as resp:
                result = await resp.json()
                return result
                
    async def kill_session(self, session_id: str) -> Dict[str, Any]:
        """Terminate shell session"""
        async with aiohttp.ClientSession() as session:
            data = {'session_id': session_id}
            async with session.post(f"{self.base_url}/interactive-shell/kill", json=data) as resp:
                result = await resp.json()
                return result

# Agent tool function definitions
async def run_interactive_shell(cmd: str = None, session_id: str = None, user_input: str = None) -> Dict[str, Any]:
    """
    Interactive shell tool function for Agent usage
    
    Args:
        cmd: Command to start new session
        session_id: ID to continue existing session
        user_input: Input to send to shell
        
    Returns:
        Dictionary containing session_id, output, waiting, finished
    """
    client = InteractiveShellClient()
    result = await client.run_shell(cmd=cmd, session_id=session_id, user_input=user_input)
    
    if result.get('status') == 'success':
        return {
            'session_id': result.get('session_id'),
            'output': result.get('output', ''),
            'waiting': result.get('waiting', False),
            'finished': result.get('finished', False)
        }
    else:
        return {
            'error': result.get('error', 'Unknown error'),
            'session_id': session_id,
            'output': '',
            'waiting': False,
            'finished': True
        }

async def kill_shell_session(session_id: str) -> Dict[str, Any]:
    """
    Session termination tool function for Agent usage
    """
    client = InteractiveShellClient()
    result = await client.kill_session(session_id)
    return result

# Usage examples
async def example_python_session():
    """Example: Python interactive session"""
    print("=== Python Interactive Session Example ===")
    
    # Start Python
    result = await run_interactive_shell(cmd="python")
    session_id = result['session_id']
    print(f"Started Python, session ID: {session_id}")
    print(f"Output: {result['output']}")
    
    # Execute Python code
    result = await run_interactive_shell(session_id=session_id, user_input="x = 10")
    print(f"Set variable x=10")
    print(f"Output: {result['output']}")
    
    result = await run_interactive_shell(session_id=session_id, user_input="print(f'x value is: {x}')")
    print(f"Print variable x")
    print(f"Output: {result['output']}")
    
    result = await run_interactive_shell(session_id=session_id, user_input="import math")
    print(f"Import math module")
    print(f"Output: {result['output']}")
    
    result = await run_interactive_shell(session_id=session_id, user_input="print(f'π value is: {math.pi}')")
    print(f"Use math module")
    print(f"Output: {result['output']}")
    
    # Exit Python
    result = await run_interactive_shell(session_id=session_id, user_input="exit()")
    print(f"Exited Python")
    print(f"Session finished: {result['finished']}")

async def example_bash_session():
    """Example: Bash interactive session"""
    print("\n=== Bash Interactive Session Example ===")
    
    # Start bash
    result = await run_interactive_shell(cmd="bash")
    session_id = result['session_id']
    print(f"Started Bash, session ID: {session_id}")
    
    # Check current directory
    result = await run_interactive_shell(session_id=session_id, user_input="pwd")
    print(f"Current directory: {result['output'].strip()}")
    
    # List files
    result = await run_interactive_shell(session_id=session_id, user_input="ls -la")
    print(f"File list:\n{result['output']}")
    
    # Create temporary directory
    result = await run_interactive_shell(session_id=session_id, user_input="mkdir -p /tmp/test_dir")
    print("Created temporary directory")
    
    # Change directory
    result = await run_interactive_shell(session_id=session_id, user_input="cd /tmp/test_dir")
    print("Changed to temporary directory")
    
    # Confirm directory change
    result = await run_interactive_shell(session_id=session_id, user_input="pwd")
    print(f"New current directory: {result['output'].strip()}")
    
    # Exit bash
    result = await run_interactive_shell(session_id=session_id, user_input="exit")
    print(f"Exited Bash, session finished: {result['finished']}")

# Agent Integration Guide
AGENT_INTEGRATION_GUIDE = """
# Agent Integration Interactive Shell Tool Guide

## 1. Add Tool Definitions to Agent Configuration

```python
from tools_definitions import INTERACTIVE_SHELL_TOOLS

# Add tools to Agent's tool list
agent_tools = INTERACTIVE_SHELL_TOOLS + other_tools
```

## 2. Implement Tool Call Functions in Agent

```python
import asyncio
from shell_integration_example import run_interactive_shell, kill_shell_session

class MyAgent:
    def __init__(self):
        self.active_sessions = {}  # Track active shell sessions
        
    async def call_tool(self, tool_name: str, parameters: dict):
        if tool_name == "run_interactive_shell":
            return await run_interactive_shell(**parameters)
        elif tool_name == "kill_shell_session":
            return await kill_shell_session(**parameters)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
```

## 3. Agent Usage Patterns

### Pattern 1: One-time Command Execution
```python
# Execute single command
result = await agent.call_tool("run_interactive_shell", {"cmd": "ls -la"})
```

### Pattern 2: Interactive Session
```python
# Start session
result = await agent.call_tool("run_interactive_shell", {"cmd": "python"})
session_id = result["session_id"]

# Continuous interaction
while not result["finished"]:
    if result["waiting"]:
        # Decide input based on context
        user_input = decide_input_based_on_context(result["output"])
        result = await agent.call_tool("run_interactive_shell", {
            "session_id": session_id,
            "user_input": user_input
        })
    else:
        # Wait for more output
        result = await agent.call_tool("run_interactive_shell", {
            "session_id": session_id
        })
```

## 4. Best Practices

1. **Session Management**: Track active session_ids to avoid confusion
2. **Error Handling**: Check returned error field and handle exceptions appropriately
3. **State Checking**: Use waiting and finished states to determine next actions
4. **Resource Cleanup**: Terminate sessions that are no longer needed
5. **Timeout Handling**: Set reasonable timeouts for long-running commands

## 5. Common Use Cases

- **Code Execution**: Python/Node.js/other interpreters
- **System Administration**: bash/zsh command execution
- **Database Operations**: mysql/psql clients
- **Development Tools**: git/npm/pip command line tools
"""

if __name__ == "__main__":
    # Run examples
    async def main():
        await example_python_session()
        await example_bash_session()
        print(AGENT_INTEGRATION_GUIDE)
    
    asyncio.run(main()) 