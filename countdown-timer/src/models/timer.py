"""
倒计时数据模型
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Timer:
    """倒计时实体类"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "新倒计时"
    duration_seconds: int = 1500  # 默认25分钟
    remaining_seconds: int = 1500
    color: str = "#4CAF50"
    status: str = "stopped"  # running, paused, stopped
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    position: int = 0
    
    def __post_init__(self):
        """初始化后处理"""
        if self.remaining_seconds == 0:
            self.remaining_seconds = self.duration_seconds
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Timer':
        """从字典创建实例"""
        return cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            name=data.get('name', '新倒计时'),
            duration_seconds=data.get('duration_seconds', 1500),
            remaining_seconds=data.get('remaining_seconds', 1500),
            color=data.get('color', '#4CAF50'),
            status=data.get('status', 'stopped'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            position=data.get('position', 0)
        )
    
    def start(self):
        """开始倒计时"""
        if self.remaining_seconds > 0:
            self.status = "running"
    
    def pause(self):
        """暂停倒计时"""
        if self.status == "running":
            self.status = "paused"
    
    def resume(self):
        """继续倒计时"""
        if self.status == "paused" and self.remaining_seconds > 0:
            self.status = "running"
    
    def stop(self):
        """停止并重置倒计时"""
        self.status = "stopped"
        self.remaining_seconds = self.duration_seconds
    
    def reset(self):
        """重置倒计时"""
        self.remaining_seconds = self.duration_seconds
        self.status = "stopped"
    
    def tick(self) -> bool:
        """
        倒计时减少一秒
        返回: True 表示倒计时结束
        """
        if self.status == "running" and self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if self.remaining_seconds <= 0:
                self.remaining_seconds = 0
                self.status = "stopped"
                return True
        return False
    
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.status == "running"
    
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self.status == "paused"
    
    def is_finished(self) -> bool:
        """是否已完成"""
        return self.remaining_seconds == 0
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """格式化时间为 HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def get_formatted_time(self) -> str:
        """获取格式化的剩余时间"""
        return self.format_time(self.remaining_seconds)
    
    def get_formatted_duration(self) -> str:
        """获取格式化的总时长"""
        return self.format_time(self.duration_seconds)


# 预设颜色
TIMER_COLORS = [
    '#4CAF50',  # 绿色 - 工作
    '#2196F3',  # 蓝色 - 学习
    '#9C27B0',  # 紫色 - 阅读
    '#FF9800',  # 橙色 - 休息
    '#00BCD4',  # 青色 - 运动
    '#E91E63',  # 粉色 - 其他
    '#795548',  # 棕色 - 思考
    '#607D8B',  # 灰蓝 - 会议
]
