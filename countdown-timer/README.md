# ⏱️ 多倒计时管理器

一个简洁美观的 Windows 桌面多倒计时应用，用于管理一天中不同时间段的工作和休息。

## 功能特性

- ✅ **多倒计时支持** - 同时管理多个独立的倒计时
- ✅ **独立颜色标识** - 每个倒计时可选择不同的颜色
- ✅ **状态记忆** - 关闭后重新打开，恢复之前的所有状态
- ✅ **声音提醒** - 倒计时结束时播放提示音
- ✅ **系统通知** - Windows 原生通知提醒
- ✅ **系统托盘** - 最小化到托盘，后台运行
- ✅ **简洁圆角设计** - 清爽理性的配色方案

## 快速开始

### 环境要求

- Python 3.9+
- Windows 10/11

### 安装依赖

```bash
cd countdown-timer
pip install -r requirements.txt
```

### 运行应用

```bash
cd countdown-timer
python src/main.py
```

### 打包为 EXE

```bash
cd countdown-timer
pyinstaller build.spec
```

打包后的可执行文件位于 `dist/CountdownTimer.exe`

## 使用说明

### 添加倒计时

1. 点击右下角「+ 添加倒计时」按钮
2. 输入名称、设置时长、选择颜色
3. 点击「保存」

### 管理倒计时

- **▶/⏸** - 开始/暂停倒计时
- **↺** - 重置倒计时
- **✏️** - 编辑倒计时设置
- **🗑️** - 删除倒计时

### 预设模板

应用内置了常用的时间模板：
- 番茄钟（25分钟）
- 短休息（5分钟）
- 长休息（15分钟）
- 1小时

## 项目结构

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
│   ├── sounds/              # 提示音文件
│   └── icons/               # 图标文件
├── requirements.txt
├── build.spec
└── README.md
```

## 技术栈

- **GUI框架**: PyQt6
- **数据存储**: JSON
- **打包工具**: PyInstaller
- **通知系统**: plyer
- **音频播放**: pygame

## 配色方案

| 用途 | 颜色 |
|------|------|
| 背景色 | #F8F9FA |
| 卡片背景 | #FFFFFF |
| 主色调 | #4A90D9 |
| 文字色 | #2C3E50 |
| 边框色 | #E1E4E8 |

## 许可证

MIT License
