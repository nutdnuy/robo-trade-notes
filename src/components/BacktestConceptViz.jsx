import React, {useEffect, useId, useRef, useState} from 'react';
import {timingSnapshot, volatilitySizing, drawdownRecovery} from '../lib/backtest-concepts.js';
import '../backtest-concepts.css';

const pct = (value, digits = 0) => `${(value * 100).toFixed(digits)}%`;
const num = (value, digits = 2) => Number(value.toFixed(digits)).toLocaleString('en-US', {maximumFractionDigits: digits});

function useChartSize() {
  const container = useRef(null);
  const [width, setWidth] = useState(720);
  useEffect(() => {
    if (!container.current || typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(240, entry.contentRect.width)));
    observer.observe(container.current);
    return () => observer.disconnect();
  }, []);
  return {container, width, height: width < 480 ? 240 : 270};
}

function TimingChart({snapshot, chartId}) {
  const {container, width, height} = useChartSize();
  const pad = {left: 38, right: 20, top: 30, bottom: 43};
  const x = index => pad.left + index / 3 * (width - pad.left - pad.right);
  const y = price => pad.top + (112 - price) / 16 * (height - pad.top - pad.bottom);
  const cursorIndex = snapshot.phase + 1;
  const points = snapshot.availablePoints;
  const pointLabels = ['close 0', 'open 1', 'close 1', 'open 2'];
  const futureBoundary = cursorIndex < 3 ? (x(cursorIndex) + x(cursorIndex + 1)) / 2 : null;

  return <figure className="btc-chart" ref={container}>
    <figcaption>ราคาสมมติ · หน่วยเงินต่อหุ้น</figcaption>
    <svg id={chartId} viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby={`${chartId}-title ${chartId}-desc`}>
      <title id={`${chartId}-title`}>ราคาที่รู้แล้ว เทียบกับราคาที่ยังไม่เกิดขึ้น</title>
      <desc id={`${chartId}-desc`}>{`เหตุการณ์เรียงจาก close 0, open 1, close 1 ถึง open 2 ขณะนี้อยู่ที่ ${pointLabels[cursorIndex]} เส้นทึบเป็นข้อมูลที่รู้แล้ว เส้นประถ้าปรากฏเป็นเฉลยข้อมูลอนาคตที่ใช้ตัดสินใจไม่ได้ ค่าที่ไม่ทราบจะแสดงเครื่องหมายคำถาม`}</desc>
      {futureBoundary !== null && <rect className="btc-future-region" x={futureBoundary} y={pad.top - 12} width={width - pad.right - futureBoundary} height={height - pad.bottom - pad.top + 12}/>}
      {[96, 100, 104, 108, 112].map(value => <g key={value}><line className="btc-grid" x1={pad.left} x2={width - pad.right} y1={y(value)} y2={y(value)}/><text x={pad.left - 8} y={y(value) + 4} textAnchor="end">{value}</text></g>)}
      <line className="btc-current-line" x1={x(cursorIndex)} x2={x(cursorIndex)} y1={pad.top - 12} y2={height - pad.bottom}/>
      {points.slice(1).map((point, i) => points[i].price !== null && point.price !== null ? <line key={point.id} className={`btc-price-line${point.exposedFuture ? ' btc-hindsight-line' : ''}`} x1={x(i)} x2={x(i + 1)} y1={y(points[i].price)} y2={y(point.price)}/> : null)}
      {points.map((point, i) => <g key={point.id}>
        {point.price === null ? <text className="btc-unknown-value" x={x(i)} y={y(104)} textAnchor="middle">?</text> : <><circle className={`btc-price-point${point.exposedFuture ? ' btc-hindsight-point' : ''}`} cx={x(i)} cy={y(point.price)} r={5}/><text className="btc-value-label" x={x(i)} y={y(point.price) - 13} textAnchor="middle">{point.price}</text></>}
        <text x={x(i)} y={height - 23} textAnchor="middle">{pointLabels[i]}</text>
        <text className={point.known ? 'btc-known-label' : ''} x={x(i)} y={height - 8} textAnchor="middle">{point.known ? 'รู้แล้ว' : 'อนาคต'}</text>
      </g>)}
    </svg>
    <p className="btc-chart-note">แกนนอนเรียงเหตุการณ์ ระยะห่างไม่ได้แทนเวลาจริง · พื้นสีเทาคืออนาคต ณ จุดที่เลือก</p>
  </figure>;
}

