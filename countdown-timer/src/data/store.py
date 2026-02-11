"""
数据存储层 - 负责状态的持久化
"""
import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models import Timer


class DataStore:
    """数据存储管理类"""
    
    def __init__(self, app_name: str = "CountdownTimer"):
        """初始化数据存储"""
        self.app_name = app_name
        self.data_dir = self._get_data_dir()
        self.data_file = self.data_dir / "state.json"
        self._ensure_data_dir()
    
    def _get_data_dir(self) -> Path:
        """获取应用数据目录"""
        # Windows: C:/Users/<user>/AppData/Local/CountdownTimer
        # 也可以使用当前目录下的 data 文件夹
        if os.name == 'nt':
            base_dir = Path(os.environ.get('LOCALAPPDATA', Path.home()))
        else:
            base_dir = Path.home() / '.local' / 'share'
        
        return base_dir / self.app_name
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def save_state(self, timers: List[Timer], window_geometry: dict = None, 
                   volume: float = 0.7) -> bool:
        """
        保存应用状态
        
        Args:
            timers: 倒计时列表
            window_geometry: 窗口位置和大小
            volume: 音量设置
            
        Returns:
            保存是否成功
        """
        try:
            state = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'timers': [timer.to_dict() for timer in timers],
                'settings': {
                    'volume': volume,
                    'window_geometry': window_geometry or {}
                }
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存状态失败: {e}")
            return False
    
    def load_state(self) -> dict:
        """
        加载应用状态
        
        Returns:
            包含 timers 和 settings 的字典
        """
        default_state = {
            'timers': [],
            'settings': {
                'volume': 0.7,
                'window_geometry': None
            }
        }
        
        if not self.data_file.exists():
            return default_state
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            timers = [Timer.from_dict(t) for t in state.get('timers', [])]
            settings = state.get('settings', default_state['settings'])
            
            return {
                'timers': timers,
                'settings': settings
            }
        except Exception as e:
            print(f"加载状态失败: {e}")
            return default_state
    
    def save_timers(self, timers: List[Timer]) -> bool:
        """仅保存倒计时数据"""
        state = self.load_state()
        return self.save_state(
            timers=timers,
            window_geometry=state['settings'].get('window_geometry'),
            volume=state['settings'].get('volume', 0.7)
        )
    
    def save_settings(self, window_geometry: dict = None, volume: float = None) -> bool:
        """仅保存设置"""
        state = self.load_state()
        settings = state['settings']
        
        if window_geometry is not None:
            settings['window_geometry'] = window_geometry
        if volume is not None:
            settings['volume'] = volume
        
        return self.save_state(
            timers=state['timers'],
            window_geometry=settings.get('window_geometry'),
            volume=settings.get('volume', 0.7)
        )
    
    def clear_all(self) -> bool:
        """清除所有数据"""
        try:
            if self.data_file.exists():
                self.data_file.unlink()
            return True
        except Exception as e:
            print(f"清除数据失败: {e}")
            return False
