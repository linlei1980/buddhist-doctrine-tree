# -*- coding: utf-8 -*-
"""把原版内容与新增内容合并，生成新版单文件 HTML。"""
import json, re, os, sys, html, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import content_a, content_b, content_c, content_d

ORIG_HTML = os.path.join(ROOT, '佛教基础理论结构树.html')
OUT_HTML = os.path.join(ROOT, '佛教基础理论结构树-v2.html')
DATA_JSON = os.path.join(ROOT, 'data', 'buddhism.json')
DATA_JS = os.path.join(ROOT, 'data', 'buddhism.data.js')

# ============================================================
# 0. 配置
# ============================================================
CATS = {
 'core':   ('四圣谛',        '#C2410C'),
 'seal':   ('三法印',        '#7C3AED'),
 'origin': ('缘起 · 业果 · 法论', '#0369A1'),
 'indian': ('部派 · 阿毗达磨', '#1D4ED8'),
 'logic':  ('因明 · 量论',    '#0F766E'),
 'truth':  ('二谛 · 三性',    '#4338CA'),
 'nonself':('无我',          '#0E7490'),
 'garbha': ('如来藏 · 佛性',  '#BE185D'),
 'school': ('判教 · 宗派',    '#A21CAF'),
 'prac':   ('修行实践',       '#4D7C0F'),
 'debate': ('论诤',          '#B91C1C'),
 'canon':  ('经律论文献',     '#7C2D12'),
 'hist':   ('历史层积 · 传播','#57534E'),
}
EPOCHS = {
 'early':  ('早期层', '#15803D', '部派分裂前即已共传的核心教说，巴利尼柯耶与汉译阿含皆具'),
 'develop':('发展层', '#1D4ED8', '佛灭数百年间陆续成立：论书体系、大乘、判教、宗派组织'),
 'folk':   ('民间层', '#B45309', '承担民间宗教功能的部分，与理论层性质不同'),
 'modern': ('近世层', '#9333EA', '近现代的研究方法与实践形态，与前三个层积性质不同'),
 'meta':   ('元层积', '#57534E', '关于文本自身形成史的方法论与结论'),
}
# 关系类型：规范化后的十类
RELS = {
 '支分': ('#0369A1', '整体与部分：含、开为、分、支'),
 '次第': ('#0F766E', '先后相待：入门、前行、位次'),
 '因果': ('#B45309', '因与果：根源、感、导致、异熟'),
 '体同': ('#7C3AED', '异名同事：即、异名'),
 '判摄': ('#A21CAF', '宗派立场：判、宗义、立'),
 '对辨': ('#B91C1C', '两说对照：同源异说、互补角度'),
 '修证': ('#4D7C0F', '教理与行的对应：行门、观法、所依'),
 '层积': ('#57534E', '文本史的归属：层、可析出'),
 '依据': ('#4338CA', '经典与义理的所依'),
 '说明': ('#8A94A6', '解释、举例、补充'),
}
TTK = {'form': '思想形成', 'fix': '文献定型', 'trans': '汉译流传'}
# 年表时段
ERAS = [
 ('前6-5', '约前 6—前 5 世纪', '佛陀在世与最初的教说'),
 ('前4-3', '约前 4—前 3 世纪', '佛灭、结集与部派初分'),
 ('前3-1', '约前 3—前 1 世纪', '阿毗达磨成立、部派论诤、巴利三藏书写'),
 ('1-2',   '约 1—2 世纪',      '初期大乘：般若、净土、龙树与中观'),
 ('3-5',   '约 3—5 世纪',      '唯识、如来藏、因明的成立'),
 ('4-7',   '约 4—7 世纪',      '中国的译经、判教与立宗'),
 ('8-12',  '约 8—12 世纪',     '密续、藏传前弘与后弘、禅宗分派'),
 ('13-20', '13 世纪以后',      '近世：法难之后、藏传系统化、现代转型'),
 ('none',  '不限时代',         '方法论与贯穿性的条目'),
]
ERA_ORDER = [e[0] for e in ERAS]
REL_ORDER = list(RELS)

# ============================================================
# 1. 载入原版数据
# ============================================================
src = open(ORIG_HTML, encoding='utf-8').read()
orig_js = src[src.index('<script>'):]

def extract_const(js, name):
    m = re.search(r'^const\s+' + name + r'\s*=\s*', js, re.M)
    start = m.end(); open_ch = js[start]; close = {'{': '}', '[': ']'}[open_ch]
    depth = 0; j = start; instr = None; esc = False
    while j < len(js):
        c = js[j]
        if instr:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == instr: instr = None
        else:
            if c in '"\'': instr = c
            elif c == open_ch: depth += 1
            elif c == close:
                depth -= 1
                if depth == 0: return js[start:j + 1]
        j += 1

def parse_js_literal(raw):
    out = []; i = 0; n = len(raw)
    while i < n:
        c = raw[i]
        if c == '/' and i + 1 < n and raw[i + 1] == '/':
            while i < n and raw[i] != '\n': i += 1
            continue
        if c == '/' and i + 1 < n and raw[i + 1] == '*':
            i += 2
            while i + 1 < n and not (raw[i] == '*' and raw[i + 1] == '/'): i += 1
            i += 2; continue
        if c in '"\'':
            q = c; buf = ['"']; i += 1
            while i < n:
                ch = raw[i]
                if ch == '\\':
                    nxt = raw[i + 1]
                    if nxt == q: buf.append(q); i += 2; continue
                    buf.append('\\'); buf.append(nxt); i += 2; continue
                if ch == q: i += 1; break
                if ch == '"': buf.append('\\"')
                elif ch == '\n': buf.append('\\n')
                else: buf.append(ch)
                i += 1
            buf.append('"'); out.append(''.join(buf)); continue
        if c.isalpha() or c == '_':
            j = i
            while j < n and (raw[j].isalnum() or raw[j] == '_'): j += 1
            word = raw[i:j]; k = j
            while k < n and raw[k] in ' \t\n': k += 1
            if k < n and raw[k] == ':' and not (k + 1 < n and raw[k + 1] == ':'):
                out.append('"' + word + '"'); i = j; continue
            out.append(word); i = j; continue
        out.append(c); i += 1
    return json.loads(''.join(out))

orig_nodes = parse_js_literal(extract_const(orig_js, 'NODES'))
orig_edges = parse_js_literal(extract_const(orig_js, 'EDGES'))
WELCOME_HTML = re.search(r'<div class="welcome">.*?</div>\s*</main>', src, re.S).group(0)
WELCOME_HTML = WELCOME_HTML[:WELCOME_HTML.rindex('</div>')]
META_NOTE = orig_js[orig_js.index('<div class="meta-note">'):]
META_NOTE = META_NOTE[:META_NOTE.index('</div>')]

# ============================================================
# 2. 合并新增内容 + 年表时段标注 + 补全修订
# ============================================================
nodes = {}
for k, v in orig_nodes.items():
    node = dict(id=k, n=v['n'], en=v.get('en') or '—', c=v['c'], ep=v['ep'],
                d=v['d'], src=v.get('src') or [], tt=v.get('tt') or {})
    if v.get('see'): node['see'] = v['see']
    nodes[k] = node

for mod in (content_a, content_b, content_c, content_d):
    for k, v in mod.NODES.items():
        if k in nodes: raise SystemExit('重复的节点 id: ' + k)
        node = dict(id=k, **(dict(v)))
        node.setdefault('en', '—'); node.setdefault('src', []); node.setdefault('tt', {})
        node.setdefault('era', 'none')
        nodes[k] = node

# ---------- 原版 14 处出处与年代的校订（2026-09 中文校对 A1 组）----------
# 这些节点的初值来自原版，故必须在此覆盖（改 content_*.py 或 i18n/work/*.json 均无效：
# build.py 从中解析原版 HTML 取初值，英文题名另经 build/i18n/sources.json 查表）。
_CN = {
 # 四圣谛四定义：所引文句「苦圣谛者即是此…」「愁悲忧恼苦」等在全汉文大藏经零命中，
 # 系南传《相应部》56.11 的现代汉译被挂到汉译阿含名下（379 经全文只讲三转十二行相）
 'dukkha':    [('t',0,'《杂阿含经》卷15 第379经','《相应部》56.11《转法轮经》（南传汉译；汉译相应经文见安世高译《佛说转法轮经》）')],
 'samudaya':  [('t',0,'《杂阿含经》卷15 第379经','《相应部》56.11《转法轮经》（南传汉译）')],
 'nirodha':   [('t',0,'《杂阿含经》卷15 第379经','《相应部》56.11《转法轮经》（南传汉译）')],
 'marga':     [('t',0,'《杂阿含经》卷15 第379经','《相应部》56.11《转法轮经》（南传汉译；「二边」与「中道」段亦见安世高译《佛说转法轮经》）')],
 # 《大智度论》卷15 原文作「一切法无我印」，「无为法」为衍增
 'three_seals':[('q',3,'以一切有为生法无常印、一切[[unconditioned|无为法]]无我印、涅槃实相法印合称三种法印。',
                   '以一切有为生法无常印、一切法无我印、涅槃实法印合称三种法印。')],
 # 十善十恶的定型列举与邪见句：DN22 无 kammapatha、无 natthi dinnaṃ（见 MN117:5.2、AN10.176）
 'ten_paths': [('t',1,'《长部》22《大念处经》','《中部》117《大四十经》、《增支部》10.176（汉译见《杂阿含经》卷37 等）')],
 # 「一切」的定义：SN35.23 以十二处（六内处、六外处）说，非十八界
 'eighteen_dhatu':[('t',1,'《相应部》35','《相应部》35.23〈一切经〉（汉译《杂阿含经》卷13 第319经）'),
                   ('q',1,'「一切」以[[eighteen_dhatu|十八界]]说明。','「一切」以十二处（六内处、六外处）说明。')],
 # 异熟三义（异时/异类/变异）见《成唯识论述记》卷二，非《俱舍论》卷二
 'vipaka':    [('t',0,'《俱舍论》卷2','《成唯识论述记》卷二'),
               ('q',0,'「[[vipaka|异熟]]」三义（异时、异类、变异）的经典界说。','「[[vipaka|异熟]]」三义（异时而熟、异类而熟、变异而熟）的界说。')],
 # 《佛性论》〈如来藏品〉在卷二
 'suchness':  [('t',2,'《佛性论》卷一〈如来藏品〉','《佛性论》卷二〈如来藏品〉')],
 # 论书成立年与译出年口径不一，与他处统一为译出年
 'four_attractions':[('trans',None,'汉译以《大智度论》（约2—3世纪）与《瑜伽师地论》（646—648）为主',
                    '汉译以《大智度论》（鸠摩罗什译，402—405）与《瑜伽师地论》（玄奘译，646—648）为主')],
 # 「无我相经」之名与现存译本不合（义净译《佛说五蕴皆空经》）
 'five_aggregates':[('trans',None,'刘宋 求那跋陀罗译《杂阿含经》；唐 玄奘、义净另有《无我相经》汉译',
                    '刘宋 求那跋陀罗译《杂阿含经》；唐 义净另译《佛说五蕴皆空经》可参照')],
 # 三无为是有部论义，非「约前5世纪（涅槃作为非择灭）」
 'three_unconditioned':[('form',None,'约前5世纪（涅槃作为非择灭）','约3—5世纪（有部论义，《俱舍论》等）')],
}
for _nid, _edits in _CN.items():
    for _fld, _idx, _old, _new in _edits:
        if _fld == 'desc':
            nodes[_nid]['d'] = nodes[_nid]['d'].replace(_old, _new)
        elif _idx is None:                    # tt 三栏
            _tt = nodes[_nid]['tt']
            assert _tt.get(_fld) == _old, (_nid, _fld, _tt.get(_fld))
            _tt[_fld] = _new
        else:                                 # src[i].t / src[i].q
            _key = 't' if _fld == 't' else 'q'
            # 原文不含链接标记（[[id|文字]] 为后续自动添加），故比对前先去标记
            def _bare(x):
                x = re.sub(r'\[\[[a-z0-9_]+\|([^\]]*)\]\]', r'\1', x or '')
                return x.replace('**', '')
            # _src 是 src 的预处理副本，此处可能已生成，故两处都要改
            for _holder in [h for h in (nodes[_nid].get('_src'), nodes[_nid].get('src')) if h]:
                _s = _holder[_idx]
                if _bare(_s.get(_key)) == _bare(_new):
                    continue
                assert _bare(_s.get(_key)) == _bare(_old), (_nid, _idx, _key, _s.get(_key))
                _s[_key] = _new
# 字词：论书以「性戒」判定此三条（原版误作「属性戒」）
nodes['right_action']['d'] = nodes['right_action']['d'].replace('「属性戒」', '「性戒」')

# ---------- 两处译人归属的校订（均来自原版）----------
# 《不增不减经》原与《胜鬘经》并列为求那跋陀罗译，实为元魏 菩提流支译
# （《大正藏》T16 No.668 题记）。《成唯识论》原注「窥基糅译」，
# 该论题「三藏法师玄奘奉诏译」，系玄奘糅译十家释、窥基笔受，
# 与原版自身另两处「玄奘糅译十家释」的说法亦不一致。
nodes['garbha_sutras']['tt']['trans'] = nodes['garbha_sutras']['tt']['trans'].replace(
    '《胜鬘经》《不增不减经》（刘宋 求那跋陀罗，436）',
    '《胜鬘经》（刘宋 求那跋陀罗，436）；《不增不减经》（元魏 菩提流支）')
nodes['eight_consciousnesses']['tt']['trans'] = nodes['eight_consciousnesses']['tt']['trans'].replace(
    '《成唯识论》（659，窥基糅译）', '《成唯识论》（659，玄奘糅译十家释，窥基笔受）')

# ---------- 四法界一处出处的标注 ----------
# 原版把「澄观释：真空观即理法界……」列为《华严法界玄镜》的引文，但该句是概述而非论疏原文
# （同节点另一条「澄观《华严法界玄镜》卷一」才是逐字引文）。标注为内容概括，
# 以免读者以为它是引文。
for _s in nodes['four_dharmadhatu']['src']:
    if _s.get('t') == '《华严法界玄镜》':
        _s['t'] = '《华严法界玄镜》所述（内容概括，非直引）'

# ---------- 律宗「性戒／遮戒」的校订 ----------
# 原释义把「前四戒为性戒、不饮酒为遮戒」并列为分类标准，易被读成「性戒仅限此四条」。
# 性戒与遮戒的分判标准是「自体即恶」与「为防护而制」，性戒的范围大于五戒之前四条
# （凡自体即恶者皆是）。此处保留五戒的对应关系，但把分判标准写明。
nodes['vinaya']['d'] = nodes['vinaya']['d'].replace(
    '戒的分类（依《萨婆多毗尼毗婆沙》）：前四戒（不杀、不盗、不邪淫、不妄语）为「性戒」——本身即是罪；'
    '不饮酒为「遮戒」——为防止犯前四戒而制。',
    '戒的分类（依《萨婆多毗尼毗婆沙》等）：**性戒**指自体即恶、不待佛制者（杀、盗、邪淫、妄语等）；'
    '**遮戒**指自体非恶、为防护性戒而制者（如不饮酒）。五戒中前四戒属性戒，不饮酒属遮戒，'
    '但性戒的范围大于此四条。')

