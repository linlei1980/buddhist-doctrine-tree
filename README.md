# Buddhist Doctrines · A Structured Reference

**English** · [中文](README.zh-CN.md)

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
