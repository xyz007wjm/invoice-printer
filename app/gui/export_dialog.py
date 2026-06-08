"""导出对话框 - 选择导出路径和文件名"""

import os
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QDateEdit,
    QFileDialog, QMessageBox, QGroupBox, QCheckBox
)


class ExportDialog(QDialog):
    """导出配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._export_path = ""
        self.setWindowTitle("导出发票数据")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 导出路径选择
        path_group = QGroupBox("导出位置")
        path_layout = QHBoxLayout(path_group)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择保存目录...")
        self.path_edit.setReadOnly(True)

        self.btn_browse = QPushButton("浏览...")
        self.btn_browse.clicked.connect(self._browse_path)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.btn_browse)
        layout.addWidget(path_group)

        # 文件名设置
        name_group = QGroupBox("文件设置")
        name_layout = QFormLayout(name_group)

        # 自动生成文件名（带日期）
        date_layout = QHBoxLayout()
        self.use_date = QCheckBox("使用日期作为文件名")
        self.use_date.setChecked(True)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setEnabled(False)

        self.use_date.toggled.connect(
            lambda checked: self.date_edit.setEnabled(checked)
        )

        date_layout.addWidget(self.use_date)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        name_layout.addRow("文件命名:", date_layout)

        self.custom_name = QLineEdit()
        self.custom_name.setPlaceholderText("自定义文件名（不填则自动生成）")
        self.custom_name.setEnabled(False)
        self.use_date.toggled.connect(
            lambda checked: self.custom_name.setEnabled(not checked)
        )
        name_layout.addRow("自定义名称:", self.custom_name)

        layout.addWidget(name_group)

        # 提示信息
        self.info_label = QLabel("导出为Excel文件 (.xlsx)")
        self.info_label.setStyleSheet("color: #666;")
        layout.addWidget(self.info_label)

        # 按钮
        btn_layout = QHBoxLayout()
        self.btn_export = QPushButton("导出")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #0078D4; color: white;
                border: none; border-radius: 4px;
                padding: 8px 24px; font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #106EBE; }
            QPushButton:disabled { background-color: #ccc; }
        """)
        self.btn_export.setEnabled(False)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #6C757D; color: white;
                border: none; border-radius: 4px;
                padding: 8px 24px;
            }
            QPushButton:hover { background-color: #5A6268; }
        """)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        # 连接信号
        self.btn_export.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _browse_path(self):
        """浏览选择目录"""
        path = QFileDialog.getExistingDirectory(
            self, "选择保存目录", ""
        )
        if path:
            self._export_path = path
            self.path_edit.setText(path)
            self.btn_export.setEnabled(True)

    def get_export_info(self) -> dict:
        """获取导出配置"""
        if self.use_date.isChecked():
            file_name = self.date_edit.date().toString("yyyy-MM-dd")
        else:
            file_name = self.custom_name.text().strip()
            if not file_name:
                file_name = QDate.currentDate().toString("yyyy-MM-dd")

        return {
            'path': self._export_path,
            'file_name': f"发票数据_{file_name}",
        }
