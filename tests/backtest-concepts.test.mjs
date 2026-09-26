import test from 'node:test';
import assert from 'node:assert/strict';
import { timingSnapshot, volatilitySizing, drawdownRecovery } from '../src/lib/backtest-concepts.js';

const near = (actual, expected, tolerance = 1e-12) => {
  assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)), `${actual} != ${expected}`);
};

test('Open 1 has only previously observed prices and no completed interval return', () => {
  const snapshot = timingSnapshot();
  assert.deepEqual(snapshot.availablePoints.map((point) => [point.id, point.price, point.known, point.exposedFuture]), [
    ['close0', 99, true, false], ['open1', 100, true, false],
    ['close1', null, false, false], ['open2', null, false, false],
  ]);
  assert.equal(snapshot.latestAvailableClose, 99);
  assert.equal(snapshot.currentSignal, 0);
  assert.equal(snapshot.executionSignal, 0);
  assert.equal(snapshot.nextOpenKnown, false);
  assert.equal(snapshot.nextOpenPrice, null);
  assert.equal(snapshot.actualReturn, null);
  assert.equal(snapshot.hindsightReturn, null);
  assert.equal(snapshot.hindsightSignal, null);
});

test('Close 1 updates the current signal without retroactively changing the Open 1 position', () => {
  const snapshot = timingSnapshot(1);
  assert.equal(snapshot.availablePoints.find((point) => point.id === 'close1').price, 108);
  assert.equal(snapshot.availablePoints.find((point) => point.id === 'open2').price, null);
  assert.equal(snapshot.latestAvailableClose, 108);
  assert.equal(snapshot.currentSignal, 1);
  assert.equal(snapshot.executionSignal, 0);
  assert.equal(snapshot.hindsightSignal, 1);
  assert.equal(snapshot.nextOpenKnown, false);
  assert.equal(snapshot.nextOpenPrice, null);
  assert.equal(snapshot.actualReturn, null);
  assert.equal(snapshot.hindsightReturn, null);
});

test('Open 2 distinguishes cash return from the impossible ten-percent hindsight trade', () => {
  const snapshot = timingSnapshot(2);
  assert.ok(snapshot.availablePoints.every((point) => point.known && !point.exposedFuture));
  assert.equal(snapshot.nextOpenKnown, true);
  assert.equal(snapshot.entryPrice, 100);
  assert.equal(snapshot.nextOpenPrice, 110);
  assert.equal(snapshot.executionSignal, 0);
  assert.equal(snapshot.actualReturn, 0);
  near(snapshot.hindsightReturn, 0.1);
  near(snapshot.nextOpenPrice / snapshot.entryPrice - 1, snapshot.hindsightReturn);
});

test('explicit hindsight reveal marks every future value and preserves the real information set', () => {
  for (const phase of [0, 1, 2]) {
    const ordinary = timingSnapshot(phase);
    const revealed = timingSnapshot(phase, true);
    assert.equal(revealed.latestAvailableClose, ordinary.latestAvailableClose);
    assert.equal(revealed.currentSignal, ordinary.currentSignal);
    assert.equal(revealed.executionSignal, ordinary.executionSignal);
    assert.equal(revealed.nextOpenKnown, ordinary.nextOpenKnown);
    assert.equal(revealed.actualReturn, ordinary.actualReturn);
    assert.equal(revealed.hindsightSignal, 1);
    near(revealed.hindsightReturn, 0.1);
    for (const point of revealed.availablePoints) {
      assert.equal(point.exposedFuture, !point.known);
      assert.equal(typeof point.price, 'number');
    }
  }
});

test('ten-percent target and twenty-percent estimated volatility allocate half to cash', () => {
  const sizing = volatilitySizing();
  near(sizing.riskyWeight, 0.5);
  near(sizing.cashWeight, 0.5);
  near(sizing.uncappedWeight, 0.5);
  near(sizing.estimatedPortfolioVol, 0.1);
  assert.equal(sizing.capped, false);
});

test('the exposure cap prevents borrowing and can leave expected risk below the target', () => {
  const sizing = volatilitySizing({ targetVol: 0.2, estimatedVol: 0.05 });
  assert.equal(sizing.riskyWeight, 1);
  assert.equal(sizing.cashWeight, 0);
  assert.equal(sizing.uncappedWeight, 4);
  assert.equal(sizing.capped, true);
  near(sizing.estimatedPortfolioVol, 0.05);
  assert.ok(sizing.estimatedPortfolioVol < sizing.targetVol);
  assert.equal(volatilitySizing({ targetVol: 0.2, estimatedVol: 0.2 }).capped, false);
});

test('a cash signal has zero risky exposure and zero estimated portfolio volatility', () => {
  const sizing = volatilitySizing({ targetVol: 0.2, estimatedVol: 0.05, side: 'cash' });
  assert.equal(sizing.riskyWeight, 0);
  assert.equal(sizing.uncappedWeight, 0);
  assert.equal(sizing.estimatedPortfolioVol, 0);
  assert.equal(sizing.cashWeight, 1);
  assert.equal(sizing.capped, false);
});

test('a twenty-percent drawdown requires twenty-five percent recovery, not twenty', () => {
  const result = drawdownRecovery();
  assert.equal(result.peak, 100);
  assert.equal(result.trough, 80);
  assert.equal(result.samePercentRecoveryValue, 96);
  near(result.requiredRecovery, 0.25);
  near(result.trough * (1 + result.requiredRecovery), result.recoveredValue);
  assert.deepEqual(result.wealth, [100, 80, 96]);
});

test('recovery uses the smaller post-loss base, including zero and severe drawdowns', () => {
  assert.deepEqual(drawdownRecovery(0).wealth, [100, 100, 100]);
  assert.equal(drawdownRecovery(0).requiredRecovery, 0);
  for (const loss of [0.1, 0.5, 0.9, 0.99]) {
    const result = drawdownRecovery(loss);
    near(result.trough * (1 + result.requiredRecovery), 100);
    assert.ok(result.requiredRecovery > loss);
    assert.ok(result.samePercentRecoveryValue < 100);
  }
});

test('invalid inputs fail explicitly instead of producing invalid teaching outputs', () => {
  for (const phase of [-1, 3, 0.5, NaN, Infinity, '1', null]) {
    assert.throws(() => timingSnapshot(phase), /phase/);
  }
  assert.throws(() => timingSnapshot(0, 'yes'), /showHindsight/);
  for (const value of [0, -0.1, NaN, Infinity, '0.2', null]) {
    assert.throws(() => volatilitySizing({ targetVol: value }), /targetVol/);
    assert.throws(() => volatilitySizing({ estimatedVol: value }), /estimatedVol/);
  }
  assert.throws(() => volatilitySizing({ side: 'short' }), /side/);
  assert.throws(() => volatilitySizing({ targetVol: Number.MAX_VALUE, estimatedVol: Number.MIN_VALUE }), /finite/);
  for (const loss of [-0.1, 1, 2, NaN, Infinity, '0.2', null]) {
    assert.throws(() => drawdownRecovery(loss), /loss/);
  }
});
