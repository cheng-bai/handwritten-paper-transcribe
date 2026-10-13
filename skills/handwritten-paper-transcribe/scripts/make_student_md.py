#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从「试卷转录稿」生成「学生版 md」（题面逐字保留 + 每题后作答留白框）。

背景：试卷转录稿的题号是行首加粗 `**1.**`、大题是 `## 一、填空题（…）`。学生版要求
题干逐字保留（不重抄、不改写），删掉答案与解析，每题后给一块 A4 上可书写的留白；
留白高度按「填空题 / 选择题 / 解答题」分档，并可逐题覆盖。手工摘抄容易串行、漏题、
把【答案】【解析】顺手带过去，所以做成脚本：题干直接抽取 + 生成后跑泄漏自检。

用法
----
  python3 make_student_md.py --src 转录稿.md --out 学生版.md
  python3 make_student_md.py --src 转录稿.md --out 学生版.md \
      --fill-mm 40 --choice-mm 40 --solve-mm 120 \
      --heights "17=80,18=80,19=120,20=120,21=150"

参数
----
  --src PATH          试卷转录稿 md（由 MinerU 转录 + 逐题校对后的稿子）
  --out PATH          输出学生版 md
  --title TEXT        标题（默认取转录稿 frontmatter 的 title）
  --fill-mm N         填空题作答区高度，默认 40
  --choice-mm N       选择题作答区高度，默认 40
  --solve-mm N        解答题作答区高度，默认 120
  --heights "N=mm,…"  逐题精确覆盖（优先于上面三档）
  --fig-preset P      exam55（默认，试卷类插图口径）| none
  --fig-kv "k=v,…"    追加/覆盖 frontmatter 的插图键
  --keep-tags         保留【考点：…】等标签行（默认不删，转录稿本就没有）
  --report            只打印统计不写文件（干跑）

生成后**必看**脚本打印的三项统计：题号数 == 作答框数、图引用数、泄漏词命中数应为 0。

