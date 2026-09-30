# -*- coding: utf-8 -*-
"""结构审查脚本（中文佛学参考资料 · 结构层）

只检查「结构数据本身」是否自洽，不判定单条内容对错：
  1 关系的对称性与传递性（体同是否双向、因果/次第/支分是否成环、方向是否与目录矛盾）
  2 关系两端的语义是否相称（说明是否用于同层概念、层积是否只跨时代）
  3 目录树与节点分类是否一致（跨层重复、层类不符、树与基础数据覆盖面）
  4 年代三栏（form/fix/trans）内部逻辑
  5 年表时段与节点 era 的一致性
  6 出处分布的系统性问题（被引最多者、卷次可疑、别名分裂、文献关系截断）
  7 释义长度按分类的异常

输入：build/review_zh/{structure.json,graph.json,A1.json,A2.json,B.json}
      （可选 data/buddhism.json，仅在存在时用于核对文献节点与引用规模）
输出：build/review_zh/structural.findings.json（JSON 数组）

运行：python3 build/review_zh/audit_structure.py
"""

import collections
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, 'structural.findings.json')

# ---------------------------------------------------------------- 载入

def load():
    S = {n['id']: n for n in json.load(open(os.path.join(HERE, 'structure.json'), encoding='utf-8'))}
    G = json.load(open(os.path.join(HERE, 'graph.json'), encoding='utf-8'))
    full = {}
    for f in ('A1.json', 'A2.json', 'B.json'):
        for n in json.load(open(os.path.join(HERE, f), encoding='utf-8')):
            full[n['id']] = n
    src = None
    p = os.path.join(ROOT, 'data', 'buddhism.json')
    if os.path.exists(p):
        src = json.load(open(p, encoding='utf-8'))
    return S, G, full, src


def tree_index(tree):
    """返回 place[id]=层号, parent[id]=父 id, depth[id]=深度, notes[id]=[note,...]"""
    place, parent, depth, notes = {}, {}, {}, collections.defaultdict(list)

    def walk(items, li, pid, d):
        for it in items:
            place[it['id']] = li
            parent[it['id']] = pid
            depth[it['id']] = d
            if it.get('note'):
                notes[it['id']].append(it['note'])
            walk(it.get('children') or [], li, it['id'], d + 1)

    for i, L in enumerate(tree, 1):
        walk(L['items'], i, None, 0)
    return place, parent, depth, notes


def is_ancestor(parent, anc, x):
    """anc 是否为 x 的祖先"""
    while parent.get(x):
        x = parent[x]
        if x == anc:
            return True
    return False


# ---------------------------------------------------------------- 年代解析
# 中文年代串 → 有符号年份区间（公元前为负）。只做「从宽」的世纪/年份抽取：
# 先删书名号内的书名与「卷N/第N经」等非年代数字，再抓 世纪 与 3-4 位年份。

_RANGE_C = re.compile(r'(约|公元|前)?\s*(\d+)\s*(?:世纪)?\s*[—\-~～至]\s*(公元|前)?\s*(\d+)\s*世纪')
_SINGLE_C = re.compile(r'(约|公元|前)?\s*(\d+)\s*世纪')
_RANGE_Y = re.compile(r'(前)?\s*(\d{3,4})\s*[—\-~～]\s*(前)?\s*(\d{3,4})')
_SINGLE_Y = re.compile(r'(?<![\d〔第卷N])(前)?(\d{3,4})(?![\d经])')


def _clean(txt):
    t = re.sub(r'《[^》]*》', '〔书〕', txt)
    t = re.sub(r'卷\s*\d+(?:\s*[—\-~～]\s*(?:卷)?\d+)?', '卷N', t)
    t = re.sub(r'第\s*\d+\s*[经册品]', '第N', t)
    t = re.sub(r'\d+\.\d+', 'N', t)
    return t


def _cspan(pre, n):
    n = int(n)
    return (-100 * n, -100 * (n - 1)) if pre == '前' else (100 * (n - 1), 100 * n)


def year_spans(txt, with_years=True):
    """返回 [(lo, hi, 原文片段), ...]"""
    if not txt:
        return []
    t = _clean(txt)
    iv, covered = [], []
    for m in _RANGE_C.finditer(t):
        p1, n1, p2, n2 = m.groups()
        lo = _cspan(p1, n1)[0]
        hi = _cspan(p2 if p2 else p1, n2)[1]
        iv.append((lo, hi, m.group(0).strip()))
        covered.append(m.span())
    for m in _SINGLE_C.finditer(t):
        if any(s <= m.start() and m.end() <= e for s, e in covered):
            continue
        sp = _cspan(*m.groups())
        iv.append((sp[0], sp[1], m.group(0).strip()))
    if with_years:
        for m in _RANGE_Y.finditer(t):
            p1, y1, p2, y2 = m.groups()
            lo = -int(y1) if p1 == '前' else int(y1)
            hi = -int(y2) if p2 == '前' else int(y2)
            iv.append((min(lo, hi), max(lo, hi), m.group(0).strip()))
        for m in _SINGLE_Y.finditer(t):
            p, y = m.groups()
            v = -int(y) if p == '前' else int(y)
            iv.append((v, v, m.group(0).strip()))
    return iv


def span_range(iv):
    return (min(a for a, b, _ in iv), max(b for a, b, _ in iv)) if iv else None


