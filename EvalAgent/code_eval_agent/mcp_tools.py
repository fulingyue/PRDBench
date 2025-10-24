"""
Local Code Agent MCP Tools Definition
Provides Python interpreter, file operations, and system operations functionality
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
from pydantic import BaseModel
import logging
import pexpect
import asyncio
from aiohttp import web
from typing import Dict, Any, Optional
from code_eval_agent.interative_shell import step, terminate
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# Fix relative imports
try:
    from .config import (
        PYTHON_INTERPRETER_MCP_URL, 
        FILE_OPERATIONS_MCP_URL, 
        SYSTEM_OPERATIONS_MCP_URL,
        MCP_SSE_TIMEOUT,
        WORKSPACE_DIR,
        ALLOWED_EXTENSIONS,
        MAX_FILE_SIZE,
        SANDBOX_MODE,
        CURRENT_EXECUTION_ID,
        ENABLE_PATH_RESTRICTION
    )
except ImportError:
    # If relative import fails, use absolute import
    from config import (
        PYTHON_INTERPRETER_MCP_URL, 
        FILE_OPERATIONS_MCP_URL, 
        SYSTEM_OPERATIONS_MCP_URL,
        MCP_SSE_TIMEOUT,
        WORKSPACE_DIR,
        ALLOWED_EXTENSIONS,
        MAX_FILE_SIZE,
        SANDBOX_MODE,
        CURRENT_EXECUTION_ID,
        ENABLE_PATH_RESTRICTION
    )
SAFE_COMMANDS = ['ls', 'pwd', 'echo', 'cat', 'head', 'tail', 'grep', 'find', 'python', 'python3', 'chmod', 'cd', 'pytest']
        
# Data model definitions
class PythonCode(BaseModel):
    """Python code execution request"""
    code: str
    timeout: int = 30
    capture_output: bool = True

class FileOperation(BaseModel):
    """File operation request"""
    operation: str  # read, write, delete, list, copy, move
    path: str
    content: Optional[str] = None
    destination: Optional[str] = None

class SystemCommand(BaseModel):
    """System command execution request"""
    command: str
    timeout: int = 30
    capture_output: bool = True
    working_directory: Optional[str] = None

# Basic utility functions
def exit_loop(tool_context: ToolContext):
    """Exit loop when task is completed"""
    tool_context.actions.escalate = True
    return {"status": "completed"}

def create_workspace(tool_context: ToolContext, workspace_name: Optional[str] = None, create_venv: bool = True):
    """
    Create workspace
    
    Args:
        tool_context: Tool context
        workspace_name: Workspace name, if None use current execution ID
        create_venv: Whether to create virtual environment, default True
    
    Returns:
        dict: Dictionary containing workspace information
    """
    if workspace_name is None:
        workspace_name = CURRENT_EXECUTION_ID
    
    workspace_path = Path(WORKSPACE_DIR) / workspace_name
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    # Create basic directory structure
    (workspace_path / "src").mkdir(exist_ok=True)
    (workspace_path / "tests").mkdir(exist_ok=True)
    (workspace_path / "data").mkdir(exist_ok=True)
    (workspace_path / "docs").mkdir(exist_ok=True)
    
    result = {
        "workspace_path": str(workspace_path),
        "workspace_name": workspace_name,
        "status": "created",
        "directories": ["src", "tests", "data", "docs"]
    }
    
    # Create virtual environment
    if create_venv:
        try:
            venv_path = workspace_path / "venv"
            
            # 创建虚拟环境
            subprocess.run(
                ['python', '-m', 'venv', str(venv_path)],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Generate activation script
            activate_script = workspace_path / "activate_venv.sh"
            with open(activate_script, 'w', encoding='utf-8') as f:
                f.write(f"""#!/bin/bash
# Virtual environment activation script
echo "Activating virtual environment: {venv_path}"
source "{venv_path}/bin/activate"
echo "Virtual environment activated, Python path: $(which python)"
echo "Current working directory: $(pwd)"
""")
            
            
            os.chmod(activate_script, 0o755)
            
            # Create requirements.txt template
            requirements_file = workspace_path / "requirements.txt"
            with open(requirements_file, 'w', encoding='utf-8') as f:
                f.write("# Project dependencies\n# Example:\n# requests==2.31.0\n# pandas==2.0.3\n")
            
            # 创建 .gitignore 文件
            gitignore_file = workspace_path / ".gitignore"
            with open(gitignore_file, 'w', encoding='utf-8') as f:
                f.write("""# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Data files
