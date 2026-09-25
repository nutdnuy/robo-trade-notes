// Offline synthetic teaching example. Keep accounting aligned with lesson_13.py.
export const START_SESSION = 60;
export const PERIODS_PER_YEAR = 252;

const mean = (values) => values.reduce((sum, value) => sum + value, 0) / values.length;
const sampleStd = (values) => {
  if (values.length < 2) return 0;
  const average = mean(values);
  return Math.sqrt(values.reduce((sum, value) => sum + (value - average) ** 2, 0) / (values.length - 1));
};

export function calculateIndicators(rows, index) {
  const closes = rows.map((row) => row.close);
  const fast = mean(closes.slice(index - 19, index + 1));
  const slow = mean(closes.slice(index - 49, index + 1));
  const returns = [];
  for (let k = index - 19; k <= index; k += 1) returns.push(closes[k] / closes[k - 1] - 1);
  return { side: fast > slow ? 1 : 0, fast, slow, volatility: sampleStd(returns) * Math.sqrt(PERIODS_PER_YEAR) };
}

// a = risky weight before trade; w = requested weight AFTER fees. With pretrade
// equity E and proportional fee c, k = E_after_fee/E solves k=1-c*abs(w*k-a).
export function rebalance(pretradeWeight, targetWeight, costFraction) {
  const a = pretradeWeight;
  const w = targetWeight;
  const c = costFraction;
  const factor = w >= a ? (1 + c * a) / (1 + c * w) : (1 - c * a) / (1 - c * w);
  const turnover = Math.abs(w * factor - a);
  return { factor, turnover, feeFraction: c * turnover };
}

export function evaluateBacktest(data, { lookahead = false, volTarget = false, costBps = 5, targetVol = 0.1, benchmark = false } = {}) {
  const rows = Array.isArray(data) ? data : data.rows;
  if (!rows || rows.length <= START_SESSION + 1) throw new RangeError('At least 62 price rows are required');
  if (!Number.isFinite(costBps) || costBps < 0 || costBps >= 10000) throw new RangeError('costBps must be finite and between 0 and 10000 (exclusive)');
  if (!Number.isFinite(targetVol) || targetVol <= 0) throw new RangeError('targetVol must be finite and positive');
  if (rows.some((row) => !Number.isFinite(row.open) || !Number.isFinite(row.close) || row.open <= 0 || row.close <= 0)) {
    throw new RangeError('All open and close prices must be finite and positive');
  }
  const c = costBps / 10000;
  const equity = [1];
  const returns = [];
  const weights = [];
  const audit = [];
  const sessions = [rows[START_SESSION].session];
  let pretradeWeight = 0;
  let totalTurnover = 0;
  for (let t = START_SESSION; t < rows.length - 1; t += 1) {
    const decisionIndex = lookahead ? t : t - 1;
    const info = calculateIndicators(rows, decisionIndex);
    const size = info.volatility > 0 ? Math.min(1, targetVol / info.volatility) : 0;
    const weight = benchmark ? 1 : info.side * (volTarget ? size : 1);
    const trade = rebalance(pretradeWeight, weight, c);
    const assetReturn = rows[t + 1].open / rows[t].open - 1;
    const holdingFactor = 1 + weight * assetReturn;
    let periodFactor = trade.factor * holdingFactor;
    const driftedWeight = weight * (1 + assetReturn) / holdingFactor;
    const finalTurnover = t === rows.length - 2 ? driftedWeight : 0;
    if (finalTurnover) periodFactor *= 1 - c * finalTurnover;
    totalTurnover += trade.turnover + finalTurnover;
    returns.push(periodFactor - 1);
    equity.push(equity.at(-1) * periodFactor);
    sessions.push(rows[t + 1].session);
    weights.push(weight);
    audit.push({ session: rows[t].session, decisionSession: rows[decisionIndex].session,
      pretradeWeight, weight, estimatedVolatility: info.volatility, side: info.side,
      assetReturn, rebalanceTurnover: trade.turnover, rebalanceFeeFraction: trade.feeFraction,
      postFeeEquityFactor: trade.factor, finalLiquidationTurnover: finalTurnover });
    pretradeWeight = driftedWeight;
  }
  let peak = 1;
  const drawdowns = equity.map((value) => { peak = Math.max(peak, value); return value / peak - 1; });
  const volatility = sampleStd(returns);
  const id = benchmark ? 'benchmark' : `${lookahead ? 'biased' : 'causal'}-${volTarget ? 'target' : 'fixed'}`;
  const labels = { 'causal-fixed': 'ใช้ข้อมูลทันเวลา · ขนาดคงที่', 'causal-target': 'ใช้ข้อมูลทันเวลา · Vol target',
    'biased-fixed': 'ใช้ข้อมูลอนาคต · ขนาดคงที่', 'biased-target': 'ใช้ข้อมูลอนาคต · Vol target',
    benchmark: 'Buy and hold · ช่วงเวลาเดียวกัน' };
  return { id, label: labels[id], returns, equity, drawdowns, weights, sessions, audit,
    metrics: { totalReturn: equity.at(-1) - 1, cagr: equity.at(-1) ** (PERIODS_PER_YEAR / returns.length) - 1,
      volatility: volatility * Math.sqrt(PERIODS_PER_YEAR),
      sharpe: volatility ? mean(returns) / volatility * Math.sqrt(PERIODS_PER_YEAR) : null,
      maxDrawdown: Math.min(...drawdowns), turnover: totalTurnover },
    assumptions: { startSession: rows[START_SESSION].session, endSession: rows.at(-1).session, periods: returns.length,
      periodsPerYear: PERIODS_PER_YEAR, costBps, targetVol, leverageCap: 1, riskFreeRate: 0,
      smaWindows: [20, 50], volatilityWindow: 20,
      volatilityEstimator: 'sample standard deviation of close-to-close simple returns',
      execution: 'rebalance at open t, hold to open t+1',
      information: lookahead && !benchmark ? 'close t (impossible at open t)' : 'close t-1',
      zeroEstimatedVolatility: 'hold cash when volatility targeting',
      costConvention: 'exact target weight after proportional fees; initial entry and final liquidation included',
      turnoverConvention: 'sum absolute traded notional / equity immediately before each trade event' } };
}

export function compareBacktests(data, options = {}) {
  return [[false, false], [false, true], [true, false], [true, true]].map(([lookahead, volTarget]) =>
    evaluateBacktest(data, { ...options, lookahead, volTarget, benchmark: false }));
}

export function evaluateBenchmark(data, options = {}) {
  return evaluateBacktest(data, { ...options, lookahead: false, volTarget: false, benchmark: true });
}
