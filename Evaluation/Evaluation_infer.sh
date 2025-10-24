MODEL_NAME=$1
PORT=$3
PYTHON_INTERPRETER_PORT=$4
FILE_OPERATIONS_PORT=$5
SYSTEM_OPERATIONS_PORT=$6
ROOT_PATH=$2
source_dir=$7
bash Evaluation/start_adk_server.sh ${MODEL_NAME} ${ROOT_PATH} ${PORT} ${PYTHON_INTERPRETER_PORT} ${FILE_OPERATIONS_PORT} ${SYSTEM_OPERATIONS_PORT}
sleep 60
# Delete JSON files used for statistics in the previous step
python Evaluation/delete_query_json.py ${ROOT_PATH}
python Evaluation/generate_code.py --local_port ${PORT} --root_path ${ROOT_PATH} --source_dir ${source_dir}
python Evaluation/score_cal.py --base_path ${ROOT_PATH}
