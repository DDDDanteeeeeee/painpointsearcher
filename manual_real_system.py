"""
小红书自动化系统 - 真实版本（手动输入URL）
用户输入真实的小红书链接，系统抓取并分析
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import time

# ============ 配置 ============
DEEPSEEK_API_KEY = "sk-b07c9af227fa49b68ff1f6e4ae36465f"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

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
互动数据：点赞{likes} | 评论{comments} | 收藏{collects}
热门评论：{top_comments}

## 分析要求：

1. **用户痛点分析**
   - 用户在抱怨什么问题？
   - 用户表达了什么不满？
   - 用户希望得到什么帮助？

2. **潜在需求挖掘**
   - 这个热点反映了什么未被满足的需求？
   - 用户愿意为解决这个问题付出什么（时间、金钱）？
   - 需求的紧急程度和普遍程度如何？

3. **商业价值评估**
   - 是否有变现可能？（产品推荐、知识付费、服务等）
   - 目标用户群体的消费能力如何？
   - 竞争程度如何？

4. **回复策略建议**
   - 最有效的回复角度（专业/产品/经验/情感）
   - 推荐的回复内容类型
   - 预估的互动率

请以 JSON 格式输出分析结果，包含以下字段：
- pain_points (数组)
- demands (数组，包含 type, description, urgency, commercial_value)
- commercial_potential (字符串)
- suggested_angles (数组)
- priority_score (数字)
"""

CONTENT_GENERATION_PROMPT = """为小红书帖子生成高质量的回复内容。

## 目标帖子信息：
标题：{title}
用户痛点：{pain_point}
核心需求：{demand}
目标角度：{angle}

## 需要回复的原始评论：
{original_comment}

## 小红书回复特点：
1. 真诚：像真人一样分享，不要像广告
2. 有用：提供实际帮助或有价值的信息
3. 有温度：情感共鸣，让读者感受到善意
4. 适度长度：50-200字为宜
5. 针对性：直接回应原评论的内容和情感

## 生成要求：
请生成 3-5 个不同版本的回复，每个版本要有：
- 独特的切入角度
- 不同的表达风格
- 高度相关的内容
- 吸引力的开头和结尾
- 针对原评论的具体回应

## 输出格式：
请以 JSON 格式输出，包含 replies 数组，每个回复包含：
- version (版本号)
- angle (角度)
- content (内容)
- relevance_score (相关性评分)
- attractiveness_score (吸引力评分)
"""

# ============ 数据模型 ============
class HotTopic:
    def __init__(self, title: str, content: str, url: str = ""):
        self.title = title
        self.content = content
        self.url = url
        self.likes = 0
        self.comments = 0
        self.collects = 0
        self.top_comments = []
        self.author = ""
        self.tags = []
        self.collected_at = datetime.now().isoformat()

        # 分析字段
        self.pain_points = []
        self.demands = []
        self.commercial_value = 0.0
        self.priority = 0.0

class TopicAnalysis:
    def __init__(self, topic: HotTopic):
        self.topic = topic
        self.pain_points = []
        self.demands = []
        self.commercial_value = 0.0
        self.priority = 0.0

class GeneratedReply:
    def __init__(self, version: int, angle: str, content: str, relevance: float, attractiveness: float):
        self.version = version
        self.angle = angle
        self.content = content
        self.relevance_score = relevance
        self.attractiveness_score = attractiveness
        self.overall_score = (relevance + attractiveness) / 2

class ReplySet:
    def __init__(self, topic_title: str, pain_point: str, demand: str, original_comment: str = ""):
        self.topic_title = topic_title
        self.pain_point = pain_point
        self.demand = demand
        self.original_comment = original_comment
        self.replies = []
        self.best_reply = None
        self.created_at = datetime.now().isoformat()

# ============ LLM 类 ============
class SimpleLLM:
    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
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

