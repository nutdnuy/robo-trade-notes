import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { calculateIndicators, compareBacktests, evaluateBacktest, evaluateBenchmark, rebalance } from '../src/lib/backtest-intro.js';

const data = JSON.parse(readFileSync(new URL('../public/downloads/backtest-intro-data.json', import.meta.url)));
const python = JSON.parse(readFileSync(new URL('../public/downloads/backtest-intro-results.json', import.meta.url)));
const near = (actual, expected, tolerance = 1e-11) => assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)), `${actual} != ${expected}`);
const flatRows = (count = 62) => Array.from({ length: count }, (_, session) => ({ session, open: 100, close: 100 }));

test('all four modes use the same explicit execution window and bounded exposure', () => {
  const results = compareBacktests(data);
  assert.deepEqual(results.map((r) => r.id), ['causal-fixed', 'causal-target', 'biased-fixed', 'biased-target']);
  for (const result of results) {
    assert.equal(result.returns.length, 259);
    assert.equal(result.equity.length, 260);
    assert.deepEqual(result.sessions, Array.from({ length: 260 }, (_, i) => i + 60));
    assert.ok(result.weights.every((w) => w >= 0 && w <= 1));
    assert.ok(result.drawdowns.every((d) => d <= 1e-15));
    near(result.returns.reduce((value, r) => value * (1 + r), 1), result.equity.at(-1));
  }
});

test('a close not known at entry cannot affect causal side or size, but leaks into both biased variants', () => {
  const rows = flatRows();
  rows[60].close = 120;
  rows[61].open = 110;
  for (const volTarget of [false, true]) {
    const causal = evaluateBacktest(rows, { volTarget, costBps: 0 });
    const biased = evaluateBacktest(rows, { volTarget, lookahead: true, costBps: 0 });
    assert.equal(causal.weights[0], 0);
    assert.ok(biased.weights[0] > 0);
    assert.equal(causal.audit[0].decisionSession, 59);
    assert.equal(biased.audit[0].decisionSession, 60);
    near(biased.returns[0], 0.1 * biased.weights[0]);
  }
});

test('future closes do not change earlier causal positions or volatility estimates', () => {
  const changed = structuredClone(data);
  changed.rows[100].close *= 2;
  const original = evaluateBacktest(data, { volTarget: true });
  const altered = evaluateBacktest(changed, { volTarget: true });
  assert.deepEqual(original.weights.slice(0, 41), altered.weights.slice(0, 41));
  assert.deepEqual(original.audit.slice(0, 41).map((a) => a.estimatedVolatility), altered.audit.slice(0, 41).map((a) => a.estimatedVolatility));
});

test('proportional fees conserve equity and attain the target weight after costs', () => {
  for (const [a, w] of [[0, 1], [1, 0], [0.5, 0.8], [0.8, 0.2], [0.5, 0.5]]) {
    const c = 0.001;
    const trade = rebalance(a, w, c);
    near(trade.factor + c * Math.abs(w * trade.factor - a), 1);
    near(trade.turnover, Math.abs(w * trade.factor - a));
    near(trade.factor + trade.feeFraction, 1);
  }
  near(rebalance(0, 1, 0.001).factor, 1 / 1.001);
  near(rebalance(1, 0, 0.001).factor, 0.999);
});

test('buy-and-hold charges initial entry and final liquidation, without repeated holding fees', () => {
  const result = evaluateBenchmark(data, { costBps: 5 });
  const c = 5 / 10000;
  near(result.equity.at(-1), data.rows.at(-1).open / data.rows[60].open * (1 - c) / (1 + c));
  near(result.metrics.turnover, 1 / (1 + c) + 1);
  assert.ok(result.audit.slice(1).every((a) => a.rebalanceTurnover < 1e-14));
  near(result.audit.at(-1).finalLiquidationTurnover, 1);
});

test('cash, undefined Sharpe, CAGR, and relative peak-to-trough drawdown use documented conventions', () => {
  const cash = evaluateBacktest(flatRows(), { costBps: 0 });
  assert.equal(cash.metrics.totalReturn, 0);
  assert.equal(cash.metrics.volatility, 0);
  assert.equal(cash.metrics.sharpe, null);
  const rows = flatRows(65);
  [100, 110, 88, 100, 120].forEach((open, i) => { rows[60 + i].open = open; });
  const result = evaluateBenchmark(rows, { costBps: 0 });
  near(result.metrics.totalReturn, 0.2);
  near(result.metrics.maxDrawdown, -0.2);
  near(result.metrics.cagr, 1.2 ** (252 / 4) - 1);
});

test('target weights drift between opens and are rebalanced from actual holdings', () => {
  const result = evaluateBacktest(data, { volTarget: true });
  for (let i = 1; i < result.audit.length; i += 1) {
    const prior = result.audit[i - 1];
    near(result.audit[i].pretradeWeight, prior.weight * (1 + prior.assetReturn) / (1 + prior.weight * prior.assetReturn));
  }
  const info = calculateIndicators(data.rows, 59);
  near(result.weights[0], info.side * Math.min(1, 0.1 / info.volatility));
});

test('JavaScript arrays and all reported metrics agree with executed Python output', () => {
  const results = [...compareBacktests(data), evaluateBenchmark(data)];
  const expected = [...python.results, python.benchmark];
  for (let i = 0; i < results.length; i += 1) {
    assert.equal(results[i].id, expected[i].id);
    for (const key of ['returns', 'equity', 'weights', 'drawdowns']) {
      assert.equal(results[i][key].length, expected[i][key].length);
      results[i][key].forEach((value, index) => near(value, expected[i][key][index]));
    }
    for (const [key, value] of Object.entries(expected[i].metrics)) near(results[i].metrics[key], value);
  }
});

test('invalid prices, costs, and insufficient data fail explicitly', () => {
  assert.throws(() => evaluateBacktest(flatRows(61)), /62 price rows/);
  assert.throws(() => evaluateBacktest(data, { costBps: -1 }), /costBps/);
  assert.throws(() => evaluateBacktest(data, { targetVol: 0 }), /targetVol/);
  const invalid = flatRows();
  invalid[60].open = 0;
  assert.throws(() => evaluateBacktest(invalid), /positive/);
});
