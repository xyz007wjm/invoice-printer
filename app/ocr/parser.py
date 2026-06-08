"""发票字段解析器 - 从OCR结果中提取结构化发票数据"""

from __future__ import annotations

import re
import logging
from typing import Optional, List
from app.ocr.engine import OcrResult

logger = logging.getLogger(__name__)


class InvoiceData:
    """发票结构化数据"""
    def __init__(self):
        self.file_name: str = ""                    # 文件名
        self.buyer_name: str = ""                   # 购方名称
        self.buyer_tax_id: str = ""                 # 购方纳税人识别号
        self.seller_name: str = ""                  # 销方名称
        self.seller_tax_id: str = ""                # 销方纳税人识别号
        self.items: list[str] | None = None         # 开票项目列表
        self.total_amount: str = ""                 # 价税合计（开票总金额）
        self.invoice_date: str = ""                 # 开票日期
        self.invoice_number: str = ""               # 发票号码

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            '文件名': self.file_name,
            '购方名称': self.buyer_name,
            '购方纳税人识别号': self.buyer_tax_id,
            '销方名称': self.seller_name,
            '销方纳税人识别号': self.seller_tax_id,
            '开票项目': '; '.join(self.items) if self.items else '',
            '开票金额': self.total_amount,
            '开票日期': self.invoice_date,
            '发票号码': self.invoice_number,
        }


