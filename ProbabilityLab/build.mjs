import { copyFile, cp, mkdir, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname } from 'node:path';
import katex from 'katex';
import { Marked } from 'marked';
import { distributions } from './distribution-models.js';

const require = createRequire(import.meta.url);
const katexDist = dirname(require.resolve('katex/dist/katex.min.css'));
const dist = new URL('./dist/', import.meta.url);
const read = (path) => readFile(new URL(path, import.meta.url), 'utf8');
const parseMath = (source, rule, displayMode) => {
  const match = rule.exec(source);
  if (!match) return;
  return { type: displayMode ? 'displayMath' : 'inlineMath', raw: match[0], formula: match[1] };
};
const renderMath = (formula, displayMode) => katex.renderToString(formula, {
  displayMode,
  throwOnError: true,
  strict: 'error',
});

function renderGraph(id) {
  const graph = distributions[id];
  if (!graph) throw new Error(`Unknown distribution graph: ${id}`);
  const controls = Object.entries(graph.params).map(([key, param]) => `
    <label class="graph-control">
      <span>${param.label} ${renderMath(param.symbol, false)}</span>
      <output></output>
      <input type="range" name="${key}" min="${param.min}" max="${param.max}" step="${param.step}" value="${param.value}">
    </label>`).join('');
  const outcome = graph.continuous ? 'x' : 'k';
  const probability = graph.continuous ? 'P(X<x)' : 'P(X=k)';
  const complement = graph.continuous ? 'P(X\\ge x)' : 'P(X\\le k)';
  return `
  <section class="distribution-graph" data-distribution="${id}" aria-labelledby="graph-${id}">
    <h4 id="graph-${id}">${graph.title} · ${graph.continuous ? 'плотность' : 'массы вероятностей'}</h4>
    <div class="graph-plot">
      <canvas role="img" aria-label="График: ${graph.title}"></canvas>
      <div class="graph-readout">
        <span>${renderMath(probability, false)} <output data-probability></output></span>
        <span>${renderMath(complement, false)} <output data-complement></output></span>
      </div>
    </div>
    <div class="graph-controls">${controls}
      <label class="graph-control graph-outcome">
        <span>${graph.continuous ? 'Порог' : 'Выбранный исход'} ${renderMath(outcome, false)}</span>
        <output></output>
        <input type="range" name="outcome">
      </label>
    </div>
    ${graph.note ? `<p class="graph-note">${graph.note}</p>` : ''}
    <noscript><p>Для интерактивного графика включи JavaScript.</p></noscript>
  </section>\n`;
}

const markdown = new Marked({
  extensions: [{
    name: 'distributionGraph',
    level: 'block',
    tokenizer(source) {
      const match = /^\{\{graph:([a-z]+)\}\}(?:\n|$)/.exec(source);
      if (match) return { type: 'distributionGraph', raw: match[0], id: match[1] };
    },
    renderer({ id }) { return renderGraph(id); },
  }, {
    name: 'displayMath',
    level: 'block',
    tokenizer(source) {
      return parseMath(source, /^\$\$\s*([\s\S]+?)\s*\$\$(?:\n|$)/, true);
    },
    renderer({ formula }) {
      return `<div class="formula" tabindex="0">${renderMath(formula, true)}</div>\n`;
    },
  }, {
    name: 'inlineMath',
    level: 'inline',
    start(source) { return source.indexOf('$'); },
    tokenizer(source) {
      return parseMath(source, /^\$([^$\n]+)\$/, false);
    },
    renderer({ formula }) {
      return renderMath(formula, false);
    },
  }],
  renderer: {
    heading({ tokens, depth }) {
      const level = depth + 1;
      return `<h${level}>${this.parser.parseInline(tokens)}</h${level}>\n`;
    },
  },
});

function render(source) {
  const html = markdown.parse(source).replaceAll('<table>', '<div class="table-scroll" tabindex="0"><table>')
    .replaceAll('</table>', '</table></div>');
  if (/\$/.test(html)) throw new Error('Unrendered math delimiter');
  return html;
}

const [template, foundations, discrete, continuous, deck] = await Promise.all([
  read('./index.html'), read('./materials/foundations.md'), read('./materials/discrete.md'),
  read('./materials/continuous.md'), read('./materials/cards.md'),
]);
const graphIds = [...`${discrete}\n${continuous}`.matchAll(/^\{\{graph:([a-z]+)\}\}$/gm)]
  .map((match) => match[1]);
if (graphIds.length !== Object.keys(distributions).length || new Set(graphIds).size !== graphIds.length) {
  throw new Error('Place exactly one graph per distribution in the Markdown chapters');
}
const cards = deck.trim().split(/^## /m).filter(Boolean).map((entry) => {
  const lineEnd = entry.indexOf('\n');
  const [id, topic, question] = entry.slice(0, lineEnd).split(' | ');
  return { id, topic, question: markdown.parseInline(question), answer: render(entry.slice(lineEnd).trim()) };
});
if (new Set(cards.map(({ id }) => id)).size !== cards.length) throw new Error('Duplicate card ID');

await mkdir(dist, { recursive: true });
await Promise.all([
  writeFile(new URL('index.html', dist), template
    .replace('<!-- FOUNDATIONS -->', () => render(foundations))
    .replace('<!-- DISCRETE -->', () => render(discrete))
    .replace('<!-- CONTINUOUS -->', () => render(continuous))
    .replace('<!-- CARD_DATA -->', () => JSON.stringify(cards).replaceAll('<', '\\u003c'))),
  ...['style.css', 'app.js', 'graphs.js', 'distribution-models.js']
    .map((file) => copyFile(new URL(file, import.meta.url), new URL(file, dist))),
  copyFile(`${katexDist}/katex.min.css`, new URL('katex.min.css', dist)),
  copyFile(`${katexDist}/../LICENSE`, new URL('katex-LICENSE.txt', dist)),
  cp(`${katexDist}/fonts`, new URL('fonts/', dist), { recursive: true }),
  writeFile(new URL('.nojekyll', dist), ''),
]);
console.log(`Built three Markdown chapters, ${graphIds.length} distribution graphs and ${cards.length} KaTeX flashcards.`);
