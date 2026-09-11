export function makeFixture() {
  return Array.from({ length: 120 }, (_, i) => ({
    day: i + 1,
    close: Math.round((100 + 0.11 * i + 5.8 * Math.sin(i / 9) + 1.5 * Math.sin(i / 2.1)) * 100) / 100,
  }));
}

export function rollingMean(values, window) {
  if (!Number.isInteger(window) || window < 1) throw new Error('Window must be a positive integer');
  let total = 0;
  return values.map((value, i) => {
    if (!Number.isFinite(value)) throw new Error('Prices must be finite');
    total += value;
    if (i >= window) total -= values[i - window];
    return i < window - 1 ? null : total / window;
  });
}

export function calculateSignals(rows, shortWindow = 5, longWindow = 20) {
  if (shortWindow >= longWindow) throw new Error('Short window must be smaller than long window');
  const short = rollingMean(rows.map(r => r.close), shortWindow);
  const long = rollingMean(rows.map(r => r.close), longWindow);
  const result = [];
  rows.forEach((row, i) => {
    const ready = short[i] !== null && long[i] !== null;
    const target = ready && short[i] > long[i] ? 1 : 0;
    const previousTarget = i > 0 ? result[i - 1].target : 0;
    result.push({ ...row, short: short[i], long: long[i], ready, target,
      nextOpenTarget: i === 0 ? 0 : previousTarget,
      changed: ready && target !== previousTarget,
      signal: !ready ? 'WARMUP' : target === 1 ? 'LONG' : 'CASH',
    });
  });
  return result;
}

export function signalEvents(rows) { return rows.filter(r => r.changed); }
