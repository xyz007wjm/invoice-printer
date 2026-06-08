"""预览与日志面板 - 右侧显示区域"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget,
    QLabel, QScrollArea, QTextEdit
)
from PyQt5.QtGui import QPixmap


class PreviewPanel(QWidget):
    """预览与日志面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ccc; border-radius: 4px; }
            QTabBar::tab { padding: 6px 16px; }
        """)

        # 预览标签页
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self.preview_label = QLabel("点击左侧文件预览发票")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 500)
        self.preview_label.setStyleSheet("""
            QLabel {
                color: #aaa; font-size: 16px;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
        """)

        scroll.setWidget(self.preview_label)
        self.tabs.addTab(scroll, "发票预览")

        # 日志标签页
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Menlo', 'Consolas', monospace;
                font-size: 11px;
                border: none;
            }
        """)
        self.tabs.addTab(self.log_text, "运行日志")

        layout.addWidget(self.tabs)

    def show_preview_image(self, pixmap: QPixmap):
        """显示预览图片，自动缩放适配"""
        scaled = pixmap.scaledToWidth(
            max(self.preview_label.width() - 20, 200),
            Qt.SmoothTransformation
        )
        if scaled.height() > self.preview_label.height() - 20:
            scaled = pixmap.scaledToHeight(
                max(self.preview_label.height() - 20, 200),
                Qt.SmoothTransformation
            )
        self.preview_label.setPixmap(scaled)
        self.preview_label.setStyleSheet("border: none;")
        self.tabs.setCurrentIndex(0)

    def append_log(self, message: str):
        """追加日志"""
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