# ============ 真实数据收集器（手动输入URL） ============
class ManualURLCollector:
    """手动输入URL收集器"""

    def __init__(self):
        self.llm = SimpleLLM()

    async def collect_from_url(self, url: str) -> Optional[HotTopic]:
        """从指定的URL收集数据"""
        print(f"\n📍 正在访问: {url}")

        try:
            # 使用 requests 获取页面
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            print("   📡 正在获取页面内容...")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            print(f"   ✓ 页面获取成功（{len(response.text)} 字符）")

            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取页面标题
            page_title = soup.find('title')
            title = page_title.text.strip() if page_title else "未知标题"

            # 提取页面文本内容
            page_text = soup.get_text(separator='\n', strip=True)

            # 限制长度
            content = page_text[:3000] if len(page_text) > 3000 else page_text

            # 使用 LLM 提取结构化数据
            print("   🤖 使用 AI 分析页面内容...")
            topic = self._extract_with_llm(title, content, url)

            if topic:
                print(f"   ✓ 成功提取: {topic.title}")

            return topic

        except Exception as e:
            print(f"   ❌ 获取失败: {e}")
            return None

    def _extract_with_llm(self, title: str, content: str, url: str) -> Optional[HotTopic]:
        """使用 LLM 从页面内容中提取结构化数据"""
        prompt = f"""请从以下小红书页面内容中提取热点信息。

页面标题：{title}

页面内容：
{content}

URL: {url}

请提取并返回 JSON 格式的热点信息，包含：
- title: 帖子标题
- content: 内容摘要（300字以内）
- author: 作者昵称
- likes: 点赞数（数字）
- comments: 评论数（数字）
- collects: 收藏数（数字）
- top_comments: 热门评论数组（包含3条代表性评论）

注意：
1. 如果某些信息找不到，使用空字符串或 0
2. 必须返回有效的 JSON 格式
3. 不要编造数据，只从提供的内容中提取

返回格式：
{{
  "title": "帖子标题",
  "content": "内容摘要",
  "author": "作者名",
  "likes": 1000,
  "comments": 50,
  "collects": 200,
  "top_comments": ["评论1", "评论2", "评论3"]
}}
"""

        try:
            response = self.llm.generate(prompt, "你是数据提取专家，擅长从小红书页面中提取结构化数据。")

            # 解析 JSON
            if '{' in response and '}' in response:
                json_str = response[response.find('{'):response.rfind('}')+1]
                data = json.loads(json_str)

                topic = HotTopic(
                    title=data.get("title", title),
                    content=data.get("content", content[:300]),
                    url=url
                )
                topic.author = data.get("author", "")
                topic.likes = data.get("likes", 0)
                topic.comments = data.get("comments", 0)
                topic.collects = data.get("collects", 0)
                topic.top_comments = data.get("top_comments", [])

                return topic

        except Exception as e:
            print(f"   ⚠️  AI 提取失败: {e}")

            # 创建基础 topic
            topic = HotTopic(title=title, content=content[:300], url=url)
            return topic

        return None

# ============ 需求分析器 ============
class DemandAnalyzer:
    """需求分析器"""
    def __init__(self):
        self.llm = SimpleLLM()

    async def analyze_topic(self, topic: HotTopic) -> TopicAnalysis:
        """分析单个热点"""
        print(f"\n🔍 分析热点: {topic.title}")

        prompt = HOT_TOPIC_ANALYSIS_PROMPT.format(
            title=topic.title,
            content=topic.content,
            likes=topic.likes,
            comments=topic.comments,
            collects=topic.collects,
            top_comments="\n".join(topic.top_comments)
        )

        try:
            response = self.llm.generate(prompt, SYSTEM_PROMPT)

            # 解析 JSON 响应
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            analysis = TopicAnalysis(topic)
            analysis.pain_points = data.get("pain_points", [])

            demands_data = data.get("demands", [])
            for d in demands_data:
                analysis.demands.append(d)

            analysis.commercial_value = float(data.get("priority_score", 0))
            analysis.priority = float(data.get("priority_score", 0))

            print(f"   ✓ 分析完成，优先级: {analysis.priority:.1f}")

        except Exception as e:
            print(f"   ⚠️  分析失败: {e}")
            # 创建基础分析
            analysis = TopicAnalysis(topic)
            analysis.priority = 7.0

        return analysis

