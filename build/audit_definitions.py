# -*- coding: utf-8 -*-
"""释义质量审计：找出「只给名词、不给判准」或「读者无法回查」的节点。

审计思路（四类，逐项可重跑）：
  A 定义句缺失 —— 释义中是否有界定性表述（谓/即/指/义为/分为…类/以…为…）
  B 组内失衡   —— 同一「组」（八正道八支、十二因缘支等）内，某节点的
                  释义深度或出处数与其他成员悬殊
  C 释义过短   —— 与该层中位数差距过大，可能只是提纲
  D 有名无据   —— 释义点名的典籍未列入出处栏（按等价类归并后判断）

用法：python3 build/audit_definitions.py
"""
import json, os, re, statistics as st, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, 'data', 'buddhism.json'), encoding='utf-8'))
N = D['nodes']
MANUAL = [k for k in N if not k.startswith('doc_')]

def plain(t):
    """去掉内部链接标记，只留显示文字"""
    t = re.sub(r'\[\[[a-z0-9_]+\|([^\]]*)\]\]', r'\1', t)
    return t.replace('**', '')

# ── 判准句的表述方式（尽量宽，宁可放过不可错杀）──
DEF = re.compile(
    r'(谓|即|指|义为|意思是|名为|称为|定义为|说的是|释为|分为.{0,4}[二三四五]|'
    r'[二三四五]种|[二三四五]类|[二三四五]义|以.{1,10}为|判准|标准|'
    r'不是.{1,30}而是|并非.{1,30}而是|严格说|其特点|核心是|要义|'
    r'etymolog|本义|依.{1,8}(而|说|立))')

# 典籍名归并：把「《X》·品名」「《X》卷n」「异写」归到同一等价类
def canon_book(b):
    b = re.split(r'[·・〈（(]', b)[0]
    b = re.sub(r'(卷|第)?[一二三四五六七八九十百\d]+(卷|品|经)?$', '', b)
    for a, c in (('增壹阿含', '增一阿含'), ('毘', '毗'), ('說', '说'), ('經', '经')):
        b = b.replace(a, c)
    return b.strip()

GROUPS = {
    '八正道八支': ['right_view', 'right_thought', 'right_speech', 'right_action',
                   'right_livelihood', 'right_effort', 'right_mindfulness', 'right_samadhi'],
    '十二因缘支': ['ignorance', 'link_formation', 'link_consciousness', 'link_namarupa',
                   'link_sadayatana', 'link_contact', 'link_feeling', 'craving',
                   'link_clinging', 'link_becoming', 'link_birth', 'link_aging_death'],
    '三法印': ['impermanence', 'all_suffering', 'nonself_seal', 'nirvana'],
    '三学': ['sila', 'samadhi_training', 'prajna'],
    '二谛': ['conventional', 'ultimate'],
    '三性': ['parikalpita', 'paratantra', 'parinispanna'],
    '汉传十宗': ['jushe', 'chengshi', 'sanlun', 'tiantai', 'huayan', 'faxiang',
                 'chan', 'pureland', 'vinaya', 'tantra'],
}

# 目录层
lay = {}
def rec(items, t):
    for it in items:
        if it['id'] in N:
            lay[it['id']] = t
        rec(it.get('children', []), t)
for L in D['tree']:
    rec(L['items'], L['title'])

report = []

# ── A：无定义句且篇幅偏短 ──
a_hits = []
for k in MANUAL:
    p = plain(N[k]['d'])
    if len(p) < 160 and not DEF.search(p):
        a_hits.append((k, N[k]['n'], len(p), lay.get(k, '?')))
if a_hits:
    report.append(('A 无定义句且篇幅偏短', a_hits))

# ── B：组内失衡 ──
b_hits = []
for g, ids in GROUPS.items():
    ids = [i for i in ids if i in N]
    if len(ids) < 3:
        continue
    L = [len(plain(N[i]['d'])) for i in ids]
    S = [len(N[i]['src']) for i in ids]
    lo, hi = min(L), max(L)
    if lo and hi >= lo * 2.4:
        small = [i for i in ids if len(plain(N[i]['d'])) == lo][0]
        b_hits.append((g, f'释义最短者 {N[small]["n"]} {lo} 字 / 最长 {hi} 字（{hi/lo:.1f}×）'))
    if max(S) - min(S) >= 3:
        few = [i for i in ids if len(N[i]['src']) == min(S)][0]
        b_hits.append((g, f'出处最少者 {N[few]["n"]} {min(S)} 条 / 最多 {max(S)} 条'))
if b_hits:
    report.append(('B 组内失衡', b_hits))

# ── C：释义过短 ──
c_hits = []
for L in D['tree']:
    ids = [i for i in lay if lay[i] == L['title']]
    lens = [len(plain(N[i]['d'])) for i in ids]
    if len(lens) < 4:
        continue
    med = st.median(lens)
    for i in ids:
        if len(plain(N[i]['d'])) < med * 0.45:
            c_hits.append((N[i]['n'], len(plain(N[i]['d'])), int(med), L['title']))
if c_hits:
    report.append(('C 释义过短', c_hits))

# ── D：有名无据（等价类归并）──
d_hits = []
BOOK = re.compile(r'《([^》]{2,20})》')
for k in MANUAL:
    v = N[k]
    named = {canon_book(b) for b in BOOK.findall(plain(v['d']))}
    cited = {canon_book(b) for s in v['src'] for b in BOOK.findall(s['t'])}
    for b in sorted(named - cited):
        if b and len(b) >= 2:
            d_hits.append((v['n'], b, [s['t'][:22] for s in v['src']]))
if d_hits:
    report.append(('D 释义点名但出处未列', d_hits))

# ── 输出 ──
print('=' * 72)
print(f'释义质量审计　人工节点 {len(MANUAL)} 个')
print('=' * 72)
if not report:
    print('四类检查均无发现。')
for title, hits in report:
    print(f'\n【{title}】{len(hits)} 处')
    for h in hits[:30]:
        print('  -', ' | '.join(str(x) for x in h))
    if len(hits) > 30:
        print(f'  …另有 {len(hits)-30} 处')
print()
print(f'合计 {sum(len(h) for _, h in report)} 处待人工判断')
