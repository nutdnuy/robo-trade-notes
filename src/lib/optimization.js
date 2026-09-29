// Pure helpers for the lesson 15 figures; all numbers come from optimization-results.json.

export const PERIODS = {
  full: {label: 'ทั้ง 20 ปี', short: '2006–2026'},
  is: {label: 'ช่วงฝึก', short: '2006–2016'},
  oos: {label: 'ช่วงทดสอบ', short: '2016–2026'},
};

export const METRICS = {
  sharpe: {label: 'Sharpe', format: value => value.toFixed(2)},
  cagr: {label: 'CAGR', format: value => `${(value * 100).toFixed(2)}%`},
  mdd: {label: 'Max DD', format: value => `${(value * 100).toFixed(1)}%`},
};

// Sequential purple ramp, light (lower) to dark (higher); lightness decreases monotonically.
export const RAMP = ['#f3effb', '#ddd0f7', '#c3aef2', '#a585ea', '#8559e0', '#6632cf', '#4516a3'];

export const pairKey = (fast, slow) => `${fast}/${slow}`;

export function rankBy(grid, period, metric = 'sharpe') {
  const sorted = [...grid].sort((a, b) => b[period][metric] - a[period][metric]);
  return new Map(sorted.map((row, index) => [pairKey(row.f, row.s), index + 1]));
}

export function bestPair(grid, period, metric = 'sharpe') {
  return grid.reduce((best, row) => (row[period][metric] > best[period][metric] ? row : best), grid[0]);
}

export function colorScale(values) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return value => RAMP[Math.min(RAMP.length - 1, Math.floor(((value - min) / span) * RAMP.length))];
}

export function percentile(values, q) {
  const sorted = [...values].sort((a, b) => a - b);
  const position = (sorted.length - 1) * q;
  const low = Math.floor(position);
  const high = Math.ceil(position);
  return sorted[low] + (sorted[high] - sorted[low]) * (position - low);
}

export function median(values) {
  return percentile(values, 0.5);
}

export function niceTicks(min, max, count = 4) {
  const range = Math.max(max - min, 1e-9);
  const rough = range / count;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const factor = rough / magnitude;
  const step = (factor <= 1 ? 1 : factor <= 2 ? 2 : factor <= 5 ? 5 : 10) * magnitude;
  const low = Math.floor(min / step) * step;
  const high = Math.ceil(max / step) * step;
  return Array.from({length: Math.round((high - low) / step) + 1}, (_, i) => Number((low + i * step).toFixed(10)));
}

export function rebase(values, index) {
  const base = values[index];
  return values.map((value, i) => (i < index ? null : (value / base) * 100));
}

export const formatUsd = value => `${Math.round(value).toLocaleString('en-US')} USD`;
export const formatPercent = (value, digits = 2) => `${(value * 100).toFixed(digits)}%`;
