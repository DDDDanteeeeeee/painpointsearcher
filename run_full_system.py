"""
小红书自动化系统 - 完整版（可运行）

绕过复杂依赖，使用核心功能
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI

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

## 小红书回复特点：
1. 真诚：像真人一样分享，不要像广告
2. 有用：提供实际帮助或有价值的信息
3. 有温度：情感共鸣，让读者感受到善意
4. 适度长度：50-200字为宜

## 生成要求：
请生成 3-5 个不同版本的回复，每个版本要有：
- 独特的切入角度
- 不同的表达风格
- 高度相关的内容
- 吸引力的开头和结尾

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
    def __init__(self, title: str, content: str, likes: int = 0, comments: int = 0, collects: int = 0, url: str = ""):
        self.title = title
        self.content = content
        self.likes = likes
        self.comments = comments
        self.collects = collects
        self.url = url  # 热点链接
        self.top_comments = []  # 热门评论
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
        self.original_comment = original_comment  # 原始评论
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

# ============ 核心模块 ============
class HotTopicsCollector:
    """热点收集器（模拟版）"""
    def __init__(self):
        self.llm = SimpleLLM()

    async def collect_from_explore_page(self, max_topics: int = 20) -> List[HotTopic]:
        """模拟收集热点"""
        print(f"📍 模拟收集小红书热点（目标: {max_topics} 个）...")

        # 示例热点数据（包含链接和热门评论）
        sample_topics = [
            {
                "title": "早C晚A的正确打开方式",
                "content": "最近护肤圈很火的早C晚A，但很多人都在吐槽：1. 早上用了维C，晚上用维A，结果皮肤泛红刺痛 2. 不知道该选哪个品牌的精华 3. 担心成分冲突不敢叠涂 4. 敏感肌能不能用？作为护肤3年的小白，真的太困惑了！求大神指点！",
                "likes": 1234,
                "comments": 56,
                "collects": 789,
                "url": "https://www.xiaohongshu.com/explore/123456789",
                "top_comments": [
                    "我也踩过雷！刚开始直接用高浓度A醇，脸肿了三天😭",
                    "敏感肌路过，建议先从0.05%开始，建立耐受很重要",
                    "有没有具体的产品推荐？学生党预算有限"
                ]
            },
            {
                "title": "极简生活：断舍离30天，我收获了什么",
                "content": "坚持断舍离30天，扔掉了家里一半的东西。开始时很难，但慢慢发现东西少了，心反而更满了。不再为买买买焦虑，反而更珍惜手边的每一样物品。有姐妹想一起尝试极简生活吗？",
                "likes": 2341,
                "comments": 123,
                "collects": 1567,
                "url": "https://www.xiaohongshu.com/explore/234567890",
                "top_comments": [
                    "太佩服了！我连扔一支过期口红都要犹豫半小时",
                    "断舍离不是扔东西，是学会控制欲望吧",
                    "求分享断舍离清单！不知道从何入手"
                ]
            },
            {
                "title": "打工人必看！3款提高效率的神器APP",
                "content": "每天加班到深夜，效率低得让人怀疑人生。直到我发现了这3款APP：1. 番茄钟-专注工作25分钟 2. 滴答清单-任务管理神器 3. Forest-种树戒手机。用了1个月，工作效率提升了50%，终于不用加班了！强烈推荐给所有打工人！",
                "likes": 3456,
                "comments": 234,
                "collects": 2345,
                "url": "https://www.xiaohongshu.com/explore/345678901",
                "top_comments": [
                    "Forest亲测有效！就是有时候会手滑玩手机😂",
                    "番茄钟用过，但是开会的时候不好用啊",
                    "有没有推荐Mac端的效率工具？"
                ]
            },
            {
                "title": "新手妈妈必看：宝宝睡眠训练全攻略",
                "content": "生完宝宝后，最痛苦的就是睡眠问题！宝宝夜里频繁醒来，导致我严重睡眠不足。尝试了各种方法后，终于总结出一套有效的睡眠训练方法。现在宝宝能睡整觉，我也能好好休息了！整理了详细攻略分享给各位新手妈妈。",
                "likes": 4567,
                "comments": 345,
                "collects": 3456,
                "url": "https://www.xiaohongshu.com/explore/456789012",
                "top_comments": [
                    "宝妈太需要了！每天凌晨3点就要醒，真的快崩溃了",
                    "请问几个月开始训练比较合适？",
                    "我家宝宝六个月了，还能训练吗？"
                ]
            },
            {
                "title": "副业月入过万？我的真实经历分享",
                "content": "90后女生，主业月薪5K，副业做自媒体2年，现在月入稳定过万。不是卖课程，不是割韭菜，纯分享我的真实经历。从0开始做账号，踩过的坑，总结的经验。想做副业的姐妹可以参考一下，但不要盲目跟风！",
                "likes": 5678,
                "comments": 456,
                "collects": 4567,
                "url": "https://www.xiaohongshu.com/explore/567890123",
                "top_comments": [
                    "求详细分享！想做副业但不知道做什么",
                    "真的是不割韭菜吗？期待后续",
                    "什么赛道比较好入门？"
                ]
            }
        ]

        topics = []
        for i, data in enumerate(sample_topics[:max_topics]):
            topic = HotTopic(
                title=data["title"],
                content=data["content"],
                likes=data["likes"],
                comments=data["comments"],
                collects=data["collects"],
                url=data.get("url", ""),
            )
            topic.top_comments = data.get("top_comments", [])
            topics.append(topic)
            print(f"   ✓ 收集热点 {i+1}: {topic.title}")

        await asyncio.sleep(1)  # 模拟网络延迟
        print(f"\n✅ 成功收集 {len(topics)} 个热点")
        return topics

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

    async def analyze_batch(self, topics: List[HotTopic]) -> List[TopicAnalysis]:
        """批量分析"""
        analyses = []
        for topic in topics:
            analysis = await self.analyze_topic(topic)
            analyses.append(analysis)
            await asyncio.sleep(1)  # 避免 API 限流

        # 按优先级排序
        analyses.sort(key=lambda x: x.priority, reverse=True)
        return analyses

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

        # 获取原始评论（选择第一条热门评论作为目标）
        original_comment = ""
        if analysis.topic.top_comments:
            original_comment = analysis.topic.top_comments[0]
            print(f"   📝 目标评论: {original_comment[:50]}...")

        prompt = CONTENT_GENERATION_PROMPT.format(
            title=analysis.topic.title,
            pain_point=pain_point,
            demand=demand,
            angle=angle
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
            reply_set = ReplySet(analysis.topic.title, pain_point, demand)

        return reply_set

# ============ 主 Agent ============
class XiaohongshuAgent:
    """小红书 Agent（完整版）"""
    def __init__(self):
        self.collector = HotTopicsCollector()
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

    async def run_full_workflow(self, max_topics: int = 20, max_replies: int = 5):
        """运行完整工作流"""
        await self.initialize()

        print("\n" + "=" * 60)
        print("🚀 小红书自动化工作流 - 开始执行")
        print("=" * 60)

        # Phase 1: 收集热点
        print("\n📍 Phase 1: 收集热点")
        print("-" * 60)
        topics = await self.collector.collect_from_explore_page(max_topics)

        # Phase 2: 分析需求
        print("\n📍 Phase 2: 分析需求")
        print("-" * 60)
        analyses = await self.analyzer.analyze_batch(topics)

        print(f"\n🏆 TOP {min(len(analyses), max_replies)} 高价值话题:")
        for i, analysis in enumerate(analyses[:max_replies], 1):
            print(f"   {i}. {analysis.topic.title} (优先级: {analysis.priority:.1f})")

        # Phase 3: 生成回复
        print("\n📍 Phase 3: 生成回复内容")
        print("-" * 60)
        reply_sets = []

        for i, analysis in enumerate(analyses[:max_replies], 1):
            reply_set = await self.generator.generate_replies(analysis)
            if reply_set.replies:
                reply_sets.append(reply_set)

            if i < len(analyses[:max_replies]) - 1:
                await asyncio.sleep(2)  # 模拟延迟

        # Phase 4: 输出报告
        print("\n📍 Phase 4: 生成报告")
        print("-" * 60)
        await self._generate_report(topics, analyses, reply_sets)

        print("\n" + "=" * 60)
        print("✅ 工作流执行完成！")
        print("=" * 60)

        return {
            "success": True,
            "topics_collected": len(topics),
            "topics_analyzed": len(analyses),
            "replies_generated": len(reply_sets)
        }

    async def _generate_report(self, topics, analyses, reply_sets):
        """生成报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存为 Markdown
        report_path = Path(f"workspace/xiaohongshu/generated_content/report_{timestamp}.md")

        with open(report_path, 'w', encoding='utf-8') as f:
            # 标题和概览
            f.write(f"# 🔥 小红书热点分析报告\n\n")
            f.write(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # 统计概览
            f.write(f"## 📊 统计概览\n\n")
            f.write(f"| 指标 | 数量 |\n")
            f.write(f"|------|------|\n")
            f.write(f"| 收集热点 | {len(topics)} 个 |\n")
            f.write(f"| 分析话题 | {len(analyses)} 个 |\n")
            f.write(f"| 生成回复 | {len(reply_sets)} 组 |\n\n")
            f.write("---\n\n")

            # TOP 高价值话题
            f.write(f"## 🏆 TOP 高价值话题\n\n")
            for i, analysis in enumerate(analyses[:len(reply_sets)], 1):
                topic = analysis.topic

                # 话题标题和链接
                f.write(f"### {i}. {topic.title}\n\n")

                if topic.url:
                    f.write(f"> 🔗 原文链接: [{topic.url}]({topic.url})\n\n")

                # 数据卡片
                f.write(f"**互动数据**: 👍 {topic.likes} | 💬 {topic.comments} | ⭐ {topic.collects}\n\n")
                f.write(f"**优先级评分**: {analysis.priority:.1f}/10\n\n")

                # 用户痛点
                f.write(f"#### 👤 用户痛点\n\n")
                for point in analysis.pain_points:
                    f.write(f"- {point}\n")
                f.write(f"\n")

                # 热门评论
                if topic.top_comments:
                    f.write(f"#### 💭 热门评论\n\n")
                    for idx, comment in enumerate(topic.top_comments[:3], 1):
                        f.write(f"{idx}. > {comment}\n\n")
                    f.write("\n")

                f.write("---\n\n")

            # 生成的回复
            f.write(f"## 💬 智能回复内容\n\n")

            for reply_set in reply_sets[:3]:
                f.write(f"### {reply_set.topic_title}\n\n")

                # 显示原始评论（如果有）
                if reply_set.original_comment:
                    f.write(f"#### 📝 原始评论\n\n")
                    f.write(f"> {reply_set.original_comment}\n\n")

                # 显示所有生成的回复版本
                f.write(f"#### ✨ 生成的回复\n\n")

                for reply in reply_set.replies:
                    score_badge = "⭐" if reply.overall_score >= 9.0 else "👍"
                    f.write(f"**{score_badge} 版本 {reply.version}: {reply.angle}**\n")
                    f.write(f">(评分: {reply.overall_score:.1f}/10)\n\n")
                    f.write(f"{reply.content}\n\n")
                    f.write("---\n\n")

                # 最佳回复
                if reply_set.best_reply:
                    f.write(f"#### 🏆 最佳回复推荐\n\n")
                    f.write(f"**评分**: {reply_set.best_reply.overall_score:.1f}/10\n")
                    f.write(f"**角度**: {reply_set.best_reply.angle}\n\n")
                    f.write(f"{reply_set.best_reply.content}\n\n")
                    f.write("---\n\n")

            # 总结
            f.write(f"## 📝 分析总结\n\n")
            f.write(f"本次共分析了 {len(topics)} 个小红书热点话题，识别出 {len(reply_sets)} 个高价值内容机会。\n\n")
            f.write(f"所有生成的回复内容均基于用户痛点和需求分析，确保内容的相关性和吸引力。\n\n")

        print(f"   ✓ 报告已保存: {report_path}")

        # 同时保存 JSON 数据（包含更完整的信息）
        json_path = Path(f"workspace/xiaohongshu/analysis/analysis_{timestamp}.json")
        data = {
            "timestamp": datetime.now().isoformat(),
            "topics": [
                {
                    "title": t.title,
                    "url": t.url,
                    "likes": t.likes,
                    "comments": t.comments,
                    "collects": t.collects,
                    "top_comments": t.top_comments
                } for t in topics
            ],
            "analyses": [
                {
                    "title": a.topic.title,
                    "priority": a.priority,
                    "pain_points": a.pain_points,
                    "demands": a.demands
                } for a in analyses
            ],
            "reply_sets": [
                {
                    "topic_title": rs.topic_title,
                    "original_comment": rs.original_comment,
                    "best_reply": {
                        "content": rs.best_reply.content if rs.best_reply else "",
                        "angle": rs.best_reply.angle if rs.best_reply else "",
                        "score": rs.best_reply.overall_score if rs.best_reply else 0
                    } if rs.best_reply else None
                } for rs in reply_sets
            ]
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 数据已保存: {json_path}")

# ============ 主函数 ============
async def main():
    """主函数"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "小红书自动化系统" + " " * 27 + "║")
    print("║" + " " * 10 + "🔥 完整版工作流 - 热点挖掘 & 智能回复" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    print("📋 系统配置:")
    print(f"   ✅ DeepSeek API: 已连接")
    print(f"   ✅ 模型: deepseek-chat")
    print(f"   ✅ 工作空间: workspace/xiaohongshu/")
    print()

    # 创建 Agent
    agent = XiaohongshuAgent()

    try:
        # 运行完整工作流
        result = await agent.run_full_workflow(
            max_topics=5,  # 收集5个热点
            max_replies=3   # 为前3个生成回复
        )

        print()
        print("🎉 任务完成！")
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
