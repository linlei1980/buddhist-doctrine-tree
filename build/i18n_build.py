# -*- coding: utf-8 -*-
"""英文译文的构建入口：从各批译文生成 build/i18n/ 下的最终数据。

流程（反复运行结果一致）：
  1. rel 约定统一  —— 各批译者对关系说明的处理不一，此处清理误填的关系名
  2. 体例规范化    —— 卷次、经号、书名连字符等排版层面的分歧
  3. 合并          —— 合成 nodes.jsonl 与 sources.json，并校验 id、交叉引用与残留中文
  4. 书名规范化    —— 同一部书只保留一种英译，避免页面上出现两个名字

各批译文位于 build/i18n/work/*.en.jsonl（输入为同名的 *.json）。
"""
import os, sys, runpy

HERE = os.path.dirname(os.path.abspath(__file__))

def run(script):
    print('── %s' % script)
    runpy.run_path(os.path.join(HERE, script), run_name='__main__')

def main():
    run('fix_rel.py')
    run('normalize_en.py')
    run('merge_i18n.py')
    run('canon_titles.py')
    run('merge_i18n.py')      # 书名替换后重新汇总 sources.json
    print('英文译文构建完成。')

if __name__ == '__main__':
    main()
