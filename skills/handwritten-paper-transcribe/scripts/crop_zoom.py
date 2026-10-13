#!/usr/bin/env python3
"""按比例裁剪图片局部并放大 —— 看清被手写覆盖/擦糊的印刷字。

用法:
    python crop_zoom.py SRC OUT --box x0,y0,x1,y1 [--scale 4] [--max-width 1400]
                                 [--gray] [--quality 85]
    python crop_zoom.py SRC OUT --grid [--max-width 1400] [--gray] [--quality 85]

说明:
    --box 用 0~1 的比例（左上、右下），与图片实际像素无关。
    输出宽度 = min(原区域宽 * scale, max-width)。因此**只裁窄区域**才能显著放大：
    全宽裁剪（比例宽约 1.0）时输出被限到 max-width，等于没放大。

    --grid 是「两步定位法」的第一步：在**缩到 max-width 的整图**上叠加 0.05 步长的
    比例网格（0.1 处加粗并标出比例值），用来一眼读出疑点所在的横带 y 范围，
    再据此写 --box 做第二步窄裁放大。直接凭感觉试 --box 会反复裁偏。

    --grid 模式下 --box 可省略（给了也不生效）。
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

GRID_MINOR = (255, 60, 60)     # 0.05 步长细线
GRID_MAJOR = (200, 0, 0)       # 0.1 步长粗线 + 标号
GRID_LABEL = (0, 60, 220)


def draw_grid(src, out, max_width, gray, quality):
    im = Image.open(src).convert("RGB")
    W, H = im.size
    # 先缩到 max_width（网格线才看得清、标号才不至于挤在一起）
    s0 = min(1.0, max_width / float(W))
    if s0 < 1.0:
        im = im.resize((max(1, int(W * s0)), max(1, int(H * s0))), Image.LANCZOS)
    W, H = im.size

    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # 0.05 细线
    for i in range(1, 20):
        x = W * i / 20.0
        y = H * i / 20.0
        d.line([(x, 0), (x, H)], fill=GRID_MINOR, width=1)
        d.line([(0, y), (W, y)], fill=GRID_MINOR, width=1)
    # 0.1 粗线 + 标号
    for j in range(1, 10):
        x = W * j / 10.0
        y = H * j / 10.0
        d.line([(x, 0), (x, H)], fill=GRID_MAJOR, width=3)
        d.line([(0, y), (W, y)], fill=GRID_MAJOR, width=3)
        if font is not None:
            d.text((x + 2, 2), "x=%.1f" % (j / 10.0), fill=GRID_LABEL, font=font)
            d.text((2, y + 2), "y=%.1f" % (j / 10.0), fill=GRID_LABEL, font=font)

    if gray:
        im = im.convert("L")
    out_dir = os.path.dirname(os.path.abspath(out))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    im.save(out, quality=quality, optimize=True)
    print("%s  %sx%s  %d KB  (grid 0.05/0.1, 缩到宽 %d)"
          % (out, im.size[0], im.size[1], os.path.getsize(out) // 1024, max_width))


def main():
    ap = argparse.ArgumentParser(description="窄区域裁剪并放大 / 比例网格定位")
    ap.add_argument("src", help="源图路径")
    ap.add_argument("out", help="输出图路径")
    ap.add_argument("--box", default=None, help="裁剪框，比例形式 x0,y0,x1,y1（0~1）；--grid 时可省")
    ap.add_argument("--grid", action="store_true", help="整图叠加 0.05/0.1 比例网格，用于读出 --box 的 y 范围")
    ap.add_argument("--scale", type=float, default=4.0, help="放大倍数上限，默认 4")
    ap.add_argument("--max-width", type=int, default=1400, help="输出宽度上限，默认 1400")
    ap.add_argument("--gray", action="store_true", help="转灰度（手写笔画更清晰、体积更小）")
    ap.add_argument("--quality", type=int, default=85, help="JPEG 质量，默认 85")
    a = ap.parse_args()

    if a.grid:
        draw_grid(a.src, a.out, a.max_width, a.gray, a.quality)
        return

    if not a.box:
        raise SystemExit("需要 --box（或改用 --grid 先定位）")
    try:
        x0, y0, x1, y1 = [float(v) for v in a.box.split(",")]
    except ValueError:
        raise SystemExit("--box 需形如 0.34,0.39,0.62,0.43")

    im = Image.open(a.src).convert("RGB")
    W, H = im.size
    box = (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))
    c = im.crop(box)
    if a.gray:
        c = c.convert("L")

    w, h = c.size
    s = min(a.scale, a.max_width / float(w))
    if s != 1:
        c = c.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)

    out_dir = os.path.dirname(os.path.abspath(a.out))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    c.save(a.out, quality=a.quality, optimize=True)
    print("%s  %sx%s  %d KB  (scale=%.2f)" % (a.out, c.size[0], c.size[1], os.path.getsize(a.out) // 1024, s))


if __name__ == "__main__":
    main()