data/*.csv
data/*.json
""")
            
            result.update({
                "venv_created": True,
                "venv_path": str(venv_path),
                "activate_script": str(activate_script),
                "requirements_file": str(requirements_file),
                "gitignore_file": str(gitignore_file)
            })
            
            logger.info(f"Virtual environment created successfully: {venv_path}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e}")
            result.update({
                "venv_created": False,
                "venv_error": str(e)
            })
        except Exception as e:
            logger.error(f"Error occurred while creating virtual environment: {e}")
            result.update({
                "venv_created": False,
                "venv_error": str(e)
            })
    else:
        result["venv_created"] = False
    
    return result

def list_workspace(tool_context: ToolContext, workspace_name: Optional[str] = None):
    """
    List the files and directories in the workspace.
    
    Args:
        tool_context: Tool context
        workspace_name: The name of the workspace, if None, use the current execution ID.
    
    Returns:
        dict: A dictionary containing the list of files and directories in the workspace.
    """
    if workspace_name is None:
        workspace_name = CURRENT_EXECUTION_ID
    
    workspace_path = Path(WORKSPACE_DIR) / workspace_name
    
    if not workspace_path.exists():
        return {"error": "The workspace does not exist！"}
    
    files = []
    for item in workspace_path.rglob("*"):
        if item.is_file():
            files.append({
                "path": str(item.relative_to(workspace_path)),
                "size": item.stat().st_size,
                "type": "file"
            })
        elif item.is_dir():
            files.append({
                "path": str(item.relative_to(workspace_path)),
                "type": "directory"
            })
    
    return {
        "workspace_path": str(workspace_path),
        "workspace_name": workspace_name,
        "files": files
    }

def validate_write_path(file_path: str) -> bool:
    """Validate if file path is safe for writing"""
    
    if ENABLE_PATH_RESTRICTION:
        # allowed_paths is the root directory, allowed path list: {WORKSPACE_DIR}/{number}/reports
        allowed_paths = [os.path.join(WORKSPACE_DIR, str(i), 'reports') for i in range(1, 51)]
        logger.warning(f"checking write path: {file_path}, allowed_paths: {WORKSPACE_DIR}/*/reports")
        if any(os.path.commonpath([file_path, allowed_path]) == allowed_path for allowed_path in allowed_paths):
            return True
        else:
            return False
    else:
        return True


def validate_read_file_path(file_path: str) -> bool:
    """verify if the file path is safe"""
    logger.warning(f"checking read path: {file_path}, allowed_paths: {WORKSPACE_DIR}")
    # Skip security check for tmp directory
    if file_path.startswith("/tmp"):
        return True
    
    # Allow relative paths in current directory and subdirectories
    if not file_path.startswith("/"):
        return True
    
    if SANDBOX_MODE:
        # In sandbox mode, only allow access to files within workspace
        workspace_path = Path(WORKSPACE_DIR).resolve()
        file_path_resolved = Path(file_path).resolve()
        
        # Check if file is within workspace or tmp directory
        # check if the file is within the workspace or tmp directory
        if (str(file_path_resolved).startswith(str(workspace_path)) or 
            str(file_path_resolved).startswith("/tmp")):
            return True
        else:
            return False
    
    return True

def read_file(tool_context: ToolContext, file_path: str):
    """
    Read the content of the file.
    
    Args:
        tool_context: Tool context
        file_path: The path of the file.
    
    Returns:
        dict: A dictionary containing the content of the file.
    """
    if not validate_read_file_path(file_path):
        return {"error": "The file path is not allowed to be read! Please concentrate on the file path in the project directory!"}
    
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": "File does not exist"}
        
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return {"error": "File is too large"}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "file_path": str(file_path),
            "content": content,
            "size": len(content)
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

def write_file(tool_context: ToolContext, file_path: str, content: str):
    """
    Write the content to the file.
    
    Args:
        tool_context: Tool context
        file_path: The path of the file (required)
        content: The content to be written (required)
    
    Returns:
        dict: A dictionary containing the result of the operation.
    """
    if not validate_write_path(file_path):
        logger.warning(f"file_path: {file_path} is not allowed to be modified")
        return {"error": "This file is not allowed to be modified! If the src code could not handle the case, you can give 0 as the result. You can not modify the code file and metric files."}
    
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {
            "file_path": str(file_path),
            "status": "written",
            "size": len(content)
        }
    except Exception as e:
        return {"error": f"Failed to write file: {str(e)}"}

