import requests
import json
import os
import shutil
import time

# for each prompt, I should first create a session, then send the query
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--local_port", type=str, default="8010")
parser.add_argument("--model_name", type=str, default="claude_3_7_sonnet")
parser.add_argument("--root_path", type=str, default='workspace/gemini_test')
parser.add_argument("--round", type=int, default=1)
parser.add_argument("--source_dir", type=str, default="data/")



args = parser.parse_args()
code_path = args.root_path
source_dir = args.source_dir

local_port = args.local_port
model_name = args.model_name

def move_to_backup(file_path, backup_dir):
    if os.path.exists(file_path):
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        base_name = os.path.basename(file_path)
        backup_file = os.path.join(backup_dir, base_name)
        shutil.move(file_path, backup_file)
        print(f"Moved {file_path} to {backup_file}")

def construct_session(session_id):
    session_query = {
        "url": f"http://localhost:{local_port}/apps/code_eval_agent/users/{model_name}/sessions/s_{session_id}",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        }
    }
    # delete session if it exists via curl -X DELETE
    delete_query = {
        "url": f"http://localhost:{local_port}/apps/code_eval_agent/users/{model_name}/sessions/s_{session_id}",
        "method": "DELETE",
        "headers": {
            "Content-Type": "application/json"
        }
    }
    
    try:
        # Delete existing session
        delete_response = requests.delete(delete_query["url"], headers=delete_query["headers"])
        print(f"Delete session response status code: {delete_response.status_code}")
        
        # Create new session
        response = requests.post(session_query["url"], headers=session_query["headers"])
        print(f"Create session response status code: {response.status_code}")
        print(f"Create session response content: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Create session failed, status code: {response.status_code}")
            return response.json()
            
    except requests.exceptions.RequestException as e:
        print(f"Network request error: {e}")
        return {"error": "network_error", "message": str(e)}
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response content: {response.text}")
        return {"error": "json_decode_error", "text": response.text}

def make_query(prompt_data, session_id):
    query_query = {
        "url": f"http://localhost:{local_port}/run",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        },
        "data": {
            "appName": f"code_eval_agent",
            "userId": model_name,
            "sessionId": f"s_{session_id}",
            "newMessage": {
                "role": "user",
                "parts": [{
                    "text": prompt_data
                }]
            }
        }
    }
    
    try:
        response = requests.post(query_query["url"], headers=query_query["headers"], json=query_query["data"])
        print(f"Query response status code: {response.status_code}")
        print(f"Query response content: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Query failed, status code: {response.status_code}")
            return response.json()
            
    except requests.exceptions.RequestException as e:
        print(f"Network request error: {e}")
        return {"error": "network_error", "message": str(e)}
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response content: {str(response)}")
        return {"error": "json_decode_error", "text": str(response)}
    # todo if token limit occurs retry up to 5 times

def check_report_format(report_file):
    """
    Check if evaluation report round.jsonl conforms to standard format
    Returns True if compliant, False if non-compliant
    """
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return False
            # Standard array
            if content.startswith('[') and content.endswith(']'):
                items = json.loads(content)
                valid_count = sum(1 for item in items if isinstance(item, dict) and 'score' in item)
                return valid_count > 0
            else:
                lines = [line for line in content.splitlines() if line.strip()]
                # JSONL check
                is_jsonl = True
                for line in lines:
                    try:
                        json.loads(line)
                    except json.JSONDecodeError:
                        is_jsonl = False
                        break
                if is_jsonl:
                    valid_count = sum(1 for line in lines
                                      if isinstance(json.loads(line), dict)
                                      and 'score' in json.loads(line))
                    return valid_count > 0
                else:
                    # Multi-line objects
                    objects = []
                    brace_depth = 0
                    obj_start = None
                    for i, c in enumerate(content):
                        if c == '{':
                            if brace_depth == 0:
                                obj_start = i
                            brace_depth += 1
                        elif c == '}':
                            brace_depth -= 1
                            if brace_depth == 0 and obj_start is not None:
                                obj_str = content[obj_start:i+1]
                                objects.append(obj_str)
                                obj_start = None
                    if len(objects) < 3:
                        return False
                    valid_count = sum(1 for obj_str in objects
                                      if isinstance(json.loads(obj_str), dict)
                                      and 'score' in json.loads(obj_str))
                    return valid_count > 0
    except Exception:
        return False


