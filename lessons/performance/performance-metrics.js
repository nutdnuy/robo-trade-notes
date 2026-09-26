(function (root, factory) {
  'use strict';
  const metrics = factory();
  if (typeof module === 'object' && module.exports) module.exports = metrics;
  if (root) root.Metrics = metrics;
})(typeof window !== 'undefined' ? window : null, function () {
  'use strict';

  function finiteArray(values, name) {
    if (!Array.isArray(values) || values.some(x => !Number.isFinite(x))) {
      throw new TypeError(name + ' must be an array of finite numbers');
    }
  }
  function sum(values) { return values.reduce((a, b) => a + b, 0); }
  function mean(values) { return values.length ? sum(values) / values.length : null; }
  function sampleStd(values) {
    if (values.length < 2) return null;
    const average = mean(values);
    return Math.sqrt(sum(values.map(x => (x - average) ** 2)) / (values.length - 1));
  }

  // A closed trade is classified by its supplied P&L (net P&L in the chapter).
  // Losses are stored as a positive magnitude in aggregate loss fields.
  // Undefined ratios are null so that the UI can explain, rather than hide, them.
  function tradeStats(pnls) {
    finiteArray(pnls, 'pnls');
    const winners = pnls.filter(x => x > 0);
    const losers = pnls.filter(x => x < 0).map(x => -x);
    const count = pnls.length;
    const wins = winners.length;
    const losses = losers.length;
    const breakevens = count - wins - losses;
    const grossProfit = sum(winners);
    const grossLoss = sum(losers);
    const averageWin = mean(winners);
    const averageLoss = mean(losers);
    return {
      count, wins, losses, breakevens,
      winRate: count ? wins / count : null,
      lossRate: count ? losses / count : null,
      breakevenRate: count ? breakevens / count : null,
      grossProfit, grossLoss, averageWin, averageLoss,
      payoffRatio: averageWin !== null && averageLoss !== null ? averageWin / averageLoss : null,
      expectancy: mean(pnls),
      profitFactor: grossLoss > 0 ? grossProfit / grossLoss : null,
      totalPnl: sum(pnls),
      // This threshold is conditional on outcomes being wins or losses only.
      breakEvenWinRate: averageWin !== null && averageLoss !== null ? averageLoss / (averageWin + averageLoss) : null
    };
  }

  function drawdownStats(equity) {
    let peak = equity[0];
    let peakIndex = 0;
    let active = null;
    const drawdowns = [0];
    const episodes = [];
    for (let i = 1; i < equity.length; i++) {
      const value = equity[i];
      if (value >= peak) {
        if (active) {
          active.recoveryIndex = i;
          active.peakToRecoveryPeriods = i - active.peakIndex;
          active.troughToRecoveryPeriods = i - active.troughIndex;
          episodes.push(active);
          active = null;
        }
        peak = value;
        peakIndex = i;
        drawdowns.push(0);
      } else {
        const drawdown = value / peak - 1;
        drawdowns.push(drawdown);
        if (!active) {
          active = {peakIndex, troughIndex: i, recoveryIndex: null, depth: drawdown,
            peakToRecoveryPeriods: null, troughToRecoveryPeriods: null};
        } else if (drawdown < active.depth) {
          active.troughIndex = i;
          active.depth = drawdown;
        }
      }
    }
    if (active) episodes.push(active);
    const deepest = episodes.reduce((worst, item) => !worst || item.depth < worst.depth ? item : worst, null);
    return {
      drawdowns,
      maxDrawdown: deepest ? deepest.depth : 0,
      maxDrawdownPeakIndex: deepest ? deepest.peakIndex : null,
      maxDrawdownTroughIndex: deepest ? deepest.troughIndex : null,
      maxDrawdownRecoveryIndex: deepest ? deepest.recoveryIndex : null,
      peakToRecoveryPeriods: deepest ? deepest.peakToRecoveryPeriods : null,
      troughToRecoveryPeriods: deepest ? deepest.troughToRecoveryPeriods : null,
      underwaterPeriodsToEnd: active ? equity.length - 1 - active.peakIndex : 0,
      maxDrawdownObservedPeriodsToEnd: deepest && deepest.recoveryIndex === null ? equity.length - 1 - deepest.peakIndex : null,
      episodes
    };
  }

  // All returns are simple periodic returns. Yearly rates are converted geometrically.
  // Annualization uses sqrt(periodsPerYear), a convention, not an independence test.
  function periodStats(equity, options = {}) {
    finiteArray(equity, 'equity');
    if (!equity.length || equity.some(x => x <= 0)) throw new RangeError('equity must contain positive values, including initial equity');
    const periodsPerYear = options.periodsPerYear === undefined ? 252 : options.periodsPerYear;
    const riskFreeAnnual = options.riskFreeAnnual === undefined ? 0 : options.riskFreeAnnual;
    const marAnnual = options.marAnnual === undefined ? 0 : options.marAnnual;
    if (!Number.isFinite(periodsPerYear) || periodsPerYear <= 0) throw new RangeError('periodsPerYear must be positive');
    if (![riskFreeAnnual, marAnnual].every(x => Number.isFinite(x) && x > -1)) throw new RangeError('annual rates must exceed -100%');
    const periods = equity.length - 1;
    const returns = equity.slice(1).map((value, i) => value / equity[i] - 1);
    const riskFreePeriod = (1 + riskFreeAnnual) ** (1 / periodsPerYear) - 1;
    const marPeriod = (1 + marAnnual) ** (1 / periodsPerYear) - 1;
    const meanReturn = mean(returns);
    const sd = sampleStd(returns);
    const meanExcessReturn = mean(returns.map(x => x - riskFreePeriod));
    const downsideDeviation = periods ? Math.sqrt(sum(returns.map(x => Math.min(x - marPeriod, 0) ** 2)) / periods) : null;
    return {
      periods, periodsPerYear,
      totalReturn: equity[equity.length - 1] / equity[0] - 1,
      cagr: periods ? (equity[equity.length - 1] / equity[0]) ** (options.years ? 1 / options.years : periodsPerYear / periods) - 1 : null,
      returns, meanReturn, sampleStd: sd,
      annualizedVolatility: sd === null ? null : sd * Math.sqrt(periodsPerYear),
      riskFreePeriod, marPeriod, meanExcessReturn,
      sharpe: sd !== null && sd > 1e-15 ? meanExcessReturn / sd * Math.sqrt(periodsPerYear) : null,
      downsideDeviation,
      sortino: downsideDeviation !== null && downsideDeviation > 1e-15 ? (meanReturn - marPeriod) / downsideDeviation * Math.sqrt(periodsPerYear) : null,
      ...drawdownStats(equity)
    };
  }

  return {tradeStats, periodStats};
});
