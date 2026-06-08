"""图片文件处理器 - 读取常见图片格式"""

import os
from PIL import Image


class ImageHandler:
    """图片文件读取"""

    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}

    @staticmethod
    def to_images(image_path: str) -> list[Image.Image]:
        """读取图片文件为PIL Image列表

        Args:
            image_path: 图片文件路径

        Returns:
            PIL Image对象列表（单张图片返回列表含一个元素）
        """
        img = Image.open(image_path).convert("RGB")
        return [img]

    @staticmethod
    def is_supported(file_path: str) -> bool:
        """检查文件扩展名是否受支持"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ImageHandler.SUPPORTED_EXTENSIONS
