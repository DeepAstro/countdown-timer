"""
声音播放服务
"""
import os
import sys
from pathlib import Path
from typing import Optional


class SoundPlayer:
    """声音播放器"""
    
    def __init__(self):
        """初始化声音播放器"""
        self._volume = 0.7
        self._enabled = True
        self._pygame_initialized = False
        self._sound_cache = {}
    
    @property
    def volume(self) -> float:
        """获取音量 (0.0 - 1.0)"""
        return self._volume
    
    @volume.setter
    def volume(self, value: float):
        """设置音量"""
        self._volume = max(0.0, min(1.0, value))
    
    @property
    def enabled(self) -> bool:
        """声音是否启用"""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        """设置声音启用状态"""
        self._enabled = value
    
    def _init_pygame(self):
        """初始化 pygame mixer"""
        if self._pygame_initialized:
            return True
        
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._pygame_initialized = True
            return True
        except ImportError:
            print("pygame 未安装，声音功能不可用")
            return False
        except Exception as e:
            print(f"pygame 初始化失败: {e}")
            return False
    
    def play_sound(self, sound_path: str = None) -> bool:
        """
        播放声音文件
        
        Args:
            sound_path: 声音文件路径，如果为 None 则使用默认提示音
            
        Returns:
            是否播放成功
        """
        if not self._enabled:
            return False
        
        # 获取默认提示音路径
        if sound_path is None:
            sound_path = self._get_default_sound()
        
        if sound_path is None or not os.path.exists(sound_path):
            # 使用系统蜂鸣声作为后备
            return self._play_beep()
        
        # 尝试使用 pygame 播放
        if self._init_pygame():
            try:
                import pygame
                if sound_path in self._sound_cache:
                    sound = self._sound_cache[sound_path]
                else:
                    sound = pygame.mixer.Sound(sound_path)
                    self._sound_cache[sound_path] = sound
                
                sound.set_volume(self._volume)
                sound.play()
                return True
            except Exception as e:
                print(f"pygame 播放失败: {e}")
        
        # 尝试使用 QSound（如果 PyQt6 可用）
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl
            
            sound_effect = QSoundEffect()
            sound_effect.setSource(QUrl.fromLocalFile(sound_path))
            sound_effect.setVolume(self._volume)
            sound_effect.play()
            return True
        except ImportError:
            pass
        except Exception as e:
            print(f"QSound 播放失败: {e}")
        
        # 使用系统蜂鸣声
        return self._play_beep()
    
    def _get_default_sound(self) -> Optional[str]:
        """获取默认提示音路径"""
        # 查找 assets/sounds 目录下的提示音
        possible_paths = [
            Path(__file__).parent.parent.parent / "assets" / "sounds" / "notification.wav",
            Path(__file__).parent.parent.parent / "assets" / "sounds" / "notification.mp3",
            Path(__file__).parent.parent.parent / "assets" / "sounds" / "alarm.wav",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def _play_beep(self) -> bool:
        """播放系统蜂鸣声"""
        try:
            # Windows
            if sys.platform == 'win32':
                import winsound
                winsound.Beep(1000, 500)  # 1000Hz, 500ms
                return True
        except Exception:
            pass
        
        # 通用方案：打印 BEL 字符
        try:
            print('\a', end='', flush=True)
            return True
        except Exception:
            return False
    
    def play_timer_finished(self) -> bool:
        """播放倒计时结束提示音"""
        return self.play_sound()
    
    def stop_all(self):
        """停止所有声音"""
        if self._pygame_initialized:
            try:
                import pygame
                pygame.mixer.stop()
            except Exception:
                pass
    
    def cleanup(self):
        """清理资源"""
        self._sound_cache.clear()
        if self._pygame_initialized:
            try:
                import pygame
                pygame.mixer.quit()
                self._pygame_initialized = False
            except Exception:
                pass
