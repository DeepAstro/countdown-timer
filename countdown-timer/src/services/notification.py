"""
系统通知服务
"""
import sys
from typing import Optional


class NotificationService:
    """系统通知服务"""
    
    def __init__(self, app_name: str = "多倒计时管理器"):
        """初始化通知服务"""
        self.app_name = app_name
        self._enabled = True
    
    @property
    def enabled(self) -> bool:
        """通知是否启用"""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        """设置通知启用状态"""
        self._enabled = value
    
    def show_notification(self, title: str, message: str, 
                          duration: int = 5) -> bool:
        """
        显示系统通知
        
        Args:
            title: 通知标题
            message: 通知内容
            duration: 显示时长（秒）
            
        Returns:
            是否显示成功
        """
        if not self._enabled:
            return False
        
        try:
            # 尝试使用 plyer（跨平台）
            from plyer import notification
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=duration
            )
            return True
        except ImportError:
            pass
        except Exception as e:
            print(f"plyer 通知失败: {e}")
        
        # Windows 备用方案：使用 win10toast
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                title,
                message,
                duration=duration,
                threaded=True
            )
            return True
        except ImportError:
            pass
        except Exception as e:
            print(f"win10toast 通知失败: {e}")
        
        # Windows 原生方案：使用 PowerShell
        if sys.platform == 'win32':
            try:
                import subprocess
                ps_script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
                
                $template = @"
                <toast>
                    <visual>
                        <binding template="ToastText02">
                            <text id="1">{title}</text>
                            <text id="2">{message}</text>
                        </binding>
                    </visual>
                </toast>
"@
                
                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($template)
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{self.app_name}").Show($toast)
                '''
                subprocess.run(
                    ['powershell', '-Command', ps_script],
                    capture_output=True,
                    timeout=10
                )
                return True
            except Exception as e:
                print(f"PowerShell 通知失败: {e}")
        
        return False
    
    def notify_timer_finished(self, timer_name: str) -> bool:
        """
        倒计时结束通知
        
        Args:
            timer_name: 倒计时名称
            
        Returns:
            是否通知成功
        """
        return self.show_notification(
            title="⏰ 倒计时结束",
            message=f"'{timer_name}' 的时间到了！"
        )