export function TimingViz() {
  const id = useId();
  const [phase, setPhase] = useState(0);
  const [showHindsight, setShowHindsight] = useState(false);
  const snapshot = timingSnapshot(phase, showHindsight);
  const chartId = `${id}-timing-chart`;
  const phases = ['1 · เปิด session 1', '2 · ปิด session 1', '3 · เปิด session 2'];
  const phaseCopy = [
    'ตอนเปิด session 1 รู้ราคาปิด session 0 เท่ากับ 99 กติกาจึงให้ถือ Cash ราคาปิดของวันนี้และราคาเปิดพรุ่งนี้ยังไม่ทราบ',
    'ราคาปิด session 1 ออกมาเป็น 108 สัญญาณจึงเปลี่ยนเป็น Long ตอนนี้ แต่ต้องรอซื้อที่ open 2 จะย้อนกลับไปซื้อที่ open 1 ไม่ได้',
    'open 2 ออกมาเป็น 110 หุ้นขึ้น 10% จาก open 1 แต่พอร์ตที่ถือ Cash ในช่วงนั้นได้ 0% คำสั่ง Long ที่เพิ่งทำได้ ณ open 2 ส่งผลต่อช่วงถัดไป',
  ];

  return <section className="btc-viz btc-timing" aria-labelledby={`${id}-heading`}>
    <header className="btc-header"><span className="btc-eyebrow">LOOK-AHEAD BIAS</span><h3 id={`${id}-heading`}>รู้ราคาปิดแล้ว ย้อนกลับไปซื้อที่ราคาเปิดได้ไหม?</h3></header>
    <p className="btc-intro">กติกาสมมติ: <strong>ราคาปิดล่าสุด &gt; 100 ให้ Long มิฉะนั้น Cash</strong> ส่งคำสั่งได้ที่ราคาเปิดถัดไป ตัวอย่างนี้แยกจากกติกา SMA 20/50 ในแล็บหลัก</p>
    <div className="btc-phase-controls" role="group" aria-label="เลื่อนไปยังเหตุการณ์เพื่อเปิดข้อมูลราคา">{phases.map((label, index) => <button key={label} type="button" aria-pressed={phase === index} aria-controls={chartId} onClick={() => setPhase(index)}>{label}</button>)}</div>
    <p className="btc-phase-status" aria-live="polite">{phaseCopy[phase]}</p>
    <TimingChart snapshot={snapshot} chartId={chartId}/>
    <div className="btc-hindsight-control"><button type="button" aria-pressed={showHindsight} aria-controls={chartId} onClick={() => setShowHindsight(value => !value)}>{showHindsight ? 'ปิดเฉลยข้อมูลอนาคต' : 'ลองเปิดเฉลยข้อมูลอนาคต'}</button><span>{showHindsight ? 'INVALID · เฉลยนี้ใช้ตัดสินใจ ณ เวลานั้นไม่ได้' : 'ข้อมูลที่ยังไม่เกิดขึ้นถูกซ่อนไว้'}</span></div>
    <div className="btc-comparison" aria-live="polite">
      <div><span className="btc-case-label">ตามเวลาจริง · ใช้ close 0</span><strong className="btc-signal">CASH ที่ open 1</strong><p>ผลช่วง open 1–open 2</p><output className="btc-result">{snapshot.actualReturn === null ? '0% · ยังไม่สิ้นช่วง' : pct(snapshot.actualReturn)}</output></div>
      <div className="btc-invalid-case"><span className="btc-case-label">INVALID · เอา close 1 มาใช้ที่ open 1</span><strong className="btc-signal">{snapshot.hindsightSignal === null ? 'close 1 ยังไม่ทราบ' : 'ย้อนเวลาให้ LONG'}</strong><p>ผลที่ backtest ผิดวิธีจะอ้าง</p><output className="btc-result">{snapshot.hindsightReturn === null ? 'รอราคา open 2' : `+${pct(snapshot.hindsightReturn)}`}</output></div>
    </div>
    <p className="btc-takeaway">สัญญาณใหม่แก้สถานะในอดีตไม่ได้ การเปิดเฉลยเปลี่ยนสิ่งที่เราเห็นบนจอ แต่ไม่เปลี่ยนข้อมูลที่ผู้ซื้อขายรู้ในตอนนั้น</p>
    <footer className="btc-footnote">ตัวอย่างสมมติจาก close 0 ถึง open 2 · หุ้นเศษส่วนได้ · Long = ลงหุ้นทั้งหมด, Cash = เงินสดทั้งหมด · ไม่คิดต้นทุนและดอกเบี้ย · ไม่มีข้อมูลตลาดจริง</footer>
  </section>;
}

