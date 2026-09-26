// Small, hypothetical examples for the introductory concept controls.
// Signals may change as information arrives, but cannot change an earlier trade.
const TIMING_POINTS = [
  { id: 'close0', label: 'Close 0', session: 0, event: 'close', price: 99, firstKnownPhase: 0 },
  { id: 'open1', label: 'Open 1', session: 1, event: 'open', price: 100, firstKnownPhase: 0 },
  { id: 'close1', label: 'Close 1', session: 1, event: 'close', price: 108, firstKnownPhase: 1 },
  { id: 'open2', label: 'Open 2', session: 2, event: 'open', price: 110, firstKnownPhase: 2 },
];

export const TIMING_PHASES = Object.freeze([
  'Open 1 · เริ่มช่วงถือครอง',
  'Close 1 · รับข้อมูลใหม่',
  'Open 2 · สิ้นสุดช่วงถือครอง',
]);

export function timingSnapshot(phase = 0, showHindsight = false) {
  if (!Number.isInteger(phase) || phase < 0 || phase >= TIMING_PHASES.length) {
    throw new RangeError('phase must be an integer from 0 to 2');
  }
  if (typeof showHindsight !== 'boolean') {
    throw new TypeError('showHindsight must be a boolean');
  }

  const latestAvailableClose = phase === 0 ? 99 : 108;
  const currentSignal = latestAvailableClose > 100 ? 1 : 0;
  const executionSignal = 0; // Close 0 = 99 was the only close known at Open 1.
  const nextOpenKnown = phase === 2;
  const exposeOutcome = nextOpenKnown || showHindsight;
  const hindsightSignal = phase > 0 || showHindsight ? 1 : null;
  const entryPrice = 100;
  const nextOpenPrice = exposeOutcome ? 110 : null;
  const messages = [
    'ที่ Open 1 รู้ราคาปิดล่าสุดเพียง Close 0 = 99 จึงถือ Cash ราคาปิด Close 1 และราคา Open 2 ยังเป็นอนาคต',
    'เมื่อ Close 1 = 108 ปรากฏ สัญญาณเปลี่ยนเป็น Long สำหรับการซื้อที่ Open 2 แต่ย้อนกลับไปซื้อที่ Open 1 ไม่ได้',
    'ช่วง Open 1 → Open 2 จบแล้ว การถือ Cash ได้ 0% ส่วน 10% เกิดจากสมมติให้รู้ Close 1 ล่วงหน้าและซื้อที่ Open 1 ซึ่งทำจริงไม่ได้',
  ];

  return {
    phase,
    phaseLabel: TIMING_PHASES[phase],
    availablePoints: TIMING_POINTS.map(({ firstKnownPhase, price, ...point }) => {
      const known = firstKnownPhase <= phase;
      const exposedFuture = !known && showHindsight;
      return { ...point, price: known || exposedFuture ? price : null, known, exposedFuture };
    }),
    latestAvailableClose,
    currentSignal,
    executionSignal,
    nextOpenKnown,
    actualReturn: nextOpenKnown ? 0 : null,
    hindsightReturn: exposeOutcome ? (110 - entryPrice) / entryPrice : null,
    entryPrice,
    nextOpenPrice,
    hindsightSignal,
    informationMessage: messages[phase] + (showHindsight && !nextOpenKnown
      ? ' กำลังเปิดดูข้อมูลอนาคตเพื่อสาธิตข้อผิดพลาด ข้อมูลนี้ไม่เปลี่ยนสัญญาณที่ตัดสินใจได้จริงในเวลานั้น'
      : ''),
  };
}

export function volatilitySizing({ targetVol = 0.10, estimatedVol = 0.20, side = 'long' } = {}) {
  for (const [name, value] of Object.entries({ targetVol, estimatedVol })) {
    if (!Number.isFinite(value) || value <= 0) {
      throw new RangeError(`${name} must be finite and positive`);
    }
  }
  if (side !== 'long' && side !== 'cash') {
    throw new RangeError('side must be long or cash');
  }

  const uncappedWeight = side === 'long' ? targetVol / estimatedVol : 0;
  if (!Number.isFinite(uncappedWeight)) {
    throw new RangeError('targetVol / estimatedVol must be finite');
  }
  const riskyWeight = Math.min(1, uncappedWeight);
  return {
    targetVol,
    estimatedVol,
    side,
    riskyWeight,
    cashWeight: 1 - riskyWeight,
    estimatedPortfolioVol: riskyWeight * estimatedVol,
    capped: uncappedWeight > 1,
    uncappedWeight,
  };
}

export function drawdownRecovery(loss = 0.20) {
  if (!Number.isFinite(loss) || loss < 0 || loss >= 1) {
    throw new RangeError('loss must be finite and between 0 (inclusive) and 1 (exclusive)');
  }
  const peak = 100;
  const trough = peak * (1 - loss);
  const samePercentRecoveryValue = trough * (1 + loss);
  return {
    loss,
    peak,
    trough,
    samePercentRecoveryValue,
    requiredRecovery: loss / (1 - loss),
    recoveredValue: peak,
    wealth: [peak, trough, samePercentRecoveryValue],
  };
}