def delete_file(tool_context: ToolContext, file_path: str):
    """
    Delete the file.
    
    Args:
        tool_context: Tool context
        file_path: The path of the file.
    
    Returns:
        dict: A dictionary containing the result of the operation.
    """
    if not validate_write_path(file_path):
        return {"error": "This file is not allowed to be deleted! You can not delete the code file and metric files."}
    
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": "File does not exist"}
        
        file_path.unlink()
        return {
            "file_path": str(file_path),
            "status": "deleted"
        }
    except Exception as e:
        return {"error": f"Failed to delete file: {str(e)}"}

def activate_venv(tool_context: ToolContext, workspace_name: Optional[str] = None):
    """
    Activate the virtual environment of the workspace.
    
    Args:
        tool_context: Tool context
        workspace_name: The name of the workspace, if None, use the current execution ID.
    
    Returns:
        dict: A dictionary containing the result of the activation.
    """
    if workspace_name is None:
        workspace_name = CURRENT_EXECUTION_ID
    
    workspace_path = Path(WORKSPACE_DIR) / workspace_name
    venv_path = workspace_path / "venv"
    
    if not venv_path.exists():
        return {"error": "Virtual environment does not exist, please create virtual environment first"}
    
    try:
        # Get virtual environment Python interpreter path
        if os.name == 'nt':  # Windows
            python_path = venv_path / "Scripts" / "python.exe"
        else:  # Unix/Linux/macOS
            python_path = venv_path / "bin" / "python"
        
        if not python_path.exists():
            return {"error": "Virtual environment Python interpreter does not exist"}
        
        # Check packages in virtual environment
        result = subprocess.run(
            [str(python_path), '-m', 'pip', 'list'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "workspace_name": workspace_name,
            "venv_path": str(venv_path),
            "python_path": str(python_path),
            "status": "activated",
            "installed_packages": result.stdout if result.returncode == 0 else "Unable to get package list"
        }
        
    except Exception as e:
        return {"error": f"Failed to activate virtual environment: {str(e)}"}

def execute_python_code(tool_context: ToolContext, code: str, timeout: int = 30, use_venv: bool = True):
    """
    Execute the Python code.
    
    Args:
        tool_context: Tool context
        code: The Python code to be executed (required)
        timeout: The timeout for the execution (seconds), default 30 seconds
        use_venv: Whether to use the virtual environment, default True
    
    Returns:
        dict: A dictionary containing the result of the execution.
    """
    try:
        # Determine which Python interpreter to use
        if use_venv:
            workspace_path = Path(WORKSPACE_DIR) / CURRENT_EXECUTION_ID
            venv_path = workspace_path / "venv"
            
            if venv_path.exists():
                if os.name == 'nt':  # Windows
                    python_executable = str(venv_path / "Scripts" / "python.exe")
                else:  # Unix/Linux/macOS
                    python_executable = str(venv_path / "bin" / "python")
                
                if not Path(python_executable).exists():
                    python_executable = 'python'  # Fall back to system Python
            else:
                python_executable = 'python'  # Fall back to system Python
        else:
            python_executable = 'python'
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Execute code
        result = subprocess.run(
            [python_executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_DIR
        )
        
        # Clean up temporary file
        os.unlink(temp_file)
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "execution_time": "completed",
            "python_executable": python_executable,
            "used_venv": use_venv and venv_path.exists() if use_venv else False
        }
    except subprocess.TimeoutExpired:
        return {"error": "Code execution timeout"}
    except Exception as e:
        return {"error": f"Code execution failed: {str(e)}"}

def run_system_command(tool_context: ToolContext, command: str, timeout: int = 30):
    """
    Run the system command.
    
    Args:
        tool_context: Tool context
        command: The system command to be executed
        timeout: The timeout for the execution (seconds), default 30 seconds
    
    Returns:
        dict: A dictionary containing the result of the execution.
    """
    if SANDBOX_MODE:
        # only allow safe commands in sandbox mode
        safe_commands = SAFE_COMMANDS
        if not any(cmd in command for cmd in safe_commands):
            return {"error": "The command you executed is not allowed in sandbox mode; Safe command list: " + str(safe_commands)}
    try:
        logger.info(f"Executing system command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORKSPACE_DIR
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command execution timeout"}
    except Exception as e:
        return {"error": f"Command execution failed: {str(e)}"}

def interactive_system_command(
    tool_context: ToolContext,
    command: str,
    inputs: Optional[List[str]] = None,
    timeout: int = 15
):
    """
    Run the system command interactively, support input and output interaction.

    Args:
        tool_context: Tool context
        command: The system command to be executed
        inputs: The content to be input to the command (string list, each element enter once)
        timeout: The timeout for the execution (seconds)

    Returns:
        dict: A dictionary containing the result of the execution.
    """
    if SANDBOX_MODE:
        safe_commands = SAFE_COMMANDS
        if not any(cmd in command for cmd in safe_commands):
            return {"error": "Command is not allowed in sandbox mode"}

    try:
        logger.info(f"Interactive execution of system command: {command}")
        child = pexpect.spawn(command, cwd=WORKSPACE_DIR, timeout=timeout, encoding='utf-8')
        output = ""
        if inputs:
            for inp in inputs:
                child.expect([pexpect.TIMEOUT, pexpect.EOF], timeout=1)
                child.sendline(inp)
        child.expect(pexpect.EOF)
        output = child.before
        return_code = child.exitstatus
        return {
            "stdout": output,
            "stderr": "",  # pexpect doesn't directly distinguish stderr
            "return_code": return_code
        }
    except pexpect.TIMEOUT:
        return {"error": "Command execution timeout"}
    except Exception as e:
        return {"error": f"Interactive command execution failed: {str(e)}"}

def run_interactive_python_code(tool_context: ToolContext, cmd: str, session_id: Optional[str] = None, timeout: int = 30):
    """
    Run a interactive Python code session.
    
    The first time to call, you need to provide the code parameter to start a new session, and then provide the session_id to continue the previous session.
    If you need to input content to the Python code, provide the user_input parameter.
    
    Args:
        tool_context: Tool context
        cmd: The Python code to be executed
        session_id: The session ID, for continuing the previous session.
        timeout: The timeout for the execution (seconds)
    Returns:
        dict: A dictionary containing the result of the execution.
    """
    session_id = None
    try:
        result = step(
            cmd=cmd,
            session_id=session_id,
            user_input=user_input
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "session_id": session_id,
            "output": "",
            "waiting": False,
            "finished": True
        }

def start_interative_shell(tool_context: ToolContext, cmd: str = "bash") -> Dict[str, Any]:
    """
    Start a interactive shell session.
    
    Args:
        tool_context: Tool context
        cmd: The shell command to be executed
    Returns:
        dict: A dictionary containing the result of the execution.
    """
    session_id = None
    try:
        result = step(
            cmd=cmd,
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "session_id": session_id,
            "output": session_id,
            "waiting": False,
            "finished": True
        }

IS_IN_PYTHON_ENV = False

def run_interactive_shell(tool_context: ToolContext, session_id: Optional[str] = None, user_input: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a interactive shell session.
    
    The first time to call, you need to provide the cmd parameter to start a new session, and then provide the session_id to continue the previous session.
    If you need to input content to the shell, provide the user_input parameter.
    
    参数:
        session_id (str, optional): The session ID, for continuing the previous session.
        user_input (str, optional): The content to be input to the shell.
        
    Returns:
        Dict[str, Any]: A dictionary containing the result of the execution.
            - session_id: str, The session ID
            - output: str, The output of the shell
            - waiting: bool, Whether to wait for input
            - finished: bool, Whether the session is finished
    """
    # Get current session state
    session_state = getattr(tool_context, 'python_env_state', {})
    if session_id not in session_state:
        session_state[session_id] = False
    is_in_python = session_state[session_id]
    
    # Check command safety
    if is_in_python and user_input:
        safe_commands = SAFE_COMMANDS
        current_command = user_input.split()[0] if user_input else ''
        if not any(cmd in current_command for cmd in safe_commands):
            return {"error": "The command you executed is not allowed in sandbox mode; Safe command list: " + str(safe_commands)}
    
    # Update Python environment state
    if user_input and user_input.startswith("python"):
        session_state[session_id] = True
    elif user_input == "exit":
        session_state[session_id] = False
    
    # Save state back to context
    setattr(tool_context, 'python_env_state', session_state)
    
    try:
        result = step(
            session_id=session_id,
            user_input=user_input
        )
        return result
    except Exception as e:
        return {
            "error": str(e),
            "session_id": session_id,
            "output": "",
            "waiting": False,
            "finished": True
        }

def kill_shell_session(tool_context: ToolContext, session_id: str) -> Dict[str, Any]:
    """
    Terminate a shell session.
    
    Args:
        session_id (str): The session ID to be terminated
        
    Returns:
        Dict[str, Any]: The result of the operation
    """
    try:
        terminate(session_id)
        return {
            "message": f"Session {session_id} has been terminated",
            "output": f"Session {session_id} has been terminated"
        }
    except Exception as e:
        return {
            "error": str(e),
            "output": "",
        }

def deal_graph(tool_context: ToolContext, graph_path_list: list, prompt: str):
    """
    Interact with the multi-modal LLM and get the reply.
    
    Args:
        graph_path_list(list): The list of image file paths
        prompt(str): The prompt of the user, need to describe the requirement in detail, and describe the pictures in the order of the image file path list (for example, whether the first picture is consistent with the type of the second picture)
    
    Returns:
        dict: The reply content of the model
    """
    for graph_path in graph_path_list:
        if not validate_read_file_path(graph_path):
            return {"error": "This file is not allowed to be read!"}
    try:
        import base64
        import requests
        import json
        import os
        
        # API configuration
        api_key = 'https://api.example.com/v1/openai/native'
        api_base = 'your-api-key-here'
        model_name = "model_name"
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        url = f'{api_base}/chat/completions'
        
        def encode_image(image_path):
            """Encode image file to base64 string"""
            try:
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode("utf-8")
            except Exception as e:
                return {"error": f"Failed to encode image {image_path}: {e}"}

        
        # Build message content
        content = [{"type": "text", "text": prompt}]
        
        # Process image list
        for graph_path in graph_path_list:
            if not os.path.exists(graph_path):
                return {"error": f"Image file does not exist: {graph_path}"}

                
            # Encode image
            base64_image = encode_image(graph_path)
            if base64_image is None:
                continue
                
            # Get file extension to determine MIME type
            file_ext = os.path.splitext(graph_path)[1].lower()
            mime_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg', 
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_type_map.get(file_ext, 'image/jpeg')
            
            # Add image to content
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}"
                }
            })
        
        # Build request payload
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.1
        }
        
        try:

            # Send request
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    reply_content = result['choices'][0]['message']['content']
                    return {"MLLM_reply_content": reply_content}
                else:
                    return {"error": "API response format exception"}
            else:
                error_info = response.text
                return {"error": f"API request failed: {response.status_code} - {error_info}"}
                
        except requests.exceptions.Timeout:
            return {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Request exception: {e}"}
        except Exception as e:
            return {"error": f"Unknown error: {e}"}
    except Exception as e:
        return {"error": "Image parsing failed"}
   
def judge(tool_context, context: str, entry_command: str, input_file: Optional[str] = None):
    """
    Run the program and simulate the user interaction, record the interaction process and output result.
    If the program does not exit automatically after the input ends, send Ctrl+C to force interrupt.
    When KeyboardInterrupt is captured, it is also considered successful.

    Args:
        tool_context: Tool context
        context: The expected output description and test requirements (only used for information transmission, not for judgment)
        entry_command: The entry command of the program (e.g. "python main.py")
        input_file: The path of the file containing the simulated user input (e.g. "a.in")

    Returns:
        dict: A dictionary containing the test result and interaction record
    """
    import os
    import time
    import pexpect
    from typing import Optional

    class CustomLogger:
        def __init__(self, file):
            self.file = file

        def write(self, data):
            for line in data.splitlines(True):
                self.file.write("program: " + line)
            self.file.flush()

        def flush(self):
            self.file.flush()

    log_file_path = 'pexpect_interact.log'
    result = {
        "success": False,
        "log": '',
        "error": None
    }
    work_dir = WORKSPACE_DIR

    if input_file and not os.path.exists(input_file):
        result["error"] = f"Input file {input_file} does not exist, please check the path and call again."
        return result

    input_lines = []
    if input_file and os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as infile:
            input_lines = [line.rstrip('\n') for line in infile]

    child = pexpect.spawn(entry_command, cwd=work_dir, timeout=30, encoding='utf-8')

    with open(log_file_path, 'w', encoding='utf-8') as logfile:
        logger = CustomLogger(logfile)
        child.logfile_read = logger

        def send_user_line(line):
            logfile.write('user: ' + line + '\n')
            logfile.flush()
            child.sendline(line)

        try:
            logfile.flush()
            time.sleep(0.2)
            for line in input_lines:
                send_user_line(line.rstrip('\n'))
                time.sleep(0.2)

            try:
                child.expect(pexpect.EOF, timeout=10)
            except pexpect.TIMEOUT:
                logfile.write('user: <Ctrl+C>\n')
                logfile.flush()
                child.sendcontrol('c')
                try:
                    child.expect(pexpect.EOF, timeout=3)
                except pexpect.TIMEOUT:
                    child.close(force=True)
                    result["error"] = "The program did not end normally, Ctrl+C was sent to force interrupt."

            child.close()

            if child.exitstatus == 0 or child.exitstatus==130 or 'keyboardInterrupt' in last_output:
                result["success"] = True
            else:
                last_output = child.before if hasattr(child, 'before') else ''
                if not result["error"]:
                    result["error"] = f"Program exit status code: {child.exitstatus}\nLast output: {last_output}"
        except pexpect.TIMEOUT:
            result["error"] = f"Program execution timed out"
        except Exception as e:
            import traceback
            print(Exception)
            tb_lines = traceback.format_exc()
            if isinstance(e, KeyboardInterrupt):
                result["success"] = True
                result["error"] = None
            #result["error"] = tb_lines

    with open(log_file_path, 'r', encoding='utf-8') as logfile:
        result["log"] = logfile.read()
    return result



# Tool definitions
TOOL_DEFINITIONS = {
    "run_interactive_shell": {
        "name": "run_interactive_shell",
        "description": """
        Run an interactive shell session. This tool allows the model to interact with the shell interactively.
        
        Usage:
        1. When using for the first time, provide the cmd parameter to start a new shell session
        2. Get the returned session_id for subsequent interactions
        3. If the shell is waiting for input (waiting=True), you can provide user_input to send input
        4. Use the returned session_id to continue interacting with the same shell session
        5. When finished=True, the session ends
        
        Examples:
        - Start new session: run_interactive_shell(cmd="python")
        - Continue session: run_interactive_shell(session_id="xxx", user_input="print('hello')")
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "cmd": {
                    "type": "string",
                    "description": "Shell command to execute, only needed for first call"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for continuing previous session"
                },
                "user_input": {
                    "type": "string",
                    "description": "Input content to send to shell"
                }
            }
        }
    },
    "kill_shell_session": {
        "name": "kill_shell_session",
        "description": "Force terminate a running shell session",
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
    },
    'judge': {
        'name': 'judge',
        'description': 'Run program and simulate user interaction, record interaction process and output result',
        'parameters': {
            'type': 'object',
            'properties': {
                'context': {
                    'type': 'string',
                    'description': 'Expected output description and test requirements'
                },
                'entry_command': {
                    'type': 'string',
                    'description': 'Program entry command'
                },
                'input_file': {
                    'type': 'string',
                    'description': 'File path containing simulated user input'
                }
            },
            'required': ['context', 'entry_command']
        }
    }
}

