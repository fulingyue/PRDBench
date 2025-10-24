"""
Tool Definitions File
Defines all tools that Agent can use and their usage methods
"""

# Interactive Shell Tool Definitions
INTERACTIVE_SHELL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_interactive_shell",
            "description": """
Run an interactive shell session. This tool allows you to interact with shell.

Usage:
1. When using for the first time, provide cmd parameter to start a new shell session
2. Get the returned session_id, for subsequent interactions
3. If shell is waiting for input (waiting=True), you can provide user_input to send input
4. Use the returned session_id to continue interacting with the same shell session
5. When finished=True, the session ends

Example workflow:
- Start Python: run_interactive_shell(cmd="python")
- Continue interaction: run_interactive_shell(session_id="xxx", user_input="print('hello')")
- Start bash: run_interactive_shell(cmd="bash")
- Execute command: run_interactive_shell(session_id="yyy", user_input="ls -la")

Note:
- Each session is independent with its own environment and state
- Sessions maintain all historical state (variables, directories, etc.)
- If session has issues, you can use kill_shell_session to force termination
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {
                        "type": "string",
                        "description": "Shell command to execute, only needed on first call. Examples: 'python', 'bash', 'node', 'mysql -u root -p', etc."
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for continuing previous session. Not needed for first call."
                    },
                    "user_input": {
                        "type": "string",
                        "description": "Text to send to shell (newline automatically appended). Use when previous call returned {\"waiting\": True}."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "kill_shell_session",
            "description": "Force terminate a running shell session. Use when session has issues or is no longer needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to terminate"
                    }
                },
                "required": ["session_id"]
            }
        }
    }
]

# All tool definitions
ALL_TOOLS = INTERACTIVE_SHELL_TOOLS

# Tool usage guide
TOOL_USAGE_GUIDE = """
# Interactive Shell Tool Usage Guide

## Basic Concepts
- Each shell session has a unique session_id
- Sessions maintain state: variables, current directory, environment, etc.
- Supports any program that can run on the command line

## Common Usage Scenarios

### 1. Python Interactive Programming
```
# Start Python
result = run_interactive_shell(cmd="python")
session_id = result["session_id"]

# Execute Python code
run_interactive_shell(session_id=session_id, user_input="x = 10")
run_interactive_shell(session_id=session_id, user_input="print(x * 2)")
```

### 2. System Management
```
# Start bash
result = run_interactive_shell(cmd="bash")
session_id = result["session_id"]

# Execute system commands
run_interactive_shell(session_id=session_id, user_input="cd /tmp")
run_interactive_shell(session_id=session_id, user_input="ls -la")
run_interactive_shell(session_id=session_id, user_input="pwd")
```

### 3. Database Operations
```
# Connect to MySQL
result = run_interactive_shell(cmd="mysql -u root -p")
session_id = result["session_id"]

# Enter password
run_interactive_shell(session_id=session_id, user_input="password123")
# Execute SQL
run_interactive_shell(session_id=session_id, user_input="SHOW DATABASES;")
```

## Return Value Description
```json
{
    "session_id": "Session ID",
    "output": "Program output content",
    "waiting": true/false,  // Whether waiting for input
    "finished": true/false  // Whether session ended
}
```

## Best Practices
1. Always check waiting status to decide whether to provide input
2. Save session_id for subsequent interactions
3. Don't use the same session_id after session ends (finished=True)
4. Force terminate sessions with issues using kill_shell_session
5. Be patient with long-running commands
"""
