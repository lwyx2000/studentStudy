# -*- coding: utf-8 -*-
"""
从一张方形插画生成 Android 全套启动图标（自适应 + 传统 + 圆形）。

用法:
    python gen-android-icons.py <源图> [res目录] [CX,CY,R]

    CX,CY,R 为源图中的正方形裁剪区(中心与半径)，省略则用下面的默认值。

产物:
    mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher.png            (48/72/96/144/192, 圆角方, 透明角)
    mipmap-{...}/ic_launcher_round.png                                 (同上, 圆形裁剪)
    mipmap-{...}/ic_launcher_foreground.png                            (108/162/216/324/432, 自适应前景)
并打印建议的 ic_launcher_background 颜色。

设计要点:
  * 自适应前景画布为 108dp，系统只显示中央 66.67%(=72dp) 的遮罩区域，
    因此把选定的裁剪区域精确铺满该可见方块，四周用图像边缘延展填充，
    保证任何遮罩形状（圆/方圆/方）下都不出现接缝或空白。
  * 传统图标使用同一裁剪区域，配合圆角方/圆遮罩，三种形态视觉一致。
"""
import os
import sys

from PIL import Image, ImageDraw

# ---- 可调参数 ----
CROP_CX, CROP_CY, CROP_R = 730, 700, 660   # 源图中的正方形裁剪区域(中心 + 半径)
BG = (211, 231, 162)                        # 兜底背景色(取自源图绿色底)
LEGACY_RADIUS_RATIO = 0.20                  # 传统图标圆角比例
SS = 4                                      # 遮罩超采样倍数(抗锯齿)

DENSITIES = {
    'mdpi':    {'legacy': 48,  'fg': 108},
    'hdpi':    {'legacy': 72,  'fg': 162},
    'xhdpi':   {'legacy': 96,  'fg': 216},
    'xxhdpi':  {'legacy': 144, 'fg': 324},
    'xxxhdpi': {'legacy': 192, 'fg': 432},
}


def rounded_mask(size, ratio, ss=SS):
    s = size * ss
    r = max(1, int(s * ratio))
    m = Image.new('L', (s, s), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, s - 1, s - 1), radius=r, fill=255)
    return m.resize((size, size), Image.LANCZOS)


def circle_mask(size, ss=SS):
    s = size * ss
    m = Image.new('L', (s, s), 0)
    ImageDraw.Draw(m).ellipse((0, 0, s - 1, s - 1), fill=255)
    return m.resize((size, size), Image.LANCZOS)


def crop_square(src):
    box = (CROP_CX - CROP_R, CROP_CY - CROP_R, CROP_CX + CROP_R, CROP_CY + CROP_R)
    return src.crop(box)


def make_legacy(src, px, mask):
    img = crop_square(src).resize((px, px), Image.LANCZOS).convert('RGBA')
    img.putalpha(mask)
    return img


def make_foreground(src, canvas_px):
    """108dp 画布：选定裁剪铺满中央 72dp 可见区，四周边缘延展。"""
    src_w = src.width
    visible = 72.0 / 108.0
    src_px = max(1, int(round(canvas_px * visible * (src_w / (2.0 * CROP_R)))))
    img = src.resize((src_px, src_px), Image.LANCZOS)
    s = img.width
    off_x = int(round(canvas_px / 2.0 - (CROP_CX / src_w) * s))
    off_y = int(round(canvas_px / 2.0 - (CROP_CY / src_w) * s))
    canvas = Image.new('RGB', (canvas_px, canvas_px), BG)
    for ax in (-s, 0, s):          # 先铺 8 个边缘延展副本，中心最后盖上去
        for ay in (-s, 0, s):
            if ax == 0 and ay == 0:
                continue
            canvas.paste(img, (off_x + ax, off_y + ay))
    canvas.paste(img, (off_x, off_y))
    return canvas.convert('RGBA')


def main():
    global CROP_CX, CROP_CY, CROP_R
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    src_path = sys.argv[1]
    res_dir = sys.argv[2] if len(sys.argv) > 2 else r'careless-correction\android\app\src\main\res'
    if len(sys.argv) > 3:
        CROP_CX, CROP_CY, CROP_R = (int(v) for v in sys.argv[3].split(','))
    src = Image.open(src_path).convert('RGB')

    written = []
    for dens, cfg in DENSITIES.items():
        d = os.path.join(res_dir, 'mipmap-' + dens)
        os.makedirs(d, exist_ok=True)

        legacy = make_legacy(src, cfg['legacy'], rounded_mask(cfg['legacy'], LEGACY_RADIUS_RATIO))
        round_ = make_legacy(src, cfg['legacy'], circle_mask(cfg['legacy']))
        fg = make_foreground(src, cfg['fg'])

        for name, im in (('ic_launcher.png', legacy),
                         ('ic_launcher_round.png', round_),
                         ('ic_launcher_foreground.png', fg)):
            p = os.path.join(d, name)
            im.save(p)
            written.append('%s  %dx%d' % (p, im.width, im.height))

    for w in written:
        print(w)
    print('背景色建议: #FF%02X%02X%02X' % BG)
    return 0


if __name__ == '__main__':
    sys.exit(main())
