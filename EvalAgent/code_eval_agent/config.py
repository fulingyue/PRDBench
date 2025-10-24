import os
import uuid
from datetime import datetime
from google.adk.models.lite_llm import LiteLlm
from lite_llm_wrapper import LiteLlmWithSleep

# Basic model configuration
BASIC_MODEL =LiteLlmWithSleep(
        model="openai/gemini-2.5-pro",
        api_base='https://api.example.com/v1/openai/native',
        api_key='your-api-key-here',
        max_tokens=32768,
        temperature=0.1
    )

friday_model_dict = {
    "claude_3_7_sonnet": LiteLlmWithSleep(
        model="openai/claude-3-7-sonnet-20250219",
        api_base='https://api.example.com/v1/openai/native',
        api_key='your-api-key-here',
        # max_completion_tokens=32000,
        max_tokens_threshold=131072-32000-1000,
        enable_compression=True,
        temperature=0.1
    )
}



# Generate random execution ID
def generate_execution_id():
    """Generate unique execution ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"exec_{timestamp}_{unique_id}"

# Current execution ID
CURRENT_EXECUTION_ID = generate_execution_id()

# Local MCP server configuration
# PYTHON_INTERPRETER_MCP_URL = "http://localhost:9001/python-interpreter"
# FILE_OPERATIONS_MCP_URL = "http://localhost:8002/file-operations"
# SYSTEM_OPERATIONS_MCP_URL = "http://localhost:8003/system-operations"

import os

# Port environment variable names
PYTHON_INTERPRETER_PORT = os.getenv("PYTHON_INTERPRETER_PORT", "9001")
FILE_OPERATIONS_PORT = os.getenv("FILE_OPERATIONS_PORT", "8002")
SYSTEM_OPERATIONS_PORT = os.getenv("SYSTEM_OPERATIONS_PORT", "8003")

PYTHON_INTERPRETER_MCP_URL = f"http://localhost:{PYTHON_INTERPRETER_PORT}/python-interpreter"
FILE_OPERATIONS_MCP_URL = f"http://localhost:{FILE_OPERATIONS_PORT}/file-operations"
SYSTEM_OPERATIONS_MCP_URL = f"http://localhost:{SYSTEM_OPERATIONS_PORT}/system-operations"


# MCP connection configuration
MCP_SSE_TIMEOUT = 30
MAX_ITERATIONS = 10

# System configuration
SYSTEM_NAME = "LocalCodeAgent"
BASE_WORKSPACE_DIR = "/tmp/code_agent_workspace"

# Support environment variable override for workspace directory, convenient for local testing
# Usage: export CODE_AGENT_WORKSPACE_DIR=/path/to/your/workspace
WORKSPACE_DIR = os.getenv('CODE_AGENT_WORKSPACE_DIR', BASE_WORKSPACE_DIR)

# If relative path, convert to absolute path
if not os.path.isabs(WORKSPACE_DIR):
    WORKSPACE_DIR = os.path.abspath(WORKSPACE_DIR)

# Security configuration
ALLOWED_EXTENSIONS = ['.py', '.txt', '.md', '.json', '.yaml', '.yml', '.csv', '.sql', '.in', '.jsonl']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SANDBOX_MODE = True


# Whether to enable path restriction
ENABLE_PATH_RESTRICTION = os.getenv('ENABLE_PATH_RESTRICTION', 'true').lower() == 'true'

print(f"🚀 Current execution ID: {CURRENT_EXECUTION_ID}")
print(f"📁 Workspace path: {WORKSPACE_DIR}")