# ---------- 正命的校订 ----------
# 原释义把论书的「五种邪命」（出家众）与经中的「不应经营的行业」（在家众）
# 合成一个「五种」来讲，且后者无出处。此处分列两套，并补《增支部》5.177 一条引证。
nodes['right_livelihood']['d'] = (
    '以不损害众生的方式谋生。正命在戒学中的位置特殊：前七支正语、正业所约束的是「已作之事」，'
    '正命所约束的是「何以维生」——即把行为的规范前推到维持生活的整个方式。\n\n'
    '**邪命**（mithyā-ājīva）一词，南北两传所举不同，须分开看：\n\n'
    '- **出家众的五种邪命**——依《大智度论》卷19、《瑜伽师地论》：诈现奇特、自说功德、'
    '占相吉凶、高声现威、说得供养。五者同指一事：以出家人的身份换取利养。\n'
    '- **在家众不应经营的行业**——依《增支部》5.177 等：贩卖武器、贩卖人口、贩卖肉类、'
    '贩卖酒类、贩卖毒药。经中称此为「不应经营的行业」，不名为「邪命」——在家众不以'
    '「说法受供」为生，故论书的五种邪命对其并不适用。\n\n'
    '两套说法的共同点在**判准**而非条目：正命所问的不是「何者被禁止」，而是'
    '「此一营生是否以损害众生为条件而成立」。因此贩毒、贩人、贩武器之类被列为'
    '在家众的禁区，是因为其收益直接建立在众生的损害之上，而非因为行业本身「不洁」。\n\n'
    '正命把修行从内心的调伏扩展到社会生存方式，是戒学中最具社会性的一支，'
    '也是在家众所受诸戒中唯一直接约束其经济生活的一条。')

nodes['right_livelihood']['src'] = list(nodes['right_livelihood']['src']) + [
    dict(t='《增支部》5.177〈五不卖〉（汉译见《杂阿含经》「营生之业」相应经）',
         q='「具足五法之优婆塞不应经营五业：贩卖武器、贩卖人、贩卖肉、贩卖酒、贩卖毒。」'),
    dict(t='《俱舍论》卷25、《瑜伽师地论》卷22 等',
         q='以正命为「身口意三业之清净」，与正语、正业共属戒学所摄。'),
]
nodes['right_livelihood']['tt'] = dict(
    form='约前5世纪',
    fix='出家众五种邪命的分类定型于论书（约2—5世纪）；在家众五种不应经营的行业见《增支部》5.177 与汉译阿含')

# ---------- 三法印/四法印的校订 ----------
# 初版把「诸法无我」一条误题为「诸行是苦」，于是三法印的第二、三项重复，
# 四法印又缺「苦」这一支。现将该条内容交由「诸行是苦」，另立「诸法无我」，
# 使南传三相（无常/苦/无我）与汉传四法印（三相加涅槃寂静）各得其位。
nodes['impermanence']['n'] = '诸行无常'
nodes['nirvana']['n'] = '涅槃寂静'
nodes['nirvana']['aka'] = ['涅槃', '寂灭']

nodes['all_suffering'] = dict(
    n='诸行是苦', en='dukkha · sabbasaṅkhārā dukkhā', c='core', ep='early', era='前6-5',
    aka=['诸行是苦', '一切行苦', '诸受皆苦', '苦相'],
    d='凡依因缘而作者，皆不安稳、不可保任，故是苦。此处「行」（saṅkhāra）与「诸行无常」的「行」同指，'
      '即一切有为法，而非仅指感受。\n\n'
      '**三苦**是其标准的展开方式：\n\n'
      '- **苦苦**——苦受本身即苦（病、痛、忧恼）；\n'
      '- **坏苦**——乐受终将变坏，坏时即是苦（故乐受非苦之反面，而是苦之缓相）；\n'
      '- **行苦**——一切有为法念念迁流、为业惑所使而不自主，这是苦最根本的形态。\n\n'
      '因此「诸行是苦」不是情绪上的悲观判断，而是对「有为」这一存在方式的界定：'
      '**无常故苦**——正因刹那生灭、不能自主，才说一切行皆苦。此支与「诸行无常」'
      '「诸法[[anatta|无我]]」合为南传的**三相**（tilakkhaṇa），是上座部观智的所缘；'
      '汉传的[[four_seals|四法印]]则取此支入印，与无常、无我、涅槃寂静并列。\n\n'
      '义理上的次第为：无常故苦，苦故无我——三者不是三个并列的结论，'
      '而是同一观察的三个面向。',
    src=[
      dict(t='《增支部》3.136、《法句经》第278颂（三相的定型句式）',
           q='「诸行无常，诸行是苦，诸法无我。」——南传三相的标准表述。'),
      dict(t='《中部》10《念处经》、《长部》22《大念处经》', q='受念处中，观三受皆苦，及「观生灭」一段。'),
      dict(t='《俱舍论》卷22', q='以苦苦、坏苦、行苦统摄诸苦。'),
      dict(t='《清净道论》〈说慧品〉', q='以三相为观智所缘，十六观智依次展开。'),
    ],
    tt=dict(form='约前5世纪（三相之一）',
            fix='三苦的系统分类见《俱舍论》卷22（4—5世纪）；南传以三相为观智所缘，见《清净道论》（5世纪）'))

nodes['nonself_seal'] = dict(
    n='诸法无我', en='dharmā anātmānaḥ / anattā', c='seal', ep='early', era='前6-5',
    aka=['诸法无我', '法无我'],
    d=nodes['nonself_seal']['d'],
    src=nodes['nonself_seal']['src'], tt=nodes['nonself_seal']['tt'])


# 原节点年表时段标注
ERA_BY_ID = {
 '前6-5': ['three_realms','kalpa_cosmology','vinaya_rites','four_truths','dukkha','samudaya','nirodha','marga','eightfold','right_view','six_realms','ten_paths',
           'right_thought','right_speech','right_action','right_livelihood','right_effort',
           'right_mindfulness','right_samadhi','craving','ignorance','medical_logic',
           'impermanence','all_suffering','nonself_seal','nirvana','dependent_origination','twelve_links',
           'link_formation','link_consciousness','link_namarupa','link_sadayatana','link_contact',
           'link_feeling','link_clinging','link_becoming','link_birth','link_aging_death',
           'three_lives','delusion_karma_suffering','forward_reverse','karma','vipaka',
           'karma_types','karma_criteria','kusala_akusala','samsara','continuity','flame_analogy',
           'dharma_term','conditioned','five_aggregates','rupa','three_refuges','five_precepts',
           'three_trainings','sila','samadhi_training','prajna','four_foundations','four_dhyanas',
           'twelve_ayatana','eighteen_dhatu','anatta','pudgala','not_one_not_diff','three_doors',
           'thirty_seven_bodhipakkhiya','sravaka_fruits'],
 '前3-1': ['caitasika','suchness','three_seals','four_seals','unconditioned','three_unconditioned'],
 '4-7':   ['samatha_vipassana','four_reliances','six_unconditioned','two_truths','conventional','ultimate',
           'emptiness','three_natures','parikalpita','paratantra','parinispanna',
           'eight_consciousnesses','alaya','transformation','four_wisdoms','karma_ownership',
           'suffering_continues','tathagatagarbha','buddha_nature','pure_mind','garbha_sutras',
           'panjiao','sanlun','eight_negations','no_attainment','faxiang','tiantai',
           'one_mind_3000','three_truths_round','six_identities','kaifozhijian','huayan',
           'one_true_dharmadhatu','dharma_realm_origination','four_dharmadhatu','ten_gates',
           'six_aspects','three_bodies','chan','seeing_nature','wunian','pureland','faith_vow',
           'buddha_name','pure_land','vinaya','precepts','tantra','three_mysteries','abhisheka',
           'mandala','sokushin_jobutsu','four_immeasurables','four_attractions','bodhisattva_path',
           'six_paramitas','five_paths','buddha_body_land','three_vehicles_one_vehicle'],
 '8-12':  ['chan_methods'],
 'none':  ['historical_layers','early_layer','development_layer','folk_layer','minimal_skeleton',
           'canon_expansion'],
}
for era, ids in ERA_BY_ID.items():
    for i in ids:
        if i not in nodes:
            print('!! 未知 id（时段标注）:', i)
        nodes[i]['era'] = era

# 修订一处与全页年代口径不一致的表述
nodes['canon_expansion']['tt']['fix'] = ('结集的叙事定型于各部派史传（约前3世纪—公元5世纪）；'
                                         '「三次结集」为部派传统之说，南北两传的记载与年代均不一致')
nodes['canon_expansion']['d'] = nodes['canon_expansion']['d'].replace(
    '三次结集（约前5世纪、前4世纪、前3世纪）为经律论的成型关键节点',
    '结集为经律论的成型关键节点（南北两传对次数与年代的记载不一致，详见「三次结集」）')

STOP = ('卷', '品', '章', '经', '论', '疏', '记', '钞', '义', '部', '本', '译', '等',
        '后分', '前半', '后半', '相应', '诸经', '传入', '目录', '系统', '传承')

def norm_title(t):
    """把引用条目归一为一个文献名：去卷品号、去作者与数字"""
    t = re.sub(r'（[^）]*）', '', t)
    t = re.sub(r'^[^《]*?(?=《)', '', t)          # 去掉前置的作者或说明
    t = re.sub(r'[（(].*?[）)]', '', t)
    t = re.sub(r'卷?\s*\d+[-—~至]?\d*', '', t)
    t = re.sub(r'第\d+', '', t)
    t = re.sub(r'[·・]\s*[^·・》]{1,20}$', '', t)  # 去掉「·品名」「·章名」
    t = t.strip('　 、，,。·')
    return t

def doc_list():
    """把各节点出处中出现的文献归一，统计引用次数、类别与相关节点。"""
    docs = {}
    for k, v in nodes.items():
        for s in v['_src']:
            for name in re.findall(r'《([^》]+)》', s['t']):
                name = norm_title(name)
                if len(name) < 2 or name in STOP: continue
                if re.fullmatch(r'[\d\-—~、]+', name): continue
                d = docs.setdefault(name, dict(name=name, ids=[], kinds=set()))
                if k not in d['ids']: d['ids'].append(k)
                d['kinds'].add(s['tag'])
    out = []
    for name, d in docs.items():
        if not d['ids']: continue
        ids = sorted(d['ids'], key=lambda i: (ERA_ORDER.index(nodes[i]['era'])
                     if nodes[i]['era'] in ERA_ORDER else 99, -len(nodes[i]['_src'])))
        cats = collections.Counter(nodes[i]['c'] for i in d['ids'])
        out.append(dict(name=name, ids=ids, n=len(ids),
                        kind=('/'.join(sorted(d['kinds']))),
                        era=nodes[ids[0]]['era'],
                        cat=CATS[cats.most_common(1)[0][0]][0]))
    order = {'经': 0, '律': 1, '论疏': 2, '史料': 3, '文献': 4}
    out.sort(key=lambda d: (order.get(d['kind'].split('/')[0], 9), -d['n'], d['name']))
    return out

def mine_dating(name):
    """从该文献自己的出处条目里挖年代线索，挖不到就留空（不拿教义节点的年代冒充）。

    出处条的写法本身带年代信息，如「《俱舍论》卷1（界品）」所在节点会写
    「唐 玄奘译《俱舍论》（651—654）」；这类串是可靠的，故据此提取。
    """
    pat = re.compile(r'《' + re.escape(name) + r'》?[^；;。]{0,30}?[（(]\s*([^）)]{2,24})\s*[）)]')
    for k, v in nodes.items():
        for srcline in v.get('src', []):
            t = srcline['t']
            if name not in t: continue
            m = pat.search(t)
            if m and re.search(r'\d{3,4}|世纪|年', m.group(1)):
                return m.group(1)
    return ''

def make_doc_nodes():
    """为被引用最多的文献建立「文献节点」。

    只写三件事：文献的性质、本页的引用规模、以及引用了它的节点。
    文献自身的写成年代不在这里硬写——那要由讨论该文献的节点（04 论书层、
    12 历史 · 传播）给出，把某部论标成「约前5世纪」正是需要避免的错误。
    """
    kind_cn = {'经': '经（佛陀的教说，含早期尼柯耶与汉译阿含）',
               '律': '律（僧团戒律与僧事制度）',
               '论疏': '论疏（论书与注疏——判年代时必须与「经」分开看）',
               '史料': '史料（史传、目录、碑记与法敕）',
               '文献': '其他引用条目'}
    made = 0
    for d in DOCS:
        if d['n'] < 3:
            continue
        kinds = d['kind'].split('/')
        # 文献节点是附录，不贴层积徽章：用它最早被引用的那个节点的年代来标注文献本身，
        # 会把《俱舍论》（常被阿含类节点引用）误标为「早期层」。文献的年代另在
        # 「04 论书层」「12 历史 · 传播」里交代。
        ep = 'meta'
        bid = 'doc_' + str(len(DOC_IDS) + 1)
        DOC_IDS[d['name']] = bid
        d['id'] = bid
        for _i in d['ids']:
            DOC_IDS_INV.setdefault(bid, []).append(_i)
        trans = mine_dating(d['name'])
        name_list = '、'.join(nodes[i]['n'] for i in d['ids'][:14])
        nodes[bid] = dict(
            n='文献 · ' + d['name'], en='—', c='canon', ep=ep, era='none',
            aka=[d['name']],
            d='**类别**　' + kind_cn.get(kinds[0], kinds[0]) +
              ('（本页跨类引用：' + d['kind'] + '）' if len(kinds) > 1 else '') + '\n\n' +
              '**本页引用**　共 ' + str(d['n']) + ' 个节点引用此文献，最相关的十几个：' +
              name_list + ('…' if d['n'] > 14 else '') + '。\n\n' +
              '这一页不重复经文，只交代它在体系里的位置；要找它的内容，' +
              '请点开下方「关联节点」——每一处引用都附有原文引文。',
            src=[dict(t='本页引用此文献的节点',
                      q='；'.join(nodes[i]['n'] for i in d['ids'][:12]) +
                        ('……' if d['n'] > 12 else ''))],
            tt=dict(trans=trans) if trans else {})
        made += 1
    print('文献节点新建', made, '个')
    return made

DOC_IDS = {}

DOC_GROUP_NAME = {'经': '经藏 · 主要经典', '律': '律藏 · 戒律与僧事',
                  '论疏': '论疏 · 论书与注疏', '史料': '史料 · 史传、目录与法敕',
                  '文献': '其他引用文献'}

# ============================================================
# 3. 目录树
# ============================================================
def item(id, children=None, note=None):
    d = {'id': id}
    if children: d['children'] = children
    if note: d['note'] = note
    return d

