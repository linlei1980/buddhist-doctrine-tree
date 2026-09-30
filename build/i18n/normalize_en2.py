# -*- coding: utf-8 -*-
"""英文译文的第二轮规范化：处理各组校对共同指出的全局性问题。

只做四类机械性统一，不改动语义：
  1. 梵巴术语统一带变音符（学界通行写法；不带变音符者仅保留在 aka 检索词中）
  2. 引号：U+2018 误用作撇号者改为 U+2019；单引号成对时闭合亦用 U+2019
  3. 卷次一律 fascicle（juan → fascicle）
  4. 术语择一：四念处、四禅八定、六处、欲界、沩仰、四无量心、实相
"""
import json, glob, re, sys, collections

W = 'build/i18n/work'

# —— 1. 变音符（词形统一，注意大小写与所有格）——
ACCENT = [
    (r'\bKumarajiva\b', 'Kumārajīva'),
    (r'\bAvatamsaka\b', 'Avataṃsaka'),
    (r'\bHinayana\b', 'Hīnayāna'),
    (r'\bHinayāna\b', 'Hīnayāna'),
    (r'\bPrajna\b(?!-)', 'Prajñā'),
    (r'\bPrajnaparamita\b', 'Prajñāpāramitā'),
    (r'\bNirvana\b', 'Nirvāṇa'),
    (r'\bSarvastivada\b', 'Sarvāstivāda'),
    (r'\bSautrantika\b', 'Sautrāntika'),
    (r'\bSamdhinirmocana-sutra\b', 'Saṃdhinirmocana-sūtra'),
    (r'\bSamdhinirmocana\b', 'Saṃdhinirmocana'),
    (r'\bAbhidharmakosa-bhasya\b', 'Abhidharmakośa-bhāṣya'),
    (r'\bAbhidharmakosa\b', 'Abhidharmakośa'),
    (r'\bSunyata\b', 'Śūnyatā'),
    (r'\bsunyata\b', 'śūnyatā'),
    (r'\bVasubandhu\b', 'Vasubandhu'),
    (r'\bMadhyamakavatara\b', 'Madhyamakāvatāra'),
    (r'\bPrasannapada\b', 'Prasannapadā'),
    (r'\bBuddhapalita\b', 'Buddhapālita'),
    (r'\bBhaviveka\b', 'Bhāviveka'),
    (r'\bCandrakirti\b', 'Candrakīrti'),
    (r'\bNagarjuna\b', 'Nāgārjuna'),
    (r'\bVijnapti-matra\b', 'Vijñapti-mātratā'),
    (r'\bVijnaptimatra\b', 'Vijñaptimātratā'),
    (r'\bSuvarnaprabhasottama\b', 'Suvarṇaprabhāsottama'),
    (r'\bPratityasamutpada\b', 'Pratītyasamutpāda'),
    (r'\bTathagatagarbha\b', 'Tathāgatagarbha'),
    (r'\bAsanga\b', 'Asaṅga'),
    (r'\bDignaga\b', 'Dignāga'),
    (r'\bDharmakirti\b', 'Dharmakīrti'),
    (r'\bSubhakarasimha\b', 'Śubhakarasiṃha'),
    (r'\bAmoghavajra\b', 'Amoghavajra'),
    (r'\bAtisa\b', 'Atiśa'),
    (r'\bSantarakṣita\b', 'Śāntarakṣita'),
    (r'\bSantiraksita\b', 'Śāntarakṣita'),
    (r'\bHarivarman\b', 'Harivarman'),
    (r'\bMoggaliputtatissa\b', 'Moggaliputtatissa'),
    (r'\bParsva\b', 'Pārśva'),
    (r'\bVasumitra\b', 'Vasumitra'),
]
# —— 3/4. 术语与体例 ——
LEXICON = [
    (r'\bfour foundations of mindfulness\b', 'the four establishments of mindfulness'),
    (r'\bthe four foundations of mindfulness\b', 'the four establishments of mindfulness'),
    (r'\beight attainments\b', 'eight concentrations'),
    (r'\bthe four dhyānas and eight attainments\b', 'the four dhyānas and eight concentrations'),
    (r'\bthe four dhyanas and eight attainments\b', 'the four dhyānas and eight concentrations'),
    (r'\bthe six bases\b', 'the six sense bases'),
    (r'\bthe sense realm\b', 'the realm of desire'),
    (r'\battachment to rites and rituals\b', 'clinging to rules and vows'),
    (r'\bWeiyang\b', 'Guiyang'),
    (r'\bthe four immeasurables\b', 'the four immeasurable attitudes'),
    (r'\btrue nature\b', 'true reality'),
    (r'\bjuan\b', 'fascicle'),
    (r'\bthree mysteries\b(?=[^)]{0,60}三玄三要)', 'three mysteries'),
]


def _walk(o):
    """遍历节点对象中所有可改写的文本字段：(路径, 值)"""
    yield ('desc', o.get('desc') or '')
    for i, s in enumerate(o.get('src') or []):
        for fld in ('t', 'q'):
            if s.get(fld): yield (f'src{i}.{fld}', s[fld])
    for k, v in (o.get('tt') or {}).items():
        if v: yield (f'tt.{k}', v)
    for t, v in (o.get('rel') or {}).items():
        if v: yield (f'rel.{t}', v)


def _set(o, path, val):
    if path == 'desc': o['desc'] = val; return
    if path.startswith('src'):
        i, fld = path[3:].split('.')
        o['src'][int(i)][fld] = val; return
    if path.startswith('tt.'):
        o['tt'][path[3:]] = val; return
    if path.startswith('rel.'):
        o['rel'][path[4:]] = val; return
    raise ValueError(path)

def fix_quotes(s):
    """U+2018 作撇号或右引号时改为 U+2019"""
    # 撇号：词内（字母‘字母）
    s = re.sub(r'(?<=[A-Za-zÀ-ÿ])[\u2018](?=[A-Za-z])', '\u2019', s)
    # 所有格：字母‘s
    s = re.sub(r'(?<=[A-Za-zÀ-ÿ])[\u2018]s\b', '\u2019s', s)
    # 成对单引号：‘…‘ → ‘…’
    s = re.sub(r'\u2018([^\u2018\u2019\n]{1,120}?)\u2018', '\u2018\\1\u2019', s)
    return s

stats = collections.Counter()
for f in sorted(glob.glob(f'{W}/*.en.jsonl')):
    lines = [l for l in open(f, encoding='utf-8') if l.strip()]
    out = []
    for l in lines:
        o = json.loads(l)
        for grp, rules in (('accent', ACCENT), ('lexicon', LEXICON)):
            for path, val in list(_walk(o)):
                new = val
                for pat, rep in rules:
                    new2 = re.sub(pat, rep, new)
                    if new2 != new:
                        stats[f'{grp}:{pat[:32]}'] += len(re.findall(pat, new)); new = new2
                new = fix_quotes(new)
                if new != val:
                    _set(o, path, new)
        out.append(json.dumps(o, ensure_ascii=False))
    open(f, 'w', encoding='utf-8').write('\n'.join(out) + '\n')

print('规范化改动统计：')
for k, v in stats.most_common(20):
    print(f'  {k:46} {v}')
