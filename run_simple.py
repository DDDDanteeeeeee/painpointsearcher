"""
小红书自动化系统 - 简化版启动脚本

绕过复杂依赖，直接运行核心功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🚀 小红书自动化系统 - 启动中...")
print("=" * 60)
print()

# 导入核心模块
try:
    from app.xiaohongshu.hot_topics import HotTopicsCollector
    from app.xiaohongshu.demand_analyzer import DemandAnalyzer
    from app.xiaohongshu.content_generator import ContentGenerator
    from app.xiaohongshu.safety_controller import SafetyController
    from app.xiaohongshu.config import get_config
    from app.llm import LLM
    print("✅ 核心模块加载成功")
except Exception as e:
    print(f"❌ 模块加载失败: {e}")
    print()
    print("请检查依赖是否安装完整")
    input("按回车键退出...")
    sys.exit(1)

print()
print("📋 可用功能:")
print("1. 测试 DeepSeek API")
print("2. 分析热点内容（手动输入）")
print("3. 生成回复内容")
print()

choice = input("请选择功能 (1/2/3): ").strip()

if choice == "1":
    print()
    print("=" * 60)
    print("🧪 测试 DeepSeek API")
    print("=" * 60)
    print()

    from openai import OpenAI
    client = OpenAI(
        api_key="sk-b07c9af227fa49b68ff1f6e4ae36465f",
        base_url="https://api.deepseek.com"
    )

    prompt = input("请输入测试消息: ").strip()
    if not prompt:
        prompt = "你好，请介绍一下你自己"

    print(f"\n📨 发送: {prompt}")
    print()

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

    result = response.choices[0].message.content
    print(f"🤖 DeepSeek 回复:")
    print("-" * 60)
    print(result)
    print("-" * 60)

elif choice == "2":
    print()
    print("=" * 60)
    print("📊 分析热点内容")
    print("=" * 60)
    print()

    title = input("请输入热点标题: ").strip()
    content = input("请输入热点内容: ").strip()

    if not title or not content:
        print("❌ 标题和内容不能为空")
    else:
        print()
        print("🔍 正在分析...")

        from app.xiaohongshu.prompts import get_prompt

        llm = LLM()
        prompt = get_prompt(
            'hot_topic_analysis',
            title=title,
            content=content,
            likes=100,
            comments=50,
            collects=80,
            top_comments="用户A: 太实用了\n用户B: 求推荐"
        )

        response = llm.generate(
            prompt=prompt,
            system_prompt=get_prompt('system')
        )

        print()
        print("📝 分析结果:")
        print("-" * 60)
        print(response)
        print("-" * 60)

elif choice == "3":
    print()
    print("=" * 60)
    print("💬 生成回复内容")
    print("=" * 60)
    print()

    title = input("请输入帖子标题: ").strip()
    pain_point = input("请输入用户痛点: ").strip()
    demand = input("请输入核心需求: ").strip()

    if not title:
        print("❌ 标题不能为空")
        pain_point = "需要解决这个问题"
        demand = "用户希望获得帮助"

    print()
    print("✍️ 正在生成回复...")

    from app.xiaohongshu.prompts import get_prompt

    llm = LLM()
    prompt = get_prompt(
        'content_generation',
        title=title,
        pain_point=pain_point or "需要解决具体问题",
        demand=demand or "用户需要获得帮助",
        angle="经验分享"
    )

    response = llm.generate(
        prompt=prompt,
        system_prompt=get_prompt('system')
    )

    print()
    print("📝 生成的回复:")
    print("-" * 60)
    print(response)
    print("-" * 60)

else:
    print("❌ 无效选择")

print()
print("=" * 60)
print("✅ 运行完成！")
print("=" * 60)
print()
input("按回车键退出...")