TREE = json.loads(r"""
[
 {"title":"01 问题层 · 四圣谛","epoch":"约前 5 世纪","items":[
   {"id":"four_truths","children":[
     {"id":"dukkha"},{"id":"samudaya","children":[{"id":"craving"},{"id":"ignorance"}]},
     {"id":"nirodha"},{"id":"marga","children":[{"id":"eightfold","children":[
       {"id":"right_view"},{"id":"right_thought"},{"id":"right_speech"},{"id":"right_action"},
       {"id":"right_livelihood"},{"id":"right_effort"},{"id":"right_mindfulness"},{"id":"right_samadhi"}]}]},
     {"id":"medical_logic"}]}]},
 {"title":"02 标准层 · 三法印","epoch":"内容见阿含，名称定型约前 2—前 1 世纪","items":[
   {"id":"three_seals","children":[{"id":"impermanence"},{"id":"all_suffering"},{"id":"nonself_seal"},{"id":"nirvana"},{"id":"four_seals"}]}]},
 {"title":"03 原理层 · 缘起 · 业果 · 法论","epoch":"约前 5—前 3 世纪","items":[
   {"id":"dependent_origination","children":[
     {"id":"twelve_links","children":[
       {"id":"ignorance","note":"第一支"},{"id":"link_formation"},{"id":"link_consciousness"},
       {"id":"link_namarupa"},{"id":"link_sadayatana"},{"id":"link_contact"},{"id":"link_feeling"},
       {"id":"craving","note":"第八支"},{"id":"link_clinging"},{"id":"link_becoming"},
       {"id":"link_birth"},{"id":"link_aging_death"},{"id":"three_lives"},
       {"id":"delusion_karma_suffering"},{"id":"forward_reverse"}]},
     {"id":"karma","children":[{"id":"vipaka"},{"id":"karma_types"},{"id":"karma_criteria"},
       {"id":"kusala_akusala","children":[{"id":"ten_paths"}]}]},
     {"id":"samsara","children":[{"id":"six_realms"},{"id":"three_realms"},{"id":"kalpa_cosmology"},
       {"id":"continuity","children":[{"id":"flame_analogy"}]}]},
     {"id":"dharma_term","children":[
       {"id":"five_aggregates","children":[{"id":"rupa"}]},
       {"id":"conditioned","children":[{"id":"caitasika"}]},
       {"id":"unconditioned","children":[{"id":"three_unconditioned"},{"id":"six_unconditioned"},{"id":"suchness"}]}]}]}]},
 {"title":"04 论书层 · 部派与阿毗达磨","epoch":"约前 3—公元 5 世纪","items":[
   {"id":"councils"},{"id":"eighteen_schools"},{"id":"abhidharma"},
   {"id":"sarvastivada","children":[{"id":"six_causes_five_results"}]},
   {"id":"sautrantika"},{"id":"debate_pudgala"},{"id":"debate_atom"}]},
 {"title":"05 大乘层 · 中观 · 唯识 · 因明","epoch":"约 1—7 世纪","items":[
   {"id":"nagarjuna"},
   {"id":"madhyamaka","children":[{"id":"eight_negations"},{"id":"buddhapalita_bhaviveka"},
     {"id":"prajna_emptiness"},{"id":"no_attainment"}]},
   {"id":"yogacara","children":[{"id":"vijnapti_matra"},
     {"id":"eight_consciousnesses","children":[{"id":"alaya"}]},
     {"id":"transformation","children":[{"id":"four_wisdoms"}]}]},
   {"id":"hetuvidya"},{"id":"yogacara_vs_madhyamaka"},{"id":"debate_tathagatagarbha"}]},
 {"title":"06 层次层 · 二谛 · 三性","epoch":"约 1—5 世纪","items":[
   {"id":"two_truths","children":[{"id":"conventional"},{"id":"ultimate","children":[{"id":"emptiness"}]},{"id":"three_doors"}]},
   {"id":"three_natures","children":[{"id":"parikalpita"},{"id":"paratantra"},{"id":"parinispanna"}]},
   {"id":"debate_two_truths"}]},
 {"title":"07 主体层 · 无我","epoch":"约前 5 世纪—5 世纪","items":[
   {"id":"anatta","children":[{"id":"pudgala"},{"id":"not_one_not_diff"},{"id":"karma_ownership"},{"id":"suffering_continues"}]}]},
 {"title":"08 依据层 · 如来藏 · 佛性","epoch":"约 3—5 世纪","items":[
   {"id":"tathagatagarbha","children":[{"id":"buddha_nature"},{"id":"icchantika"},{"id":"pure_mind"},{"id":"garbha_sutras"}]}]},
 {"title":"09 体系层 · 判教","epoch":"约 4—8 世纪","items":[
   {"id":"panjiao","children":[{"id":"wushi_bajiao"},{"id":"wujiao_shizong"},{"id":"three_vehicles_one_vehicle"}]}]},
 {"title":"10 汉传十宗","epoch":"约 5—9 世纪","items":[
   {"id":"tiantai","children":[{"id":"one_mind_3000"},{"id":"three_truths_round"},{"id":"six_identities"},{"id":"kaifozhijian"}]},
   {"id":"huayan","children":[{"id":"one_true_dharmadhatu"},{"id":"dharma_realm_origination"},{"id":"four_dharmadhatu"},{"id":"ten_gates"},{"id":"six_aspects"}]},
   {"id":"sanlun","children":[{"id":"sizhong_erdi"}]},
   {"id":"faxiang","note":"三性 · 八识 · 转识成智 · 四智 见「05 大乘层」"},
   {"id":"chan","children":[{"id":"seeing_nature"},{"id":"wunian"},{"id":"chan_methods"},{"id":"five_houses_seven_schools"}]},
   {"id":"pureland","children":[{"id":"faith_vow"},{"id":"buddha_name"},{"id":"pure_land"},{"id":"two_paths_two_powers"}]},
   {"id":"vinaya","children":[{"id":"precepts"},{"id":"jie_ti"}]},
   {"id":"tantra","children":[{"id":"three_mysteries"},{"id":"abhisheka"},{"id":"mandala"},{"id":"sokushin_jobutsu"},{"id":"four_tantra_classes"},{"id":"tangmi_tibetan"}]},
   {"id":"jushe"},{"id":"chengshi"},{"id":"tibetan_schools"},{"id":"southern_tradition"}]},
 {"title":"11 修行实践","epoch":"贯穿全体系","items":[
   {"id":"three_refuges","children":[{"id":"five_precepts"}]},
   {"id":"three_trainings","children":[{"id":"sila"},{"id":"samadhi_training"},{"id":"prajna"}]},
   {"id":"four_foundations"},{"id":"thirty_seven_bodhipakkhiya"},{"id":"sravaka_fruits"},
   {"id":"samatha_vipassana"},{"id":"vinaya_rites"},
   {"id":"bodhisattva_path","children":[{"id":"six_paramitas"},{"id":"five_paths"}]},
   {"id":"four_immeasurables"},{"id":"four_attractions"},{"id":"four_dhyanas"},
   {"id":"twelve_ayatana"},{"id":"eighteen_dhatu"},
   {"id":"buddha_body_land","children":[{"id":"three_bodies"}]}]},
 {"title":"12 历史层积 · 传播","epoch":"方法论与流传史","items":[
   {"id":"historical_layers","children":[{"id":"early_layer"},{"id":"development_layer"},{"id":"folk_layer"},{"id":"minimal_skeleton"},{"id":"canon_expansion"}]},
   {"id":"four_reliances"},{"id":"mahayana_origins"},{"id":"ashoka"},
   {"id":"translation_history","children":[{"id":"yichang"}]},
   {"id":"tibetan_translation"},{"id":"huiChang_persecution"},{"id":"modern_studies"},
   {"id":"docbranch","note":"主要文献","children":[]}]}
]
""")

nodes['sizhong_erdi'] = dict(id='sizhong_erdi', n='四重二谛', en='—', c='school', ep='develop', era='4-7',
 aka=['四重二谛'],
 d='三论宗吉藏对二谛的逐层破斥，是「不立自宗」方法的具体操作。四重如下：\n\n1. 以「有」为俗谛、「空」为真谛；\n2. 以「有空」为俗谛、「非有非空」为真谛；\n3. 以「二（有空的二）不二」为俗谛、「非二非不二」为真谛；\n4. 以前三重皆为俗谛、「无所得」为真谛。\n\n**四重的用意**　每一重都把前一重的「真」转为下一重的「俗」——真谛不是一次到位的结论，而是逐层被超越的台阶。到第四重，「真谛」本身也成为须舍的方便，落点是「无所得」。\n\n这一手法与《中论》的遮诠一脉相承，但在中国被系统化为可操作的解释层次。**它同时说明三论宗为何不做判教**：判教要给诸经定高下，而四重二谛是要取消一切层级定位，二者在方法上互斥。',
 src=[dict(t='吉藏《二谛义》《大乘玄论》', q='四重二谛的逐层建立与「无所得」为极。'),
      dict(t='《中论》卷4〈观四谛品〉', q='二谛相待而立的经典根据。')],
 tt=dict(form='约2—3世纪（《中论》的二谛说）', fix='吉藏《二谛义》（6—7世纪）'))
nodes['sizhong_erdi']['see'] = ['two_truths', 'prajna_emptiness']


# ============================================================
# 3b. 出处分类与互链（5. 渲染 的前半）
# ============================================================
def classify_src(t):
    """出处条目标签：经 / 律 / 论疏 / 史料"""
    if any(k in t for k in ('律', '毗尼', '毗奈耶', '羯磨', '清规')):
        return ('律', PURPLE)
    if any(k in t for k in ('论', '疏', '记', '钞', '义', '玄义', '止观', '灯录', '传灯',
                            '集', '章', '玄镜', '门论', '正理门', '量论', '广论', '次第')):
        return ('论疏', GREY)
    if any(k in t for k in ('经', '尼柯耶', '阿含', '相应部', '中部', '长部', '增支部', '小诵',
                            '颂', '法句')):
        return ('经', TEAL)
    if any(k in t for k in ('法敕', '碑', '写本', '目录', '史', '录', '传', '目录集')):
        return ('史料', '#B45309')
    return ('文献', GREY)

TEAL, GREY, PURPLE = '#0F766E', '#8A94A6', '#7C3AED'

def build_src_index():
    """把 src 列表预处理为带标签与颜色的 _src（文献节点生成后需再跑一次）"""
    for _k, _v in nodes.items():
        _v.setdefault('aka', [])
        _v['_src'] = [dict(t=_s['t'], q=_s.get('q', ''), tag=classify_src(_s['t'])[0],
                           color=classify_src(_s['t'])[1]) for _s in _v.get('src', [])]

build_src_index()

# ============================================================
# 4. 关系规范化 + 新增关系
# ============================================================
REL_MAP = {
 '判为':'判摄','含':'支分','核心':'判摄','即':'体同','支':'支分','展开':'说明','印':'层积',
 '宗义':'判摄','开为':'支分','层':'层积','解释':'说明','依据':'依据','根源':'因果','分':'支分',
 '行门':'修证','基础':'依据','果':'因果','入门':'次第','判定':'说明','需解释':'说明','对映':'对辨',
 '组织':'说明','归摄':'支分','逻辑形式':'体同','开为四':'支分','诸受皆苦即苦谛':'体同','遍于':'支分',
 '即灭谛':'体同','即择灭无为':'体同','脱胎于三三昧':'层积','组织方式':'说明','两向':'说明','机制':'说明',
 '导致':'因果','即业':'体同','展开为八识':'说明','业的积聚':'说明','即性空':'体同','即依他起':'体同',
 '在伦理层面的展开':'说明','感':'因果','构成':'支分','分类':'说明','判':'判摄','判准':'说明',
 '境界':'修证','即相续，非实体搬迁':'体同','喻':'说明','含色法':'支分','含心所法':'支分','归类':'说明',
 '色蕴':'体同','互补的分析角度':'对辨','加六识成十八界':'说明','观处无我':'修证','观界无我':'修证',
 '有部立':'判摄','唯识立':'判摄','以真如为极':'判摄','异名':'体同','真如出缠即如来藏':'体同',
 '因果成立处':'依据','空即无我，无我即空':'体同','开为三':'支分','空门':'修证','由三性建立':'依据',
 '迷':'说明','缘起':'体同','悟':'说明','于其上妄执':'说明','于其上离执':'说明','依识而现':'依据',
 '第八':'体同','持种相续':'修证','转成':'因果','成三身':'因果','所依':'依据','以空性为前提':'依据',
 '客尘即遍计所执':'体同','实践展开':'修证','行':'体同','所见的性':'体同','菩提心之前行':'次第',
 '利他行':'修证','观五蕴':'修证','不坏假名':'说明','相续义':'体同','则':'说明','故':'说明',
 '无我故无证者，涅槃即苦灭':'说明','苦的止息':'体同','方法':'修证','究极':'判摄','立':'判摄',
 '三时判教':'判摄','位次':'次第','宗旨':'判摄','融摄':'判摄','四念处之发挥':'修证',
 '二谛开为三谛，三谛即二谛':'体同','即空即假即中':'体同','毗卢遮那':'体同','开为十玄门':'支分',
 '十玄门与六相圆融互释':'对辨','即缘起之华严式展开':'体同','不二':'体同','所见':'体同',
 '实践般若':'修证','无所得即禅宗无住':'体同','同源异说':'对辨','大乘':'判摄','戒学':'修证',
 '道谛':'体同','戒相':'支分','在家戒':'判摄','坛城':'修证','次第':'次第','如实知业果':'修证',
 '如实知空':'修证','法念处所观':'修证','可修至三禅四禅':'修证','菩提心前行':'次第','可析出':'层积',
 '现世涅槃':'判摄','起点':'层积','细节与图像化':'说明','报应故事':'说明','机械化倾向':'说明',
 '论疏与判教':'说明','戒律细节':'说明',
}

new_edges = []
unknown = set()
for e in orig_edges:
    lab = e['l']
    if lab.isdigit():
        lab = '支分'
    if lab in RELS:
        mapped = lab
    elif lab in REL_MAP:
        mapped = REL_MAP[lab]
    else:
        unknown.add(lab); mapped = '说明'
    ne = dict(s=e['s'], t=e['t'], l=mapped)
    if e['l'] not in RELS and e['l'] != mapped:
        ne['note'] = e['l']
    new_edges.append(ne)

E = [dict(s='four_truths', t='three_seals', l='说明', note='判定'),
     dict(s='three_seals', t='dependent_origination', l='说明', note='需解释'),
     dict(s='dependent_origination', t='two_truths', l='依据', note='展开'),
     dict(s='two_truths', t='three_natures', l='对辨', note='对映')]
E += [e for e in new_edges if (e['s'], e['t']) not in
      {('four_truths', 'three_seals'), ('three_seals', 'dependent_origination'),
       ('dependent_origination', 'two_truths'), ('two_truths', 'three_natures')}]

def add(s, t, l, note=None):
    e = dict(s=s, t=t, l=l)
    if note: e['note'] = note
    E.append(e)

