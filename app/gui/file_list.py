"""文件列表面板 - 左侧文件列表管理"""

import os
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QAbstractItemView, QLabel
)
from PyQt5.QtGui import QIcon, QDragEnterEvent, QDropEvent


class FileListPanel(QWidget):
    """文件列表面板"""

    # 信号：文件列表发生变化
    files_changed = pyqtSignal(list)
    # 信号：选中了某个文件（双击或单击选中）
    file_selected = pyqtSignal(str)

    # 支持的扩展名
    SUPPORTED_EXTS = {
        '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp',
        '.pdf',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_paths: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题行（含清空按钮）
        title_row = QHBoxLayout()
        title = QLabel("📄 发票文件列表")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")

        self.btn_clear = QPushButton("清空列表")
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #6C757D; color: white;
                border: none; border-radius: 4px;
                padding: 4px 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: #5A6268; }
        """)

        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.btn_clear)
        layout.addLayout(title_row)

        # 文件列表
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setDragDropMode(QListWidget.NoDragDrop)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
                color: white;
            }
        """)
        layout.addWidget(self.list_widget)

        # 连接信号
        self.btn_clear.clicked.connect(self.clear_all)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.setAcceptDrops(True)

    def add_files(self):
        """打开文件选择对话框添加文件"""
        dialog = QFileDialog(self, "选择发票文件", "")
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter(
            "支持的文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.pdf);;"
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp);;"
            "PDF文件 (*.pdf);;"
            "所有文件 (*)"
        )
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        files = []
        if dialog.exec_() == QFileDialog.Accepted:
            files = dialog.selectedFiles()
        if files:
            self._add_file_paths(files)

    def remove_selected(self):
        """移除选中的文件"""
        selected = self.list_widget.selectedItems()
        if not selected:
            QMessageBox.information(self, "提示", "请先选择要移除的文件")
            return

        for item in selected:
            path = item.data(Qt.UserRole)
            if path in self.file_paths:
                self.file_paths.remove(path)
            self.list_widget.takeItem(self.list_widget.row(item))

        self.files_changed.emit(self.file_paths.copy())

    def clear_all(self):
        """清空文件列表"""
        if not self.file_paths:
            return
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有文件吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.file_paths.clear()
            self.list_widget.clear()
            self.files_changed.emit(self.file_paths.copy())

    def get_files(self) -> list[str]:
        """获取当前文件列表"""
        return self.file_paths.copy()

    def get_selected_files(self) -> list[str]:
        """获取选中的文件路径列表"""
        selected = self.list_widget.selectedItems()
        return [item.data(Qt.UserRole) for item in selected if item.data(Qt.UserRole)]

    def _add_file_paths(self, paths: list[str]):
        """添加文件路径到列表"""
        added = 0
        for path in paths:
            ext = os.path.splitext(path)[1].lower()
            if ext not in self.SUPPORTED_EXTS:
                continue
            if path not in self.file_paths:
                self.file_paths.append(path)
                item = QListWidgetItem(os.path.basename(path))
                item.setData(Qt.UserRole, path)
                item.setToolTip(path)
                self.list_widget.addItem(item)
                added += 1

        if added > 0:
            self.files_changed.emit(self.file_paths.copy())

    def add_folder(self, folder_path: str):
        """添加文件夹内所有支持的发票文件（不递归子目录）"""
        paths = []
        for fname in os.listdir(folder_path):
            ext = os.path.splitext(fname)[1].lower()
            if ext in self.SUPPORTED_EXTS:
                full = os.path.join(folder_path, fname)
                if os.path.isfile(full):
                    paths.append(full)
        paths.sort()
        self._add_file_paths(paths)

    def _on_item_clicked(self, item):
        """点击文件列表中的项时触发预览"""
        path = item.data(Qt.UserRole)
        if path:
            self.file_selected.emit(path)

    # --- 拖拽支持 ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
        self._add_file_paths(paths)
        event.acceptProposedAction()
