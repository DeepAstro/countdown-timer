"""
主窗口组件 - 增强版拖拽支持
"""
import sys
from typing import Dict, Optional, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame,
    QSystemTrayIcon, QMenu, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint, QEvent
from PyQt6.QtGui import QFont, QIcon, QAction, QPixmap, QPainter, QColor

from models import Timer
from services import TimerManager, NotificationService, SoundPlayer
from data import DataStore
from .timer_card import TimerCard, PlaceholderCard
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
        
        # 拖拽相关
        self._placeholder: Optional[PlaceholderCard] = None
        self._drag_source_index: Optional[int] = None
        self._drag_source_color: Optional[str] = None
        self._is_dragging = False
        self._animations: List[QPropertyAnimation] = []
        self._current_target_index: Optional[int] = None  # 当前占位符所在的目标索引
        self._placeholder_target_index: Optional[int] = None  # 占位符当前目标索引
        
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
        self.timers_container.setAcceptDrops(True)  # 启用容器的拖放
        self.timers_container.installEventFilter(self)
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
        card.drag_started.connect(self._on_drag_started)
        card.drag_finished.connect(self._on_drag_finished)
        card.drag_over_card.connect(self._on_drag_over_card)
        
        # 启用拖拽进入事件
        card.setAcceptDrops(True)
        
        # 仅在最后一项是stretch/spacer时，插入到其之前
        layout_index = self.timers_layout.count()
        if self.timers_layout.count() > 0:
            last_item = self.timers_layout.itemAt(self.timers_layout.count() - 1)
            if last_item and last_item.spacerItem() is not None:
                layout_index = self.timers_layout.count() - 1
        self.timers_layout.insertWidget(layout_index, card)
        
        self._timer_cards[timer.id] = card
    
    def _on_drag_started(self, timer_id: str):
        """拖拽开始回调"""
        card = self._timer_cards.get(timer_id)
        if not card:
            return
        
        self._is_dragging = True
        self._drag_source_index = card.index
        self._drag_source_color = card.timer.color
        # 每次拖拽开始都清空目标索引，避免沿用悬停残留值
        self._current_target_index = None
        self._placeholder_target_index = self._drag_source_index
        
        # 创建占位符
        if self._placeholder:
            self._placeholder.deleteLater()
        
        self._placeholder = PlaceholderCard(self._drag_source_color)
        self._placeholder.setFixedHeight(90)
        
        # 在原位置插入占位符（被拖拽的卡片已隐藏）
        source_layout_index = self._get_layout_index_for_card_index(self._drag_source_index)
        self.timers_layout.insertWidget(source_layout_index, self._placeholder)
    
    def _on_drag_finished(self, timer_id: str):
        """拖拽结束回调"""
        #print(f"[DEBUG] drag_finished: source={self._drag_source_index}, target={self._current_target_index}")
        
        # 如果有目标索引，执行重新排序
        if self._current_target_index is not None and self._drag_source_index is not None:
            if self._current_target_index != self._drag_source_index:
                #print(f"[DEBUG] Calling reorder_timers({self._drag_source_index}, {self._current_target_index})")
                self._timer_manager.reorder_timers(self._drag_source_index, self._current_target_index)
                self._save_state()
        
        self._is_dragging = False
        
        # 移除占位符
        if self._placeholder:
            self._placeholder.deleteLater()
            self._placeholder = None
        
        self._drag_source_index = None
        self._drag_source_color = None
        self._current_target_index = None  # 重置目标索引
        self._placeholder_target_index = None
    
    def _on_drag_over_card(self, target_index: int):
        """拖拽悬停在卡片上时移动占位符
        
        Args:
            target_index: 目标卡片的原始索引（_index属性）
        """
        if not self._is_dragging or self._drag_source_index is None:
            return
        
        # 不需要移动到自己的位置
        if target_index == self._drag_source_index:
            return

        # 与占位符当前目标一致时，不重复移动，避免布局抖动
        if target_index == self._placeholder_target_index:
            return
        
        # 移动占位符到目标位置
        self._move_placeholder_to_target(target_index)

    def eventFilter(self, watched, event):
        """处理容器空白区域的拖拽（如拖到底部空白区）"""
        if watched is self.timers_container and self._is_dragging:
            event_type = event.type()

            if event_type == QEvent.Type.DragEnter:
                if event.mimeData().hasFormat("application/x-timer-index"):
                    event.acceptProposedAction()
                    return True

            elif event_type == QEvent.Type.DragMove:
                if self._handle_container_drag_move(event):
                    return True

            elif event_type == QEvent.Type.Drop:
                if self._handle_container_drop(event):
                    return True

        return super().eventFilter(watched, event)

    def _get_visible_timer_cards_in_layout_order(self) -> List[TimerCard]:
        """按布局顺序获取可见卡片（排除正在被拖拽隐藏的卡片）"""
        cards: List[TimerCard] = []
        for i in range(self.timers_layout.count()):
            item = self.timers_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), TimerCard):
                card = item.widget()
                if card.isVisible():
                    cards.append(card)
        return cards

    def _get_edge_drop_target_index(self, local_y: int) -> Optional[int]:
        """根据容器内y坐标判断是否命中顶部/底部空白区，并返回目标索引"""
        if self._drag_source_index is None:
            return None

        visible_cards = self._get_visible_timer_cards_in_layout_order()
        if not visible_cards:
            return None

        first_card = visible_cards[0]
        last_card = visible_cards[-1]

        if local_y <= first_card.geometry().center().y():
            return 0
        if local_y >= last_card.geometry().center().y():
            return len(self._timer_cards) - 1

        return None

    def _handle_container_drag_move(self, event) -> bool:
        """容器空白区域拖动：仅处理顶部/底部边缘区域"""
        if not event.mimeData().hasFormat("application/x-timer-index"):
            return False

        local_pos = event.position().toPoint()
        target_index = self._get_edge_drop_target_index(local_pos.y())
        if target_index is None:
            return False

        if self._drag_source_index is not None and target_index != self._drag_source_index:
            self._move_placeholder_to_target(target_index)

        event.acceptProposedAction()
        return True

    def _handle_container_drop(self, event) -> bool:
        """容器区域放下：仅在边缘或占位符上处理，其他交给卡片自身drop"""
        if not event.mimeData().hasFormat("application/x-timer-index"):
            return False

        local_pos = event.position().toPoint()
        target_index = self._get_edge_drop_target_index(local_pos.y())
        if target_index is None:
            hit_widget = self._get_drag_hit_widget(local_pos)
            if isinstance(hit_widget, PlaceholderCard):
                target_index = self._placeholder_target_index
            elif isinstance(hit_widget, TimerCard):
                return False

        # 没有明确目标时，不要吞掉事件，也不要覆盖已有目标索引
        if target_index is None:
            return False

        self._current_target_index = target_index
        event.acceptProposedAction()
        return True

    def _get_drag_hit_widget(self, local_pos: QPoint) -> Optional[QWidget]:
        """根据容器内坐标获取命中的拖拽相关控件（TimerCard/PlaceholderCard）"""
        widget = self.timers_container.childAt(local_pos)
        while widget is not None:
            if isinstance(widget, (TimerCard, PlaceholderCard)):
                return widget
            widget = widget.parentWidget()
        return None

    def _get_card_index_at_local_pos(self, local_pos: QPoint) -> Optional[int]:
        """根据容器内坐标获取对应的卡片索引"""
        widget = self.timers_container.childAt(local_pos)
        while widget is not None:
            if isinstance(widget, TimerCard):
                return widget.index
            if isinstance(widget, PlaceholderCard):
                if self._placeholder_target_index is not None:
                    return self._placeholder_target_index
                return self._drag_source_index
            widget = widget.parentWidget()

        return None
    
    def _get_drop_index_at_pos(self, pos: QPoint) -> int:
        """根据鼠标位置计算放置的索引位置"""
        # 获取容器的全局位置
        container_pos = self.timers_container.mapToGlobal(QPoint(0, 0))
        relative_y = pos.y() - container_pos.y()
        
        # 计算应该插入的位置
        card_height = 90
        spacing = 12
        margin_top = 16
        
        # 计算当前y坐标对应的卡片索引
        y_offset = margin_top
        card_count = 0
        for i in range(self.timers_layout.count()):
            item = self.timers_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), (TimerCard, PlaceholderCard)):
                card_count += 1
        
        # 根据y位置计算索引
        estimated_index = 0
        y_offset = margin_top
        for i in range(self.timers_layout.count()):
            item = self.timers_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), (TimerCard, PlaceholderCard)):
                widget = item.widget()
                widget_height = widget.height() if widget.height() > 0 else card_height
                
                # 检查鼠标是否在这个卡片的中心位置之上
                if relative_y < y_offset + widget_height // 2:
                    break
                estimated_index += 1
                y_offset += widget_height + spacing
        
        return min(estimated_index, card_count - 1)
    
    def _move_placeholder_to_target(self, target_card_index: int):
        """移动占位符到目标卡片的位置
        
        Args:
            target_card_index: 目标卡片的原始索引（_index属性）
        """
        if not self._placeholder:
            return

        # 目标未变化时不重复移位，避免布局抖动
        if target_card_index == self._placeholder_target_index:
            return
        
        # 找到目标卡片在布局中的位置
        target_layout_index = -1
        
        for i in range(self.timers_layout.count()):
            item = self.timers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # 找到目标卡片（必须是可见的）
                if isinstance(widget, TimerCard) and widget.index == target_card_index and widget.isVisible():
                    target_layout_index = i
                    break
        
        # 如果没找到目标卡片
        if target_layout_index == -1:
            # 找到最后一个可见的TimerCard
            for i in range(self.timers_layout.count() - 1, -1, -1):
                item = self.timers_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, TimerCard) and widget.isVisible():
                        target_layout_index = i + 1
                        break
        
        # 确保不超过stretch的位置
        if target_layout_index >= 0:
            # 先从布局中移除占位符
            self.timers_layout.removeWidget(self._placeholder)
            # 重新插入到新位置
            self.timers_layout.insertWidget(target_layout_index, self._placeholder)
            self._placeholder_target_index = target_card_index
    
    def _get_layout_index_for_card_index(self, card_index: int) -> int:
        """根据卡片索引获取布局索引"""
        for i in range(self.timers_layout.count()):
            item = self.timers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, TimerCard) and widget.index == card_index:
                    return i
        return card_index
    
    def _get_card_at_position(self, pos: QPoint) -> Optional[TimerCard]:
        """获取指定位置的卡片"""
        for card in self._timer_cards.values():
            if card.geometry().contains(pos):
                return card
        return None
    
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
        """处理重新排序请求 - 从dropEvent触发"""
        # 注意：实际的重新排序现在在 _on_drag_finished 中处理
        # 这里只记录目标索引
        self._current_target_index = new_index
    
    def _animate_reorder(self, old_index: int, new_index: int):
        """使用动画刷新卡片位置"""
        # 清理旧动画
        for anim in self._animations:
            if anim.state() == QPropertyAnimation.State.Running:
                anim.stop()
        self._animations.clear()
        
        # 获取所有卡片（按当前布局顺序）
        cards = []
        for i in range(self.timers_layout.count()):
            item = self.timers_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), TimerCard):
                cards.append(item.widget())
        
        # 更新卡片索引
        for i, card in enumerate(cards):
            card.index = i
        
        # 简化处理：直接刷新布局
        # 完整的动画实现需要更复杂的坐标计算
        self._refresh_timer_cards()
    
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
