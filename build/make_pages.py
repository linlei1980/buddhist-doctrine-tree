# -*- coding: utf-8 -*-
"""生成中英两版页面。由 build.py 末尾调用，也可单独运行。"""
import sys, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import render

def meta_zh():
    """中文版的年代说明：从页面模板里取（与数据无关的静态文字）"""
    import seg
    m = re.search(r'<div class="meta-note" id="metaNote">(.*?)</div>', seg.PAGE, re.S)
    return m.group(1) if m else ''

def main():
    mz = meta_zh()
    for lang in ('zh', 'en'):
        name, html = render.render_page(lang, mz)
        out = os.path.join(ROOT, name)
        open(out, 'w', encoding='utf-8').write(html)
        print('已生成 %-12s %8.1f KB' % (name, len(html.encode('utf-8')) / 1024))
    # 中文版另存一份中文名副本，便于本地识别
    import shutil
    shutil.copyfile(os.path.join(ROOT, 'index.html'),
                    os.path.join(ROOT, '佛教基础理论结构树-v2.html'))
    print('已同步 佛教基础理论结构树-v2.html')

if __name__ == '__main__':
    main()
