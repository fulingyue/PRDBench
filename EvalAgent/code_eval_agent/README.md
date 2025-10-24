# Local Code Agent

Local code agent system based on Google ADK, supporting Python interpreter, file operations and other functions, all tools are provided in the form of local MCP.

## 🚀 Features

### Core Functions
- **Complete code development workflow**: Planning, writing, testing, debugging, summary
- **Quick code execution**: Mathematical calculations, data processing, quick verification
- **File management**: Create, read, modify, delete files and directories
- **Workspace management**: Isolated development environment

### Security Features
- **Sandbox environment**: All code execution is in a secure sandbox environment
- **File operation restrictions**: Can only access files within the specified workspace
- **System command whitelist**: Only allows execution of safe system commands
- **File type restrictions**: Only allows operation of safe file types

### MCP Tool Support
- **Python interpreter**: Execute Python code snippets
- **File operations**: Complete file system operations
- **System operations**: Safe system command execution

## 📁 Project Structure

```
code_agent_local/
├── __init__.py              # Package initialization file
├── config.py                # Configuration file
├── agent.py                 # Agent system main file
├── mcp_tools.py             # MCP tool definitions
├── mcp_servers.py           # MCP server implementation
├── main.py                  # Main program entry
├── test_agent.py            # Test file
└── README.md                # Documentation
```

## 🛠️ Installation and Configuration

### 1. Install Dependencies

Ensure the main project dependencies are installed:

```bash
pip install -r requirements.txt
```

### 2. Configure Model

Edit the `config.py` file to configure your model parameters:

```python
BASIC_MODEL = LiteLlm(
    model="your-model-name",
    api_base='your-api-base',
    api_key='your-api-key'
)
```

### 3. Create Workspace

The system will automatically create a workspace in `/tmp/code_agent_workspace`, you can also modify `WORKSPACE_DIR` in `config.py` to specify other locations.

## 🚀 Usage

### 1. Start MCP Server

First start the local MCP server:

```bash
cd examples/code_agent_local
python mcp_servers.py
```

This will start the following services:
- Python interpreter service (port 9001)
- File operations service (port 8002)

### 2. Run Main Program

Run the main program in another terminal:

```bash
# Interactive mode
python main.py

# Execute single task
python main.py -t "Create a calculator program"

# Show examples
python main.py --examples

# Verbose output mode
python main.py --verbose
```

### 3. Run Tests

Verify that the system is working properly:

```bash
python test_agent.py
```

## 💡 Usage Examples

### Code Development Example

```
💬 Please enter your request: Create a simple calculator program

🔄 Processing: Create a simple calculator program

✅ Processing completed:
Status: success
Response: Local Code Agent has processed your request: Create a simple calculator program
```

### Code Execution Example

```
💬 Please enter your request: Calculate the first 10 terms of Fibonacci sequence

🔄 Processing: Calculate the first 10 terms of Fibonacci sequence

✅ Processing completed:
Status: success
Response: Local Code Agent has processed your request: Calculate the first 10 terms of Fibonacci sequence
```

### File Management Example

```
💬 Please enter your request: Create a new workspace and list files

🔄 Processing: Create a new workspace and list files

✅ Processing completed:
Status: success
Response: Local Code Agent has processed your request: Create a new workspace and list files
```

## 🔧 Configuration Options

### Main Configuration Items

The following options can be configured in `config.py`:

```python
# Model configuration
BASIC_MODEL = LiteLlm(...)

# MCP server configuration
PYTHON_INTERPRETER_MCP_URL = "http://localhost:9001/python-interpreter"
FILE_OPERATIONS_MCP_URL = "http://localhost:8002/file-operations"

# System configuration
WORKSPACE_DIR = "/tmp/code_agent_workspace"
MAX_ITERATIONS = 10

# Security configuration
ALLOWED_EXTENSIONS = ['.py', '.txt', '.md', '.json', '.yaml', '.yml', '.csv', '.sql']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SANDBOX_MODE = True
```

### Command Line Options

```bash
python main.py [options]

Options:
  -t, --task TEXT        Task to execute
  --examples             Show usage examples
  --workspace PATH       Workspace directory
  --verbose              Verbose output mode
  -h, --help             Show help information
```

## 🔒 Security Notes

### Sandbox Environment
- All code execution is in an isolated sandbox environment
- Cannot access system critical files and directories
- Network access is restricted

### File Operation Security
- Can only access files within the specified workspace
- File type whitelist restrictions
- File size limits to prevent resource abuse

### System Command Security
- Only allows execution of safe system commands
- Command whitelist mechanism
- Execution timeout limits

## 🐛 Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   ```
   Error: MCP server connection failed
   Solution: Ensure mcp_servers.py is running
   ```

2. **Model Configuration Error**
   ```
   Error: Invalid model configuration
   Solution: Check model configuration in config.py
   ```

3. **Permission Error**
   ```
   Error: Insufficient file permissions
   Solution: Check workspace directory permissions
   ```

### Debug Mode

Enable verbose log output:

```bash
python main.py --verbose
```

### Test System

Run complete tests:

```bash
python test_agent.py
```

## 📚 API Reference

### Main Classes

#### LocalCodeAgentSystem
Main agent system class that manages all sub-agents.

#### LocalCodeAgentCLI
Command line interface class that provides user interaction functionality.

### Main Tools

#### Basic Tools
- `create_workspace()`: Create workspace
- `list_workspace()`: List workspace contents
- `read_file()`: Read file
- `write_file()`: Write file
- `delete_file()`: Delete file
- `execute_python_code()`: Execute Python code
- `run_system_command()`: Run system command

#### MCP Tools
- `create_python_interpreter_toolset()`: Python interpreter toolset
- `create_file_operations_toolset()`: File operations toolset

## 🤝 Contributing

Welcome to submit Issues and Pull Requests to improve this project.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built on Google ADK
- Uses MCP (Model Context Protocol) standard
- Thanks to all contributors for their support


