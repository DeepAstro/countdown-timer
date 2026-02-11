"""
主窗口组件
"""
import sys
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QScrollArea, QFrame,
    QSystemTrayIcon, QMenu, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon, QAction, QPixmap, QPainter, QColor

from models import Timer
from services import TimerManager, NotificationService, SoundPlayer
from data import DataStore
from .timer_card import TimerCard
from .add_dialog import AddTimerDialog


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化服务
        self._timer_manager = TimerManager()
        self._notification_service = NotificationService()
        self._sound_player = SoundPlayer()
        self._data_store = DataStore()
        
        # 卡片缓存
        self._timer_cards: Dict[str, TimerCard] = {}
        
        # 设置回调
        self._timer_manager.set_callbacks(
            on_timer_update=self._on_timer_update,
            on_timer_finished=self._on_timer_finished,
            on_timers_changed=self._on_timers_changed
        )
        
        # 初始化UI
        self._setup_ui()
        self._setup_tray_icon()
        self._setup_timer()
        self._apply_styles()
        
        # 加载保存的状态
        self._load_state()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("⏱️ 多倒计时管理器")
        self.setMinimumSize(500, 400)
        self.resize(520, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 标题栏
        header = self._create_header()
        main_layout.addWidget(header)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # 倒计时容器
        self.timers_container = QWidget()
        self.timers_layout = QVBoxLayout(self.timers_container)
        self.timers_layout.setContentsMargins(16, 16, 16, 16)
        self.timers_layout.setSpacing(12)
        self.timers_layout.addStretch()
        
        scroll_area.setWidget(self.timers_container)
        main_layout.addWidget(scroll_area)
        
        # 底部添加按钮
        footer = self._create_footer()
        main_layout.addWidget(footer)
    
    def _create_header(self) -> QWidget:
        """创建标题栏"""
        header = QFrame()
        header.setFixedHeight(60)
        header.setObjectName("header")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # 标题
        title = QLabel("⏱️ 多倒计时管理器")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        layout.addStretch()
        
        # 运行计数
        self.running_count_label = QLabel("运行中: 0")
        self.running_count_label.setFont(QFont("Microsoft YaHei", 10))
        layout.addWidget(self.running_count_label)
        
        return header
    
    def _create_footer(self) -> QWidget:
        """创建底部栏"""
        footer = QFrame()
        footer.setFixedHeight(70)
        footer.setObjectName("footer")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 16, 20, 16)
        
        layout.addStretch()
        
        # 添加按钮
        add_btn = QPushButton("+ 添加倒计时")
        add_btn.setFixedSize(140, 40)
        add_btn.setFont(QFont("Microsoft YaHei", 11))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._show_add_dialog)
        add_btn.setObjectName("addBtn")
        layout.addWidget(add_btn)
        
        return footer
    
    def _setup_tray_icon(self):
        """设置系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 创建默认图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#4A90D9"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(8, 8, 48, 48)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "⏱")
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip("多倒计时管理器")
        
        # 托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_and_activate)
        tray_menu.addAction(show_action)
        
        add_action = QAction("添加倒计时", self)
        add_action.triggered.connect(self._show_add_dialog)
        tray_menu.addAction(add_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_app)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
    
    def _setup_timer(self):
        """设置时钟定时器"""
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._on_tick)
        self._clock_timer.start(1000)  # 每秒触发
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8F9FA;
            }
            
            #header {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E1E4E8;
            }
            
            #header QLabel {
                color: #2C3E50;
            }
            
            #footer {
                background-color: #FFFFFF;
                border-top: 1px solid #E1E4E8;
            }
            
            QScrollArea {
                background-color: #F8F9FA;
                border: none;
            }
            
            QPushButton#addBtn {
                background-color: #4A90D9;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            
            QPushButton#addBtn:hover {
                background-color: #3A7BC8;
            }
            
            QPushButton#addBtn:pressed {
                background-color: #2D6CB5;
            }
        """)
    
    def _load_state(self):
        """加载保存的状态"""
        state = self._data_store.load_state()
        
        # 恢复倒计时
        timers = state.get('timers', [])
        self._timer_manager.load_timers(timers)
        
        # 恢复窗口位置
        geometry = state.get('settings', {}).get('window_geometry')
        if geometry:
            self.restoreGeometry(bytes(geometry) if isinstance(geometry, list) else geometry)
        
        # 恢复音量
        volume = state.get('settings', {}).get('volume', 0.7)
        self._sound_player.volume = volume
        
        # 刷新UI
        self._refresh_timer_cards()
    
    def _save_state(self):
        """保存当前状态"""
        # 保存倒计时
        timers = self._timer_manager.timers
        
        # 保存窗口位置
        geometry = list(self.saveGeometry().data())
        
        self._data_store.save_state(
            timers=timers,
            window_geometry=geometry,
            volume=self._sound_player.volume
        )
    
    def _refresh_timer_cards(self):
        """刷新所有倒计时卡片"""
        # 清除现有卡片
        for card in self._timer_cards.values():
            card.deleteLater()
        self._timer_cards.clear()
        
        # 移除stretch
        while self.timers_layout.count() > 0:
            item = self.timers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 添加新卡片
        timers = sorted(self._timer_manager.timers, key=lambda t: t.position)
        
        if not timers:
            # 显示空状态提示
            empty_label = QLabel("还没有倒计时\n点击下方按钮添加")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #9CA3AF; font-size: 14px; padding: 40px;")
            self.timers_layout.addWidget(empty_label)
        else:
            for idx, timer in enumerate(timers):
                self._add_timer_card(timer, index=idx)
        
        self.timers_layout.addStretch()
        self._update_running_count()
    
    def _add_timer_card(self, timer: Timer, index: int = None):
        """添加倒计时卡片"""
        if index is None:
            # 查找timer在排序列表中的位置
            timers = sorted(self._timer_manager.timers, key=lambda t: t.position)
            for i, t in enumerate(timers):
                if t.id == timer.id:
                    index = i
                    break
            if index is None:
                index = 0
        
        card = TimerCard(timer, index=index)
        
        # 连接信号
        card.start_clicked.connect(self._on_start_clicked)
        card.pause_clicked.connect(self._on_pause_clicked)
        card.edit_clicked.connect(self._on_edit_clicked)
        card.delete_clicked.connect(self._on_delete_clicked)
        card.reset_clicked.connect(self._on_reset_clicked)
        card.reorder_requested.connect(self._on_reorder_requested)
        
        # 插入到stretch之前
        layout_index = self.timers_layout.count() - 1 if self.timers_layout.count() > 0 else 0
        self.timers_layout.insertWidget(layout_index, card)
        
        self._timer_cards[timer.id] = card
    
    def _show_add_dialog(self):
        """显示添加对话框"""
        dialog = AddTimerDialog(parent=self)
        
        if dialog.exec():
            data = dialog.get_timer_data()
            self._timer_manager.add_timer(
                name=data['name'],
                duration_seconds=data['duration_seconds'],
                color=data['color']
            )
            self._save_state()
    
    def _on_start_clicked(self, timer_id: str):
        """开始按钮点击"""
        self._timer_manager.start_timer(timer_id)
        self._save_state()
    
    def _on_pause_clicked(self, timer_id: str):
        """暂停按钮点击"""
        self._timer_manager.pause_timer(timer_id)
        self._save_state()
    
    def _on_reset_clicked(self, timer_id: str):
        """重置按钮点击"""
        self._timer_manager.reset_timer(timer_id)
        self._save_state()
    
    def _on_edit_clicked(self, timer_id: str):
        """编辑按钮点击"""
        timer = self._timer_manager.get_timer(timer_id)
        if timer:
            dialog = AddTimerDialog(timer=timer, parent=self)
            if dialog.exec():
                data = dialog.get_timer_data()
                self._timer_manager.update_timer(
                    timer_id=timer_id,
                    name=data['name'],
                    duration_seconds=data['duration_seconds'],
                    color=data['color']
                )
                self._save_state()
    
    def _on_delete_clicked(self, timer_id: str):
        """删除按钮点击"""
        timer = self._timer_manager.get_timer(timer_id)
        if timer:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除 '{timer.name}' 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._timer_manager.remove_timer(timer_id)
                self._save_state()
    
    def _on_tick(self):
        """时钟滴答"""
        self._timer_manager.tick()
    
    def _on_timer_update(self, timer: Timer):
        """倒计时更新回调"""
        if timer.id in self._timer_cards:
            self._timer_cards[timer.id].refresh(timer)
    
    def _on_timer_finished(self, timer: Timer):
        """倒计时结束回调"""
        # 更新卡片显示
        if timer.id in self._timer_cards:
            self._timer_cards[timer.id].refresh(timer)
        
        # 播放提示音
        self._sound_player.play_timer_finished()
        
        # 显示系统通知
        self._notification_service.notify_timer_finished(timer.name)
        
        # 更新运行计数
        self._update_running_count()
        
        # 保存状态
        self._save_state()
    
    def _on_timers_changed(self):
        """倒计时列表变化回调"""
        self._refresh_timer_cards()
        self._update_running_count()
    
    def _update_running_count(self):
        """更新运行计数"""
        count = self._timer_manager.get_running_count()
        self.running_count_label.setText(f"运行中: {count}")
    
    def _on_reorder_requested(self, old_index: int, new_index: int):
        """处理重新排序请求"""
        if self._timer_manager.reorder_timers(old_index, new_index):
            self._save_state()
    
    def _on_tray_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_and_activate()
    
    def show_and_activate(self):
        """显示并激活窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 最小化到托盘而不是关闭
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "多倒计时管理器",
            "程序已最小化到系统托盘，双击图标可恢复窗口",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def _quit_app(self):
        """退出应用"""
        self._save_state()
        self._sound_player.cleanup()
        self.tray_icon.hide()
        QApplication.quit()