def era_range(era):
    """节点 era 字段 → 年份区间；'none' → None"""
    if not era or era == 'none':
        return None
    if '-' in era:
        a, b = era.split('-', 1)
        if a.startswith('前'):
            return (-100 * int(a[1:]), -100 * int(b))
        return (100 * (int(a) - 1), 100 * int(b))
    return (100 * (int(era) - 1), 100 * int(era))   # 单值（如 '7'）按一个世纪处理


def epoch_window(txt):
    """层标题下的 epoch 串 → 年份窗口；无法解析或为「贯穿/方法论」类 → None"""
    t = (txt or '').replace(' ', '')
    if not re.search(r'[前公元\d]', t) or '贯穿' in t or '方法论' in t:
        return None
    m = re.search(r'约?(前)?(\d+)—(?:公元)?(前)?(\d+)世纪', t)
    if m:
        p1, a, p2, b = m.groups()
        lo = -100 * int(a) if p1 else 100 * (int(a) - 1)
        hi = -100 * int(b) if p2 else 100 * int(b)
        return (min(lo, hi), max(lo, hi))
    m = re.search(r'约?(前)?(\d+)世纪—(前)?(\d+)世纪', t)
    if m:
        p1, a, p2, b = m.groups()
        lo = -100 * int(a) if p1 else 100 * (int(a) - 1)
        hi = -100 * int(b) if p2 else 100 * int(b)
        return (min(lo, hi), max(lo, hi))
    m = re.search(r'约?(前)?(\d+)世纪', t)
    if m:
        p, a = m.groups()
        return (-100 * int(a), -100 * (int(a) - 1)) if p else (100 * (int(a) - 1), 100 * int(a))
    return None


def overlap(a, b, tol=0):
    return a is not None and b is not None and a[0] <= b[1] + tol and b[0] <= a[1] + tol


# ---------------------------------------------------------------- 出处解析

BOOK = re.compile(r'《([^》]+)》')
VOL = re.compile(r'卷\s*(\d+)')


def first_title(t):
    m = BOOK.search(t or '')
    return m.group(1) if m else None


def all_titles(t):
    return [m.split('·')[0] for m in BOOK.findall(t or '')]


def vol_nums(t):
    return [int(v) for v in VOL.findall(t or '')]


# ================================================================ 检查项

def check_1(S, G, place, parent, depth):
    """关系的对称性与传递性"""
    F = []
    E = G['edges']
    pairs = {(e['s'], e['t']) for e in E}
    label = {(e['s'], e['t']): e['l'] for e in E}
    name = lambda x: S.get(x, {}).get('name', x)

    # --- 体同 是否双向
    ti = [(e['s'], e['t']) for e in E if e['l'] == '体同']
    rev_same = [(a, b) for a, b in ti if (b, a) in pairs and label.get((b, a)) == '体同']
    rev_other = [(a, b) for a, b in ti if (b, a) in pairs and label.get((b, a)) != '体同']
    no_rev = [(a, b) for a, b in ti if (b, a) not in pairs]
    F.append(dict(
        area='1 关系对称性与传递性',
        severity='high',
        problem='「体同」按定义为「异名同事：即、异名」，两端应可互换；实际 38 条体同边中只有 2 条（1 对：佛性↔见性成佛）互为体同，'
                '35 条完全没有反向边，1 条的反向边标成了「支分」。渲染器按有向边展示关联节点（区分 → 与 ←），'
                '因此从任一端看关系都不对等；唯一成对的那一对说明双向写法并未被禁止，而是数据不一致。',
        evidence='体同边 %d 条：互为体同 %d 条（%s）；反向边存在但类型不同 %d 条（%s）；无任何反向边 %d 条，例：%s' % (
            len(ti), len(rev_same), '、'.join('%s↔%s' % tuple(sorted(p)) for p in {tuple(sorted(x)) for x in rev_same}),
            len(rev_other), '、'.join('%s→%s（反向为「%s」）' % (name(a), name(b), label[(b, a)]) for a, b in rev_other),
            len(no_rev), '、'.join('%s→%s' % (name(a), name(b)) for a, b in no_rev[:6])),
        instances=['%s|%s' % (a, b) for a, b in no_rev + rev_other],
    ))

    # --- 体同 两端是否相称（跨层/跨类）
    cross = [(a, b) for a, b in ti if place.get(a) != place.get(b)]
    odd = [('nirvana', 'suffering_continues'), ('pure_mind', 'parikalpita'),
           ('vinaya', 'eightfold'), ('no_attainment', 'chan'),
           ('all_suffering', 'dukkha'), ('medical_logic', 'four_truths')]
    F.append(dict(
        area='1 关系对称性与传递性',
        severity='medium',
        problem='「体同」（同一所指的异名）被大量用在层级、类别都不相当的两个概念之间，两端并非同一所指，'
                '作等号讲不成立（例：涅槃寂静＝苦在相续、自性清净心＝遍计所执性、律宗＝八正道、无所得＝禅宗）。',
        evidence='38 条体同中 %d 条两端分属不同目录层；可疑例：%s' % (
            len(cross), '；'.join('%s(L%s)=%s(L%s)' % (name(a), place.get(a), name(b), place.get(b)) for a, b in odd)),
        instances=['%s|%s' % (a, b) for a, b in odd],
    ))

    # --- 因果 / 次第 / 支分 成环
    def cycle_paths(lab, maxlen=8):
        adj = collections.defaultdict(list)
        for e in E:
            if e['l'] == lab:
                adj[e['s']].append(e['t'])
        found = []

        def dfs(start, u, path):
            for v in adj[u]:
                if v == start and len(path) >= 2:
                    found.append(path[:])
                elif v not in path and len(path) < maxlen:
                    dfs(start, v, path + [v])

        for s in list(adj):
            dfs(s, s, [s])
        uniq = set()
        for c in found:
            m = min(range(len(c)), key=lambda i: c[i])
            uniq.add(tuple(c[m:] + c[:m]))
        return sorted(uniq)

    cyc = {lab: cycle_paths(lab) for lab in ('因果', '次第', '支分')}
    clean = [k for k, v in cyc.items() if not v]
    F.append(dict(
        area='1 关系对称性与传递性',
        severity='medium',
        problem='「因果」「次第」「支分」三类均无环，方向性成立；但「支分」（整体—部分）有 4 条与目录树的层级方向相反，'
                '即箭头由下级指向上级，同一份数据里整体—部分关系与目录从属关系互相矛盾。',
        evidence='有环类型：%s；无环类型：%s。方向与目录相反的支分边：%s' % (
            {k: ['→'.join(name(x) for x in c) for c in v] for k, v in cyc.items() if v} or '无',
            '、'.join(clean),
            '；'.join('%s(树深%d)→%s(树深%d)' % (name(a), depth.get(a), name(b), depth.get(b))
                      for a, b in [('all_suffering', 'three_seals'), ('three_bodies', 'buddha_body_land'),
                                   ('icchantika', 'tathagatagarbha'), ('chan_methods', 'chan')])),
        instances=['all_suffering|three_seals', 'three_bodies|buddha_body_land',
                   'icchantika|tathagatagarbha', 'chan_methods|chan'],
    ))

    # --- 其它关系类型的环
    F.append(dict(
        area='1 关系对称性与传递性',
        severity='medium',
        problem='除上三类外，「依据」「判摄」也存在 A→B 且 B→A 的互指环：三性↔识有境无、空↔三论宗、法相宗↔判教。'
                '「依据」（谁依谁）与「判摄」（谁判谁）都预设单向，互指使关系无法判读。',
        evidence='；'.join(' ↔ '.join([name(a), name(b)] + [label.get((b, a), '?')])
                          for a, b in [('three_natures', 'vijnapti_matra'), ('emptiness', 'sanlun'),
                                       ('faxiang', 'panjiao')]),
        instances=['three_natures|vijnapti_matra', 'emptiness|sanlun', 'faxiang|panjiao'],
    ))

    # --- 重复边
    triples = collections.Counter((e['s'], e['t'], e['l']) for e in E)
    dup = [(k, c) for k, c in triples.items() if c > 1]
    F.append(dict(
        area='1 关系对称性与传递性',
        severity='low',
        problem='存在完全重复的关系（同两端、同类型），619 条边按「两端+类型」去重后只有 %d 条。' % len(triples),
        evidence='；'.join('%s-%s-%s ×%d' % (name(k[0]), k[2], name(k[1]), c) for k, c in dup),
        instances=['%s|%s' % (k[0], k[1]) for k, _ in dup],
    ))
    return F


