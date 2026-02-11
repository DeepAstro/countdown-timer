# 多倒计时管理器 - 需求与技术总结文档

## 一、项目概述

### 1.1 项目背景
开发一个简洁美观的 Windows 桌面多倒计时应用，用于管理一天中不同时间段的工作和休息，帮助用户更好地进行时间管理。

### 1.2 核心功能
- **多倒计时管理** - 同时管理多个独立的倒计时任务
- **独立颜色标识** - 每个倒计时可选择不同的颜色进行区分
- **状态持久化** - 关闭后重新打开，恢复之前的所有状态
- **声音提醒** - 倒计时结束时播放提示音
- **系统通知** - Windows 原生通知提醒
- **系统托盘** - 最小化到托盘，后台运行
- **拖拽排序** - 支持拖拽卡片调整顺序

## 二、技术架构

### 2.1 技术栈
| 技术 | 用途 |
|------|------|
| Python 3.9+ | 开发语言 |
| PyQt6 | GUI框架 |
| JSON | 数据存储 |
| PyInstaller | 打包工具 |
| plyer | 系统通知 |
| pygame | 音频播放 |

### 2.2 项目结构
```
countdown-timer/
├── src/
│   ├── main.py              # 应用入口
│   ├── models/
│   │   └── timer.py         # 倒计时数据模型
│   ├── widgets/
│   │   ├── main_window.py   # 主窗口
│   │   ├── timer_card.py    # 倒计时卡片组件
│   │   └── add_dialog.py    # 添加/编辑对话框
│   ├── services/
│   │   ├── timer_manager.py # 倒计时管理器
│   │   ├── notification.py  # 通知服务
│   │   └── sound_player.py  # 音频播放
│   └── data/
│       └── store.py         # 数据存储
├── assets/
│   └── sounds/              # 提示音文件
├── requirements.txt
├── build.spec
└── README.md
```

## 三、核心模块设计

### 3.1 数据模型 (Timer)

```python
class Timer:
    - id: str           # 唯一标识
    - name: str         # 倒计时名称
    - duration_seconds: int    # 总时长
    - remaining_seconds: int   # 剩余时间
    - color: str        # 颜色
    - position: int     # 排序位置
    - state: TimerState # 状态 (IDLE/RUNNING/PAUSED/FINISHED)
```

### 3.2 服务层

#### TimerManager (倒计时管理器)
- 管理所有倒计时的生命周期
- 处理开始、暂停、重置操作
- 支持拖拽重新排序
- 提供回调机制通知UI更新

#### NotificationService (通知服务)
- 发送 Windows 原生通知
- 倒计时结束时触发提醒

#### SoundPlayer (音频播放)
- 使用 pygame 播放提示音
- 支持音量控制

### 3.3 UI组件

#### MainWindow (主窗口)
- 管理卡片列表显示
- 处理拖拽排序逻辑
- 系统托盘集成
- 状态持久化

#### TimerCard (倒计时卡片)
- 显示倒计时信息和进度
- 提供操作按钮（开始/暂停/重置/编辑/删除）
- 支持拖拽操作
- 进度条可视化

#### PlaceholderCard (占位符卡片)
- 拖拽时显示半透明占位符
- 指示放置位置

## 四、拖拽排序实现

### 4.1 实现原理
1. **拖拽开始** - 隐藏原始卡片，创建半透明占位符
2. **拖拽移动** - 占位符跟随目标位置移动
3. **拖拽结束** - 更新数据层，刷新UI

### 4.2 关键代码流程

```
用户拖拽卡片
    ↓
TimerCard._start_drag()
    → 隐藏原始卡片
    → 创建拖拽预览图
    → 发送 drag_started 信号
    ↓
MainWindow._on_drag_started()
    → 创建 PlaceholderCard
    → 插入到原位置
    ↓
TimerCard.dragEnterEvent()
    → 发送 drag_over_card 信号
    ↓
MainWindow._on_drag_over_card()
    → 移动占位符到目标位置
    ↓
TimerCard.dropEvent()
    → 发送 reorder_requested 信号
    ↓
MainWindow._on_drag_finished()
    → 调用 TimerManager.reorder_timers()
    → 保存状态
    → 刷新UI
```

### 4.3 注意事项
- 拖拽时源卡片需要隐藏，避免显示两个卡片
- 占位符位置计算需要考虑隐藏的源卡片
- 重新排序后需要更新所有卡片的 position 属性

## 五、数据持久化

### 5.1 存储位置
- Windows: `%APPDATA%/countdown-timer/state.json`

### 5.2 存储内容
```json
{
    "timers": [
        {
            "id": "uuid",
            "name": "倒计时名称",
            "duration_seconds": 1500,
            "remaining_seconds": 1200,
            "color": "#4A90D9",
            "position": 0,
            "state": "paused"
        }
    ],
    "settings": {
        "window_geometry": [...],
        "volume": 0.7
    }
}
```

## 六、构建与部署

### 6.1 开发环境
```bash
cd countdown-timer
pip install -r requirements.txt
python src/main.py
```

### 6.2 打包发布
```bash
cd countdown-timer
pyinstaller build.spec
```

输出: `dist/CountdownTimer.exe`

## 七、已知问题与解决方案

### 7.1 拖拽排序问题
**问题**: 拖拽卡片时出现两个卡片，占位符位置不正确
**解决**: 
- 拖拽开始时隐藏原始卡片
- 使用卡片索引属性而非布局索引定位
- 正确处理最后一个位置的边界情况

### 7.2 状态恢复问题
**问题**: 重启后倒计时状态不正确
**解决**: 保存完整的倒计时状态，包括 remaining_seconds 和 state

## 八、未来扩展

- [ ] 支持自定义提示音
- [ ] 支持倒计时分组
- [ ] 支持云端同步
- [ ] 支持多语言
- [ ] 支持主题切换
