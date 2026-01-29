"""
小红书热点抓取模块

使用 Browser Use 工具抓取小红书热点内容
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.tool.browser_use_tool import BrowserUseTool
from app.tool.crawl4ai import Crawl4aiTool
from app.llm import LLM
from app.logger import logger
from app.xiaohongshu.config import get_config


class HotTopic(BaseModel):
    """热点数据模型"""
    title: str = Field(description="标题")
    content: str = Field(description="内容摘要")
    url: str = Field(description="帖子链接")
    author: str = Field(default="", description="作者")
    likes: int = Field(default=0, description="点赞数")
    comments: int = Field(default=0, description="评论数")
    collects: int = Field(default=0, description="收藏数")
    shares: int = Field(default=0, description="分享数")
    top_comments: List[str] = Field(default_factory=list, description="热门评论")
    tags: List[str] = Field(default_factory=list, description="标签")
    collected_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="采集时间")

    # 分析字段
    pain_points: List[str] = Field(default_factory=list, description="用户痛点")
    demands: List[str] = Field(default_factory=list, description="潜在需求")
    commercial_value: float = Field(default=0.0, description="商业价值评分 0-10")
    priority: float = Field(default=0.0, description="优先级评分 0-10")


class HotTopicsCollector:
    """热点收集器"""

    def __init__(self):
        self.config = get_config().get()
        self.browser_tool = BrowserUseTool()
        self.crawl_tool = Crawl4aiTool()
        self.llm = LLM()

    async def collect_from_explore_page(self, max_topics: int = 20) -> List[HotTopic]:
        """
        从小红书探索页收集热点

        Args:
            max_topics: 最大收集数量

        Returns:
            热点列表
        """
        logger.info(f"开始收集小红书热点，目标数量: {max_topics}")

        try:
            # 访问小红书探索页
            await self._goto_explore_page()

            # 等待页面加载
            await asyncio.sleep(3)

            # 滚动加载更多内容
            await self._scroll_to_load_content()

            # 提取热点内容
            topics = await self._extract_topics(max_topics)

            # 保存数据
            await self._save_topics(topics)

            logger.info(f"成功收集 {len(topics)} 个热点")
            return topics

        except Exception as e:
            logger.error(f"收集热点失败: {e}")
            return []

    async def _goto_explore_page(self):
        """访问小红书探索页"""
        logger.info(f"访问小红书探索页: {self.config.hot_topic_url}")

        result = await self.browser_tool.execute(
            action="go_to_url",
            url=self.config.hot_topic_url
        )

        if result.error:
            raise Exception(f"访问探索页失败: {result.error}")

    async def _scroll_to_load_content(self, scroll_times: int = 3):
        """滚动加载更多内容"""
        logger.info(f"滚动加载内容，滚动次数: {scroll_times}")

        for i in range(scroll_times):
            # 模拟人类滚动速度
            await asyncio.sleep(2)
            result = await self.browser_tool.execute(
                action="scroll_down",
                scroll_amount=800
            )

            if result.error:
                logger.warning(f"滚动失败: {result.error}")

    async def _extract_topics(self, max_topics: int) -> List[HotTopic]:
        """
        从页面提取热点内容

        这里使用两种方法：
        1. Browser Use 的 extract_content 功能
        2. Crawl4AI 的网页抓取功能
        """
        logger.info("开始提取热点内容")

        topics = []

        # 方法1: 使用 Browser Use 提取
        try:
            result = await self.browser_tool.execute(
                action="extract_content",
                goal=f"""提取小红书热点内容，包括：
                1. 帖子标题
                2. 内容摘要
                3. 点赞数、评论数、收藏数
                4. 链接
                5. 标签

                提取前 {max_topics} 个帖子，以 JSON 格式返回。"""
            )

            if result.output and not result.error:
                # 解析提取的内容
                topics = self._parse_extracted_content(result.output, max_topics)
                logger.info(f"Browser Use 提取到 {len(topics)} 个热点")

        except Exception as e:
            logger.warning(f"Browser Use 提取失败: {e}，尝试使用 Crawl4AI")

            # 方法2: 使用 Crawl4AI
            try:
                result = await self.crawl_tool.execute(
                    urls=[self.config.hot_topic_url],
                    timeout=30
                )

                if result.output and not result.error:
                    topics = self._parse_crawled_content(result.output, max_topics)
                    logger.info(f"Crawl4AI 提取到 {len(topics)} 个热点")

            except Exception as e2:
                logger.error(f"Crawl4AI 也失败了: {e2}")

        return topics[:max_topics]

    def _parse_extracted_content(self, content: str, max_topics: int) -> List[HotTopic]:
        """解析 Browser Use 提取的内容"""
        topics = []

        try:
            # 尝试解析 JSON
            if content.strip().startswith('['):
                data = json.loads(content)
                for item in data[:max_topics]:
                    topics.append(HotTopic(**item))
            else:
                # 如果不是 JSON，使用 LLM 提取结构化数据
                topics = self._extract_with_llm(content, max_topics)

        except Exception as e:
            logger.warning(f"JSON 解析失败: {e}，使用 LLM 提取")
            topics = self._extract_with_llm(content, max_topics)

        return topics

    def _parse_crawled_content(self, content: str, max_topics: int) -> List[HotTopic]:
        """解析 Crawl4AI 抓取的内容"""
        # Crawl4AI 返回 Markdown，使用 LLM 提取结构化数据
        return self._extract_with_llm(content, max_topics)

    def _extract_with_llm(self, content: str, max_topics: int) -> List[HotTopic]:
        """使用 LLM 从文本中提取结构化数据"""
        prompt = f"""从以下小红书页面内容中提取热点信息。

{content[:10000]}

请提取前 {max_topics} 个热点，以 JSON 数组格式返回，每个热点包含：
- title: 标题
- content: 内容摘要（100字以内）
- url: 链接
- author: 作者
- likes: 点赞数
- comments: 评论数
- collects: 收藏数
- tags: 标签列表

如果某个字段找不到，使用空字符串或 0。"""

        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt="你是数据提取专家，擅长从非结构化文本中提取结构化数据。"
            )

            # 解析 LLM 返回的 JSON
            if '[' in response and ']' in response:
                json_str = response[response.find('['):response.rfind(']')+1]
                data = json.loads(json_str)

                topics = []
                for item in data:
                    topics.append(HotTopic(**item))
                return topics

        except Exception as e:
            logger.error(f"LLM 提取失败: {e}")

        return []

    async def _save_topics(self, topics: List[HotTopic]):
        """保存热点数据"""
        if not self.config.save_analysis_report:
            return

        # 保存为 JSON
        self.config.hot_topics_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        file_path = self.config.hot_topics_dir / f"hot_topics_{date_str}.json"

        data = [topic.model_dump() for topic in topics]
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"热点数据已保存到: {file_path}")

    async def collect_from_specific_url(self, url: str) -> Optional[HotTopic]:
        """从特定 URL 收集单个热点"""
        try:
            result = await self.crawl_tool.execute(
                urls=[url],
                timeout=30
            )

            if result.output and not result.error:
                topics = self._parse_crawled_content(result.output, 1)
                if topics:
                    return topics[0]

        except Exception as e:
            logger.error(f"从 URL 收集失败: {e}")

        return None