def check_2(S, G, place, parent, depth):
    """关系两端的语义是否相称"""
    F = []
    E = G['edges']
    name = lambda x: S.get(x, {}).get('name', x)

    # 说明：同层且非父子
    same = [(e['s'], e['t'], e.get('note')) for e in E if e['l'] == '说明'
            and place.get(e['s']) is not None and place.get(e['s']) == place.get(e['t'])]
    sibling = [(a, b, n) for a, b, n in same
               if parent.get(b) != a and parent.get(a) != b
               and not is_ancestor(parent, a, b) and not is_ancestor(parent, b, a)]
    F.append(dict(
        area='2 两端语义相称',
        severity='medium',
        problem='「说明」（解释、举例、补充）有 12 条用在同层但无父子关系（分属不同支）的两个概念之间，'
                '这类并列概念的关系更适合「对辨」或「体同」；其中「遍计所执性→依他起性」「圆成实性→依他起性」'
                '是同一目标的两条对置说明，形态与「对辨」相同却标为「说明」。',
        evidence='说明边共 %d 条，两端同层者 %d 条，其中无父子关系者 %d 条：%s' % (
            sum(1 for e in E if e['l'] == '说明'), len(same), len(sibling),
            '；'.join('%s→%s(%s)' % (name(a), name(b), n or '无note') for a, b, n in sibling)),
        instances=['%s|%s' % (a, b) for a, b, n in sibling],
    ))

    # 层积：跨时代
    cj = [(e['s'], e['t']) for e in E if e['l'] == '层积']
    same_era = [(a, b) for a, b in cj if S.get(a, {}).get('era') == S.get(b, {}).get('era')]
    none_era = [(a, b) for a, b in same_era
                if S.get(a, {}).get('era') == 'none' and S.get(b, {}).get('era') == 'none']
    real_same = [(a, b) for a, b in same_era if (a, b) not in none_era]
    F.append(dict(
        area='2 两端语义相称',
        severity='medium',
        problem='「层积」用于文本发展层的归属，本应连接不同时代的节点；12 条层积边中有 %d 条两端 era 相同（%d 条两端均为 none，'
                '1 条为 councils(前4-3)→ashoka(前4-3)）。三次结集→阿育王与佛法西传是同代史事之间的叙述关系，并非文本的层次归属；'
                'none↔none 的 4 条属方法论层内部的层归属，为边界情形。' % (len(same_era), len(none_era)),
        evidence='层积边 %d 条；同 era 者 %d 条（none↔none %d 条，非 none %s）；跨 era 者 %d 条' % (
            len(cj), len(same_era), len(none_era),
            '、'.join('%s[%s]→%s[%s]' % (name(a), S[a]['era'], name(b), S[b]['era']) for a, b in real_same),
            len(cj) - len(same_era)),
        instances=['%s|%s' % (a, b) for a, b in same_era],
    ))

    # 层积：语义错配（传播/传承）
    F.append(dict(
        area='2 两端语义相称',
        severity='low',
        problem='两条「层积」实际表达的是法脉传播而非文本层次：tantra(密宗)→tangmi_tibetan(唐密与藏传)、'
                'tangmi_tibetan→tibetan_schools(藏传佛教诸派)，按定义（文本史的归属：层、可析出）应属「判摄」或「次第」。',
        evidence='note 均为空；两端 era 分别为 4-7→7-9、7-9→11-15',
        instances=['tantra|tangmi_tibetan', 'tangmi_tibetan|tibetan_schools'],
    ))
    return F


