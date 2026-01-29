"""
安全控制模块

频率控制、时间分散、安全机制
"""

import asyncio
import random
from datetime import datetime, time, timedelta
from typing import Optional, List, Callable
from pathlib import Path
import json

from app.logger import logger
from app.xiaohongshu.config import get_config


class SafetyEvent:
    """安全事件"""
    def __init__(self, event_type: str, message: str, severity: str = "info"):
        self.event_type = event_type
        self.message = message
        self.severity = severity  # info, warning, error, critical
        self.timestamp = datetime.now()

    def to_dict(self):
        return {
            "event_type": self.event_type,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat()
        }


class SafetyController:
    """安全控制器"""

    def __init__(self):
        self.config = get_config().get()
        self.events: List[SafetyEvent] = []
        self.paused = False
        self.pause_reason = ""

        # 加载历史事件
        self._load_events()

    async def before_action(self, action_name: str) -> bool:
        """
        行动前检查

        Args:
            action_name: 行动名称

        Returns:
            是否允许执行
        """
        if self.paused:
            logger.warning(f"⚠️  系统已暂停: {self.pause_reason}")
            return False

        # 检查工作时间
        if not self.config.is_working_hours():
            logger.info("不在工作时间内，跳过行动")
            return False

        # 记录事件
        self._log_event("action_check", f"检查行动: {action_name}", "info")

        return True

    async def after_action(self, action_name: str, success: bool, error: Optional[str] = None):
        """行动后处理"""
        if success:
            self._log_event("action_success", f"行动成功: {action_name}", "info")
        else:
            self._log_event("action_failed", f"行动失败: {action_name} - {error}", "error")

    async def apply_random_delay(self, action_name: str = "action"):
        """应用随机延迟"""
        if not self.config.enable_safety_limits:
            return

        delay = self.config.get_random_delay()
        logger.info(f"⏱️  随机延迟 {delay} 秒 ({action_name})")

        await asyncio.sleep(delay)

    async def simulate_human_behavior(self):
        """模拟人类行为"""
        if not self.config.enable_safety_limits:
            return

        # 随机鼠标移动（如果需要）
        if self.config.random_mouse_movement:
            await self._random_mouse_movement()

        # 随机思考停顿
        if self.config.simulate_reading:
            await self._random_thinking_pause()

    async def _random_mouse_movement(self):
        """随机鼠标移动"""
        # 这里可以添加鼠标移动逻辑
        # 暂时跳过
        pass

    async def _random_thinking_pause(self):
        """随机思考停顿"""
        pause_time = random.uniform(1, 3)
        logger.debug(f"思考停顿 {pause_time:.1f} 秒...")
        await asyncio.sleep(pause_time)

    def _log_event(self, event_type: str, message: str, severity: str = "info"):
        """记录事件"""
        event = SafetyEvent(event_type, message, severity)
        self.events.append(event)

        # 根据严重性输出
        if severity == "critical":
            logger.critical(f"🚨 [{event_type}] {message}")
        elif severity == "error":
            logger.error(f"❌ [{event_type}] {message}")
        elif severity == "warning":
            logger.warning(f"⚠️  [{event_type}] {message}")
        else:
            logger.info(f"ℹ️  [{event_type}] {message}")

        # 保存到文件
        self._save_event(event)

    def pause(self, reason: str):
        """暂停系统"""
        self.paused = True
        self.pause_reason = reason
        self._log_event("system_paused", f"系统暂停: {reason}", "warning")

    def resume(self):
        """恢复系统"""
        self.paused = False
        self.pause_reason = ""
        self._log_event("system_resumed", "系统恢复", "info")

    def is_paused(self) -> bool:
        """检查是否暂停"""
        return self.paused

    def get_recent_errors(self, minutes: int = 10) -> List[SafetyEvent]:
        """获取最近的错误"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            e for e in self.events
            if e.severity in ["error", "critical"] and e.timestamp > cutoff_time
        ]

    def check_error_threshold(self, threshold: int = 5) -> bool:
        """检查错误是否超过阈值"""
        recent_errors = self.get_recent_errors()
        if len(recent_errors) >= threshold:
            self.pause(f"最近 {minutes} 分钟内错误过多（{len(recent_errors)}）")
            return True
        return False

    async def execute_with_safety(
        self,
        action: Callable,
        action_name: str,
        *args,
        **kwargs
    ):
        """
        带安全检查执行行动

        Args:
            action: 要执行的函数
            action_name: 行动名称
            *args, **kwargs: 传递给 action 的参数

        Returns:
            action 的返回值，或 None（如果被拒绝）
        """
        # 前置检查
        if not await self.before_action(action_name):
            return None

        # 模拟人类行为
        await self.simulate_human_behavior()

        try:
            # 执行行动
            result = await action(*args, **kwargs)

            # 后置处理
            await self.after_action(action_name, True)

            return result

        except Exception as e:
            # 后置处理（失败）
            await self.after_action(action_name, False, str(e))

            # 检查错误阈值
            self.check_error_threshold()

            raise

    def _save_event(self, event: SafetyEvent):
        """保存事件到文件"""
        if not self.config.save_reply_logs:
            return

        self.config.logs_dir.mkdir(parents=True, exist_ok=True)
        date_str = event.timestamp.strftime("%Y%m%d")
        log_path = self.config.logs_dir / f"safety_events_{date_str}.jsonl"

        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')

    def _load_events(self):
        """加载历史事件"""
        # 加载最近的事件
        date_str = datetime.now().strftime("%Y%m%d")
        log_path = self.config.logs_dir / f"safety_events_{date_str}.jsonl"

        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        event = SafetyEvent(
                            data["event_type"],
                            data["message"],
                            data["severity"]
                        )
                        event.timestamp = datetime.fromisoformat(data["timestamp"])
                        self.events.append(event)
                    except:
                        pass

    def get_daily_summary(self) -> dict:
        """获取今日汇总"""
        today = datetime.now().date()
        today_events = [
            e for e in self.events
            if e.timestamp.date() == today
        ]

        summary = {
            "total_events": len(today_events),
            "by_severity": {},
            "by_type": {}
        }

        for event in today_events:
            # 按严重性统计
            if event.severity not in summary["by_severity"]:
                summary["by_severity"][event.severity] = 0
            summary["by_severity"][event.severity] += 1

            # 按类型统计
            if event.event_type not in summary["by_type"]:
                summary["by_type"][event.event_type] = 0
            summary["by_type"][event.event_type] += 1

        return summary

    def generate_report(self) -> str:
        """生成安全报告"""
        summary = self.get_daily_summary()

        report = f"""# 安全控制日报 - {datetime.now().strftime('%Y-%m-%d')}

## 事件统计
- 总事件数: {summary['total_events']}

## 按严重性分类
"""

        for severity, count in sorted(summary['by_severity'].items()):
            report += f"- {severity}: {count}\n"

        report += "\n## 按类型分类\n"
        for event_type, count in sorted(summary['by_type'].items(), key=lambda x: x[1], reverse=True):
            report += f"- {event_type}: {count}\n"

        if self.paused:
            report += f"\n⚠️  系统状态: 已暂停\n"
            report += f"暂停原因: {self.pause_reason}\n"
        else:
            report += f"\n✅ 系统状态: 正常运行\n"

        return report
