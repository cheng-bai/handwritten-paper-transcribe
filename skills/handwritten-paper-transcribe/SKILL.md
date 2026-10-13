---
name: handwritten-paper-transcribe
display_name: 手写试卷全链路（转录 → 双版本 PDF）
version: 2.0.0
description: 把"学生做过 / 教师批改过的手写试卷照片"一路做成可交付的学生版与学生版 PDF（全链路一个技能包到底）。链路为：扫描全能王手写擦除（camscanner `image enhance --mode 9`）→ 合成 PDF → MinerU 转录 → 对照原图逐题校对与润色 → 自检落盘 → 解全部题并做数值自验 → 出学生版（题面 + 作答留白）与教师版（答案 + 完整解析）PDF → 全绿后交付。MUST use when the user sends 手写/批改过的试卷照片（企业微信、微信、相机拍摄的 jpg/png）并要求"转录 / 转成可编辑版 / 录成 md / 去手写后再识别 / 出学生版 / 出教师版 PDF / 做成讲义"，或说"这几张卷子帮我转成文字 / 帮我出成卷子"。仅要擦手写不要文字走 `handwriting-remover`；**PDF**（非照片）转录润色走 `exam-paper-transcribe-polish`；读学生手写做错因诊断走 `exam-scan-error-diagnosis`；单纯从题库筛题出讲义走 `math-handout-pdf`。
description_zh: 手写试卷照片 → 去手写 → MinerU 转录 → 逐题对照原图校对润色 → 解题与数值自验 → 学生版 / 教师版 PDF → 交付自检（全链路）
author: chengbai
license: MIT
agent_created: true
---

# 手写试卷全链路（照片 → 双版本 PDF）

## 这个技能解决什么

手机拍的学生试卷（满页红蓝手写）直接喂 OCR，手写会被当成题目内容，识别结果一团糟。本技能的做法是**先把手写擦掉、拿到干净版面，再转录**，然后用"逐题对照原图"把 MinerU 的丢失与误识别补回来，最后**把卷子解出来、出成两版可打印 PDF**。

**核心认知一：去手写版是更好的转录源，但手写压印过的印刷字会被擦糊 —— 那几处必须回原图 + 用数学反推双验。**

**核心认知二：去手写也会把"学生填进印刷空格 / 横线作答处"的答案一并擦掉。凡是印刷体留空、横线、`______` 的作答位，必须回原图看学生填了什么 —— 干净版里那里是空白，光看它既读不出答案、也会误判"原卷漏印"。**

## 适用 / 不适用

| 场景 | 走哪条 |
|---|---|
| 手写卷**照片** → 转录稿 / 学生版 / 教师版 PDF | **本技能（全链路）** |
| 只要去手写、不要文字 | `handwriting-remover` |
| **PDF**（非照片）转录 + 润色 + 出片 | `exam-paper-transcribe-polish` |
| 读学生手写、做错因诊断 | `exam-scan-error-diagnosis` |
| 从题库/教辅筛题出讲义（不是照片） | `math-handout-pdf` |

## 前置检查（每次会话首次执行前）

```bash
CLI=/Users/thj/.local/bin/camscanner-cli
"$CLI" --version                 # 不在 PATH，必须绝对路径
"$CLI" auth status               # 需 {"authenticated": true}
ls /Users/thj/.local/bin/mineru-open-api                        # MinerU CLI，同样不在 PATH
ls /Users/thj/.workbuddy/skills/math-handout-pdf/scripts/build-handout.py   # 出片脚本
```

CLI 未装 / 未登录 → 先走 `camscanner` 官方技能（`scripts/setup.sh` 装、`auth login` 前台登录）。

## 全链路（九步）

### 第 0 步：拿到能读的图

企业微信/微信 @ 进来的路径（`~/Library/Containers/...`）**读不了**（macOS TCC）。让用户把图拖到 `~/Desktop`/`~/Downloads`/工作区。先核一遍：文件存在、是 JPG/JPEG/PNG、**单张 ≤ 40 MB**。

### 第 1 步：去手写（逐张）

```bash
"$CLI" image enhance "<原图>" --mode 9 -o "<输出目录>/<卷名> 第N页 去手写.jpg"
```

硬约束（都是踩过的）：

- **逐张执行，不要并发**（服务端限流）。批量时每张之间 `sleep 2`。
- **只给 `-o`，不要加 `-s`** —— `-s` 会把结果存进用户的扫描全能王云端账号。除非用户明确要云文档，否则不擅自往账号里写东西。
- **`-o` 会静默覆盖同名文件** → 写前先 `[ -e "$dst" ]` 判一下，存在就加序号或先问。
- **`-o` 的目标目录要先存在** —— CLI 不会自动建目录，先 `mkdir -p "<输出目录>"`（输入/输出路径都加引号，卷名里常有空格与中文）。
- **`--mode 9` 只擦手写**。改印刷文字是 `image scan`+`image edit`，去水印是 `--mode 10`，别混。

