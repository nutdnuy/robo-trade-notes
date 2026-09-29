import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {rankBy, bestPair, pairKey, colorScale, RAMP} from '../src/lib/optimization.js';

const data = JSON.parse(readFileSync(new URL('../public/downloads/optimization-results.json', import.meta.url), 'utf8'));
const byKey = new Map(data.grid.map(row => [pairKey(row.f, row.s), row]));

test('grid covers every fast<slow pair exactly once', () => {
  const {fastSpans, slowSpans} = data.metadata;
  const expected = fastSpans.flatMap(f => slowSpans.filter(s => f < s).map(s => pairKey(f, s)));
  assert.equal(data.grid.length, 484);
  assert.deepEqual(data.grid.map(row => pairKey(row.f, row.s)), expected);
});

test('EMA 20/200 over the full window reproduces chapter 14', () => {
  const full = byKey.get('20/200').full;
  assert.equal(full.sharpe, 0.6567);
  assert.equal(full.cagr, 0.0802);
  assert.equal(full.mdd, -0.2667);
  assert.equal(full.trades, 17);
});

test('highlighted pairs are the arg-max of their windows', () => {
  const pickIs = bestPair(data.grid, 'is');
  assert.deepEqual([pickIs.f, pickIs.s], data.highlights.bestInSample);
  const pickFull = bestPair(data.grid, 'full');
  assert.deepEqual([pickFull.f, pickFull.s], data.highlights.bestFull);
});

test('prose numbers match the data', () => {
  const pick = pairKey(...data.highlights.bestInSample);
  assert.equal(pick, '65/120');
  assert.equal(rankBy(data.grid, 'oos').get(pick), 197);
  assert.equal(rankBy(data.grid, 'oos').get('20/200'), 101);
  assert.equal(rankBy(data.grid, 'is').get('20/200'), 439);
  assert.equal(rankBy(data.grid, 'full').get('20/200'), 237);
  assert.equal(data.rankCorrelation.toFixed(2), "-0.09");
  assert.equal(data.grid.filter(row => row.oos.sharpe > row.is.sharpe).length, 475);
  const wf = data.walkForward;
  assert.equal(wf.steps.length, 15);
  assert.equal(new Set(wf.steps.map(s => pairKey(s.fast, s.slow))).size, 9);
  assert.equal(wf.metrics.walkForward.trades, 24);
  const last = data.noise.summary.at(-1);
  assert.deepEqual([data.noise.summary[0].is, data.noise.summary[0].oos, last.is, last.oos].map(v => v.toFixed(2)), ['0.30', '0.31', '0.57', '0.36']);
});

test('walk-forward only trains on data before each test year', () => {
  for (const step of data.walkForward.steps) {
    assert.ok(step.trainStart < step.testStart);
    assert.ok(step.testStart <= step.testEnd);
  }
});

test('colour scale maps the extremes to the ramp ends', () => {
  const scale = colorScale([0, 1]);
  assert.equal(scale(0), RAMP[0]);
  assert.equal(scale(1), RAMP.at(-1));
});
