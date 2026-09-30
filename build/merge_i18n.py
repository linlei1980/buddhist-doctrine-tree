# -*- coding: utf-8 -*-
"""把各批译文合并为 build/i18n/nodes.jsonl 与 sources.json，并做一致性检查。"""
import json, glob, os, re, collections, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'build', 'i18n', 'work')
OUT = os.path.join(ROOT, 'build', 'i18n')

CJK = re.compile(r'[\u3400-\u9fff]')
nodes_out, sources_out, problems = {}, {}, []

for f in sorted(glob.glob(os.path.join(W, '*.en.jsonl'))):
    base = f[:-len('.en.jsonl')]
    src = json.load(open(base + '.json', encoding='utf-8'))
    zh_by_id = {x['id']: x for x in src}
    lines = [l for l in open(f, encoding='utf-8') if l.strip()]
    seen = []
    for n, line in enumerate(lines, 1):
        try:
            o = json.loads(line)
        except Exception as e:
            problems.append(f'{os.path.basename(f)}:{n} JSON 非法 {e}'); continue
        i = o.get('id')
        if i not in zh_by_id:
            problems.append(f'{os.path.basename(f)}:{n} 未知 id {i}'); continue
        seen.append(i)
        nodes_out[i] = o
        # 书名对照：按位置对齐中文出处
        zh_src = zh_by_id[i]['src']
        for k, s in enumerate(o.get('src') or []):
            if k < len(zh_src) and s.get('t'):
                zh_t = zh_src[k]['t']
                if zh_t in sources_out and sources_out[zh_t]['en'] != s['t']:
                    problems.append(f'书名译法不一致：{zh_t!r} → {sources_out[zh_t]["en"]!r} / {s["t"]!r}')
                sources_out.setdefault(zh_t, dict(en=s['t'], id=i))
    miss = set(zh_by_id) - set(seen)
    if miss:
        problems.append(f'{os.path.basename(f)} 缺 {len(miss)} 个 id：{sorted(miss)[:5]}')

# 合法节点 id 取自中文数据全量（其余批次仍在翻译中，故不能只看已合并的）
DATA = json.load(open(os.path.join(ROOT, 'data', 'buddhism.json'), encoding='utf-8'))
IDS_ALL = set(DATA['nodes'])
# 校验交叉引用（对照中文数据的全量 id）
for i, o in nodes_out.items():
    for m in re.finditer(r'\[\[([a-z0-9_]+)\|', o.get('desc', '')):
        if m.group(1) not in IDS_ALL:
            problems.append(f'{i} 的交叉引用指向不存在的节点 {m.group(1)}')
    if CJK.search(o.get('name', '')) or CJK.search(o.get('desc', '')):
        problems.append(f'{i} 的 name/desc 残留中文')

# ---- 出处标题规范化：按 doc_names.json 的最长匹配替换 ----
DOC_NAMES = json.load(open(os.path.join(OUT, 'doc_names.json'), encoding='utf-8'))
DOC_NAMES = {k: v for k, v in DOC_NAMES.items() if not k.startswith('_')}
KEYS = sorted(DOC_NAMES, key=len, reverse=True)
def canon_title(t):
    for k in KEYS:
        if k in t:
            return t.replace(k, DOC_NAMES[k])
    return t
n_canon = 0
for i, o in nodes_out.items():
    for s2 in o.get('src') or []:
        if s2.get('t'):
            new = canon_title(s2['t'])
            if new != s2['t']:
                n_canon += 1
            s2['t'] = new
print(f'按规范名表替换出处标题 {n_canon} 处')

# 硬性防线：英文正文（desc/src/tt/rel）不得出现任何中文字符
CJK_HARD = re.compile(r'[\u3400-\u9fff\u3000-\u303f\uff00-\uffef]')
for i, o in nodes_out.items():
    for path, val in [('desc', o.get('desc') or '')] + \
                     [(f'src[{n}].{f}', (s or {}).get(f, '')) for n, s in enumerate(o.get('src') or [])
                      for f in ('t', 'q')] + \
                     [(f'tt.{k}', v) for k, v in (o.get('tt') or {}).items()] + \
                     [(f'rel.{k}', v) for k, v in (o.get('rel') or {}).items()]:
        if CJK_HARD.search(val):
            problems.append(f'{i} 的 {path} 含中文字符：{CJK_HARD.search(val).group(0)}')

with open(os.path.join(OUT, 'nodes.jsonl'), 'w', encoding='utf-8') as f:
    for i, o in nodes_out.items():
        f.write(json.dumps(o, ensure_ascii=False) + '\n')
json.dump({k: v['en'] for k, v in sources_out.items()},
          open(os.path.join(OUT, 'sources.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print(f'合并节点译文 {len(nodes_out)} 条 → build/i18n/nodes.jsonl')
print(f'汇总书名对照 {len(sources_out)} 条 → build/i18n/sources.json')
print('问题：', len(problems))
for p in problems[:20]:
    print('  -', p)