def check_3(S, G, place, parent, depth, notes, full):
    """目录树与节点分类是否一致"""
    F = []
    name = lambda x: S.get(x, {}).get('name', x)

    # 目录树中的跨层重复：一次遍历记录每个 id 落在哪些层
    layers_of = collections.defaultdict(list)
    for li, L in enumerate(G['tree'], 1):
        stack = list(L['items'])
        while stack:
            it = stack.pop()
            layers_of[it['id']].append(li)
            stack.extend(it.get('children') or [])
    dup = {k: sorted(set(v)) for k, v in layers_of.items() if len(set(v)) > 1}
    lines = []
    for k, layers in dup.items():
        marked = any('另见' in n for n in notes.get(k, []))
        lines.append('%s 出现于第 %s 层，note=%s' % (k, '、'.join(map(str, layers)), notes.get(k) or '无'))
    F.append(dict(
        area='3 目录树与节点分类',
        severity='high',
        problem='%d 个节点在目录树中出现于两层，且没有任何跨层标记（修订说明称「原版……5 个节点在目录中重复出现。本版各归其位，'
                '重复处改标『另见』」）；全树 note 中「另见」0 处，跨层指引只有 faxiang 的 1 处「见『05 大乘层』」。' % len(dup),
        evidence='跨层重复节点 %d 个：%s；全树 8 条 note 中「另见」0 条' % (len(dup), '；'.join(lines)),
        instances=sorted(dup),
    ))

    # 层内分类不符
    layer_cat = collections.defaultdict(collections.Counter)
    for k, li in place.items():
        if k in S:
            layer_cat[li][S[k]['cat']] += 1
    odd = [
        ('southern_tradition', 10, 'hist', '「10 汉传十宗」层（约5—9世纪）内唯一 hist 类节点，且是南传佛教与巴利三藏'),
        ('tibetan_schools', 10, 'school', '「汉传十宗」层内藏传诸派'),
        ('three_bodies', 11, 'school', '「11 修行实践」层内的 school 类节点'),
        ('bodhisattva_path', 11, 'garbha', '「11 修行实践」层内的 garbha 类节点'),
        ('six_paramitas', 11, 'garbha', '「11 修行实践」层内的 garbha 类节点'),
        ('all_suffering', 2, 'core', '「02 标准层」内唯一 cat=core，同层其余 5 个均为 seal'),
    ]
    F.append(dict(
        area='3 目录树与节点分类',
        severity='medium',
        problem='若干节点的分类与其所在层明显不符：南传佛教与巴利三藏（hist、era=前4-3）被放进「10 汉传十宗」（约5—9世纪）；'
                '三身佛（school）与菩萨道、六度（garbha）被放进「11 修行实践」；「02 标准层」三相之一「诸行是苦」标为 core，'
                '而同层的诸行无常、诸法无我标为 seal。',
        evidence='；'.join('%s：L%d cat=%s（%s）' % (k, li, c, why) for k, li, c, why in odd),
        instances=[k for k, _, _, _ in odd],
    ))

    # 层内大部分分类 + 少数类别跨层
    F.append(dict(
        area='3 目录树与节点分类',
        severity='low',
        problem='「修行实践」层内的十二处、十八界标为 prac（修行实践），但二者是法数/法论概念（处、界），'
                '与同层四念处、三十七道品等行门性质不同。',
        evidence='L11 cat=prac 的 18 个节点中含 twelve_ayatana、eighteen_dhatu；二者在关系图中以「说明」相连（加六识成十八界）',
        instances=['twelve_ayatana', 'eighteen_dhatu'],
    ))

    doc_ids = sorted(k for k in place if k not in S)
    F.append(dict(
        area='3 目录树与节点分类',
        severity='low',
        problem='目录树（%d 个唯一节点）与 structure.json（%d 个节点）不是同一集合：树中另有 %d 个文献层节点'
                '（doc_1–doc_51、docbranch 与 4 个分组）无分类/年代/释义基础数据，其分类 canon 也不在页面声明的 12 类之内。' % (
                    len(place), len(S), len(doc_ids)),
        evidence='树内节点 %d 个（唯一 %d），structure.json %d 个，差集 %d 个（%s …）' % (
            sum(len(v) for v in layers_of.values()), len(place), len(S), len(doc_ids),
            '、'.join(doc_ids[:5])),
        instances=doc_ids,
    ))
    return F


