#!/usr/bin/env python3
"""
发票助手 - 电子发票批量打印软件
==================================
功能：
1. 加载电子发票文件（图片/PDF/ODF）
2. 文件预览
3. 两张合并一页批量打印
4. 支持选择打印机、份数、缩放等设置

依赖：
    pip install PyQt5 PyMuPDF Pillow
"""

import sys
import os
import logging


def setup_logging():
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def check_dependencies():
    missing = []
    try:
        import PyQt5
    except ImportError:
        missing.append("PyQt5")
    try:
        import PIL
    except ImportError:
        missing.append("Pillow")

    if missing:
        print("❌ 缺少依赖库，请安装：")
        print(f"   pip install {' '.join(missing)}")
        return False
    return True


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    if not check_dependencies():
        input("按回车退出...")
        sys.exit(1)

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QFont
    from PyQt5.QtCore import QTranslator
    import PyQt5 as _pyqt5

    QApplication.setAttribute(5, True)
    QApplication.setAttribute(6, True)

    app = QApplication(sys.argv)
    app.setApplicationName("发票助手")

    # 设置应用图标
    _icon_path = os.path.join(os.path.dirname(__file__), 'app', 'icon.png')
    if os.path.isfile(_icon_path):
        from PyQt5.QtGui import QIcon, QPixmap
        app.setWindowIcon(QIcon(QPixmap(_icon_path)))

    # 加载Qt自带的中文翻译
    _trans = QTranslator()
    _qt_dir = os.path.join(os.path.dirname(_pyqt5.__file__), 'Qt5', 'translations')
    if not os.path.isdir(_qt_dir):
        _qt_dir = os.path.join(os.path.dirname(_pyqt5.__file__), 'translations')
    for _lang in ['qt_zh_CN', 'qt_zh']:
        if _trans.load(_lang, _qt_dir):
            app.installTranslator(_trans)
            break

    font = QFont()
    if sys.platform == 'darwin':
        font.setPointSize(13)
    else:
        font.setPointSize(10)
    app.setFont(font)

    from app.gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    logger.info("发票助手启动成功")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
