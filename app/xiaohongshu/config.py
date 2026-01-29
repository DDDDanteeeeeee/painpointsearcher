"""
小红书自动化系统配置管理
"""

from pathlib import Path
from typing import Dict, Any
import toml
import json
from datetime import datetime, time
from pydantic import BaseModel, Field


class XiaohongshuConfig(BaseModel):
    """小红书配置"""

    # 目标设置
    target_daily_replies: int = Field(default=5, description="每天目标回复数")
    max_daily_replies: int = Field(default=10, description="最大回复数")
    working_hours_start: int = Field(default=9, description="工作开始时间")
    working_hours_end: int = Field(default=22, description="工作结束时间")

    # 内容质量
    min_relevance_score: float = Field(default=0.7, description="最小相关性评分")
    min_attractiveness_score: float = Field(default=0.6, description="最小吸引力评分")
    require_human_review: bool = Field(default=True, description="需要人工审核")

    # 安全设置
    enable_safety_limits: bool = Field(default=True, description="启用安全限制")
    random_delay_min: int = Field(default=300, description="最小延迟（秒）")
    random_delay_max: int = Field(default=900, description="最大延迟（秒）")

    # 行为模拟
    simulate_human_typing: bool = Field(default=True, description="模拟打字")
    simulate_reading: bool = Field(default=True, description="模拟阅读")
    random_mouse_movement: bool = Field(default=True, description="随机鼠标移动")
    typing_speed_variance: float = Field(default=0.3, description="打字速度变化幅度")

    # 数据保存
    save_analysis_report: bool = Field(default=True, description="保存分析报告")
    save_generated_content: bool = Field(default=True, description="保存生成内容")
    save_reply_logs: bool = Field(default=True, description="保存回复日志")

    # URL 配置
    xiaohongshu_base_url: str = Field(default="https://www.xiaohongshu.com", description="小红书主页")
    hot_topic_url: str = Field(default="https://www.xiaohongshu.com/explore", description="探索页")

    # 工作空间路径
    workspace_root: Path = Field(default=Path("workspace/xiaohongshu"), description="工作空间根目录")
    hot_topics_dir: Path = Field(default=Path("workspace/xiaohongshu/hot_topics"), description="热点数据目录")
    analysis_dir: Path = Field(default=Path("workspace/xiaohongshu/analysis"), description="分析结果目录")
    content_dir: Path = Field(default=Path("workspace/xiaohongshu/generated_content"), description="生成内容目录")
    logs_dir: Path = Field(default=Path("workspace/xiaohongshu/logs"), description="日志目录")


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config/xiaohongshu.toml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> XiaohongshuConfig:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)
            return XiaohongshuConfig(**config_data.get('xiaohongshu', {}))
        else:
            # 返回默认配置
            return XiaohongshuConfig()

    def save_config(self, config: XiaohongshuConfig):
        """保存配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            toml.dump({'xiaohongshu': config.model_dump()}, f)
        self.config = config

    def get(self) -> XiaohongshuConfig:
        """获取配置"""
        return self.config

    def is_working_hours(self) -> bool:
        """检查是否在工作时间内"""
        now = datetime.now()
        current_hour = now.hour
        return self.config.working_hours_start <= current_hour < self.config.working_hours_end

    def can_reply_today(self, today_count: int) -> bool:
        """检查今天是否还可以回复"""
        return today_count < self.config.max_daily_replies

    def get_random_delay(self) -> int:
        """获取随机延迟时间（秒）"""
        import random
        return random.randint(self.config.random_delay_min, self.config.random_delay_max)


# 全局配置实例
_config_manager = None


def get_config() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