# Loop evaluation of projects 1 to 50
def run_evaluation(i, args, code_path, source_dir, construct_session, make_query, retry_round=0):
    print(f"\n=== Starting evaluation of project {i} ===")
    path_suffix = i
    dir_path = os.path.join(code_path, str(path_suffix))
    project_dir = dir_path

    # Check if project directory exists
    if not os.path.exists(project_dir):
        print(f"Warning: Project directory {project_dir} does not exist, skipping...")
        return False

    report_file = os.path.join(dir_path, "reports", f"round{args.round}.jsonl")
    if os.path.exists(report_file):
        print(f"Project {i} has already been evaluated, skipping...")
        return True

    report_dir = os.path.join(dir_path, "reports")
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    eva_path = os.path.join(source_dir, str(i), "evaluation")
    eval_dir_source = eva_path
    eval_dir_target = os.path.join(dir_path, "evaluation")
    '''
    if os.path.exists(eval_dir_source):
        shutil.copytree(eval_dir_source, eval_dir_target, dirs_exist_ok=True)
        print(f"Copied {i}/evaluation directory")
    else:
        print(f"Warning: No evaluation directory found in {i}")
    '''
    prompt_data = f"""### Task
Please evaluate the implementation of {project_dir} by running its tests and generating an evaluation report according to the evaluation criteria. The evaluation criteria are provided in evaluation/detailed_test_plan.json, and the project code is located in the src/ directory.
The code should be completed strictly in accordance with the evaluation criteria to be considered qualified. If the code fails to run or adapt to the interface, please directly give the current test point a score of 0.
### Path Instructions
The project code is located in the {project_dir}/src/ directory. DO NOT MODIFY THE PROJECT CODE.
The evaluation criteria are located in the {project_dir}/evaluation/detailed_test_plan.json file. DO NOT MODIFY THE EVALUATION CRITERIA.DO NOT MODIFY ANY FILES UNDER THE {project_dir}/evaluation DIRECTORY.
The evaluation report must be saved to {project_dir}/reports/round{args.round}.jsonl in JSON format.

### Tips
If you meet 'No module named xxx' error, you can try `/mnt/dolphinfs/hdd_pool/docker/user/hadoop-aipnlp/EVA/kuangjun/.conda/.envs/evalADK. If there is still error, report it in the report.
If the code is unable to run, please report it in the report.
If the detailed_test_plan mentions that image analysis is required, use the "deal_graph" tool to analyze the images.

### Example
The detailed evaluation report must be saved to reports/round{args.round}.jsonl in JSON format. Entries in the report should follow this structure:
{{
"metric": "1.3 Menu Navigation - Export Results Submenu",
"description": "1. **Act:** Start the program and select main menu '3' to enter the export results submenu.\\n2. **Assert:** Check whether the submenu displays 'Export Huffman codes to CSV', 'Export Huffman tree to JSON', and 'Return to main menu'.",
"score": 0,
"explanation": "When attempting to export results without having generated Huffman codes, the program does not enter the export submenu but instead prompts 'No available Huffman codes, please generate them first.' and returns to the main menu, which does not meet the expected behavior."
}},
{{
"metric": "3.2 Unit Test - Generate Huffman Codes",
"description": "1. **Pre-check (User Path):** Is there a unit test for the `generate_huffman_codes` function in `src/tests/` or a similar directory?\\n2. **Arrange:** Prepare test data, such as a constructed Huffman tree and the expected encoding dictionary.\\n3. **Act:** Run the unit test command `pytest src/tests/test_huffman.py::TestHuffman::test_generate_huffman_codes -v`.\\n4. **Assert:** Observe whether the test passes.",
"score": 2,
"explanation": "The test command `pytest src/tests/test_huffman.py::TestHuffman::test_generate_huffman_codes -v` executed successfully, and the result was 'PASSED', which matches the expected output 'Unit test passed'."
}}

Please strictly follow the evaluation criteria in {project_dir}/evaluation/detailed_test_plan.json to run the relevant tests in the exact order specified, making sure not to miss any test points in detailed_test_plan.json. After that, generate a comprehensive evaluation report as described above, and save it to {project_dir}/reports/round{args.round}.jsonl in the specified format. 

### Final Reminder
The interface of the code must be completed strictly in accordance with the evaluation criteria to be considered qualified. If the code fails to run or adapt to the interface, please directly give the current test point a score of 0.
DO NOT modify the project code. DO NOT MODIFY the evaluation criteria. 
""".strip()
    # After getting prompt_data, add:
    if retry_round is not None:
        try:
            if retry_round > 0:
                prompt_data += ' ' * retry_round
                print(f"Retry {retry_round} detected. Added {retry_round} space(s) to prompt.")
        except ValueError:
            print(f"Warning: --retry must be an integer, current value: {retry_round}")

    # Add retry round to session_id to ensure uniqueness
    if retry_round == 0:
        session_id = str(path_suffix)
    else:
        session_id = f"{path_suffix}_{retry_round}"

    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    print(f"Starting to create session, session_id: {session_id} ...")
    session_response = construct_session(session_id)

    print(f"Starting to send query...")
    query_response = make_query(prompt_data, session_id)

    log_dir = os.path.join(dir_path, "reports")
    if(not os.path.exists(log_dir)):
        os.makedirs(log_dir)

    with open(os.path.join(log_dir, f"round{args.round}.log"), 'w', encoding='utf-8') as f:
        json.dump(query_response, f, indent=2, ensure_ascii=False)

    print(f"dir_path: {dir_path}")
    print(f"=== Project {i} evaluation completed ===\n")
    return True

