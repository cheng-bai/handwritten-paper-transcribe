# 出片与交付：试卷转录稿 → 学生版 / 教师版 PDF

本文件是「手写试卷全链路」第 7~9 步的操作手册。**出片参数的真源是 `math-handout-pdf` 技能**
（`scripts/build-handout.py`），本文件只记录**试卷类**已验证的调用方式与实测坑；两者不一致时以
`math-handout-pdf` 当前值为准。

---

## 一、学生版

### 1. 生成学生版 md

用本技能的 `scripts/make_student_md.py` 从转录稿出题面 + 作答框（题干逐字抽取，不重抄）：

```bash
PY=~/.workbuddy/binaries/python/envs/default/bin/python
"$PY" scripts/make_student_md.py \
  --src "<录音稿> 转录稿YYYYMMDD.md" \
  --out "<卷名> 学生版YYYYMMDD.md" \
  --fill-mm 40 --choice-mm 40 --solve-mm 120 \
  --heights "17=80,18=80,19=120,20=120,21=150"
```

- 题型自动按大题标题（含「填空 / 选择 / 解答」）分档；`--heights` 逐题覆盖。
- `--report` 可干跑，只打印统计。
- 脚本自己打三项核对：**题号数 == 作答框数**、图引用数、**泄漏词命中数应为 0**；不一致 exit 1。
- frontmatter 默认带 `--fig-preset exam55`（试卷插图 55% 口径快照）。

### 2. 出 PDF

```bash
/opt/homebrew/bin/python3 ~/.workbuddy/skills/math-handout-pdf/scripts/build-handout.py \
  --src "<卷名> 学生版YYYYMMDD.md" \
  --out "<卷名> 学生版YYYYMMDD.pdf" \
  --mode student --theme color \
  --build work/build-<卷名简写>-student \
  --expect-boxes 21 \
  --box-mm 40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,40,80,80,120,120,150
```

- `--expect-boxes` 必须等于 md 里 `class="answer-space"` 的**实际个数**（先 `grep -c`）。
- `--box-mm` 逐框设计高度，能查出"框被分页切开"。
- 全绿才算交付。

---

## 二、教师版

### 1. 先把答案与解析补成 md

教师版 = 题面 + **紧跟每题的**【答案】+【解析】。结构约定：

```
**17.**（本题共两小题，第一小题6分，第二小题8分，满分14分）
（题干原文，逐字保留）

**答案**：（1）…；（2）…

**解析**：（1）因为 …所以 …（完整推导）
（2）…
```

- `**答案**` / `**解析**` 必须是**行首独立加粗的标签行**（`build-handout.py` 靠它识别并给彩色小标签）。
- **不要**沿用原卷"卷末集中给答案"的排法，答案要贴在题后。
- 原卷**只给答案、没给过程**的题：**不补写解析**，只写答案并在末尾说明里注明。
- 题干里照抄原卷记号，别顺手改成更"标准"的写法（原卷写 $\overrightarrow{AB}$ 就别写 $\vec{AB}$）。

### 2. 出 PDF

```bash
/opt/homebrew/bin/python3 ~/.workbuddy/skills/math-handout-pdf/scripts/build-handout.py \
  --src "<卷名> 教师版YYYYMMDD.md" \
  --out "<卷名> 教师版YYYYMMDD.pdf" \
  --mode teacher --theme color \
  --build work/build-<卷名简写>-teacher \
  --uniq "三、解答题（本大题共有5题，满分78分" \
  --color-text-min 400
```

---

## 三、实测坑（2026-10-12 / 10-13 真踩）

| 坑 | 现象 | 处理 |
|---|---|---|
| `--color-text-min` 阈值 | 纯客观题学生版无【考点】标签 → 彩色文字天然只有二三百字，默认阈值（800/300）会误报 FAIL | 学生版传 **250** 左右；教师版彩色字少时传 **400**（实测 501 字时默认 FAIL） |
| `--expect-boxes` 计数 | 数错会漏掉被分页切开的框 | 先 `grep -c 'class="answer-space"'` 再填 |
| `node_modules` | 沙箱里 `npm install` 装不上 | **软链复用**现成目录：`ln -sfn <已有>/node_modules <builddir>/node_modules` |
| 中文路径配图 | 图片路径含中文会让出片中止 | 打印稿配图一律 **ASCII 名**放 `figs/` / `images/` |
| `--uniq` | 校验用的唯一串若写错会误判 | 传一个大题说明的**原文片段**（如"三、解答题（本大题共有5题，满分78分"） |
| 页脚 | 工作台版本要求零页脚 | 若目标是导入工作台，走 `math-handout-pdf` 的 `--no-page-number` 链路（另见 `xdf-digital-note-import`） |

## 四、交付

- 产物与 md、`images/` 同放**同一专属目录**：`<卷名> 转录YYYYMMDD/`。
- 文件名体现内容与用途、**不用下划线**、中文名：`<卷名> 学生版YYYYMMDD.pdf` / `<卷名> 教师版YYYYMMDD.pdf`。
- 交付前跑：`make_student_md.py` 自带统计 + `build-handout.py` 自检 + 本技能 `check_transcribe.py`（转录稿）。
- 用 `present_files` 同时呈上 PDF 与同名 md；**教师版排在学生版之前**（信息更全）。
