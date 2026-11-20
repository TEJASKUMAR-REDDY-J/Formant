// Generate one README per section folder from site/plan-data.js.
const fs = require('fs'), path = require('path');
const root = process.argv[2] || ".";
global.window = {};
eval(fs.readFileSync(path.join(root, 'site', 'plan-data.js'), 'utf8'));
const P = window.PLAN;
const li = a => a.map(x => `- ${x}`).join('\n');
for (const s of P.sections) {
  const phases = s.cells.map((c, i) => [
    `### ${c.id} · ${P.phases[i].week} · ${c.title}`,
    '',
    c.goal,
    '',
    `- **Done when:** ${c.done}`,
    `- **Needs:** ${c.needs.length ? c.needs.map(d => d[0] === '~' ? `${d.slice(1)} (same-week handoff)` : d).join(', ') : 'nothing'}`,
    c.gpu ? `- **GPU:** ${c.gpu} T4-hours` : null,
    `- **Status:** ${c.status}`
  ].filter(x => x !== null).join('\n')).join('\n\n');
  const md = `# ${s.num} · ${s.name}

${s.means}

- **Owner:** _unassigned_
- **Board:** [site/plan.html](../site/plan.html#view=section&section=${s.code}) (phase IDs start with \`${s.code}\`)
${s.merged ? `\n> ${s.merged}\n` : ''}
## Scope for v0.1

${li(s.scope)}

**Not in v0.1:**

${li(s.out)}

## What to expect

${li(s.expect)}

## Takes in

${li(s.inputs)}

## Hands over

${li(s.outputs)}

## Phases

${phases}

## Folder layout

Create a subfolder the first time you need it.

\`\`\`
${s.folder}/
├── README.md     this file
├── configs/      run, filter and export configs (YAML), one per job
├── scripts/      code for this section's jobs
├── notebooks/    Kaggle notebooks, outputs cleared before commit
└── reports/      one file per phase: ${s.cells.map(c => c.id + '.md').join(', ')}
\`\`\`

Large files (audio, tokens, checkpoints, model exports) never go in git. They live on the Hugging Face Hub, and this folder's configs point to them. See [GUIDELINES.md](../GUIDELINES.md).

<!-- Generated from site/plan-data.js on ${P.updated}. Do not edit by hand: change site/plan-data.js, then run node 10-infrastructure/scripts/gen-readmes.js . -->
`;
  fs.writeFileSync(path.join(root, s.folder, 'README.md'), md);
  console.log('wrote', s.folder);
}