export function VolatilitySizingViz() {
  const id = useId();
  const [targetVol, setTargetVol] = useState(0.10);
  const [estimatedVol, setEstimatedVol] = useState(0.20);
  const [side, setSide] = useState('long');
  const result = volatilitySizing({targetVol, estimatedVol, side});
  const formula = side === 'cash' ? 'สัญญาณ Cash → น้ำหนักหุ้น = 0%' : `น้ำหนักหุ้น = min(1, ${pct(targetVol)} ÷ ${pct(estimatedVol)}) = ${pct(result.riskyWeight, 1)}`;

  return <section className="btc-viz btc-volatility" aria-labelledby={`${id}-heading`}>
    <header className="btc-header"><span className="btc-eyebrow">VOLATILITY TARGETING</span><h3 id={`${id}-heading`}>ลดน้ำหนักอย่างไรให้ความเสี่ยงเข้าใกล้เป้า?</h3></header>
    <p className="btc-intro">เมื่อความผันผวนของสินทรัพย์สูงขึ้น ใช้เงินลงทุนน้อยลงได้โดยไม่ต้องเปลี่ยนกติกาสัญญาณ ทดลองแบ่งพอร์ตสมมติ 100 หน่วยระหว่างหุ้นกับเงินสด</p>
    <div className="btc-range-controls">
      <label htmlFor={`${id}-target`}><span>เป้า Vol ของพอร์ตต่อปี <strong>{pct(targetVol)}</strong></span><input id={`${id}-target`} type="range" min="5" max="20" step="1" value={Math.round(targetVol * 100)} aria-valuetext={`${pct(targetVol)} ต่อปี`} onChange={event => setTargetVol(Number(event.target.value) / 100)}/><small>5–20% ต่อปี</small></label>
      <label htmlFor={`${id}-estimated`}><span>Vol สินทรัพย์ที่ประเมินได้ <strong>{pct(estimatedVol)}</strong></span><input id={`${id}-estimated`} type="range" min="5" max="40" step="1" value={Math.round(estimatedVol * 100)} aria-valuetext={`${pct(estimatedVol)} ต่อปี`} onChange={event => setEstimatedVol(Number(event.target.value) / 100)}/><small>5–40% ต่อปี · สมมติว่าประเมินก่อนตัดสินใจ</small></label>
    </div>
    <div className="btc-side-controls"><span>สัญญาณขณะนี้</span><div role="group" aria-label="เลือกสัญญาณ Long หรือ Cash"><button type="button" aria-pressed={side === 'long'} onClick={() => setSide('long')}>Long</button><button type="button" aria-pressed={side === 'cash'} onClick={() => setSide('cash')}>Cash</button></div></div>
    <div className="btc-allocation" aria-live="polite">
      <div className="btc-allocation-labels"><span><i className="btc-key btc-key-shares" aria-hidden="true"/>หุ้น <strong>{pct(result.riskyWeight, 1)}</strong></span><span><i className="btc-key btc-key-cash" aria-hidden="true"/>เงินสด <strong>{pct(result.cashWeight, 1)}</strong></span></div>
      <div className="btc-allocation-bar" role="img" aria-label={`พอร์ตเต็ม 100 เปอร์เซ็นต์ แบ่งเป็นหุ้น ${pct(result.riskyWeight, 1)} และเงินสด ${pct(result.cashWeight, 1)}`}><span className="btc-share-allocation" style={{width: pct(result.riskyWeight, 6)}}/><span className="btc-cash-allocation" style={{width: pct(result.cashWeight, 6)}}/></div>
      <p className="btc-formula">{formula}</p>
    </div>
    <div className="btc-vol-result"><div><span>Vol พอร์ตที่ประมาณจากน้ำหนักนี้</span><output>{pct(result.estimatedPortfolioVol, 1)}</output><small>น้ำหนักหุ้น × Vol สินทรัพย์</small></div><p>{side === 'cash' ? 'สัญญาณ Cash ทำให้น้ำหนักหุ้นเป็นศูนย์ แม้จะกำหนดเป้า Vol ไว้ก็ตาม' : result.capped ? 'ชนเพดานลงทุน 100% แล้ว จึงไม่กู้เพิ่มเพื่อไล่ให้ถึงเป้า Vol ที่ตั้งไว้' : 'เงินส่วนที่ไม่ลงหุ้นอยู่ในเงินสด เป้า Vol ใช้กำหนดขนาดสถานะ ไม่ได้เปลี่ยนสัญญาณ Long ให้ถูกต้องขึ้น'}</p></div>
    <p className="btc-takeaway">นี่คือการประมาณภายใต้สมมติฐานอย่างง่าย ความผันผวนที่เกิดจริงอาจต่างจากค่าที่ประเมิน และ Vol targeting ไม่ได้รับประกันว่าจะลด drawdown หรือไม่ขาดทุน</p>
    <footer className="btc-footnote">สมมติหุ้นหนึ่งตัว เงินสดให้ผลตอบแทน 0% และไม่มีความผันผวน · ไม่มี leverage · ใช้ Vol ต่อปีในหน่วยเดียวกัน · ไม่รวมต้นทุนและความคลาดเคลื่อนของการประมาณ</footer>
  </section>;
}

