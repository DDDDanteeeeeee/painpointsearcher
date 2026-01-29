"""
需求分析模块

使用 LLM 分析热点，挖掘用户需求和商业价值
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.llm import LLM
from app.logger import logger
from app.xiaohongshu.config import get_config
from app.xiaohongshu.hot_topics import HotTopic
from app.xiaohongshu.prompts import get_prompt


class DemandInsight(BaseModel):
    """需求洞察"""
    demand_type: str = Field(description="需求类型：工具/知识/情感")
    description: str = Field(description="需求描述")
    urgency: float = Field(default=0.0, ge=0, le=10, description="紧急性 0-10")
    universality: float = Field(default=0.0, ge=0, le=10, description="普遍性 0-10")
    commerciality: float = Field(default=0.0, ge=0, le=10, description="商业性 0-10")
    feasibility: float = Field(default=0.0, ge=0, le=10, description="可行性 0-10")
    total_score: float = Field(default=0.0, ge=0, le=10, description="总分 0-10")

    solution_directions: List[str] = Field(default_factory=list, description="解决方案方向")


class TopicAnalysis(BaseModel):
    """话题分析结果"""
    topic: HotTopic = Field(description="原始热点数据")

    # 用户痛点
    pain_points: List[str] = Field(default_factory=list, description="用户痛点列表")

    # 需求洞察
    demands: List[DemandInsight] = Field(default_factory=list, description="需求列表")

    # 商业价值
    commercial_value: float = Field(default=0.0, ge=0, le=10, description="商业价值评分")
    target_audience: str = Field(default="", description="目标用户群体")
    consumption_power: str = Field(default="", description="消费能力评估")
    competition_level: str = Field(default="", description="竞争程度")

    # 回复策略
    suggested_angles: List[str] = Field(default_factory=list, description="建议的回复角度")
    expected_engagement: str = Field(default="", description="预期互动率")

    # 优先级
    priority: float = Field(default=0.0, ge=0, le=10, description="优先级评分")

    analyzed_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class DemandAnalyzer:
    """需求分析器"""

    def __init__(self):
        self.config = get_config().get()
        self.llm = LLM()

    async def analyze_topic(self, topic: HotTopic) -> TopicAnalysis:
        """
        分析单个热点，挖掘需求

        Args:
            topic: 热点数据

        Returns:
            分析结果
        """
        logger.info(f"开始分析热点: {topic.title}")

        try:
            # 使用 LLM 分析
            prompt = get_prompt(
                'hot_topic_analysis',
                title=topic.title,
                content=topic.content[:500],
                likes=topic.likes,
                comments=topic.comments,
                collects=topic.collects,
                top_comments='\n'.join(topic.top_comments[:5])
            )

            response = await self._call_llm_with_retry(prompt)

            # 解析分析结果
            analysis = self._parse_analysis_response(topic, response)

            # 计算优先级
            analysis.priority = self._calculate_priority(analysis)

            # 保存分析结果
            await self._save_analysis(analysis)

            logger.info(f"分析完成，优先级: {analysis.priority:.2f}")
            return analysis

        except Exception as e:
            logger.error(f"分析失败: {e}")
            return TopicAnalysis(topic=topic)

    async def analyze_batch(self, topics: List[HotTopic]) -> List[TopicAnalysis]:
        """批量分析热点"""
        analyses = []

        for topic in topics:
            try:
                analysis = await self.analyze_topic(topic)
                analyses.append(analysis)

                # 避免 API 限流
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"分析热点失败 {topic.title}: {e}")

        # 按优先级排序
        analyses.sort(key=lambda x: x.priority, reverse=True)

        return analyses

    async def mine_deep_demands(self, analysis: TopicAnalysis) -> List[DemandInsight]:
        """深入挖掘需求"""
        logger.info("深入挖掘需求...")

        try:
            prompt = get_prompt(
                'demand_mining',
                previous_analysis=analysis.model_dump_json(indent=2)
            )

            response = await self._call_llm_with_retry(prompt)

            # 解析需求
            demands = self._parse_demands(response)

            # 更新分析结果
            analysis.demands = demands

            return demands

        except Exception as e:
            logger.error(f"深入挖掘失败: {e}")
            return []

    async def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """带重试的 LLM 调用"""
        for attempt in range(max_retries):
            try:
                response = self.llm.generate(
                    prompt=prompt,
                    system_prompt=get_prompt('system')
                )
                return response

            except Exception as e:
                logger.warning(f"LLM 调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    raise

    def _parse_analysis_response(self, topic: HotTopic, response: str) -> TopicAnalysis:
        """解析 LLM 分析响应"""
        try:
            # 尝试提取 JSON
            if '{' in response and '}' in response:
                json_str = response[response.find('{'):response.rfind('}')+1]
                data = json.loads(json_str)

                # 创建分析结果
                analysis = TopicAnalysis(topic=topic)

                # 填充字段
                analysis.pain_points = data.get('pain_points', [])
                analysis.commercial_value = data.get('commercial_value', 0)
                analysis.target_audience = data.get('target_audience', '')
                analysis.consumption_power = data.get('consumption_power', '')
                analysis.competition_level = data.get('competition_level', '')
                analysis.suggested_angles = data.get('suggested_angles', [])
                analysis.expected_engagement = data.get('expected_engagement', '')

                return analysis

        except Exception as e:
            logger.warning(f"JSON 解析失败: {e}")

        # 如果解析失败，返回基础分析
        return TopicAnalysis(topic=topic)

    def _parse_demands(self, response: str) -> List[DemandInsight]:
        """解析需求列表"""
        demands = []

        try:
            # 尝试提取 JSON 数组
            if '[' in response and ']' in response:
                json_str = response[response.find('['):response.rfind(']')+1]
                data = json.loads(json_str)

                for item in data:
                    demands.append(DemandInsight(**item))

        except Exception as e:
            logger.warning(f"需求解析失败: {e}")

        return demands

    def _calculate_priority(self, analysis: TopicAnalysis) -> float:
        """计算优先级"""
        # 综合考虑多个因素
        weights = {
            'commercial_value': 0.3,
            'engagement': 0.2,
            'demand_urgency': 0.3,
            'feasibility': 0.2,
        }

        # 互动度归一化
        engagement_score = min(
            (analysis.topic.likes + analysis.topic.comments * 2 + analysis.topic.collects * 3) / 1000,
            10.0
        )

        # 需求紧急性
        demand_urgency = max([d.urgency for d in analysis.demands], default=0)

        # 可行性
        feasibility = max([d.feasibility for d in analysis.demands], default=5)

        # 计算总分
        priority = (
            analysis.commercial_value * weights['commercial_value'] +
            engagement_score * weights['engagement'] +
            demand_urgency * weights['demand_urgency'] +
            feasibility * weights['feasibility']
        )

        return round(priority, 2)

    async def _save_analysis(self, analysis: TopicAnalysis):
        """保存分析结果"""
        if not self.config.save_analysis_report:
            return

        self.config.analysis_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")

        # 保存为 JSON
        file_path = self.config.analysis_dir / f"analysis_{date_str}.jsonl"
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(analysis.model_dump_json(ensure_ascii=False) + '\n')

        logger.debug(f"分析结果已保存")

    def get_top_topics(self, analyses: List[TopicAnalysis], top_n: int = 5) -> List[TopicAnalysis]:
        """获取 TOP 热点"""
        # 按优先级排序
        sorted_analyses = sorted(analyses, key=lambda x: x.priority, reverse=True)
        return sorted_analyses[:top_n]
