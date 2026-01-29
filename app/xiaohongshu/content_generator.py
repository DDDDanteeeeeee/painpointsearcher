"""
内容生成模块

生成小红书回复内容
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
from app.xiaohongshu.demand_analyzer import TopicAnalysis, DemandInsight
from app.xiaohongshu.prompts import get_prompt


class GeneratedReply(BaseModel):
    """生成的回复"""
    version: int = Field(description="版本号")
    angle: str = Field(description="回复角度")
    content: str = Field(description="回复内容")
    relevance_score: float = Field(default=0.0, ge=0, le=10, description="相关性评分")
    attractiveness_score: float = Field(default=0.0, ge=0, le=10, description="吸引力评分")

    # 质量评估
    overall_score: float = Field(default=0.0, ge=0, le=10, description="总体评分")
    recommended: bool = Field(default=False, description="是否推荐使用")
    feedback: str = Field(default="", description="修改建议")

    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ReplySet(BaseModel):
    """回复集合"""
    topic_title: str = Field(description="话题标题")
    topic_url: str = Field(description="话题链接")

    # 策略
    target_angle: str = Field(description="目标角度")
    pain_point: str = Field(description="用户痛点")
    demand: str = Field(description="核心需求")

    # 生成的回复
    replies: List[GeneratedReply] = Field(default_factory=list, description="生成的回复列表")

    # 最佳回复
    best_reply: Optional[GeneratedReply] = Field(default=None, description="最佳回复")

    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ContentGenerator:
    """内容生成器"""

    def __init__(self):
        self.config = get_config().get()
        self.llm = LLM()

    async def generate_replies(
        self,
        analysis: TopicAnalysis,
        angle: Optional[str] = None,
        num_versions: int = 5
    ) -> ReplySet:
        """
        生成回复内容

        Args:
            analysis: 话题分析
            angle: 目标角度（专业/产品/经验/情感）
            num_versions: 生成版本数

        Returns:
            回复集合
        """
        logger.info(f"为话题生成回复: {analysis.topic.title}")

        try:
            # 确定目标角度
            if not angle:
                angle = analysis.suggested_angles[0] if analysis.suggested_angles else "经验"

            # 获取主要需求
            main_demand = ""
            if analysis.demands:
                main_demand = analysis.demands[0].description

            # 构建生成 Prompt
            prompt = get_prompt(
                'content_generation',
                title=analysis.topic.title,
                pain_point=', '.join(analysis.pain_points[:3]),
                demand=main_demand,
                angle=angle
            )

            # 调用 LLM 生成
            response = await self._call_llm_with_retry(prompt)

            # 解析生成的回复
            replies = self._parse_generated_replies(response, angle)

            # 评估质量
            for reply in replies:
                await self._assess_quality(reply, analysis)

            # 选择最佳回复
            best_reply = max(replies, key=lambda r: r.overall_score) if replies else None

            # 创建回复集合
            reply_set = ReplySet(
                topic_title=analysis.topic.title,
                topic_url=analysis.topic.url,
                target_angle=angle,
                pain_point=', '.join(analysis.pain_points[:3]),
                demand=main_demand,
                replies=replies,
                best_reply=best_reply
            )

            # 保存
            await self._save_reply_set(reply_set)

            logger.info(f"生成完成，共 {len(replies)} 个版本，最佳评分: {best_reply.overall_score if best_reply else 0:.2f}")
            return reply_set

        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            return ReplySet(topic_title=analysis.topic.title, topic_url=analysis.topic.url)

    async def optimize_reply(self, reply: GeneratedReply, analysis: TopicAnalysis) -> GeneratedReply:
        """优化回复内容"""
        logger.info("优化回复内容...")

        try:
            prompt = get_prompt(
                'content_optimization',
                original_content=reply.content
            )

            response = await self._call_llm_with_retry(prompt)

            # 创建优化后的回复
            optimized_reply = GeneratedReply(
                version=reply.version + 100,  # 优化版本号
                angle=reply.angle,
                content=response.strip(),
                relevance_score=0,
                attractiveness_score=0
            )

            # 重新评估
            await self._assess_quality(optimized_reply, analysis)

            logger.info(f"优化完成，评分: {reply.overall_score:.2f} → {optimized_reply.overall_score:.2f}")
            return optimized_reply

        except Exception as e:
            logger.error(f"优化失败: {e}")
            return reply

    async def _assess_quality(self, reply: GeneratedReply, analysis: TopicAnalysis):
        """评估回复质量"""
        try:
            prompt = get_prompt(
                'quality_assessment',
                content=reply.content,
                target_post_context=f"""
                标题：{analysis.topic.title}
                内容：{analysis.topic.content[:200]}
                痛点：{', '.join(analysis.pain_points[:3])}
                """
            )

            response = await self._call_llm_with_retry(prompt)

            # 解析评分
            scores = self._parse_quality_assessment(response)

            reply.relevance_score = scores.get('relevance', 7.0)
            reply.attractiveness_score = scores.get('attractiveness', 7.0)
            reply.overall_score = scores.get('overall', 7.0)
            reply.recommended = scores.get('recommended', False)
            reply.feedback = scores.get('feedback', '')

        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
            # 使用默认评分
            reply.relevance_score = 7.0
            reply.attractiveness_score = 7.0
            reply.overall_score = 7.0
            reply.recommended = True

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
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    def _parse_generated_replies(self, response: str, angle: str) -> List[GeneratedReply]:
        """解析生成的回复"""
        replies = []

        try:
            # 尝试提取各个版本
            versions = response.split('## 版本')

            for i, version_text in enumerate(versions[1:], 1):  # 跳过第一个（空）
                try:
                    # 提取角度和内容
                    if '【' in version_text and '】' in version_text:
                        angle_start = version_text.find('【') + 1
                        angle_end = version_text.find('】')
                        current_angle = version_text[angle_start:angle_end]
                    else:
                        current_angle = angle

                    # 提取评分
                    relevance = 8.0
                    attractiveness = 8.0

                    if '相关性' in version_text:
                        try:
                            score_start = version_text.find('相关性') + 4
                            score_end = version_text.find('/', score_start)
                            relevance = float(version_text[score_start:score_end].strip())
                        except:
                            pass

                    if '吸引力' in version_text:
                        try:
                            score_start = version_text.find('吸引力') + 4
                            score_end = version_text.find('/', score_start)
                            attractiveness = float(version_text[score_start:score_end].strip())
                        except:
                            pass

                    # 提取内容（去掉评分部分）
                    content = version_text
                    if '评分：' in content:
                        content = content[:content.find('评分：')]

                    # 去掉标题行
                    if '\n' in content:
                        content = content[content.find('\n')+1:]

                    reply = GeneratedReply(
                        version=i,
                        angle=current_angle,
                        content=content.strip(),
                        relevance_score=relevance,
                        attractiveness_score=attractiveness,
                        overall_score=(relevance + attractiveness) / 2
                    )

                    replies.append(reply)

                except Exception as e:
                    logger.warning(f"解析版本 {i} 失败: {e}")

        except Exception as e:
            logger.warning(f"解析生成回复失败: {e}")

        # 如果解析失败，尝试简单提取
        if not replies:
            reply = GeneratedReply(
                version=1,
                angle=angle,
                content=response.strip(),
                relevance_score=7.0,
                attractiveness_score=7.0,
                overall_score=7.0
            )
            replies.append(reply)

        return replies

    def _parse_quality_assessment(self, response: str) -> Dict[str, Any]:
        """解析质量评估结果"""
        scores = {
            'relevance': 7.0,
            'attractiveness': 7.0,
            'overall': 7.0,
            'recommended': True,
            'feedback': ''
        }

        try:
            # 提取总体评分
            if '总体评分' in response or '总分' in response:
                for line in response.split('\n'):
                    if '总体评分' in line or '总分' in line:
                        try:
                            score_str = line.split(':')[1].strip()
                            scores['overall'] = float(score_str.split('/')[0].strip())
                            break
                        except:
                            pass

            # 判断是否推荐
            if '不推荐' in response or '修改后使用' in response:
                scores['recommended'] = False

            # 提取建议
            if '建议' in response or '修改' in response:
                for line in response.split('\n'):
                    if '建议' in line or '修改' in line:
                        scores['feedback'] += line.strip() + '\n'

        except Exception as e:
            logger.warning(f"解析评估结果失败: {e}")

        return scores

    async def _save_reply_set(self, reply_set: ReplySet):
        """保存回复集合"""
        if not self.config.save_generated_content:
            return

        self.config.content_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        timestamp = datetime.now().strftime("%H%M%S")

        # 保存为 JSON
        file_path = self.config.content_dir / f"replies_{date_str}_{timestamp}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(reply_set.model_dump_json(ensure_ascii=False, indent=2))

        # 保存为 Markdown（更易读）
        md_path = self.config.content_dir / f"replies_{date_str}_{timestamp}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self._format_reply_as_markdown(reply_set))

        logger.debug(f"回复已保存到: {file_path}")

    def _format_reply_as_markdown(self, reply_set: ReplySet) -> str:
        """格式化为 Markdown"""
        md = f"""# 小红书回复内容

## 目标帖子
- **标题**: {reply_set.topic_title}
- **链接**: {reply_set.topic_url}

## 策略
- **角度**: {reply_set.target_angle}
- **用户痛点**: {reply_set.pain_point}
- **核心需求**: {reply_set.demand}

## 生成的回复

"""

        for reply in reply_set.replies:
            md += f"""### 版本 {reply.version}：【{reply.angle}】

**评分**: 相关性 {reply.relevance_score:.1f} | 吸引力 {reply.attractiveness_score:.1f} | 总分 {reply.overall_score:.1f}
**推荐**: {'✅ 是' if reply.recommended else '❌ 否'}

{reply.content}

"""

            if reply.feedback:
                md += f"""**建议**: {reply.feedback}

"""

        if reply_set.best_reply:
            md += f"""
## ⭐ 最佳回复

**版本**: {reply_set.best_reply.version} | **评分**: {reply_set.best_reply.overall_score:.1f}

{reply_set.best_reply.content}

"""

        md += f"""
---
生成时间: {reply_set.created_at}
"""

        return md
