# -*- coding: utf-8 -*-
"""英文版译名与译文。

文件
  ui.json       — 界面文字、分类、关系类型、层积（键为中文原文）
  nodes.jsonl   — 节点译文：name / aka / desc / src / tt / rel
  sources.json  — 出处书名译文（键为中文原题，未命中的条目在构建时报告）
  static.json   — 静态说明：总览页、修订说明、读法、关系类型表、年代说明
"""
import json, os, collections

_DIR = os.path.dirname(os.path.abspath(__file__))
_cache = {}

def _load_json(name, default=None):
    if name not in _cache:
        path = os.path.join(_DIR, name + '.json')
        _cache[name] = (json.load(open(path, encoding='utf-8'))
                        if os.path.exists(path) else (default if default is not None else {}))
    return _cache[name]

def _load_jsonl(name):
    if name not in _cache:
        out = {}
        path = os.path.join(_DIR, name + '.jsonl')
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    o = json.loads(line)
                    out[o.pop('id')] = o
        _cache[name] = out
    return _cache[name]

def ui():        return _load_json('ui')
def nodes():     return _load_jsonl('nodes')
def sources():   return _load_json('sources')
def static():    return _load_json('static')

def node(i, field=None, default=''):
    """取节点译文：field 为 None 时返回整个译文对象"""
    o = nodes().get(i)
    if o is None:
        return {} if field is None else default
    return o if field is None else o.get(field, default)

def source(t, field='en', default=None):
    """按中文书名取英文题名；未命中时返回 default（构建时另行报告）"""
    return sources().get(t, {}).get(field, default if default is not None else t)

def ui_str(lang, key):
    return ui()['lang'][lang].get(key, '')

def ui_map(lang, group, key='en'):
    """categories / relations / epochs：中文名 → 目标语言的名称"""
    return {k: v[key] for k, v in ui()[group].items()}

def missing():
    """返回缺失译文与未命中书名的清单，供构建时核对"""
    n_zh = nodes()   # 已合并的译文
    s = sources()
    return dict(nodes=len(n_zh), sources=len(s))
