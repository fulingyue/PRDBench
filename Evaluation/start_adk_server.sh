# ==================== ADK Server Startup Script ====================
# Function: Start Claude 3.7 Sonnet ADK server and run code generation script
# Usage: ./start_adk_server.sh <test_type> <root_path> <port> <python_port> <file_port> <system_port>



# Receive script parameters
TEST_TYPE=$1
ROOT_PATH=$2
PORT=$3
export PYTHON_INTERPRETER_PORT=$4
export FILE_OPERATIONS_PORT=$5
export SYSTEM_OPERATIONS_PORT=$6

echo "Parameter settings:"
echo "  test_type: $TEST_TYPE"
echo "  root_path: $ROOT_PATH"
echo "  port: $PORT"

MODEL_NAME=$TEST_TYPE
SESSION_NAME="adk_server_${MODEL_NAME}"
FILE_SERVER_NAME="file_server_${MODEL_NAME}"

# Environment setup
conda activate evalADK

# Clean up existing ADK server and file service tmux sessions (avoid port conflicts)
echo "SESSION NAME $SESSION_NAME"
echo "FILE SERVER NAME $FILE_SERVER_NAME"
echo "Cleaning up existing ADK server tmux sessions..."
tmux kill-session -t $SESSION_NAME 2>/dev/null || true
echo "Cleaning up existing file service tmux sessions..."
tmux kill-session -t $FILE_SERVER_NAME 2>/dev/null || true


# Set ADK server working directory to root_path
export CODE_AGENT_WORKSPACE_DIR="$ROOT_PATH"
echo "Setting ADK working directory: $CODE_AGENT_WORKSPACE_DIR"

# Start file service (restart each time to ensure correct port configuration)
echo "Starting file service... $FILE_SERVER_NAME"
tmux new-session -d -s $FILE_SERVER_NAME -n $FILE_SERVER_NAME
tmux send-keys -t $FILE_SERVER_NAME "conda activate evalADK; export PYTHON_INTERPRETER_PORT=${PYTHON_INTERPRETER_PORT} ; export FILE_OPERATIONS_PORT=${FILE_OPERATIONS_PORT} ; export SYSTEM_OPERATIONS_PORT=${SYSTEM_OPERATIONS_PORT} ; export CODE_AGENT_WORKSPACE_DIR=${ROOT_PATH} ; cd EvalAgent/code_eval_agent ; ./start.sh" C-m

# Wait for file service to start
echo "Waiting for file service to start..."
sleep 5

# Start a shared ADK server (start only once, working directory set to root_path)
echo "Starting shared ${MODEL_NAME} ADK server..."

# Create ADK server session
tmux new-session -d -s $SESSION_NAME -n $SESSION_NAME

# Set environment variables
tmux send-keys -t $SESSION_NAME "conda activate evalADK" C-m
tmux send-keys -t $SESSION_NAME "export ADK_MODEL=${MODEL_NAME}" C-m
tmux send-keys -t $SESSION_NAME "export CODE_AGENT_WORKSPACE_DIR=${ROOT_PATH}" C-m
tmux send-keys -t $SESSION_NAME "export PYTHON_INTERPRETER_PORT=${PYTHON_INTERPRETER_PORT}" C-m
tmux send-keys -t $SESSION_NAME "export FILE_OPERATIONS_PORT=${FILE_OPERATIONS_PORT}" C-m
tmux send-keys -t $SESSION_NAME "export SYSTEM_OPERATIONS_PORT=${SYSTEM_OPERATIONS_PORT}" C-m
tmux send-keys -t $SESSION_NAME "cd EvalAgent" C-m

# Wait for environment setup to complete
sleep 2

# Start ADK server
tmux send-keys -t $SESSION_NAME "adk api_server --port ${PORT}" C-m

# Wait for ADK server to start
echo "Waiting for ADK server to start..."
sleep 15

# Check if server started successfully
# echo "Checking ADK server status..."
# if curl -s "http://localhost:${PORT}/health" > /dev/null 2>&1; then
#     echo "ADK server started successfully!"
# else
#     echo "Warning: ADK server may not have started completely, continuing execution..."
# fi
