// 浏览器实测：用无头 Chrome 打开产物，断言真实计算样式与交互。
//
// 与 verify_page.py 的分工：
//   verify_page.py  —— 静态断言（样式段是否完整、元数据是否齐备），零依赖，CI 用
//   本脚本          —— 真实渲染断言（计算样式、布局尺寸、点开节点是否可用），本地用
//
// 用法（先启动一个 CDP 端口由脚本自己拉起浏览器，无需额外依赖）：
//     node build/verify_page.mjs                # 检查两版
//     node build/verify_page.mjs index.html     # 只检查一份
//
// 找不到 Chrome 时以退出码 0 跳过（CI 上不阻塞），并打印提示。

import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import fs from 'node:fs';
import path from 'node:path';

const CANDIDATES = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
];
const CHROME = process.env.CHROME_PATH || CANDIDATES.find(p => fs.existsSync(p));
const ROOT = path.resolve(import.meta.dirname, '..');

if (!CHROME) {
  console.log('未找到 Chrome/Chromium，跳过浏览器实测（设 CHROME_PATH 可指定路径）。');
  process.exit(0);
}

const PAGES = process.argv.slice(2).length ? process.argv.slice(2) : ['index.html', 'en.html'];

// 计算样式断言：选择器 → 属性 → 期望值（正则为匹配，字符串为相等）
const STYLE_ASSERTIONS = [
  ['body', 'display', 'flex'],
  ['aside.outline', 'width', /^39[0-9](\.\d+)?px$/],
  ['main.detail', 'overflowY', 'auto'],
  ['.node-ep', 'backgroundColor', /^rgb\(/],
  ['.cstep', 'display', 'flex'],
  ['#mBack', 'display', 'none'],          // 桌面端应隐藏「返回目录」
];

const BEHAVIOUR = [
  ['统计数字已填充', `JSON.stringify([stN.textContent, stE.textContent, stS.textContent])
      .match(/—/) === null`],
  ['目录有节点行', `document.querySelectorAll('.node-row').length > 200`],
  ['节点详情可打开', `(()=>{selectNode('four_truths');
      const d=document.getElementById('pane-node');
      return !!d.querySelector('h2') && d.querySelectorAll('.rel').length > 0;})()`],
  ['出处引文已渲染', `(()=>{const d=document.getElementById('pane-node');
      return d.querySelectorAll('.sitem').length > 0;})()`],
  ['交叉链接可用', `(()=>{const d=document.getElementById('pane-node');
      return d.querySelectorAll('.ilink').length > 0;})()`],
  ['年表有内容', `(()=>{setTab('timeline',false);
      return document.querySelectorAll('.tl-chip').length > 100;})()`],
  ['文献总览可渲染', `(()=>{setDetailPane('docs',false);
      return document.querySelectorAll('#pane-docs .doc-row').length > 100;})()`],
  ['学习路径有卡片', `(()=>{setTab('path',false);
      return document.querySelectorAll('.path-card').length === 4;})()`],
];

async function checkPage(file) {
  const full = path.join(ROOT, file);
  if (!fs.existsSync(full)) { console.log(`✗ ${file}: 文件不存在`); return 1; }
  const port = 9500 + Math.floor(Math.random() * 400);
  const profile = `/tmp/dsh-verify-${port}`;
  const proc = spawn(CHROME, ['--headless=new', '--disable-gpu', '--no-sandbox',
    `--user-data-dir=${profile}`, `--remote-debugging-port=${port}`,
    '--window-size=1500,1000', 'file://' + full], { stdio: 'ignore' });
  let bad = 0;
  try {
    let list = null;
    for (let i = 0; i < 40 && !list; i++) {
      await sleep(400);
      try { list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); } catch {}
    }
    const page = (list || []).find(t => t.type === 'page');
    if (!page) { console.log(`✗ ${file}: 浏览器未就绪`); return 1; }
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise(r => ws.onopen = r);
    let id = 0; const pend = {}; const errs = [];
    ws.onmessage = e => {
      const m = JSON.parse(e.data);
      if (m.id && pend[m.id]) pend[m.id](m);
      if (m.method === 'Runtime.exceptionThrown')
        errs.push(m.params.exceptionDetails.exception?.description || 'unknown');
    };
    const send = (method, params) => new Promise(r => {
      const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params }));
    });
    const ev = async expr => (await send('Runtime.evaluate',
      { expression: expr, returnByValue: true })).result?.result?.value;
    await send('Runtime.enable');
    await sleep(1500);

    console.log(`\n${file}`);
    for (const [sel, prop, want] of STYLE_ASSERTIONS) {
      const got = await ev(`(()=>{const el=document.querySelector(${JSON.stringify(sel)});
        return el ? getComputedStyle(el)[${JSON.stringify(prop)}] : null;})()`);
      const ok = got !== null && (want instanceof RegExp ? want.test(got) : got === want);
      if (!ok) bad++;
      console.log(`  ${ok ? '✓' : '✗'} ${sel} {${prop}} = ${JSON.stringify(got)}` +
                  (ok ? '' : `（期望 ${want}）`));
    }
    for (const [label, expr] of BEHAVIOUR) {
      const ok = await ev(expr) === true;
      if (!ok) bad++;
      console.log(`  ${ok ? '✓' : '✗'} ${label}`);
    }
    if (errs.length) { bad++; console.log(`  ✗ JS 异常: ${errs.slice(0, 2).join(' | ')}`); }
    else console.log('  ✓ 无 JS 异常');
    ws.close();
  } finally {
    proc.kill();
  }
  return bad;
}

let total = 0;
for (const f of PAGES) total += await checkPage(f);
console.log(total === 0 ? '\n浏览器实测全部通过。' : `\n浏览器实测失败 ${total} 项。`);
process.exit(total === 0 ? 0 : 1);