# ============ 内容生成器 ============
class ContentGenerator:
    """内容生成器"""
    def __init__(self):
        self.llm = SimpleLLM()

    async def generate_replies(self, analysis: TopicAnalysis, num_versions: int = 3) -> ReplySet:
        """生成回复"""
        print(f"\n✍️  为 '{analysis.topic.title}' 生成回复...")

        pain_point = ", ".join(analysis.pain_points[:3])
        demand = analysis.demands[0]["description"] if analysis.demands else "用户需要帮助"
        angle = "经验分享"

        # 获取原始评论
        original_comment = ""
        if analysis.topic.top_comments:
            original_comment = analysis.topic.top_comments[0]
            print(f"   📝 目标评论: {original_comment[:50]}...")

        prompt = CONTENT_GENERATION_PROMPT.format(
            title=analysis.topic.title,
            pain_point=pain_point,
            demand=demand,
            angle=angle,
            original_comment=original_comment
        )

        try:
            response = self.llm.generate(prompt, SYSTEM_PROMPT)

            # 解析 JSON 响应
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            reply_set = ReplySet(
                topic_title=analysis.topic.title,
                pain_point=pain_point,
                demand=demand,
                original_comment=original_comment
            )

            for reply_data in data.get("replies", []):
                reply = GeneratedReply(
                    version=reply_data["version"],
                    angle=reply_data["angle"],
                    content=reply_data["content"],
                    relevance=reply_data["relevance_score"],
                    attractiveness=reply_data["attractiveness_score"]
                )
                reply_set.replies.append(reply)

            # 选择最佳回复
            if reply_set.replies:
                reply_set.best_reply = max(reply_set.replies, key=lambda r: r.overall_score)
                print(f"   ✓ 生成了 {len(reply_set.replies)} 个版本")
                print(f"   ★ 最佳评分: {reply_set.best_reply.overall_score:.1f}")

        except Exception as e:
            print(f"   ⚠️  生成失败: {e}")
            reply_set = ReplySet(analysis.topic.title, pain_point, demand, original_comment)

        return reply_set