# 09 体系层 → 10 汉传十宗
add('three_natures', 'vijnapti_matra', '依据', '由三性建立识有境无')
# 如来藏 → 中国各宗
for s, t, l, n in [
  ('three_natures','tathagatagarbha','依据',None),
  ('tathagatagarbha','panjiao','说明','组织'),
  ('madhyamaka','sanlun','判摄','汉传传承'),
  ('madhyamaka','sizhong_erdi','修证',None),
  ('prajna_emptiness','sizhong_erdi','修证',None),
  ('madhyamaka','nagarjuna','依据',None),
  ('madhyamaka','buddhapalita_bhaviveka','判摄',None),
  ('yogacara','vijnapti_matra','判摄',None),
  ('yogacara','eight_consciousnesses','判摄',None),
  ('yogacara','faxiang','判摄','汉传传承'),
  ('vijnapti_matra','yogacara_vs_madhyamaka','对辨',None),
  ('madhyamaka','yogacara_vs_madhyamaka','对辨',None),
  ('tathagatagarbha','debate_tathagatagarbha','对辨',None),
  ('hetuvidya','faxiang','支分','玄奘传入的论辩工具'),
  ('sarvastivada','abhidharma','支分',None),
  ('sautrantika','abhidharma','支分',None),
  ('sarvastivada','sautrantika','对辨','三世实有与过未无体'),
  ('sarvastivada','debate_atom','对辨',None),
  ('sautrantika','debate_atom','对辨',None),
  ('sarvastivada','jushe','依据',None),
  ('sautrantika','jushe','依据','世亲以经部义破有部'),
  ('councils','eighteen_schools','因果',None),
  ('councils','ashoka','层积',None),
  ('councils','abhidharma','说明','论藏定型之说'),
  ('ashoka','southern_tradition','因果','传教师分赴各地'),
  ('ashoka','sarvastivada','因果','西北印度传播'),
  ('karma','vipaka','因果',None),
  ('dharma_term','abhidharma','说明',None),
  ('anatta','karma_ownership','对辨',None),
  ('pudgala','debate_pudgala','对辨',None),
  ('sarvastivada','debate_pudgala','对辨',None),
  ('sautrantika','debate_pudgala','对辨',None),
  ('alaya','debate_pudgala','对辨',None),
  ('sravaka_fruits','five_paths','说明',None),
  ('four_foundations','thirty_seven_bodhipakkhiya','支分',None),
  ('eightfold','thirty_seven_bodhipakkhiya','支分',None),
  ('thirty_seven_bodhipakkhiya','prajna','修证',None),
  ('four_foundations','four_immeasurables','修证',None),
  ('three_trainings','five_paths','修证',None),
  ('bodhisattva_path','five_paths','修证',None),
  ('two_truths','debate_two_truths','对辨',None),
  ('three_truths_round','debate_two_truths','对辨',None),
  ('sizhong_erdi','debate_two_truths','对辨',None),
  ('three_vehicles_one_vehicle','debate_tathagatagarbha','对辨',None),
  ('three_vehicles_one_vehicle','wushi_bajiao','判摄',None),
  ('three_vehicles_one_vehicle','wujiao_shizong','判摄',None),
  ('panjiao','wushi_bajiao','支分',None),
  ('panjiao','wujiao_shizong','支分',None),
  ('panjiao','three_vehicles_one_vehicle','支分',None),
  ('faxiang','three_vehicles_one_vehicle','判摄',None),
  ('faxiang','wushi_bajiao','对辨','三时判教与五时八教'),
  ('chan','five_houses_seven_schools','支分',None),
  ('chan','tathagatagarbha','依据',None),
  ('chan','emptiness','依据',None),
  ('pureland','two_paths_two_powers','判摄',None),
  ('vinaya','jie_ti','判摄',None),
  ('sarvastivada','jie_ti','对辨','无表色为戒体'),
  ('sautrantika','jie_ti','对辨','思种为戒体'),
  ('jie_ti','chengshi','依据','道宣依《成实论》立非色非心戒体'),
  ('tantra','four_tantra_classes','支分',None),
  ('tantra','tangmi_tibetan','层积',None),
  ('tangmi_tibetan','tibetan_schools','层积',None),
  ('tibetan_schools','buddhapalita_bhaviveka','判摄','以应成见为究竟'),
  ('tibetan_schools','hetuvidya','修证','量论为僧伽教育核心'),
  ('tibetan_translation','tibetan_schools','依据',None),
  ('translation_history','yichang','支分',None),
  ('translation_history','pureland','因果',None),
  ('translation_history','tiantai','因果',None),
  ('translation_history','huayan','因果',None),
  ('translation_history','faxiang','因果',None),
  ('translation_history','sanlun','因果',None),
  ('translation_history','tantra','因果',None),
  ('huiChang_persecution','chan','因果','禅宗抗毁力最强'),
  ('huiChang_persecution','pureland','因果',None),
  ('huiChang_persecution','tangmi_tibetan','因果',None),
  ('mahayana_origins','madhyamaka','因果',None),
  ('mahayana_origins','yogacara','因果',None),
  ('modern_studies','historical_layers','说明',None),
  ('southern_tradition','four_foundations','依据',None),
  ('southern_tradition','four_dhyanas','依据',None),
  ('southern_tradition','sravaka_fruits','依据',None),
  ('chengshi','sarvastivada','对辨','破法体实有'),
  ('buddha_body_land','tathagatagarbha','依据','法身即如来藏出缠'),
  ('buddha_body_land','yogacara','依据','报身由识所变'),
  ('three_bodies','buddha_body_land','支分',None),
  ('five_paths','transformation','修证',None),
  ('vijnapti_matra','three_natures','依据',None),
  ('abhidharma','six_causes_five_results','支分',None),
  ('hetuvidya','madhyamaka','依据','量论与中观见地结合（藏传）'),
]:
    add(s, t, l, n)

add('samsara','three_realms','支分',None)
add('three_realms','four_dhyanas','修证','四禅八定的果报处所')
add('three_realms','six_realms','对辨','六道与三界的两种分类')
add('kalpa_cosmology','samsara','依据','轮回的时间尺度')
add('kalpa_cosmology','mahayana_origins','说明','多劫多佛与十方诸佛的背景')
add('four_dhyanas','samatha_vipassana','支分',None)
add('four_foundations','samatha_vipassana','修证',None)
add('thirty_seven_bodhipakkhiya','samatha_vipassana','修证',None)
add('samatha_vipassana','prajna','修证','观属慧学')
add('samatha_vipassana','samadhi_training','修证','止属定学')
add('samatha_vipassana','chan_methods','对辨','默照近止、话头近观')
add('samatha_vipassana','southern_tradition','判摄','清净道论的止观次第')
add('samatha_vipassana','tiantai','判摄','止观双修与一心三观')
add('vinaya_rites','precepts','支分',None)
add('vinaya_rites','jie_ti','说明','戒体的落实方式')
add('vinaya','vinaya_rites','支分',None)
add('four_reliances','historical_layers','对辨','教内判准与文献学判准')
add('four_reliances','panjiao','依据','依了义经不依不了义经')
add('four_reliances','yichang','依据','依义不依语为格义与意译开路')
add('four_reliances','debate_tathagatagarbha','依据',None)
add('icchantika','debate_tathagatagarbha','对辨',None)
add('icchantika','buddha_nature','依据',None)
add('icchantika','tathagatagarbha','支分',None)
add('icchantika','sanlun','判摄','竺道生与涅槃学的一阐提之争')
add('chan_methods','chan','支分',None)
add('chan_methods','seeing_nature','修证',None)
add('chan_methods','wunian','依据',None)
add('all_suffering','impermanence','因果','无常故苦')
add('all_suffering','dukkha','体同','即苦谛的行相')
add('all_suffering','nonself_seal','因果','苦故无我')
add('all_suffering','three_seals','支分',None)
add('all_suffering','southern_tradition','依据','三相为观智所缘')
add('all_suffering','nirvana','依据',None)

if unknown:
    print('!! 未能归类的原关系标签:', sorted(unknown))
E = [e for e in E if e['s'] in nodes and e['t'] in nodes]
print('关系总数', len(E), '类型', sorted({e['l'] for e in E}))

# ============================================================
# 4b. 文献索引与文献节点：从各节点出处反查，不另建一份数据
# ============================================================
DOCS = doc_list()
DOC_IDS = {}
DOC_IDS_INV = {}
make_doc_nodes()
build_src_index()   # 文献节点也要有 _src

DOC_GROUP_NAME = {'经': '经藏 · 主要经典', '律': '律藏 · 戒律与僧事',
                  '论疏': '论疏 · 论书与注疏', '史料': '史料 · 史传、目录与法敕',
                  '文献': '其他引用文献'}

def build_doc_branch():
    """把生成的文献节点按类别挂到第 12 层的「文献」分组下。"""
    kids = collections.OrderedDict()
    for d in DOCS:
        if 'id' not in d: continue
        kids.setdefault(d['kind'].split('/')[0], []).append(d)
    items = []
    for k, lst in kids.items():
        items.append(dict(id='docgroup_' + k,
                          note=DOC_GROUP_NAME.get(k, k) + ' · %d 种' % len(lst),
                          children=[dict(id=d['id']) for d in lst]))
    return items

for _L in TREE:
    for _it in _L['items']:
        if _it['id'] == 'docbranch':
            _it['children'] = build_doc_branch()
            _it['note'] = '%d 种' % sum(1 for d in DOCS if 'id' in d)

# 文献节点 → 引用该文献的节点（此时文献节点才存在）
# 注意：此处**不可截断**。文献节点正文声明「共 N 个节点引用此文献」，
# 若只连最相关的少数几条，关系图与正文自相矛盾（曾误限为 8 条，
# 使 444 条引用只画出 273 条，被引最多的《杂阿含经》只有 8 条出边）。
_doc_edge = 0
for _k in list(DOC_IDS.values()):
    for _i in DOC_IDS_INV.get(_k, []):
        add(_k, _i, '依据', None)
        _doc_edge += 1
E = [e for e in E if e['s'] in nodes and e['t'] in nodes]
print('文献关系新建', _doc_edge, '条')

# ============================================================
# 5. 渲染
# ============================================================
# 自动互链：长释义取前 2 次，短释义与出处取 1 次
# 只对两字以上的名称自动互链：单字名（行、识、受、取、有、生、法、空、业、苦…）
# 在正文中多为普通字词或引文术语，自动链接会破坏原文；这些概念由「关联节点」覆盖。
NAMES = sorted({nm for nm in ({v['n'] for v in nodes.values()} |
                              {a for v in nodes.values() for a in v.get('aka', [])})
                if len(nm) >= 2}, key=len, reverse=True)
NAME2ID = {}
for i, v in nodes.items():
    for nm in [v['n']] + list(v.get('aka', [])):
        NAME2ID.setdefault(nm, i)
PAT = re.compile('(' + '|'.join(re.escape(n) for n in NAMES) + ')')

def linkify(text, max_links=2, selfid=None):
    """把释义中首次出现的其他节点名转为内部链接（最多 max_links 个不同节点）"""
    used = []
    def repl(m):
        nm = m.group(0); tid = NAME2ID.get(nm)
        if tid is None or tid in used or tid == selfid:
            return nm
        if len(used) >= max_links:
            return nm
        used.append(tid)
        return '[[%s|%s]]' % (tid, nm)
    return PAT.sub(repl, text)

# 树：统计每个节点在目录中出现的位置，用于「另见」
place = {}
def walk_place(items, depth):
    for it in items:
        place.setdefault(it['id'], []).append(depth)
        walk_place(it.get('children', []), depth + 1)
for L in TREE: walk_place(L['items'], 1)
# 互链标记：释义长文取前 2 个不同节点，短释义与引文取 1 个
for k, v in nodes.items():
    v['d'] = linkify(v['d'], 2 if len(v['d']) > 150 else 1, selfid=k)
    for s in v['_src']:
        s['q'] = linkify(s['q'], 1)

for k, v in nodes.items():
    v['depth'] = place[k][0] if k in place else 3
    v['see'] = [x for x in (v.get('see') or []) if x in nodes]

# 校验
errs = []
for k, v in nodes.items():
    if not v['d'].strip(): errs.append('空释义: ' + k)
    if not v['_src']: errs.append('无出处: ' + k)
    if not v['tt'] and not k.startswith('doc_'):
        errs.append('无年代: ' + k)
    if k not in place: errs.append('未进目录: ' + k)
for e in E:
    if e['s'] not in nodes: errs.append('关系起点不存在: ' + e['s'])
    if e['t'] not in nodes: errs.append('关系终点不存在: ' + e['t'])
    if e['l'] not in RELS: errs.append('未知关系类型: ' + e['l'])
# 每个节点的 era 必须落在年表既有时段内，否则该节点不会出现在年表视图
_era_ids = [x[0] if isinstance(x, (tuple, list)) else x['id'] for x in ERAS]
for k, v in nodes.items():
    e = v.get('era')
    if e and e not in _era_ids:
        errs.append('era 值不在年表时段内（该节点将不进年表）: %s → %s' % (k, e))
if errs:
    print('校验发现问题：'); [print('  -', x) for x in errs[:40]]
else:
    print('校验通过：%d 节点 / %d 关系 / %d 条出处' % (
        len(nodes), len(E), sum(len(v['_src']) for v in nodes.values())))

# 生成前端数据
def dumps(o):
    return json.dumps(o, ensure_ascii=False, separators=(',', ':'))

JS_NODES = {}
for k, v in nodes.items():
    JS_NODES[k] = dict(n=v['n'], en=v['en'], c=v['c'], ep=v['ep'], d=v['d'],
                       src=[dict(t=s['t'], q=s['q'], tag=s['tag'], color=s['color']) for s in v['_src']],
                       tt=v['tt'], era=v.get('era', 'none'))
    if v.get('see'): JS_NODES[k]['see'] = v['see']
    if v.get('key'): JS_NODES[k]['key'] = 1

JS_TREE = TREE
JS_RELS = {k: dict(name=k, color=v[0], hint=v[1]) for k, v in RELS.items()}
JS_CATS = {k: dict(name=v[0], color=v[1]) for k, v in CATS.items()}
JS_EPS = {k: dict(name=v[0], color=v[1], hint=v[2]) for k, v in EPOCHS.items()}
JS_ERAS = [dict(id=e[0], label=e[1], hint=e[2]) for e in ERAS]