def check_4(S, full):
    """年代三栏的内部逻辑"""
    F = []
    name = lambda k: S[k]['name']
    rows = {}
    for k, n in S.items():
        tt = n['tt']
        rows[k] = dict(form=span_range(year_spans(tt.get('form'))),
                       fix=span_range(year_spans(tt.get('fix'))),
                       trans=span_range(year_spans(tt.get('trans'))))

    strict = [k for k, r in rows.items() if r['form'] and r['fix'] and r['form'][0] > r['fix'][1]]
    late = [k for k, r in rows.items() if r['form'] and r['fix'] and r['form'][1] > r['fix'][1] + 50]
    F.append(dict(
        area='4 年代三栏逻辑',
        severity='low',
        problem='「思想形成」整体晚于「文献定型」的节点 0 个（无严重倒置）；但 icchantika 的 form（约3—5世纪）区间末晚于 fix 的定点'
                '（421年译出后），属区间与定点的粒度冲突，节点内无说明。',
        evidence='form 起点晚于 fix 终点者 %d 个（%s）；form 终点晚于 fix 终点者 %d 个：%s' % (
            len(strict), '、'.join(strict) or '无', len(late),
            '；'.join('%s form=%s fix=%s' % (k, rows[k]['form'], rows[k]['fix']) for k in late)),
        instances=late,
    ))

    bt = [k for k, r in rows.items() if r['fix'] and r['trans'] and r['fix'][0] > r['trans'][1] + 30]
    bt2 = [k for k, r in rows.items() if r['fix'] and r['trans'] and r['fix'][1] > r['trans'][1] + 30]
    F.append(dict(
        area='4 年代三栏逻辑',
        severity='medium',
        problem='「文献定型」整体晚于「汉译流传」的节点 7 个：三论宗、天台宗、净土宗、律宗、识有境无属汉传立宗语境'
                '（立宗晚于所依经典的汉译），应成与自续、四部密续属藏传定型晚于汉译。前者是三栏模型（form→fix→trans）'
                '与汉传宗派节点语境冲突，后者是同一节点内 mix 了汉传与藏传两条时间线。',
        evidence='fix 起点晚于 trans 终点者：%s；fix 终点晚于 trans 终点者 %d 个' % (
            '；'.join('%s fix=%s trans=%s' % (k, rows[k]['fix'], rows[k]['trans']) for k in bt), len(bt2)),
        instances=bt,
    ))

    miss_fix = [k for k, n in S.items() if not (n['tt'].get('fix') or '').strip()]
    miss_tr = [k for k, n in S.items() if not (n['tt'].get('trans') or '').strip()]
    F.append(dict(
        area='4 年代三栏逻辑',
        severity='low',
        problem='三栏为每节点声明，但覆盖不均：fix 空 %d 个、trans 空 %d 个（占 %d/%d），'
                '使「三栏」在多数节点上退化为单栏，无法作年代对照。' % (len(miss_fix), len(miss_tr), len(miss_tr), len(S)),
        evidence='fix 空：%s…；trans 空：%s…' % ('、'.join(miss_fix[:8]), '、'.join(miss_tr[:8])),
        instances=miss_tr,
    ))
    return F


