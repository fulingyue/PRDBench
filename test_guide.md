# PRDBench 测试流程指南

## 第一步：使用Prompt获取代码

将 `claude_code_prompt_simple.md` 的内容发送给Claude Code，让它生成完整的餐厅供应链系统代码。

## 第二步：准备测试环境

```bash
# 确保代码在正确位置
确认Claude Code生成的代码已放在：/Users/yuzhengxu/projects/PRDBench/PRDBench/1/src/
```

## 第三步：快速验证

```bash
# 进入代码目录
cd /Users/yuzhengxu/projects/PRDBench/PRDBench/1/src

# 1. 检查是否能启动
python main.py

# 2. 检查基本结构
ls -la
```

## 第四步：自动化测试

```bash
# 回到PRDBench根目录
cd /Users/yuzhengxu/projects/PRDBench

# 运行judge测试脚本
python test_with_judge.py --project_id 1 --workspace_path /Users/yuzhengxu/projects/PRDBench/PRDBench
```

## 第五步：查看结果

```bash
# 查看测试报告
cat /Users/yuzhengxu/projects/PRDBench/PRDBench/1/reports/judge_test_results.jsonl
```

**准备好了吗？发送prompt给Claude Code开始测试！** 🚀