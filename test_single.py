#!/usr/bin/env python3
"""
单个项目测试脚本
使用方法: python test_single.py --project_id 1 --workspace_path /your/workspace --port 8000
"""

import os
import sys
import json
import argparse
import requests
import time
import shutil

def construct_session(session_id, port, model_name):
    """创建测试会话"""
    session_url = f"http://localhost:{port}/apps/code_eval_agent/users/{model_name}/sessions/s_{session_id}"
    
    try:
        # 删除已存在的会话
        response = requests.delete(session_url)
        print(f"Delete session response: {response.status_code}")
        
        # 创建新会话
        response = requests.post(session_url)
        print(f"Create session response: {response.status_code}")
        
        if response.status_code == 200:
            return True
        return False
            
    except Exception as e:
        print(f"Session creation error: {e}")
        return False

def run_evaluation(project_id, workspace_path, port, model_name="claude_code"):
    """运行单个项目评估"""
    
    project_dir = os.path.join(workspace_path, str(project_id))
    if not os.path.exists(project_dir):
        print(f"错误: 项目目录不存在 {project_dir}")
        return False
    
    # 确保有evaluation目录
    eval_source = f"PRDBench/{project_id}/evaluation"
    eval_target = os.path.join(project_dir, "evaluation")
    if not os.path.exists(eval_target):
        if os.path.exists(eval_source):
            shutil.copytree(eval_source, eval_target)
            print(f"复制评估文件到 {eval_target}")
        else:
            print(f"错误: 找不到评估文件 {eval_source}")
            return False
    
    # 创建reports目录
    reports_dir = os.path.join(project_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # 构建评估提示词
    prompt_data = f"""### Task
请评估项目 {project_dir} 的实现，通过运行测试并根据评估标准生成评估报告。评估标准在 evaluation/detailed_test_plan.json 中提供，项目代码位于 src/ 目录。

### Path Instructions
项目代码位于 {project_dir}/src/ 目录。不要修改项目代码。
评估标准位于 {project_dir}/evaluation/detailed_test_plan.json 文件。不要修改评估标准。
评估报告必须以JSON格式保存到 {project_dir}/reports/round1.jsonl。

### Example
详细的评估报告必须以JSON格式保存到 reports/round1.jsonl。报告条目应遵循以下结构：
{{
"metric": "1.3 Menu Navigation - Export Results Submenu",
"description": "1. **Act:** Start the program and select main menu '3' to enter the export results submenu.\\n2. **Assert:** Check whether the submenu displays 'Export Huffman codes to CSV', 'Export Huffman tree to JSON', and 'Return to main menu'.",
"score": 0,
"explanation": "When attempting to export results without having generated Huffman codes, the program does not enter the export submenu but instead prompts 'No available Huffman codes, please generate them first.' and returns to the main menu, which does not meet the expected behavior."
}}

请严格按照 {project_dir}/evaluation/detailed_test_plan.json 中的评估标准按确切指定的顺序运行相关测试，确保不遗漏任何测试点。之后，生成如上所述的综合评估报告，并按指定格式保存到 {project_dir}/reports/round1.jsonl。

### Final Reminder
代码的接口必须严格按照评估标准完成才能被认为是合格的。如果代码无法运行或无法适配接口，请直接给当前测试点0分。
不要修改项目代码。不要修改评估标准。
""".strip()
    
    # 创建会话
    session_id = f"test_{project_id}"
    if not construct_session(session_id, port, model_name):
        print("会话创建失败")
        return False
    
    # 发送评估请求
    query_data = {
        "appName": "code_eval_agent",
        "userId": model_name,
        "sessionId": f"s_{session_id}",
        "newMessage": {
            "role": "user",
            "parts": [{
                "text": prompt_data
            }]
        }
    }
    
    try:
        response = requests.post(f"http://localhost:{port}/run", json=query_data)
        print(f"评估请求状态: {response.status_code}")
        
        if response.status_code == 200:
            # 保存日志
            log_file = os.path.join(reports_dir, "round1.log")
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, indent=2, ensure_ascii=False)
            print(f"评估完成，日志保存到: {log_file}")
            return True
        else:
            print(f"评估请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"评估请求错误: {e}")
        return False

def calculate_project_score(project_id, workspace_path):
    """计算项目得分"""
    report_file = os.path.join(workspace_path, str(project_id), "reports", "round1.jsonl")
    
    if not os.path.exists(report_file):
        print(f"评估报告不存在: {report_file}")
        return None
    
    try:
        total_score = 0
        total_count = 0
        
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        # 解析JSON内容
        if content.startswith('[') and content.endswith(']'):
            items = json.loads(content)
            for item in items:
                if isinstance(item, dict) and 'score' in item:
                    total_score += item['score']
                    total_count += 1
        else:
            # 处理其他格式
            lines = [line for line in content.splitlines() if line.strip()]
            for line in lines:
                try:
                    item = json.loads(line)
                    if isinstance(item, dict) and 'score' in item:
                        total_score += item['score']
                        total_count += 1
                except:
                    continue
        
        if total_count == 0:
            return None
            
        # 计算通过率 (满分每项2分)
        max_possible = total_count * 2
        pass_rate = (total_score / max_possible) * 100 if max_possible > 0 else 0
        
        print(f"\n=== 项目 {project_id} 测试结果 ===")
        print(f"总测试项: {total_count}")
        print(f"获得分数: {total_score}/{max_possible}")
        print(f"通过率: {pass_rate:.2f}%")
        
        return {
            "project_id": project_id,
            "total_tests": total_count,
            "total_score": total_score,
            "max_score": max_possible,
            "pass_rate": pass_rate
        }
        
    except Exception as e:
        print(f"计算分数错误: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="测试单个PRDBench项目")
    parser.add_argument("--project_id", type=int, required=True, help="项目ID (1-50)")
    parser.add_argument("--workspace_path", type=str, required=True, help="工作空间路径")
    parser.add_argument("--port", type=int, default=8000, help="ADK服务端口")
    parser.add_argument("--model_name", type=str, default="claude_code", help="模型名称")
    
    args = parser.parse_args()
    
    print(f"开始测试项目 {args.project_id}")
    print(f"工作空间: {args.workspace_path}")
    print(f"端口: {args.port}")
    
    # 运行评估
    if run_evaluation(args.project_id, args.workspace_path, args.port, args.model_name):
        # 等待评估完成
        time.sleep(10)
        
        # 计算分数
        result = calculate_project_score(args.project_id, args.workspace_path)
        if result:
            print("\n测试完成!")
            return result["pass_rate"]
    
    print("测试失败!")
    return 0

if __name__ == "__main__":
    main()