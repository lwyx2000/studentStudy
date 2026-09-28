"""
将 GitHub访问令牌获取方法 (2).png 应用为 APK Logo
"""
import os
from PIL import Image, ImageDraw

SRC = r'D:\workspace\studentStudy\GitHub访问令牌获取方法 (2).png'
RES_DIR = r'D:\workspace\studentStudy\careless-correction\android\app\src\main\res'

SIZES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

FG_SIZES = {
    'mipmap-mdpi': 108,
    'mipmap-hdpi': 162,
    'mipmap-xhdpi': 216,
    'mipmap-xxhdpi': 324,
    'mipmap-xxxhdpi': 432,
}

def make_rounded_mask(size):
    """生成圆角矩形蒙版"""
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    radius = size * 0.2  # 20% 圆角
    draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    return mask

def make_round_mask(size):
    """生成圆形蒙版"""
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size, size], fill=255)
    return mask

def process():
    print(f'加载原图: {SRC}')
    src = Image.open(SRC).convert('RGBA')
    print(f'原图尺寸: {src.size}')

    for folder, size in SIZES.items():
        dir_path = os.path.join(RES_DIR, folder)
        os.makedirs(dir_path, exist_ok=True)

        # 缩放原图（保持高质量）
        icon = src.resize((size, size), Image.LANCZOS)

        # 背景色（从原图取平均色或固定暖橙）
        bg_color = (255, 224, 178)  # #FFE0B2 暖橙色

        # ic_launcher.png - 带圆角背景
        bg = Image.new('RGBA', (size, size), bg_color + (255,))
        mask = make_rounded_mask(size)
        bg.paste(icon, (0, 0), mask)
        bg.save(os.path.join(dir_path, 'ic_launcher.png'))

        # ic_launcher_round.png - 圆形裁剪
        round_icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        round_mask = make_round_mask(size)
        round_icon.paste(icon, (0, 0), round_mask)
        round_icon.save(os.path.join(dir_path, 'ic_launcher_round.png'))

        # ic_launcher_foreground.png - 透明背景图标（adaptive icon 前景）
        fg = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        fg.paste(icon, (0, 0))  # 原图直接作为前景
        fg.save(os.path.join(dir_path, 'ic_launcher_foreground.png'))

        print(f'  [OK] {folder}: {size}x{size}')

    print('\n所有图标已更新！')

if __name__ == '__main__':
    process()
