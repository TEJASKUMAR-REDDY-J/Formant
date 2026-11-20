// Generate site/sections/: one page per section with everything in its folder (plan data, phase plans,
// docs, reports, CSV tables) plus an index page. Run after editing plan-data.js or any section doc:
//   node 10-infrastructure/scripts/gen-sections.js
const fs = require('fs'), path = require('path');
const root = process.argv[2] || '.';
global.window = {};
eval(fs.readFileSync(path.join(root, 'site', 'plan-data.js'), 'utf8'));
const P = window.PLAN;
const REPO = 'https://github.com/TEJASKUMAR-REDDY-J/Formant';
const OUT = path.join(root, 'site', 'sections');
const MARKED = 'https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js';
const CSV_COLS = ['priority', 'dataset', 'style', 'used_for', 'licence', 'access', 'hours_our_languages_est',
  'raw_gb_our_languages', 'v01_hours_kept', 'v01_stored_gb', 'keep_rule'];

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const slug = s => s.folder.slice(3);
const li = a => a.map(x => `<li>${esc(x)}</li>`).join('');
const cellSec = Object.fromEntries(P.sections.flatMap(s => s.cells.map(c => [c.id, s])));
const anchor = p => 'doc-' + p.replace(/[^A-Za-z0-9]+/g, '-');
const gpuSum = cells => cells.reduce((t, c) => {
  if (!c.gpu) return t; const [a, b = a] = c.gpu.split('–').map(Number); return [t[0] + a, t[1] + b];
}, [0, 0]);