留白经验值（mm）：填空 / 选择 40；解答按问数 —— 两问 80~90、三问 120~150。
自动档只是起点，正式交付前用 --heights 精调。**以 math-handout-pdf 技能的口径为准。**
"""
import argparse
import re
import sys
from pathlib import Path

# 学生版里绝不该出现的词（若命中说明解析/答案泄漏进来了）
LEAK_WORDS = ["参考答案", "完整推导", "解题总结", "解析", "要点", "卡点", "答案"]
# 白名单：这些是卷面说明，不算泄漏
LEAK_OK = ["作答", "答题纸", "答题"]

# 试卷类插图口径（55% 快照；真源是 math-handout-pdf 技能）
FIG_PRESET = {
    "exam55": {
        "fig_width": "23%",
        "fig_max_height": "37mm",
        "fig_group_width": "10%",
        "fig_group_max_height": "50mm",
        "fig_fallback_max_height": "40mm",
    },
    "none": {},
}

QX = re.compile(r"^\*\*(\d+)\.\*\*")
H2 = re.compile(r"^##\s+(.*)$")
FM = re.compile(r"^(?:\\?-{3,})\s*\n(.*?)\n(?:\\?-{3,})\s*\n", re.S)


def section_kind(heading: str) -> str:
    if "填空" in heading:
        return "fill"
    if "选择" in heading:
        return "choice"
    if "解答" in heading:
        return "solve"
    return "solve"


def main():
    ap = argparse.ArgumentParser(description="试卷转录稿 → 学生版 md（题面 + 作答留白框）")
    ap.add_argument("--src", required=True, help="试卷转录稿 md")
    ap.add_argument("--out", default=None, help="输出学生版 md")
    ap.add_argument("--title", default=None, help="标题，默认取转录稿 frontmatter 的 title")
    ap.add_argument("--fill-mm", type=int, default=40, help="填空题留白，默认 40")
    ap.add_argument("--choice-mm", type=int, default=40, help="选择题留白，默认 40")
    ap.add_argument("--solve-mm", type=int, default=120, help="解答题留白，默认 120")
    ap.add_argument("--heights", default="", help='逐题覆盖，如 "17=80,21=150"')
    ap.add_argument("--fig-preset", choices=sorted(FIG_PRESET), default="exam55")
    ap.add_argument("--fig-kv", default="", help='追加 frontmatter 键，如 "fig_width=25%"')
    ap.add_argument("--report", action="store_true", help="只统计不写文件")
    args = ap.parse_args()

    src = Path(args.src).expanduser().resolve()
    if not src.is_file():
        sys.exit("转录稿不存在: %s" % src)
    txt = src.read_text(encoding="utf-8")

    # --- 剥 frontmatter（兼容 --- 与 \--- 两种写法），抽 title ---
    title = args.title
    m = FM.match(txt)
    if m:
        fm_body = m.group(1)
        if not title:
            tm = re.search(r"(?m)^title:\s*(.+?)\s*$", fm_body)
            if tm:
                title = tm.group(1).strip()
        txt = txt[m.end():]
    if not title:
        h1 = re.search(r"(?m)^#\s+(.+?)\s*$", txt)
        title = h1.group(1).strip() if h1 else src.stem

    # --- 砍掉末尾的校对说明（不进学生版）---
    cut = txt.find("## 转录与校对说明")
    if cut != -1:
        txt = txt[:cut]

    # --- 逐题切块 ---
    default_mm = {"fill": args.fill_mm, "choice": args.choice_mm, "solve": args.solve_mm}
    overrides = {}
    for kv in filter(None, (s.strip() for s in args.heights.split(","))):
        if "=" not in kv:
            sys.exit('--heights 需形如 "17=80,21=150"，收到: %s' % kv)
        k, v = kv.split("=", 1)
        overrides[int(k.strip())] = int(v.strip())

    out, cur, buf, kind = [], None, [], "solve"
    seq = []  # (题号, 题型)  用于核对与统计

    def flush(qno, body):
        if qno is None:
            return
        while body and body[-1].strip() == "":
            body.pop()
        out.extend(body)
        out.append("")
        h = overrides.get(qno, default_mm[kind])
        out.append('<div class="answer-space" style="height:%dmm;border:1px dashed #b9c0e0;'
                   'border-radius:6px;"><span class="as-label">作答区</span></div>' % h)
        out.append("")

    for ln in txt.split("\n"):
        h2 = H2.match(ln)
        if h2:
            flush(cur, buf)
            cur, buf = None, []
            kind = section_kind(h2.group(1))
            out.append(ln)
            out.append("")
            continue
        qm = QX.match(ln)
        if qm:
            flush(cur, buf)
            cur, buf = int(qm.group(1)), [ln]
            seq.append((cur, kind))
        elif cur is None:
            out.append(ln)
        else:
            buf.append(ln)
    flush(cur, buf)

    # 压掉连续空行
    res = []
    for ln in out:
        if ln.strip() == "" and res and res[-1].strip() == "":
            continue
        res.append(ln)
    body = "\n".join(res).strip() + "\n"

    # --- frontmatter ---
    fig = dict(FIG_PRESET[args.fig_preset])
    for kv in filter(None, (s.strip() for s in args.fig_kv.split(","))):
        if "=" in kv:
            k, v = kv.split("=", 1)
            fig[k.strip()] = v.strip()
    header = "---\ntitle: %s（学生版）\n" % title
    for k, v in fig.items():
        header += "%s: %s\n" % (k, v)
    header += "---\n\n"
    text = header + body

    # --- 统计与自检 ---
    n_boxes = text.count('class="answer-space"')
    n_q = len(re.findall(r"(?m)^\*\*\d+\.\*\*", text))
    n_fig = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", text))
    leaks = {}
    for w in LEAK_WORDS:
        hits = len(re.findall(re.escape(w), text))
        if hits:
            leaks[w] = hits

    print("src        : %s" % src)
    print("title      : %s" % title)
    print("题号个数    : %d" % n_q)
    print("作答框个数  : %d %s" % (n_boxes, "OK" if n_boxes == n_q else "!! 与题号数不符"))
    print("图引用     : %d" % n_fig)
    by_kind = {}
    for q, k in seq:
        by_kind.setdefault(k, []).append(q)
    for k in ("fill", "choice", "solve"):
        if by_kind.get(k):
            qs = by_kind[k]
            print("  %-6s 题号 %d-%d 共 %d 题" % (k, min(qs), max(qs), len(qs)))
    print("泄漏词命中  : %s" % (leaks if leaks else "无"))
    ok = (n_boxes == n_q) and not leaks
    print("RESULT     : %s" % ("PASS" if ok else "FAIL"))

    if args.report:
        print("（--report 干跑，未写文件）")
        sys.exit(0 if ok else 1)
    if not args.out:
        sys.exit("需给 --out（或用 --report 干跑）")
    outp = Path(args.out).expanduser().resolve()
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(text, encoding="utf-8")
    print("saved      : %s" % outp)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
