import json
import subprocess
import os
import sys
import time
from datetime import datetime
import argparse

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='PRDBench测试评估工具')
    parser.add_argument('--project', '-p', nargs='*', type=int,
                       help='指定要测试的PRD项目编号 (例如: 1 2)，不指定则测试当前目录项目')
    parser.add_argument('--tests', '-t', nargs='*', 
                       help='指定要运行的测试用例ID (例如: 1.1.1 1.2.1)，不指定则运行全部')
    parser.add_argument('--output', '-o', default='test_results.json',
                       help='输出结果文件名 (默认: test_results.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细输出')
    return parser.parse_args()

def load_test_plan(project_id):
    """加载测试计划"""
    plan_file = f'/Users/yuzhengxu/projects/PRDBench/PRDBench/{project_id}/evaluation/detailed_test_plan.json'
    try:
        with open(plan_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到测试计划文件 {plan_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"错误: 测试计划文件格式错误 - {e}")
        return None

def filter_tests(plan, test_ids):
    """根据指定的测试ID过滤测试"""
    if not test_ids:
        return plan
    
    filtered = []
    for test in plan:
        # 提取测试ID (例如从 "1.1.1 Main Menu Function..." 提取 "1.1.1")
        test_id = test['metric'].split(' ')[0]
        if test_id in test_ids:
            filtered.append(test)
    
    # 检查是否有无效的测试ID
    found_ids = [test['metric'].split(' ')[0] for test in filtered]
    invalid_ids = set(test_ids) - set(found_ids)
    if invalid_ids:
        print(f"警告: 未找到测试ID: {', '.join(invalid_ids)}")
    
    return filtered

def run_readme_check(test_id, project_dir, verbose=False):
    """检查README.md是否符合要求"""
    import re
    start_time = time.time()

    readme_path = os.path.join(project_dir, 'src', 'README.md')
    if not os.path.exists(readme_path):
        readme_path = os.path.join(project_dir, 'README.md')

    if not os.path.exists(readme_path):
        end_time = time.time()
        return [{
            'test_case_id': f"{test_id}.1",
            'command': f"file_comparison: check README.md in {project_dir}",
            'success': False,
            'return_code': 1,
            'execution_time': round(end_time - start_time, 3),
            'stdout': '',
            'stderr': f'README.md not found in {project_dir} or {project_dir}/src'
        }]

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        end_time = time.time()
        return [{
            'test_case_id': f"{test_id}.1",
            'command': f"file_comparison: read {readme_path}",
            'success': False,
            'return_code': 1,
            'execution_time': round(end_time - start_time, 3),
            'stdout': '',
            'stderr': f'Failed to read README.md: {e}'
        }]

    sections = re.findall(r'^#{1,3}\s+.+', readme_content, re.MULTILINE)
    has_enough_sections = len(sections) >= 3

    content_lower = readme_content.lower()
    has_intro = any(kw in content_lower for kw in ['introduction', 'overview', 'about', '介绍', '简介', '概述', 'features', 'description'])
    has_setup = any(kw in content_lower for kw in ['install', 'setup', 'environment', 'dependencies', 'requirements', '安装', '环境', '依赖'])
    has_run = any(kw in content_lower for kw in ['run', 'start', 'usage', 'how to', 'getting started', '运行', '启动', '使用'])

    success = has_enough_sections and has_intro and has_setup and has_run
    end_time = time.time()

    stdout_parts = [
        f"README.md found at: {readme_path}",
        f"Sections found ({len(sections)}): {sections[:5]}",
        f"Has intro: {has_intro}, Has setup: {has_setup}, Has run instructions: {has_run}"
    ]
    stderr = ''
    if not success:
        reasons = []
        if not has_enough_sections:
            reasons.append(f"only {len(sections)} sections (need >= 3)")
        if not has_intro:
            reasons.append("missing project introduction")
        if not has_setup:
            reasons.append("missing environment setup instructions")
        if not has_run:
            reasons.append("missing startup commands")
        stderr = "README.md does not meet requirements: " + '; '.join(reasons)

    if verbose:
        print(f"    README检查: sections={len(sections)}, intro={has_intro}, setup={has_setup}, run={has_run}")

    return [{
        'test_case_id': f"{test_id}.1",
        'command': f"file_comparison: check {readme_path}",
        'success': success,
        'return_code': 0 if success else 1,
        'execution_time': round(end_time - start_time, 3),
        'stdout': '\n'.join(stdout_parts),
        'stderr': stderr
    }]


def run_file_comparison_test(test, project_id, verbose=False):
    """运行file_comparison类型的测试"""
    test_id = test['metric'].split(' ')[0]
    project_dir = f'/Users/yuzhengxu/projects/PRDBench/PRDBench/{project_id}'
    expected_files = test.get('expected_output_files') or []

    # 没有expected_output_files时，按README检查处理
    if not expected_files:
        return run_readme_check(test_id, project_dir, verbose)

    results = []

    # 先运行test_command生成输出文件
    for i, tc in enumerate(test.get('testcases', [])):
        cmd = tc.get('test_command')
        if not cmd:
            continue
        test_input = tc.get('test_input')
        if test_input:
            full_cmd = f"cd {project_dir} && {cmd} < {test_input}"
        else:
            full_cmd = f"cd {project_dir} && {cmd}"

        if verbose:
            print(f"    准备文件: {full_cmd}")

        try:
            subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            pass

    # 比较每个expected_output_file
    for i, expected_file in enumerate(expected_files):
        start_time = time.time()
        expected_path = os.path.join(project_dir, expected_file)

        if not os.path.exists(expected_path):
            end_time = time.time()
            results.append({
                'test_case_id': f"{test_id}.{i+1}",
                'command': f"file_comparison: check {expected_path}",
                'success': False,
                'return_code': 1,
                'execution_time': round(end_time - start_time, 3),
                'stdout': '',
                'stderr': f'Expected file not found: {expected_path}'
            })
            continue

        # 推断实际输出文件路径：expected文件名去掉"expected_"前缀
        expected_basename = os.path.basename(expected_file)
        if expected_basename.startswith('expected_'):
            actual_basename = expected_basename[len('expected_'):]
        else:
            actual_basename = expected_basename

        # 在src/和项目根目录下查找实际输出文件
        actual_path = None
        for search_dir in [os.path.join(project_dir, 'src'), project_dir]:
            candidate = os.path.join(search_dir, actual_basename)
            if os.path.exists(candidate):
                actual_path = candidate
                break

        if not actual_path:
            end_time = time.time()
            results.append({
                'test_case_id': f"{test_id}.{i+1}",
                'command': f"file_comparison: find {actual_basename}",
                'success': False,
                'return_code': 1,
                'execution_time': round(end_time - start_time, 3),
                'stdout': '',
                'stderr': f'Actual output file not found: {actual_basename}'
            })
            continue

        # 读取并比较文件内容
        try:
            with open(expected_path, 'r', encoding='utf-8') as f:
                expected_content = f.read().strip()
            with open(actual_path, 'r', encoding='utf-8') as f:
                actual_content = f.read().strip()
        except Exception as e:
            end_time = time.time()
            results.append({
                'test_case_id': f"{test_id}.{i+1}",
                'command': f"file_comparison: read files",
                'success': False,
                'return_code': 1,
                'execution_time': round(end_time - start_time, 3),
                'stdout': '',
                'stderr': f'Failed to read files: {e}'
            })
            continue

        # 检查expected内容中的关键行是否都出现在actual中
        expected_lines = [l.strip() for l in expected_content.splitlines() if l.strip()]
        actual_lower = actual_content.lower()
        # 第一行（header）精确匹配，其余行检查包含关系
        if expected_lines:
            header_match = expected_lines[0].strip().lower() in actual_lower
        else:
            header_match = True
        has_content = len(actual_content.strip()) > 0

        success = header_match and has_content
        end_time = time.time()

        stdout_parts = [
            f"Expected file: {expected_path}",
            f"Actual file: {actual_path}",
            f"Header match: {header_match}, Has content: {has_content}"
        ]
        stderr = ''
        if not success:
            if not has_content:
                stderr = f'Actual file {actual_basename} is empty'
            elif not header_match:
                stderr = f'Header mismatch: expected "{expected_lines[0]}" not found in output'

        if verbose:
            print(f"    文件比较: {actual_basename} vs {expected_basename}, header={header_match}, content={has_content}")

        results.append({
            'test_case_id': f"{test_id}.{i+1}",
            'command': f"file_comparison: {actual_path} vs {expected_path}",
            'success': success,
            'return_code': 0 if success else 1,
            'execution_time': round(end_time - start_time, 3),
            'stdout': '\n'.join(stdout_parts),
            'stderr': stderr
        })

    return results if results else run_readme_check(test_id, project_dir, verbose)


def run_single_test(test, project_id, verbose=False):
    """运行单个测试并返回结果"""
    test_id = test['metric'].split(' ')[0]
    test_type = test.get('type', 'shell_interaction')

    # 处理file_comparison类型的测试
    if test_type == 'file_comparison' or all(tc.get('test_command') is None for tc in test['testcases']):
        return run_file_comparison_test(test, project_id, verbose)

    results = []

    for i, tc in enumerate(test['testcases']):
        cmd = tc['test_command']
        if cmd is None:
            continue
        test_input = tc.get('test_input')

        if test_input:
            full_cmd = f"cd /Users/yuzhengxu/projects/PRDBench/PRDBench/{project_id} && {cmd} < {test_input}"
        else:
            full_cmd = f"cd /Users/yuzhengxu/projects/PRDBench/PRDBench/{project_id} && {cmd}"

        if verbose:
            print(f"    执行: {full_cmd}")

        start_time = time.time()
        try:
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
            timed_out = False
        except subprocess.TimeoutExpired as e:
            # 超时时仍然收集已有的输出
            result = type('Result', (), {
                'returncode': -1,
                'stdout': (e.stdout or b'').decode('utf-8', errors='replace') if isinstance(e.stdout, bytes) else (e.stdout or ''),
                'stderr': (e.stderr or b'').decode('utf-8', errors='replace') if isinstance(e.stderr, bytes) else (e.stderr or ''),
            })()
            timed_out = True
        end_time = time.time()

        execution_time = end_time - start_time
        # 对于无输入的交互式测试，超时但有输出也视为成功（菜单已显示）
        if timed_out and not test_input and result.stdout.strip():
            success = True
        elif timed_out:
            success = False
        else:
            success = result.returncode == 0

        test_result = {
            'test_case_id': f"{test_id}.{i+1}",
            'command': full_cmd,
            'success': success,
            'return_code': result.returncode,
            'execution_time': round(execution_time, 3),
            'stdout': result.stdout,
            'stderr': result.stderr
        }

        results.append(test_result)

        if verbose:
            print(f"    结果: {'✓' if success else '✗'} (用时: {execution_time:.3f}s)")
            if result.stderr:
                print(f"    错误: {result.stderr[:200]}...")

    return results

def generate_metrics(all_results):
    """生成测试指标"""
    total_tests = len(all_results)
    successful_tests = sum(1 for r in all_results if all(tc['success'] for tc in r['test_cases']))
    failed_tests = total_tests - successful_tests
    
    total_execution_time = sum(
        sum(tc['execution_time'] for tc in r['test_cases']) 
        for r in all_results
    )
    
    metrics = {
        'summary': {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': round(successful_tests / total_tests * 100, 2) if total_tests > 0 else 0,
            'total_execution_time': round(total_execution_time, 3)
        },
        'test_details': []
    }
    
    for result in all_results:
        test_id = result['test_id']
        test_cases = result['test_cases']
        success_count = sum(1 for tc in test_cases if tc['success'])
        
        detail = {
            'project_id': result.get('project_id', 'unknown'),
            'test_id': test_id,
            'test_name': result['test_name'],
            'total_cases': len(test_cases),
            'successful_cases': success_count,
            'failed_cases': len(test_cases) - success_count,
            'success_rate': round(success_count / len(test_cases) * 100, 2),
            'execution_time': round(sum(tc['execution_time'] for tc in test_cases), 3)
        }
        metrics['test_details'].append(detail)
    
    return metrics

def load_existing_results(output_file):
    """加载现有测试结果"""
    if not os.path.exists(output_file):
        return {
            'test_history': [],
            'cumulative_results': {},
            'last_updated': None
        }
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        print(f"警告: 无法读取现有结果文件 {output_file}，将创建新文件")
        return {
            'test_history': [],
            'cumulative_results': {},
            'last_updated': None
        }

def merge_results(existing_data, new_results, new_metrics):
    """合并新的测试结果到现有数据中"""
    timestamp = datetime.now().isoformat()
    
    # 添加本次测试到历史记录
    test_session = {
        'timestamp': timestamp,
        'session_metrics': new_metrics,
        'session_results': new_results
    }
    existing_data['test_history'].append(test_session)
    
    # 更新累积结果
    cumulative = existing_data.get('cumulative_results', {})
    
    for result in new_results:
        test_id = result['test_id']
        if test_id not in cumulative:
            cumulative[test_id] = {
                'test_name': result['test_name'],
                'total_runs': 0,
                'successful_runs': 0,
                'last_result': None,
                'last_run_time': None,
                'best_execution_time': float('inf'),
                'test_cases_history': []
            }
        
        # 更新测试统计
        test_data = cumulative[test_id]
        test_data['total_runs'] += 1
        
        # 检查本次是否成功
        current_success = all(tc['success'] for tc in result['test_cases'])
        if current_success:
            test_data['successful_runs'] += 1
            
        test_data['last_result'] = 'success' if current_success else 'failed'
        test_data['last_run_time'] = timestamp
        
        # 更新最佳执行时间
        current_execution_time = sum(tc['execution_time'] for tc in result['test_cases'])
        if current_execution_time < test_data['best_execution_time']:
            test_data['best_execution_time'] = current_execution_time
            
        # 记录测试用例历史
        test_data['test_cases_history'].append({
            'timestamp': timestamp,
            'success': current_success,
            'execution_time': current_execution_time,
            'test_cases': result['test_cases']
        })
    
    existing_data['cumulative_results'] = cumulative
    existing_data['last_updated'] = timestamp
    
    return existing_data

def calculate_cumulative_metrics(cumulative_data):
    """计算累积指标"""
    cumulative_results = cumulative_data.get('cumulative_results', {})
    
    if not cumulative_results:
        return {
            'total_unique_tests': 0,
            'total_test_runs': 0,
            'successful_test_runs': 0,
            'overall_success_rate': 0,
            'test_summary': []
        }
    
    total_runs = 0
    successful_runs = 0
    test_summary = []
    
    for test_id, data in cumulative_results.items():
        total_runs += data['total_runs']
        successful_runs += data['successful_runs']
        
        success_rate = (data['successful_runs'] / data['total_runs'] * 100) if data['total_runs'] > 0 else 0
        
        test_summary.append({
            'test_id': test_id,
            'test_name': data['test_name'],
            'total_runs': data['total_runs'],
            'successful_runs': data['successful_runs'],
            'success_rate': round(success_rate, 2),
            'last_result': data['last_result'],
            'best_execution_time': round(data['best_execution_time'], 3) if data['best_execution_time'] != float('inf') else 0
        })
    
    overall_success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    
    return {
        'total_unique_tests': len(cumulative_results),
        'total_test_runs': total_runs,
        'successful_test_runs': successful_runs,
        'overall_success_rate': round(overall_success_rate, 2),
        'test_summary': sorted(test_summary, key=lambda x: x['test_id'])
    }

def save_results(results, metrics, output_file):
    """保存测试结果和指标（累加模式）"""
    # 加载现有结果
    existing_data = load_existing_results(output_file)
    
    # 合并新结果
    merged_data = merge_results(existing_data, results, metrics)
    
    # 计算累积指标
    cumulative_metrics = calculate_cumulative_metrics(merged_data)
    merged_data['cumulative_metrics'] = cumulative_metrics
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        print(f"\n结果已累加保存到: {output_file}")
        return cumulative_metrics
    except Exception as e:
        print(f"保存结果时出错: {e}")
        return None

def get_current_project_id():
    """获取当前目录对应的项目ID"""
    current_dir = os.getcwd()
    # 从路径中提取项目ID，例如从 /path/PRDBench/2/evaluation 提取 2
    parts = current_dir.split('/')
    for i, part in enumerate(parts):
        if part == 'PRDBench' and i + 1 < len(parts):
            try:
                return int(parts[i + 1])
            except ValueError:
                pass
    return None

def ensure_init_py(project_id):
    """确保src目录下有__init__.py，没有则自动创建"""
    src_dir = f'/Users/yuzhengxu/projects/PRDBench/PRDBench/{project_id}/src'
    init_file = os.path.join(src_dir, '__init__.py')
    if os.path.isdir(src_dir) and not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            pass
        print(f"  ⚙️ 自动创建 {init_file}")


def run_project_tests(project_id, args):
    """运行单个项目的测试"""
    print(f"\n{'='*20} PRD项目 {project_id} {'='*20}")

    # 确保src下有__init__.py
    ensure_init_py(project_id)

    # 加载测试计划
    plan = load_test_plan(project_id)
    if not plan:
        print(f"❌ 跳过项目 {project_id}: 无法加载测试计划")
        return []
    
    # 过滤测试
    if args.tests:
        filtered_plan = filter_tests(plan, args.tests)
    else:
        filtered_plan = plan
    
    if not filtered_plan:
        print(f"❌ 项目 {project_id}: 没有找到要运行的测试")
        return []
    
    print(f"📋 项目 {project_id}: 总共 {len(filtered_plan)} 个测试\n")
    
    # 运行测试
    project_results = []
    for i, test in enumerate(filtered_plan, 1):
        test_id = test['metric'].split(' ')[0]
        test_name = test['metric']
        
        print(f"[{i}/{len(filtered_plan)}] 测试 {test_id}: {test_name[:60]}...")
        
        test_results = run_single_test(test, project_id, args.verbose)
        
        result_summary = {
            'project_id': project_id,
            'test_id': test_id,
            'test_name': test_name,
            'test_cases': test_results
        }
        project_results.append(result_summary)
        
        # 显示测试结果
        success_count = sum(1 for tc in test_results if tc['success'])
        total_count = len(test_results)
        status = "✓" if success_count == total_count else "✗"
        print(f"  {status} {success_count}/{total_count} 通过\n")
    
    return project_results

def main():
    args = parse_arguments()
    
    print("PRDBench多项目测试评估工具")
    print("=" * 60)
    
    # 确定要测试的项目
    if args.project:
        project_ids = args.project
        print(f"🎯 指定测试项目: {', '.join(map(str, project_ids))}")
    else:
        current_project = get_current_project_id()
        if current_project:
            project_ids = [current_project]
            print(f"🏠 当前项目: PRD{current_project}")
        else:
            print("❌ 错误: 无法确定项目ID，请使用 --project 参数指定")
            sys.exit(1)
    
    if args.tests:
        print(f"📝 指定测试用例: {', '.join(args.tests)}")
    
    # 运行所有项目的测试
    all_results = []
    for project_id in project_ids:
        project_results = run_project_tests(project_id, args)
        all_results.extend(project_results)
    
    if not all_results:
        print("\n❌ 没有完成任何测试")
        sys.exit(1)
    
    # 生成指标
    metrics = generate_metrics(all_results)
    
    # 按项目分组显示结果
    projects_summary = {}
    for result in all_results:
        project_id = result.get('project_id', 'unknown')
        if project_id not in projects_summary:
            projects_summary[project_id] = {'total': 0, 'success': 0}
        
        projects_summary[project_id]['total'] += 1
        if all(tc['success'] for tc in result['test_cases']):
            projects_summary[project_id]['success'] += 1
    
    # 显示本次测试总结
    print("\n" + "=" * 60)
    print("📊 本次测试总结:")
    
    # 按项目显示结果
    for project_id, summary in projects_summary.items():
        success_rate = (summary['success'] / summary['total'] * 100) if summary['total'] > 0 else 0
        status_emoji = "✅" if success_rate == 100 else "⚠️" if success_rate >= 50 else "❌"
        print(f"  {status_emoji} PRD项目 {project_id}: {summary['success']}/{summary['total']} ({success_rate:.1f}%)")
    
    print(f"\n🎯 总体统计:")
    print(f"  测试项目数: {len(projects_summary)}")
    print(f"  总测试数: {metrics['summary']['total_tests']}")
    print(f"  成功: {metrics['summary']['successful_tests']}")
    print(f"  失败: {metrics['summary']['failed_tests']}")
    print(f"  成功率: {metrics['summary']['success_rate']}%")
    print(f"  总用时: {metrics['summary']['total_execution_time']}秒")
    
    # 保存结果并获取累积指标
    cumulative_metrics = save_results(all_results, metrics, args.output)
    
    if cumulative_metrics:
        # 显示累积统计
        print("\n" + "=" * 50)
        print("📊 累积测试统计:")
        print(f"  累积测试总数: {cumulative_metrics['total_test_runs']} 次")
        print(f"  不同测试项目: {cumulative_metrics['total_unique_tests']} 个")
        print(f"  累积成功: {cumulative_metrics['successful_test_runs']} 次")
        print(f"  累积失败: {cumulative_metrics['total_test_runs'] - cumulative_metrics['successful_test_runs']} 次")
        print(f"  🎯 总体准确率: {cumulative_metrics['overall_success_rate']}%")
        
        # 显示各测试项目的详细统计
        if args.verbose and cumulative_metrics['test_summary']:
            print("\n📋 各测试用例统计:")
            for test_stat in cumulative_metrics['test_summary']:
                status_emoji = "✅" if test_stat['last_result'] == 'success' else "❌"
                print(f"  {status_emoji} {test_stat['test_id']}: {test_stat['successful_runs']}/{test_stat['total_runs']} ({test_stat['success_rate']}%)")
        
        print("\n💡 提示: 使用 --verbose 查看详细统计")
        print("💡 使用 --project 1 2 测试多个项目")

if __name__ == "__main__":
    main()
