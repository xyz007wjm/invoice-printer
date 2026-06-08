#!/bin/bash
# macOS 构建脚本
# 使用: chmod +x build_macos.sh && ./build_macos.sh

cd "$(dirname "$0")"

# 检查依赖
pip3 install -i https://mirrors.aliyun.com/pypi/simple/ PyQt5 PyMuPDF Pillow

# 生成图标 (.icns)
mkdir -p app/icon.iconset
python3 -c "
from PIL import Image
img = Image.open('app/icon.png')
for s in [16,32,64,128,256,512]:
    resized = img.resize((s,s), Image.LANCZOS)
    resized.save(f'app/icon.iconset/icon_{s}x{s}.png')
    if s < 512:
        resized.save(f'app/icon.iconset/icon_{s}x{s}@2x.png')
"
iconutil -c icns app/icon.iconset -o app/icon.icns
rm -rf app/icon.iconset

# 构建
/Users/zl/Library/Python/3.9/bin/pyinstaller --clean --noconfirm \
    --name "发票助手" \
    --icon "app/icon.icns" \
    --windowed \
    --add-data "app:app" \
    --hidden-import PyQt5.QtPrintSupport \
    --hidden-import PyQt5.QtSvg \
    --hidden-import PIL \
    main.py

echo "✅ macOS 构建完成: dist/发票助手.app"
open dist/
