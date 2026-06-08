"""主窗口 - 电子发票批量打印"""

import os
import logging
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QAction, QMessageBox,
    QStatusBar, QLabel, QPushButton, QFileDialog, QApplication
)

from app.gui.file_list import FileListPanel
from app.gui.preview_panel import PreviewPanel
from app.io.image_handler import ImageHandler
from app.io.pdf_handler import PdfHandler

logger = logging.getLogger(__name__)


def file_to_images(file_path: str) -> list[Image.Image]:
    """将任意支持的文件转换为图片列表"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ImageHandler.SUPPORTED_EXTENSIONS:
        return ImageHandler.to_images(file_path)
    elif ext in PdfHandler.SUPPORTED_EXTENSIONS:
        return PdfHandler.to_images(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


class MainWindow(QMainWindow):
    """发票批量打印主窗口"""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()

    def _setup_ui(self):
        """设置主界面"""
        self.setWindowTitle("发票助手 - 电子发票批量打印")
        self.setMinimumSize(1100, 700)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # ── 工具栏 ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.btn_add = QPushButton("📂 添加文件")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #0078D4; color: white;
                border: none; border-radius: 4px;
                padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background-color: #106EBE; }
        """)

        self.btn_add_folder = QPushButton("📁 添加文件夹")
        self.btn_add_folder.setStyleSheet("""
            QPushButton {
                background-color: #17A2B8; color: white;
                border: none; border-radius: 4px;
                padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background-color: #138496; }
        """)

        self.btn_remove = QPushButton("🗑️ 移除选中")
        self.btn_remove.setStyleSheet("""
            QPushButton {
                background-color: #D9534F; color: white;
                border: none; border-radius: 4px;
                padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background-color: #C9302C; }
        """)

        self.btn_print_all = QPushButton("🖨️ 打印全部")
        self.btn_print_all.setStyleSheet("""
            QPushButton {
                background-color: #FD7E14; color: white;
                border: none; border-radius: 4px;
                padding: 6px 18px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #E06B0A; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.btn_print_all.setEnabled(False)

        self.btn_print_selected = QPushButton("🖨️ 打印选中")
        self.btn_print_selected.setStyleSheet("""
            QPushButton {
                background-color: #6F42C1; color: white;
                border: none; border-radius: 4px;
                padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background-color: #5A32A3; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.btn_print_selected.setEnabled(False)

        self.btn_preview = QPushButton("👁️ 打印预览")
        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #20C997; color: white;
                border: none; border-radius: 4px;
                padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background-color: #17A673; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.btn_preview.setEnabled(False)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_add_folder)
        toolbar.addWidget(self.btn_remove)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_preview)
        toolbar.addWidget(self.btn_print_selected)
        toolbar.addWidget(self.btn_print_all)

        main_layout.addLayout(toolbar)

        # ── 分割面板 ──
        splitter = QSplitter(Qt.Horizontal)

        self.file_list = FileListPanel()
        self.file_list.setMinimumWidth(250)
        self.file_list.setMaximumWidth(400)

        self.preview = PreviewPanel()

        splitter.addWidget(self.file_list)
        splitter.addWidget(self.preview)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter, 1)

        # ── 信号连接 ──
        self.btn_add.clicked.connect(self.file_list.add_files)
        self.btn_add_folder.clicked.connect(self._add_folder)
        self.btn_remove.clicked.connect(self.file_list.remove_selected)
        self.btn_print_all.clicked.connect(self._print_all)
        self.btn_print_selected.clicked.connect(self._print_selected)
        self.btn_preview.clicked.connect(self._print_preview)
        self.file_list.files_changed.connect(self._on_files_changed)
        self.file_list.file_selected.connect(self._show_preview)

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件(&F)")
        act_add = QAction("添加文件...", self)
        act_add.triggered.connect(self.file_list.add_files)
        file_menu.addAction(act_add)
        act_add_folder = QAction("添加文件夹...", self)
        act_add_folder.triggered.connect(self._add_folder)
        file_menu.addAction(act_add_folder)
        act_remove = QAction("移除选中", self)
        act_remove.triggered.connect(self.file_list.remove_selected)
        file_menu.addAction(act_remove)
        act_clear = QAction("清空列表", self)
        act_clear.triggered.connect(self.file_list.clear_all)
        file_menu.addAction(act_clear)
        file_menu.addSeparator()
        act_exit = QAction("退出", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        print_menu = menubar.addMenu("打印(&P)")
        act_preview = QAction("打印预览", self)
        act_preview.triggered.connect(self._print_preview)
        print_menu.addAction(act_preview)
        print_menu.addSeparator()
        act_print_all = QAction("打印全部（2合1）", self)
        act_print_all.triggered.connect(self._print_all)
        print_menu.addAction(act_print_all)
        act_print_sel = QAction("打印选中文件", self)
        act_print_sel.triggered.connect(self._print_selected)
        print_menu.addAction(act_print_sel)

        help_menu = menubar.addMenu("帮助(&H)")
        act_about = QAction("关于发票助手", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _setup_statusbar(self):
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("就绪")
        self.copyright_label = QLabel(
            '制作: Jackwang  <a href="https://wangjinming.com" '
            'style="color:#409EFF; text-decoration:none;">'
            'wangjinming.com</a>  2026-6'
        )
        self.copyright_label.setStyleSheet("color: #999; font-size: 10px;")
        self.copyright_label.setOpenExternalLinks(True)
        self.status_count = QLabel("文件数: 0")
        self.status_count.setMinimumWidth(120)
        self.status_count.setAlignment(Qt.AlignRight)
        status.addWidget(self.status_label, 1)
        status.addPermanentWidget(self.copyright_label)
        status.addPermanentWidget(self.status_count)

    # ── 事件处理 ──

    def _on_files_changed(self, files: list[str]):
        count = len(files)
        self.status_count.setText(f"文件数: {count}")
        self.btn_print_all.setEnabled(count > 0)
        self.btn_print_selected.setEnabled(count > 0)
        self.btn_preview.setEnabled(count > 0)

    def _add_folder(self):
        """选择文件夹并添加其中所有支持的发票文件"""
        folder = QFileDialog.getExistingDirectory(self, "选择发票文件夹")
        if folder:
            files = self.file_list.get_files()
            self.file_list.add_folder(folder)
            new_files = self.file_list.get_files()
            added = len(new_files) - len(files)
            if added > 0:
                self.preview.append_log(f"📁 从文件夹添加了 {added} 个文件")
                self.status_label.setText(f"已添加 {added} 个文件")

    def _show_preview(self, file_path: str):
        """点击文件时显示预览"""
        try:
            images = file_to_images(file_path)
            if images:
                img = images[0].convert("RGB")
                data = img.tobytes("raw", "RGB")
                w, h = img.size
                qimg = QImage(data, w, h, w * 3, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                self.preview.show_preview_image(pixmap)
                self.status_label.setText(f"预览: {os.path.basename(file_path)}")
                self.preview.append_log(f"📄 预览: {os.path.basename(file_path)} ({len(images)} 页)")
        except Exception as e:
            self.status_label.setText(f"无法预览: {os.path.basename(file_path)}")

    # ── 打印预览 ──

    def _print_preview(self):
        """显示打印预览"""
        from PyQt5.QtPrintSupport import QPrintPreviewDialog
        from PyQt5.QtCore import QRectF
        from PyQt5.QtGui import QPainter, QImage

        files = self.file_list.get_files()
        if not files:
            return

        # 提前加载所有图片
        self._pv_images = []
        for f in files:
            try:
                self._pv_images.extend(file_to_images(f))
            except Exception:
                pass
        if not self._pv_images:
            return

        from app.printer.batch_printer import BatchPrinter
        bp = BatchPrinter()

        preview = QPrintPreviewDialog(bp.printer, self)
        preview.setWindowTitle("打印预览")
        preview.resize(900, 700)

        def paint_page(prt):
            """直接使用BatchPrinter的打印逻辑"""
            bp.printer = prt
            bp.print_invoices(self._pv_images)

        preview.paintRequested.connect(paint_page)
        preview.exec_()
        self._pv_images = None

    # ── 批量打印 ──

    def _print_all(self):
        """打印全部文件"""
        files = self.file_list.get_files()
        self._do_print(files)

    def _print_selected(self):
        """打印选中的文件"""
        selected = self.file_list.get_selected_files()
        if not selected:
            QMessageBox.information(self, "提示", "请在文件列表中选中要打印的文件")
            return
        self._do_print(selected)

    def _do_print(self, files: list[str]):
        """执行批量打印"""
        if not files:
            QMessageBox.information(self, "提示", "没有要打印的文件")
            return

        from app.printer.batch_printer import BatchPrinter

        # 将文件转为图片
        self.status_label.setText("正在准备打印文件...")
        QApplication.processEvents()

        all_images = []
        for f in files:
            try:
                images = file_to_images(f)
                all_images.extend(images)
                self.preview.append_log(f"  加载: {os.path.basename(f)} ({len(images)} 页)")
            except Exception as e:
                self.preview.append_log(f"  ⚠️ 加载失败: {os.path.basename(f)} - {e}")

        if not all_images:
            QMessageBox.warning(self, "错误", "没有可打印的图片内容")
            return

        # 计算打印页数
        total_sheets = (len(all_images) + 1) // 2  # 2合1
        total_pages = len(all_images)

        reply = QMessageBox.question(
            self, "打印确认",
            f"文件数: {len(files)}\n"
            f"发票页数: {total_pages} 页\n"
            f"合并打印: {total_sheets} 张纸（每页2张发票）\n\n"
            f"是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            printer = BatchPrinter()
            if printer.show_print_dialog():
                self.status_label.setText("正在打印...")
                QApplication.processEvents()

                success = printer.print_invoices(all_images)
                if success:
                    self.status_label.setText("打印完成")
                    self.preview.append_log(
                        f"🖨️ 打印完成: {total_pages} 页发票 → {total_sheets} 张纸"
                    )
                else:
                    self.status_label.setText("打印失败")
                    QMessageBox.warning(self, "打印失败", "打印过程出现错误，请检查打印机设置")
        except Exception as e:
            QMessageBox.critical(self, "打印错误", str(e))
            logger.exception("打印出错")

    # ── 辅助 ──

    def _show_about(self):
        QMessageBox.about(
            self, "关于发票助手",
            "📄 发票助手 v1.0\n\n"
            "功能：\n"
            "• 加载电子发票文件（图片/PDF）\n"
            "• 文件预览\n"
            "• 两张合并一页批量打印\n\n"
            "适用于增值税电子发票的批量打印。"
        )