class InvoiceParser:
    """从OCR识别的文本行中提取发票字段"""

    # 关键字段的标签匹配模式
    PATTERNS = {
        'buyer_name': [
            r'名称\s*[:：]?\s*',
            r'购方名称\s*[:：]?\s*',
            r'购买方名称\s*[:：]?\s*',
        ],
        'buyer_tax_id': [
            r'纳税人识别号\s*[:：]?\s*',
            r'纳税人识别号',
            r'统一社会信用代码\s*[:：]?\s*',
        ],
        'seller_name': [
            r'名称\s*[:：]?\s*',
            r'销方名称\s*[:：]?\s*',
            r'销售方名称\s*[:：]?\s*',
        ],
        'seller_tax_id': [
            r'纳税人识别号\s*[:：]?\s*',
            r'纳税人识别号',
            r'统一社会信用代码\s*[:：]?\s*',
        ],
        'total_amount': [
            r'价税合计\s*[\(（]?大写[\)）]?',
            r'价税合计',
            r'合计',
            r'总金额',
            r'税额',
        ],
        'invoice_date': [
            r'开票日期\s*[:：]?\s*',
            r'发票日期',
            r'日期',
        ],
        'invoice_number': [
            r'发票号码\s*[:：]?\s*',
            r'发票代码',
            r'发票号',
        ],
    }

    # 金额正则（匹配"¥1,234.56"或"1234.56"或"壹仟贰佰叁拾肆圆伍角陆分"等）
    AMOUNT_PATTERN = re.compile(
        r'[¥￥]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
    )
    CN_AMOUNT_PATTERN = re.compile(
        r'[零壹贰叁肆伍陆柒捌玖拾佰仟万亿圆整角分]+'
    )
    TAX_ID_PATTERN = re.compile(
        r'\d{15,20}'  # 统一社会信用代码15-20位数字
    )
    DATE_PATTERN = re.compile(
        r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'
        r'|'
        r'(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})'
    )

    def __init__(self):
        self._buyer_section = True  # 标记当前是在购方区域还是销方区域

    def parse(self, ocr_lines: list[list[OcrResult]], file_name: str = "") -> InvoiceData:
        """解析OCR结果提取发票数据

        Args:
            ocr_lines: OCR引擎返回的按行组织的识别结果
            file_name: 原始文件名

        Returns:
            提取的发票结构化数据
        """
        invoice = InvoiceData()
        invoice.file_name = file_name

        # 将所有文本按行合并
        texts = []
        all_text = ""
        for line in ocr_lines:
            line_text = " ".join(r.text for r in line).strip()
            if line_text:
                texts.append(line_text)
                all_text += line_text + "\n"

        # 识别行间位置关系来判断字段归属
        self._classify_sections(texts)

        # 逐行匹配字段
        for i, line_text in enumerate(texts):
            self._match_buyer_info(line_text, invoice, texts, i)
            self._match_seller_info(line_text, invoice, texts, i)
            self._match_items(line_text, invoice)
            self._match_amount(line_text, invoice)
            self._match_date(line_text, invoice)
            self._match_invoice_number(line_text, invoice)

        # 后处理：如果某些字段未识别到，尝试全文本扫描
        if not invoice.invoice_date:
            self._fallback_scan(all_text, invoice)

        return invoice

    def _classify_sections(self, texts: list[str]):
        """通过文本内容判断购方/销方区域"""
        buyer_found = False
        seller_found = False

        for text in texts:
            if '购' in text or '购买方' in text or '买方' in text:
                buyer_found = True
            if '销' in text or '销售方' in text or '卖方' in text:
                seller_found = True

        self._buyer_section = not seller_found  # 如果没出现"销方"，默认前半部分为购方

    def _match_buyer_info(self, text: str, invoice: InvoiceData,
                          texts: list[str], idx: int):
        """匹配购方信息"""
        # 购方名称
        if not invoice.buyer_name:
            for pattern in self.PATTERNS['buyer_name']:
                if re.search(pattern, text) and '购' in text:
                    value = re.sub(pattern, '', text).strip()
                    if value and len(value) < 100:
                        invoice.buyer_name = value
                        break

        # 购方税号 - 如果购方名称未填但找到了税号，尝试关联
        if not invoice.buyer_tax_id:
            match = self.TAX_ID_PATTERN.search(text)
            if match and ('购' in text or '统一社会信用代码' in text or '纳税人' in text):
                # 判断这段文本是否属于购方区域
                if '销' not in text and '销售方' not in text:
                    invoice.buyer_tax_id = match.group()

    def _match_seller_info(self, text: str, invoice: InvoiceData,
                           texts: list[str], idx: int):
        """匹配销方信息"""
        # 销方名称
        if not invoice.seller_name:
            for pattern in self.PATTERNS['seller_name']:
                if re.search(pattern, text) and ('销' in text or '销售方' in text):
                    value = re.sub(pattern, '', text).strip()
                    if value and len(value) < 100:
                        invoice.seller_name = value
                        break

        # 销方税号
        if not invoice.seller_tax_id:
            match = self.TAX_ID_PATTERN.search(text)
            if match and ('销' in text or '销售方' in text or '卖方' in text):
                invoice.seller_tax_id = match.group()

    def _match_items(self, text: str, invoice: InvoiceData):
        """匹配开票项目（货物或应税劳务、服务名称）"""
        # 在明细表中，项目行通常包含商品名称且不含标签
        ignore_keywords = ['名称', '纳税人识别号', '价税合计', '发票', '合计',
                          '密码区', '备注', '开户行', '账号', '地址', '电话']
        # 单价、数量、金额相关的关键词
        item_indicators = ['*', '税', '服务', '货物', '材料', '设备', '软件',
                          '维修', '咨询', '劳务', '商品', '产品', '工程']

        if any(kw in text for kw in ignore_keywords):
            return

        # 如果文本看起来像发票项目（较短且有项目特征）
        if (any(ind in text for ind in item_indicators)
                and len(text) < 100 and len(text) > 2):
            if invoice.items is None:
                invoice.items = []
            if text not in invoice.items:
                invoice.items.append(text)

    def _match_amount(self, text: str, invoice: InvoiceData):
        """匹配总金额"""
        if invoice.total_amount:
            return

        # 检查是否含有"价税合计"等金额标签
        is_amount_line = any(
            re.search(p, text) for p in self.PATTERNS['total_amount']
        )

        if is_amount_line or self.AMOUNT_PATTERN.search(text):
            # 尝试提取金额
            amount_match = self.AMOUNT_PATTERN.search(text)
            cn_match = self.CN_AMOUNT_PATTERN.search(text) if '价税合计' in text else None

            if is_amount_line:
                if amount_match:
                    invoice.total_amount = amount_match.group(1)
                elif cn_match:
                    invoice.total_amount = cn_match.group()
            elif amount_match and not any(
                re.search(p, text) for p in self.PATTERNS['seller_name'] +
                self.PATTERNS['buyer_name']
            ):
                invoice.total_amount = amount_match.group(1)

    def _match_date(self, text: str, invoice: InvoiceData):
        """匹配开票日期"""
        if invoice.invoice_date:
            return

        # 检查日期标签
        has_date_label = any(
            re.search(p, text) for p in self.PATTERNS['invoice_date']
        )

        date_match = self.DATE_PATTERN.search(text)
        if date_match:
            groups = date_match.groups()
            if groups[0]:  # 中文日期格式：2024年01月01日
                year, month, day = groups[0], groups[1], groups[2]
            else:  # 横线/斜线格式：2024-01-01
                year, month, day = groups[3], groups[4], groups[5]
            invoice.invoice_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    def _match_invoice_number(self, text: str, invoice: InvoiceData):
        """匹配发票号码"""
        if invoice.invoice_number:
            return

        for pattern in self.PATTERNS['invoice_number']:
            match = re.search(pattern, text)
            if match:
                value = re.sub(pattern, '', text).strip()
                if value and len(value) < 50:
                    invoice.invoice_number = value
                    return

    def _fallback_scan(self, all_text: str, invoice: InvoiceData):
        """全文本扫描，补充缺失字段"""
        # 扫描日期
        if not invoice.invoice_date:
            dates = self.DATE_PATTERN.findall(all_text)
            if dates:
                g = dates[0]
                if g[0]:
                    invoice.invoice_date = f"{g[0]}-{g[1].zfill(2)}-{g[2].zfill(2)}"
                else:
                    invoice.invoice_date = f"{g[3]}-{g[4].zfill(2)}-{g[5].zfill(2)}"

        # 扫描税号
        if not invoice.buyer_tax_id:
            tax_ids = self.TAX_ID_PATTERN.findall(all_text)
            if len(tax_ids) >= 1:
                invoice.buyer_tax_id = tax_ids[0]
            if len(tax_ids) >= 2:
                invoice.seller_tax_id = tax_ids[1]

        # 扫描金额
        if not invoice.total_amount:
            amounts = self.AMOUNT_PATTERN.findall(all_text)
            if amounts:
                # 取最后一个金额（通常是合计金额）
                invoice.total_amount = amounts[-1]
