# -*- coding: utf-8 -*-
"""生成 sitemap.xml 与 robots.txt。

两版页面由同一份数据产出，URL 来自 build/i18n/ui.json 的 canonical 字段，
故站点地图不会与页面里的 canonical 脱节。
"""
import os, sys, json, datetime, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import i18n

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def main():
    zh = i18n.ui_str('zh', 'canonical')
    en = i18n.ui_str('en', 'canonical')
    # lastmod 取数据文件最后一次提交的日期。
    # 不能用文件 mtime：CI 每次检出都会把 mtime 更新为当天，
    # 生成结果就会与仓库内容不一致，导致比对步骤失败。
    def last_commit_date(rel):
        try:
            out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', rel],
                                 cwd=ROOT, capture_output=True, text=True, timeout=10)
            d = out.stdout.strip()
            if len(d) == 10 and d[4] == '-':
                return d
        except Exception:
            pass
        return datetime.date.today().isoformat()

    lastmod = last_commit_date('data/buddhism.json')

    alt = ('    <xhtml:link rel="alternate" hreflang="zh-Hans" href="%s"/>\n'
           '    <xhtml:link rel="alternate" hreflang="en" href="%s"/>\n'
           '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n' % (esc(zh), esc(en), esc(zh)))

    entries = []
    for loc, prio in ((zh, '1.0'), (en, '0.9')):
        entries.append(
            '  <url>\n'
            '    <loc>%s</loc>\n'
            '    <lastmod>%s</lastmod>\n'
            '    <changefreq>monthly</changefreq>\n'
            '    <priority>%s</priority>\n'
            '%s'
            '  </url>\n' % (esc(loc), lastmod, prio, alt))

    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<!-- 佛教基础理论结构树 / Buddhist Doctrines · A Structured Reference\n'
               '     两版页面同源，互以 hreflang 声明语言关系。由 build/make_seo_files.py 生成。 -->\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
               '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
               + ''.join(entries) +
               '</urlset>\n')
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(sitemap)

    # 站点根 + 仓库路径，例如 https://linlei1980.github.io/buddhist-doctrine-tree/
    site_root = '/'.join(zh.split('/')[:4]) + '/'
    site_url = zh.rsplit('/', 1)[0] + '/'
    assert site_root.count('/') == 4, '站点根解析异常：%s' % site_root
    assert site_url != '/', '站点地址解析异常'
    robots = ('# 佛教基础理论结构树 / Buddhist Doctrines · A Structured Reference\n'
              'User-agent: *\n'
              'Allow: /\n\n'
              'Sitemap: %ssitemap.xml\n' % site_url)
    open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write(robots)

    if '/buddhist-doctrine-tree/' not in sitemap or 'Sitemap: %ssitemap.xml' % site_url not in robots:
        raise SystemExit('生成结果中的 URL 不正确，请检查 ui.json 的 canonical')
    print('已生成 sitemap.xml（%s，2 个 URL）与 robots.txt' % lastmod)
    print('  站点地图:', zh.replace('index.html', '') + 'sitemap.xml')
    print('  抓取规则中的 Sitemap 行:', robots.strip().splitlines()[-1])

if __name__ == '__main__':
    main()
