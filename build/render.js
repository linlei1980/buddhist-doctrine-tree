
/* ============================================================
   佛教基础理论 · 结构树（第二版）
   数据来自 data/buddhism.data.js（同源生成），亦可直接编辑本文件重建
   ============================================================ */
const DATA = window.BUDDHISM_DATA;
const UI = __UI__;
/* 跨语言检索词：另一语言的名称与别名，使中英两版都能被两种语言搜到 */
const XSEARCH = DATA.xsearch || {};   /* 界面文字，随语言注入 */
const DOCS = __DOCS__;
const NODES = DATA.nodes, TREE = DATA.tree, EDGES = DATA.edges;
const RELS = DATA.rels, CATS = DATA.cats, EP = DATA.epochs, ERAS = DATA.eras, TTK = DATA.ttk;

const ADJ = {}; Object.keys(NODES).forEach(id => ADJ[id] = []);
let edgeN = 0;
EDGES.forEach(e => {
  if (!NODES[e.s] || !NODES[e.t]) return;
  edgeN++;
  ADJ[e.s].push({o: e.t, l: e.l, note: e.note || '', dir: 'out'});
  ADJ[e.t].push({o: e.s, l: e.l, note: e.note || '', dir: 'in'});
});

/* ---------- 工具 ---------- */
const esc = s => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const mdIn = s => esc(s)
  // 先斜体后粗体，二者可互相嵌套（如 **粗体内的 *书名***）
  .replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, '$1<i>$2</i>')
  .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
  .replace(/\[\[([a-z0-9_]+)\|(.+?)\]\]/g, '<a href="#$1" class="ilink">$2</a>')
  .replace(/\n\n/g, '<br><br>')
  .replace(/\n(?=- |\d+\. )/g, '<br>')
  .replace(/\n(?=[^<])/g, '<br>')
  .replace(/(^|<br>)- /g, '$1<span class="li">·</span>');
const q = s => document.querySelector(s);
const qa = s => Array.prototype.slice.call(document.querySelectorAll(s));
const isNarrow = () => window.matchMedia('(max-width: 820px)').matches;

/* ---------- 左栏：目录 ---------- */
const treeEl = q('#tree'), tlEl = q('#timeline'), pathsEl = q('#paths');
let detailEl = null;   /* 节点详情的容器，首次渲染前解析 */
let selectedId = null, query = '', activeTab = 'tree';

function nodeRow(id, depth, role) {
  const n = NODES[id];
  if (!n) return null;
  const row = document.createElement('div');
  row.className = 'node-row lv' + Math.min(n.depth || depth, 4);
  row.dataset.id = id;
  row.style.paddingLeft = (14 + (n.depth || depth) * 13) + 'px';
  const ep = EP[n.ep], cat = CATS[n.c];
  row.innerHTML =
    '<span class="node-dot" style="background:' + cat.color + '"></span>' +
    '<span class="node-label">' + esc(n.n) + '</span>' +
    (role ? '<span class="node-role">' + esc(role) + '</span>' : '') +
    '<span class="node-src" title="' + n.src.length + '">' + n.src.length + '</span>' +
    (ep ? '<span class="node-ep" style="background:' + ep.color + '">' + ep.name.slice(0, 2) + '</span>' : '');
  row.addEventListener('click', () => selectNode(id));
  return row;
}
function buildItem(item, depth) {
  const frag = document.createDocumentFragment();
  // 分组节点（如「经藏 · 主要经典」）自身不是知识点，只作分隔标题
  if (!NODES[item.id]) {
    const head = document.createElement('div');
    head.className = 'node-group';
    head.style.paddingLeft = (14 + depth * 13) + 'px';
    head.textContent = item.name || item.note || '';
    if (item.name) frag.appendChild(head);
  } else {
    const row = nodeRow(item.id, depth, item.note);
    if (row) frag.appendChild(row);
  }
  (item.children || []).forEach(c => frag.appendChild(buildItem(c, depth + 1)));
  return frag;
}
TREE.forEach(layer => {
  const group = document.createElement('div');
  group.className = 'layer-group';
  group.style.setProperty('--c', '#B45309');
  const head = document.createElement('div');
  head.className = 'layer-header';
  head.innerHTML = '<span class="num">' + esc(layer.title.slice(0, 2)) + '</span>' +
    '<span class="name">' + esc(layer.title.slice(3)) + '</span>' +
    '<span class="epoch">' + esc(layer.epoch) + '</span><span class="tog">▼</span>';
  head.addEventListener('click', () => group.classList.toggle('collapsed'));
  const body = document.createElement('div');
  body.className = 'layer-body';
  layer.items.forEach(it => body.appendChild(buildItem(it, 1)));
  group.appendChild(head); group.appendChild(body);
  treeEl.appendChild(group);
});

