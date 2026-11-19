import { distributions, graphPoints } from './distribution-models.js';

const number = new Intl.NumberFormat('ru', { maximumFractionDigits: 3 });
const percent = new Intl.NumberFormat('ru', { style: 'percent', maximumFractionDigits: 3 });
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

function probabilityText(value) {
  if (value > 0 && value < 0.000005) return '< 0,001 %';
  if (value < 1 && value > 0.999995) return '> 99,999 %';
  return percent.format(value);
}

function mountGraph(section) {
  const definition = distributions[section.dataset.distribution];
  const { continuous, params } = definition;
  const canvas = section.querySelector('canvas');
  const ctx = canvas.getContext('2d');
  const outcome = section.querySelector('[name="outcome"]');
  const leftOutput = section.querySelector('[data-probability]');
  const rightOutput = section.querySelector('[data-complement]');
  const controls = Object.entries(params).map(([key, config]) => ({
    key, config, input: section.querySelector(`[name="${key}"]`),
  }));
  let model;

  function showControl(input) {
    input.parentElement.querySelector('output').textContent = number.format(input.valueAsNumber);
  }

  function updateModel() {
    const state = {};
    for (const { key, config, input } of controls) {
      if (config.maxFrom) input.max = state[config.maxFrom];
      state[key] = input.valueAsNumber;
      showControl(input);
    }
    const previous = model ? outcome.valueAsNumber : null;
    model = definition.model(state);
    outcome.min = continuous ? model.min : model.first;
    outcome.max = continuous ? model.max : model.last;
    outcome.step = continuous ? model.step : 1;
    outcome.value = clamp(previous ?? model.initial, Number(outcome.min), Number(outcome.max));
    outcome.disabled = outcome.min === outcome.max;
    updateEvent();
  }

  function updateEvent() {
    const value = outcome.valueAsNumber;
    showControl(outcome);
    const left = continuous ? model.probability(value) : model.values[value - model.first];
    let right = 1 - left;
    if (!continuous) {
      right = value === model.last && !definition.unbounded
        ? 1
        : model.values.slice(0, value - model.first + 1).reduce((sum, mass) => sum + mass, 0);
    }
    leftOutput.textContent = probabilityText(clamp(left, 0, 1));
    rightOutput.textContent = probabilityText(clamp(right, 0, 1));
    draw();
  }

  function draw() {
    if (!ctx) return;
    const { clientWidth: width, clientHeight: height } = canvas;
    if (!width || !height) return;
    const scale = window.devicePixelRatio || 1;
    canvas.width = Math.round(scale * width);
    canvas.height = Math.round(scale * height);
    ctx.setTransform(scale, 0, 0, scale, 0, 0);

    const left = 50;
    const right = width - 16;
    const top = 15;
    const bottom = height - 28;
    const lo = continuous ? model.min : model.first - 0.5;
    const hi = continuous ? model.max : model.last + 0.5;
    const max = continuous ? model.yMax : Math.min(1, Math.ceil(Math.max(...model.values) * 10) / 10);
    const px = (x) => left + (right - left) * (x - lo) / (hi - lo);
    const py = (y) => bottom - (bottom - top) * y / max;
    const selected = outcome.valueAsNumber;

    ctx.font = '12px system-ui';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#c6d9d0';
    ctx.strokeStyle = '#55746a';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = max * i / 4;
      strokeLine(left, py(y), right, py(y));
      ctx.fillText(number.format(y), left - 7, py(y));
    }

    if (continuous) {
      const points = graphPoints(model);
      ctx.save();
      ctx.beginPath();
      ctx.rect(left, 0, px(selected) - left, bottom);
      ctx.clip();
      trace(points, px, py);
      ctx.lineTo(right, bottom);
      ctx.lineTo(left, bottom);
      ctx.closePath();
      ctx.fillStyle = '#99bc54';
      ctx.fill();
      ctx.restore();
      ctx.strokeStyle = '#e7f2df';
      ctx.lineWidth = 2;
      trace(points, px, py);
      ctx.stroke();
      ctx.strokeStyle = '#c8ed71';
      ctx.setLineDash([4, 4]);
      strokeLine(px(selected), top, px(selected), bottom);
      ctx.setLineDash([]);
    } else {
      const barWidth = Math.min(52, (right - left) / model.values.length * 0.72);
      model.values.forEach((mass, i) => {
        const value = model.first + i;
        ctx.fillStyle = value === selected ? '#c8ed71' : '#86a396';
        const barHeight = bottom - py(mass);
        ctx.fillRect(px(value) - barWidth / 2, bottom - barHeight, barWidth, barHeight);
      });
    }

    ctx.textAlign = 'center';
    ctx.fillStyle = '#e7f2df';
    ctx.strokeStyle = '#86a396';
    ctx.lineWidth = 1;
    strokeLine(left, bottom, right, bottom);
    if (!continuous) {
      ctx.strokeStyle = '#c8ed71';
      strokeLine(px(selected) - 4, bottom + 4, px(selected) + 4, bottom + 4);
      ctx.strokeStyle = '#86a396';
    }
    const capacity = Math.max(2, Math.floor((right - left) / 39));
    const step = continuous ? Math.ceil((hi - lo) / capacity) : Math.ceil(model.values.length / capacity);
    const start = continuous ? Math.ceil(lo / step) * step : model.first;
    for (let x = start; x <= hi; x += step) {
      strokeLine(px(x), bottom, px(x), bottom + 4);
      ctx.fillText(number.format(x), px(x), bottom + 15);
    }
  }

  function strokeLine(fromX, fromY, toX, toY) {
    ctx.beginPath();
    ctx.moveTo(fromX, fromY);
    ctx.lineTo(toX, toY);
    ctx.stroke();
  }

  function trace(points, px, py) {
    ctx.beginPath();
    ctx.moveTo(px(points[0][0]), py(points[0][1]));
    for (const [x, y] of points.slice(1)) ctx.lineTo(px(x), py(y));
  }

  for (const { input } of controls) input.addEventListener('input', updateModel);
  outcome.addEventListener('input', updateEvent);
  updateModel();
  new ResizeObserver(draw).observe(canvas);
}

document.querySelectorAll('.distribution-graph').forEach(mountGraph);
