#!/usr/bin/env python3
"""转录稿自检：$ 定界符配对、$$ 偶数、图片引用可达且无孤儿。

用法:
    python check_transcribe.py <转录稿.md> [-r 根目录]

退出码 0 = 全部通过；1 = 有问题。

计数口径（2026-10-12 v1.2.0 修）：
    - fenced 代码块（``` / ~~~）整段跳过；
    - **行内反引号 `` `...` `` 也整段剥掉** —— 校对说明里引用 MinerU 原始输出（如
      `` `M \\neq {-1,1,3}` ``）时，里面的符号不再被误当成正文 $ / $$ 计数。
"""
import argparse
import os
import re
import sys


def strip_inline_code(line):
    """去掉行内代码片段（反引号内的内容），避免把校对说明里引用的原样 LaTeX 当正文计数。

    - 先处理双反引号 `` ``...`` ``，再处理单反引号 `...`（不跨行）。
    - 这样 `` `M \\neq {-1,1,3}` `` 里的字符不再计入 $ / $$ 统计。
    """
    line = re.sub(r"``.+?``", "", line)
    line = re.sub(r"`[^`\n]*`", "", line)
    return line


def strip_fenced(txt):
    """去掉 fenced 代码块（``` 或 ~~~ 包裹，可跨行），用于 $$ 计数。"""
    txt = re.sub(r"^[ \t]*```.*?^[ \t]*```", "", txt, flags=re.S | re.M)
    txt = re.sub(r"^[ \t]*~~~.*?^[ \t]*~~~", "", txt, flags=re.S | re.M)
    return txt


def main():
    ap = argparse.ArgumentParser(description="数学转录稿格式与图片引用自检")
    ap.add_argument("md", help="待检查的 markdown 文件")
    ap.add_argument("-r", "--root", default=None, help="图片相对路径的基准目录，默认取 md 所在目录")
    a = ap.parse_args()

    md = os.path.abspath(a.md)
    root = a.root or os.path.dirname(md)
    with open(md, encoding="utf-8") as f:
        txt = f.read()
    lines = txt.split("\n")

    ok = True
    print("===== %s =====" % os.path.basename(md))

    # 1) 代码块外的行内 $ 配对（行内反引号里的内容先剥掉）
    in_code = False
    odd_lines = []
    total_dollar = 0
    for i, l in enumerate(lines, 1):
        if l.strip().startswith("```") or l.strip().startswith("~~~"):
            in_code = not in_code
            continue
        if in_code:
            continue
        bare = strip_inline_code(l)
        c = bare.count("$") - bare.count("\\$")
        total_dollar += c
        if c % 2:
            odd_lines.append(i)
    print("  行内 $ 不成对的行: %s" % (odd_lines if odd_lines else "无"))
    if odd_lines:
        ok = False
    print("  $ 总数: %d %s" % (total_dollar, "(偶数 OK)" if total_dollar % 2 == 0 else "(奇数 !! 检查)"))
    if total_dollar % 2:
        ok = False

    # 2) $$ 块配对（fenced 代码块 + 行内反引号都不计入）
    n_block = strip_fenced(strip_inline_code(txt)).count("$$")
    if n_block:
        print("  $$ 出现 %d 次 %s" % (n_block, "(偶数 OK)" if n_block % 2 == 0 else "(奇数 !! 检查)"))
        if n_block % 2:
            ok = False
    else:
        print("  $$ 出现 0 次")

    # 3) 图片引用可达性
    refs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", txt)
    refs = [r.strip() for r in refs]
    missing = []
    external = 0
    for r in refs:
        if re.match(r"^https?://", r):
            external += 1
            continue
        if not os.path.exists(os.path.join(root, r)):
            missing.append(r)
    print("  图片引用 %d 处（远程 %d），缺失: %s" % (len(refs), external, missing if missing else "无"))
    if missing:
        ok = False

    # 4) images/ 孤儿文件
    imgdir = os.path.join(root, "images")
    if os.path.isdir(imgdir):
        referenced = {os.path.basename(r) for r in refs}
        orphan = sorted(set(os.listdir(imgdir)) - referenced)
        print("  images/ 孤儿文件: %s" % (orphan if orphan else "无"))
        if orphan:
            ok = False

    print("  RESULT: %s" % ("PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