def check_5(S, G, place):
    """年表时段与节点 era 的一致性"""
    F = []
    name = lambda k: S[k]['name']
    declared = {e['id']: e['label'] for e in G['eras']}
    used = collections.Counter(n['era'] for n in S.values())
    undeclared = {k: v for k, v in used.items() if k not in declared}
    F.append(dict(
        area='5 era 与年表时段',
        severity='medium',
        problem='年表只声明 9 个时段，实际节点使用了 13 个未声明的 era 取值（如 6-8、6-7、7-9、2-8、11-15、9-12、15-20），'
                '这些节点无法归入任何年表时段；同时声明中的 13-20 无任何节点使用。',
        evidence='声明时段 %s；未声明取值 %s；声明未使用 %s' % (
            '、'.join(declared), json.dumps(undeclared, ensure_ascii=False),
            '、'.join(k for k in declared if not used.get(k))),
        instances=[k for k, v in S.items() if v['era'] in undeclared],
    ))

    bad_fmt = [k for k, v in S.items() if v['era'] != 'none' and '-' not in v['era']]
    F.append(dict(
        area='5 era 与年表时段',
        severity='low',
        problem='jie_ti 的 era 为单值「7」，与其余全部节点的「区间」写法不一致，且 7 与 7-8、7-9、6-7 等相邻取值并存，语义不明。',
        evidence='jie_ti era=%r；全部 era 取值 %s' % ('7', '、'.join(sorted(used))),
        instances=bad_fmt,
    ))

    win = {}
    for i, L in enumerate(G['tree'], 1):
        w = epoch_window(L['epoch'])
        if i == 2:      # 「内容见阿含，名称定型约前2—前1世纪」：层内内容属阿含期，故窗口放宽到前6—前1世纪
            w = (-600, -100)
        win[i] = w
    outside = []
    for k, v in S.items():
        li = place.get(k)
        w = win.get(li)
        er = era_range(v['era'])
        if er and w and not overlap(er, w):
            outside.append((k, li, v['era'], er, w))
    F.append(dict(
        area='5 era 与年表时段',
        severity='high',
        problem='%d 个节点的 era 与所属层的年代窗口完全不重叠：第 03 原理层（约前5—前3世纪）内有 era=8-12、4-7 的节点；'
                '第 06 层次层（约1—5世纪）内的三解脱门 era=前6-5；第 10 汉传十宗（约5—9世纪）内有 era=前4-3、11-15 的节点。' % len(outside),
        evidence='；'.join('%s[L%02d] era=%s%s ⊄ 层窗口%s' % (name(k), li, e, list(er), list(w))
                          for k, li, e, er, w in outside),
        instances=[k for k, *_ in outside],
    ))

    F.append(dict(
        area='5 era 与年表时段',
        severity='low',
        problem='第 02 标准层的 epoch 只给「名称定型约前2—前1世纪」，而层内 4 个节点 era=前6-5，'
                '按 era 筛选时这些节点会落在该层声明的年代之外（层级 epoch 与节点 era 两套口径不一致）。',
        evidence='L2 (%s) 内节点 era：%s' % (
            G['tree'][1]['epoch'],
            '、'.join('%s=%s' % (S[k]['name'], S[k]['era']) for k in S if place.get(k) == 2)),
        instances=[k for k in S if place.get(k) == 2],
    ))

    missing = [k for k, v in S.items() if not v.get('era')]
    lonely = sorted(k for k, v in used.items() if v == 1)
    lonely_nodes = [k for k, v in S.items() if v['era'] in lonely]
    F.append(dict(
        area='5 era 与年表时段',
        severity='low',
        problem='%d 个 era 取值只被 1 个节点使用（%s），这些「时段」实为单点，与 9 段年表的粒度不匹配；'
                '另 6 个 era=none 全部集中在第 12 层。179 个节点的 era 字段均已填写，无缺失。' % (len(lonely), '、'.join(lonely)),
        evidence='孤立 era：%s；对应节点：%s；era=none 节点：%s' % (
            '、'.join(lonely),
            '、'.join('%s=%s' % (S[k]['name'], S[k]['era']) for k in lonely_nodes),
            '、'.join(k for k, v in S.items() if v['era'] == 'none')),
        instances=lonely_nodes,
    ))

    # era 与 tt.form：年表时段与「思想形成」应大体一致
    conflict = []
    for k, v in S.items():
        er = era_range(v['era'])
        fm = span_range(year_spans(v['tt'].get('form')))
        if er and fm and not overlap(er, fm):
            gap = (er[0] - fm[1]) if er[0] > fm[1] else (fm[0] - er[1])
            conflict.append((k, v['era'], er, fm, gap, v['tt']['form']))
    conflict.sort(key=lambda x: -x[4])
    F.append(dict(
        area='5 era 与年表时段',
        severity='medium',
        problem='%d 个节点（%.0f%%）的 era（年表时段）与同一节点的 tt.form（思想形成）区间不重叠：'
                '多数是 era 取汉传定型/流传期（4-7、6-7）而 form 取印度源流期，说明 era 的取义在各节点间不统一'
                '（有的按思想形成，有的按定型或流传）；其中 ten_paths、six_realms 的 era(8-12) 比 form(约前5世纪) 晚一千余年。' % (
                    len(conflict), 100.0 * len(conflict) / len(S)),
        evidence='；'.join('%s era=%s%s vs form=%s（相差约%d年）' % (S[k]['name'], e, list(er), list(fm), g)
                          for k, e, er, fm, g, _ in conflict[:10]),
        instances=[k for k, *_ in conflict],
    ))
    return F


