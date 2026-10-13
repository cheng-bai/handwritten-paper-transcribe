#!/usr/bin/env python3
"""按给定顺序把多张图片合并成一个 PDF（供 MinerU 转录用）。

用法:
    python images_to_pdf.py OUT.pdf IMG1 IMG2 [IMG3 ...] [--dpi 200]

要点:
    - 页序 = 命令行给出的顺序，不要用 glob 传参（顺序不确定）。
    - 保持各页原始像素尺寸；分辨率只写进 PDF 元数据（供打印/预览用）。
    - 依赖 Pillow（托管 python 环境已带）。
"""
import argparse
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("缺少 Pillow：请用带 Pillow 的 python 运行（如 ~/.workbuddy/binaries/python/envs/default/bin/python）")


def main():
    ap = argparse.ArgumentParser(description="多图按序合并为单个 PDF")
    ap.add_argument("out", help="输出 PDF 路径")
    ap.add_argument("images", nargs="+", help="按页序排列的图片路径")
    ap.add_argument("--dpi", type=float, default=200.0, help="写入 PDF 的分辨率标记，默认 200")
    a = ap.parse_args()

    pages = []
    for p in a.images:
        if not os.path.isfile(p):
            sys.exit("文件不存在: %s" % p)
        im = Image.open(p).convert("RGB")
        pages.append(im)
        print("add: %s %sx%s" % (os.path.basename(p), im.size[0], im.size[1]))

    out_dir = os.path.dirname(os.path.abspath(a.out))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    pages[0].save(a.out, save_all=True, append_images=pages[1:], resolution=a.dpi)
    print("saved: %s  (%d KB, %d pages)" % (a.out, os.path.getsize(a.out) // 1024, len(pages)))


if __name__ == "__main__":
    main()