function RecoveryChart({result, chartId}) {
  const {container, width, height} = useChartSize();
  const pad = {left: 38, right: 22, top: 32, bottom: 52};
  const x = index => pad.left + index / 2 * (width - pad.left - pad.right);
  const y = value => pad.top + (110 - value) / 110 * (height - pad.top - pad.bottom);
  const labels = ['ยอดเดิม', 'หลังขาดทุน', 'ฟื้น %'];
  const points = result.wealth;
  return <figure className="btc-chart" ref={container}>
    <figcaption>ดัชนีมูลค่าพอร์ต · ยอดเดิม = 100</figcaption>
    <svg id={chartId} viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby={`${chartId}-title ${chartId}-desc`}>
      <title id={`${chartId}-title`}>ฟื้นด้วยเปอร์เซ็นต์เท่าที่ขาดทุน ยังกลับไม่ถึงยอดเดิม</title>
      <desc id={`${chartId}-desc`}>{`พอร์ตเริ่มที่ 100 ลดลง ${pct(result.loss)} เหลือ ${num(result.trough)} แล้วเพิ่ม ${pct(result.loss)} จากฐานที่ต่ำลง ได้ ${num(result.samePercentRecoveryValue)} เส้นอ้างอิงที่ 100 คือเป้ากลับทุนเดิม`}</desc>
      {[0, 25, 50, 75, 100].map(value => <g key={value}><line className={`btc-grid${value === 100 ? ' btc-peak-line' : ''}`} x1={pad.left} x2={width - pad.right} y1={y(value)} y2={y(value)}/><text x={pad.left - 8} y={y(value) + 4} textAnchor="end">{value}</text></g>)}
      <polyline className="btc-price-line" points={points.map((value, index) => `${x(index)},${y(value)}`).join(' ')}/>
      <line className="btc-recovery-gap" x1={x(2)} x2={x(2)} y1={y(result.samePercentRecoveryValue)} y2={y(100)}/>
      <circle className="btc-peak-point" cx={x(2)} cy={y(100)} r={4}/>
      {points.map((value, index) => <g key={index}><circle className="btc-price-point" cx={x(index)} cy={y(value)} r={5}/><text className="btc-value-label" x={x(index)} y={y(value) + (index === 2 && 100 - value < 10 ? 23 : -13)} textAnchor="middle">{num(value)}</text><text x={x(index)} y={height - 23} textAnchor={index === 0 ? 'start' : index === 2 ? 'end' : 'middle'}>{labels[index]}{index === 2 && <tspan x={x(index)} dy={15}>เท่าที่เสีย</tspan>}</text></g>)}
    </svg>
    <p className="btc-chart-note">เส้นอ้างอิงสีเขียว = ทุนเดิม 100 · ตัวเลขบนเส้นม่วงคือมูลค่าจริงของตัวอย่างแต่ละช่วง</p>
  </figure>;
}

