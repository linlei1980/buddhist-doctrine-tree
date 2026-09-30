# -*- coding: utf-8 -*-
"""统一各批 rel 的约定：rel 的值应为该关系的「具体说明」(note) 英译，而非关系类型名。

渲染器中关系类型由 edges[].l 单独渲染（RELS[e.l].name），note 渲染为行内小字。
部分批次误把类型名填进 rel，此处按中文 note 是否为英文关系名来识别并剔除。
"""
import json, glob, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import i18n

W = os.path.join(ROOT, 'build', 'i18n', 'work')
DATA = json.load(open(os.path.join(ROOT, 'data', 'buddhism.json'), encoding='utf-8'))
RELS_EN = {k: v['en'] for k, v in i18n.ui()['relations'].items()}
TYPE_NAMES = {v.lower() for v in RELS_EN.values()} | {'part','sequence','cause','identity',
             'assessment','contrast','practice','layer','basis','note'}

fixed = 0
for f in sorted(glob.glob(os.path.join(W, '*.en.jsonl'))):
    lines = [l for l in open(f, encoding='utf-8') if l.strip()]
    out = []
    for l in lines:
        o = json.loads(l)
        n = len(o.get('rel') or {})
        o['rel'] = {k: v for k, v in (o.get('rel') or {}).items()
                    if (v or '').strip().lower() not in TYPE_NAMES}
        if len(o['rel']) != n:
            fixed += 1
        out.append(json.dumps(o, ensure_ascii=False))
    open(f, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('清理了', fixed, '个节点中被误当作说明的关系类型名')
