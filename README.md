# 佛教基础理论结构树 · Buddhist Doctrines

**English** · [中文](#中文)　·　[Jump to English](#english)

一份把佛教基础理论组织为十二层结构的单页参考：230 个概念、619 条带类型的关系、549 条文献出处引证，每个概念附释义、分栏年代与出处原文；中英双语，可离线使用。

*A single-page reference in twelve layers — 230 concepts, 619 typed relations, 549 cited passages — bilingual, self-contained, works offline.*

---

## English

A single-page reference that organises the foundational doctrines of Buddhism into **twelve layers**: 230 concepts, 619 typed relations between them, and 549 cited passages, each concept carrying a definition, the source it rests on, and dated textual layers.

**Read online (no download)**: <https://linlei1980.github.io/buddhist-doctrine-tree/en.html>
**Chinese edition**: <https://linlei1980.github.io/buddhist-doctrine-tree/>　·　a language switch sits at the top right of both pages
**Offline**: download [`en.html`](en.html) (English) or [`index.html`](index.html) (Chinese) — one file each, double-click to open in any browser. Both are self-contained: all styles, scripts and data are inline, with no network access and no external assets.

The two editions **search across each other**: on the English page you can type 缘起 or 俱舍论, and on the Chinese page you can type `dependent origination` or `Kośa`.

---

## Why this exists

The Buddhist canon is vast — the Tripiṭaka plus two thousand years of commentarial and scholastic literature. The beginner's difficulty is rarely a shortage of material. It is not knowing **where a concept sits within the system**, nor **when, by whom, and against what background it took shape**.

This page therefore:

- organises the material along a line that runs **from the problem to the system** — Four Noble Truths, three seals, dependent origination and karma, the Nikāyas and Abhidharma, Madhyamaka and Yogācāra, tathāgatagarbha, doctrinal classification and the schools — rather than listing entries in dictionary order;
- gives every concept four things: a **definition** (in three tiers: gist, exposition, disputed points), **dated textual layers**, **cited sources**, and **typed relations** to neighbouring concepts;
- splits the dating into three columns — *formation of the idea*, *fixation of the text*, *Chinese translation* — because for a single scripture these are often centuries apart, and collapsing them into one year falsifies the history;
- records the relations between concepts as ten types (Part · Sequence · Cause · Identity · Assessment · Contrast · Practice · Layer · Basis · Note), and gives doctrinal disagreement its own class of nodes and its own *Contrast* relation.

## Features

| View | Purpose |
|---|---|
| **Outline** | the twelve-layer tree; filterable by type of relation — selecting *Contrast* alone gives every disputed question |
| **Timeline** | the whole corpus in nine periods, with 31 key nodes marked, for tracing lines of development |
| **Study paths** | four routes: foundations (core claims and their reasons) → depth (scholastic literature, Madhyamaka and Yogācāra) → history (India to East Asia and Tibet) → practice (stages, methods, criteria) |
| **Canon index** | a searchable table of 148 texts; open any row to see every node that cites it |
| **Node view** | definition, dating, quoted sources, related nodes; terms inside a definition link straight through |

Search covers names, Indic terms, the body of the definitions, and the titles of cited texts — enter *Kośa* or *Mūlamadhyamakakārikā* to list everything relevant. Names are matched in Chinese, pinyin, English and Sanskrit. The current node is written into the URL, so a refresh or a shared link keeps its place. There is a separate narrow-screen layout for phones, and a print stylesheet that exports cleanly to PDF.

## Contents at a glance

| | |
|---|---|
| Concepts | 230 (50 of them text entries, generated automatically) |
| Typed relations | 619 in ten types, about 49 % of them crossing layers |
| Cited passages | 549, given down to fascicle, chapter or sutta number, with the quotation |
| Outline depth | 12 layers |
| Timeline | 9 periods, from about the 6th century BCE to the modern period |
| Categories | Four Noble Truths · three seals · origination and karma · Nikāyas and Abhidharma · Buddhist logic · two truths and three natures · non-self · tathāgatagarbha · doctrinal classification and schools · practice · contested questions · scriptural texts · textual layers and transmission |

Coverage includes the foundational teachings; the schools and Abhidharma; Madhyamaka and Yogācāra; tathāgatagarbha and Buddha-nature; Buddhist logic and *pramāṇa*; four classical disputes; the ten Chinese schools; the Tibetan lineages; the Southern Theravāda; the stages of practice and monastic procedure; cosmology; and the philology and transmission of the texts.

## Repository layout

```
index.html                ← Chinese edition (491 KB, self-contained) — the GitHub Pages home page
en.html                   ← English edition (674 KB, self-contained)
sitemap.xml               ← both URLs with hreflang annotations (generated)
og-image.png              ← 1280×640 social preview card (used by og:image)
robots.txt                ← crawl rules, pointing at the sitemap (generated)
archive/v1-原版.html       ← the 2026-09 first edition, kept only for comparison (see archive/README.md)

data/buddhism.json        ← snapshot of the Chinese data (for review, error-checking, reuse)
data/buddhism.data.js     ← the same data as a JS file

build/content_a.py        ← Chinese content: scholasticism, Mahāyāna, logic, disputes
build/content_b.py        ← Chinese content: doctrinal classification, the schools, practice
build/content_c.py        ← Chinese content: history and transmission
build/content_d.py        ← Chinese content: cosmology, monastic procedure, meditation, hermeneutics
build/build.py            ← main script: merge → normalise relations → build the tree → validate → emit both editions

build/render.py           ← bilingual renderer: swaps data and interface text per language, then assembles
build/render.js           ← front-end script (interface text injected at build time)
build/seg.py              ← styles and the HTML shell
build/make_pages.py       ← writes index.html and en.html
build/i18n_build.py       ← entry point for the English translation data
build/i18n/               ← English terms and translations
  ui.json                 ← interface text, categories, relation types, layers (zh/en pairs)
  TRANSLATION-SPEC.md     ← translation rules: terminology, style, acceptance checks
  doc_names.json          ← canonical English titles for cited texts, one name per work
  nodes.jsonl             ← English translations of the 179 hand-written nodes
  sources.json            ← Chinese–English index of 321 cited items
  work/                   ← per-batch inputs and translations, kept for review
build/README.md           ← how to generate and maintain the page
```

Only `index.html` and `en.html` need to be distributed. `build/` and `data/` are for editing the content; `archive/` is a record.

## Editing the content

Content and presentation are separate: definitions, sources and dating live as Python data in `build/content_*.py`; the build script merges, validates and renders the single-file pages.

```bash
python3 build/build.py          # Chinese data + both editions
python3 build/i18n_build.py     # rebuild the English translation data only
```

The main script runs five checks first, and prints a problem list if any fails: empty definition, no source, no dating, node absent from the outline, relation endpoint or type that does not exist. The English data has checks of its own: every id present, cross-reference ids identical to the Chinese, no Chinese characters left behind.

Two further checks run over the generated pages — a dependency-free one for structural integrity of the styles and metadata, and a headless-browser one asserting the computed styles and the interactions (that the outline is 398 px wide, that a node opens, that the canon index renders):

```bash
python3 build/verify_page.py     # static assertions, run by CI
node build/verify_page.mjs       # rendered check (skips itself if no Chrome)
```

See [`build/README.md`](build/README.md).

When adding a concept you **do not need to write cross-links by hand** — the first occurrence of another concept's name inside a definition becomes a clickable link automatically.

### The English edition

Definitions, source titles and classical Chinese quotations are translated in full. Terminology follows the Sanskrit or Pali original (dependent origination, non-self, tathāgatagarbha, the three natures); concepts coined in China use their established English form (the five periods and eight teachings; three thousand realms in a single moment of mind). The rules are in [`build/i18n/TRANSLATION-SPEC.md`](build/i18n/TRANSLATION-SPEC.md).

One deliberate difference from the Chinese edition: **the English page does not reproduce the Chinese source text** of a quotation. For a reader who does not read Chinese it is only noise; to check a passage against the original, open the same node in the Chinese edition.

## How to read it, and where this page stands

- **Dating.** All dates are approximate or given as a range. For the Buddha's dates there are three traditions — Southern (624–544 BCE), Chinese (565–486 BCE) and modern scholarship (c. 480–400 BCE) — and this page counts from "c. 5th century BCE" throughout, without adopting one.
- **Standpoint.** This page passes no judgement on the doctrines; it records structure, definitions, sources and dating. Where the schools differ over a concept (tathāgatagarbha, the two truths, unconditioned dharmas, the essence of the precepts), the divergence is marked at the node concerned and given its own contested-question nodes, so that a reader can compare them directly.
- **Textual layers.** Content is labelled early layer, developmental layer, folk layer, modern layer, meta layer. The translation history, Tibetan and Southern transmission, and scholarly discussion collected in layer 12 are material about the transmission and study of texts, and are not to be conflated with the doctrinal content of layers 01 to 11.
- **Text entries.** Each text cited by three or more nodes gets an entry of its own, giving its character, how often it is cited here, and the nodes that cite it — but **no date of its own**, because for a single scripture the origin of its teaching and the fixation of its text are often centuries apart; that judgement belongs to the nodes that discuss the text.

Corrections are welcome. If a definition is wrong, a quotation does not match its source, or a date is misjudged, please open an [issue](../../issues) or send a pull request.

## Licence

- **Code** (the scripts in `build/`, the page templates and styles): [MIT](LICENSE)
- **Content** (definitions, dating, the structure, the explanatory text): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Quotations from scriptures and treatises**: the Chinese Buddhist canon is largely in the public domain. Quotations here were checked against the *Taishō Tripiṭaka* (CBETA), with thanks.

If you reuse the content, please keep the attribution and a link back to this repository.

---

**Topics**: `buddhism` · `buddhist-studies` · `dharma` · `madhyamaka` · `yogacara` · `abhidharma` · `tathagatagarbha` · `chinese-buddhism` · `tibetan-buddhism` · `theravada` · `reference` · `knowledge-graph` · `static-site` · `gh-pages` · `bilingual`


---

## 中文

[English](#english) · **中文**

一份把佛教基础理论组织为**十二层结构**的单页参考：230 个概念，619 条带类型的概念关系，549 条文献出处引证，每个概念都标注释义、出处原文与分栏年代。

**在线查看（无需下载）**：<https://linlei1980.github.io/buddhist-doctrine-tree/>
**英文版**：<https://linlei1980.github.io/buddhist-doctrine-tree/en.html>　·　两页右上角均可切换语言
**离线使用**：下载 [`index.html`](index.html)（中文）或 [`en.html`](en.html)（英文）单个文件，双击用浏览器打开即可。两者都自包含全部样式、脚本与数据，不依赖网络与任何外部资源。

中英两版**可以互相检索**：中文页里输入 `dependent origination` 或 `Kośa` 能命中，英文页里输入「缘起」或「俱舍论」同样能命中。

---

## 这份东西解决什么问题

佛教文献浩繁——经、律、论三藏加上两千年的注疏与宗派著作。初学者面临的困难往往不是「找不到资料」，而是**不知道一个概念在体系中的位置**，以及**不知道它是什么时候、由谁、在什么背景下成形的**。

本页的做法是：

- 沿一条**由问题到体系**的线索组织内容——四圣谛、三法印、缘起业果、部派阿毗达磨、中观唯识、如来藏、判教与宗派——而不是按词典顺序罗列条目；
- 每个概念给出四项：**释义**（要义 / 展开 / 争议三层）、**分栏年代**、**出处引文**、**关联节点**；
- 把年代拆成三栏——**思想形成 / 文献定型 / 汉译流传**——因为三者常相差数百年，合并成一个年份会失真；
- 把概念之间的关系记为十种类型（支分 · 次第 · 因果 · 体同 · 判摄 · 对辨 · 修证 · 层积 · 依据 · 说明），并另设「论诤」类节点与「对辨」类关系专门记录宗派分歧。

## 功能

| 视图 | 用途 |
|---|---|
| **目录** | 十二层结构树；可按关系类型筛选——只看「对辨」即得全部论诤 |
| **年表** | 九个时段排列全部条目，标出 31 个重点节点，用来看发展线索 |
| **学习路径** | 四条读法：基础（核心主张与理由）→ 深入（部派论书、中观唯识）→ 脉络（印度至东亚与西藏）→ 实践（次第、方法、判准） |
| **经律论总览** | 148 种文献的检索表，点开可见全部引用它的节点 |
| **节点详情** | 释义、时间 · 层积、出处引文、关联节点；释义中的其他概念名可直接点击跳转 |

检索范围覆盖名称、梵巴原语、释义正文与所引经论名（例如输入《俱舍论》可列出全部相关节点）。名称支持中文、拼音、英文与梵文四种写法匹配。当前节点会写入 URL，刷新与分享不丢失位置。手机上有独立的窄屏布局；另有打印样式，可直接导出 PDF。

## 内容规模

| 项 | 数量 |
|---|---|
| 概念 | 230（其中 50 个为自动生成的文献节点） |
| 概念关系 | 619，规范为 10 类，约 49% 为跨层关系 |
| 出处引证 | 549 条，标至卷 / 品 / 经号并附原文 |
| 目录层级 | 12 层 |
| 年表时段 | 9 段（约前 6 世纪 — 近现代） |
| 分类 | 四圣谛 · 三法印 · 缘起业果 · 部派阿毗达磨 · 因明量论 · 二谛三性 · 无我 · 如来藏 · 判教宗派 · 修行实践 · 论诤 · 经律论文献 · 历史传播 |

覆盖范围包括：根本教义、部派与阿毗达磨、中观与唯识、如来藏与佛性、因明量论、四大论诤、汉传十宗、藏传诸派、南传上座部、修行次第与僧团行仪、宇宙论、文献与传播史。

## 仓库结构

```
index.html                ← 中文版成品（491 KB，自包含），GitHub Pages 首页
en.html                   ← 英文版成品（674 KB，自包含）
sitemap.xml               ← 两个地址与 hreflang 声明（生成产物）
og-image.png              ← 1280×640 社交分享预览图（供 og:image 使用）
robots.txt                ← 抓取规则，其中指明站点地图位置（生成产物）
archive/v1-原版.html       ← 2026-09 初版存档，仅用于对照修订过程（见 archive/README.md）

data/buddhism.json        ← 中文数据的 JSON 快照（供审阅、查错、二次开发）
data/buddhism.data.js     ← 同一份数据的 JS 形式

build/content_a.py        ← 中文内容：印度论书层、大乘中观唯识、因明、论诤
build/content_b.py        ← 中文内容：判教、汉传十宗、藏传南传、实践补全
build/content_c.py        ← 中文内容：历史与传播
build/content_d.py        ← 中文内容：宇宙论、戒律行仪、止观、四依
build/build.py            ← 主脚本：合并 → 规范化关系 → 建目录树 → 校验 → 产出两版页面

build/render.py           ← 双语渲染：按语言替换数据与界面文字并组装页面
build/render.js           ← 前端脚本（界面文字以 __UI__ 占位，生成时注入）
build/seg.py              ← 样式与 HTML 骨架
build/make_pages.py       ← 生成 index.html 与 en.html
build/i18n_build.py       ← 英文译文构建入口（合并各批译文、统一书名与体例）
build/i18n/               ← 英文译名与译文
  ui.json                 ← 界面文字、分类、关系类型、层积（中英对照）
  TRANSLATION-SPEC.md     ← 翻译规范：术语表、体例、验收标准
  doc_names.json          ← 经典题名的规范英译（同一部书只用一个名字）
  nodes.jsonl             ← 179 个人工节点的英文译文（合并产物）
  sources.json            ← 321 种出处条目的中英对照（合并产物）
  work/                   ← 分批翻译的输入与译文，保留以便复查
build/README.md           ← 生成与维护说明
```

`index.html` 与 `en.html` 是仅有的两个成品（双击即可离线使用，也可直接放在任何静态服务器上）；`build/` 与 `data/` 供改内容时使用，`archive/` 仅为存档。

## 修改与重新生成

内容与界面是分离的：释义、出处、年代以 Python 字面量存放于 `build/content_*.py`，组装脚本负责合并、校验并渲染出单文件页面。

```bash
python3 build/build.py          # 中文数据 + 两版页面
python3 build/i18n_build.py     # 只重建英文译文数据（改动译文后运行）
```

主脚本会先做五项校验，任一不通过即打印问题清单：释义为空、无出处、无年代、节点未进目录、关系端点或类型不存在。英文译文另有一套校验：每个 id 必须齐备、交叉引用 id 必须与中文一致、不得残留中文字符。详见 [`build/README.md`](build/README.md)。

新增概念时**不必手写交叉链接**——正文中首次出现的其他节点名会自动转为可点击链接。

### 英文版

英文版的释义、出处标题与古典引文均为全译，术语以梵文／巴利文为准（dependent origination、non-self、tathāgatagarbha、the three natures…）；汉地自撰概念用通行英译（the five periods and eight teachings、three thousand realms in a single moment of mind）。规范见 [`build/i18n/TRANSLATION-SPEC.md`](build/i18n/TRANSLATION-SPEC.md)。

**正文中的汉文引文不保留原文**——这是与中文版的一处有意区别：英文版面向不以汉文阅读的读者，保留原文徒增噪声；需要核对原文时请对照中文版同一节点。

节点名、出处题名与界面文字都在 `build/i18n/` 下，可直接编辑后重新生成，无须改动渲染代码。

## 引用与立场说明

- **年代**：所有年代均为约数或区间。佛陀生卒年有南传（前 624—前 544）、汉传（前 565—前 486）、现代学界（约前 480—前 400）三说，本页统一自「约前 5 世纪」起算，不取一说。
- **立场**：本页不作教义评判，仅收录理论结构、释义、文献出处与年代。宗派之间对部分概念（如来藏、二谛、无为法、戒体等）的解释互有出入，页内于相应节点标明分歧所在，并另设「论诤」类节点专门记录，读者可据此自行参校。
- **层积**：内容按早期层、发展层、民间层、近世层、元层积标注。「历史 · 传播」一层所收汉译史、藏译史、南传史与学界讨论，性质属文献的流传与研究，不宜与前十一层的教义内容混同看待。
- **文献节点**：被 3 个以上节点引用的文献各建一个节点，只交代其性质、引用规模与引用它的节点，**不标注该文献自身的年代**——同一部经的思想源头与文本定型常相差数百年，此类判断由讨论该文献的节点给出。

欢迎指正错误。若发现释义有误、出处引文与原文不符、或年代标注失当，请开 [Issue](../../issues) 或提交 Pull Request。

## 许可

- **代码**（`build/` 中的脚本、页面模板与样式）：[MIT](LICENSE)
- **内容**（各节点的释义、年代标注、结构编排与说明文字）：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.zh)
- **所引经文与论疏原文**：汉文佛典原文多属公有领域，本仓库仅为研究引用。引文原文据《大正新修大藏经》（CBETA 电子佛典集成）核对，谨此说明并致谢。

使用或转载内容时，请保留出处与本仓库链接。

---

**关键词（Topics）**：`buddhism` · `buddhist-studies` · `dharma` · `madhyamaka` · `yogacara` · `abhidharma` · `tathagatagarbha` · `chinese-buddhism` · `tibetan-buddhism` · `theravada` · `reference` · `knowledge-graph` · `static-site` · `gh-pages` · `bilingual` · `佛学` · `佛教` · `佛学入门` · `佛教知识体系` · `阿含` · `唯识` · `中观` · `天台` · `华严` · `禅宗` · `净土`


---

<sub>中英两版页面：[中文](https://linlei1980.github.io/buddhist-doctrine-tree/) ｜ [English](https://linlei1980.github.io/buddhist-doctrine-tree/en.html)</sub>
