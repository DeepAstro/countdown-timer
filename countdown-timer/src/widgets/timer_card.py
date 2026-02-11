"""
倒计时卡片组件
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QDrag, QPixmap

from models import Timer


class TimerCard(QFrame):
    """倒计时卡片组件"""
    
    # 信号定义
    start_clicked = pyqtSignal(str)      # 开始按钮点击
    pause_clicked = pyqtSignal(str)      # 暂停按钮点击
    edit_clicked = pyqtSignal(str)       # 编辑按钮点击
    delete_clicked = pyqtSignal(str)     # 删除按钮点击
    reset_clicked = pyqtSignal(str)      # 重置按钮点击
    drag_started = pyqtSignal(str)       # 拖拽开始
    reorder_requested = pyqtSignal(int, int)  # 重新排序请求 (old_index, new_index)
    
    def __init__(self, timer: Timer, index: int = 0, parent=None):
        """初始化卡片"""
        super().__init__(parent)
        self._timer = timer
        self._index = index
        
        # 拖拽相关
        self._drag_start_pos = None
        self._is_dragging = False
        
        self.setAcceptDrops(True)
        self._setup_ui()
        self._update_display()
    
    @property
    def timer(self) -> Timer:
        """获取关联的倒计时"""
        return self._timer
    
    @property
    def index(self) -> int:
        """获取卡片索引"""
        return self._index
    
    @index.setter
    def index(self, value: int):
        """设置卡片索引"""
        self._index = value
    
    def _setup_ui(self):
        """设置UI布局"""
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # 名称和时间区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # 名称
        self.name_label = QLabel(self._timer.name)
        self.name_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        info_layout.addWidget(self.name_label)
        
        # 时间显示
        self.time_label = QLabel(self._timer.get_formatted_time())
        self.time_label.setFont(QFont("Consolas", 24, QFont.Weight.Bold))
        info_layout.addWidget(self.time_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # 开始/暂停按钮
        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setFixedSize(36, 36)
        self.play_pause_btn.clicked.connect(self._on_play_pause_clicked)
        self.play_pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.play_pause_btn)
        
        # 重置按钮
        self.reset_btn = QPushButton("↺")
        self.reset_btn.setFixedSize(36, 36)
        self.reset_btn.clicked.connect(lambda: self.reset_clicked.emit(self._timer.id))
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.reset_btn)
        
        # 编辑按钮
        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setFixedSize(36, 36)
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self._timer.id))
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.edit_btn)
        
        # 删除按钮
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setFixedSize(36, 36)
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._timer.id))
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        # 设置固定高度
        self.setFixedHeight(90)
    
    def _get_colors(self) -> tuple:
        """
        获取背景颜色（正常饱和度和低饱和度）
        返回: (normal_color, desaturated_color)
        """
        base_color = QColor(self._timer.color)
        
        # 转换为HSV
        h = base_color.hue()
        s = base_color.saturation()
        v = base_color.value()
        
        # 正常颜色
        normal_color = QColor.fromHsv(h, s, v)
        
        # 低饱和度颜色（用于未过去的时间）
        desaturated_color = QColor.fromHsv(h, max(s // 4, 20), min(v + 40, 255))
        
        return normal_color, desaturated_color
    
    def _get_text_color(self, bg_color: QColor) -> QColor:
        """
        根据背景颜色计算合适的文字颜色
        """
        # 计算亮度
        luminance = (0.299 * bg_color.red() + 
                    0.587 * bg_color.green() + 
                    0.114 * bg_color.blue()) / 255
        
        if luminance > 0.5:
            return QColor("#2C3E50")  # 深色文字
        else:
            return QColor("#FFFFFF")  # 白色文字
    
    def paintEvent(self, event):
        """绘制事件 - 绘制进度条背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取颜色
        normal_color, desaturated_color = self._get_colors()
        
        # 计算进度
        if self._timer.duration_seconds > 0:
            elapsed = self._timer.duration_seconds - self._timer.remaining_seconds
            progress = elapsed / self._timer.duration_seconds
        else:
            progress = 0
        
        # 绘制圆角矩形背景
        rect = self.rect()
        radius = 12
        
        # 创建圆角路径
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
        painter.setClipPath(path)
        
        # 绘制低饱和度背景（未过去的时间）
        painter.fillRect(rect, QBrush(desaturated_color))
        
        # 绘制正常饱和度部分（已过去的时间）- 从左边开始
        if progress > 0:
            elapsed_width = int(rect.width() * progress)
            elapsed_rect = rect.adjusted(0, 0, -(rect.width() - elapsed_width), 0)
            painter.fillRect(elapsed_rect, QBrush(normal_color))
        
        # 绘制边框
        painter.setClipping(False)
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.drawRoundedRect(rect.x(), rect.y(), rect.width() - 1, rect.height() - 1, radius, radius)
        
        # 如果正在拖拽，添加半透明效果
        if self._is_dragging:
            painter.fillRect(rect, QColor(255, 255, 255, 100))
    
    def _update_display(self):
        """更新显示"""
        self.name_label.setText(self._timer.name)
        self.time_label.setText(self._timer.get_formatted_time())
        
        # 获取文字颜色
        normal_color, _ = self._get_colors()
        text_color = self._get_text_color(normal_color)
        text_style = f"color: {text_color.name()}; background: transparent;"
        
        self.name_label.setStyleSheet(text_style)
        
        # 根据状态设置时间颜色
        if self._timer.is_finished():
            time_color = "#E74C3C"  # 红色 - 已结束
            self.time_label.setStyleSheet(f"color: {time_color}; background: transparent;")
        elif self._timer.is_running():
            self.time_label.setStyleSheet(text_style)
        elif self._timer.is_paused():
            time_color = "#F39C12"  # 橙色 - 已暂停
            self.time_label.setStyleSheet(f"color: {time_color}; background: transparent;")
        else:
            self.time_label.setStyleSheet(text_style)
        
        # 更新按钮状态
        if self._timer.is_running():
            self.play_pause_btn.setText("⏸")
        else:
            self.play_pause_btn.setText("▶")
        
        # 更新按钮样式
        self._update_button_styles()
        
        # 触发重绘
        self.update()
    
    def _update_button_styles(self):
        """更新按钮样式"""
        # 获取文字颜色来决定按钮颜色
        normal_color, _ = self._get_colors()
        text_color = self._get_text_color(normal_color)
        
        # 根据背景亮度选择按钮样式
        luminance = (0.299 * normal_color.red() + 
                    0.587 * normal_color.green() + 
                    0.114 * normal_color.blue()) / 255
        
        if luminance > 0.5:
            btn_bg = "rgba(0, 0, 0, 0.1)"
            btn_hover = "rgba(0, 0, 0, 0.15)"
            btn_pressed = "rgba(0, 0, 0, 0.2)"
            btn_color = "#2C3E50"
        else:
            btn_bg = "rgba(255, 255, 255, 0.2)"
            btn_hover = "rgba(255, 255, 255, 0.3)"
            btn_pressed = "rgba(255, 255, 255, 0.4)"
            btn_color = "#FFFFFF"
        
        btn_style = f"""
            QPushButton {{
                background-color: {btn_bg};
                border: none;
                border-radius: 8px;
                font-size: 14px;
                color: {btn_color};
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:pressed {{
                background-color: {btn_pressed};
            }}
        """
        
        for btn in [self.play_pause_btn, self.reset_btn, self.edit_btn, self.delete_btn]:
            btn.setStyleSheet(btn_style)
    
    def _on_play_pause_clicked(self):
        """播放/暂停按钮点击"""
        if self._timer.is_running():
            self.pause_clicked.emit(self._timer.id)
        else:
            self.start_clicked.emit(self._timer.id)
    
    def refresh(self, timer: Timer = None):
        """
        刷新显示
        
        Args:
            timer: 新的倒计时数据，如果为 None 则使用当前数据
        """
        if timer:
            self._timer = timer
        self._update_display()
        self.update()
    
    # ========== 拖拽功能 ==========
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 处理拖拽"""
        if not self._drag_start_pos:
            super().mouseMoveEvent(event)
            return
        
        if event.buttons() & Qt.MouseButton.LeftButton:
            distance = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
            
            if distance >= 10:  # 开始拖拽的最小距离
                self._start_drag()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self._drag_start_pos = None
        self._is_dragging = False
        self.update()
        super().mouseReleaseEvent(event)
    
    def _start_drag(self):
        """开始拖拽"""
        self._is_dragging = True
        self.update()
        
        # 创建拖拽对象
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self._timer.id)
        mime_data.setData("application/x-timer-index", str(self._index).encode())
        drag.setMimeData(mime_data)
        
        # 创建拖拽预览图
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self._drag_start_pos)
        
        # 发送拖拽开始信号
        self.drag_started.emit(self._timer.id)
        
        # 执行拖拽
        drag.exec(Qt.DropAction.MoveAction)
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasFormat("application/x-timer-index"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasFormat("application/x-timer-index"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """放置事件"""
        if event.mimeData().hasFormat("application/x-timer-index"):
            data = event.mimeData().data("application/x-timer-index")
            source_index = int(bytes(data).decode())
            
            if source_index != self._index:
                self.reorder_requested.emit(source_index, self._index)
            
            event.acceptProposedAction()
        else:
            event.ignore()
