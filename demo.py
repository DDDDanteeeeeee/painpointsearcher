"""
小红书自动化系统 - 独立演示版

展示核心功能，不依赖复杂模块
"""

from openai import OpenAI
import json
from datetime import datetime
from pathlib import Path

# ============ 配置 ============
DEEPSEEK_API_KEY = "sk-b07c9af227fa49b68ff1f6e4ae36465f"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ============ 核心 LLM 类 ============
class SimpleLLM:
    """简化的 LLM 类"""
    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """生成回复"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=2000,
            temperature=0.0
        )

        return response.choices[0].message.content

# ============ Prompt 模板 ============
SYSTEM_PROMPT = """你是一个专业的小红书内容分析和创作助手，具备以下能力：

1. **热点敏感度**：能快速识别小红书平台上的热点话题和趋势
2. **用户洞察**：深刻理解小红书用户的心理、需求和痛点
3. **内容创作**：能创作符合小红书风格的高质量内容（真实、有用、有温度）

你的工作原则：
- 只分析真实的数据，不编造信息
- 生成的回复必须真实、有价值，不能是垃圾广告
- 保持小红书社区的真实氛围
- 尊重用户，提供真诚的帮助
"""

HOT_TOPIC_ANALYSIS_PROMPT = """请分析以下小红书热点内容，挖掘潜在的用户需求和商业价值：

## 热点内容：
标题：{title}
内容：{content}

## 分析要求：

1. **用户痛点分析**
   - 用户在抱怨什么问题？
   - 用户表达了什么不满？

2. **潜在需求挖掘**
   - 这个热点反映了什么未被满足的需求？
   - 用户愿意为解决这个问题付出什么（时间、金钱）？

3. **商业价值评估**
   - 是否有变现可能？
   - 目标用户群体的消费能力如何？

请以简洁明了的方式输出分析结果。
"""

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

请生成 3 个不同版本的回复，每个版本要有：
- 独特的切入角度
- 不同的表达风格
- 高度相关的内容

## 输出格式：
### 版本 1：【{angle}】
{回复内容}

### 版本 2：【{angle}】
{回复内容}

### 版本 3：【{angle}】
{回复内容}
"""

# ============ 演示函数 ============
def demo_api_test():
    """演示 1: API 测试"""
    print("=" * 60)
    print("🧪 演示 1: DeepSeek API 测试")
    print("=" * 60)
    print()

    llm = SimpleLLM()

    print("💬 发送测试消息...")
    response = llm.generate(
        "你好，请简单介绍一下你自己",
        "你是一个友好的 AI 助手"
    )

    print()
    print("🤖 DeepSeek 回复:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    print()

def demo_topic_analysis():
    """演示 2: 热点分析"""
    print("=" * 60)
    print("📊 演示 2: 热点需求分析")
    print("=" * 60)
    print()

    # 示例热点
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
    print(f"📄 热点内容: {content[:100]}...")
    print()
    print("🔍 正在分析...")
    print()

    llm = SimpleLLM()
    prompt = HOT_TOPIC_ANALYSIS_PROMPT.format(
        title=title,
        content=content
    )

    response = llm.generate(prompt, SYSTEM_PROMPT)

    print("📊 分析结果:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    print()

def demo_content_generation():
    """演示 3: 内容生成"""
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
    print("✍️  正在生成回复...")
    print()

    llm = SimpleLLM()
    prompt = CONTENT_GENERATION_PROMPT.format(
        title=title,
        pain_point=pain_point,
        demand=demand,
        angle="经验分享"
    )

    response = llm.generate(prompt, SYSTEM_PROMPT)

    print("💬 生成的回复:")
    print("-" * 60)
    print(response)
    print("-" * 60)
    print()

# ============ 主函数 ============
def main():
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "小红书自动化系统" + " " * 25 + "║")
    print("║" + " " * 12 + "🔥 热点挖掘 · 需求分析 · 智能回复" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    print("📋 系统状态:")
    print(f"   ✅ DeepSeek API: 已配置")
    print(f"   ✅ API Key: {DEEPSEEK_API_KEY[:8]}...{DEEPSEEK_API_KEY[-4:]}")
    print(f"   ✅ 模型: deepseek-chat")
    print()

    print("🎯 选择演示:")
    print("1. API 连接测试")
    print("2. 热点需求分析（示例）")
    print("3. 回复内容生成（示例）")
    print("4. 运行完整演示（全部）")
    print()

    choice = input("请选择 (1-4): ").strip()

    print()

    if choice == "1":
        demo_api_test()
    elif choice == "2":
        demo_topic_analysis()
    elif choice == "3":
        demo_content_generation()
    elif choice == "4":
        demo_api_test()
        input("\n按回车继续...")
        print()
        demo_topic_analysis()
        input("\n按回车继续...")
        print()
        demo_content_generation()
    else:
        print("❌ 无效选择")

    print()
    print("=" * 60)
    print("✅ 演示完成！")
    print("=" * 60)
    print()
    print("📚 更多功能:")
    print("   - 查看 XIAOHONGSHU_ARCHITECTURE.md 了解系统架构")
    print("   - 查看 XIAOHONGSHU_README.md 了解完整功能")
    print("   - 查看 WEB_README.md 了解 Web 界面")
    print()
    print("🚀 下一步:")
    print("   1. 使用 Python 3.11/3.12 环境运行完整版")
    print("   2. 或基于此演示代码定制你的需求")
    print()

if __name__ == "__main__":
    main()
    input("按回车键退出...")
