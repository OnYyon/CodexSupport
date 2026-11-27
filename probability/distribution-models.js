const range = (symbol, label, min, max, step, value) => ({ symbol, label, min, max, step, value });

function choose(n, k) {
  if (k < 0 || k > n) return 0;
  let result = 1;
  const count = Math.min(k, n - k);
  for (let i = 1; i <= count; i++) result *= (n - count + i) / i;
  return result;
}

function masses(first, last, probability, initial) {
  return {
    first, last, initial,
    values: Array.from({ length: last - first + 1 }, (_, i) => probability(first + i)),
  };
}

const gaussian = (z) => Math.exp(-z * z / 2) / Math.sqrt(2 * Math.PI);

function normalCdf(z) {
  const upper = Math.min(9, Math.abs(z));
  const steps = 100;
  const step = upper / steps;
  let sum = gaussian(0) + gaussian(upper);
  for (let i = 1; i < steps; i++) sum += (i % 2 ? 4 : 2) * gaussian(i * step);
  return Math.max(0, Math.min(1, 0.5 + Math.sign(z) * sum * step / 3));
}

export const distributions = {
  bernoulli: {
    title: 'Бернулли',
    params: { p: range('p', 'Вероятность успеха', 0, 1, 0.05, 0.65) },
    model: ({ p }) => masses(0, 1, (k) => k ? p : 1 - p, 1),
  },
  binomial: {
    title: 'Биномиальный закон',
    params: {
      n: range('n', 'Число испытаний', 1, 30, 1, 12),
      p: range('p', 'Вероятность успеха', 0, 1, 0.05, 0.35),
    },
    model: ({ n, p }) => masses(0, n, (k) => choose(n, k) * p ** k * (1 - p) ** (n - k), 4),
  },
  geometric: {
    title: 'Геометрический закон',
    unbounded: true,
    note: 'Показаны первые 30 попыток. За правой границей графика могут оставаться исходы.',
    params: { p: range('p', 'Вероятность успеха', 0.05, 1, 0.05, 0.25) },
    model: ({ p }) => masses(1, 30, (k) => (1 - p) ** (k - 1) * p, 3),
  },
  poisson: {
    title: 'Закон Пуассона',
    unbounded: true,
    note: 'Показаны исходы от 0 до 35. За правой границей графика остаётся хвост распределения.',
    params: { lambda: range('\\lambda', 'Среднее число событий', 0.5, 15, 0.5, 4) },
    model({ lambda }) {
      let mass = Math.exp(-lambda);
      return masses(0, 35, (k) => {
        if (k > 0) mass *= lambda / k;
        return mass;
      }, 4);
    },
  },
  hypergeometric: {
    title: 'Гипергеометрический закон',
    params: {
      N: range('N', 'Деталей в партии', 2, 30, 1, 20),
      M: { ...range('M', 'Бракованных деталей', 0, 20, 1, 6), maxFrom: 'N' },
      n: { ...range('n', 'Размер выборки', 1, 20, 1, 8), maxFrom: 'N' },
    },
    model({ N, M, n }) {
      const total = choose(N, n);
      return masses(Math.max(0, n - N + M), Math.min(n, M),
        (k) => choose(M, k) * choose(N - M, n - k) / total, 2);
    },
  },
  uniform: {
    title: 'Равномерный закон',
    continuous: true,
    params: {
      a: range('a', 'Левая граница', -5, 5, 0.5, -2),
      width: range('b-a', 'Длина отрезка', 1, 8, 0.5, 6),
    },
    model({ a, width }) {
      const b = a + width;
      const height = 1 / width;
      return {
        min: -6, max: 14, yMax: 1, step: 0.5, initial: 1,
        density: (x) => x >= a && x <= b ? height : 0,
        probability: (x) => Math.max(0, Math.min(1, (x - a) / width)),
        points: [[-6, 0], [a, 0], [a, height], [b, height], [b, 0], [14, 0]],
      };
    },
  },
  exponential: {
    title: 'Показательный закон',
    continuous: true,
    note: 'При вычислении правого хвоста учитывается и область за границей графика.',
    params: { lambda: range('\\lambda', 'Интенсивность', 0.25, 3, 0.25, 1) },
    model: ({ lambda }) => ({
      min: -1, max: 10, yMax: 3, step: 0.25, initial: 1,
      density: (x) => x < 0 ? 0 : lambda * Math.exp(-lambda * x),
      probability: (x) => x < 0 ? 0 : -Math.expm1(-lambda * x),
      jump: 0,
    }),
  },
  normal: {
    title: 'Нормальный закон',
    continuous: true,
    params: {
      mean: range('m', 'Среднее', -4, 4, 0.5, 0),
      sigma: range('\\sigma', 'СКО', 0.5, 2.5, 0.25, 1),
    },
    model: ({ mean, sigma }) => ({
      min: -12, max: 12, yMax: 0.8, step: 0.25, initial: 1,
      density: (x) => gaussian((x - mean) / sigma) / sigma,
      probability: (x) => normalCdf((x - mean) / sigma),
    }),
  },
};

export function graphPoints(model) {
  if (model.points) return model.points;
  const start = model.jump ?? model.min;
  const points = Array.from({ length: 201 }, (_, i) => {
    const x = start + (model.max - start) * i / 200;
    return [x, model.density(x)];
  });
  if (model.jump !== undefined) points.unshift([model.min, 0], [start, 0]);
  return points;
}
