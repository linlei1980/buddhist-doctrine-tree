# -*- coding: utf-8 -*-
"""统一英文译文的体例。

原则：只规范**同一部文献的同一写法**，不改变各批译者对术语的选择（那是学术判断）。
规范对象是排版层面的分歧：卷次词、经号词、书名连字符与大小写、引号、梵文变音符的
去留由各处自行决定，此处只做与「同一文献是否写成同一个名字」相关的归一。
"""
import json, glob, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, 'data', 'buddhism.json'), encoding='utf-8'))
W = os.path.join(ROOT, 'build', 'i18n', 'work')

# 卷次：统一用 fascicle
JUAN = [(re.compile(r'\bjuan\s+(\d+)'), r'fascicle \1'),
        (re.compile(r'\bch\.\s*(\d+)'), r'fascicle \1'),
        (re.compile(r'\bchapter\s+(\d+)\b(?=,|\s*$)', re.I), r'fascicle \1')]
# 经号：统一用 "sūtra N"
SUTRA = [(re.compile(r'\bsūtra no\.\s*'), 'sūtra '),
         (re.compile(r'\bsutta no\.\s*'), 'sutta ')]
# 书名：Nikāya / Āgama / Sūtra 等词去连字符、统一大写
TITLES = [
 (re.compile(r'\bDīgha-nikāya\b'), '*Dīgha Nikāya*'),
 (re.compile(r'\bMajjhima-nikāya\b'), '*Majjhima Nikāya*'),
 (re.compile(r'\bSaṃyutta-nikāya\b'), '*Saṃyutta Nikāya*'),
 (re.compile(r'\bSaṃyukta-nikāya\b'), '*Saṃyukta Nikāya*'),
 (re.compile(r'\bAṅguttara-nikāya\b'), '*Aṅguttara Nikāya*'),
 (re.compile(r'\bSaṃyukta-āgama\b'), '*Saṃyukta-āgama*'),
 (re.compile(r'\bMadhyama-āgama\b'), '*Madhyama-āgama*'),
 (re.compile(r'\bDīrgha-āgama\b'), '*Dīrgha-āgama*'),
 (re.compile(r'\bEkottarika-āgama\b'), '*Ekottarika-āgama*'),
 (re.compile(r'\bMahāsatipaṭṭhāna[- ]sutta\b'), '*Mahāsatipaṭṭhāna Sutta*'),
 (re.compile(r'\bMahācattārīsaka[- ]sutta\b'), '*Mahācattārīsaka Sutta*'),
 (re.compile(r'\bSāmaññaphala[- ]sutta\b'), '*Sāmaññaphala Sutta*'),
 (re.compile(r'\bSatipaṭṭhāna[- ]sutta\b'), '*Satipaṭṭhāna Sutta*'),
 (re.compile(r'\bAnattalakkhaṇa[- ]sutta\b'), '*Anattalakkhaṇa Sutta*'),
 (re.compile(r'\bMūlamadhyamakakārikā\b'), '*Mūlamadhyamakakārikā*'),
 (re.compile(r'\bMulamadhyamakakarika\b'), '*Mūlamadhyamakakārikā*'),
 (re.compile(r'\bMadhyamaka-kārikā\b'), '*Mūlamadhyamakakārikā*'),
 (re.compile(r'\bYogācārabhūmi\b(?!-śāstra)'), '*Yogācārabhūmi-śāstra*'),
 (re.compile(r'\bYogacarabhumi-sastra\b'), '*Yogācārabhūmi-śāstra*'),
 (re.compile(r'\bSaṃdhinirmocana Sūtra\b'), '*Saṃdhinirmocana-sūtra*'),
 (re.compile(r'\bAbhidharmakośa-bhāṣya\b'), '*Abhidharmakośa-bhāṣya*'),
]
# 中文注释：同一部书的罗马化括注统一
PARENS = [
 (re.compile(r'\(Yujia[\s-]?shidi[\s-]?lun\)'), '(Yujia Shidi Lun)'),
 (re.compile(r'\(Yujiashidi Lun\)'), '(Yujia Shidi Lun)'),
 (re.compile(r'\(Zhong Lun\)'), '(Zhong lun)'),
 (re.compile(r'\(Da Zhidu Lun\)'), '(Da Zhidu Lun)'),
 (re.compile(r'\(Jushe lun\)'), '(Jushe lun)'),
]

def normalize(t):
    for rx, rep in JUAN + SUTRA + TITLES + PARENS:
        t = rx.sub(rep, t)
    t = t.replace('“', '“').replace('"', '“').replace("'", '‘')
    return t

changed = 0
for f in sorted(glob.glob(os.path.join(W, '*.en.jsonl'))):
    out = []
    for line in open(f, encoding='utf-8'):
        if not line.strip():
            continue
        o = json.loads(line)
        for s in o.get('src') or []:
            if s.get('t'):
                new = normalize(s['t'])
                if new != s['t']:
                    changed += 1
                s['t'] = new
        out.append(json.dumps(o, ensure_ascii=False))
    open(f, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('规范化出处标题', changed, '处')