/* ---------- 左栏：年表 ---------- */
ERAS.forEach(era => {
  const ids = Object.keys(NODES).filter(id => NODES[id].era === era.id);
  if (!ids.length) return;
  const catOrder = Object.keys(CATS);
  ids.sort((a, b) => {
    const A = NODES[a], B = NODES[b];
    if (!!B.key !== !!A.key) return (B.key ? 1 : 0) - (A.key ? 1 : 0);
    const ca = catOrder.indexOf(A.c), cb = catOrder.indexOf(B.c);
    if (ca !== cb) return ca - cb;
    return A.n.localeCompare(B.n, 'zh');
  });
  const box = document.createElement('div');
  box.className = 'tl-era';
  const keyN = ids.filter(i => NODES[i].key).length;
  box.innerHTML = '<div class="tl-head"><span class="lbl">' + esc(era.label) + '</span>' +
    '<span class="hint">' + esc(era.hint) + '</span>' +
    '<span class="n">' + ids.length + ' 项' + (keyN ? '（重点 ' + keyN + '）' : '') + '</span></div>';
  const items = document.createElement('div');
  items.className = 'tl-items';
  ids.forEach(id => {
    const n = NODES[id], cat = CATS[n.c];
    const chip = document.createElement('button');
    chip.className = 'tl-chip' + (n.key ? ' key' : '');
    chip.dataset.id = id;
    chip.innerHTML = '<i style="background:' + cat.color + '"></i>' + esc(n.n) +
      '<span class="d">' + n.src.length + '</span>';
    chip.addEventListener('click', () => selectNode(id));
    items.appendChild(chip);
  });
  box.appendChild(items); tlEl.appendChild(box);
});

/* ---------- 左栏：学习路径 ---------- */
function buildPathCards() {
pathsEl.innerHTML = '';
PATHS.forEach((p, i) => {
  const box = document.createElement('div');
  box.className = 'path-card';
  box.innerHTML = '<div class="ph"><span class="num">' + (i + 1) + '</span>' +
    '<span class="pn">' + esc(p.n) + '</span><span class="pt">' + esc(p.time) + '</span></div>' +
    '<div class="psub">' + esc(p.sub) + '</div>' +
    '<div class="pgoal">' + esc(p.goal) + '</div>' +
    '<div class="plabel">依次读这些节点</div><div class="pnodes"></div>' +
    '<div class="plabel">配合原典</div><ul class="ptexts">' +
    p.texts.map(t => '<li>' + esc(t) + '</li>').join('') + '</ul>' +
    '<div class="pprac">动手一处：' + esc(p.prac) + '</div>';
  const holder = box.querySelector('.pnodes');
  p.nodes.forEach(id => {
    const n = NODES[id]; if (!n) return;
    const b = document.createElement('button');
    b.className = 'tl-chip'; b.dataset.id = id;
    b.innerHTML = '<i style="background:' + CATS[n.c].color + '"></i>' + esc(n.n);
    b.addEventListener('click', () => { selectNode(id); scrollToRow(id); });
    holder.appendChild(b);
  });
  pathsEl.appendChild(box);
});
}

/* ---------- 左栏：关系筛选 ---------- */
const relBar = q('#relLegend');
let relOff = {};
Object.keys(RELS).forEach(k => {
  const b = document.createElement('button');
  b.className = 'lg'; b.dataset.rel = k;
  b.innerHTML = '<i style="background:' + RELS[k].color + '"></i>' + RELS[k].name;
  b.title = RELS[k].hint;
  b.addEventListener('click', () => {
    relOff[k] = !relOff[k];
    b.classList.toggle('off', !!relOff[k]);
    applyFilter();
  });
  relBar.appendChild(b);
});