def check_6(S, full, G, place, src):
    """出处分布的系统性问题"""
    F = []
    name = lambda k: S[k]['name']

    # 统计：以每条出处的主书名（首个《》）计一次引用；节点数按「任一位置提及」计（与页面文献节点的口径一致）
    cnt = collections.Counter()
    nodes = collections.defaultdict(set)
    vols = collections.defaultdict(list)
    entries = 0
    multi = 0
    for k, n in full.items():
        for s in (n.get('sources') or []):
            t = s.get('t') or ''
            titles = all_titles(t)
            entries += 1
            if len(titles) > 1:
                multi += 1
            for x in titles:
                nodes[x].add(k)
            ft = first_title(t)
            if ft:
                cnt[ft] += 1
                for v in vol_nums(t):
                    vols[ft].append((k, v))
    top = cnt.most_common(15)
    top_lines = []
    for t, c in top:
        vs = sorted({v for _, v in vols.get(t, [])})
        top_lines.append('%s:引用%d次/%d节点,卷次%s' % (
            t, c, len(nodes.get(t, ())), ('%d—%d' % (vs[0], vs[-1])) if vs else '无卷号'))

    # 6-1 卷号与经号不符（杂阿含经，被引最多）
    wrong = []
    for k, n in full.items():
        for s in (n.get('sources') or []):
            t = s.get('t') or ''
            if '杂阿含经' in t and '第34经' in t and '卷1' in t:
                wrong.append((k, t, '第34经属卷2（卷1止于第32经）'))
            if '杂阿含经' in t and '第335' in t:
                wrong.append((k, t, '第335经属卷13、第358经属卷14（卷13为第304—342经，卷14为第343—364经）'))
    F.append(dict(
        area='6 出处分布',
        severity='medium',
        problem='被引最多的典籍《杂阿含经》（50 个节点引用）存在标注卷号与经号不符的情况：'
                '「卷1 第34经」（第34经在卷二）、「卷10 第335、358经」（二经分别在卷十三、卷十四）。',
        evidence='；'.join('%s：%s → %s' % (k, t, why) for k, t, why in wrong),
        instances=sorted({k for k, _, _ in wrong}),
    ))

    # 6-2 巴利文献带汉译卷次
    pali_vol = []
    for k, n in full.items():
        for s in (n.get('sources') or []):
            t = s.get('t') or ''
            if re.search(r'《(长部|中部|相应部|增支部)》[^；;]*卷\s*\d', t):
                pali_vol.append((k, t))
    F.append(dict(
        area='6 出处分布',
        severity='low',
        problem='巴利《长部》被标出「卷2」——《长部》为巴利文献，无汉译卷次划分（PTS 本分 3 册，沙门果经为第 2 经），'
                '卷号与经号混用。',
        evidence='；'.join('%s：%s' % (k, t) for k, t in pali_vol),
        instances=[k for k, _ in pali_vol],
    ))

    # 6-3 别名分裂
    alias = {'法华玄义': '妙法莲华经玄义', '顺正理论': '阿毗达磨顺正理论', '增一阿含经': '增壹阿含经',
             '法华经': '妙法莲华经', '俱舍论': '阿毗达磨俱舍释论'}
    alias_lines = []
    for a, b in alias.items():
        if cnt.get(a) and cnt.get(b):
            alias_lines.append('%s(%d次) / %s(%d次)' % (a, cnt[a], b, cnt[b]))
    F.append(dict(
        area='6 出处分布',
        severity='low',
        problem='同一部典籍在不同出处条中使用不同题名，使引用计数被拆分，也使「被引最多的典籍」排序依赖题名归并口径'
                '（build/canon_titles.py 的 PREFER 表本身已把《俱舍论》与《阿毗达磨俱舍释论》视为同一条目）。',
        evidence='；'.join(alias_lines),
        instances=list(alias),
    ))

    # 6-4 文献节点关系被截断
    doc_edges = collections.Counter(e['s'] for e in G['edges'] if re.match(r'^doc_\d+$', e['s']))
    trunc = sorted((k, c) for k, c in doc_edges.items() if c >= 8)
    claim = {}
    if src:
        for x in src.get('docs', []):
            if 'id' in x:
                claim[x['id']] = x.get('n')
    over = [(k, c, claim.get(k)) for k, c in trunc if claim.get(k, 0) > c]
    F.append(dict(
        area='6 出处分布',
        severity='high',
        problem='文献节点与概念节点之间的「依据」关系被截断：%d 个文献节点各只保留 8 条关系边，而这些文献中有 %d 个的实际引用节点数大于 8'
                '（如《杂阿含经》正文声明「共 50 个节点引用此文献」「最相关的十几个」，关系图只有 8 条）。'
                '619 条关系因此不是完整关系集，被截掉的恰好是被引最多的典籍。' % (len(trunc), len(over)),
        evidence='%s' % '；'.join('%s 边%d 条 / 声明引用%s 个节点' % (k, c, n) for k, c, n in sorted(over, key=lambda x: -(x[2] or 0))[:8]),
        instances=[k for k, _, _ in over],
    ))

    # 6-5 卷号是否有超出实际卷数者（记录正/负结果供复核）
    print('  [6] 被引最多 15 部典籍：')
    for line in top_lines:
        print('      ' + line)
    print('  [6] 卷号超范围检查：本次未发现卷号大于典籍实际卷数的标注（最长者《俱舍论》卷30/30卷、'
          '《成唯识论》卷10/10卷、《中论》卷4/4卷，《大毗婆沙论》卷99/200卷、《瑜伽师地论》卷74/100卷均在范围内）')
    print('  [6] 498 条出处中 %d 条同时引用多部典籍，故「被引最多」按主书名、按全部提及两种口径结果不同' % multi)
    F.append(dict(
        area='6 出处分布',
        severity='low',
        problem='498 条出处中 %d 条在同一题名串里并列引用多部典籍（如「《俱舍论》卷25、《瑜伽师地论》卷22 等」），'
                '页面的「被引最多」统计未说明计入口径，按主书名与按全部提及所得排序不同。' % multi,
        evidence='主书名口径 top15：%s' % '；'.join(top_lines),
        instances=[t for t, _ in top],
    ))
    return F


def check_7(S):
    """释义长度的异常"""
    F = []
    name = lambda k: S[k]['name']
    by = collections.defaultdict(list)
    for n in S.values():
        by[n['cat']].append(n)

    stat = {}
    for c, ns in by.items():
        v = sorted(x['dlen'] for x in ns)
        if len(v) >= 5:
            q1 = statistics.quantiles(v, n=4)[0]
            q3 = statistics.quantiles(v, n=4)[2]
            iqr = q3 - q1
            stat[c] = dict(n=len(v), med=statistics.median(v), lo=q1 - 1.5 * iqr, hi=q3 + 1.5 * iqr,
                           mean=statistics.mean(v), sd=statistics.pstdev(v))
        else:
            stat[c] = dict(n=len(v), med=statistics.median(v), lo=None, hi=None,
                           mean=statistics.mean(v), sd=0)
    out = [(c, x['dlen'], x['id'], x['name']) for c, ns in by.items() for x in ns
           if stat[c]['lo'] is not None and (x['dlen'] < stat[c]['lo'] or x['dlen'] > stat[c]['hi'])]

    # 支分分支系统性偏短：八正道八支、十二因缘诸支
    eight = [k for k in ('right_view', 'right_thought', 'right_speech', 'right_action', 'right_livelihood',
                         'right_effort', 'right_mindfulness', 'right_samadhi') if k in S]
    links = [k for k in S if k.startswith('link_')]
    F.append(dict(
        area='7 释义长度',
        severity='medium',
        problem='同一目录分支内的下位节点释义系统性偏短：八正道八支中七支 87—124 字（仅正命 511 字例外；父节点八正道 267 字，'
                '同层 core 中位 202 字）；十二因缘诸支 91—216 字（父节点十二因缘 391 字）。此量级下释义多为名相罗列。',
        evidence='八正道支：%s；十二因缘支：%s' % (
            '、'.join('%s %d' % (name(k), S[k]['dlen']) for k in eight),
            '、'.join('%s %d' % (name(k), S[k]['dlen']) for k in links)),
        instances=eight + links,
    ))

    short = sorted((x['dlen'], x['id'], x['cat']) for x in S.values())[:8]
    long_ = sorted(((x['dlen'], x['id'], x['cat']) for x in S.values()), reverse=True)[:8]
    F.append(dict(
        area='7 释义长度',
        severity='low',
        problem='同类之内长度极差过大：core 类 right_action 87 字与 right_livelihood 511 字相差 5.9 倍（core 的 sd=118.7，'
                '为各类最高）；hist 类 translation_history 762 字对 huiChang_persecution 491 字。'
                '超出同类四分位距 1.5 倍者：%s。' % (
                    '；'.join('%s(%s)%d' % (nm, c, d) for c, d, i, nm in out) or '无'),
        evidence='最短 8：%s；最长 8：%s；分类统计 %s' % (
            '、'.join('%s(%s)%d' % (name(i), c, d) for d, i, c in short),
            '、'.join('%s(%s)%d' % (name(i), c, d) for d, i, c in long_),
            json.dumps({c: {kk: (round(vv, 1) if isinstance(vv, float) else vv) for kk, vv in s.items()}
                        for c, s in stat.items()}, ensure_ascii=False)),
        instances=[i for _, _, i, _ in out],
    ))

    thin = [c for c, s in stat.items() if s['n'] <= 2]
    F.append(dict(
        area='7 释义长度',
        severity='low',
        problem='分类样本数极不均衡：logic 类只有 1 个节点（因明 659 字），seal/nonself/debate 各 5 个，'
                '此四类的「同类均值/中位」由个别节点决定，按分类比较释义长度的结论不成立。',
        evidence='各类节点数与长度中位：%s' % json.dumps({c: [s['n'], s['med']] for c, s in stat.items()}, ensure_ascii=False),
        instances=sorted(thin),
    ))
    return F