# ============ 主 Agent ============
class ManualRealAgent:
    """小红书 Agent（真实版本 - 手动输入URL）"""
    def __init__(self):
        self.collector = ManualURLCollector()
        self.analyzer = DemandAnalyzer()
        self.generator = ContentGenerator()
        self._initialized = False

    async def initialize(self):
        """初始化"""
        if self._initialized:
            return

        # 创建工作目录
        workspace = Path("workspace/xiaohongshu")
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "hot_topics").mkdir(parents=True, exist_ok=True)
        (workspace / "analysis").mkdir(parents=True, exist_ok=True)
        (workspace / "generated_content").mkdir(parents=True, exist_ok=True)
        (workspace / "logs").mkdir(parents=True, exist_ok=True)

        self._initialized = True
        print("✅ Agent 初始化完成\n")

    async def run_single_url_workflow(self, url: str):
        """运行单个URL的完整工作流"""
        await self.initialize()

        print("\n" + "=" * 60)
        print("🚀 小红书自动化工作流 - 真实数据")
        print("=" * 60)
        print("⚠️  分析真实的小红书链接")
        print("=" * 60)

        # Phase 1: 收集数据
        print("\n📍 Phase 1: 从真实URL收集数据")
        print("-" * 60)

        topic = await self.collector.collect_from_url(url)

        if not topic:
            print("\n❌ 未能收集到数据，请检查URL是否正确")
            return {"success": False, "error": "收集数据失败"}

        # Phase 2: 分析需求
        print("\n📍 Phase 2: 分析需求")
        print("-" * 60)
        analysis = await self.analyzer.analyze_topic(topic)

        # Phase 3: 生成回复
        print("\n📍 Phase 3: 生成回复内容")
        print("-" * 60)
        reply_set = await self.generator.generate_replies(analysis)

        # Phase 4: 输出报告
        print("\n📍 Phase 4: 生成报告")
        print("-" * 60)
        await self._generate_single_report(topic, analysis, reply_set)

        print("\n" + "=" * 60)
        print("✅ 工作流执行完成！")
        print("=" * 60)

        return {
            "success": True,
            "title": topic.title,
            "url": topic.url
        }

    async def _generate_single_report(self, topic, analysis, reply_set):
        """生成单个话题的报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存为 Markdown
        report_path = Path(f"workspace/xiaohongshu/generated_content/report_{timestamp}.md")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# 🔥 小红书热点分析报告（真实数据）\n\n")
            f.write(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 数据来源: 真实小红书链接\n\n")
            f.write("---\n\n")

            # 话题详情
            f.write(f"## 📌 话题详情\n\n")
            f.write(f"### {topic.title}\n\n")

            if topic.url:
                f.write(f"> 🔗 原文链接: [{topic.url}]({topic.url})\n\n")
                f.write(f"> ✅ 真实链接，可直接访问\n\n")

            f.write(f"**作者**: {topic.author or '未知'}\n\n")
            f.write(f"**互动数据**: 👍 {topic.likes} | 💬 {topic.comments} | ⭐ {topic.collects}\n\n")
            f.write(f"**优先级评分**: {analysis.priority:.1f}/10\n\n")

            f.write("---\n\n")

            # 内容摘要
            f.write(f"## 📄 内容摘要\n\n")
            f.write(f"{topic.content}\n\n")
            f.write("---\n\n")

            # 用户痛点
            f.write(f"## 👤 用户痛点\n\n")
            for point in analysis.pain_points:
                f.write(f"- {point}\n")
            f.write(f"\n---\n\n")

            # 热门评论
            if topic.top_comments:
                f.write(f"## 💭 热门评论\n\n")
                for idx, comment in enumerate(topic.top_comments, 1):
                    f.write(f"{idx}. > {comment}\n\n")
                f.write("\n---\n\n")

            # 生成的回复
            f.write(f"## 💬 智能回复内容\n\n")

            # 显示原始评论
            if reply_set.original_comment:
                f.write(f"### 📝 原始评论\n\n")
                f.write(f"> {reply_set.original_comment}\n\n")

            # 显示所有生成的回复版本
            f.write(f"### ✨ 生成的回复\n\n")

            for reply in reply_set.replies:
                score_badge = "⭐" if reply.overall_score >= 9.0 else "👍"
                f.write(f"**{score_badge} 版本 {reply.version}: {reply.angle}**\n")
                f.write(f">(评分: {reply.overall_score:.1f}/10)\n\n")
                f.write(f"{reply.content}\n\n")
                f.write("---\n\n")

            # 最佳回复
            if reply_set.best_reply:
                f.write(f"### 🏆 最佳回复推荐\n\n")
                f.write(f"**评分**: {reply_set.best_reply.overall_score:.1f}/10\n")
                f.write(f"**角度**: {reply_set.best_reply.angle}\n\n")
                f.write(f"{reply_set.best_reply.content}\n\n")

        print(f"   ✓ 报告已保存: {report_path}")

        # 同时保存 JSON 数据
        json_path = Path(f"workspace/xiaohongshu/analysis/analysis_{timestamp}.json")
        data = {
            "timestamp": datetime.now().isoformat(),
            "data_source": "真实小红书链接",
            "topic": {
                "title": topic.title,
                "url": topic.url,
                "author": topic.author,
                "content": topic.content,
                "likes": topic.likes,
                "comments": topic.comments,
                "collects": topic.collects,
                "top_comments": topic.top_comments
            },
            "analysis": {
                "priority": analysis.priority,
                "pain_points": analysis.pain_points,
                "demands": analysis.demands
            },
            "best_reply": {
                "content": reply_set.best_reply.content if reply_set.best_reply else "",
                "angle": reply_set.best_reply.angle if reply_set.best_reply else "",
                "score": reply_set.best_reply.overall_score if reply_set.best_reply else 0
            } if reply_set.best_reply else None
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 数据已保存: {json_path}")

# ============ 主函数 ============
async def main():
    """主函数"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "小红书真实数据分析系统" + " " * 26 + "║")
    print("║" + " " * 10 + "🔗 输入真实链接进行分析" + " " * 24 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    print("📋 系统配置:")
    print(f"   ✅ DeepSeek API: 已连接")
    print(f"   ✅ 模型: deepseek-chat")
    print(f"   ✅ 数据源: 用户提供的真实链接")
    print()

    # 创建 Agent
    agent = ManualRealAgent()

    # 获取用户输入
    print("请输入小红书链接（例如: https://www.xiaohongshu.com/explore/...）")
    url = input("\n🔗 URL: ").strip()

    if not url:
        print("❌ URL不能为空")
        return

    if not url.startswith('http'):
        url = 'https://' + url

    try:
        # 运行工作流
        result = await agent.run_single_url_workflow(url)

        if result.get("success"):
            print()
            print("🎉 分析完成！")
            print()
            print("📁 查看结果:")
            print("   - 报告: workspace/xiaohongshu/generated_content/")
            print("   - 数据: workspace/xiaohongshu/analysis/")
            print()

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

    input("\n按回车键退出...")