export function DrawdownRecoveryViz() {
  const id = useId();
  const [loss, setLoss] = useState(0.20);
  const result = drawdownRecovery(loss);
  return <section className="btc-viz btc-drawdown" aria-labelledby={`${id}-heading`}>
    <header className="btc-header"><span className="btc-eyebrow">DRAWDOWN & RECOVERY</span><h3 id={`${id}-heading`}>ขาดทุน {pct(loss)} ต้องฟื้นเท่าไรถึงทุนเดิม?</h3></header>
    <p className="btc-intro">เปอร์เซ็นต์ขาดทุนคิดจากยอดเดิม แต่เปอร์เซ็นต์ฟื้นตัวคิดจากเงินที่เหลือ ฐานที่ต่างกันทำให้ตัวเลขขาลงและขากลับไม่เท่ากัน</p>
    <label className="btc-loss-control" htmlFor={`${id}-loss`}><span>ลดลงจากยอดสูงสุด <strong>{pct(loss)}</strong></span><input id={`${id}-loss`} type="range" min="5" max="60" step="1" value={Math.round(loss * 100)} aria-valuetext={`ขาดทุน ${pct(loss)} จากยอดสูงสุด`} onChange={event => setLoss(Number(event.target.value) / 100)}/><small>5–60% · ยอดเริ่มต้น 100</small></label>
    <RecoveryChart result={result} chartId={`${id}-recovery-chart`}/>
    <div className="btc-recovery-results" aria-live="polite"><div><span>ถ้าฟื้นเพียง {pct(loss)}</span><output>{num(result.samePercentRecoveryValue)}</output><small>ยังต่ำกว่ายอดเดิม 100</small></div><div><span>ต้องฟื้นจาก {num(result.trough)} ให้ถึง 100</span><output>+{pct(result.requiredRecovery, 2)}</output><small>คิดจากมูลค่าหลังขาดทุน</small></div></div>
    <p className="btc-formula">ผลตอบแทนที่ต้องได้ = {pct(loss)} ÷ (1 − {pct(loss)}) = {pct(result.requiredRecovery, 2)}</p>
    <p className="btc-takeaway">ที่ขาดทุน {pct(loss)} พอร์ตเหลือ {num(result.trough)} การเพิ่ม {pct(loss)} ของฐานนี้ได้ {num(result.trough * loss)} หน่วย จึงจบที่ {num(result.samePercentRecoveryValue)} ไม่ใช่ 100</p>
    <footer className="btc-footnote">ตัวอย่างเลขคณิตสมมติ 3 จุด ไม่มีต้นทุนหรือเงินไหลเข้าออก · ไม่ได้ทำนายว่าจะฟื้นตัวได้จริง · Drawdown วัดการลดลงจากยอดสูงสุดและไม่ปรับเป็นรายปี</footer>
  </section>;
}