/* ---------- 搜索 / 筛选 ---------- */
const searchInput = q('#search'), searchInfo = q('#searchInfo');
function haystack(id) {
  const n = NODES[id];
  return (n.n + ' ' + (n.en || '') + ' ' + id + ' ' +
    n.src.map(s => s.t + ' ' + s.q).join(' ') + ' ' +
    [n.tt.form, n.tt.fix, n.tt.trans].join(' ') + ' ' + n.d + ' ' +
    (XSEARCH[id] || '')).toLowerCase();
}
function keptRels() { return Object.keys(RELS).filter(k => !relOff[k]); }
function matchRels(id) {
  // 关系筛选是「只看被选中的类型」：节点的全部关系都须在保留的集合内
  const kept = keptRels();
  if (!kept.length) return false;
  const rs = (ADJ[id] || []).map(e => e.l);
  if (!rs.length) return false;
  return rs.every(l => kept.indexOf(l) >= 0);
}
function applyFilter() {
  let cnt = 0;
  const seen = {};
  const q = query;
  const relFiltering = Object.keys(relOff).some(k => relOff[k]);
  const filtering = !!q || relFiltering || keyOnly;
  qa('.node-row, .tl-chip').forEach(row => {
    const id = row.dataset.id;
    if (!NODES[id]) return;
    let ok = true;
    if (q) ok = haystack(id).indexOf(q) >= 0;
    if (ok && relFiltering) ok = matchRels(id);
    if (ok && keyOnly) ok = !!NODES[id].key || NODES[id].era === 'none';
    // 只有一个目录位置被计为「匹配」，重复出现的节点只计数一次
    if (ok && !seen[id]) { seen[id] = 1; cnt++; }
    row.classList.toggle('dim', !ok);
    row.classList.toggle('match', !!q && ok);
  });
  if (filtering) {
    searchInfo.innerHTML = cnt ? UI.match.replace('{n}', cnt)
      : UI.noMatch;
    qa('.layer-group').forEach(g => g.classList.remove('collapsed'));
  } else searchInfo.textContent = '';
}
searchInput.addEventListener('input', e => { query = e.target.value.trim().toLowerCase(); applyFilter(); });
searchInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    const first = q('.node-row.match') || q('.tl-chip.match');
    if (first) { selectNode(first.dataset.id); scrollToRow(first.dataset.id); }
  }
});
qa('#treeTools button').forEach(b => b.addEventListener('click', () => {
  const collapse = b.dataset.act === 'collapse';
  qa('.layer-group').forEach(g => g.classList.toggle('collapsed', collapse));
}));
let keyOnly = false;
qa('#tlTools button').forEach(b => b.addEventListener('click', () => {
  keyOnly = b.dataset.act === 'key';
  applyFilter();
}));

/* ---------- 标签页 ---------- */
function setTab(tab, push) {
  activeTab = tab;
  qa('.seg button').forEach(b => b.classList.toggle('on', b.dataset.view === tab));
  q('#tree').style.display = tab === 'tree' ? '' : 'none';
  q('#timeline').style.display = tab === 'timeline' ? '' : 'none';
  q('#paths').style.display = tab === 'path' ? '' : 'none';
  q('#relLegend').style.display = tab === 'tree' ? '' : 'none';
  q('#treeTools').style.display = tab === 'tree' ? '' : 'none';
  q('#tlTools').style.display = tab === 'timeline' ? '' : 'none';
  q('#pathTools').style.display = tab === 'path' ? '' : 'none';
  if (push) location.hash = tab === 'tree' ? '' : 'view=' + tab;
  try { localStorage.setItem('fojiao.tab', tab); } catch (err) {}
}
qa('.seg button').forEach(b => b.addEventListener('click', () => setTab(b.dataset.view, true)));

