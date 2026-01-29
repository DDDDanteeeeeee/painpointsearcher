"""
测试 DeepSeek API 连接
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI

print("=" * 60)
print("🔍 DeepSeek API 连接测试")
print("=" * 60)
print()

print("📡 正在连接 DeepSeek API...")
print()

try:
    client = OpenAI(
        api_key="sk-b07c9af227fa49b68ff1f6e4ae36465f",
        base_url="https://api.deepseek.com"
    )

    print("💬 发送测试消息...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "你好，请回复 '连接成功'"}],
        max_tokens=50
    )

    result = response.choices[0].message.content
    print(f"✅ DeepSeek 连接成功！")
    print(f"📨 AI 回复: {result}")
    print()
    print("=" * 60)
    print("🎉 API 配置验证通过！")
    print("=" * 60)

except Exception as e:
    print(f"❌ 连接失败: {e}")
    print()
    print("可能的原因:")
    print("1. API Key 不正确")
    print("2. 网络连接问题")
    print("3. DeepSeek API 服务异常")