### 第 2 步：合 PDF（保页序）

MinerU 对 PDF 最稳。用 `scripts/images_to_pdf.py`，**页序按用户给的顺序显式传入**，别用 glob（顺序不确定）。

```bash
python scripts/images_to_pdf.py "<输出>/<卷名> 去手写版.pdf" \
  "<p1>" "<p2>" "<p3>" "<p4>" --dpi 200
```

### 第 3 步：MinerU 转录

```bash
export PATH="$HOME/.local/bin:$PATH"
mineru-open-api extract "<去手写版.pdf>" -f md -o "<工作目录>/mineru_out/" \
  --model vlm --language ch
```

`--model vlm` 对公式与版式更准。产 `<同名>.md` + `images/`。

### 第 4 步：图形完整性核对（必做）

MinerU 的 `images/` 常混入它额外裁出的公式碎片；同时正文可能有引用而磁盘缺图。用 `scripts/check_transcribe.py` 一次跑完（见第 6 步），重点看两个数：**引用 vs 磁盘是否一一对应**。若出现"引用里的图磁盘没有"→ 回 PDF 裁图补；"磁盘有图但正文没引用"→ 多半是公式碎片，确认后可删。

### 第 5 步：逐题对照原图校对与润色（本技能的核心，最花时间，不要跳）

**双源交叉看**：

- **去手写版** —— 读印刷字正文（手写已没了，最干净）。
- **原始照片** —— 读被手写压印处的印刷残影（去手写会把那里擦糊），**也读学生填进印刷作答空处的答案**（去手写连这个一起擦）。

**印刷作答空处必回原图**：凡是印刷体留空、横线、`______`、括号内作答题位，**一律回原图看学生填了什么**，不能只看干净版。实例：向明卷第 21(1)「与 $y=-x^2+4x$ 在区间　上的分割函数」——原卷印刷体在"在区间"与"上的"间**只留约半字空白、无区间记号**，但**原图空白正上方有学生手写的 $(-\infty,+\infty)$**，去手写版把这条线索整个擦掉了。所以"原卷是否真的漏印记号"与"学生填没填"是两件事，都要回原图才能判。

**窄区域放大 —— 两步定位法（别盲试）**：输出宽受限于 ~1400 px，全宽裁等于没放大 → **只裁疑点那十几个字符**，才能拉到 3~4 倍看清一字之差（`增/着`、`F₁/F₂`、`9/y`）。

1. **先定位**：`--grid` 在整图上叠加 0.05/0.1 比例网格（0.1 处加粗并标 $x=0.1\ldots$、$y=0.1\ldots$），一眼读出疑点所在**横带**的 $y$ 范围。
2. **再窄裁**：按该带取 `--box`，`--scale 4`（或更高）放大细看。

```bash
# 1) 定位：整图叠网格，读出疑点在 y≈0.73~0.77 这一横带
python scripts/crop_zoom.py "<原图>" "work/crops/q21_locate.jpg" --grid
# 2) 窄裁放大：只取那条带
python scripts/crop_zoom.py "<原图>" "work/crops/q21_raw.jpg" \
  --box 0.30,0.735,0.50,0.768 --scale 6
```

盲试 `--box` 会反复裁偏（实测量级：一个子 Agent 偏了约 20 次），先过一遍网格再裁能一次命中。

**数学反推验证（比看糊图可靠得多）**：被手写盖死、两版都读不出的参数，用题面其他条件或选项反推。实测例：第 15 题椭圆方程被写死，靠"若 $x^2/4+y^2/3=1$ 则与 $y^2=4x$ 交于 $x=2/3$，$|AB|=\frac{4}{3}\sqrt6$ 正合选项 B"一击锁定。

**MinerU 高频错型速查** → `references/mineru-math-error-catalog.md`（题号丢失、选项末位被吞、`\neq` 乱码、向量上横线↔箭头、指数负号被吞、凭空加粗升格、`F₁`/`F₂`、`\frac{y}{x}` vs `\frac{9}{x}` …），对照着逐题过。

**润色口径（明确边界，别越界）**：本技能的"润色"只做两件事 —— ① **修正识别错误**（回原图核对后改）；② **规范标点与题号样式**（题号加粗 `**1.**`、括号全角、补回缺失的作答横线）。**题干内容逐字保留：不改写、不补写、不"顺手润顺"**；数学记法照原卷（原卷写 $R$ 就别改成 $\mathbb{R}$）。改造过什么，一条条记进 md 末尾的【转录与校对说明】表里。

