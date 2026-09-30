# -*- coding: utf-8 -*-
"""页面产物检查：不依赖浏览器，断言生成的 HTML 结构完整、样式未被误删。

本脚本针对的是一类具体事故：生成 head 时把 <style> 段一并替换掉，
页面因此完全失去样式——所有元素退化为默认块级排列、目录宽达整屏、
徽章配色消失。这类事故 JS 与数据都正常，只靠内容比对发现不了，
故在此逐项断言。

退出码非 0 表示检查失败，可直接用于 CI。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 每份产物：文件名与必须出现的标记
PAGES = {
    'index.html': dict(
        lang='zh-CN', canonical='https://linlei1980.github.io/buddhist-doctrine-tree/',
        ui=['目录', '年表', '学习路径', '释义', '关联节点'],
        sample_node='四圣谛'),
    'en.html': dict(
        lang='en', canonical='https://linlei1980.github.io/buddhist-doctrine-tree/en.html',
        ui=['Outline', 'Timeline', 'Study paths', 'Definition', 'Related nodes'],
        sample_node='Four Noble Truths'),
}

# 缺了这些，样式必然不生效
CSS_MARKERS = ['--bg:', '.node-row', '.cstep', '@media (max-width:820px)', '@media print']
MIN_CSS_BYTES = 12000          # 样式表缩水到这个量级以下，说明被截断


def fail(msg, errs):
    errs.append(msg)


def check_page(name, spec, errs):
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
        return fail(f'{name}: 文件不存在', errs)
    s = open(path, encoding='utf-8').read()
    size = len(s.encode('utf-8'))

    # 1. 样式段完整
    styles = re.findall(r'<style>(.*?)</style>', s, re.S)
    if len(styles) != 1:
        fail(f'{name}: <style> 段数量为 {len(styles)}，应为 1', errs)
    else:
        css = styles[0]
        if len(css.encode('utf-8')) < MIN_CSS_BYTES:
            fail(f'{name}: 样式表仅 {len(css.encode("utf-8"))} 字节，疑被截断', errs)
        for m in CSS_MARKERS:
            if m not in css:
                fail(f'{name}: 样式表缺少 {m}', errs)

    # 2. 无占位符残留
    for ph in ('__CSS__', '__JS__', '__DATA__', '__UI__', '__DOCS__', '{{', '__META_FULL__'):
        if ph in s:
            fail(f'{name}: 存在未替换的占位符 {ph}', errs)

    # 3. head 元数据
    if f'<html lang="{spec["lang"]}">' not in s:
        fail(f'{name}: html lang 不是 {spec["lang"]}', errs)
    if f'rel="canonical" href="{spec["canonical"]}"' not in s:
        fail(f'{name}: canonical 不正确或缺席', errs)
    for tag in ('name="description"', 'name="keywords"', 'hreflang="en"',
                'hreflang="zh-Hans"', 'og:title', 'application/ld+json'):
        if tag not in s:
            fail(f'{name}: 缺少 {tag}', errs)

    # 4. JSON-LD 可解析
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    if m:
        try:
            ld = json.loads(m.group(1))
            if ld.get('@type') != 'LearningResource':
                fail(f'{name}: JSON-LD 的 @type 为 {ld.get("@type")}', errs)
        except Exception as e:
            fail(f'{name}: JSON-LD 无法解析（{e}）', errs)

    # 5. 数据与业务串：脚本段里应能看到节点数与界面文字
    i = s.find('<script>')
    js = s[i:] if i >= 0 else ''
    for k in spec['ui']:
        if k not in js:
            fail(f'{name}: 脚本段缺少界面文字「{k}」', errs)
    if spec['sample_node'] not in s:
        fail(f'{name}: 找不到示例节点「{spec["sample_node"]}」', errs)

    # 6. 内联数据可解析，且节点/关系数达到应有规模
    m = re.search(r'window\.BUDDHISM_DATA = (\{.*?\});</script>', s, re.S)
    if not m:
        fail(f'{name}: 找不到内联数据', errs)
    else:
        try:
            d = json.loads(m.group(1))
            n, e = len(d.get('nodes', {})), len(d.get('edges', []))
            if n < 200 or e < 500:
                fail(f'{name}: 数据规模异常（节点 {n}、关系 {e}）', errs)
            else:
                print(f'  {name}: {size/1024:.0f} KB，样式 {len(styles[0].encode("utf-8"))/1024:.0f} KB，'
                      f'节点 {n}、关系 {e}')
        except Exception as ex:
            fail(f'{name}: 内联数据无法解析（{ex}）', errs)

    # 7. HTML 标签区（脚本与样式之外）不得残留 Markdown 标记。
    #    内联数据里的 **粗体** / *书名* 是正常的 Markdown 源，浏览器渲染时转换，
    #    因此只检查标签区，避免把数据当正文误判。
    markup = re.sub(r'<script[\s\S]*?</script>', '', s)
    markup = re.sub(r'<style[\s\S]*?</style>', '', markup)
    if re.search(r'\*\*[^*\n]{2,40}\*\*', markup):
        fail(f'{name}: HTML 标签区存在未转换的 **粗体** 标记', errs)
    if re.search(r'\[\[[a-z0-9_]+\|', markup):
        fail(f'{name}: HTML 标签区残留未转换的交叉引用标记', errs)


def check_seo_files(errs):
    """sitemap.xml 与 robots.txt 必须存在，且地址与页面的 canonical 一致。"""
    sm = os.path.join(ROOT, 'sitemap.xml')
    rb = os.path.join(ROOT, 'robots.txt')
    for f in (sm, rb):
        if not os.path.exists(f):
            fail(f'{os.path.basename(f)}: 不存在', errs)
    if not os.path.exists(sm):
        return
    import xml.etree.ElementTree as ET
    try:
        root = ET.parse(sm).getroot()
    except Exception as e:
        return fail(f'sitemap.xml: 无法解析（{e}）', errs)
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9',
          'x': 'http://www.w3.org/1999/xhtml'}
    urls = [u.find('s:loc', ns).text for u in root.findall('s:url', ns)]
    want = {PAGES['index.html']['canonical'], PAGES['en.html']['canonical']}
    if set(urls) != want:
        fail(f'sitemap.xml: URL 集合为 {sorted(urls)}，与页面的 canonical 不一致', errs)
    for u in root.findall('s:url', ns):
        alts = {x.get('hreflang') for x in u.findall('x:link', ns)}
        if alts != {'zh-Hans', 'en', 'x-default'}:
            fail(f'sitemap.xml: {u.find("s:loc", ns).text} 的 hreflang 不完整（{sorted(alts)}）', errs)
    if os.path.exists(rb):
        r = open(rb, encoding='utf-8').read()
        if 'Sitemap:' not in r:
            fail('robots.txt: 缺少 Sitemap 行', errs)
        elif PAGES['index.html']['canonical'].rstrip('/') + '/sitemap.xml' not in r:
            fail('robots.txt: Sitemap 地址与仓库路径不一致', errs)
    print(f'  sitemap.xml: {len(urls)} 个 URL，hreflang 齐全 | robots.txt: 已声明 Sitemap')


def main():
    errs = []
    print('检查页面产物：')
    for name, spec in PAGES.items():
        check_page(name, spec, errs)
    check_seo_files(errs)
    if errs:
        print(f'\n检查未通过，{len(errs)} 个问题：')
        for e in errs:
            print('  ✗', e)
        return 1
    print('\n全部通过。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
