"""批量打印模块 - 自动根据纸张尺寸调整排版"""

import logging
from PIL import Image

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QSpinBox, QPushButton, QGroupBox)

logger = logging.getLogger(__name__)


class PrintSetupDialog(QDialog):
    """中文打印设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("打印设置")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 纸张设置
        paper_group = QGroupBox("纸张设置")
        paper_layout = QVBoxLayout(paper_group)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("纸张大小:"))
        self.paper_combo = QComboBox()
        self.paper_combo.addItems(["A4 (210×297mm) — 每页2张发票", "A5 (148×210mm) — 每页1张发票"])
        self.paper_combo.setCurrentIndex(0)
        size_row.addWidget(self.paper_combo)
        paper_layout.addLayout(size_row)

        orient_row = QHBoxLayout()
        orient_row.addWidget(QLabel("方向:"))
        self.orient_combo = QComboBox()
        self.orient_combo.addItems(["纵向", "横向"])
        self.orient_combo.setCurrentIndex(0)
        orient_row.addWidget(self.orient_combo)
        paper_layout.addLayout(orient_row)

        layout.addWidget(paper_group)

        # 份数
        copy_row = QHBoxLayout()
        copy_row.addWidget(QLabel("打印份数:"))
        self.copies_spin = QSpinBox()
        self.copies_spin.setMinimum(1)
        self.copies_spin.setMaximum(99)
        self.copies_spin.setValue(1)
        copy_row.addWidget(self.copies_spin)
        copy_row.addStretch()
        layout.addLayout(copy_row)

        layout.addStretch()

        # 按钮
        btn_row = QHBoxLayout()
        self.btn_ok = QPushButton("确定")
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #0078D4; color: white;
                border: none; border-radius: 4px;
                padding: 8px 24px; font-weight: bold;
            }
        """)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #6C757D; color: white;
                border: none; border-radius: 4px;
                padding: 8px 24px;
            }
        """)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def get_settings(self) -> dict:
        return {
            'paper': 'A4' if self.paper_combo.currentIndex() == 0 else 'A5',
            'landscape': self.orient_combo.currentIndex() == 1,
            'copies': self.copies_spin.value(),
        }


class BatchPrinter:
    """批量打印管理器，自动适配纸张尺寸"""

    def __init__(self):
        self.printer = QPrinter(QPrinter.HighResolution)
        self.printer.setPageSize(QPrinter.A4)
        self.printer.setOrientation(QPrinter.Portrait)
        self._setup_defaults()

    def _setup_defaults(self):
        self.printer.setDuplex(QPrinter.DuplexAuto)
        self.printer.setColorMode(QPrinter.Color)
        self.printer.setResolution(300)

    def show_print_dialog(self) -> bool:
        """显示中文打印设置 → 再弹出系统打印机选择"""
        # 先显示中文设置
        setup = PrintSetupDialog()
        if setup.exec_() != PrintSetupDialog.Accepted:
            return False

        settings = setup.get_settings()

        # 应用设置到打印机
        if settings['paper'] == 'A4':
            self.printer.setPageSize(QPrinter.A4)
        else:
            self.printer.setPageSize(QPrinter.A5)

        if settings['landscape']:
            self.printer.setOrientation(QPrinter.Landscape)
        else:
            self.printer.setOrientation(QPrinter.Portrait)

        self.printer.setCopyCount(settings['copies'])

        # 再弹出系统打印对话框（选打印机）
        dialog = QPrintDialog(self.printer)
        dialog.setWindowTitle("选择打印机")
        return dialog.exec_() == QPrintDialog.Accepted

    def _get_layout_per_page(self) -> int:
        """根据用户选择的纸张尺寸自动判断每页打印几张发票

        Returns:
            2 — A4/Letter等大纸张，每页两张（上下排列）
            1 — A5等小纸张，每页一张（居中）
        """
        # 用 Point 单位（1/72 英寸）获取页面尺寸，不受 DPI 影响
        page = self.printer.pageRect(QPrinter.Point)
        pw = page.width()
        ph = page.height()

        # A4 = 595×842 pt, A5 = 420×595 pt, Letter = 612×792 pt
        # 页面较高（>=600pt）说明是大纸张 → 2张/页
        # 页面较矮（<600pt）说明是小纸张 → 1张/页
        is_large = max(pw, ph) >= 600

        if is_large:
            logger.info(f"纸张尺寸较大 ({pw:.0f}×{ph:.0f} pt)，每页2张")
            return 2
        else:
            logger.info(f"纸张尺寸较小 ({pw:.0f}×{ph:.0f} pt)，每页1张")
            return 1

    def print_invoices(self, images: list[Image.Image]) -> bool:
        """打印发票，自动根据纸张尺寸调整排版

        Args:
            images: 每张图片代表一页发票

        Returns:
            打印是否成功
        """
        if not images:
            logger.warning("没有需要打印的发票")
            return False

        per_page = self._get_layout_per_page()

        painter = QPainter()
        if not painter.begin(self.printer):
            logger.error("无法开始打印任务")
            return False

        try:
            page_rect = self.printer.pageRect(QPrinter.DevicePixel)
            pw = page_rect.width()
            ph = page_rect.height()

            for i in range(0, len(images), per_page):
                if i > 0:
                    self.printer.newPage()

                batch = images[i:i + per_page]

                if len(batch) == 2 and per_page == 2:
                    self._draw_two_up(painter, batch[0], batch[1], pw, ph)
                else:
                    # 只有1张或纸张为小尺寸时，每张发票单独一页居中
                    for img in batch:
                        self._draw_centered(painter, img, pw, ph)

        except Exception as e:
            logger.exception(f"打印出错: {e}")
            return False
        finally:
            painter.end()

        return True

    # ── 绘制方法 ──

    def _draw_two_up(self, painter: QPainter,
                     img1: Image.Image, img2: Image.Image,
                     pw: int, ph: int):
        """A4大纸张：两张上下排列"""
        margin = int(pw * 0.03)
        gap = int(ph * 0.02)

        uw = pw - 2 * margin
        uh = (ph - 2 * margin - gap) // 2

        self._draw_scaled(painter, img1, margin, margin, uw, uh)
        self._draw_scaled(painter, img2, margin, margin + uh + gap, uw, uh)

    def _draw_centered(self, painter: QPainter, img: Image.Image,
                       pw: int, ph: int):
        """A5小纸张：单张居中"""
        margin = int(pw * 0.05)
        uw = pw - 2 * margin
        uh = ph - 2 * margin
        self._draw_scaled(painter, img, margin, margin, uw, uh)

    def _draw_scaled(self, painter: QPainter, img: Image.Image,
                     x: int, y: int, mw: int, mh: int):
        """在指定区域内居中缩放绘制图片"""
        qimg = self._pil_to_qimage(img)
        iw = qimg.width()
        ih = qimg.height()

        scale = min(mw / iw, mh / ih)
        dw = int(iw * scale)
        dh = int(ih * scale)

        ox = x + (mw - dw) // 2
        oy = y + (mh - dh) // 2

        painter.drawImage(QRectF(ox, oy, dw, dh), qimg)

    @staticmethod
    def _pil_to_qimage(img: Image.Image) -> QImage:
        img = img.convert("RGB")
        data = img.tobytes("raw", "RGB")
        return QImage(data, img.width, img.height, img.width * 3,
                      QImage.Format_RGB888)