### 第 6 步：落盘与自检

**目录规范**（产物放专属目录，md 与配图同级，便于复用）：

```
<卷名> 转录YYYYMMDD/
├── <卷名> 转录稿YYYYMMDD.md
├── <卷名> 学生版YYYYMMDD.md / .pdf
├── <卷名> 教师版YYYYMMDD.md / .pdf
└── images/                      # 只放正文引用的图
```

md 结构（层级与写法都定死，出片才好切题）：

- frontmatter `title`（**不加引号**，加了会把引号印进标题）+ H1 卷名。
- **大题标题用 `##`、题号用加粗 `**1.**`** —— 即 `## 一、填空题：` 下接 `**1.** …`；**不要用 `### 第N题`**。
- **保留原卷的大题说明**（如"（本大题共有 12 题，满分 54 分，第 1-6 题每题 4 分…）"）—— 它是卷面信息，不删。
- **选择题选项 A/B/C/D 各起一行**（不要挤在一行里）。
- **印刷作答横线照抄为 `______`**（半角下划线；被 MinerU 吞掉的按填空题惯例补回）。
- 末尾一节 `## 转录与校对说明`（表格列"位置 / 原始输出 / 修正为" + 两栏"待核事项"）。

**自检（必跑，exit 0 才算交付）**：

```bash
python scripts/check_transcribe.py "<转录稿.md>"
```

覆盖三件事：`$` 定界符配对、`$$` 偶数、图片引用可达且无孤儿。计数口径：**fenced 代码块与行内反引号 `` `...` `` 内的内容整段跳过**（校对说明里引用 MinerU 原始输出如 `` `M \neq {-1,1,3}` ``、`` `$$` `` 时不会误报）。项目内若另有 `check_math.py`，两个都跑。

### 第 7 步：解题与数值自验（出教师版前必做）

1. **把全部题目解出来**：填空、选择、解答逐题给出答案；解答题给**完整推导**（这是要上课堂的）。选择填空也要有依据，别只报字母。
2. **原卷只给答案、没给过程的题：不补写解析**，只写答案，并在说明里注明"原卷未给过程"。
3. **难题做数值自验**（不是可选）：对解析几何 / 不等式最值 / 集合区间这类容易算错的题，写一个 numpy 脚本独立复算。

   ```bash
   # 向量化优先：别写 4000² 双重循环（会被 SIGTERM 杀掉）
   "$PY" work/<卷名>-test/solve_check.py
   ```

   - 被手写或印刷模糊导致条件不确定的，**把退化情形排除干净再报区间**（实测：某题初版把 $\alpha=0,\pi$ 的退化解算进去，区间从 $[-\frac65,\frac65]$ 错报成 $[-2,2]$）。
   - `scipy` 本机不可用 → 用网格搜索 + 解析推理替代 `linprog`。
4. **解不出/条件不全** → 在 md 末尾【待核事项】写清"按 X 解得 …；若实际为 Y 则 …"，**绝不猜一个值当确定值**。

### 第 8 步：出片（学生版 / 教师版）

**默认先问一句**（用户 2026-10-12 定的规则）：

> 要不要输出 PDF？要的话出学生版、教师版，还是都要？

- 用户本次已经明确说"要 / 都要 / 出学生版"→ **直接做，不用再问**。
- 问答过一次 → 不再追问第二次。
- 完整调用方式、参数、自检阈值与坑 → **`references/handout-build-and-delivery.md`**（本技能的操作手册）。
- **出片参数以 `math-handout-pdf` 技能为唯一真源**，调用前读它的 `SKILL.md` / `--help`；本技能的参考文件只是"试卷类已验证的调用快照"。

要点速览：

```bash
PY=~/.workbuddy/binaries/python/envs/default/bin/python
# 1) 学生版 md：题面逐字 + 每题作答留白框（脚本自带 题号数==作答框数 与 泄漏自检）
"$PY" scripts/make_student_md.py --src "<卷名> 转录稿YYYYMMDD.md" \
  --out "<卷名> 学生版YYYYMMDD.md" --heights "17=80,21=150"
# 2) 出 PDF（教师版同法，改 --mode teacher）
/opt/homebrew/bin/python3 ~/.workbuddy/skills/math-handout-pdf/scripts/build-handout.py \
  --src "<卷名> 学生版YYYYMMDD.md" --out "<卷名> 学生版YYYYMMDD.pdf" \
  --mode student --theme color --build work/build-<简写>-student \
  --expect-boxes <grep 出来的框数> --box-mm 40,40,...,150
```

