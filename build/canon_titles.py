# -*- coding: utf-8 -*-
"""出处标题的最终规范化。

各批译者对同一中文条目的英译有风格差异（是否加汉译括注、卷次用 fascicle 还是 juan、
书名用斜体还是粗体、别名选 *Lotus Sūtra* 还是 *Saddharmapuṇḍarīka*）。
此脚本对每个中文条目**只保留一种**英译，避免同一部书在页面上出现两个名字。
"""
import json, glob, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'build', 'i18n', 'work')
# 人工指定：同一中文条目若译者选了不同书名，以此为准（键为中文条目的「基本题名」）
PREFER = {
 '《妙法莲华经》': 'Lotus Sūtra', '《法华经》': 'Lotus Sūtra',
 '《妙法莲华经·方便品》': 'Lotus Sūtra', '《法华经·方便品》': 'Lotus Sūtra',
 '《解深密经》': 'Saṃdhinirmocana-sūtra',
 '《大般涅槃经》': 'Mahāparinirvāṇa Sūtra',
 '《俱舍论》': 'Abhidharmakośa-bhāṣya', '《阿毗达磨俱舍释论》': 'Abhidharmakośa-bhāṣya',
 '《中论》': 'Mūlamadhyamakakārikā',
 '《成唯识论》': 'Cheng Weishi Lun',
 '《瑜伽师地论》': 'Yogācārabhūmi-śāstra',
 '《摄大乘论》': 'Mahāyānasaṃgraha',
 '《大乘起信论》': 'Awakening of Faith in the Mahāyāna',
 '《大智度论》': 'Mahāprajñāpāramitā-śāstra',
 '《大毗婆沙论》': 'Abhidharma-mahāvibhāṣā',
 '《那先比丘经》': 'Milindapañha',
 '《四分律》': 'Dharmaguptaka Vinaya',
 '《梵网经》': 'Brahmajāla Sūtra',
 '《无量寿经》': 'Sūtra of Immeasurable Life',
 '《阿弥陀经》': 'Amitābha Sūtra',
 '《观无量寿经》': 'Amitāyurdhyāna-sūtra',
 '《六祖坛经》': 'Platform Sūtra of the Sixth Patriarch',
 '《华严经》': 'Avataṃsaka Sūtra',
 '《宝性论》': 'Ratnagotravibhāga',
 '《萨婆多毗尼毗婆沙》': 'Sarvāstivāda-vinaya-vibhāṣā',
 '《佛地经论》': 'Buddhabhūmi-śāstra',
}

def score(t, prefer=None):
    s = 0
    if prefer and prefer in t: s += 100          # 命中人工指定
    if re.search(r'\*[^*]+\*', t): s += 10       # 有斜体书名
    if re.search(r'\([A-Z][a-z]+', t): s += 4    # 有汉译括注
    if 'fascicle' in t: s += 3                   # 卷次用 fascicle
    if 'juan' in t or re.search(r'\bch\.', t): s -= 3
    if '**' in t: s -= 8                         # 用粗体当书名，不规范
    if '“' in t or '”' in t: s += 1              # 品名用中文引号
    s -= abs(len(t) - 60) / 100.0                # 长度适中
    return s

def base_key(zh):
    """取出基本题名（用于查人工指定表）"""
    for k in sorted(PREFER, key=len, reverse=True):
        if k in zh: return k
    return None

# 第一遍：为每个中文条目选出规范译法
choices = {}
for f in sorted(glob.glob(os.path.join(W, '*.en.jsonl'))):
    src = {x['id']: x for x in json.load(open(f.replace('.en.jsonl', '.json'), encoding='utf-8'))}
    for line in open(f, encoding='utf-8'):
        if not line.strip(): continue
        o = json.loads(line)
        zs = src[o['id']]['src']
        for k, s in enumerate(o.get('src') or []):
            if k < len(zs) and s.get('t'):
                zh = zs[k]['t']
                pk = base_key(zh)
                pref = PREFER.get(pk) if pk else None
                sc = score(s['t'], pref)
                if zh not in choices or sc > choices[zh][0]:
                    choices[zh] = (sc, s['t'])

# 第二遍：替换
changed = 0
for f in sorted(glob.glob(os.path.join(W, '*.en.jsonl'))):
    src = {x['id']: x for x in json.load(open(f.replace('.en.jsonl', '.json'), encoding='utf-8'))}
    out = []
    for line in open(f, encoding='utf-8'):
        if not line.strip(): continue
        o = json.loads(line)
        zs = src[o['id']]['src']
        for k, s in enumerate(o.get('src') or []):
            if k < len(zs) and s.get('t'):
                zh = zs[k]['t']
                best = choices[zh][1]
                if s['t'] != best:
                    changed += 1
                    s['t'] = best
        out.append(json.dumps(o, ensure_ascii=False))
    open(f, 'w', encoding='utf-8').write('\n'.join(out) + '\n')

print('统一了', changed, '处出处标题；覆盖中文条目', len(choices), '种')
# 复查
pairs = collections.defaultdict(set)
for f in sorted(glob.glob(os.path.join(W, '*.en.jsonl'))):
    src = {x['id']: x for x in json.load(open(f.replace('.en.jsonl', '.json'), encoding='utf-8'))}
    for line in open(f, encoding='utf-8'):
        if not line.strip(): continue
        o = json.loads(line); zs = src[o['id']]['src']
        for k, s in enumerate(o.get('src') or []):
            if k < len(zs) and s.get('t'): pairs[zs[k]['t']].add(s['t'])
multi = {k: v for k, v in pairs.items() if len(v) > 1}
print('仍不一致:', len(multi))
for k, v in list(multi.items())[:10]:
    print(' ', k); [print('    ', x[:90]) for x in sorted(v)]
