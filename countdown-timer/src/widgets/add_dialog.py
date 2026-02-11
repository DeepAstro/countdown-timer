"""
添加/编辑倒计时对话框
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QSpinBox, QPushButton, QWidget,
    QColorDialog, QTimeEdit, QComboBox, QFormLayout
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from models import Timer, TIMER_COLORS


class ColorButton(QPushButton):
    """颜色选择按钮"""
    
    color_changed = pyqtSignal(str)
    
    def __init__(self, color: str = "#4CAF50", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(40, 40)
        self.clicked.connect(self._choose_color)
        self._update_style()
    
    @property
    def color(self) -> str:
        return self._color
    
    @color.setter
    def color(self, value: str):
        self._color = value
        self._update_style()
        self.color_changed.emit(value)
    
    def _update_style(self):
        """更新按钮样式"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                border: 2px solid #E1E4E8;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                border-color: #4A90D9;
            }}
        """)
    
    def _choose_color(self):
        """打开颜色选择器"""
        color = QColorDialog.getColor(QColor(self._color), self, "选择颜色")
        if color.isValid():
            self.color = color.name()


class PresetColorSelector(QWidget):
    """预设颜色选择器"""
    
    color_selected = pyqtSignal(str)
    
    def __init__(self, current_color: str = "#4CAF50", parent=None):
        super().__init__(parent)
        self._current_color = current_color
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        self._color_buttons = []
        for color in TIMER_COLORS:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid transparent;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    border-color: #2C3E50;
                }}
            """)
            btn.clicked.connect(lambda checked, c=color: self._select_color(c))
            layout.addWidget(btn)
            self._color_buttons.append((btn, color))
        
        layout.addStretch()
        self._highlight_current()
    
    def _select_color(self, color: str):
        """选择颜色"""
        self._current_color = color
        self._highlight_current()
        self.color_selected.emit(color)
    
    def _highlight_current(self):
        """高亮当前选中的颜色"""
        for btn, color in self._color_buttons:
            if color == self._current_color:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        border: 2px solid #2C3E50;
                        border-radius: 6px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        border: 2px solid transparent;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        border-color: #2C3E50;
                    }}
                """)
    
    @property
    def current_color(self) -> str:
        return self._current_color


class AddTimerDialog(QDialog):
    """添加/编辑倒计时对话框"""
    
    def __init__(self, timer: Timer = None, parent=None):
        """
        初始化对话框
        
        Args:
            timer: 要编辑的倒计时，如果为 None 则是添加新模式
            parent: 父窗口
        """
        super().__init__(parent)
        self._timer = timer
        self._is_edit_mode = timer is not None
        
        self._setup_ui()
        self._apply_styles()
        
        if self._timer:
            self._load_timer_data()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("编辑倒计时" if self._is_edit_mode else "添加倒计时")
        self.setFixedSize(400, 320)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题
        title = QLabel("编辑倒计时" if self._is_edit_mode else "添加新倒计时")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # 名称输入
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入倒计时名称")
        self.name_input.setMaxLength(50)
        form_layout.addRow("名称:", self.name_input)
        
        # 时长设置
        duration_widget = QWidget()
        duration_layout = QHBoxLayout(duration_widget)
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(8)
        
        # 小时
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setSuffix(" 小时")
        self.hour_spin.setFixedWidth(100)
        duration_layout.addWidget(self.hour_spin)
        
        # 分钟
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setSuffix(" 分钟")
        self.minute_spin.setFixedWidth(100)
        duration_layout.addWidget(self.minute_spin)
        
        # 秒
        self.second_spin = QSpinBox()
        self.second_spin.setRange(0, 59)
        self.second_spin.setSuffix(" 秒")
        self.second_spin.setFixedWidth(100)
        duration_layout.addWidget(self.second_spin)
        
        duration_layout.addStretch()
        form_layout.addRow("时长:", duration_widget)
        
        # 颜色选择
        self.color_selector = PresetColorSelector()
        form_layout.addRow("颜色:", self.color_selector)
        
        layout.addLayout(form_layout)
        
        # 预设模板
        preset_layout = QHBoxLayout()
        preset_label = QLabel("快速预设:")
        preset_label.setStyleSheet("color: #666;")
        preset_layout.addWidget(preset_label)
        
        presets = [
            ("番茄钟", 25, 0, 0),
            ("短休息", 5, 0, 0),
            ("长休息", 15, 0, 0),
            ("1小时", 0, 60, 0),
        ]
        
        for name, h, m, s in presets:
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, h=h, m=m, s=s: self._set_duration(h, m, s))
            preset_layout.addWidget(btn)
        
        preset_layout.addStretch()
        layout.addLayout(preset_layout)
        
        layout.addStretch()
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 36)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setFixedSize(80, 36)
        save_btn.clicked.connect(self._on_save)
        save_btn.setObjectName("saveBtn")
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            
            QLabel {
                color: #2C3E50;
                font-size: 13px;
            }
            
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #E1E4E8;
                border-radius: 6px;
                background-color: #FAFBFC;
                font-size: 13px;
            }
            
            QLineEdit:focus {
                border-color: #4A90D9;
                background-color: #FFFFFF;
            }
            
            QSpinBox {
                padding: 6px 10px;
                border: 1px solid #E1E4E8;
                border-radius: 6px;
                background-color: #FAFBFC;
                font-size: 13px;
            }
            
            QSpinBox:focus {
                border-color: #4A90D9;
                background-color: #FFFFFF;
            }
            
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #E1E4E8;
                border-radius: 6px;
                background-color: #F1F3F5;
                color: #2C3E50;
                font-size: 12px;
            }
            
            QPushButton:hover {
                background-color: #E8EAED;
                border-color: #D0D7DE;
            }
            
            QPushButton#saveBtn {
                background-color: #4A90D9;
                border-color: #4A90D9;
                color: white;
            }
            
            QPushButton#saveBtn:hover {
                background-color: #3A7BC8;
                border-color: #3A7BC8;
            }
        """)
    
    def _load_timer_data(self):
        """加载倒计时数据到表单"""
        self.name_input.setText(self._timer.name)
        
        # 使用当前剩余时间而不是原始时长
        total_seconds = self._timer.remaining_seconds
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        self.hour_spin.setValue(hours)
        self.minute_spin.setValue(minutes)
        self.second_spin.setValue(seconds)
        
        self.color_selector._select_color(self._timer.color)
    
    def _set_duration(self, hours: int, minutes: int, seconds: int):
        """设置时长"""
        self.hour_spin.setValue(hours)
        self.minute_spin.setValue(minutes)
        self.second_spin.setValue(seconds)
    
    def _on_save(self):
        """保存按钮点击"""
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return
        
        # 验证时长
        total_seconds = self.get_duration_seconds()
        if total_seconds <= 0:
            # 显示错误提示
            return
        
        self.accept()
    
    def get_timer_data(self) -> dict:
        """
        获取表单数据
        
        Returns:
            包含名称、时长和颜色的字典
        """
        return {
            'name': self.name_input.text().strip() or "新倒计时",
            'duration_seconds': self.get_duration_seconds(),
            'color': self.color_selector.current_color
        }
    
    def get_duration_seconds(self) -> int:
        """获取总时长（秒）"""
        hours = self.hour_spin.value()
        minutes = self.minute_spin.value()
        seconds = self.second_spin.value()
        return hours * 3600 + minutes * 60 + seconds