/* ---------- 详情面板的两个标签 ---------- */
let detailPane = 'welcome';
function setDetailPane(name, push) {
  detailPane = name;
  qa('.tabs button').forEach(b => b.classList.toggle('on', b.dataset.pane === name));
  ['welcome', 'docs', 'node'].forEach(k => {
    const el = q('#pane-' + k); if (el) el.classList.toggle('on', k === name);
  });
  if (name === 'docs' && !q('#pane-docs').dataset.done) renderDocs();
  if (push) location.hash = name === 'docs' ? 'view=docs' : (selectedId || '');
}
qa('.tabs button').forEach(b => b.addEventListener('click', () => {
  selectedId = null;
  qa('.node-row.selected, .tl-chip.on').forEach(el => el.classList.remove('selected', 'on'));
  setDetailPane(b.dataset.pane, true);
  detailEl.scrollTop = 0;
}));

const KIND_ORDER = ['经', '律', '论疏', '史料', '文献'];
const KIND_HINT = {
  '经': '佛陀的教说（含早期尼柯耶与汉译阿含）',
  '律': '僧团戒律与僧事制度',
  '论疏': '论书、注疏与宗派著作——判年代时须与「经」分开看',
  '史料': '史传、目录、碑铭与法敕',
  '文献': '其他引用条目'
};
function renderDocs() {
  const box = q('#pane-docs');
  if (!box || box.dataset.done) return;
  box.dataset.done = '1';
  let h = '<div class="welcome" style="max-width:900px"><h2>经 · 律 · 论 总览</h2>' +
    '<p>下表由各节点的「出处」自动汇总——<strong>共 ' + DOCS.length + ' 种文献</strong>。' +
    '每行给出该文献在本页被引用的次数、<b>本页的年代定位</b>、内容所属类别，' +
    '点任一行可展开所有引用它的节点。</p>' +
    '<p><b>「本页的年代定位」怎么读</b>　它取该文献在相关节点「时间 · 层积」栏中的' +
    '<b>文献定型</b>值（即该文献自身被命名、被系统整理的时间），若该栏为「不适用」才退回到' +
    '最早引用节点的<b>思想形成</b>值。</p>' +
    '<p><b>为何常出现很早的年代</b>　很多文献（尤其阿含与巴利尼柯耶）在本页的「思想形成」' +
    '被标为「约前 5 世纪」，指的是<strong>其内容所依的教说</strong>源自佛陀时代，' +
    '不是该文本的写成年代。两者相差数百年，故本表不采用前者；要精确到文本层面，' +
    '请看各节点的「文献定型」与「汉译流传」两栏。</p>' +
    '<input id="docSearch" placeholder="在文献名中检索：俱舍 / 中论 / 涅槃 / 律 / 量论" ' +
    'style="width:100%;max-width:420px;padding:6px 10px;border:1px solid var(--line);' +
    'border-radius:7px;font-family:inherit;font-size:12.5px;background:#FCFCFA;margin:0 0 14px"></div>';
  KIND_ORDER.forEach(kind => {
    const list = DOCS.filter(d => d.kind.split('/')[0] === kind);
    if (!list.length) return;
    h += '<div class="d-sec"><h3>' + esc(kind) + '（' + list.length + '）</h3>' +
      '<i>· ' + esc(KIND_HINT[kind] || '') + '</i></div>';
    h += '<table class="doc-tbl"><tr><th style="width:30%">文献</th><th style="width:10%">引用</th>' +
      '<th style="width:34%">本页的年代定位</th><th>所属</th></tr>';
    list.forEach(d => {
      h += '<tr class="doc-row" data-name="' + esc(d.name) + '"><td class="dn">' +
        esc(d.name) + '</td><td class="dc">' + d.n + '</td><td class="dw">' +
        esc(d.when || '—') + '</td><td class="dk">' + esc(d.cat) + '</td></tr>';
      h += '<tr class="doc-detail" data-for="' + esc(d.name) + '" style="display:none"><td colspan="4">' +
        d.ids.map(id => '<button class="tl-chip" data-id="' + id + '">' +
          '<i style="background:' + CATS[NODES[id].c].color + '"></i>' + esc(NODES[id].n) +
          '</button>').join(' ') + '</td></tr>';
    });
    h += '</table>';
  });
  box.innerHTML = h;
  box.querySelectorAll('.doc-row').forEach(r => r.addEventListener('click', () => {
    const d = box.querySelector('.doc-detail[data-for="' + r.dataset.name + '"]');
    if (d) d.style.display = d.style.display === 'none' ? '' : 'none';
  }));
  box.querySelectorAll('.doc-detail .tl-chip').forEach(b => b.addEventListener('click', ev => {
    ev.stopPropagation();
    setDetailPane('welcome', false);
    selectNode(b.dataset.id); scrollToRow(b.dataset.id);
  }));
  const inp = box.querySelector('#docSearch');
  inp.addEventListener('input', () => {
    const v = inp.value.trim().toLowerCase();
    box.querySelectorAll('.doc-row').forEach(r => {
      const hit = !v || r.dataset.name.toLowerCase().indexOf(v) >= 0;
      r.style.display = hit ? '' : 'none';
      if (!hit) {
        const d = box.querySelector('.doc-detail[data-for="' + r.dataset.name + '"]');
        if (d) d.style.display = 'none';
      }
    });
  });
}

