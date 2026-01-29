"""
单独运行演示 3: 生成回复
"""

from openai import OpenAI

DEEPSEEK_API_KEY = "sk-b07c9af227fa49b68ff1f6e4ae36465f"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

SYSTEM_PROMPT = """你是一个专业的小红书内容创作助手。"""

CONTENT_GENERATION_PROMPT = """为小红书帖子生成高质量的回复内容。

## 目标帖子信息：
标题：{title}
用户痛点：{pain_point}
核心需求：{demand}

## 小红书回复特点：
1. 真诚：像真人一样分享，不要像广告
2. 有用：提供实际帮助或有价值的信息
3. 有温度：情感共鸣，让读者感受到善意
4. 适度长度：50-200字为宜

请生成 3 个不同版本的回复。

## 输出格式：
### 版本 1：【专业科普】
(回复内容)

### 版本 2：【经验分享】
(回复内容)

### 版本 3：【情感共鸣】
(回复内容)
"""

print("=" * 60)
print("✍️  演示 3: 回复内容生成")
print("=" * 60)
print()

title = "早C晚A的正确打开方式"
pain_point = "早C晚A护肤步骤混乱，担心成分冲突，敏感肌不敢用"
demand = "需要了解正确的护肤流程和产品搭配建议"

print(f"📝 帖子标题: {title}")
print(f"😟 用户痛点: {pain_point}")
print(f"🎯 核心需求: {demand}")
print()
print("✍️  DeepSeek 正在生成回复...")
print()

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

prompt = CONTENT_GENERATION_PROMPT.format(
    title=title,
    pain_point=pain_point,
    demand=demand
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ],
    max_tokens=1500
)

result = response.choices[0].message.content

print("💬 生成的回复:")
print("-" * 60)
print(result)
print("-" * 60)
print()
print("✅ 内容生成完成！")