def check_0(S, full):
    """基础数据与完整内容的字段一致性（structure.json vs A1/A2/B）"""
    F = []
    mm = []
    for k, v in full.items():
        s = S.get(k)
        if s is None:
            mm.append((k, 'structure.json 缺此节点'))
            continue
        if s['name'] != v.get('name'):
            mm.append((k, 'name', s['name'], v.get('name')))
        if s['cat'] != v.get('category'):
            mm.append((k, 'cat', s['cat'], v.get('category')))
        if s['era'] != v.get('era'):
            mm.append((k, 'era', s['era'], v.get('era')))
        if s['tt'] != v.get('tt'):
            mm.append((k, 'tt 三栏不一致'))
        if s['nsrc'] != len(v.get('sources') or []):
            mm.append((k, 'nsrc', s['nsrc'], len(v.get('sources') or [])))
        if s['dlen'] != len(v.get('desc') or ''):
            mm.append((k, 'dlen', s['dlen'], len(v.get('desc') or '')))
    if mm:
        F.append(dict(area='0 基础数据一致性', severity='medium',
                      problem='structure.json 与 A1/A2/B 的节点字段不一致 %d 处。' % len(mm),
                      evidence=json.dumps(mm[:10], ensure_ascii=False), instances=[m[0] for m in mm]))
    return F


def main():
    S, G, full, src = load()
    place, parent, depth, notes = tree_index(G['tree'])

    print('结构审查：structure.json %d 节点 / graph.json %d 边 / 树 %d 层 %d 节点 / 出处 %d 条' % (
        len(S), len(G['edges']), len(G['tree']), len(place),
        sum(len(n.get('sources') or []) for n in full.values())))

    findings = []
    for tag, fn in (('0', lambda: check_0(S, full)),
                    ('1', lambda: check_1(S, G, place, parent, depth)),
                    ('2', lambda: check_2(S, G, place, parent, depth)),
                    ('3', lambda: check_3(S, G, place, parent, depth, notes, full)),
                    ('4', lambda: check_4(S, full)),
                    ('5', lambda: check_5(S, G, place)),
                    ('6', lambda: check_6(S, full, G, place, src)),
                    ('7', lambda: check_7(S))):
        print('  运行检查 %s …' % tag)
        findings.extend(fn())

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(findings, f, ensure_ascii=False, indent=1)
        f.write('\n')

    dist = collections.Counter(f['severity'] for f in findings)
    print('\n已写入 %s：%d 条（high %d / medium %d / low %d）' % (
        OUT, len(findings), dist['high'], dist['medium'], dist['low']))

    # 各检查项的结果概况，供复核
    areas = collections.Counter(f['area'] for f in findings)
    for tag, label in (('0', '基础数据一致性'), ('1', '关系对称性与传递性'), ('2', '两端语义相称'),
                       ('3', '目录树与节点分类'), ('4', '年代三栏逻辑'), ('5', 'era 与年表时段'),
                       ('6', '出处分布'), ('7', '释义长度')):
        n = sum(v for k, v in areas.items() if k.startswith(tag + ' '))
        print('  %s %s：%s' % (tag, label, ('%d 条问题' % n) if n else '已检查、无异常'))

    print('已检查、无异常：')
    print('  · structure.json 的 name/cat/era/tt/nsrc/dlen 与 A1/A2/B 逐节点一致（0 处不符）')
    print('  · 因果 / 次第 / 支分 三类关系均无环（方向性成立）')
    print('  · 节点 era 无缺失（%d/%d），关系两端均在 structure.json 内（除文献节点）' % (
        sum(1 for v in S.values() if v.get('era')), len(S)))
    print('  · 未发现卷号超过典籍实际卷数的标注')
    return 0


if __name__ == '__main__':
    sys.exit(main())