# 数据文件（便于后续拆分与审阅）
os.makedirs(os.path.dirname(DATA_JSON), exist_ok=True)
json.dump(dict(nodes=JS_NODES, tree=JS_TREE, edges=E, rels=JS_RELS, cats=JS_CATS,
               epochs=JS_EPS, eras=JS_ERAS, ttk=TTK, docs=DOCS),
          open(DATA_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write('/* 佛教基础理论数据（由 build/build.py 生成，可直接编辑本文件后重建页面） */\n')
    f.write('window.BUDDHISM_DATA = ' + json.dumps(dict(
        nodes=JS_NODES, tree=JS_TREE, edges=E, rels=JS_RELS, cats=JS_CATS,
        epochs=JS_EPS, eras=JS_ERAS, ttk=TTK), ensure_ascii=False) + ';\n')
print('数据文件已生成：', os.path.relpath(DATA_JSON, ROOT), os.path.relpath(DATA_JS, ROOT))


# ============================================================
# 6. 页面模板
# ============================================================
CSS = r'''
:root{
  --bg:#F6F6F3; --panel:#FFFFFF; --line:#E6E6E0; --line2:#F1F1EC;
  --ink:#1B2330; --ink2:#46536A; --ink3:#8A94A6; --ink4:#A8B0BE;
  --accent:#B45309; --accent-bg:#FDF3E7; --ok:#0F766E;
}
*{box-sizing:border-box;}
html,body{height:100%;margin:0;}
body{
  background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  font-size:13px;line-height:1.7;-webkit-font-smoothing:antialiased;
  display:flex;flex-direction:column;overflow:hidden;
}
header{flex:0 0 auto;padding:12px 22px 10px;background:linear-gradient(180deg,#FFFFFF 0%,#FCFCFA 100%);
  border-bottom:1px solid var(--line);}
header h1{margin:0;font-size:16px;font-weight:650;letter-spacing:.3px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;}
header h1 span{font-size:11.5px;font-weight:400;color:var(--ink3);letter-spacing:0;}
header .sub{margin-top:5px;font-size:11.5px;color:var(--ink3);display:flex;gap:16px;flex-wrap:wrap;align-items:center;}
header .sub b{color:var(--ink2);font-weight:600;font-variant-numeric:tabular-nums;}
header .sub .k{color:var(--ink4);}
.main{flex:1 1 auto;display:flex;min-height:0;}

/* ---------- 左栏 ---------- */
aside.outline{width:398px;flex:0 0 auto;background:var(--panel);border-right:1px solid var(--line);
  display:flex;flex-direction:column;min-height:0;}
.o-top{flex:0 0 auto;padding:9px 14px 8px;border-bottom:1px solid var(--line);background:var(--panel);}
#search{width:100%;padding:6px 10px;border:1px solid var(--line);border-radius:7px;font-size:12.5px;
  font-family:inherit;background:#FCFCFA;color:var(--ink);outline:none;}
#search:focus{border-color:var(--accent);background:#fff;}
.seg{display:flex;gap:0;margin-top:8px;border:1px solid var(--line);border-radius:8px;overflow:hidden;width:fit-content;}
.seg button{border:0;background:#FCFCFA;font-family:inherit;font-size:12px;color:var(--ink2);
  padding:5px 13px;cursor:pointer;display:flex;align-items:center;gap:6px;}
.seg button + button{border-left:1px solid var(--line);}
.seg button.on{background:var(--accent-bg);color:var(--accent);font-weight:600;}
.seg .cnt{font-size:10.5px;color:var(--ink4);font-variant-numeric:tabular-nums;}
.seg button.on .cnt{color:var(--accent);}
.search-info{font-size:11px;color:var(--ink3);margin-top:6px;min-height:15px;}
.search-info em{font-style:normal;color:var(--accent);font-weight:600;}
.o-body{flex:1 1 auto;overflow-y:auto;padding-bottom:60px;}
.rel-legend{display:flex;flex-wrap:wrap;gap:4px;padding:8px 12px 4px;border-bottom:1px solid var(--line2);}
.rel-legend .lg{font-size:10.5px;padding:2px 7px;border-radius:10px;border:1px solid var(--line);
  background:#FCFCFA;color:var(--ink2);cursor:pointer;display:flex;align-items:center;gap:4px;}
.rel-legend .lg i{width:7px;height:7px;border-radius:50%;display:block;}
.rel-legend .lg.on{background:#FFF7E6;border-color:#E7C79B;color:var(--accent);font-weight:600;}
.rel-legend .lg.off{opacity:.45;}
.tree-tools{display:flex;gap:10px;padding:6px 14px 4px;font-size:11px;color:var(--ink3);}
.tree-tools button{border:0;background:none;font-family:inherit;font-size:11px;color:var(--ink3);
  cursor:pointer;padding:0;text-decoration:underline dotted;}
.tree-tools button:hover{color:var(--accent);}
.layer-group{margin-bottom:1px;}
.layer-header{display:flex;align-items:center;gap:8px;padding:9px 14px 9px 12px;cursor:pointer;
  user-select:none;border-left:3px solid var(--c);background:#FCFCFA;transition:.12s;}
.layer-header:hover{background:#F4F4F0;}
.layer-header .num{font-size:11px;font-weight:650;color:var(--c);font-variant-numeric:tabular-nums;flex:0 0 auto;}
.layer-header .name{flex:1 1 auto;font-size:12.5px;font-weight:600;color:var(--ink);}
.layer-header .epoch{font-size:10.5px;color:var(--ink3);flex:0 0 auto;text-align:right;max-width:46%;}
.layer-header .tog{font-size:9px;color:var(--ink3);transition:.15s;flex:0 0 auto;width:12px;text-align:center;}
.layer-group.collapsed .layer-body{display:none;}
.layer-group.collapsed .tog{transform:rotate(-90deg);}
.layer-body{padding:2px 0 6px;}
.node-row{display:flex;align-items:center;gap:7px;padding:4px 12px 4px 14px;cursor:pointer;
  border-left:3px solid transparent;user-select:none;}
.node-row:hover{background:#F4F4F0;}
.node-row.selected{background:var(--accent-bg);}
.node-row.selected .node-label{color:var(--accent);font-weight:600;}
.node-row.dim{display:none;}
.node-row.match{background:#FFF7E6;}
.node-row.match.selected{background:var(--accent-bg);}
.node-dot{width:7px;height:7px;border-radius:50%;flex:0 0 auto;}
.node-label{flex:1 1 auto;font-size:12.5px;color:var(--ink2);white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;}
.node-role{font-size:9.5px;color:var(--ink4);flex:0 0 auto;background:#F2F2EE;border-radius:3px;
  padding:0 4px;line-height:1.5;}
.node-src{font-size:9.5px;color:var(--ink4);flex:0 0 auto;font-variant-numeric:tabular-nums;}
.node-ep{font-size:9.5px;padding:1px 5px;border-radius:3px;flex:0 0 auto;color:#fff;line-height:1.4;}
.node-row.lv1 .node-label{font-weight:600;color:var(--ink);font-size:13px;}
.node-row.lv1 .node-dot{width:9px;height:9px;}
.node-group{font-size:11px;color:var(--ink3);padding-top:8px;padding-bottom:2px;letter-spacing:.3px;}

/* ---------- 学习路径 ---------- */
.path-card{border-bottom:1px solid var(--line2);padding:12px 14px 14px;}
.path-card .ph{display:flex;align-items:baseline;gap:8px;}
.path-card .num{width:18px;height:18px;border-radius:5px;background:var(--accent);color:#fff;
  font-size:10.5px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:0 0 auto;}
.path-card .pn{font-size:13px;font-weight:650;color:var(--ink);}
.path-card .pt{font-size:10.5px;color:var(--ink4);margin-left:auto;}
.path-card .psub{font-size:11.5px;color:var(--accent);margin:4px 0 6px;}
.path-card .pgoal{font-size:12px;color:var(--ink2);line-height:1.8;}
.path-card .plabel{font-size:10.5px;color:var(--ink3);margin:10px 0 5px;}
.path-card .pnodes{display:flex;flex-wrap:wrap;gap:4px;}
.path-card .pnodes .tl-chip{font-size:11px;padding:2px 8px;}
.path-card .ptexts{margin:0;padding-left:17px;font-size:11.5px;color:var(--ink2);line-height:1.85;}
.path-card .pprac{margin-top:9px;font-size:11.5px;color:var(--ok);background:#F2F8F6;
  border-radius:7px;padding:7px 10px;line-height:1.75;}

/* ---------- 年表 ---------- */
.tl-era{margin-bottom:2px;}
.tl-head{display:flex;align-items:baseline;gap:9px;padding:11px 14px 6px;position:sticky;top:0;
  background:linear-gradient(180deg,#FFFFFF 70%,rgba(255,255,255,0));z-index:2;}
.tl-head .lbl{font-size:12.5px;font-weight:650;color:var(--ink);}
.tl-head .hint{font-size:10.5px;color:var(--ink3);}
.tl-head .n{font-size:10.5px;color:var(--ink4);margin-left:auto;font-variant-numeric:tabular-nums;}
.tl-items{display:flex;flex-wrap:wrap;gap:5px;padding:2px 14px 10px;border-bottom:1px dashed var(--line2);}
.tl-chip{font-size:11.5px;padding:3px 9px;border-radius:12px;border:1px solid var(--line);
  background:#FCFCFA;color:var(--ink2);cursor:pointer;display:flex;align-items:center;gap:5px;}
.tl-chip:hover{border-color:var(--accent);color:var(--accent);background:#FFF9F0;}
.tl-chip.on{background:var(--accent-bg);border-color:#E7C79B;color:var(--accent);font-weight:600;}
.tl-chip.key{background:#fff;border-color:#D9D9D2;font-weight:600;color:var(--ink);}
.tl-chip i{width:7px;height:7px;border-radius:50%;display:block;flex:0 0 auto;}
.tl-chip .d{font-size:9.5px;color:var(--ink4);}

/* ---------- 右栏 ---------- */
main.detail{flex:1 1 auto;overflow-y:auto;padding:22px 30px 60px;min-width:0;}
#pane-node{max-width:none;}
.tabs{display:flex;gap:0;border:1px solid var(--line);border-radius:8px;overflow:hidden;width:fit-content;margin:0 0 16px;}
.tabs button{border:0;background:#FCFCFA;font-family:inherit;font-size:12px;color:var(--ink2);
  padding:5px 14px;cursor:pointer;}
.tabs button + button{border-left:1px solid var(--line);}
.tabs button.on{background:var(--accent-bg);color:var(--accent);font-weight:600;}
.pane{display:none;}
.pane.on{display:block;}
.welcome{max-width:820px;color:var(--ink2);}
.welcome h2{font-size:17px;font-weight:650;margin:0 0 10px;color:var(--ink);}
.welcome p{margin:0 0 10px;font-size:12.8px;line-height:1.9;}
.welcome ul{margin:8px 0 0;padding-left:20px;font-size:12.8px;line-height:1.9;}
.welcome li{margin-bottom:3px;}
.welcome code{background:#F0F0EC;border-radius:4px;padding:1px 5px;font-size:12px;font-family:inherit;color:var(--ink2);}
.chain{display:flex;align-items:center;flex-wrap:wrap;gap:9px 0;margin:14px 0 6px;}
.chain-break{flex:0 0 100%;height:0;margin:0;}
.chain-side{font-size:10.5px;color:var(--ink3);flex:0 0 auto;padding:0 9px 0 2px;
  border-left:2px solid var(--line);margin-left:2px;line-height:1.4;}
.cstep{display:flex;align-items:center;gap:6px;background:#fff;border:1px solid var(--line);
  border-radius:9px;padding:5px 9px 5px 6px;}
.cstep .cn{width:19px;height:19px;border-radius:5px;color:#fff;font-size:10px;font-weight:700;
  display:flex;align-items:center;justify-content:center;flex:0 0 auto;}
.cstep .ct{font-size:12px;font-weight:600;color:var(--ink);line-height:1.3;}
.cstep .ct em{display:block;font-style:normal;font-size:10px;font-weight:400;color:var(--ink3);letter-spacing:.3px;}
.car{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 2px;}
.car .ar{color:var(--ink4);font-size:13px;line-height:1;}
.car .lb{font-size:9.5px;color:var(--ink3);line-height:1.2;white-space:nowrap;}
.guide{margin-top:22px;border-top:1px solid var(--line);padding-top:16px;max-width:820px;}
.guide h3{font-size:13.5px;margin:0 0 10px;color:var(--ink);}
.guide details{border:1px solid var(--line);border-radius:9px;background:#FCFCFA;margin-bottom:8px;}
.guide summary{cursor:pointer;padding:9px 13px;font-size:12.5px;font-weight:600;color:var(--ink2);
  list-style:none;display:flex;align-items:center;gap:7px;}
.guide summary::-webkit-details-marker{display:none;}
.guide summary:before{content:"▸";color:var(--ink4);font-size:11px;}
.guide details[open] summary:before{content:"▾";}
.guide .gb{padding:0 14px 12px;font-size:12.5px;color:var(--ink2);line-height:1.9;}
.guide .gb ul{margin:6px 0;padding-left:18px;}
.guide .gb li{margin-bottom:4px;}
.guide .gb b{color:var(--ink);}
.guide table{border-collapse:collapse;width:100%;margin:8px 0;font-size:12px;}
.guide th,.guide td{border:1px solid var(--line);padding:4px 8px;text-align:left;color:var(--ink2);}
.guide th{background:#F7F7F3;color:var(--ink);font-weight:600;}
.tagline{display:inline-block;font-size:11px;color:var(--ink3);background:#F2F2EE;border-radius:4px;
  padding:0 6px;line-height:1.6;}

/* 详情 */
.d-head h2{margin:0 0 4px;font-size:19px;font-weight:650;}
.d-en{font-size:12px;color:var(--ink3);font-family:"Times New Roman",Georgia,serif;font-style:italic;}
.d-badges{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0 20px;align-items:center;}
.badge{font-size:10.5px;color:#fff;border-radius:4px;padding:1px 7px;line-height:1.7;}
.badge.ghost{background:none!important;color:var(--ink3);border:1px solid var(--line);}
.d-sec{display:flex;align-items:baseline;gap:9px;margin:22px 0 9px;padding-bottom:5px;
  border-bottom:1px solid var(--line);}
.d-sec h3{margin:0;font-size:12.5px;font-weight:650;color:var(--ink);letter-spacing:.4px;}
.d-sec i{font-style:normal;font-size:11px;color:var(--ink4);}
.d-desc{font-size:13.2px;line-height:2.0;color:var(--ink2);max-width:760px;white-space:pre-wrap;}
.d-desc a{color:var(--accent);text-decoration:none;border-bottom:1px solid #E7C79B;cursor:pointer;}
.d-desc .li{display:inline-block;width:13px;color:var(--ink3);}
.d-desc b{color:var(--ink);}
.d-desc a:hover{background:var(--accent-bg);}
.tbl{border:1px solid var(--line);border-radius:9px;overflow:hidden;max-width:820px;background:#FCFCFA;}
.trow{display:flex;gap:12px;padding:8px 13px;border-bottom:1px solid var(--line2);align-items:baseline;}
.trow:last-child{border-bottom:none;}
.tk{flex:0 0 72px;font-size:11.5px;color:var(--ink3);}
.tv{flex:1 1 auto;font-size:12.5px;color:var(--ink2);line-height:1.8;}
.tv .ep-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;position:relative;top:-1px;}
.src{display:flex;flex-direction:column;gap:9px;max-width:820px;}
.sitem{border-left:2px solid var(--accent);background:#FCFBF8;border-radius:0 8px 8px 0;padding:8px 13px;}
.sname{font-size:12.5px;font-weight:600;color:var(--ink);display:flex;align-items:center;gap:7px;flex-wrap:wrap;}
.stag{font-size:10px;color:#fff;border-radius:3px;padding:0 5px;line-height:1.6;font-weight:400;}
.squote{margin-top:5px;font-size:12.3px;color:var(--ink2);line-height:1.85;padding-left:9px;
  border-left:2px solid var(--line);}
.rel-list{display:flex;flex-direction:column;max-width:820px;border:1px solid var(--line);border-radius:9px;overflow:hidden;}
.rel{display:flex;align-items:center;gap:9px;padding:7px 12px;border-bottom:1px solid var(--line2);
  background:#fff;cursor:pointer;text-align:left;font-family:inherit;font-size:12.5px;color:var(--ink2);
  border-left:0;border-right:0;border-top:0;width:100%;}
.rel:last-child{border-bottom:none;}
.rel:hover{background:#F6F6F2;}
.rel:hover .rel-name{color:var(--accent);}
.rel .dir{color:var(--ink3);font-size:11px;flex:0 0 auto;width:14px;}
.rel .rel-name{flex:0 0 auto;color:var(--ink);font-weight:500;}
.rel .tag{font-size:10.5px;color:#fff;border-radius:4px;padding:1px 7px;flex:0 0 auto;}
.rel .rn{font-size:11.5px;color:var(--ink3);flex:1 1 auto;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap;}
.see-bar{display:flex;flex-wrap:wrap;gap:7px;align-items:center;font-size:11.5px;color:var(--ink3);margin:10px 0 0;}
.see-bar button{font-family:inherit;font-size:11.5px;border:1px dashed var(--line);background:#FCFCFA;
  color:var(--accent);border-radius:12px;padding:2px 10px;cursor:pointer;}
.meta-note{margin-top:30px;padding:13px 15px;background:#FCFCFA;border:1px solid var(--line);
  border-radius:9px;font-size:11.8px;color:var(--ink3);line-height:1.9;max-width:820px;}
.meta-note b{color:var(--ink2);}

/* 文献总览 */
.doc-tbl{border-collapse:collapse;width:100%;max-width:900px;font-size:12.3px;margin:2px 0 4px;}
.doc-tbl th{background:#F7F7F3;border:1px solid var(--line);padding:5px 9px;text-align:left;
  color:var(--ink);font-weight:600;font-size:11.5px;}
.doc-tbl td{border:1px solid var(--line2);padding:5px 9px;color:var(--ink2);vertical-align:top;}
.doc-row{cursor:pointer;}
.doc-row:hover td{background:#FFF9F0;}
.doc-row .dn{font-weight:600;color:var(--ink);}
.doc-row .dc{font-variant-numeric:tabular-nums;color:var(--ink3);}
.doc-detail td{background:#FCFBF8;padding:8px 9px;}
.doc-detail .tl-chip{font-size:11px;padding:2px 8px;margin:0 3px 3px 0;}

/* 窄屏 */
.m-back{display:none;}
.m-guide{display:none;}
@media (max-width:820px){
  header{padding:11px 14px 9px;}
  header h1{font-size:15px;}
  header .sub{gap:12px;}
  aside.outline{width:100%;border-right:0;}
  main.detail{display:none;}
  body.detail-open aside.outline{display:none;}
  body.detail-open main.detail{display:block;padding:14px 15px 60px;}
  .m-back{display:flex;position:fixed;left:12px;bottom:14px;z-index:20;align-items:center;gap:6px;
    background:#fff;border:1px solid var(--line);border-radius:20px;padding:7px 15px;font-size:12.5px;
    color:var(--ink2);box-shadow:0 2px 10px rgba(0,0,0,.08);cursor:pointer;}
  body:not(.detail-open) .m-back{display:none;}
  .m-back .ar{font-size:15px;}
  .seg button{padding:6px 11px;font-size:12.5px;}
  .node-row{padding-top:7px;padding-bottom:7px;min-height:38px;}
  .node-row.lv1{min-height:42px;}
  .node-row.lv1 .node-label{font-size:14px;}
  .rel{padding:10px 4px;}
  .tl-head{position:static;}
  .d-desc{font-size:13.6px;line-height:1.95;}
  .welcome h2{font-size:16px;}
  .welcome p,.welcome ul{font-size:13.2px;line-height:1.85;}
  .chain{flex-direction:column;align-items:stretch;gap:0;margin:12px 0 4px;}
  .cstep{width:100%;border-radius:9px;}
  .cstep .ct{white-space:normal;font-size:13px;}
  .car{flex-direction:row;padding:3px 0 3px 14px;justify-content:flex-start;gap:7px;}
  .car .ar{transform:rotate(90deg);}
  /* 窄屏下详情为覆盖层，总览与说明需另给入口，故在目录底部展开一份 */
  .m-guide{display:block;margin:10px 12px 0;border:1px solid var(--line);border-radius:9px;
    background:#FCFCFA;overflow:hidden;}
  .m-guide summary{padding:11px 13px;font-size:12.5px;font-weight:600;color:var(--ink2);
    cursor:pointer;list-style:none;display:flex;align-items:center;gap:7px;}
  .m-guide summary::-webkit-details-marker{display:none;}
  .m-guide summary:before{content:"▸";color:var(--ink4);font-size:11px;}
  .m-guide[open] summary:before{content:"▾";}
  .mg-body{padding:0 13px 14px;}
  .mg-body .welcome{max-width:none;}
  .mg-body .welcome h2:first-child{display:none;}
  .mg-body .chain{flex-direction:column;align-items:stretch;gap:0;}
  .mg-body .cstep{width:100%;}
  .mg-body .car{flex-direction:row;padding:3px 0 3px 14px;gap:7px;}
  .mg-body .car .ar{transform:rotate(90deg);}
  .mg-body .guide{margin-top:12px;border-top:1px solid var(--line);}
}
@media print{
  header,.o-top,body:not(.detail-open) aside.outline{display:none;}
  html,body{height:auto;overflow:visible;}
  .main{display:block;}
  aside.outline{width:auto;border:0;}
  main.detail{display:block!important;padding:0;overflow:visible;}
  .tabs{display:none;}
  .pane{display:block!important;}
}
'''

# 总览页：主线链 + 修订说明（作为单页应用的首页）
# 主线链：nodes 之间用 arrows 连接（None 表示该处换行分隔）
CHAIN_NODES = [
 ('四圣谛', '问题层', '#C2410C'),
 ('三法印', '标准层', '#7C3AED'),
 ('缘起 · 业果', '原理层', '#0369A1'),
 ('部派 · 阿毗达磨', '论书层', '#1D4ED8'),
 ('中观 · 唯识', '大乘层', '#4338CA'),
 ('如来藏', '依据层', '#BE185D'),
 ('判教 · 十宗', '体系层', '#A21CAF'),
 ('修行实践', '实践层', '#4D7C0F'),
 ('历史 · 传播', '史论层', '#57534E'),
]
CHAIN_ARROWS = ['判定标准', '追问原理', '论书整理', None,
                '大乘开展', '成立依据', '判摄组织', None, None]

GUIDE_REV = '''<details open><summary>本版修订说明</summary><div class="gb">
<b>一、时间维度独立为「年表」视图</b>　原版把年代分散于各节点的「时间 · 层积」栏内，发展线索因此不易看出。本版新增按九个时段编排的年表，可检索、可跳转；每个时段内标出重点节点（共 31 个）。
<br><br><b>二、关系类型规范化</b>　原版 223 条关系使用 142 种标签，其中 12 条以数字 1—12 标注十二因缘诸支，无法按类检索。本版归为十类：<b>支分 · 次第 · 因果 · 体同 · 判摄 · 对辨 · 修证 · 层积 · 依据 · 说明</b>。原有的具体说法移入行内小字保留，关系可按类型筛选。
<br><br><b>三、补足四个体系支点</b>
<ul>
<li><b>04 论书层</b>——三次结集、部派分裂、阿毗达磨、说一切有部、经量部、六因四缘五果。原版引《俱舍论》46 处，却没有安放「论」这一层的位置；而部派论诤是理解此后一切宗派的前提。</li>
<li><b>05 大乘层</b>——龙树、中观派、应成与自续、瑜伽行派、识有境无、因明。原版的中观仅见于「三论宗」的传承简介，印度大乘的两大轨道缺其一。</li>
<li><b>四大论诤</b>——无我谁受报、极微与无方分、二谛的体与教、如来藏是否了义。理论推进的关键争论，原版未作记录。</li>
<li><b>12 历史 · 传播</b>——阿育王与佛法西传、大乘起源问题、汉译四阶段、译场与格义、藏译与藏文大藏经、会昌法难、南传与巴利三藏、现代佛学研究。原版有宗派而无输入史，故「近代汉传何以禅净为主」一类问题无从解答。</li>
</ul>
<b>四、目录层级对齐</b>　原版有 57 个节点的层级标记与目录缩进不一致（八识、转识成智被列为顶层概念），5 个节点在目录中重复出现。本版各归其位，重复处改标「另见」。
<br><br><b>五、文献层与年代口径</b>　新增 52 个文献节点（被 3 个以上节点引用的经、律、论疏、史料各一个节点）与可检索的「经律论总览」（151 种）。文献节点只交代性质、引用规模与引用它的节点，<b>不标注该文献自身的年代</b>——同一部经的思想源头与文本定型常相差数百年，此类判断只能由讨论该文献的节点（04 论书层、12 历史 · 传播）给出。
<br><br><b>六、细节校订</b>　南传「三相」的第二支恢复为「诸行是苦」（原版误重复「诸法无我」）；「涅槃」统一为「涅槃寂静」；《俱舍论》的两种题名统一。释义保持原状：深度依各概念的需要而定，不作长度上的齐一。
</div></details>'''

GUIDE_USE = '''<details><summary>阅读路径与判读方法</summary><div class="gb">
<b>四种读法</b>
<ul>
<li><b>建立框架</b>——由本页主线链入手，再按目录 01 → 12 逐层阅读各节点释义。各节点释义<b>首段为要义</b>，其后为展开与争议。</li>
<li><b>理清源流</b>——切至「年表」，自「约前 6—前 5 世纪」逐段下读，留意标注为重点的节点。</li>
<li><b>考辨单一概念</b>——用检索。检索范围含名称、梵巴原语、释义正文与所引经论名；输入《俱舍论》《中论》可列出全部相关节点与文献节点。</li>
<li><b>比较宗派立场</b>——用关系色标筛选。只看「对辨」可得全部论诤，只看「判摄」可得各宗对同一概念的定位。</li>
</ul>
<b>每一节点的四项内容</b>
<ul>
<li><b>释义</b>——按要义、展开、争议三层组织。</li>
<li><b>时间 · 层积</b>——「思想形成」为该观念在文献中可追溯的最早形态；「文献定型」为其被命名、被系统整理的时间；「汉译流传」为汉传读者实际接触的时点。三者常相差数百年，故分列。</li>
<li><b>出处</b>——尽量标至卷、品或经号，并附原文引文；标签区分经、律、论疏、史料。同一概念常先见于经、后由论书定型，混同会误判年代。</li>
<li><b>关联节点</b>——标注关系类型与具体说明；释义中的彩色词亦可直接跳转。</li>
</ul>
<b>三个断代判准</b>
<ul>
<li>本页年代均为约数或区间。佛陀生卒年有南传（前 624—前 544）、汉传（前 565—前 486）、现代学界（约前 480—前 400）三说，本页统一自「约前 5 世纪」起算。</li>
<li>「结集」「大乘起源」诸问题，传统记载均为后世追溯，与实物史料（阿育王法敕、犍陀罗写本）所示时间表并不重合，页内分列两方。</li>
<li>第十二层的传播史属现代史学与文献学的整理，性质不同于前十一层的教义内容，宜分开看待。</li>
</ul>
<b>关系网络与主线的关系</b>
<ul>
<li>主线九项只表示主干，不表示唯一的理解顺序。全页 795 条关系中约 76% 为跨层关系，另有「论诤」「对辨」两类专门记录宗派分歧。</li>
</ul>
</div></details>'''

GUIDE_GLOSS = '''<details><summary>十种关系类型</summary><div class="gb">
本页节点之间的关联统一归为十类。原版关系标签共 142 种，具体说法现移入关联行的小字栏，此处仅存其类。
<table><tr><th>类型</th><th>含义</th><th>本页例证</th></tr>
''' + ''.join(
 '<tr><td><span class="tagline" style="color:%s">%s</span></td><td>%s</td><td>%s</td></tr>' % (
   RELS[k][0], k, RELS[k][1], ex) for k, ex in [
   ('支分', '四圣谛 ← 苦谛 / 集谛 / 灭谛 / 道谛'),
   ('次第', '三皈依 → 五戒'),
   ('因果', '十二因缘 → 六道轮回'),
   ('体同', '涅槃寂静 ＝ 择灭无为'),
   ('判摄', '如来藏 → 密宗判为依据'),
   ('对辨', '说一切有部 ↔ 经量部（三世实有 / 过未无体）'),
   ('修证', '四念处 → 三十七道品（观法所摄）'),
   ('层积', '早期层 → 发展层'),
   ('依据', '阿赖耶识 依《解深密经》'),
   ('说明', '三法印 由 四圣谛 判定'),
 ]) + '</table></div></details>'''

JS = r'''
/* ============================================================
   佛教基础理论 · 结构树（第二版）
   数据来自 data/buddhism.data.js（同源生成），亦可直接编辑本文件重建
   ============================================================ */
const DATA = window.BUDDHISM_DATA;
const DOCS = __DOCS__;
const NODES = DATA.nodes, TREE = DATA.tree, EDGES = DATA.edges;
const RELS = DATA.rels, CATS = DATA.cats, EP = DATA.epochs, ERAS = DATA.eras, TTK = DATA.ttk;

const ADJ = {}; Object.keys(NODES).forEach(id => ADJ[id] = []);
let edgeN = 0;
EDGES.forEach(e => {
  if (!NODES[e.s] || !NODES[e.t]) return;
  edgeN++;
  ADJ[e.s].push({o: e.t, l: e.l, note: e.note || '', dir: 'out'});
  ADJ[e.t].push({o: e.s, l: e.l, note: e.note || '', dir: 'in'});
});

/* ---------- 工具 ---------- */
const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const mdIn = s => esc(s)
  .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
  .replace(/\[\[([a-z0-9_]+)\|(.+?)\]\]/g, '<a href="#$1" class="ilink">$2</a>')
  .replace(/\n\n/g, '<br><br>')
  .replace(/\n(?=- |\d+\. )/g, '<br>')
  .replace(/\n(?=[^<])/g, '<br>')
  .replace(/(^|<br>)- /g, '$1<span class="li">·</span>');
const q = s => document.querySelector(s);
const qa = s => Array.prototype.slice.call(document.querySelectorAll(s));
const isNarrow = () => window.matchMedia('(max-width: 820px)').matches;

/* ---------- 左栏：目录 ---------- */
const treeEl = q('#tree'), tlEl = q('#timeline'), pathsEl = q('#paths');
let detailEl = null;   /* 节点详情的容器，首次渲染前解析 */
let selectedId = null, query = '', activeTab = 'tree';

function nodeRow(id, depth, role) {
  const n = NODES[id];
  if (!n) return null;
  const row = document.createElement('div');
  row.className = 'node-row lv' + Math.min(n.depth || depth, 4);
  row.dataset.id = id;
  row.style.paddingLeft = (14 + (n.depth || depth) * 13) + 'px';
  const ep = EP[n.ep], cat = CATS[n.c];
  row.innerHTML =
    '<span class="node-dot" style="background:' + cat.color + '"></span>' +
    '<span class="node-label">' + esc(n.n) + '</span>' +
    (role ? '<span class="node-role">' + esc(role) + '</span>' : '') +
    '<span class="node-src" title="出处 ' + n.src.length + ' 条">' + n.src.length + '</span>' +
    (ep ? '<span class="node-ep" style="background:' + ep.color + '">' + ep.name.slice(0, 2) + '</span>' : '');
  row.addEventListener('click', () => selectNode(id));
  return row;
}
function buildItem(item, depth) {
  const frag = document.createDocumentFragment();
  // 分组节点（如「经藏 · 主要经典」）自身不是知识点，只作分隔标题
  if (!NODES[item.id]) {
    const head = document.createElement('div');
    head.className = 'node-group';
    head.style.paddingLeft = (14 + depth * 13) + 'px';
    head.textContent = item.name || item.note || '';
    if (item.name) frag.appendChild(head);
  } else {
    const row = nodeRow(item.id, depth, item.note);
    if (row) frag.appendChild(row);
  }
  (item.children || []).forEach(c => frag.appendChild(buildItem(c, depth + 1)));
  return frag;
}
TREE.forEach(layer => {
  const group = document.createElement('div');
  group.className = 'layer-group';
  group.style.setProperty('--c', '#B45309');
  const head = document.createElement('div');
  head.className = 'layer-header';
  head.innerHTML = '<span class="num">' + esc(layer.title.slice(0, 2)) + '</span>' +
    '<span class="name">' + esc(layer.title.slice(3)) + '</span>' +
    '<span class="epoch">' + esc(layer.epoch) + '</span><span class="tog">▼</span>';
  head.addEventListener('click', () => group.classList.toggle('collapsed'));
  const body = document.createElement('div');
  body.className = 'layer-body';
  layer.items.forEach(it => body.appendChild(buildItem(it, 1)));
  group.appendChild(head); group.appendChild(body);
  treeEl.appendChild(group);
});

/* ---------- 左栏：年表 ---------- */
ERAS.forEach(era => {
  const ids = Object.keys(NODES).filter(id => NODES[id].era === era.id);
  if (!ids.length) return;
  const catOrder = Object.keys(CATS);
  ids.sort((a, b) => {
    const A = NODES[a], B = NODES[b];
    if (!!B.key !== !!A.key) return (B.key ? 1 : 0) - (A.key ? 1 : 0);
    const ca = catOrder.indexOf(A.c), cb = catOrder.indexOf(B.c);
    if (ca !== cb) return ca - cb;
    return A.n.localeCompare(B.n, 'zh');
  });
  const box = document.createElement('div');
  box.className = 'tl-era';
  const keyN = ids.filter(i => NODES[i].key).length;
  box.innerHTML = '<div class="tl-head"><span class="lbl">' + esc(era.label) + '</span>' +
    '<span class="hint">' + esc(era.hint) + '</span>' +
    '<span class="n">' + ids.length + ' 项' + (keyN ? '（重点 ' + keyN + '）' : '') + '</span></div>';
  const items = document.createElement('div');
  items.className = 'tl-items';
  ids.forEach(id => {
    const n = NODES[id], cat = CATS[n.c];
    const chip = document.createElement('button');
    chip.className = 'tl-chip' + (n.key ? ' key' : '');
    chip.dataset.id = id;
    chip.innerHTML = '<i style="background:' + cat.color + '"></i>' + esc(n.n) +
      '<span class="d">' + n.src.length + '</span>';
    chip.addEventListener('click', () => selectNode(id));
    items.appendChild(chip);
  });
  box.appendChild(items); tlEl.appendChild(box);
});

/* ---------- 左栏：学习路径 ---------- */
function buildPathCards() {
pathsEl.innerHTML = '';
PATHS.forEach((p, i) => {
  const box = document.createElement('div');
  box.className = 'path-card';
  box.innerHTML = '<div class="ph"><span class="num">' + (i + 1) + '</span>' +
    '<span class="pn">' + esc(p.n) + '</span><span class="pt">' + esc(p.time) + '</span></div>' +
    '<div class="psub">' + esc(p.sub) + '</div>' +
    '<div class="pgoal">' + esc(p.goal) + '</div>' +
    '<div class="plabel">依次读这些节点</div><div class="pnodes"></div>' +
    '<div class="plabel">配合原典</div><ul class="ptexts">' +
    p.texts.map(t => '<li>' + esc(t) + '</li>').join('') + '</ul>' +
    '<div class="pprac">动手一处：' + esc(p.prac) + '</div>';
  const holder = box.querySelector('.pnodes');
  p.nodes.forEach(id => {
    const n = NODES[id]; if (!n) return;
    const b = document.createElement('button');
    b.className = 'tl-chip'; b.dataset.id = id;
    b.innerHTML = '<i style="background:' + CATS[n.c].color + '"></i>' + esc(n.n);
    b.addEventListener('click', () => { selectNode(id); scrollToRow(id); });
    holder.appendChild(b);
  });
  pathsEl.appendChild(box);
});
}

/* ---------- 左栏：关系筛选 ---------- */
const relBar = q('#relLegend');
let relOff = {};
Object.keys(RELS).forEach(k => {
  const b = document.createElement('button');
  b.className = 'lg'; b.dataset.rel = k;
  b.innerHTML = '<i style="background:' + RELS[k].color + '"></i>' + k;
  b.title = RELS[k].hint;
  b.addEventListener('click', () => {
    relOff[k] = !relOff[k];
    b.classList.toggle('off', !!relOff[k]);
    applyFilter();
  });
  relBar.appendChild(b);
});

/* ---------- 搜索 / 筛选 ---------- */
const searchInput = q('#search'), searchInfo = q('#searchInfo');
function haystack(id) {
  const n = NODES[id];
  return (n.n + ' ' + (n.en || '') + ' ' + id + ' ' +
    n.src.map(s => s.t + ' ' + s.q).join(' ') + ' ' +
    [n.tt.form, n.tt.fix, n.tt.trans].join(' ') + ' ' + n.d).toLowerCase();
}
function keptRels() { return Object.keys(RELS).filter(k => !relOff[k]); }
function matchRels(id) {
  // 关系筛选是「只看被选中的类型」：节点的全部关系都须在保留的集合内
  const kept = keptRels();
  if (!kept.length) return false;
  const rs = (ADJ[id] || []).map(e => e.l);
  if (!rs.length) return false;
  return rs.every(l => kept.indexOf(l) >= 0);
}
function applyFilter() {
  let cnt = 0;
  const seen = {};
  const q = query;
  const relFiltering = Object.keys(relOff).some(k => relOff[k]);
  const filtering = !!q || relFiltering || keyOnly;
  qa('.node-row, .tl-chip').forEach(row => {
    const id = row.dataset.id;
    if (!NODES[id]) return;
    let ok = true;
    if (q) ok = haystack(id).indexOf(q) >= 0;
    if (ok && relFiltering) ok = matchRels(id);
    if (ok && keyOnly) ok = !!NODES[id].key || NODES[id].era === 'none';
    // 只有一个目录位置被计为「匹配」，重复出现的节点只计数一次
    if (ok && !seen[id]) { seen[id] = 1; cnt++; }
    row.classList.toggle('dim', !ok);
    row.classList.toggle('match', !!q && ok);
  });
  if (filtering) {
    searchInfo.innerHTML = cnt ? '匹配 <em>' + cnt + '</em> 项，回车跳到第一个'
      : '无匹配（可放宽关系筛选）';
    qa('.layer-group').forEach(g => g.classList.remove('collapsed'));
  } else searchInfo.textContent = '';
}
searchInput.addEventListener('input', e => { query = e.target.value.trim().toLowerCase(); applyFilter(); });
searchInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    const first = q('.node-row.match') || q('.tl-chip.match');
    if (first) { selectNode(first.dataset.id); scrollToRow(first.dataset.id); }
  }
});
qa('#treeTools button').forEach(b => b.addEventListener('click', () => {
  const collapse = b.dataset.act === 'collapse';
  qa('.layer-group').forEach(g => g.classList.toggle('collapsed', collapse));
}));
let keyOnly = false;
qa('#tlTools button').forEach(b => b.addEventListener('click', () => {
  keyOnly = b.dataset.act === 'key';
  applyFilter();
}));

/* ---------- 标签页 ---------- */
function setTab(tab, push) {
  activeTab = tab;
  qa('.seg button').forEach(b => b.classList.toggle('on', b.dataset.view === tab));
  q('#tree').style.display = tab === 'tree' ? '' : 'none';
  q('#timeline').style.display = tab === 'timeline' ? '' : 'none';
  q('#paths').style.display = tab === 'path' ? '' : 'none';
  q('#relLegend').style.display = tab === 'tree' ? '' : 'none';
  q('#treeTools').style.display = tab === 'tree' ? '' : 'none';
  q('#tlTools').style.display = tab === 'timeline' ? '' : 'none';
  q('#pathTools').style.display = tab === 'path' ? '' : 'none';
  if (push) location.hash = tab === 'tree' ? '' : 'view=' + tab;
  try { localStorage.setItem('fojiao.tab', tab); } catch (err) {}
}
qa('.seg button').forEach(b => b.addEventListener('click', () => setTab(b.dataset.view, true)));

/* ---------- 详情面板的两个标签 ---------- */
let detailPane = 'welcome';
function setDetailPane(name, push) {
  detailPane = name;
  qa('.tabs button').forEach(b => b.classList.toggle('on', b.dataset.pane === name));
  ['welcome', 'docs', 'node'].forEach(k => {
    const el = q('#pane-' + k); if (el) el.classList.toggle('on', k === name);
  });
  if (name === 'docs' && !q('#pane-docs').dataset.done) renderDocs();
  if (push) location.hash = name === 'docs' ? 'view=docs' : (selectedId || '');
}
qa('.tabs button').forEach(b => b.addEventListener('click', () => {
  selectedId = null;
  qa('.node-row.selected, .tl-chip.on').forEach(el => el.classList.remove('selected', 'on'));
  setDetailPane(b.dataset.pane, true);
  detailEl.scrollTop = 0;
}));

const KIND_ORDER = ['经', '律', '论疏', '史料', '文献'];
const KIND_HINT = {
  '经': '佛陀的教说（含早期尼柯耶与汉译阿含）',
  '律': '僧团戒律与僧事制度',
  '论疏': '论书、注疏与宗派著作——判年代时须与「经」分开看',
  '史料': '史传、目录、碑铭与法敕',
  '文献': '其他引用条目'
};
function renderDocs() {
  const box = q('#pane-docs');
  if (!box || box.dataset.done) return;
  box.dataset.done = '1';
  let h = '<div class="welcome" style="max-width:900px"><h2>经 · 律 · 论 总览</h2>' +
    '<p>下表由各节点的「出处」自动汇总——<strong>共 ' + DOCS.length + ' 种文献</strong>。' +
    '每行给出该文献在本页被引用的次数、<b>本页的年代定位</b>、内容所属类别，' +
    '点任一行可展开所有引用它的节点。</p>' +
    '<p><b>「本页的年代定位」怎么读</b>　它取该文献在相关节点「时间 · 层积」栏中的' +
    '<b>文献定型</b>值（即该文献自身被命名、被系统整理的时间），若该栏为「不适用」才退回到' +
    '最早引用节点的<b>思想形成</b>值。</p>' +
    '<p><b>为何常出现很早的年代</b>　很多文献（尤其阿含与巴利尼柯耶）在本页的「思想形成」' +
    '被标为「约前 5 世纪」，指的是<strong>其内容所依的教说</strong>源自佛陀时代，' +
    '不是该文本的写成年代。两者相差数百年，故本表不采用前者；要精确到文本层面，' +
    '请看各节点的「文献定型」与「汉译流传」两栏。</p>' +
    '<input id="docSearch" placeholder="在文献名中检索：俱舍 / 中论 / 涅槃 / 律 / 量论" ' +
    'style="width:100%;max-width:420px;padding:6px 10px;border:1px solid var(--line);' +
    'border-radius:7px;font-family:inherit;font-size:12.5px;background:#FCFCFA;margin:0 0 14px"></div>';
  KIND_ORDER.forEach(kind => {
    const list = DOCS.filter(d => d.kind.split('/')[0] === kind);
    if (!list.length) return;
    h += '<div class="d-sec"><h3>' + esc(kind) + '（' + list.length + '）</h3>' +
      '<i>· ' + esc(KIND_HINT[kind] || '') + '</i></div>';
    h += '<table class="doc-tbl"><tr><th style="width:30%">文献</th><th style="width:10%">引用</th>' +
      '<th style="width:34%">本页的年代定位</th><th>所属</th></tr>';
    list.forEach(d => {
      h += '<tr class="doc-row" data-name="' + esc(d.name) + '"><td class="dn">' +
        esc(d.name) + '</td><td class="dc">' + d.n + '</td><td class="dw">' +
        esc(d.when || '—') + '</td><td class="dk">' + esc(d.cat) + '</td></tr>';
      h += '<tr class="doc-detail" data-for="' + esc(d.name) + '" style="display:none"><td colspan="4">' +
        d.ids.map(id => '<button class="tl-chip" data-id="' + id + '">' +
          '<i style="background:' + CATS[NODES[id].c].color + '"></i>' + esc(NODES[id].n) +
          '</button>').join(' ') + '</td></tr>';
    });
    h += '</table>';
  });
  box.innerHTML = h;
  box.querySelectorAll('.doc-row').forEach(r => r.addEventListener('click', () => {
    const d = box.querySelector('.doc-detail[data-for="' + r.dataset.name + '"]');
    if (d) d.style.display = d.style.display === 'none' ? '' : 'none';
  }));
  box.querySelectorAll('.doc-detail .tl-chip').forEach(b => b.addEventListener('click', ev => {
    ev.stopPropagation();
    setDetailPane('welcome', false);
    selectNode(b.dataset.id); scrollToRow(b.dataset.id);
  }));
  const inp = box.querySelector('#docSearch');
  inp.addEventListener('input', () => {
    const v = inp.value.trim().toLowerCase();
    box.querySelectorAll('.doc-row').forEach(r => {
      const hit = !v || r.dataset.name.toLowerCase().indexOf(v) >= 0;
      r.style.display = hit ? '' : 'none';
      if (!hit) {
        const d = box.querySelector('.doc-detail[data-for="' + r.dataset.name + '"]');
        if (d) d.style.display = 'none';
      }
    });
  });
}

/* ---------- 详情 ---------- */
detailEl = q('#pane-node');
const WELCOME = q('#pane-welcome').innerHTML;

/* 总览页上的年代说明与统计（首屏即需，故在首次渲染前注入） */
(function () {
  let sc = 0; Object.keys(NODES).forEach(id => sc += NODES[id].src.length);
  const set = (sel, v) => { const el = q(sel); if (el) el.textContent = v; };
  set('#stN', Object.keys(NODES).length);
  set('#stE', edgeN);
  set('#stS', sc);
  set('#stT', ERAS.length);
  set('#cntLayers', TREE.length + ' 层');
  set('#cntEras', ERAS.length + ' 时段');
})();

function renderDetail() {
  const n = NODES[selectedId];
  if (!n) { setDetailPane('welcome', false); return; }
  const cat = CATS[n.c], ep = EP[n.ep];
  let h = '<div class="d-head"><h2>' + esc(n.n) + '</h2>';
  if (n.en && n.en !== '—') h += '<div class="d-en">' + esc(n.en) + '</div>';
  h += '<div class="d-badges">' +
    '<span class="badge" style="background:' + cat.color + '">' + esc(cat.name) + '</span>' +
    (ep ? '<span class="badge" style="background:' + ep.color + '">' + esc(ep.name) + '</span>' : '') +
    '<span class="badge ghost">出处 ' + n.src.length + ' 条</span>' +
    '<span class="badge ghost">关联 ' + (ADJ[selectedId] || []).length + '</span></div></div>';
  h += '<div class="d-sec"><h3>释义</h3></div><div class="d-desc">' + mdIn(n.d) + '</div>';
  if (n.see && n.see.length) {
    h += '<div class="see-bar">另见：' + n.see.map(x => '<button data-id="' + x + '">' +
      esc(NODES[x].n) + '</button>').join('') + '</div>';
  }
  h += '<div class="d-sec"><h3>时间 · 层积</h3><div class="tbl">';
  ['form', 'fix', 'trans'].forEach(k => {
    if (n.tt[k]) h += '<div class="trow"><span class="tk">' + TTK[k] + '</span><span class="tv">' +
      mdIn(n.tt[k]) + '</span></div>';
  });
  if (ep) h += '<div class="trow"><span class="tk">所属层积</span><span class="tv">' +
    '<span class="ep-dot" style="background:' + ep.color + '"></span>' + esc(ep.name) +
    '　·　' + esc(ep.hint) + '</span></div>';
  if (selectedId.indexOf('doc_') === 0) {
    h += '<div class="trow"><span class="tk">关于年代</span><span class="tv">' +
      '文献节点不单列「思想形成／文献定型」——同一部经的思想源头与文本定型常相差数百年，' +
      '须在讨论它的节点里分开交代（见「04 论书层」「12 历史 · 传播」，' +
      '以及在「经律论总览」里检索该文献名）。</span></div>';
  }
  h += '</div></div>';
  if (n.src.length) {
    h += '<div class="d-sec"><h3>出处</h3><i>· ' + n.src.length + ' 条</i></div><div class="src">';
    n.src.forEach(s => {
      h += '<div class="sitem"><div class="sname">' + esc(s.t) +
        '<span class="stag" style="background:' + s.color + '">' + esc(s.tag) + '</span></div>' +
        (s.q ? '<div class="squote">' + mdIn(s.q) + '</div>' : '') + '</div>';
    });
    h += '</div>';
  }
  const adj = ADJ[selectedId] || [];
  if (adj.length) {
    h += '<div class="d-sec"><h3>关联节点</h3><i>· ' + adj.length + '</i></div><div class="rel-list">';
    adj.forEach(e => {
      const o = NODES[e.o]; if (!o) return;
      const dir = e.dir === 'out' ? '→' : '←';
      const rl = RELS[e.l] || {name: e.l, color: '#8A94A6'};
      h += '<button class="rel" data-id="' + e.o + '"><span class="dir">' + dir + '</span>' +
        '<span class="rel-name">' + esc(o.n) + '</span>' +
        '<span class="tag" style="background:' + rl.color + '">' + esc(rl.name) + '</span>' +
        (e.note ? '<span class="rn">' + esc(e.note) + '</span>' : '') + '</button>';
    });
    h += '</div>';
  }
  if (n.era && n.era !== 'none') {
    const era = ERAS.filter(x => x.id === n.era)[0];
    if (era) h += '<div class="see-bar">年表位置：<button data-act="era">' + esc(era.label) + '</button></div>';
  }
  detailEl.innerHTML = h;
  q('#tabNode').style.display = '';
  setDetailPane('node', false);
  detailEl.scrollTop = 0;
  q('#detail').scrollTop = 0;
  qa('#detail .rel, #detail .see-bar button').forEach(b => b.addEventListener('click', () => {
    if (b.dataset.act === 'era') { setTab('timeline', true); return; }
    selectNode(b.dataset.id); scrollToRow(b.dataset.id);
  }));
}

function scrollToRow(id) {
  const row = q('.node-row[data-id="' + id + '"]') ||
    q('.tl-chip[data-id="' + id + '"]');
  if (row) row.scrollIntoView({block: 'center', behavior: 'smooth'});
}
function selectNode(id) {
  if (!NODES[id]) return;
  selectedId = id;
  qa('.node-row.selected, .tl-chip.on').forEach(el => el.classList.remove('selected', 'on'));
  qa('.node-row[data-id="' + id + '"]').forEach(el => el.classList.add('selected'));
  qa('.tl-chip[data-id="' + id + '"]').forEach(el => el.classList.add('on'));
  renderDetail();
  location.hash = id;
  if (isNarrow()) {
    if (document.activeElement === searchInput) searchInput.blur();
    document.body.classList.add('detail-open');
  }
}
q('#mBack').addEventListener('click', () => {
  document.body.classList.remove('detail-open');
  detailEl.scrollTop = 0;
});


/* ---------- 学习路径（分段式读法） ---------- */
const PATHS = [
 {n:'一 · 基础路径', sub:'佛法的核心主张与理由', goal:'读完能用自己的话说明：佛教要解决什么问题、凭什么说「无我」、修行的目标是什么。', time:'约 12–15 小时',
  nodes:['four_truths','dukkha','samudaya','craving','nirodha','marga','eightfold','three_seals','impermanence','nonself_seal','nirvana','dependent_origination','twelve_links','karma','vipaka','samsara','anatta','karma_ownership','five_aggregates','thirty_seven_bodhipakkhiya'],
  texts:['《杂阿含经》卷15 第379经（转法轮经）','《相应部》56.11','《长部》22《大念处经》','《中阿含经》卷24 第98经'],
  prac:'先只做一件事：读四念处，并试着在走路时观察一次「身」与「受」。'},
 {n:'二 · 深入路径', sub:'部派论书 → 大乘两大轨道', goal:'读完能说明：缘起如何推出无自性、唯识为何要立阿赖耶识、两派究竟在争什么。', time:'约 25–30 小时',
  nodes:['councils','eighteen_schools','abhidharma','sarvastivada','sautrantika','six_causes_five_results','debate_pudgala','nagarjuna','madhyamaka','emptiness','two_truths','debate_two_truths','yogacara','vijnapti_matra','eight_consciousnesses','alaya','three_natures','paratantra','yogacara_vs_madhyamaka','hetuvidya','tathagatagarbha','debate_tathagatagarbha'],
  texts:['《俱舍论》卷1（界品）、卷6—7（根品）','《中论》卷1〈观因缘品〉、卷4〈观四谛品〉','《解深密经·一切法相品》','《成唯识论》卷1、卷8','《因明正理门论》'],
  prac:'做一次对照阅读：同一「依他起」，看《中论》与《成唯识论》各自如何界定，把分歧写成三行字。'},
 {n:'三 · 脉络路径', sub:'佛教如何从恒河传到东亚与西藏', goal:'读完能说明：为什么今天汉传以禅净为主、藏传以格鲁为主、南传保存了较早期形态。', time:'约 15–20 小时',
  nodes:['councils','ashoka','mahayana_origins','nagarjuna','yogacara','garbha_sutras','translation_history','yichang','panjiao','wushi_bajiao','wujiao_shizong','three_vehicles_one_vehicle','tiantai','huayan','sanlun','faxiang','chan','pureland','vinaya','tantra','jushe','chengshi','tangmi_tibetan','tibetan_schools','southern_tradition','huiChang_persecution','modern_studies'],
  texts:['《出三藏记集》','《开元释教录》','《高僧传》','《异部宗轮论》','《土观宗派源流》'],
  prac:'取《开元释教录》的目录，对照本页各宗条目，看译出年代与立宗年代的对应关系。'},
 {n:'四 · 实践路径', sub:'次第、方法、判准', goal:'读完能说明：止与观为何必须配合、顿与渐争的是什么、不同宗派的用功法差别在哪。', time:'约 20 小时',
  nodes:['three_refuges','five_precepts','vinaya_rites','three_trainings','sila','samadhi_training','prajna','four_foundations','samatha_vipassana','four_dhyanas','thirty_seven_bodhipakkhiya','sravaka_fruits','five_paths','bodhisattva_path','six_paramitas','four_immeasurables','four_attractions','chan_methods','buddha_name','two_paths_two_powers','mandala','three_mysteries','four_reliances','historical_layers'],
  texts:['《清净道论》〈说戒品〉〈说定品〉〈说慧品〉','智顗《摩诃止观》（选读）','《瑜伽师地论》〈声闻地〉','《菩提道次第广论》（科目）','《大般涅槃经》卷6（四依）'],
  prac:'按《大念处经》的「身念处」做一次二十分钟的入出息念；再读《默照铭》与《大慧书》各一段，比较两种用功法。'},
];

/* ---------- 总览页上的主线链 ---------- */
qa('#pane-welcome .chain a, #mGuide .chain a').forEach(a => a.addEventListener('click', ev => {
  ev.preventDefault(); selectNode(a.dataset.id);
}));
qa('#pane-welcome [data-id], #mGuide [data-id]').forEach(el => {
  if (el.tagName === 'A' && el.closest('.chain')) return;
  el.addEventListener('click', () => selectNode(el.dataset.id));
});

/* ---------- 启动 ---------- */
(function () {
  // 先建可交互内容（学习路径的节点标签、文献总览表），再定初始视图
  buildPathCards();
  renderDocs();
  const h = decodeURIComponent(location.hash.replace(/^#/, ''));
  let tab = 'tree';
  try { tab = localStorage.getItem('fojiao.tab') || 'tree'; } catch (err) {}
  if (h === 'view=timeline') tab = 'timeline';
  if (h === 'view=path') tab = 'path';
  setTab(tab, false);
  if (h === 'view=docs') { setDetailPane('docs', false); }
  else if (h && h.indexOf('view=') !== 0 && NODES[h]) selectNode(h);
  else { setDetailPane('welcome', false); }
})();
window.addEventListener('hashchange', () => {
  const h = decodeURIComponent(location.hash.replace(/^#/, ''));
  if (h === 'view=docs') { selectedId = null; setDetailPane('docs', false); return; }
  if (h === 'view=timeline' || h === 'view=path') { setTab(h.slice(5), false); return; }
  if (h && NODES[h] && h !== selectedId) selectNode(h);
});
''' + r'''
window.addEventListener('load', function () {
  const w = q('.welcome');
  const box = q('#mGuide .mg-body');
  if (w && box) {
    const clone = w.cloneNode(true);
    const walker = document.createTreeWalker(clone, NodeFilter.SHOW_TEXT);
    let t;
    while ((t = walker.nextNode())) t.nodeValue = t.nodeValue.split('左侧').join('上方');
    box.appendChild(clone);
  }
});
'''

# ============================================================
# 7. 组装页面
# ============================================================
_orig_meta = META_NOTE
_orig_meta = _orig_meta.replace(
    '本页剔除评判性内容（如「佛教的漏洞与争议」一类段落），仅保留理论结构、释义、文献出处与年代；'
    '宗派之间对部分概念（如如来藏、二谛、无为法）存在不同解释，页内已标明分歧所在，读者可另行参考。',
    '本页不作教义评判，仅收录理论结构、释义、文献出处与年代；'
    '宗派之间对部分概念（如如来藏、二谛、无为法、戒体）的解释互有出入，'
    '页内于相应节点标明分歧所在，并另设「论诤」类节点与「对辨」类关系专门记录，读者可据此自行参校。')
_orig_meta = _orig_meta.replace(
    '佛陀生卒年有南传（前624—前544）、汉传（前565—前486）、现代学界（约前480—前400）三说，'
    '本页统一以「约前 5 世纪」起算，不取单一说法。',
    '佛陀生卒年有南传（前624—前544）、汉传（前565—前486）、现代学界（约前480—前400）三说；'
    '本页统一自「约前 5 世纪」起算，不取一说。')

META_NOTE_FULL = _orig_meta.replace('</div>', '') + (
 '<br><br><b>关于层积标注</b>　本页于早期层、发展层、民间层、元层积之外增设「近世层」'
 '（近现代的研究方法与实践形态）。该层与前四层同属关于教义如何被整理、研究与延续的层次，'
 '而非教义本身。第十二层「历史 · 传播」所收汉译史、藏译史、南传史及学界讨论，'
 '性质属文献的流传与研究，不宜与前十一层的教义内容混同看待。'
 '<br><br><b>关于许可</b>　本页内容以 CC BY 4.0 发布，<b>欢迎转载、翻译、改编与再分发（含商业用途），'
 '无须事先征得同意</b>，注明出处并附本仓库链接即可；代码部分为 MIT。'
 '本页为单文件，可直接另存分享，也可离线使用。</div>')

def chain_html():
    """01—07 为一行（主线七环）；换行后列出修行实践与历史 · 传播，并注明二者非接续环节。"""
    out, num = [], 0
    for i, (name, sub, color) in enumerate(CHAIN_NODES):
        if i == 7:
            out.append('<div class="chain-break"></div>')
            out.append('<div class="chain-side">贯穿视角</div>')
        num += 1
        out.append('<div class="cstep"><span class="cn" style="background:%s">%02d</span>'
                   '<span class="ct">%s<em>%s</em></span></div>'
                   % (color, num, esc_html(name), esc_html(sub)))
        lb = CHAIN_ARROWS[i]
        if lb is not None:
            out.append('<div class="car"><span class="ar">\u2192</span>'
                       '<span class="lb">%s</span></div>' % esc_html(lb))
    return ''.join(out)

def esc_html(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

WELCOME_NEW = '''<div class="welcome">
  <h2>体系总览</h2>
  <p>本页将佛教基础理论组织为<strong>十二层</strong>与一条<strong>由问题到体系</strong>的主线。主线九项依次为：四圣谛、三法印、缘起 · 业果、部派 · 阿毗达磨、中观 · 唯识、如来藏、判教 · 十宗，另设修行实践与历史 · 传播两层；后两层不在主线上，而是贯穿全页的两个视角——前者为教理在行持上的落实，后者为文本与宗派在历史上的形成过程。</p>
  <p>主线各环之间为承接关系：四圣谛确定问题所在，三法印给出判定教说的标准，缘起 · 业果展开其原理，部派佛教将原理整理为论书体系，大乘由此开出中观与唯识两大轨道，如来藏为「何故能成佛」补足依据，判教与十宗则把上述内容组织为宗派的体系。</p>
  <div class="chain">__CHAIN__</div>
  <p style="margin-top:12px">左栏三个视图：<b>目录</b>为十二层结构树，可按关系类型筛选；<b>年表</b>按九个时段排列，用于检视发展线索；<b>学习路径</b>提供四条自基础至实践的读法。右侧两个标签页：<b>总览</b>（本条及其下的修订说明、阅读路径与关系类型）与<b>经律论总览</b>（151 种文献的检索表）。</p>
  <div class="guide">
    __GUIDE_REV__
    __GUIDE_USE__
    __GUIDE_GLOSS__
  </div>
  <div class="meta-note" id="metaNote">__META_FULL__</div>
</div>'''

WELCOME_NEW = (WELCOME_NEW.replace('__META_FULL__', META_NOTE_FULL)
                          .replace('__CHAIN__', chain_html())
                          .replace('__GUIDE_REV__', GUIDE_REV)
                          .replace('__GUIDE_USE__', GUIDE_USE)
                          .replace('__GUIDE_GLOSS__', GUIDE_GLOSS))

PAGE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>佛教基础理论 · 结构树（第二版：结构 · 释义 · 出处 · 年表）</title>
<style>__CSS__</style>
</head>
<body>

<header>
  <h1>佛教基础理论 · 结构树
    <span>十二层主线 + 部派阿毗达磨 + 印度大乘 + 汉传十宗 + 藏传南传　·　每个概念附释义、出处引文与年代考订</span>
  </h1>
  <div class="sub">
    <span><span class="k">节点</span> <b id="stN">—</b></span>
    <span><span class="k">关系</span> <b id="stE">—</b>（规范为 10 类）</span>
    <span><span class="k">出处引证</span> <b id="stS">—</b> 条</span>
    <span><span class="k">年表时段</span> <b id="stT">—</b> 段</span>
    <span class="k">检索范围：名称 / 梵巴原语 / 释义 / 所引经论名（可输《俱舍论》或《中论》试）</span>
  </div>
</header>

<div class="m-back" id="mBack"><span class="ar">←</span>返回目录</div>

<div class="main">
  <aside class="outline">
    <div class="o-top">
      <input id="search" type="text" placeholder="搜索：缘起 / 阿赖耶识 / 如来藏 / 俱舍论" autocomplete="off">
      <div class="seg">
        <button data-view="tree" class="on">目录<span class="cnt" id="cntLayers">—</span></button>
        <button data-view="timeline">年表<span class="cnt" id="cntEras">—</span></button>
        <button data-view="path">学习路径<span class="cnt">4 条</span></button>
      </div>
      <div class="search-info" id="searchInfo"></div>
    </div>
    <div class="o-body">
      <div id="relLegend" class="rel-legend"></div>
      <div class="tree-tools" id="treeTools">
        <button data-act="expand">展开全部</button>
        <button data-act="collapse">收起全部</button>
        <span style="color:var(--ink4)">点关系色标＝只看该类（再点一次还原）</span>
      </div>
      <div class="tree-tools" id="pathTools" style="display:none">
        <span style="color:var(--ink4)">四条读法：基础 → 深入 → 脉络 → 实践</span>
      </div>
      <div class="tree-tools" id="tlTools" style="display:none">
        <button data-act="key">只看重点节点</button>
        <button data-act="all">显示全部</button>
        <span style="color:var(--ink4)">年表按时段分组，粗体为重点</span>
      </div>
      <div id="tree"></div>
      <div id="timeline" style="display:none"></div>
      <div id="paths" style="display:none"></div>
      <details class="m-guide" id="mGuide">
        <summary>总览 · 主线是怎么串起来的</summary>
        <div class="mg-body"></div>
      </details>
    </div>
  </aside>

  <main class="detail" id="detail">
    <div class="tabs">
      <button data-pane="welcome" class="on">总览</button>
      <button data-pane="docs">经律论总览</button>
      <button data-pane="node" id="tabNode" style="display:none">节点详情</button>
    </div>
    <div class="pane on" id="pane-welcome">__WELCOME_INNER__</div>
    <div class="pane" id="pane-docs"></div>
    <div class="pane" id="pane-node"></div>
  </main>
</div>

<script>window.BUDDHISM_DATA = __DATA__;</script>
<script>
__JS__
</script>
</body>
</html>
'''

page = (PAGE.replace('__CSS__', CSS)
            .replace('__DATA__', json.dumps(dict(
                nodes=JS_NODES, tree=JS_TREE, edges=E, rels=JS_RELS, cats=JS_CATS,
                epochs=JS_EPS, eras=JS_ERAS, ttk=TTK), ensure_ascii=False))
            .replace('__JS__', JS)
            .replace('__DOCS__', json.dumps(DOCS, ensure_ascii=False))
            .replace('__WELCOME_INNER__', WELCOME_NEW)
            .replace('META_NOTE_PLACEHOLDER', ''))

# 总览页的 meta-note 使用完整版说明

# 双语页面由 render.py 生成（中文 index.html、英文 en.html）
sys.path.insert(0, os.path.join(ROOT, 'build'))
import make_pages
make_pages.main()
import make_seo_files
make_seo_files.main()
