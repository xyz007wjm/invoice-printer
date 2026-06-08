@echo off
REM Windows 构建脚本
REM 使用方法: 双击运行, 或在命令行执行 build_windows.bat

cd /d "%~dp0"

REM 安装依赖
pip install -i https://mirrors.aliyun.com/pypi/simple/ PyQt5 PyMuPDF Pillow pyinstaller

REM 构建
pyinstaller --clean --noconfirm ^
    --name "发票助手" ^
    --icon "app\icon.png" ^
    --windowed ^
    --add-data "app;app" ^
    --hidden-import PyQt5.QtPrintSupport ^
    --hidden-import PyQt5.QtSvg ^
    --hidden-import PIL ^
    main.py

echo ✅ Windows 构建完成: dist\发票助手\
pause
