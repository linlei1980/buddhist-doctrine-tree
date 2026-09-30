# -*- coding: utf-8 -*-
"""生成社交分享预览图（og:image / twitter:image）：1280×640。

社交平台与即时通讯工具在分享链接时抓取这张图。设计取自页面自身的配色：
纸白底、朱砂强调色、深墨正文色。

依赖 Pillow。CI 上不安装 Pillow，故本脚本在缺少 Pillow 时**跳过并保留已有图片**，
不视为失败；图片本身提交进仓库，日常构建不需要重新生成。

    <python with Pillow> build/make_og_image.py
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1280, 640
BG, PANEL, LINE = '#F6F6F3', '#FFFFFF', '#E6E6E0'
INK, INK2, INK3 = '#1B2330', '#46536A', '#8A94A6'
ACCENT, INDIGO, VIOLET, GREEN = '#B45309', '#1D4ED8', '#7C3AED', '#15803D'

CJK_FONTS = ['/System/Library/Fonts/Hiragino Sans GB.ttc',
             '/System/Library/Fonts/STHeiti Medium.ttc',
             '/System/Library/Fonts/Supplemental/Songti.ttc',
             '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']
LATIN_FONTS = ['/System/Library/Fonts/Supplemental/Georgia.ttf',
               '/System/Library/Fonts/Helvetica.ttc',
               '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf']


def load(paths, size):
    from PIL import ImageFont
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap(draw, text, font, max_w):
    lines, cur = [], ''
    for ch in text:
        trial = cur + ch
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def main():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print('未安装 Pillow，跳过预览图生成（保留已有文件）。')
        return 0

    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)

    # 顶部朱砂色边条与左侧竖条，呼应页面的强调色
    d.rectangle([0, 0, W, 10], fill=ACCENT)
    d.rectangle([0, 0, 8, H], fill=ACCENT)

    cn_title = load(CJK_FONTS, 62)
    en_title = load(LATIN_FONTS, 34)
    body = load(CJK_FONTS, 25)
    small = load(CJK_FONTS, 21)
    tiny = load(CJK_FONTS, 18)
    mono = load(LATIN_FONTS, 19)

    x = 74
    # 主标题（中文）
    d.text((x, 92), '佛教基础理论结构树', font=cn_title, fill=INK)
    # 副标题（英文）
    d.text((x, 174), 'Buddhist Doctrines · A Structured Reference',
           font=en_title, fill=ACCENT)

    # 一句话说明
    line1 = '十二层结构，从四圣谛到汉传十宗；'
    line2 = '每个概念附释义、分栏年代与出处引文。'
    d.text((x, 240), line1, font=body, fill=INK2)
    d.text((x, 276), line2, font=body, fill=INK2)

    # 数据条：四块面板
    stats = [('230', '概念 / concepts', INK),
             ('831', '关系 / relations', INDIGO),
             ('549', '出处引证 / citations', VIOLET),
             ('12', '层级 / layers', GREEN)]
    y0, box_w, gap = 348, 268, 22
    for i, (num, label, color) in enumerate(stats):
        bx = x + i * (box_w + gap)
        d.rounded_rectangle([bx, y0, bx + box_w, y0 + 116], radius=12,
                            fill=PANEL, outline=LINE, width=2)
        d.rectangle([bx, y0, bx + 4, y0 + 116], fill=color)
        big = load(LATIN_FONTS, 44)
        d.text((bx + 22, y0 + 16), num, font=big, fill=color)
        for j, seg in enumerate(label.split(' / ')):
            d.text((bx + 22, y0 + 68 + j * 22), seg, font=tiny, fill=INK3)

    # 底部：两种语言与地址
    d.line([x, 508, W - 74, 508], fill=LINE, width=2)
    d.text((x, 528), '中英双语 · 可离线使用 · 引文标至卷品',
           font=small, fill=INK2)
    d.text((x, 560), 'linlei1980.github.io/buddhist-doctrine-tree',
           font=mono, fill=INK3)

    out = os.path.join(ROOT, 'og-image.png')
    img.save(out, 'PNG', optimize=True)
    print('已生成 og-image.png：%d×%d，%.0f KB' % (W, H, os.path.getsize(out) / 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())
