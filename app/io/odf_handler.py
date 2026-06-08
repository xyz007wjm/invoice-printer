"""ODF文件处理器 - 将ODF文档页面渲染为图片

ODF（Open Document Format）支持 .odt(文本), .ods(表格), .odp(演示) 等格式。
由于ODF无直接的页面渲染API，策略：
1. 尝试通过odfpy解析文本内容
2. 通过系统命令或LibreOffice转换为PDF
3. 再由PDF处理器渲染为图片
"""

import os
import subprocess
import tempfile
import platform
from typing import Optional
from pathlib import Path
from PIL import Image
from app.io.pdf_handler import PdfHandler


class OdfHandler:
    """ODF文件读取与转换"""

    SUPPORTED_EXTENSIONS = {'.odt', '.ods', '.odp', '.odf'}

    # 缓存LibreOffice路径检测结果
    _libreoffice_path = None

    @classmethod
    def to_images(cls, odf_path: str) -> list[Image.Image]:
        """将ODF文件转换为图片列表

        优先通过LibreOffice转换为PDF再渲染为图片。
        如果LibreOffice不可用，尝试提取纯文本。

        Args:
            odf_path: ODF文件路径

        Returns:
            PIL Image对象列表
        """
        lo_path = cls._find_libreoffice()

        if lo_path:
            return cls._convert_via_libreoffice(odf_path, lo_path)
        else:
            # 降级：返回空白提示图片
            img = Image.new('RGB', (800, 600), (255, 255, 255))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.text((50, 280), f"无法渲染ODF文件：{os.path.basename(odf_path)}\n"
                                 f"请安装LibreOffice以获得完整支持", fill=(0, 0, 0))
            return [img]

    @classmethod
    def _find_libreoffice(cls) -> Optional[str]:
        """查找LibreOffice可执行文件路径"""
        if cls._libreoffice_path is not None:
            return cls._libreoffice_path

        candidates = []
        system = platform.system()

        if system == 'Darwin':  # macOS
            candidates = [
                '/Applications/LibreOffice.app/Contents/MacOS/soffice',
                '/Applications/LibreOffice.app/Contents/MacOS/soffice.bin',
            ]
        elif system == 'Windows':
            candidates = [
                r'C:\Program Files\LibreOffice\program\soffice.exe',
                r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
            ]
        else:  # Linux
            candidates = ['libreoffice', 'soffice']

        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                cls._libreoffice_path = candidate
                return candidate
            elif candidate and not os.path.isabs(candidate):
                # 尝试在PATH中查找
                try:
                    subprocess.run([candidate, '--version'],
                                   capture_output=True, timeout=10)
                    cls._libreoffice_path = candidate
                    return candidate
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue

        cls._libreoffice_path = None
        return None

    @classmethod
    def _convert_via_libreoffice(cls, odf_path: str, lo_path: str) -> list[Image.Image]:
        """通过LibreOffice将ODF转换为PDF，再转为图片"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 转换为PDF
            result = subprocess.run(
                [lo_path, '--headless', '--convert-to', 'pdf',
                 '--outdir', tmpdir, odf_path],
                capture_output=True, timeout=120
            )
            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice转换失败：{result.stderr.decode()}")

            # 找到生成的PDF文件
            pdf_files = list(Path(tmpdir).glob('*.pdf'))
            if not pdf_files:
                raise RuntimeError("LibreOffice未生成PDF文件")
            pdf_path = str(pdf_files[0])

            # 通过PDF处理器渲染为图片
            return PdfHandler.to_images(pdf_path)

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in cls.SUPPORTED_EXTENSIONS