/* ---------- 详情 ---------- */
detailEl = q('#pane-node');
const WELCOME = q('#pane-welcome').innerHTML;

/* 总览页上的年代说明与统计（首屏即需，故在首次渲染前注入） */
(function () {
  let sc = 0; Object.keys(NODES).forEach(id => sc += NODES[id].src.length);
  const set = (sel, v) => { const el = q(sel); if (el) el.textContent = v; };
  set('#stN', Object.keys(NODES).length);
  set('#stE', edgeN);
  set('#stS', sc);
  set('#stT', ERAS.length);
  set('#cntLayers', TREE.length + (UI.unitLayers || ''));
  set('#cntEras', ERAS.length + (UI.unitPeriods || ''));
})();

function renderDetail() {
  const n = NODES[selectedId];
  if (!n) { setDetailPane('welcome', false); return; }
  const cat = CATS[n.c], ep = EP[n.ep];
  let h = '<div class="d-head"><h2>' + esc(n.n) + '</h2>';
  if (n.en && n.en !== '—') h += '<div class="d-en">' + esc(n.en) + '</div>';
  h += '<div class="d-badges">' +
    '<span class="badge" style="background:' + cat.color + '">' + esc(cat.name) + '</span>' +
    (ep ? '<span class="badge" style="background:' + ep.color + '">' + esc(ep.name) + '</span>' : '') +
    '<span class="badge ghost">' + UI.badgeSrc.replace('{n}', n.src.length) + '</span>' +
    '<span class="badge ghost">' + UI.badgeRel.replace('{n}', (ADJ[selectedId] || []).length) + '</span></div></div>';
  h += '<div class="d-sec"><h3>' + UI.secMeaning + '</h3></div><div class="d-desc">' + mdIn(n.d) + '</div>';
  if (n.see && n.see.length) {
    h += '<div class="see-bar">' + UI.seeAlso + n.see.map(x => '<button data-id="' + x + '">' +
      esc(NODES[x].n) + '</button>').join('') + '</div>';
  }
  h += '<div class="d-sec"><h3>' + UI.secTime + '</h3><div class="tbl">';
  ['form', 'fix', 'trans'].forEach(k => {
    if (n.tt[k]) h += '<div class="trow"><span class="tk">' + (UI['ttk_' + k] || TTK[k]) + '</span><span class="tv">' +
      mdIn(n.tt[k]) + '</span></div>';
  });
  if (ep) h += '<div class="trow"><span class="tk">' + UI.epLabel + '</span><span class="tv">' +
    '<span class="ep-dot" style="background:' + ep.color + '"></span>' + esc(ep.name) +
    '　·　' + esc(ep.hint) + '</span></div>';
  if (selectedId.indexOf('doc_') === 0) {
    h += '<div class="trow"><span class="tk">' + UI.ttkAbout + '</span><span class="tv">' +
      UI.docNoDating + '</span></div>';
  }
  h += '</div></div>';
  if (n.src.length) {
    h += '<div class="d-sec"><h3>' + UI.secSource + '</h3><i>· ' + n.src.length + '</i></div><div class="src">';
    n.src.forEach(s => {
      h += '<div class="sitem"><div class="sname">' + esc(s.t) +
        '<span class="stag" style="background:' + s.color + '">' + esc(s.tag) + '</span></div>' +
        (s.q ? '<div class="squote">' + mdIn(s.q) + '</div>' : '') + '</div>';
    });
    h += '</div>';
  }
  const adj = ADJ[selectedId] || [];
  if (adj.length) {
    h += '<div class="d-sec"><h3>' + UI.secRelated + '</h3><i>· ' + adj.length + '</i></div><div class="rel-list">';
    adj.forEach(e => {
      const o = NODES[e.o]; if (!o) return;
      const dir = e.dir === 'out' ? '→' : '←';
      const rl = RELS[e.l] || {name: e.l, color: '#8A94A6'};
      h += '<button class="rel" data-id="' + e.o + '"><span class="dir">' + dir + '</span>' +
        '<span class="rel-name">' + esc(o.n) + '</span>' +
        '<span class="tag" style="background:' + rl.color + '">' + esc(rl.name) + '</span>' +
        (e.note ? '<span class="rn">' + esc(e.note) + '</span>' : '') + '</button>';
    });
    h += '</div>';
  }
  if (n.era && n.era !== 'none') {
    const era = ERAS.filter(x => x.id === n.era)[0];
    if (era) h += '<div class="see-bar">' + UI.eraPos + '<button data-act="era">' + esc(era.label) + '</button></div>';
  }
  detailEl.innerHTML = h;
  q('#tabNode').style.display = '';
  setDetailPane('node', false);
  detailEl.scrollTop = 0;
  q('#detail').scrollTop = 0;
  qa('#detail .rel, #detail .see-bar button').forEach(b => b.addEventListener('click', () => {
    if (b.dataset.act === 'era') { setTab('timeline', true); return; }
    selectNode(b.dataset.id); scrollToRow(b.dataset.id);
  }));
}

