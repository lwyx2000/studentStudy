"""
生成安卓 APK 各分辨率图标
用法: python generate-icons.py
需要 Pillow: pip install Pillow
"""
import os
try:
    from PIL import Image, ImageDraw
except ImportError:
    os.system("pip install Pillow")
    from PIL import Image, ImageDraw

# 图标尺寸映射 (Android mipmap)
SIZES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

# 前景图标尺寸 (adaptive icon foreground)
FG_SIZES = {
    'mipmap-mdpi': 108,
    'mipmap-hdpi': 162,
    'mipmap-xhdpi': 216,
    'mipmap-xxhdpi': 324,
    'mipmap-xxxhdpi': 432,
}

RES_DIR = os.path.join(os.path.dirname(__file__), 'android', 'app', 'src', 'main', 'res')

def draw_fox(draw, size, offset=0):
    """绘制可爱小狐狸图标"""
    cx = size / 2 + offset
    cy = size / 2 + offset
    r = size * 0.35  # 头部半径

    # 耳朵（橙色三角形）
    ear_color = (255, 138, 101)
    ear_inner = (255, 171, 145)
    ear_size = r * 0.6

    # 左耳外
    draw.polygon([
        (cx - r * 0.7, cy - r * 0.3),
        (cx - r * 1.1, cy - r * 1.3),
        (cx - r * 0.2, cy - r * 0.9),
    ], fill=ear_color)
    # 左耳内
    draw.polygon([
        (cx - r * 0.65, cy - r * 0.4),
        (cx - r * 0.9, cy - r * 1.0),
        (cx - r * 0.3, cy - r * 0.85),
    ], fill=ear_inner)

    # 右耳外
    draw.polygon([
        (cx + r * 0.7, cy - r * 0.3),
        (cx + r * 1.1, cy - r * 1.3),
        (cx + r * 0.2, cy - r * 0.9),
    ], fill=ear_color)
    # 右耳内
    draw.polygon([
        (cx + r * 0.65, cy - r * 0.4),
        (cx + r * 0.9, cy - r * 1.0),
        (cx + r * 0.3, cy - r * 0.85),
    ], fill=ear_inner)

    # 头部（浅橙圆形）
    draw.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 1.1], fill=(255, 171, 145))

    # 白色嘴部区域
    mouth_r = r * 0.55
    draw.ellipse([cx - mouth_r, cy - mouth_r * 0.3, cx + mouth_r, cy + mouth_r * 1.2], fill=(255, 255, 255))

    # 眼睛
    eye_r = r * 0.08
    eye_offset_x = r * 0.35
    eye_y = cy - r * 0.15
    # 左眼
    draw.ellipse([cx - eye_offset_x - eye_r, eye_y - eye_r, cx - eye_offset_x + eye_r, eye_y + eye_r], fill=(62, 39, 35))
    # 左眼高光
    draw.ellipse([cx - eye_offset_x - eye_r * 0.3, eye_y - eye_r * 0.5, cx - eye_offset_x + eye_r * 0.3, eye_y + eye_r * 0.2], fill=(255, 255, 255))
    # 右眼
    draw.ellipse([cx + eye_offset_x - eye_r, eye_y - eye_r, cx + eye_offset_x + eye_r, eye_y + eye_r], fill=(62, 39, 35))
    # 右眼高光
    draw.ellipse([cx + eye_offset_x - eye_r * 0.3, eye_y - eye_r * 0.5, cx + eye_offset_x + eye_r * 0.3, eye_y + eye_r * 0.2], fill=(255, 255, 255))

    # 鼻子
    nose_r = r * 0.07
    draw.ellipse([cx - nose_r, cy + r * 0.15 - nose_r, cx + nose_r, cy + r * 0.15 + nose_r], fill=(62, 39, 35))

    # 嘴巴微笑
    smile_r = r * 0.15
    draw.arc([cx - smile_r, cy + r * 0.2, cx + smile_r, cy + r * 0.5], 0, 180, fill=(62, 39, 35), width=max(1, int(size * 0.015)))

    # 腮红
    cheek_r = r * 0.1
    cheek_color = (255, 205, 210)
    draw.ellipse([cx - r * 0.65 - cheek_r, cy + r * 0.1 - cheek_r, cx - r * 0.65 + cheek_r, cy + r * 0.1 + cheek_r], fill=cheek_color)
    draw.ellipse([cx + r * 0.65 - cheek_r, cy + r * 0.1 - cheek_r, cx + r * 0.65 + cheek_r, cy + r * 0.1 + cheek_r], fill=cheek_color)


def generate_icon(size, bg=True):
    """生成单个图标"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if bg:
        # 圆角背景
        bg_color = (255, 224, 178)  # 温暖的浅橙
        margin = size * 0.05
        radius = (size - margin * 2) / 2
        draw.ellipse([margin, margin, size - margin, size - margin], fill=bg_color)

    draw_fox(draw, size)
    return img


def generate_foreground(size):
    """生成 adaptive icon 前景（透明背景，居中 66%）"""
    fg_size = int(size * 0.66)
    img = Image.new('RGBA', (fg_size, fg_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_fox(draw, fg_size)

    # 放到中心，四周留白
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    offset = (size - fg_size) // 2
    result.paste(img, (offset, offset), img)
    return result


def main():
    print("生成小树成长岛 APK 图标...")

    for folder, size in SIZES.items():
        dir_path = os.path.join(RES_DIR, folder)
        os.makedirs(dir_path, exist_ok=True)

        # ic_launcher.png (带背景)
        icon = generate_icon(size, bg=True)
        icon.save(os.path.join(dir_path, 'ic_launcher.png'))
        icon.save(os.path.join(dir_path, 'ic_launcher_round.png'))

        # ic_launcher_foreground.png (透明背景，自适应图标前景)
        fg = generate_foreground(size)
        fg.save(os.path.join(dir_path, 'ic_launcher_foreground.png'))

        print(f"  [OK] {folder}: {size}x{size}")

    print("\n图标生成完成! ✓")
    print("图标: 可爱小狐狸 🦊")
    print("背景: 温暖浅橙色 #FFE0B2")


if __name__ == '__main__':
    main()
