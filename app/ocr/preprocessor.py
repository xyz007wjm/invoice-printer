"""图像预处理 - 为OCR引擎优化图片质量"""

import cv2
import numpy as np
from PIL import Image


class ImagePreprocessor:
    """OCR前的图像增强处理"""

    @staticmethod
    def preprocess(image: Image.Image) -> Image.Image:
        """执行完整的预处理流程

        Args:
            image: 输入PIL图片

        Returns:
            处理后的PIL图片
        """
        img = np.array(image)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # 1. 灰度化
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. 去噪
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # 3. 对比度增强（CLAHE）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # 4. 二值化（自适应阈值）
        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # 转回PIL
        result = Image.fromarray(binary)
        return result

    @staticmethod
    def deskew(image: Image.Image) -> Image.Image:
        """倾斜校正"""
        img = np.array(image)
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img

        # 检测边缘
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is not None:
            angles = []
            for rho, theta in lines[:, 0]:
                angle = np.degrees(theta) - 90
                if abs(angle) < 45:
                    angles.append(angle)
            if angles:
                median_angle = np.median(angles)
                h, w = gray.shape[:2]
                center = (w // 2, h // 2)
                rot_matrix = cv2.getRotationMatrix2D(
                    center, median_angle, 1.0
                )
                rotated = cv2.warpAffine(
                    img, rot_matrix, (w, h),
                    borderMode=cv2.BORDER_REPLICATE
                )
                return Image.fromarray(rotated)

        return image

    @staticmethod
    def enhance_resolution(image: Image.Image, scale: float = 2.0) -> Image.Image:
        """提高分辨率（简单缩放）"""
        w, h = image.size
        return image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