function scrollToRow(id) {
  const row = q('.node-row[data-id="' + id + '"]') ||
    q('.tl-chip[data-id="' + id + '"]');
  if (row) row.scrollIntoView({block: 'center', behavior: 'smooth'});
}
function selectNode(id) {
  if (!NODES[id]) return;
  selectedId = id;
  qa('.node-row.selected, .tl-chip.on').forEach(el => el.classList.remove('selected', 'on'));
  qa('.node-row[data-id="' + id + '"]').forEach(el => el.classList.add('selected'));
  qa('.tl-chip[data-id="' + id + '"]').forEach(el => el.classList.add('on'));
  renderDetail();
  location.hash = id;
  if (isNarrow()) {
    if (document.activeElement === searchInput) searchInput.blur();
    document.body.classList.add('detail-open');
  }
}
q('#mBack').addEventListener('click', () => {
  document.body.classList.remove('detail-open');
  detailEl.scrollTop = 0;
});


/* ---------- 学习路径（分段式读法） ---------- */
const PATHS = [
 {n:'一 · 基础路径', sub:'佛法的核心主张与理由', goal:'读完能用自己的话说明：佛教要解决什么问题、凭什么说「无我」、修行的目标是什么。', time:'约 12–15 小时',
  nodes:['four_truths','dukkha','samudaya','craving','nirodha','marga','eightfold','three_seals','impermanence','nonself_seal','nirvana','dependent_origination','twelve_links','karma','vipaka','samsara','anatta','karma_ownership','five_aggregates','thirty_seven_bodhipakkhiya'],
  texts:['《杂阿含经》卷15 第379经（转法轮经）','《相应部》56.11','《长部》22《大念处经》','《中阿含经》卷24 第98经'],
  prac:'先只做一件事：读四念处，并试着在走路时观察一次「身」与「受」。'},
 {n:'二 · 深入路径', sub:'部派论书 → 大乘两大轨道', goal:'读完能说明：缘起如何推出无自性、唯识为何要立阿赖耶识、两派究竟在争什么。', time:'约 25–30 小时',
  nodes:['councils','eighteen_schools','abhidharma','sarvastivada','sautrantika','six_causes_five_results','debate_pudgala','nagarjuna','madhyamaka','emptiness','two_truths','debate_two_truths','yogacara','vijnapti_matra','eight_consciousnesses','alaya','three_natures','paratantra','yogacara_vs_madhyamaka','hetuvidya','tathagatagarbha','debate_tathagatagarbha'],
  texts:['《俱舍论》卷1（界品）、卷6—7（根品）','《中论》卷1〈观因缘品〉、卷4〈观四谛品〉','《解深密经·一切法相品》','《成唯识论》卷1、卷8','《因明正理门论》'],
  prac:'做一次对照阅读：同一「依他起」，看《中论》与《成唯识论》各自如何界定，把分歧写成三行字。'},
 {n:'三 · 脉络路径', sub:'佛教如何从恒河传到东亚与西藏', goal:'读完能说明：为什么今天汉传以禅净为主、藏传以格鲁为主、南传保存了较早期形态。', time:'约 15–20 小时',
  nodes:['councils','ashoka','mahayana_origins','nagarjuna','yogacara','garbha_sutras','translation_history','yichang','panjiao','wushi_bajiao','wujiao_shizong','three_vehicles_one_vehicle','tiantai','huayan','sanlun','faxiang','chan','pureland','vinaya','tantra','jushe','chengshi','tangmi_tibetan','tibetan_schools','southern_tradition','huiChang_persecution','modern_studies'],
  texts:['《出三藏记集》','《开元释教录》','《高僧传》','《异部宗轮论》','《土观宗派源流》'],
  prac:'取《开元释教录》的目录，对照本页各宗条目，看译出年代与立宗年代的对应关系。'},
 {n:'四 · 实践路径', sub:'次第、方法、判准', goal:'读完能说明：止与观为何必须配合、顿与渐争的是什么、不同宗派的用功法差别在哪。', time:'约 20 小时',
  nodes:['three_refuges','five_precepts','vinaya_rites','three_trainings','sila','samadhi_training','prajna','four_foundations','samatha_vipassana','four_dhyanas','thirty_seven_bodhipakkhiya','sravaka_fruits','five_paths','bodhisattva_path','six_paramitas','four_immeasurables','four_attractions','chan_methods','buddha_name','two_paths_two_powers','mandala','three_mysteries','four_reliances','historical_layers'],
  texts:['《清净道论》〈说戒品〉〈说定品〉〈说慧品〉','智顗《摩诃止观》（选读）','《瑜伽师地论》〈声闻地〉','《菩提道次第广论》（科目）','《大般涅槃经》卷6（四依）'],
  prac:'按《大念处经》的「身念处」做一次二十分钟的入出息念；再读《默照铭》与《大慧书》各一段，比较两种用功法。'},
];

