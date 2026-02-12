"""
倒计时管理器 - 管理所有倒计时的核心逻辑
"""
from typing import List, Callable, Optional
from models import Timer


class TimerManager:
    """倒计时管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self._timers: List[Timer] = []
        self._on_timer_update: Optional[Callable[[Timer], None]] = None
        self._on_timer_finished: Optional[Callable[[Timer], None]] = None
        self._on_timers_changed: Optional[Callable[[], None]] = None
    
    @property
    def timers(self) -> List[Timer]:
        """获取所有倒计时"""
        return self._timers
    
    def set_callbacks(self, on_timer_update: Callable[[Timer], None] = None,
                      on_timer_finished: Callable[[Timer], None] = None,
                      on_timers_changed: Callable[[], None] = None):
        """设置回调函数"""
        self._on_timer_update = on_timer_update
        self._on_timer_finished = on_timer_finished
        self._on_timers_changed = on_timers_changed
    
    def add_timer(self, name: str, duration_seconds: int, color: str) -> Timer:
        """
        添加新的倒计时
        
        Args:
            name: 倒计时名称
            duration_seconds: 时长（秒）
            color: 颜色
            
        Returns:
            新创建的倒计时
        """
        timer = Timer(
            name=name,
            duration_seconds=duration_seconds,
            remaining_seconds=duration_seconds,
            color=color,
            position=len(self._timers)
        )
        self._timers.append(timer)
        self._notify_timers_changed()
        return timer
    
    def remove_timer(self, timer_id: str) -> bool:
        """
        删除倒计时
        
        Args:
            timer_id: 倒计时ID
            
        Returns:
            是否删除成功
        """
        for i, timer in enumerate(self._timers):
            if timer.id == timer_id:
                self._timers.pop(i)
                # 更新位置
                for j, t in enumerate(self._timers):
                    t.position = j
                self._notify_timers_changed()
                return True
        return False
    
    def get_timer(self, timer_id: str) -> Optional[Timer]:
        """根据ID获取倒计时"""
        for timer in self._timers:
            if timer.id == timer_id:
                return timer
        return None
    
    def get_running_timer(self) -> Optional[Timer]:
        """获取当前正在运行的倒计时"""
        for timer in self._timers:
            if timer.is_running():
                return timer
        return None
    
    def start_timer(self, timer_id: str) -> bool:
        """
        开始倒计时
        注意：同一时间只能有一个倒计时运行，会自动暂停其他正在运行的倒计时
        """
        timer = self.get_timer(timer_id)
        if timer:
            # 先暂停其他正在运行的倒计时
            running_timer = self.get_running_timer()
            if running_timer and running_timer.id != timer_id:
                running_timer.pause()
                self._notify_timer_update(running_timer)
            
            timer.start()
            self._notify_timer_update(timer)
            return True
        return False
    
    def pause_timer(self, timer_id: str) -> bool:
        """暂停倒计时"""
        timer = self.get_timer(timer_id)
        if timer:
            timer.pause()
            self._notify_timer_update(timer)
            return True
        return False
    
    def resume_timer(self, timer_id: str) -> bool:
        """继续倒计时"""
        timer = self.get_timer(timer_id)
        if timer:
            timer.resume()
            self._notify_timer_update(timer)
            return True
        return False
    
    def reset_timer(self, timer_id: str) -> bool:
        """重置倒计时"""
        timer = self.get_timer(timer_id)
        if timer:
            timer.reset()
            self._notify_timer_update(timer)
            return True
        return False
    
    def update_timer(self, timer_id: str, name: str = None, 
                     duration_seconds: int = None, color: str = None) -> bool:
        """
        更新倒计时设置
        
        Args:
            timer_id: 倒计时ID
            name: 新名称
            duration_seconds: 新时长
            color: 新颜色
            
        Returns:
            是否更新成功
        """
        timer = self.get_timer(timer_id)
        if timer:
            if name is not None:
                timer.name = name
            if duration_seconds is not None:
                timer.duration_seconds = duration_seconds
                timer.remaining_seconds = duration_seconds
            if color is not None:
                timer.color = color
            self._notify_timer_update(timer)
            self._notify_timers_changed()
            return True
        return False
    
    def tick(self):
        """
        时钟滴答 - 每秒调用一次
        检查所有运行中的倒计时并更新
        """
        for timer in self._timers:
            if timer.is_running():
                finished = timer.tick()
                if finished:
                    self._notify_timer_finished(timer)
                else:
                    self._notify_timer_update(timer)
    
    def load_timers(self, timers: List[Timer]):
        """加载倒计时列表"""
        self._timers = timers
        self._notify_timers_changed()
    
    def get_running_count(self) -> int:
        """获取运行中的倒计时数量"""
        return sum(1 for t in self._timers if t.is_running())
    
    def reorder_timers(self, old_index: int, new_index: int) -> bool:
        """
        重新排序倒计时
        
        Args:
            old_index: 原始位置（基于position排序后的索引）
            new_index: 新位置（基于position排序后的索引）
            
        Returns:
            是否排序成功
        """
        print(f"[DEBUG TimerManager] reorder_timers: old={old_index}, new={new_index}")
        
        if old_index < 0 or new_index < 0:
            return False
        if old_index == new_index:
            return False
        
        # 先按position排序获取排序后的列表
        sorted_timers = sorted(self._timers, key=lambda t: t.position)
        print(f"[DEBUG TimerManager] Before: {[(t.name, t.position) for t in sorted_timers]}")
        
        if old_index >= len(sorted_timers) or new_index >= len(sorted_timers):
            return False
        
        # 直接重新分配所有position值
        # 先移除要移动的元素
        timer_to_move = sorted_timers.pop(old_index)
        print(f"[DEBUG TimerManager] Moving: {timer_to_move.name}")
        # 插入到新位置
        sorted_timers.insert(new_index, timer_to_move)
        
        # 重新分配所有position
        for i, timer in enumerate(sorted_timers):
            timer.position = i
        
        print(f"[DEBUG TimerManager] After: {[(t.name, t.position) for t in sorted_timers]}")
        
        self._notify_timers_changed()
        return True
    
    def _notify_timer_update(self, timer: Timer):
        """通知倒计时更新"""
        if self._on_timer_update:
            self._on_timer_update(timer)
    
    def _notify_timer_finished(self, timer: Timer):
        """通知倒计时结束"""
        if self._on_timer_finished:
            self._on_timer_finished(timer)
    
    def _notify_timers_changed(self):
        """通知倒计时列表变化"""
        if self._on_timers_changed:
            self._on_timers_changed()
