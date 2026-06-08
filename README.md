# 🖨️ 发票助手 - Invoice Printer

电子发票批量打印工具。支持图片和PDF发票，自动两张合并一页打印（A4），或单张一页（A5）。

## 功能

- 📂 添加文件/文件夹 — 批量导入发票
- 👁️ 预览 — 点击文件即时预览
- 🖨️ 批量打印 — 自动2合1排版（A4每页2张，A5每页1张）
- ⚙️ 中文打印设置 — 纸张、方向、份数

## 快速使用

```bash
# 安装依赖
pip install PyQt5 PyMuPDF Pillow

# 运行
python main.py
```

## 构建可执行文件

### macOS

```bash
chmod +x build_macos.sh && ./build_macos.sh
```
输出: `dist/发票助手.app`

### Windows

```bat
build_windows.bat
```
输出: `dist/发票助手.exe`

## 技术栈

- Python 3.9 + PyQt5
- PyMuPDF (PDF渲染)
- Pillow (图片处理)
- PyInstaller (打包)

## 版权

制作: Jackwang  |  https://wangjinming.com  |  2026-6