/* ---------- 总览页上的主线链 ---------- */
qa('#pane-welcome .chain a, #mGuide .chain a').forEach(a => a.addEventListener('click', ev => {
  ev.preventDefault(); selectNode(a.dataset.id);
}));
qa('#pane-welcome [data-id], #mGuide [data-id]').forEach(el => {
  if (el.tagName === 'A' && el.closest('.chain')) return;
  el.addEventListener('click', () => selectNode(el.dataset.id));
});

/* ---------- 启动 ---------- */
(function () {
  // 先建可交互内容（学习路径的节点标签、文献总览表），再定初始视图
  buildPathCards();
  renderDocs();
  const h = decodeURIComponent(location.hash.replace(/^#/, ''));
  let tab = 'tree';
  try { tab = localStorage.getItem('fojiao.tab') || 'tree'; } catch (err) {}
  if (h === 'view=timeline') tab = 'timeline';
  if (h === 'view=path') tab = 'path';
  setTab(tab, false);
  if (h === 'view=docs') { setDetailPane('docs', false); }
  else if (h && h.indexOf('view=') !== 0 && NODES[h]) selectNode(h);
  else { setDetailPane('welcome', false); }
})();
window.addEventListener('hashchange', () => {
  const h = decodeURIComponent(location.hash.replace(/^#/, ''));
  if (h === 'view=docs') { selectedId = null; setDetailPane('docs', false); return; }
  if (h === 'view=timeline' || h === 'view=path') { setTab(h.slice(5), false); return; }
  if (h && NODES[h] && h !== selectedId) selectNode(h);
});

window.addEventListener('load', function () {
  const w = q('.welcome');
  const box = q('#mGuide .mg-body');
  if (w && box) {
    const clone = w.cloneNode(true);
    const walker = document.createTreeWalker(clone, NodeFilter.SHOW_TEXT);
    let t;
    while ((t = walker.nextNode())) t.nodeValue = t.nodeValue.split('左侧').join('上方');
    box.appendChild(clone);
  }
});
