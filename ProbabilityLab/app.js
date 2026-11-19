const byId = (id) => document.getElementById(id);
const cards = JSON.parse(byId('card-data').textContent);
const topic = byId('topic');
const review = byId('review');
const question = byId('question');
const answer = byId('answer');
const reveal = byId('reveal');
const rating = byId('rating');
const progress = byId('progress');
const pagination = byId('pagination');
const storageKey = 'codexsupport-probability-known-v1';
const known = new Set();
let index = 0;

try {
  const saved = JSON.parse(localStorage.getItem(storageKey) ?? '[]');
  if (Array.isArray(saved)) saved.forEach((id) => known.add(id));
} catch {
  // Practice remains available when storage is disabled.
}

topic.add(new Option('Все разделы', ''));
for (const group of new Set(cards.map((card) => card.topic))) {
  topic.add(new Option(group, group));
}

function selectedCards() {
  return cards.filter((card) => !topic.value || card.topic === topic.value);
}

function queue() {
  const selected = selectedCards();
  return review.checked ? selected.filter((card) => !known.has(card.id)) : selected;
}

function renderCard({ focus = false } = {}) {
  const selected = selectedCards();
  const visible = queue();
  index = Math.min(index, Math.max(0, visible.length - 1));
  const card = visible[index];
  const mastered = selected.filter(({ id }) => known.has(id)).length;
  const status = `Запомнено ${mastered} из ${selected.length}`;
  progress.textContent = card
    ? `Карточка ${index + 1} из ${visible.length} · ${status}`
    : status;
  question.innerHTML = card ? card.question : 'Все карточки раздела пройдены';
  answer.innerHTML = card?.answer ?? '';
  answer.hidden = true;
  reveal.hidden = !card;
  reveal.textContent = 'Показать формулу';
  reveal.setAttribute('aria-expanded', 'false');
  rating.hidden = true;
  pagination.hidden = visible.length < 2;
  byId('known').setAttribute('aria-pressed', card && known.has(card.id) ? 'true' : 'false');
  if (focus) question.focus();
}

function changeCard(step) {
  const count = queue().length;
  if (count < 2) return;
  index = (index + step + count) % count;
  renderCard({ focus: true });
}

function record(isKnown) {
  const card = queue()[index];
  if (!card) return;
  if (isKnown) known.add(card.id);
  else known.delete(card.id);
  try {
    localStorage.setItem(storageKey, JSON.stringify([...known]));
  } catch {
    // Keep the current session's marks in memory.
  }
  const count = queue().length;
  if (count && !(review.checked && isKnown)) index = (index + 1) % count;
  renderCard({ focus: true });
}

for (const filter of [topic, review]) {
  filter.addEventListener('change', () => {
    index = 0;
    renderCard();
  });
}
reveal.addEventListener('click', () => {
  answer.hidden = !answer.hidden;
  reveal.setAttribute('aria-expanded', String(!answer.hidden));
  reveal.textContent = answer.hidden ? 'Показать формулу' : 'Скрыть формулу';
  rating.hidden = answer.hidden;
});
byId('prev').addEventListener('click', () => changeCard(-1));
byId('next').addEventListener('click', () => changeCard(1));
byId('again').addEventListener('click', () => record(false));
byId('known').addEventListener('click', () => record(true));
renderCard();

const slider = byId('radius');
const canvas = byId('curve');
const context = canvas.getContext('2d');
const density = (x) => Math.exp(-x * x / 2) / Math.sqrt(2 * Math.PI);
const decimal = new Intl.NumberFormat('ru', { maximumFractionDigits: 2 });
const percent = new Intl.NumberFormat('ru', { style: 'percent', maximumFractionDigits: 2 });

function draw() {
  const radius = Number(slider.value);
  const steps = 120;
  const interval = radius / steps;
  let area = interval * (density(0) + density(radius));
  for (let i = 1; i < steps; i++) area += 2 * interval * density(i * interval);

  const halfWidth = decimal.format(radius);
  byId('radius-value').textContent = `±${halfWidth}`;
  byId('probability').textContent = percent.format(area);
  slider.setAttribute('aria-valuetext', `По ${halfWidth} СКО от среднего`);
  if (!context) return;

  const { clientWidth: width, clientHeight: height } = canvas;
  const scale = window.devicePixelRatio || 1;
  canvas.width = Math.round(scale * width);
  canvas.height = Math.round(scale * height);
  context.setTransform(scale, 0, 0, scale, 0, 0);

  const left = 14;
  const span = width - 2 * left;
  const baseline = height - 28;
  const px = (x) => left + (x + 3.6) * span / 7.2;
  const py = (x) => baseline - density(x) * (height - 42) / 0.4;

  context.beginPath();
  context.moveTo(px(-radius), baseline);
  for (let i = 0; i <= steps; i++) {
    const x = -radius + 2 * radius * i / steps;
    context.lineTo(px(x), py(x));
  }
  context.lineTo(px(radius), baseline);
  context.closePath();
  context.fillStyle = '#c8ed71';
  context.fill();

  context.strokeStyle = '#729084';
  context.lineWidth = 1;
  context.beginPath();
  context.moveTo(left, baseline);
  context.lineTo(width - left, baseline);
  context.stroke();
  context.font = '13px system-ui';
  context.textAlign = 'center';
  context.fillStyle = '#c6d9d0';
  for (let tick = -3; tick <= 3; tick++) {
    const x = px(tick);
    context.fillRect(x, baseline, 1, 5);
    context.fillText(String(tick).replace('-', '−'), x, height - 6);
  }
  context.strokeStyle = '#e7f2df';
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(px(-3.6), py(-3.6));
  for (let i = 1; i <= steps; i++) {
    const x = -3.6 + 7.2 * i / steps;
    context.lineTo(px(x), py(x));
  }
  context.stroke();
}
slider.addEventListener('input', draw);
new ResizeObserver(draw).observe(canvas);
draw();