- 留白经验值：填空 / 选择 **40mm**；解答按问数 —— 两问 80~90mm、三问 120~150mm。
- 试卷类插图套 **55% 口径**（`--fig-preset exam55` 已内置）。
- **`--color-text-min` 要放宽**：纯客观题学生版彩色文字只有二三百字，传 **250** 左右；教师版彩色字少时传 **400**（实测 501 字时默认 FAIL）。
- **`--expect-boxes` 必须等于 md 里 `class="answer-space"` 的实际个数**（先 `grep -c`）。
- **出片自检全绿**才算交付。

### 第 9 步：交付

- 产物与 md、`images/` 同放专属目录；文件名体现内容与用途、**不用下划线**、中文名。
- 用 `present_files` 呈上 PDF 与同名 md（**教师版排在学生版之前**，信息更全）。
- 回复里给出：页数、自检通过项、题目答案摘要、以及**遗留的待核项**。

## 硬约束与坑（全部实测）

1. **去手写会擦糊"手写压住印刷字"的位置** → 转录源用去手写版，但这些位置必须回原图 + 数学反推。学生规规矩矩在留白处作答的卷子效果最好；把答案写在题干/选项上的，擦完题干会花。
2. **去手写会擦掉"学生填进印刷作答空处的答案"** → 印刷体留空 / 横线 / `______` / 括号作答位，**必回原图看学生填了什么**；干净版那里是空白，只看它会误判"原卷漏印"、还丢掉学生答案。（实例见第 5 步。）
3. **图片上传扫描全能王云端处理** —— 含学生姓名/学号的卷子，**先裁掉或打码再上**，并事先告知用户。
4. **输出宽 ≤1400 px 才能放大** → 裁剪只裁窄区，别指望全宽放大；先 `--grid` 定位再窄裁（两步法），别盲试 `--box`。
5. **`-o` 静默覆盖**；`image enhance` 不改原图（安全），但仍先判目标是否存在；**`-o` 目标目录要先 `mkdir -p`**。
6. **题干逐字保留，绝不手抄**；只规范标点与题号样式，不动数学内容。
7. **读不清就标"待核"**，不许猜一个值填进去；待核项写进 md 末尾，并说明"若实际是 X，结论/答案会怎么变"。
8. **难题必须数值自验**，不许只在纸上推一遍就落进教师版（第 7 步）。
9. **学生版只留题面 + 作答框**：`make_student_md.py` 的"泄漏词命中"必须为 0；教师版的【答案】【解析】必须**紧跟试题**，不得沿用原卷"卷末集中给答案"的排法。
10. **出片参数以 `math-handout-pdf` 为真源**，本技能不复制它的整套参数，避免两处失同步。

## 脚本与解释器（别用错 python）

本机有两个 python，**依赖不同**，用错会 `ImportError`：

| 脚本 | 依赖 | 用哪个 python |
|---|---|---|
| `scripts/images_to_pdf.py` | Pillow | 托管 `~/.workbuddy/binaries/python/envs/default/bin/python`（或 `/opt/homebrew/bin/python3`） |
| `scripts/crop_zoom.py` | Pillow | 同上 |
| `scripts/make_student_md.py` | 仅标准库 | 任意 `python3` |
| `scripts/check_transcribe.py` | 仅标准库 | 任意 `python3` |
| `math-handout-pdf/scripts/build-handout.py` | PyMuPDF 等 | **`/opt/homebrew/bin/python3`**（`fitz` 只在这里） |

- 托管环境已带 Pillow/numpy；`fitz`(PyMuPDF) 只在 `/opt/homebrew/bin/python3`。
- 沙箱里 `npm install` 装不上 → 需要 `node_modules` 时**复用现成目录做软链**（`ln -sfn <已有>/node_modules <目标>/node_modules`），别重装。

## 参考

- `scripts/images_to_pdf.py` —— 图片按序合 PDF
- `scripts/crop_zoom.py` —— 窄区裁剪并放大；`--grid` 整图叠 0.05/0.1 比例网格用于定位
- `scripts/check_transcribe.py` —— 转录稿自检（`$` 配对 / `$$` 偶数 / 图片引用；跳过 fenced 代码块与行内反引号）
- `scripts/make_student_md.py` —— 转录稿 → 学生版 md（题面 + 作答框；自带计数与泄漏自检）
- `references/mineru-math-error-catalog.md` —— MinerU 中学数学卷高频错型清单与实例
- `references/handout-build-and-delivery.md` —— 出片与交付手册（学生版 / 教师版命令、自检阈值、实测坑）

---

**作者**：chengbai（上海 · 高中数学）　**许可**：MIT，见 `LICENSE`
版权归 chengbai 所有。使用、修改、再分发须保留本署名与 `LICENSE` 全文。
本技能方法整理自 2026-10 起在真实手写试卷上的实测迭代。