def check_all_reports_generated(code_path, args):
    """Check if all projects have generated jsonl files"""
    for i in range(1, 51):
        dir_path = os.path.join(code_path, str(i))
        report_file = os.path.join(dir_path, "reports", f"round{args.round}.jsonl")
        if not os.path.exists(report_file):
            return False
    return True

def main(args, code_path, source_dir, construct_session, make_query):
    # First round evaluation
    for i in range(1,51):
        run_evaluation(i, args, code_path, source_dir, construct_session, make_query, retry_round=0)
    print("All 50 projects initial evaluation completed!")

    retry_count = 0
    while True:
        all_generated = True
        for i in range(1, 51):
            dir_path = os.path.join(code_path, str(i))
            report_file = os.path.join(dir_path, "reports", f"round{args.round}.jsonl")
            log_file = os.path.join(dir_path, "reports", f"round{args.round}.log")
            project_dir = dir_path

            # Check if project directory exists
            if not os.path.exists(project_dir):
                print(f"Gap-filling check: Project directory {project_dir} does not exist, skipping...")
                continue

            # Check if evaluation report exists and is compliant
            if not os.path.exists(report_file) or not check_report_format(report_file):
                all_generated = False
                print(f"Gap-filling check: Project {i} evaluation report does not exist or format non-compliant, preparing retry...")
                # Backup report and log files to root_path/reports_backup/i/
                backup_dir = os.path.join(code_path, "reports_backup", str(i))
                if os.path.exists(report_file):
                    move_to_backup(report_file, backup_dir)
                if os.path.exists(log_file):
                    move_to_backup(log_file, backup_dir)
                # Re-run evaluation process, pass current retry round to ensure session_id uniqueness
                if retry_count < 30:
                    run_evaluation(i, args, code_path, source_dir, construct_session, make_query, retry_round=retry_count+1)
                else:
                    print(f"Project {i} retry has reached 3 times, skipping!")
            else:
                print(f"Gap-filling check: Project {i} evaluation report exists and compliant, skipping...")

        if all_generated or retry_count >= 3:
            break
        retry_count += 1
        print(f"\n=== Gap-filling retry round {retry_count} ===")

    print("All projects' jsonl files have been generated and compliant, gap-filling retry ended!")
if __name__ == '__main__':
    main(args, code_path, source_dir, construct_session, make_query)
