# -*- coding: utf-8 -*-
"""双语渲染：读 data/buddhism.json，产出中文版 index.html 与英文版 en.html。

中文页直接用中文数据；英文页在数据层做一次英译替换（节点名、释义、出处、年代、
关系说明），并把界面文字换成英文。两个语言共用同一套渲染代码。
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import i18n
import seg

DATA = json.load(open(os.path.join(ROOT, 'data', 'buddhism.json'), encoding='utf-8'))

LANGS = {
    'zh': dict(file='index.html', dst='佛教基础理论结构树-v2.html'),
    'en': dict(file='en.html', dst='en.html'),
}

# 注入前端的界面文字键（对应 ui.json 的 lang.<lang> 字段）
UI_KEYS = [
    'searchPlaceholder', 'tabTree', 'tabTimeline', 'tabPath', 'tabWelcome', 'tabDocs', 'tabNode',
    'toolsExpand', 'toolsCollapse', 'relHint', 'tlKeyOnly', 'tlAll', 'tlHint', 'pathHint',
    'back', 'guideSummary', 'noMatch', 'seeAlsoPrefix', 'eraPosPrefix', 'ttkAbout',
    'secMeaning', 'secTime', 'secSource', 'secRelated', 'badgeSrc', 'badgeRel', 'epLabel',
    'docNoDating', 'unitLayers', 'unitPeriods',
]

def build_ui(lang):
    """构造注入前端的界面文字对象；match 用 {n} 占位符"""
    u = {k: i18n.ui_str(lang, k) for k in UI_KEYS if i18n.ui_str(lang, k)}
    u['match'] = i18n.ui_str(lang, 'matchPrefix')
    for k in ('form', 'fix', 'trans'):
        u['ttk_' + k] = i18n.ui_str(lang, 'ttk' + k.capitalize())
    return u

# ---------------------------------------------------------------- 英文数据层
LAYER_TITLES_EN = {
    '01 问题层 · 四圣谛': '01 The Problem · Four Noble Truths',
    '02 标准层 · 三法印': '02 The Criterion · Three Seals',
    '03 原理层 · 缘起 · 业果 · 法论': '03 The Principle · Origination, Karma, Dharmas',
    '04 论书层 · 部派与阿毗达磨': '04 Scholasticism · Nikāyas and Abhidharma',
    '05 大乘层 · 中观 · 唯识 · 因明': '05 Mahāyāna · Madhyamaka, Yogācāra, Logic',
    '06 层次层 · 二谛 · 三性': '06 Levels of Truth · Two Truths, Three Natures',
    '07 主体层 · 无我': '07 The Subject · Non-self',
    '08 依据层 · 如来藏 · 佛性': '08 The Ground · Tathāgatagarbha, Buddha-nature',
    '09 体系层 · 判教': '09 The System · Doctrinal Classification',
    '10 汉传十宗': '10 The Chinese Schools',
    '11 修行实践': '11 Practice',
    '12 历史层积 · 传播': '12 Textual Layers · Transmission',
}
LAYER_EPOCH_EN = {
    '约前 5 世纪': 'c. 5th century BCE',
    '内容见阿含，名称定型约前 2—前 1 世纪': 'content in the Āgamas; the name fixed c. 2nd–1st century BCE',
    '约前 5—前 3 世纪': 'c. 5th–3rd century BCE',
    '约前 3—公元 5 世纪': 'c. 3rd century BCE – 5th century CE',
    '约 1—7 世纪': 'c. 1st–7th century CE',
    '约 1—5 世纪': 'c. 1st–5th century CE',
    '约前 5 世纪—5 世纪': 'c. 5th century BCE – 5th century CE',
    '约 3—5 世纪': 'c. 3rd–5th century CE',
    '约 4—8 世纪': 'c. 4th–8th century CE',
    '约 5—9 世纪': 'c. 5th–9th century CE',
    '贯穿全体系': 'running through the whole system',
    '方法论与流传史': 'method and transmission history',
}
# 少数文献的英文题名需手工指定（其出处条目用的是巴利名或经号，反查不到）
DOC_NAME_EN = {
    '大四十经': '*Mahācattārīsaka Sutta* (Majjhima Nikāya 117)',
    '沙门果经': '*Sāmaññaphala Sutta* (Dīgha Nikāya 2)',
    '大品般若经': '*Pañcaviṃśatisāhasrikā Prajñāpāramitā*',
    '大因缘经': '*Mahānidāna Sutta* (Dīgha Nikāya 15)',
    '有明小经': '*Cūḷavedalla Sutta* (Majjhima Nikāya 44)',
    '大史': '*Mahāvaṃsa*',
}

DOC_GROUP_EN = {
    '经藏 · 主要经典': 'Sūtra · principal scriptures',
    '律藏 · 戒律与僧事': 'Vinaya · precepts and monastic procedure',
    '论疏 · 论书与注疏': 'Treatise and commentary',
    '史料 · 史传、目录与法敕': 'Historical source',
    '其他引用文献': 'Other cited texts',
}

def translate_data(lang):
    """返回该语言下用于渲染的节点数据"""
    if lang == 'zh':
        return DATA['nodes']
    # 中文标题 → 规范英文题名 的反查表
    zh2en = i18n.sources()
    # 兜底索引：凡出处标题的英文译文中含此中文题名者，取其形式
    _loose = {}
    for _zh, _en in zh2en.items():
        m = re.search(r'《([^》]+)》', _zh)
        if m:
            _loose.setdefault(m.group(1), _en)
    DOC_CN = {d['id']: d['name'] for d in DATA.get('docs', []) if d.get('id')}
    tr, miss = {}, []
    _doc_later = {}
    for k, v in DATA['nodes'].items():
        if k.startswith('doc_'):
            # 文献节点：题名取规范英文书名，说明按类别生成（与中文版同构）
            cn = v['n']
            if cn.startswith('文献 · '):
                cn = cn[len('文献 · '):]
            en_name = (DOC_NAME_EN.get(cn) or zh2en.get('《%s》' % cn) or zh2en.get(cn)
                       or _loose.get(cn) or i18n.source('《%s》' % cn, default=cn))
            later = [e['t'] for e in DATA['edges'] if e['s'] == k][:14]
            if '律' in cn or '毗尼' in cn or '毗奈耶' in cn or '清规' in cn:
                kind = 'a vinaya work (monastic precepts and procedure)'
            elif '论' in cn or '疏' in cn or '义' in cn or '记' in cn or '钞' in cn or '止观' in cn:
                kind = 'a treatise or commentary — to be dated separately from the scriptures'
            elif any(x in cn for x in ('史', '传', '录', '目录', '法敕', '记集')):
                kind = 'a historical source (chronicle, catalogue, inscription or edict)'
            else:
                kind = 'a scripture (the Buddha’s teaching, including the early Nikāyas and the Chinese Āgamas)'
            tr[k] = dict(v)
            tr[k]['n'] = en_name
            tr[k]['d'] = ('**Category**　%s.\n\n**Cited here**　%d nodes cite this text; the most relevant '
                          'are listed under “Related nodes” below.\n\nThis entry does not reproduce the '
                          'text; it records the text\'s place in the system. Every citation in those nodes '
                          'carries the quoted passage.' % (kind, len(later)))
            tr[k]['aka'] = [en_name.lower()]
            _doc_later[k] = later
            tr[k]['src'] = [dict(t='Nodes citing this text', q='',
                                 tag=v['src'][0]['tag'] if v.get('src') else '文献',
                                 color=v['src'][0]['color'] if v.get('src') else '#8A94A6')]
            continue
        t = i18n.node(k)
        if not t:
            miss.append(k)
            tr[k] = dict(v)
            continue
        src = []
        for idx, s in enumerate(v['src']):
            e = (t.get('src') or [])[idx] if idx < len(t.get('src') or []) else {}
            src.append(dict(t=e.get('t') or s['t'], q=e.get('q') or s['q'],
                            tag=s['tag'], color=s['color']))
        tt = {}
        for kk, vv in v['tt'].items():
            tt[kk] = (t.get('tt') or {}).get(kk) or vv
        tr[k] = dict(v)
        tr[k]['n'] = t.get('name') or v['n']
        tr[k]['d'] = t.get('desc') or v['d']
        tr[k]['src'] = src
        tr[k]['tt'] = tt
        if t.get('aka'):
            tr[k]['aka'] = t['aka']
    if miss:
        print(f'!! 英文译文缺失 {len(miss)} 个节点：{miss[:12]}{" …" if len(miss) > 12 else ""}')
    # 文献节点的引文需用英文名，故在其余节点译完后回填
    for k, later in _doc_later.items():
        tr[k]['src'][0]['q'] = '; '.join(tr[i]['n'] for i in later if i in tr)
    return tr

def tree_for(lang):
    """目录树：英文版换层名、层期与备注"""
    T = json.loads(json.dumps(DATA['tree'], ensure_ascii=False))
    if lang == 'zh':
        return T
    for L in T:
        L['title'] = LAYER_TITLES_EN.get(L['title'], L['title'])
        L['epoch'] = LAYER_EPOCH_EN.get(L['epoch'], L['epoch'])
        for it in L['items']:
            note = it.get('note')
            if note:
                if '见「05 大乘层」' in note:
                    it['note'] = 'three natures · eight consciousnesses · transformation into wisdom · four wisdoms — see layer 05'
                elif note == '第一支':
                    it['note'] = '1st link'
                elif note == '第八支':
                    it['note'] = '8th link'
                elif re.fullmatch(r'\d+ 种', note):
                    it['note'] = note.replace('种', ' texts')
                else:
                    parts = note.split(' · ')
                    head = DOC_GROUP_EN.get(parts[0], parts[0])
                    it['note'] = ' · '.join([head] + [p.replace('种', ' texts') for p in parts[1:]])
        # 文献分组标题
    def fix_group(items):
        for it in items:
            if it['id'].startswith('docgroup_'):
                it['name'] = it.get('note', '')
            fix_group(it.get('children', []))
    for L in T:
        fix_group(L['items'])
    return T

def rels_for(lang):
    if lang == 'zh':
        return {k: dict(name=k, color=v['color'], hint=v['hint']) for k, v in DATA['rels'].items()}
    return {k: dict(name=i18n.ui()['relations'][k]['en'], color=v['color'],
                    hint=i18n.ui()['relations'][k]['hint']) for k, v in DATA['rels'].items()}

def cats_for(lang):
    if lang == 'zh':
        return {k: dict(name=v['name'], color=v['color']) for k, v in DATA['cats'].items()}
    return {k: dict(name=i18n.ui()['categories'][k]['en'], color=v['color'])
            for k, v in DATA['cats'].items()}

def epochs_for(lang):
    if lang == 'zh':
        return {k: dict(name=v['name'], color=v['color'], hint=v['hint']) for k, v in DATA['epochs'].items()}
    return {k: dict(name=i18n.ui()['epochs'][k]['en'], color=v['color'],
                    hint=i18n.ui()['epochs'][k]['hint']) for k, v in DATA['epochs'].items()}

ERA_LABELS_EN = {
    '前6-5': 'c. 6th–5th century BCE', '前4-3': 'c. 4th–3rd century BCE',
    '前3-1': 'c. 3rd–1st century BCE', '1-2': 'c. 1st–2nd century CE',
    '3-5': 'c. 3rd–5th century CE', '4-7': 'c. 4th–7th century CE',
    '8-12': 'c. 8th–12th century CE', '13-20': '13th century onwards',
    '15-20': 'modern period', '11-15': 'c. 11th–15th century',
}
ERA_HINTS_EN = {
    '前6-5': 'the Buddha and the earliest teaching',
    '前4-3': 'parinirvāṇa, the councils, the first schisms',
    '前3-1': 'Abhidharma, scholastic debate, the Pali canon written down',
    '1-2': 'early Mahāyāna: the perfection of wisdom, Pure Land, Nāgārjuna',
    '3-5': 'Yogācāra, tathāgatagarbha, Buddhist logic',
    '4-7': 'translation, doctrinal classification and schools in China',
    '8-12': 'tantra, the Tibetan transmissions, the division of Chan',
    '13-20': 'after the persecutions, systematisation in Tibet, modern transition',
}

def eras_for(lang):
    if lang == 'zh':
        return DATA['eras']
    return [dict(id=e['id'], label=ERA_LABELS_EN.get(e['id'], e['label']),
                 hint=ERA_HINTS_EN.get(e['id'], e['hint'])) for e in DATA['eras']]

# ---------------------------------------------------------------- 界面文字注入
PLACEHOLDERS = [
    ('__DATA__', lambda lang: json.dumps(lang_data(lang), ensure_ascii=False)),
    ('__UI__', lambda lang: json.dumps(build_ui(lang), ensure_ascii=False)),
    ('__DOCS__', lambda lang: json.dumps(
        [dict(name=(i18n.node(d['id'], 'name') or d['name']) if d.get('id') else d['name'],
              ids=d['ids'], n=d['n'], kind=d['kind'], cat=d['cat'],
              id=d.get('id'))
         for d in DATA.get('docs', [])], ensure_ascii=False)),
    ('{{searchPlaceholder}}', lambda lang: i18n.ui_str(lang, 'searchPlaceholder')),
    ('{{tabTree}}', lambda lang: i18n.ui_str(lang, 'tabTree')),
    ('{{tabTimeline}}', lambda lang: i18n.ui_str(lang, 'tabTimeline')),
    ('{{tabPath}}', lambda lang: i18n.ui_str(lang, 'tabPath')),
    ('{{pathCount}}', lambda lang: '4' if lang == 'zh' else 'four'),
    ('{{tabWelcome}}', lambda lang: i18n.ui_str(lang, 'tabWelcome')),
    ('{{tabDocs}}', lambda lang: i18n.ui_str(lang, 'tabDocs')),
    ('{{tabNode}}', lambda lang: i18n.ui_str(lang, 'tabNode')),
    ('{{toolsExpand}}', lambda lang: i18n.ui_str(lang, 'toolsExpand')),
    ('{{toolsCollapse}}', lambda lang: i18n.ui_str(lang, 'toolsCollapse')),
    ('{{relHint}}', lambda lang: i18n.ui_str(lang, 'relHint')),
    ('{{tlKeyOnly}}', lambda lang: i18n.ui_str(lang, 'tlKeyOnly')),
    ('{{tlAll}}', lambda lang: i18n.ui_str(lang, 'tlAll')),
    ('{{tlHint}}', lambda lang: i18n.ui_str(lang, 'tlHint')),
    ('{{pathHint}}', lambda lang: i18n.ui_str(lang, 'pathHint')),
    ('{{back}}', lambda lang: i18n.ui_str(lang, 'back')),
    ('{{guideSummary}}', lambda lang: i18n.ui_str(lang, 'guideSummary')),
    ('{{searchInfo}}', lambda lang: ''),
]

# 中文名（检索用）
_zh_compact = {}

def _init_zh_compact():
    for k, v in DATA['nodes'].items():
        _zh_compact[k] = v['n']

def cross_terms(lang):
    """另一语言的检索词：使中文页可搜英文、英文页可搜中文。

    只收录名称、梵巴原语与别名，不含释义正文（避免体积翻倍）；释义本身
    在本语言页面内已可检索。带变音符的梵文同时收录去音符写法。
    """
    import unicodedata
    def plain(t):
        return ''.join(c for c in unicodedata.normalize('NFD', t)
                       if unicodedata.category(c) != 'Mn')
    out = {}
    for k, v in DATA['nodes'].items():
        terms = []
        if lang == 'zh':
            t = i18n.node(k)
            if t:
                terms.append(t.get('name', ''))
                terms += t.get('aka', [])[:6]
            if v.get('en') and v['en'] != '—':
                terms.append(v['en'])
        else:
            terms.append(v['n'])
            terms.append(_zh_compact.get(k, ''))
            if v.get('en') and v['en'] != '—':
                terms.append(v['en'])
        terms = [x for x in dict.fromkeys(x.strip().lower() for x in terms if x and x.strip())]
        extra = [plain(x) for x in terms if plain(x) != x]
        keys = terms + extra
        if keys:
            out[k] = ' '.join(keys)
    return out

_init_zh_compact()

def lang_data(lang):
    """注入前端的数据对象"""
    return dict(
        nodes=translate_data(lang), tree=tree_for(lang), edges=DATA['edges'],
        rels=rels_for(lang), cats=cats_for(lang), epochs=epochs_for(lang),
        eras=eras_for(lang), ttk={k: i18n.ui_str(lang, 'ttk' + k.capitalize())
                                  for k in ('form', 'fix', 'trans')},
        xsearch=cross_terms(lang),
    )

def _apply(text, lang):
    for key, fn in PLACEHOLDERS:
        text = text.replace(key, fn(lang))
    return text

# ---------------------------------------------------------------- 页面组装
def chain_html(lang):
    if lang == 'zh':
        nodes, arrows = seg.CHAIN_NODES, seg.CHAIN_ARROWS
    else:
        st = i18n.static()
        nodes = [(n, sub, color) for n, sub, color in st['chainNodes']]
        arrows = st['chainArrows']
    out, num = [], 0
    for i, (name, sub, color) in enumerate(nodes):
        if i == 7:
            out.append('<div class="chain-break"></div>')
            label = '贯穿视角' if lang == 'zh' else i18n.static()['chainSide']
            out.append('<div class="chain-side">%s</div>' % label)
        num += 1
        out.append('<div class="cstep"><span class="cn" style="background:%s">%02d</span>'
                   '<span class="ct">%s<em>%s</em></span></div>' % (color, num, name, sub))
        lb = arrows[i]
        if lb is not None:
            out.append('<div class="car"><span class="ar">→</span><span class="lb">%s</span></div>' % lb)
    return ''.join(out)

def guide_html(lang):
    if lang == 'zh':
        rev, use, gloss = seg.GUIDE_REV, seg.GUIDE_USE, seg.GUIDE_GLOSS
    else:
        st = i18n.static()
        rev, use, gloss = st['guideRev'], st['guideUse'], st['guideGloss']
        rev = '<details open><summary>%s</summary><div class="gb">%s</div></details>' % (
            st['guideRevSummary'], rev)
        use = '<details><summary>%s</summary><div class="gb">%s</div></details>' % (
            st['guideUseSummary'], use)
        gloss = '<details><summary>%s</summary><div class="gb">%s</div></details>' % (
            st['guideGlossSummary'], gloss)
        return rev + use + gloss
    rows = ''.join(
        '<tr><td><span class="tagline" style="color:%s">%s</span></td><td>%s</td><td>%s</td></tr>'
        % (v['color'], k, v['hint'][:0] or hint, ex)
        for (k, hint, ex), v in zip(
            [(k, DATA['rels'][k]['hint'], ex) for k, ex in [
                ('支分', '四圣谛 ← 苦谛/集谛/灭谛/道谛'), ('次第', '三皈依 → 五戒'),
                ('因果', '十二因缘 → 六道轮回'), ('体同', '涅槃寂静 ＝ 择灭无为'),
                ('判摄', '如来藏 → 密宗判为依据'), ('对辨', '说一切有部 ↔ 经量部'),
                ('修证', '四念处 → 三十七道品'), ('层积', '早期层 → 发展层'),
                ('依据', '阿赖耶识 依《解深密经》'), ('说明', '三法印 由 四圣谛 判定')]],
            [DATA['rels'][k] for k in ['支分', '次第', '因果', '体同', '判摄', '对辨', '修证', '层积', '依据', '说明']]))
    gloss = gloss.replace('__GLOSSROWS__', rows)
    return rev + use + gloss

def welcome_html(lang, meta_zh=''):
    if lang == 'zh':
        h2 = '体系总览'
        p1 = ('本页将佛教基础理论组织为<strong>十二层</strong>与一条<strong>由问题到体系</strong>的主线。'
              '主线九项依次为：四圣谛、三法印、缘起 · 业果、部派 · 阿毗达磨、中观 · 唯识、如来藏、判教 · 十宗，'
              '另设修行实践与历史 · 传播两层；后两层不在主线上，而是贯穿全页的两个视角——'
              '前者为教理在行持上的落实，后者为文本与宗派在历史上的形成过程。')
        p2 = ('主线各环之间为承接关系：四圣谛确定问题所在，三法印给出判定教说的标准，缘起 · 业果展开其原理，'
              '部派佛教将原理整理为论书体系，大乘由此开出中观与唯识两大轨道，如来藏为「何故能成佛」补足依据，'
              '判教与十宗则把上述内容组织为宗派的体系。')
        p3 = ('左栏三个视图：<b>目录</b>为十二层结构树，可按关系类型筛选；<b>年表</b>按九个时段排列，'
              '用于检视发展线索；<b>学习路径</b>提供四条自基础至实践的读法。右侧两个标签页：'
              '<b>总览</b>（本条及其下的修订说明、阅读路径与关系类型）与<b>经律论总览</b>（148 种文献的检索表）。')
        meta = meta_zh
    else:
        st = i18n.static(), 
        st = i18n.static()
        w = st['welcome']
        h2, p1, p2, p3, meta = w['h2'], w['p1'], w['p2'], w['p3'], st['metaNote']
    return ('<div class="welcome">\n  <h2>%s</h2>\n  <p>%s</p>\n  <p>%s</p>\n'
            '  <div class="chain">%s</div>\n  <p style="margin-top:12px">%s</p>\n'
            '  <div class="guide">%s</div>\n'
            '  <div class="meta-note" id="metaNote">%s</div>\n</div>'
            % (h2, p1, p2, chain_html(lang), p3, guide_html(lang), meta))

# ---------------------------------------------------------------- <head>（含 SEO）
def head_html(lang):
    """生成 head：标题、描述、关键词、canonical、hreflang 与 OG。"""
    u = lambda k: i18n.ui_str(lang, k)
    esc = lambda t: (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                     .replace('"', '&quot;'))
    title, desc, kw = u('title'), u('metaDesc'), u('metaKeywords')
    canon, alt = u('canonical'), i18n.ui_str('en' if lang == 'zh' else 'zh', 'canonical')
    return ('<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>%s</title>\n'
            '<meta name="description" content="%s">\n'
            '<meta name="keywords" content="%s">\n'
            '<link rel="canonical" href="%s">\n'
            '<link rel="alternate" hreflang="zh-Hans" href="%s">\n'
            '<link rel="alternate" hreflang="en" href="%s">\n'
            '<link rel="alternate" hreflang="x-default" href="%s">\n'
            '<meta property="og:type" content="article">\n'
            '<meta property="og:site_name" content="%s">\n'
            '<meta property="og:title" content="%s">\n'
            '<meta property="og:description" content="%s">\n'
            '<meta property="og:url" content="%s">\n'
            '<meta property="og:locale" content="%s">\n'
            '<meta property="og:locale:alternate" content="%s">\n'
            '<meta name="twitter:card" content="summary">\n'
            '<meta name="twitter:title" content="%s">\n'
            '<meta name="twitter:description" content="%s">\n'
            '<script type="application/ld+json">%s</script>\n'
            '</head>\n'
            % (esc(title), esc(desc), esc(kw), esc(canon),
               i18n.ui_str('zh', 'canonical'), i18n.ui_str('en', 'canonical'),
               i18n.ui_str('zh', 'canonical'), esc(u('siteName')), esc(title), esc(desc),
               esc(canon), u('ogLocale'), u('ogLocaleAlt'), esc(title), esc(desc),
               json.dumps(ldjson(lang), ensure_ascii=False)))

def ldjson(lang):
    """结构化数据：说明这是什么、面向谁、以何语言呈现。"""
    u = lambda k: i18n.ui_str(lang, k)
    return {
        '@context': 'https://schema.org',
        '@type': 'LearningResource',
        'name': u('title'),
        'description': u('metaDesc'),
        'url': u('canonical'),
        'inLanguage': 'zh-Hans' if lang == 'zh' else 'en',
        'learningResourceType': 'Reference work',
        'educationalLevel': 'Beginner to advanced',
        'about': [{'@type': 'Thing', 'name': x} for x in
                  (['佛教', '佛学', '四圣谛', '缘起', '无我', '中观', '唯识', '如来藏', '判教',
                    '汉传佛教', '藏传佛教', '南传佛教'] if lang == 'zh' else
                   ['Buddhism', 'Buddhist doctrine', 'Four Noble Truths', 'dependent origination',
                    'non-self', 'Madhyamaka', 'Yogācāra', 'tathāgatagarbha',
                    'doctrinal classification', 'Chinese Buddhism', 'Tibetan Buddhism',
                    'Theravāda'])],
        'isAccessibleForFree': True,
        'license': 'https://creativecommons.org/licenses/by/4.0/',
        'author': {'@type': 'Person', 'name': 'Lin Lei'},
        'keywords': u('metaKeywords'),
        'hasPart': {'@type': 'WebPage', 'url': i18n.ui_str('en' if lang == 'zh' else 'zh', 'canonical'),
                    'inLanguage': 'en' if lang == 'zh' else 'zh-Hans'},
    }

# ---------------------------------------------------------------- 整页生成
def header_html(lang):
    u = lambda k: i18n.ui_str(lang, k)
    stats = ('<span><span class="k">%s</span> <b id="stN">—</b></span>\n'
             '    <span><span class="k">%s</span> <b id="stE">—</b>%s</span>\n'
             '    <span><span class="k">%s</span> <b id="stS">—</b>%s</span>\n'
             '    <span><span class="k">%s</span> <b id="stT">—</b>%s</span>\n'
             '    <span class="k">%s</span>')
    if lang == 'zh':
        return stats % ('节点', '关系', '（规范为 10 类）', '出处引证', ' 条', '年表时段', ' 段',
                        '检索范围：名称 / 梵巴原语 / 释义 / 所引经论名（可输《俱舍论》或《中论》试）')
    return stats % ('nodes', 'relations', '(reduced to 10 types)', 'citations', '', 'periods', '',
                    'Search covers names, Indic terms, definitions and the titles of cited texts '
                    '(try <i>Kośa</i> or <i>Madhyamakakārikā</i>)')

def render_page(lang, meta_zh=''):
    cfg = LANGS[lang]
    switcher = ('<a href="%s" style="text-decoration:none;color:var(--accent);'
                'border:1px solid var(--line);border-radius:12px;padding:2px 11px;font-size:11.5px">%s</a>'
                % (i18n.ui_str(lang, 'switchHref'), i18n.ui_str(lang, 'switchLabel')))
    page = seg.PAGE
    # 用生成好的 head 段替换模板里的 head
    i = page.index('<head'); j = page.index('</head>') + len('</head>')
    page = page[:i] + head_html(lang).rstrip('\n') + page[j:]
    page = page.replace('<html lang="zh-CN">', '<html lang="%s">' % i18n.ui_str(lang, 'htmlLang'), 1)
    page = page.replace('__CSS__', seg.CSS)
    page = page.replace('<span>十二层主线 + 部派阿毗达磨 + 印度大乘 + 汉传十宗 + 藏传南传　·　每个概念附释义、出处引文与年代考订</span>',
                        '<span>%s</span>' % i18n.ui_str(lang, 'pageSub'))
    # 标题行加语言切换
    page = page.replace('</h1>', ' ' + switcher + '</h1>')
    # 页头统计行整体替换
    start = page.index('<div class="sub">')
    end = page.index('</div>', start) + len('</div>')
    page = page[:start] + '<div class="sub">\n    ' + header_html(lang) + '\n  </div>' + page[end:]
    if '<h1>' in page:
        i = page.index('<h1>') + 4
        j = page.index('<span>', i)
        page = page[:i] + i18n.ui_str(lang, 'pageTitle') + ' ' + page[j:]
    page = page.replace('__WELCOME_INNER__', welcome_html(lang, meta_zh))
    # 搜索框与移动端返回、说明等占位符
    page = _apply(page, lang)
    # JS 也需替换占位符
    js = _apply(seg.JS, lang)
    page = page.replace('__JS__', js)
    return cfg['file'], page
