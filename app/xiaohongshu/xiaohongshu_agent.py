"""
小红书主 Agent

整合所有模块，实现完整的工作流程
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from app.llm import LLM
from app.logger import logger
from app.xiaohongshu.config import get_config
from app.xiaohongshu.hot_topics import HotTopicsCollector, HotTopic
from app.xiaohongshu.demand_analyzer import DemandAnalyzer, TopicAnalysis
from app.xiaohongshu.content_generator import ContentGenerator, ReplySet
from app.xiaohongshu.auto_replier import AutoReplier
from app.xiaohongshu.safety_controller import SafetyController
from app.xiaohongshu.prompts import get_prompt


class WorkflowResult(BaseModel):
    """工作流结果"""
    success: bool = Field(description="是否成功")
    topics_collected: int = Field(default=0, description="收集的热点数")
    topics_analyzed: int = Field(default=0, description="分析的话题数")
    replies_generated: int = Field(default=0, description="生成的回复数")
    replies_sent: int = Field(default=0, description="发送的回复数")
    duration_seconds: float = Field(default=0, description="耗时（秒）")
    errors: List[str] = Field(default_factory=list, description="错误列表")


class XiaohongshuAgent:
    """小红书 Agent"""

    def __init__(self):
        self.config = get_config().get()
        self.llm = LLM()

        # 初始化各模块
        self.collector = HotTopicsCollector()
        self.analyzer = DemandAnalyzer()
        self.generator = ContentGenerator()
        self.replier = AutoReplier()
        self.safety = SafetyController()

        self._initialized = False

    async def initialize(self):
        """初始化 Agent"""
        if self._initialized:
            return

        logger.info("初始化小红书 Agent...")

        # 创建必要的目录
        self.config.workspace_root.mkdir(parents=True, exist_ok=True)
        self.config.hot_topics_dir.mkdir(parents=True, exist_ok=True)
        self.config.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.config.content_dir.mkdir(parents=True, exist_ok=True)
        self.config.logs_dir.mkdir(parents=True, exist_ok=True)

        self._initialized = True
        logger.info("✅ Agent 初始化完成")

    async def run_full_workflow(self, max_topics: int = 20, max_replies: int = 5) -> WorkflowResult:
        """
        运行完整工作流

        Args:
            max_topics: 最大收集热点数
            max_replies: 最大回复数

        Returns:
            工作流结果
        """
        await self.initialize()

        start_time = datetime.now()
        result = WorkflowResult(success=True)

        logger.info("=" * 60)
        logger.info("🚀 开始小红书自动化工作流")
        logger.info("=" * 60)

        try:
            # Phase 1: 收集热点
            logger.info("\n📍 Phase 1: 收集热点")
            topics = await self.safety.execute_with_safety(
                self.collector.collect_from_explore_page,
                "collect_hot_topics",
                max_topics
            )

            if not topics:
                logger.warning("未收集到热点，工作流终止")
                result.success = False
                return result

            result.topics_collected = len(topics)
            logger.info(f"✅ 收集到 {len(topics)} 个热点")

            # Phase 2: 分析需求
            logger.info("\n📍 Phase 2: 分析需求")
            analyses = await self.safety.execute_with_safety(
                self.analyzer.analyze_batch,
                "analyze_topics",
                topics
            )

            result.topics_analyzed = len(analyses)
            logger.info(f"✅ 分析了 {len(analyses)} 个话题")

            # 获取 TOP 话题
            top_topics = self.analyzer.get_top_topics(analyses, top_n=max_replies)
            logger.info(f"\n🏆 TOP {len(top_topics)} 高价值话题：")
            for i, analysis in enumerate(top_topics, 1):
                logger.info(f"  {i}. {analysis.topic.title} (优先级: {analysis.priority:.2f})")

            # Phase 3: 生成回复
            logger.info("\n📍 Phase 3: 生成回复内容")
            reply_sets = []

            for i, analysis in enumerate(top_topics, 1):
                logger.info(f"\n[{i}/{len(top_topics)}] 为 '{analysis.topic.title}' 生成回复...")

                # 检查是否可以回复
                can_reply, reason = self.replier.can_reply_now()
                if not can_reply:
                    logger.warning(f"跳过: {reason}")
                    continue

                # 生成回复
                reply_set = await self.safety.execute_with_safety(
                    self.generator.generate_replies,
                    "generate_replies",
                    analysis,
                    num_versions=5
                )

                if reply_set and reply_set.best_reply:
                    reply_sets.append(reply_set)
                    result.replies_generated += 1

                    # Phase 4: 发送回复（半自动）
                    if self.config.require_human_review:
                        logger.info("\n📍 Phase 4: 准备发送（需人工确认）")
                        success = await self.safety.execute_with_safety(
                            self.replier.send_reply,
                            "send_reply",
                            reply_set.best_reply,
                            analysis.topic.url,
                            analysis.topic.title,
                            auto_send=False
                        )

                        if success:
                            result.replies_sent += 1
                            logger.info("✅ 回复发送成功")
                        else:
                            logger.warning("❌ 回复发送失败或被取消")

                    # 频率控制
                    if i < len(top_topics):
                        await self.safety.apply_random_delay("between_replies")

            # 生成日报
            if self.config.save_analysis_report:
                await self._generate_daily_report(topics, analyses, reply_sets)

        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            result.success = False
            result.errors.append(str(e))

        # 统计耗时
        result.duration_seconds = (datetime.now() - start_time).total_seconds()

        logger.info("\n" + "=" * 60)
        logger.info("📊 工作流执行结果:")
        logger.info(f"  - 收集热点: {result.topics_collected} 个")
        logger.info(f"  - 分析话题: {result.topics_analyzed} 个")
        logger.info(f"  - 生成回复: {result.replies_generated} 个")
        logger.info(f"  - 发送回复: {result.replies_sent} 个")
        logger.info(f"  - 总耗时: {result.duration_seconds:.1f} 秒")
        logger.info("=" * 60)

        return result

    async def collect_only(self, max_topics: int = 20) -> List[HotTopic]:
        """仅收集热点"""
        await self.initialize()

        logger.info("📍 收集热点...")

        topics = await self.safety.execute_with_safety(
            self.collector.collect_from_explore_page,
            "collect_hot_topics",
            max_topics
        )

        logger.info(f"✅ 收集到 {len(topics)} 个热点")
        return topics

    async def analyze_only(self, topics: List[HotTopic]) -> List[TopicAnalysis]:
        """仅分析热点"""
        await self.initialize()

        logger.info(f"📍 分析 {len(topics)} 个热点...")

        analyses = await self.safety.execute_with_safety(
            self.analyzer.analyze_batch,
            "analyze_topics",
            topics
        )

        logger.info(f"✅ 分析完成")
        return analyses

    async def generate_only(self, analyses: List[TopicAnalysis], max_replies: int = 5) -> List[ReplySet]:
        """仅生成回复"""
        await self.initialize()

        logger.info(f"📍 为 TOP {max_replies} 话题生成回复...")

        top_topics = self.analyzer.get_top_topics(analyses, top_n=max_replies)
        reply_sets = []

        for i, analysis in enumerate(top_topics, 1):
            logger.info(f"[{i}/{len(top_topics)}] {analysis.topic.title}")

            reply_set = await self.safety.execute_with_safety(
                self.generator.generate_replies,
                "generate_replies",
                analysis
            )

            if reply_set:
                reply_sets.append(reply_set)

        logger.info(f"✅ 生成 {len(reply_sets)} 组回复")
        return reply_sets

    async def reply_one(self, url: str, auto_send: bool = False) -> bool:
        """
        为单个帖子生成并发送回复

        Args:
            url: 帖子链接
            auto_send: 是否自动发送

        Returns:
            是否成功
        """
        await self.initialize()

        logger.info(f"📍 处理单个帖子: {url}")

        try:
            # 收集
            topic = await self.collector.collect_from_specific_url(url)
            if not topic:
                logger.error("无法收集帖子信息")
                return False

            # 分析
            analysis = await self.analyzer.analyze_topic(topic)

            # 生成
            reply_set = await self.generator.generate_replies(analysis)
            if not reply_set or not reply_set.best_reply:
                logger.error("无法生成回复")
                return False

            # 发送
            success = await self.replier.send_reply(
                reply_set.best_reply,
                url,
                topic.title,
                auto_send=auto_send
            )

            return success

        except Exception as e:
            logger.error(f"处理失败: {e}")
            return False

    async def _generate_daily_report(
        self,
        topics: List[HotTopic],
        analyses: List[TopicAnalysis],
        reply_sets: List[ReplySet]
    ):
        """生成日报"""
        logger.info("生成日报...")

        # 准备数据
        daily_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "topics_count": len(topics),
            "top_topics": [
                {
                    "title": t.topic.title,
                    "url": t.topic.url,
                    "priority": t.priority,
                    "commercial_value": t.commercial_value
                }
                for t in analyses[:5]
            ],
            "replies_generated": len(reply_sets),
            "replies": [
                {
                    "topic": rs.topic_title,
                    "best_content": rs.best_reply.content if rs.best_reply else "",
                    "score": rs.best_reply.overall_score if rs.best_reply else 0
                }
                for rs in reply_sets
            ]
        }

        # 使用 LLM 生成报告
        try:
            prompt = get_prompt('daily_report', daily_data=str(daily_data))
            report = self.llm.generate(
                prompt=prompt,
                system_prompt=get_prompt('system')
            )

            # 保存报告
            report_path = self.config.logs_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"✅ 日报已保存: {report_path}")

        except Exception as e:
            logger.warning(f"生成日报失败: {e}")

    async def cleanup(self):
        """清理资源"""
        logger.info("清理资源...")
        # 清理浏览器等资源
        self._initialized = False
