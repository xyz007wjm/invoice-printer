"""OCR引擎封装 - 支持PaddleOCR和Tesseract双引擎"""

from __future__ import annotations

import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)


class OcrResult:
    """OCR识别结果"""
    def __init__(self, text: str, confidence: float, bbox: Optional[tuple] = None):
        self.text = text
        self.confidence = confidence
        self.bbox = bbox  # (x1, y1, x2, y2) 或 None

    def __repr__(self):
        return f"OcrResult(text='{self.text}', conf={self.confidence:.2f})"


class OcrEngine:
    """OCR引擎统一封装，自动选择可用引擎"""

    def __init__(self):
        self._paddle = None
        self._tesseract = None
        self._active_engine = None
        self._initialize()

    def _initialize(self):
        """尝试初始化OCR引擎，优先使用PaddleOCR"""
        # 尝试PaddleOCR
        try:
            from paddleocr import PaddleOCR
            self._paddle = PaddleOCR(lang='ch')
            self._active_engine = 'paddle'
            logger.info("PaddleOCR引擎加载成功")
            return
        except ImportError:
            logger.info("PaddleOCR未安装，尝试Tesseract...")
        except Exception as e:
            logger.warning(f"PaddleOCR加载失败: {e}，尝试Tesseract...")

        # 尝试Tesseract
        try:
            import pytesseract
            # 测试是否可用
            pytesseract.get_tesseract_version()
            self._tesseract = pytesseract
            self._active_engine = 'tesseract'
            logger.info("Tesseract OCR引擎加载成功")
            return
        except ImportError:
            logger.warning("Tesseract未安装")
        except Exception as e:
            logger.warning(f"Tesseract加载失败: {e}")

        if self._active_engine is None:
            logger.error("未找到可用的OCR引擎，请安装PaddleOCR或Tesseract")
            raise RuntimeError(
                "未找到可用的OCR引擎。\n"
                "请安装：pip install paddleocr paddlepaddle\n"
                "或安装Tesseract：https://github.com/tesseract-ocr/tesseract"
            )

    @property
    def is_ready(self) -> bool:
        return self._active_engine is not None

    @property
    def engine_name(self) -> str:
        return self._active_engine or '未知'

    def recognize(self, image: Image.Image) -> list[list[OcrResult]]:
        """对图片进行OCR识别

        Args:
            image: PIL图片

        Returns:
            按行组织的识别结果列表，每行包含多个OcrResult
        """
        if self._active_engine == 'paddle':
            return self._recognize_paddle(image)
        elif self._active_engine == 'tesseract':
            return self._recognize_tesseract(image)
        else:
            raise RuntimeError("OCR引擎不可用")

    def _recognize_paddle(self, image: Image.Image) -> list[list[OcrResult]]:
        """使用PaddleOCR识别（兼容新旧版本API）"""
        import numpy as np
        img_array = np.array(image.convert('RGB'))
        results = self._paddle.ocr(img_array)

        lines = []
        if not results:
            return lines

        # 新版本PaddleOCR (3.x) 返回 list[dict]
        if isinstance(results, list) and len(results) > 0 and isinstance(results[0], dict):
            result = results[0]
            rec_texts = result.get('rec_texts', []) or []
            rec_scores = result.get('rec_scores', []) or []
            rec_polys = result.get('rec_polys', []) or []
            rec_boxes = result.get('rec_boxes', [])

            # 优先使用rec_polys
            for i, text in enumerate(rec_texts):
                if not text or not text.strip():
                    continue
                conf = rec_scores[i] if i < len(rec_scores) else 0.0

                # 从多边形提取bbox
                bbox = None
                if i < len(rec_polys) and len(rec_polys[i]) >= 4:
                    pts = rec_polys[i]
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    bbox = (min(xs), min(ys), max(xs), max(ys))
                elif i < len(rec_boxes):
                    try:
                        box = rec_boxes[i]
                        if len(box) >= 4:
                            bbox = (int(box[0]), int(box[1]),
                                    int(box[2]), int(box[3]))
                    except (IndexError, TypeError):
                        pass

                lines.append([OcrResult(text.strip(), conf, bbox)])

        # 旧版本PaddleOCR (2.x) 返回 list[list[tuple]]
        elif (isinstance(results, list) and len(results) > 0
              and isinstance(results[0], list)):
            for line_group in results:
                if not line_group:
                    continue
                for item in line_group:
                    if isinstance(item, tuple) and len(item) == 2:
                        bbox_points, (text, conf) = item
                        if not text or not text.strip():
                            continue
                        xs = [p[0] for p in bbox_points]
                        ys = [p[1] for p in bbox_points]
                        bbox = (min(xs), min(ys), max(xs), max(ys))
                        lines.append([OcrResult(text.strip(), conf, bbox)])

        return lines

    def _recognize_tesseract(self, image: Image.Image) -> list[list[OcrResult]]:
        """使用Tesseract识别"""
        import pytesseract

        # Tesseract返回带坐标的数据
        data = pytesseract.image_to_data(
            image, lang='chi_sim+eng',
            output_type=pytesseract.Output.DICT
        )

        lines = []
        current_line = []
        prev_line_num = -1

        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if not text:
                continue

            conf = data['conf'][i]
            line_num = data['line_num'][i]

            if line_num != prev_line_num and current_line:
                lines.append(current_line)
                current_line = []

            x, y, w, h = (data['left'][i], data['top'][i],
                          data['width'][i], data['height'][i])
            bbox = (x, y, x + w, y + h)

            current_line.append(OcrResult(
                text=text,
                confidence=conf / 100.0 if conf > 0 else 0.0,
                bbox=bbox
            ))
            prev_line_num = line_num

        if current_line:
            lines.append(current_line)

        return lines
