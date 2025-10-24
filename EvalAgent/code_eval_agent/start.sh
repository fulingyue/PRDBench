#!/bin/bash

# Local Code Agent Startup Script
# One-click startup of MCP servers and main program

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed, please install Python 3 first"
        exit 1
    fi
    print_success "Python 3 is installed"
}

# Check if dependencies are installed
check_dependencies() {
    print_info "Checking dependencies..."
    
    # Check required Python packages
    python3 -c "import aiohttp" 2>/dev/null || {
        print_warning "aiohttp is not installed, installing..."
        pip3 install aiohttp
    }
    
    python3 -c "import google.adk" 2>/dev/null || {
        print_error "mt-llm-adk is not installed, please run: pip install mt-llm-adk==1.2.1.3"
        exit 1
    }
    
    print_success "Dependency check completed"
}

# Create workspace directory
create_workspace() {
    print_info "Creating workspace directory..."
    mkdir -p /tmp/code_agent_workspace
    print_success "Workspace directory created: /tmp/code_agent_workspace"
}

# Start MCP servers
start_mcp_servers() {
    print_info "Starting MCP servers..."

    # Read ports, prioritize environment variables, default 9001/8002
    PYTHON_INTERPRETER_PORT="${PYTHON_INTERPRETER_PORT:-9001}"
    FILE_OPERATIONS_PORT="${FILE_OPERATIONS_PORT:-8002}"

    # Check if ports are occupied
    if lsof -Pi :"$PYTHON_INTERPRETER_PORT" -sTCP:LISTEN -t >/dev/null ; then
        print_warning "Port $PYTHON_INTERPRETER_PORT is already occupied, MCP server might be running"
    fi

    if lsof -Pi :"$FILE_OPERATIONS_PORT" -sTCP:LISTEN -t >/dev/null ; then
        print_warning "Port $FILE_OPERATIONS_PORT is already occupied, MCP server might be running"
    fi

    # Start MCP servers (run in background)
    python3 mcp_servers.py &
    MCP_PID=$!

    # Wait for servers to start
    sleep 3

    # Check if servers started successfully
    if curl -s "http://localhost:${PYTHON_INTERPRETER_PORT}/python-interpreter/health" > /dev/null; then
        print_success "Python interpreter MCP server started successfully (port $PYTHON_INTERPRETER_PORT)"
    else
        print_error "Python interpreter MCP server failed to start (port $PYTHON_INTERPRETER_PORT)"
        exit 1
    fi

    if curl -s "http://localhost:${FILE_OPERATIONS_PORT}/file-operations/health" > /dev/null; then
        print_success "File operations MCP server started successfully (port $FILE_OPERATIONS_PORT)"
    else
        print_error "File operations MCP server failed to start"
        exit 1
    fi

    print_success "All MCP servers started successfully"
}

# Cleanup function
cleanup() {
    print_info "Cleaning up..."
    
    # Stop MCP servers
    if [ ! -z "$MCP_PID" ]; then
        kill $MCP_PID 2>/dev/null || true
        print_info "MCP servers stopped"
    fi
    
    # Stop all related Python processes
    pkill -f "mcp_servers.py" 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Show help information
show_help() {
    echo "Local Code Agent Startup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --test-only     Run tests only, don't start main program"
    echo "  --mcp-only      Start MCP servers only"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full startup (recommended)"
    echo "  $0 --test-only        # Run tests only"
    echo "  $0 --mcp-only         # Start MCP servers only"
    echo "  $0 -t 'calculate 2+2' # Execute specific task"
}

# Main function
main() {
    # Set signal handling
    trap cleanup EXIT INT TERM
    
    print_info "🚀 Starting Local Code Agent System"
    echo ""
    
    # Parse command line arguments
    TEST_ONLY=false
    MCP_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --test-only)
                TEST_ONLY=true
                shift
                ;;
            --mcp-only)
                MCP_ONLY=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                break
                ;;
        esac
    done
    
    # Check environment
    check_python
    check_dependencies
    # create_workspace
    
    # Start MCP servers
    start_mcp_servers
    print_info "MCP servers started, press Ctrl+C to stop"
    wait
}

# Run main function
main "$@" 