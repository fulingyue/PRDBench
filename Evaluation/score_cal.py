import os
import json
import re
import argparse

def calculate_score(json_file):
    total_score = 0
    total_count = 0
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return None
            # Standard array
            if content.startswith('[') and content.endswith(']'):
                items = json.loads(content)
                for item in items:
                    if isinstance(item, dict) and 'score' in item:
                        total_score += item['score']
                        total_count += 1
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
                    for line in lines:
                        try:
                            item = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(item, dict) and 'score' in item:
                            total_score += item['score']
                            total_count += 1
                else:
                    # New: No [] wrapper and one {} may span multiple lines
                    # Use regex to extract top-level objects
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
                    # Must ensure object count is above 5
                    if len(objects) < 5:
                        return 0
                    for obj_str in objects:
                        try:
                            item = json.loads(obj_str)
                        except Exception:
                            continue
                        if isinstance(item, dict) and 'score' in item:
                            total_score += item['score']
                            total_count += 1
    except FileNotFoundError:
        return None
    except Exception:
        return None

    if total_count == 0:
        return None

    final_score = total_score / total_count / 2
    return final_score

def batch_calculate_and_average(base_path, round_name):
    results = {}
    total_sum = 0
    valid_count = 0
    for i in range(1, 51):
        json_path = os.path.join(base_path, str(i), 'reports', f'round{round_name}.jsonl')
        score = calculate_score(json_path)
        if score is not None:
            results[i] = score
            total_sum += score
            valid_count += 1
        else:
            results[i] = "File does not exist or no valid data"
    average_score = total_sum / valid_count if valid_count > 0 else 0
    return results, average_score, valid_count

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Batch calculate average score")
    parser.add_argument('--base_path', type=str, required=True, help='Base path')
    parser.add_argument('--round', type=str, default=1)
    args = parser.parse_args()

    results, average_score, valid_count = batch_calculate_and_average(args.base_path, args.round)
    output = {
        "scores": results,
        "valid_count": valid_count,
        "average_score": average_score
    }
    output_path = os.path.join(args.base_path, f'results_{args.round}.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