# 创建MCP工具集
def create_python_interpreter_toolset():
    """Create Python interpreter MCP toolset"""
    return MCPToolset(
        connection_params=SseServerParams(
            url=PYTHON_INTERPRETER_MCP_URL,
            sse_read_timeout=MCP_SSE_TIMEOUT
        )
    )

def create_file_operations_toolset():
    """Create file operations MCP toolset"""
    return MCPToolset(
        connection_params=SseServerParams(
            url=FILE_OPERATIONS_MCP_URL,
            sse_read_timeout=MCP_SSE_TIMEOUT
        )
    )

def create_system_operations_toolset():
    """Create system operations MCP toolset"""
    return MCPToolset(
        connection_params=SseServerParams(
            url=SYSTEM_OPERATIONS_MCP_URL,
            sse_read_timeout=MCP_SSE_TIMEOUT
        )
    )



# Basic tools list - remove duplicates, ensure each tool appears only once
BASIC_TOOLS = [
    exit_loop,
    create_workspace,
    list_workspace,
    read_file,
    write_file,
    delete_file,
    activate_venv,
    execute_python_code,
    run_system_command,
    interactive_system_command,
    run_interactive_shell,
    judge,  # Add Judge tool
    deal_graph
    # interactive_python_code,
]

# MCP toolsets - temporarily commented out to avoid tool duplication issues
# MCP_TOOLS = [
#     create_python_interpreter_toolset(),
#     create_file_operations_toolset(),
#     create_system_operations_toolset()
# ]

# All tools - temporarily use only basic tools
ALL_TOOLS = BASIC_TOOLS 