// Every .md (except the folder README) and .csv in a section folder, plans first, reports last.
function docs(s) {
  const out = [], walk = d => fs.readdirSync(path.join(root, d), { withFileTypes: true }).forEach(e => {
    const p = d + '/' + e.name;
    if (e.isDirectory()) return walk(p);
    if (p === s.folder + '/README.md' || !/\.(md|csv)$/.test(e.name)) return;
    out.push(p);
  });
  walk(s.folder);
  const rank = p => p.includes('/plans/') ? 0 : p.includes('/reports/') ? 3 : p.endsWith('.csv') ? 2 : 1;
  return out.sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
}
const DOCS = Object.fromEntries(P.sections.flatMap(s => docs(s).map(p => [p, `${slug(s)}.html#${anchor(p)}`])));
const title = (p, text) => (p.endsWith('.md') && (text.match(/^# (.+)$/m) || [])[1]) || p.split('/').pop();

function csvRows(text) {  // RFC 4180-ish: quoted fields, doubled quotes, commas and newlines inside quotes
  const rows = [[]]; let f = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) { if (ch === '"' && text[i + 1] === '"') { f += '"'; i++; } else if (ch === '"') q = false; else f += ch; }
    else if (ch === '"') q = true;
    else if (ch === ',') { rows.at(-1).push(f); f = ''; }
    else if (ch === '\n') { rows.at(-1).push(f.replace(/\r$/, '')); f = ''; rows.push([]); }
    else f += ch;
  }
  if (f || rows.at(-1).length) rows.at(-1).push(f);
  return rows.filter(r => r.length > 1);
}
function csvTable(text) {
  const [head, ...rows] = csvRows(text);
  const keep = CSV_COLS.every(c => head.includes(c)) ? CSV_COLS.map(c => head.indexOf(c)) : head.map((_, i) => i);
  const url = head.indexOf('url');
  const td = (r, i) => head[i] === 'dataset' && url >= 0 ? `<a href="${esc(r[url])}">${esc(r[i])}</a>` : esc(r[i]);
  return `<div class="tw"><table><thead><tr>${keep.map(i => `<th>${esc(head[i])}</th>`).join('')}</tr></thead><tbody>` +
    rows.map(r => `<tr>${keep.map(i => `<td>${td(r, i)}</td>`).join('')}</tr>`).join('') + '</tbody></table></div>' +
    (keep.length < head.length ? `<p class="sub">Showing ${keep.length} of ${head.length} columns; the full file is on GitHub.</p>` : '');
}

const head = (t, d) => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${esc(t)}</title>
<meta name="description" content="${esc(d)}">
<link rel="icon" href="../favicon.png" type="image/png">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="sections.css">
</head>
<body>
`;
const nav = cur => `<nav aria-label="Sections"><div class="wrap"><b><img src="../logo.webp" alt="Formant" width="1000" height="175">Sections</b>` +
  `<a href="index.html"${cur ? '' : ' aria-current="page"'}>All</a>` +
  P.sections.map(s => `<a href="${slug(s)}.html"${cur === s ? ' aria-current="page"' : ''}>${esc(s.name)}</a>`).join('') +
  `<a href="../plan.html">Plan board</a><a href="../index.html">Project site</a><a href="${REPO}" target="_blank" rel="noopener">GitHub</a></div></nav>\n`;
const foot = `<footer><div class="wrap">Generated from site/plan-data.js (plan ${P.version}, ${P.updated}) and the section folders by 10-infrastructure/scripts/gen-sections.js.</div></footer>\n`;
const status = c => `<span class="st ${c.status}">${c.status}</span>`;
const chip = d => { const id = d.replace('~', ''), s = cellSec[id];
  return `<a class="chip${d[0] === '~' ? ' soft' : ''}" href="${s ? slug(s) + '.html#' + id : '#'}" title="${d[0] === '~' ? 'same-week handoff' : 'must be done first'}">${esc(id)}</a>`; };

// Markdown is rendered in the browser with marked; the raw text stays in the page as a no-JS fallback.
const script = `<script src="${MARKED}"></script>
<script>
const MAP = ${JSON.stringify(DOCS)}, REPO = ${JSON.stringify(REPO)};
document.querySelectorAll('.md[data-path]').forEach(el => {
  if (!window.marked) return;
  const p = el.dataset.path, dir = p.split('/').slice(0, -1).join('/');
  el.innerHTML = marked.parse(el.querySelector('.raw').textContent);
  el.querySelectorAll('table').forEach(t => { const w = document.createElement('div'); w.className = 'tw'; t.replaceWith(w); w.append(t); });
  el.querySelectorAll('a[href]').forEach(a => {
    const h = a.getAttribute('href');
    if (/^(https?:|mailto:|#)/.test(h)) return;
    const [file, hash] = h.split('#'), abs = new URL(file, 'https://x/' + dir + '/').pathname.slice(1);
    a.href = MAP[abs] || REPO + '/blob/main/' + abs + (hash ? '#' + hash : '');
  });
});
</script>
`;

fs.mkdirSync(OUT, { recursive: true });
P.sections.forEach((s, i) => {
  const ds = docs(s), [lo, hi] = gpuSum(s.cells);
  const prev = P.sections[i - 1], next = P.sections[i + 1];
  const docHtml = ds.map(p => {
    const text = fs.readFileSync(path.join(root, p), 'utf8');
    const body = p.endsWith('.csv') ? csvTable(text) : `<div class="md" data-path="${esc(p)}"><pre class="raw">${esc(text)}</pre></div>`;
    return `<article class="doc" id="${anchor(p)}"><div class="doc-h"><span>${esc(p)}</span><a href="${REPO}/blob/main/${esc(p)}" target="_blank" rel="noopener">View on GitHub</a></div>${body}</article>`;
  }).join('\n');
  const phases = s.cells.map((c, k) => {
    const plan = ds.find(p => p.endsWith(`/plans/${c.id}.md`)), rep = ds.find(p => p.endsWith(`/reports/${c.id}.md`));
    return `<div class="card" id="${c.id}"><div class="top"><span class="id">${c.id}${P.critical.includes(c.id) ? ' · critical' : ''}</span><span class="wk">${esc(P.phases[k].week)}</span></div>
<h3>${esc(c.title)}</h3><p>${esc(c.goal)}</p>
<div class="chips"><span class="lbl" style="margin:0">Needs</span>${c.needs.length ? c.needs.map(chip).join('') : '<span class="lbl" style="margin:0;color:var(--muted)">nothing</span>'}</div>
<div class="chips">${status(c)}${c.gpu ? `<span class="lbl" style="margin:0">${esc(c.gpu)} T4-h</span>` : ''}</div>
<div class="links">${plan ? `<a href="#${anchor(plan)}">Week plan</a>` : ''}${rep ? `<a href="#${anchor(rep)}">Report</a>` : ''}</div>
<div class="done"><b>Done when</b>${esc(c.done)}</div></div>`;
  }).join('\n');
  const html = head(`Formant · ${s.name}`, `${s.name}: ${s.means}`) + nav(s) + `
<header><div class="wrap">
<div class="kicker">${s.num} · Section ${esc(s.code)} · <a href="${REPO}/tree/main/${s.folder}" target="_blank" rel="noopener">${s.folder}/</a></div>
<h1>${esc(s.name)}</h1>
<p class="lede">${esc(s.means)}</p>
${s.merged ? `<p class="note">${esc(s.merged)}</p>` : ''}
<div class="facts"><span>Phases <b>${s.cells.map(c => c.id).join(' · ')}</b></span><span>GPU <b>${hi ? `${lo}–${hi} T4-hours` : 'none'}</b></span><span>Documents <b>${ds.length}</b></span><span><a href="../plan.html#view=section&section=${s.code}">Open on the plan board</a></span></div>
</div></header>
<section><div class="wrap">
<h2>Scope</h2>
<div class="grid2"><div class="kv"><h3>In v0.1</h3><ul>${li(s.scope)}</ul></div><div class="kv"><h3>Not in v0.1</h3><ul>${li(s.out)}</ul></div></div>
<div class="grid3"><div class="kv"><h3>What to expect</h3><ul>${li(s.expect)}</ul></div><div class="kv"><h3>Takes in</h3><ul>${li(s.inputs)}</ul></div><div class="kv"><h3>Hands over</h3><ul>${li(s.outputs)}</ul></div></div>
</div></section>
<section><div class="wrap">
<h2>Phases</h2>
<p class="sub">One week each. Solid chips must be done before the phase starts; dashed chips are same-week handoffs.</p>
<div class="cards">${phases}</div>
</div></section>
<section><div class="wrap">
<h2>Documents</h2>
<p class="sub">Everything in <code>${s.folder}/</code> apart from its README: phase plans, design notes, data tables and reports.</p>
${ds.length ? `<ul class="toc">${ds.map(p => `<li><a href="#${anchor(p)}">${esc(title(p, fs.readFileSync(path.join(root, p), 'utf8')))}</a><span>${esc(p)}</span></li>`).join('')}</ul>${docHtml}` : '<p class="sub">No documents yet.</p>'}
</div></section>
<div class="wrap pager">${prev ? `<a href="${slug(prev)}.html">← ${esc(prev.num)} ${esc(prev.name)}</a>` : '<span></span>'}${next ? `<a href="${slug(next)}.html">${esc(next.num)} ${esc(next.name)} →</a>` : '<span></span>'}</div>
` + foot + script + '</body>\n</html>\n';
  fs.writeFileSync(path.join(OUT, slug(s) + '.html'), html);
  console.log('wrote sections/' + slug(s) + '.html', ds.length, 'docs');
});

// Index: goal, constraints, weeks, then one card per section.
const all = P.sections.flatMap(s => s.cells), [glo, ghi] = gpuSum(all);
const idx = head('Formant · Sections', 'Formant v0.1 by section: scope, phases, week plans, data tables and reports for all twelve sections.') + nav(null) + `
<header><div class="wrap">
<div class="kicker">Plan ${esc(P.version)} · updated ${esc(P.updated)}</div>
<h1>Twelve sections, four weeks</h1>
<p class="lede">${esc(P.goal)}</p>
<ul class="cons">${li(P.constraints)}</ul>
<div class="facts"><span>Phases <b>${all.length}</b></span><span>Done <b>${all.filter(c => c.status === 'done').length}</b></span><span>In progress <b>${all.filter(c => c.status === 'doing').length}</b></span><span>GPU <b>${glo}–${ghi} T4-hours</b></span></div>
</div></header>
<section><div class="wrap">
<h2>Weeks</h2>
<div class="cards">${P.phases.map((p, k) => `<div class="card"><div class="top"><span class="id">${esc(p.week)}</span></div><h3>${esc(p.title)}</h3><p>${esc(p.theme)}</p><div class="chips">${P.sections.map(s => s.cells[k]).map(c => `<a class="chip${P.critical.includes(c.id) ? ' crit' : ''}" href="${slug(cellSec[c.id])}.html#${c.id}">${c.id}</a>`).join('')}</div></div>`).join('')}</div>
<p class="sub" style="margin-top:14px">Red chips are on the critical path: ${P.critical.join(' → ')}.</p>
</div></section>
<section><div class="wrap">
<h2>Sections</h2>
<div class="cards">${P.sections.map(s => { const now = s.cells.find(c => c.status !== 'done') || s.cells.at(-1), [lo, hi] = gpuSum(s.cells);
  return `<a class="card" href="${slug(s)}.html"><div class="top"><span class="id">${s.num} · ${esc(s.code)}</span>${status(now)}</div><h3>${esc(s.name)}</h3><p>${esc(s.means)}</p><div class="done"><b>Now: ${now.id}</b>${esc(now.title)}${hi ? ` · ${lo}–${hi} T4-h in total` : ''} · ${docs(s).length} docs</div></a>`; }).join('')}</div>
</div></section>
` + foot + '</body>\n</html>\n';
fs.writeFileSync(path.join(OUT, 'index.html'), idx);
console.log('wrote sections/index.html');
