"""PDF文件处理器 - 将PDF页面渲染为图片供OCR处理"""

import fitz  # PyMuPDF
from PIL import Image
import io


class PdfHandler:
    """PDF文件读取与转换"""

    SUPPORTED_EXTENSIONS = {'.pdf'}

    @staticmethod
    def to_images(pdf_path: str, dpi: int = 300) -> list[Image.Image]:
        """将PDF每页渲染为PIL Image列表

        Args:
            pdf_path: PDF文件路径
            dpi: 渲染分辨率，默认300dpi

        Returns:
            PIL Image对象列表
        """
        images = []
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            zoom = dpi / 72  # PDF默认72dpi
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            images.append(img)
        doc.close()
        return images

    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """获取PDF页数"""
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
