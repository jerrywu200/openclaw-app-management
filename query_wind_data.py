#!/usr/bin/env python3
"""
使用 Computer Use Agent 查询风电数据
"""

import sys
import os
sys.path.append('/Users/jw/.openclaw/workspace')

# 设置 API Key
os.environ['DASHSCOPE_API_KEY'] = 'sk-sp-a35e73b47fe74d12805863a65c06064c'
os.environ['DASHSCOPE_BASE_URL'] = 'https://coding.dashscope.aliyuncs.com/v1'

from computer_use import ComputerUseAgent

print("=" * 70)
print("Computer Use Agent - 查询风电数据")
print("=" * 70)

# 创建代理
agent = ComputerUseAgent()
agent.max_steps = 20  # 设置最大步数

print(f"\n✅ Agent 已创建")
print(f"   视觉模型：{agent.vision.vision_model.model_type}")
print(f"   最大步数：{agent.max_steps}")

# 任务
task = "查询中国风电装机数据，包括 2024 年和 2025 年的新增装机和累计装机"
app_name = "Wind"

print(f"\n【任务】")
print(f"   {task}")
print(f"   应用：{app_name}")

print("\n" + "=" * 70)
print("开始执行...")
print("=" * 70)

# 执行任务
result = agent.run(task, app_name)

# 显示结果
print("\n" + "=" * 70)
print("执行结果")
print("=" * 70)

print(f"\n成功：{result['success']}")
print(f"步数：{result['steps']}")
print(f"耗时：{result['elapsed']:.1f}秒")

# 显示执行历史
print(f"\n执行历史 ({len(result['history'])} 步):")
for i, step in enumerate(result['history'], 1):
    action = step.get('action', {})
    action_type = action.get('action', 'unknown')
    reason = action.get('reason', '')
    print(f"  {i}. {action_type} - {reason[:50] if reason else ''}")

# 保存结果
import json
output_path = '/Users/jw/.openclaw/workspace/wind_data_query_result.json'
with open(output_path, 'w', encoding='utf-8') as f:
    # 简化历史，避免序列化问题
    simple_result = {
        'success': result['success'],
        'steps': result['steps'],
        'elapsed': result['elapsed'],
        'task': task,
        'app': app_name,
    }
    json.dump(simple_result, f, ensure_ascii=False, indent=2)

print(f"\n结果已保存：{output_path}")
print("\n" + "=" * 70)
print("任务完成!")
print("=" * 70)

EOF
