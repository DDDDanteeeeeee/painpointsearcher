"""
单独运行演示 2: 热点分析
"""

from openai import OpenAI

DEEPSEEK_API_KEY = "sk-b07c9af227fa49b68ff1f6e4ae36465f"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

SYSTEM_PROMPT = """你是一个专业的小红书内容分析和创作助手。"""

HOT_TOPIC_ANALYSIS_PROMPT = """请分析以下小红书热点内容，挖掘潜在的用户需求和商业价值：

## 热点内容：
标题：{title}
内容：{content}

## 分析要求：

1. **用户痛点分析**
   - 用户在抱怨什么问题？

2. **潜在需求挖掘**
   - 这个热点反映了什么未被满足的需求？

3. **商业价值评估**
   - 是否有变现可能？

请以简洁明了的方式输出分析结果。
"""

print("=" * 60)
print("📊 演示 2: 热点需求分析")
print("=" * 60)
print()

title = "早C晚A的正确打开方式"
content = """
最近护肤圈很火的早C晚A，但很多人都在吐槽：
1. 早上用了维C，晚上用维A，结果皮肤泛红刺痛
2. 不知道该选哪个品牌的精华
3. 担心成分冲突不敢叠涂
4. 敏感肌能不能用？

作为护肤3年的小白，真的太困惑了！求大神指点！
"""

print(f"📝 热点标题: {title}")
print(f"📄 热点内容摘要: {content[:80]}...")
print()
print("🔍 DeepSeek 正在分析...")
print()

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

prompt = HOT_TOPIC_ANALYSIS_PROMPT.format(title=title, content=content)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ],
    max_tokens=1500
)

result = response.choices[0].message.content

print("📊 分析结果:")
print("-" * 60)
print(result)
print("-" * 60)
print()
print("✅ 分析完成！")
