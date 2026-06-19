#!/usr/bin/env python3
"""
直接使用judge工具的测试脚本
这个版本直接调用judge工具进行测试，不需要ADK服务器
"""

import os
import sys
import json
import argparse
import pexpect
import time
import traceback
from pathlib import Path

class PRDBenchTester:
    """直接使用judge工具进行PRDBench测试"""
    
    def __init__(self, project_id, workspace_path):
        self.project_id = project_id
        self.workspace_path = workspace_path
        self.project_dir = os.path.join(workspace_path, str(project_id))
        self.test_results = []
    
    def judge(self, context: str, entry_command: str, input_file: str = None):
        """
        judge工具的Python实现
        运行程序并模拟用户交互，记录交互过程和输出结果
        """
        print(f"\n=== 运行测试: {context} ===")
        print(f"命令: {entry_command}")
        print(f"输入文件: {input_file}")
        
        result = {
            "success": False,
            "log": '',
            "error": None,
            "context": context,
            "command": entry_command
        }
        
        # 检查输入文件
        input_lines = []
        if input_file and os.path.exists(input_file):
            with open(input_file, 'r', encoding='utf-8') as f:
                input_lines = [line.rstrip('\n') for line in f]
            print(f"输入内容: {input_lines}")
        elif input_file:
            result["error"] = f"输入文件 {input_file} 不存在"
            return result
        
        # 使用pexpect运行程序
        output_log = []
        stderr_log = []
        
        # 创建一个日志记录器类
        class LogCapture:
            def __init__(self, output_log):
                self.output_log = output_log
                
            def write(self, data):
                if data.strip():  # 只记录非空数据
                    self.output_log.append(f"程序输出: {data}")
                    print(f"程序输出: {data.strip()}")
                    
            def flush(self):
                pass  # pexpect可能会调用这个方法
        
        try:
            print(f"在目录 {self.project_dir} 中执行: {entry_command}")
            child = pexpect.spawn(entry_command, cwd=self.project_dir, timeout=30, encoding='utf-8')
            
            # 设置日志捕获
            log_capture = LogCapture(output_log)
            child.logfile_read = log_capture
            
            # 等待程序启动
            time.sleep(0.5)
            
            # 发送用户输入
            for line in input_lines:
                print(f"用户输入: {line}")
                output_log.append(f"用户输入: {line}")
                try:
                    child.sendline(line)
                    time.sleep(0.2)
                except Exception as send_error:
                    error_msg = f"发送输入失败: {send_error}"
                    print(error_msg)
                    output_log.append(error_msg)
                    break
            
            # 等待程序结束或超时
            try:
                child.expect(pexpect.EOF, timeout=10)
                result["success"] = True
            except pexpect.TIMEOUT:
                print("程序超时，发送Ctrl+C")
                output_log.append("用户输入: <Ctrl+C>")
                child.sendcontrol('c')
                try:
                    child.expect(pexpect.EOF, timeout=3)
                    result["success"] = True  # Ctrl+C也算成功
                except pexpect.TIMEOUT:
                    child.close(force=True)
                    result["error"] = "程序无法正常结束，强制关闭"
            
            # 检查退出状态并收集详细信息
            exit_status = child.exitstatus
            signal_status = child.signalstatus
            
            if exit_status == 0 or exit_status == 130:  # 130 是Ctrl+C的退出码
                result["success"] = True
            else:
                result["success"] = False
                error_details = [
                    f"程序异常退出 - 退出码: {exit_status}",
                    f"信号状态: {signal_status}",
                    f"执行命令: {entry_command}",
                    f"工作目录: {self.project_dir}"
                ]
                
                # 尝试分析常见错误类型
                if exit_status == 1:
                    error_details.append("可能的原因: 程序内部错误、未处理异常、导入错误")
                elif exit_status == 2:
                    error_details.append("可能的原因: 命令行参数错误、文件未找到")
                elif exit_status == 127:
                    error_details.append("可能的原因: 命令未找到、Python解释器问题")
                
                result["error"] = "\n".join(error_details)
                print(f"\n=== 程序异常退出详情 ===")
                for detail in error_details:
                    print(f"  {detail}")
            
            child.close()
            
        except FileNotFoundError as e:
            result["error"] = f"文件未找到错误: {str(e)}\n可能原因:\n- 主程序文件不存在\n- Python解释器未找到\n- 工作目录错误: {self.project_dir}"
            print(f"\n=== 文件未找到错误 ===")
            print(f"错误: {e}")
            print(f"检查路径: {self.project_dir}")
            print(f"执行命令: {entry_command}")
            
        except PermissionError as e:
            result["error"] = f"权限错误: {str(e)}\n可能原因:\n- 文件没有执行权限\n- 目录访问被拒绝\n- 系统权限限制"
            print(f"\n=== 权限错误 ===")
            print(f"错误: {e}")
            
        except pexpect.exceptions.ExceptionPexpect as e:
            result["error"] = f"Pexpect执行错误: {str(e)}\n错误类型: {type(e).__name__}\n可能原因:\n- 程序无法正常启动\n- 终端交互异常\n- 编码问题"
            print(f"\n=== Pexpect错误 ===")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {e}")
            
        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            result["error"] = f"未预期错误: {str(e)}\n错误类型: {type(e).__name__}\n\n完整堆栈跟踪:\n{tb_str}"
            print(f"\n=== 未预期错误 ===")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {e}")
            print(f"完整traceback:\n{tb_str}")
        
        # 无论成功失败都记录完整日志
        result["log"] = '\n'.join(output_log)
        
        # 添加执行环境信息
        result["environment"] = {
            "command": entry_command,
            "working_directory": self.project_dir,
            "input_lines_count": len(input_lines),
            "output_lines_count": len(output_log)
        }
        
        return result
    
    def load_test_plan(self):
        """加载测试计划"""
        test_plan_file = os.path.join(self.project_dir, "evaluation", "detailed_test_plan.json")
        if not os.path.exists(test_plan_file):
            raise FileNotFoundError(f"测试计划文件不存在: {test_plan_file}")
        
        with open(test_plan_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def evaluate_output(self, test_case, judge_result):
        """评估测试结果"""
        if not judge_result["success"]:
            error_msg = judge_result.get('error', '未知错误')
            output_log = judge_result.get('log', '')
            environment = judge_result.get('environment', {})
            
            detailed_explanation = f"❌ 程序执行失败\n\n" \
                                 f"🔥 错误信息:\n{error_msg}\n\n"
            
            if environment:
                detailed_explanation += f"🔧 执行环境:\n"
                for key, value in environment.items():
                    detailed_explanation += f"  - {key}: {value}\n"
                detailed_explanation += "\n"
            
            if output_log:
                detailed_explanation += f"📝 程序输出日志:\n{output_log}\n\n"
                
                # 尝试识别常见错误模式
                log_lower = output_log.lower()
                if 'traceback' in log_lower or 'error:' in log_lower:
                    detailed_explanation += "🐛 检测到Python异常\n"
                if 'importerror' in log_lower or 'modulenotfounderror' in log_lower:
                    detailed_explanation += "💡 建议: 检查依赖包是否安装 (pip install -r requirements.txt)\n"
                if 'syntaxerror' in log_lower:
                    detailed_explanation += "💡 建议: 检查Python语法错误\n"
                if 'filenotfounderror' in log_lower:
                    detailed_explanation += "💡 建议: 检查文件路径是否正确\n"
                if "'function' object has no attribute" in log_lower:
                    detailed_explanation += "💡 建议: 检查是否有变量名与内置函数冲突 (如open, print等)\n"
                    
            print(f"\n❌ 测试失败详情:")
            print(f"错误: {error_msg}")
            if output_log:
                print(f"\n📝 程序输出:\n{output_log}")
            
            return {
                "score": 0,
                "explanation": detailed_explanation
            }
        
        output_log = judge_result["log"]
        expected_output = test_case.get("expected_output", "")
        
        # 简单的输出匹配逻辑
        if expected_output.lower() in output_log.lower():
            print(f"✅ 测试通过: 找到预期输出 '{expected_output}'")
            return {
                "score": 2,
                "explanation": f"✅ 程序输出符合预期要求\n\n📝 找到预期输出: {expected_output}"
            }
        else:
            print(f"❌ 测试失败: 未找到预期输出 '{expected_output}'")
            print(f"\n📝 实际程序输出:\n{output_log}")
            return {
                "score": 0,
                "explanation": f"❌ 程序输出不符合预期\n\n" \
                             f"🎯 期望输出: {expected_output}\n\n" \
                             f"📝 实际输出:\n{output_log}"
            }
    
    def run_single_test(self, test_case):
        """运行单个测试用例"""
        metric = test_case.get("metric", "未知测试")
        description = test_case.get("description", "")
        test_type = test_case.get("type", "shell_interaction")
        testcases = test_case.get("testcases", [])
        
        print(f"\n{'='*60}")
        print(f"测试项: {metric}")
        print(f"描述: {description}")
        print(f"类型: {test_type}")
        
        if not testcases:
            return {
                "metric": metric,
                "description": description,
                "score": 0,
                "explanation": "无测试用例"
            }
        
        # 运行第一个测试用例
        first_test = testcases[0]
        test_command = first_test.get("test_command", "")
        test_input = first_test.get("test_input", "")
        
        if not test_command:
            return {
                "metric": metric,
                "description": description,
                "score": 0,
                "explanation": "无测试命令"
            }
        
        # 构建输入文件路径
        input_file_path = None
        if test_input:
            input_file_path = os.path.join(self.project_dir, test_input)
        
        # 使用judge工具运行测试
        judge_result = self.judge(
            context=metric,
            entry_command=test_command,
            input_file=input_file_path
        )
        
        # 评估结果
        evaluation = self.evaluate_output(test_case, judge_result)
        
        return {
            "metric": metric,
            "description": description,
            "score": evaluation["score"],
            "explanation": evaluation["explanation"],
            "judge_log": judge_result["log"]  # 保存详细日志
        }
    
    def run_all_tests(self):
        """运行所有测试"""
        try:
            test_plan = self.load_test_plan()
        except FileNotFoundError as e:
            print(f"错误: {e}")
            return False
        
        print(f"加载了 {len(test_plan)} 个测试用例")
        
        # 运行每个测试
        for test_case in test_plan:
            result = self.run_single_test(test_case)
            self.test_results.append(result)
        
        return True
    
    def save_results(self, output_file):
        """保存测试结果"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 计算统计信息
        score_info = self.calculate_score()
        
        # 创建详细的测试报告
        report_data = {
            "summary": score_info if score_info else {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_id": self.project_id,
            "workspace_path": self.workspace_path,
            "test_results": []
        }
        
        # 保存测试结果（简化版用于报告）
        for result in self.test_results:
            clean_result = {
                "metric": result["metric"],
                "description": result["description"][:200] + "..." if len(result.get("description", "")) > 200 else result.get("description", ""),
                "score": result["score"],
                "explanation": result["explanation"][:500] + "..." if len(result.get("explanation", "")) > 500 else result.get("explanation", ""),
                "status": "PASSED" if result["score"] > 0 else "FAILED"
            }
            report_data["test_results"].append(clean_result)
        
        # 保存主报告
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # 保存详细日志（包含完整的judge日志）
        detailed_file = output_file.replace('.jsonl', '_detailed.json')
        detailed_data = {
            "summary": report_data["summary"],
            "execution_details": {
                "timestamp": report_data["timestamp"],
                "project_id": self.project_id,
                "workspace_path": self.workspace_path,
                "total_execution_time": "未记录"
            },
            "full_test_results": self.test_results  # 包含完整的judge_log
        }
        
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 测试报告已保存到: {output_file}")
        print(f"📋 详细日志已保存到: {detailed_file}")
        
        return output_file, detailed_file
    
    def calculate_score(self):
        """计算总分"""
        if not self.test_results:
            return None
        
        total_score = sum(result["score"] for result in self.test_results)
        max_score = len(self.test_results) * 2
        pass_rate = (total_score / max_score * 100) if max_score > 0 else 0
        
        # 统计测试结果
        passed = sum(1 for result in self.test_results if result["score"] > 0)
        failed = len(self.test_results) - passed
        
        return {
            "total_tests": len(self.test_results),
            "passed_tests": passed,
            "failed_tests": failed,
            "total_score": total_score,
            "max_score": max_score,
            "pass_rate": pass_rate,
            "grade": self._get_grade(pass_rate)
        }
    
    def _get_grade(self, pass_rate):
        """根据通过率给出等级"""
        if pass_rate >= 90:
            return "🏆 优秀 (A)"
        elif pass_rate >= 80:
            return "🥇 良好 (B)"
        elif pass_rate >= 60:
            return "🥈 及格 (C)"
        elif pass_rate >= 40:
            return "🥉 待改进 (D)"
        else:
            return "❌ 需重做 (F)"

def main():
    parser = argparse.ArgumentParser(description="直接使用judge工具测试PRDBench项目")
    parser.add_argument("--project_id", type=int, required=True, help="项目ID (1-50)")
    parser.add_argument("--workspace_path", type=str, required=True, help="工作空间路径")
    
    args = parser.parse_args()
    
    print(f"开始测试项目 {args.project_id}")
    print(f"工作空间: {args.workspace_path}")
    
    # 创建测试器
    tester = PRDBenchTester(args.project_id, args.workspace_path)
    
    # 检查项目目录
    if not os.path.exists(tester.project_dir):
        print(f"错误: 项目目录不存在 {tester.project_dir}")
        return 1
    
    # 运行测试
    if not tester.run_all_tests():
        print("测试运行失败")
        return 1
    
    # 计算分数
    score_info = tester.calculate_score()
    if score_info:
        print(f"\n{'='*60}")
        print(f"📊 测试结果总览")
        print(f"{'='*60}")
        print(f"📝 总测试项: {score_info['total_tests']}")
        print(f"✅ 通过测试: {score_info['passed_tests']}")
        print(f"❌ 失败测试: {score_info['failed_tests']}")
        print(f"📈 获得分数: {score_info['total_score']}/{score_info['max_score']}")
        print(f"📊 通过率: {score_info['pass_rate']:.2f}%")
        print(f"🏆 评级: {score_info['grade']}")
        print(f"{'='*60}")
        
        # 显示失败的测试详情
        failed_tests = [r for r in tester.test_results if r["score"] == 0]
        if failed_tests:
            print(f"\n💡 失败测试详情:")
            for i, result in enumerate(failed_tests, 1):
                print(f"\n{i}. {result['metric']}")
                print(f"   📋 描述: {result['description'][:100]}...")
                print(f"   🔍 原因: {result['explanation'].split('\\n')[0]}")
        
        # 给出建议
        if score_info['pass_rate'] < 100:
            print(f"\n💡 改进建议:")
            print(f"   - 检查失败测试的详细日志")
            print(f"   - 确认所有依赖包已正确安装")
            print(f"   - 验证程序启动命令是否正确")
            print(f"   - 查看程序是否正确响应用户输入")
    
    # 保存结果
    output_file = os.path.join(tester.project_dir, "reports", "judge_test_results.jsonl")
    report_file, detailed_file = tester.save_results(output_file)
    
    print(f"\n✨ 测试完成!")
    print(f"📊 查看完整结果: {report_file}")
    print(f"🔍 查看调试日志: {detailed_file}")
    
    # 根据通过率返回退出码
    final_pass_rate = score_info['pass_rate'] if score_info else 0
    return 0 if final_pass_rate >= 60 else 1

if __name__ == "__main__":
    sys.exit(main())