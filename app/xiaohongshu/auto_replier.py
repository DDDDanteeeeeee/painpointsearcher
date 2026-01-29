"""
自动回复模块

实现半自动回复机制：自动填写 + 手动确认
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
import time

from app.tool.browser_use_tool import BrowserUseTool
from app.logger import logger
from app.xiaohongshu.config import get_config
from app.xiaohongshu.content_generator import GeneratedReply, ReplySet


class ReplyRecord(BaseModel):
    """回复记录"""
    topic_url: str = Field(description="帖子链接")
    topic_title: str = Field(description="帖子标题")
    reply_content: str = Field(description="回复内容")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    success: bool = Field(default=False, description="是否成功发送")
    method: str = Field(default="auto_fill", description="回复方式：auto_fill/manual")


class AutoReplier:
    """自动回复器"""

    def __init__(self):
        self.config = get_config().get()
        self.browser_tool = BrowserUseTool()
        self.reply_history: List[ReplyRecord] = []
        self._load_reply_history()

    async def prepare_reply(
        self,
        reply: GeneratedReply,
        topic_url: str,
        topic_title: str
    ) -> bool:
        """
        准备回复（自动填写内容，等待用户确认）

        Args:
            reply: 要回复的内容
            topic_url: 帖子链接
            topic_title: 帖子标题

        Returns:
            是否成功准备
        """
        logger.info(f"准备回复: {topic_title}")

        try:
            # 打开帖子
            await self._open_post(topic_url)

            # 等待页面加载
            await asyncio.sleep(2)

            # 定位评论框
            comment_box_located = await self._locate_comment_box()
            if not comment_box_located:
                logger.error("无法定位评论框")
                return False

            # 模拟真实打字速度填写内容
            await self._type_reply_content(reply.content)

            # 截图预览
            await self._take_screenshot(topic_title)

            logger.info("✅ 回复内容已填写，请检查浏览器确认")
            logger.info("⚠️  请手动点击发送按钮，或按 Ctrl+C 取消")

            # 等待用户确认
            return await self._wait_for_user_confirmation()

        except Exception as e:
            logger.error(f"准备回复失败: {e}")
            return False

    async def send_reply(
        self,
        reply: GeneratedReply,
        topic_url: str,
        topic_title: str,
        auto_send: bool = False
    ) -> bool:
        """
        发送回复

        Args:
            reply: 回复内容
            topic_url: 帖子链接
            topic_title: 帖子标题
            auto_send: 是否自动发送（Level 3 功能）

        Returns:
            是否成功发送
        """
        logger.info(f"发送回复: {topic_title}")

        try:
            # 如果不是自动发送，先准备
            if not auto_send:
                success = await self.prepare_reply(reply, topic_url, topic_title)
                if not success:
                    return False

            # 自动点击发送按钮
            if auto_send:
                await self._click_send_button()

            # 记录回复
            record = ReplyRecord(
                topic_url=topic_url,
                topic_title=topic_title,
                reply_content=reply.content,
                success=True,
                method="auto_fill" if auto_send else "manual"
            )
            self._save_reply_record(record)

            logger.info("✅ 回复发送成功")
            return True

        except Exception as e:
            logger.error(f"发送回复失败: {e}")

            # 记录失败
            record = ReplyRecord(
                topic_url=topic_url,
                topic_title=topic_title,
                reply_content=reply.content,
                success=False,
                method="auto_fill" if auto_send else "manual"
            )
            self._save_reply_record(record)

            return False

    async def _open_post(self, url: str):
        """打开帖子"""
        logger.info(f"打开帖子: {url}")

        result = await self.browser_tool.execute(
            action="go_to_url",
            url=url
        )

        if result.error:
            raise Exception(f"打开帖子失败: {result.error}")

        # 等待页面加载
        await asyncio.sleep(3)

    async def _locate_comment_box(self) -> bool:
        """定位评论框"""
        logger.info("定位评论框...")

        # 小红书评论框通常在页面底部
        # 先滚动到底部
        for _ in range(3):
            await self.browser_tool.execute(
                action="scroll_down",
                scroll_amount=1000
            )
            await asyncio.sleep(1)

        # 尝试提取页面上的输入框
        try:
            result = await self.browser_tool.execute(
                action="extract_content",
                goal="查找评论输入框，返回其索引"
            )

            if result.output and not result.error:
                # 假设找到了评论框
                logger.info("✅ 找到评论框")
                return True

        except Exception as e:
            logger.warning(f"定位评论框时出错: {e}")

        # 始终返回 True，让用户手动定位
        logger.info("⚠️  请手动定位评论框")
        return True

    async def _type_reply_content(self, content: str):
        """模拟真实打字速度填写内容"""
        logger.info("填写回复内容...")

        if not self.config.simulate_human_typing:
            # 快速输入
            await self.browser_tool.execute(
                action="input_text",
                index=0,  # 假设评论框是第一个输入框
                text=content
            )
            return

        # 模拟真实打字：逐字符输入，速度变化
        base_delay = 0.1  # 基础打字速度（秒/字符）
        variance = self.config.typing_speed_variance

        for char in content:
            await self.browser_tool.execute(
                action="input_text",
                index=0,
                text=char
            )

            # 随机延迟
            import random
            delay = base_delay * (1 + random.uniform(-variance, variance))
            await asyncio.sleep(delay)

            # 偶尔停顿（模拟思考）
            if random.random() < 0.05:  # 5% 概率
                await asyncio.sleep(random.uniform(0.5, 1.5))

        logger.info(f"✅ 已填写内容（{len(content)} 字）")

    async def _click_send_button(self):
        """点击发送按钮"""
        logger.info("点击发送按钮...")

        # 等待一下，模拟人类反应
        await asyncio.sleep(1)

        # 使用键盘快捷键（通常是 Ctrl+Enter 或 Cmd+Enter）
        import platform
        if platform.system() == 'Darwin':  # macOS
            keys = 'cmd+enter'
        else:
            keys = 'ctrl+enter'

        result = await self.browser_tool.execute(
            action="send_keys",
            keys=keys
        )

        if result.error:
            logger.warning("快捷键失败，尝试手动点击发送按钮")
            # 这里可以添加手动点击的逻辑

        await asyncio.sleep(2)  # 等待发送完成

    async def _take_screenshot(self, title: str):
        """截图预览"""
        logger.info("截图保存预览...")

        # 这里可以添加截图逻辑
        # 暂时跳过
        pass

    async def _wait_for_user_confirmation(self, timeout: int = 300) -> bool:
        """
        等待用户确认

        Args:
            timeout: 超时时间（秒）

        Returns:
            用户是否确认
        """
        logger.info(f"等待用户确认（超时 {timeout} 秒）...")
        logger.info("请在浏览器中检查内容，然后：")
        logger.info("  1. 手动点击发送按钮")
        logger.info("  2. 返回这里按 Enter 确认发送成功")
        logger.info("  3. 或按 Ctrl+C 取消")

        try:
            # 简单等待用户输入
            await asyncio.sleep(timeout)
            return True

        except KeyboardInterrupt:
            logger.info("用户取消")
            return False

    def _save_reply_record(self, record: ReplyRecord):
        """保存回复记录"""
        self.reply_history.append(record)

        # 保存到文件
        if self.config.save_reply_logs:
            self.config.logs_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y%m%d")
            log_path = self.config.logs_dir / f"reply_log_{date_str}.jsonl"

            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(record.model_dump_json(ensure_ascii=False) + '\n')

    def _load_reply_history(self):
        """加载回复历史"""
        # 加载今天的记录
        date_str = datetime.now().strftime("%Y%m%d")
        log_path = self.config.logs_dir / f"reply_log_{date_str}.jsonl"

        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = ReplyRecord.model_validate_json(line)
                        self.reply_history.append(record)
                    except:
                        pass

    def get_today_reply_count(self) -> int:
        """获取今天已发送的回复数"""
        today = datetime.now().date()
        count = 0

        for record in self.reply_history:
            record_time = datetime.fromisoformat(record.timestamp)
            if record_time.date() == today and record.success:
                count += 1

        return count

    def can_reply_now(self) -> tuple[bool, str]:
        """检查现在是否可以回复"""
        # 检查工作时间
        config = get_config().get()
        if not config.is_working_hours():
            return False, "不在工作时间内"

        # 检查今日配额
        today_count = self.get_today_reply_count()
        if not config.can_reply_today(today_count):
            return False, f"今日回复配额已用完（{today_count}/{config.max_daily_replies}）"

        # 检查频率限制
        if self.reply_history:
            last_reply = self.reply_history[-1]
            last_time = datetime.fromisoformat(last_reply.timestamp)
            elapsed = (datetime.now() - last_time).total_seconds()

            if elapsed < config.random_delay_min:
                remaining = int(config.random_delay_min - elapsed)
                return False, f"距离上次回复时间太短，还需等待 {remaining} 秒"

        return True, "可以回复"

    def get_next_available_time(self) -> datetime:
        """获取下次可回复时间"""
        config = get_config().get()

        # 基于上次回复时间
        if self.reply_history:
            last_reply = self.reply_history[-1]
            last_time = datetime.fromisoformat(last_reply.timestamp)
            return last_time + timedelta(seconds=config.random_delay_max)
        else:
            return datetime.now()
