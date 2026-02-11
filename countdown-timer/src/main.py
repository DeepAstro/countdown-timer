"""
多倒计时管理器 - 应用入口
"""
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from widgets import MainWindow


def main():
    """主函数"""
    # 启用高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("多倒计时管理器")
    app.setApplicationVersion("1.0.0")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，托盘运行
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
