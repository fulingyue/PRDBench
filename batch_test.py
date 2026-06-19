#!/usr/bin/env python3
"""
批量测试多个项目
使用方法: python batch_test.py --projects 1,2,3 --workspace_path /your/workspace --port 8000
"""

import os
import argparse
from test_single import run_evaluation, calculate_project_score
import time

def batch_test(project_ids, workspace_path, port, model_name="claude_code"):
    """批量测试多个项目"""
    results = {}
    
    for project_id in project_ids:
        print(f"\n{'='*50}")
        print(f"开始测试项目 {project_id}")
        print(f"{'='*50}")
        
        # 运行评估
        if run_evaluation(project_id, workspace_path, port, model_name):
            # 等待评估完成
            print("等待评估完成...")
            time.sleep(15)
            
            # 计算分数
            result = calculate_project_score(project_id, workspace_path)
            if result:
                results[project_id] = result
            else:
                results[project_id] = {"pass_rate": 0, "error": "计算分数失败"}
        else:
            results[project_id] = {"pass_rate": 0, "error": "评估失败"}
    
    # 打印总结
    print("\n" + "="*50)
    print("批量测试总结")
    print("="*50)
    
    total_rate = 0
    valid_count = 0
    
    for project_id, result in results.items():
        if isinstance(result, dict) and 'pass_rate' in result:
            rate = result['pass_rate']
            print(f"项目 {project_id}: {rate:.2f}%")
            if 'error' not in result:
                total_rate += rate
                valid_count += 1
        else:
            print(f"项目 {project_id}: 测试失败")
    
    if valid_count > 0:
        avg_rate = total_rate / valid_count
        print(f"\n平均通过率: {avg_rate:.2f}%")
        print(f"成功测试项目数: {valid_count}/{len(project_ids)}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="批量测试多个PRDBench项目")
    parser.add_argument("--projects", type=str, required=True, help="项目ID列表，用逗号分隔 (例: 1,2,3)")
    parser.add_argument("--workspace_path", type=str, required=True, help="工作空间路径")
    parser.add_argument("--port", type=int, default=8000, help="ADK服务端口")
    parser.add_argument("--model_name", type=str, default="claude_code", help="模型名称")
    
    args = parser.parse_args()
    
    # 解析项目ID列表
    try:
        project_ids = [int(x.strip()) for x in args.projects.split(',')]
    except ValueError:
        print("错误: 项目ID必须是数字，用逗号分隔")
        return
    
    print(f"将测试项目: {project_ids}")
    print(f"工作空间: {args.workspace_path}")
    
    # 运行批量测试
    results = batch_test(project_ids, args.workspace_path, args.port, args.model_name)
    
    # 保存结果
    import json
    result_file = os.path.join(args.workspace_path, "batch_test_results.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细结果已保存到: {result_file}")

if __name__ == "__main__":
    main()