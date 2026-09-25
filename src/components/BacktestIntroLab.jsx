import React, {useEffect, useId, useMemo, useRef, useState} from 'react';
import {compareBacktests, evaluateBenchmark} from '../lib/backtest-intro.js';
import data from '../../public/downloads/backtest-intro-data.json';
import '../backtest-intro.css';

const MODES = {
  'causal-fixed': {name: 'รู้ข้อมูลตามเวลา · น้ำหนักคงที่', short: 'ตามเวลา · คงที่', className: 'bti-causal-fixed', number: '1'},
  'causal-target': {name: 'รู้ข้อมูลตามเวลา · Vol targeting', short: 'ตามเวลา · Vol target', className: 'bti-causal-target', number: '2'},
  'biased-fixed': {name: 'แอบใช้ข้อมูลอนาคต · น้ำหนักคงที่', short: 'ข้อมูลอนาคต · คงที่', className: 'bti-biased-fixed', number: '3'},
  'biased-target': {name: 'แอบใช้ข้อมูลอนาคต · Vol targeting', short: 'ข้อมูลอนาคต · Vol target', className: 'bti-biased-target', number: '4'},
};

const percent = value => Number.isFinite(value) ? `${(value * 100).toFixed(2)}%` : '—';
const decimal = value => Number.isFinite(value) ? value.toFixed(2) : '—';

function makeTicks(min, max) {
  const range = Math.max(max - min, 0.01);
  const rough = range / 4;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const factor = rough / magnitude;
  const step = (factor <= 1 ? 1 : factor <= 2 ? 2 : factor <= 5 ? 5 : 10) * magnitude;
  const low = Math.floor(min / step) * step;
  const high = Math.ceil(max / step) * step;
  return Array.from({length: Math.round((high - low) / step) + 1}, (_, i) => low + i * step);
}

function ComparisonChart({results, view, selected, chartId}) {
  const holder = useRef(null);
  const [width, setWidth] = useState(700);
  useEffect(() => {
    if (!holder.current || typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(240, entry.contentRect.width)));
    observer.observe(holder.current);
    return () => observer.disconnect();
  }, []);

  const height = width < 480 ? 252 : 300;
  const pad = {left: 44, right: 16, top: 18, bottom: 34};
  const series = results.map(result => ({
    ...MODES[result.id],
    id: result.id,
    values: (view === 'equity' ? result.equity : result.drawdowns).map(value => value * 100),
  }));
  const values = series.flatMap(item => item.values);
  const observedMin = Math.min(...values);
  const observedMax = Math.max(...values);
  const margin = Math.max((observedMax - observedMin) * 0.08, view === 'equity' ? 1 : 0.5);
  const ticks = makeTicks(observedMin - margin, view === 'equity' ? observedMax + margin : 0);
  const min = ticks[0];
  const max = ticks.at(-1);
  const sessions = results[0].sessions;
  const x = index => pad.left + index / (sessions.length - 1) * (width - pad.left - pad.right);
  const y = value => pad.top + (max - value) / (max - min) * (height - pad.top - pad.bottom);
  const xTickCount = width < 480 ? 4 : 6;
  const tickIndices = Array.from({length: xTickCount}, (_, i) => Math.round(i / (xTickCount - 1) * (sessions.length - 1)));
  const title = view === 'equity' ? 'ดัชนีมูลค่าพอร์ต เริ่มที่ 100' : 'Drawdown จากยอดสูงสุดของพอร์ต';
  const axisFormat = value => `${Number(value.toFixed(1))}${view === 'drawdown' ? '%' : ''}`;

  return <div className="bti-chart" ref={holder}>
    <p className="bti-chart-unit">{title}</p>
    <svg id={chartId} viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby={`${chartId}-title ${chartId}-description`}>
      <title id={`${chartId}-title`}>{`${title} · เปรียบเทียบ 4 วิธีบนข้อมูลสังเคราะห์`}</title>
      <desc id={`${chartId}-description`}>แกนนอนเป็นลำดับ session {sessions[0]} ถึง {sessions.at(-1)} เส้นทึบใช้ข้อมูลที่รู้ก่อนซื้อขาย เส้นประแอบใช้ข้อมูลอนาคตและทำจริงไม่ได้ ใช้ตัวเลื่อนใต้กราฟเพื่ออ่านค่าของทั้งสี่เส้น</desc>
      {ticks.map(tick => <g key={tick}>
        <line className={`bti-grid${(view === 'equity' && tick === 100) || tick === 0 ? ' bti-baseline' : ''}`} x1={pad.left} x2={width - pad.right} y1={y(tick)} y2={y(tick)}/>
        <text x={pad.left - 8} y={y(tick) + 4} textAnchor="end">{axisFormat(tick)}</text>
      </g>)}
      {tickIndices.map(index => <text key={index} x={x(index)} y={height - 9} textAnchor="middle">{sessions[index]}</text>)}
      {series.map(item => <path key={item.id} className={`bti-series ${item.className}`} d={item.values.map((value, index) => `${index === 0 ? 'M' : 'L'}${x(index).toFixed(2)},${y(value).toFixed(2)}`).join(' ')}/>)}
      <line className="bti-cursor" x1={x(selected)} x2={x(selected)} y1={pad.top} y2={height - pad.bottom}/>
      {series.map(item => <circle key={item.id} className={`bti-point ${item.className}`} cx={x(selected)} cy={y(item.values[selected])} r={4}/>)}
    </svg>
    <p className="bti-x-label">ลำดับ session สมมติ · ไม่มีวันที่ตลาดจริง</p>
  </div>;
}

export default function BacktestIntroLab() {
  const id = useId();
  const [costBps, setCostBps] = useState(5);
  const [targetVol, setTargetVol] = useState(0.1);
  const [view, setView] = useState('equity');
  const results = useMemo(() => compareBacktests(data, {costBps, targetVol}), [costBps, targetVol]);
  const benchmark = useMemo(() => evaluateBenchmark(data, {costBps}), [costBps]);
  const sessions = results[0].sessions;
  const [selected, setSelected] = useState(sessions.length - 1);
  const firstSession = sessions[0];
  const lastSession = sessions.at(-1);
  const chartId = `${id}-chart`;

  function reset() {
    setCostBps(5);
    setTargetVol(0.1);
    setView('equity');
    setSelected(sessions.length - 1);
  }

  return <section className="backtest-intro-lab" aria-labelledby={`${id}-title`}>
    <header className="bti-header">
      <div><span className="bti-eyebrow">BACKTEST EXPERIMENT</span><h3 id={`${id}-title`}>กติกาเดิม ผลต่างกันเพราะอะไร?</h3></div>
      <span className="bti-data-label">ข้อมูลสังเคราะห์</span>
    </header>
    <p className="bti-lead">เปรียบเทียบเวลาใช้ข้อมูลและการกำหนดน้ำหนักบนราคาเส้นเดียวกัน ทั้งสี่วิธีใช้ SMA 20/50 ชุดเดิม ลองเปลี่ยนต้นทุนและเป้าความผันผวน แล้วอ่านทั้งผลตอบแทนและความเสี่ยง</p>

    <div className="bti-controls">
      <label htmlFor={`${id}-cost`}>
        <span>ต้นทุนต่อข้าง <strong>{costBps} bps</strong></span>
        <input id={`${id}-cost`} type="range" min="0" max="20" step="1" value={costBps} aria-valuetext={`${costBps} basis points หรือ ${(costBps / 100).toFixed(2)} เปอร์เซ็นต์ต่อมูลค่าซื้อขาย`} onChange={event => setCostBps(Number(event.target.value))}/>
        <small>0–20 bps · 1 bp = 0.01% ของมูลค่าซื้อขาย</small>
      </label>
      <label htmlFor={`${id}-vol`}>
        <span>เป้าความผันผวนต่อปี <strong>{Math.round(targetVol * 100)}%</strong></span>
        <input id={`${id}-vol`} type="range" min="5" max="20" step="1" value={Math.round(targetVol * 100)} aria-valuetext={`${Math.round(targetVol * 100)} เปอร์เซ็นต์ต่อปี`} onChange={event => setTargetVol(Number(event.target.value) / 100)}/>
        <small>5–20% · ใช้กับวิธี Vol targeting เท่านั้น</small>
      </label>
    </div>
    <div className="bti-settings"><p>กติกาคงที่: SMA 20/50 · Vol ย้อนหลัง 20 ผลตอบแทน · ถือหุ้น 0–100% · ไม่ใช้ leverage</p><button type="button" onClick={reset}>คืนค่าเริ่มต้น</button></div>

    <div className="bti-chart-heading">
      <p>เส้นทึบ: รู้ข้อมูลตามเวลา<br/><span>เส้นประ: ใช้ข้อมูลอนาคต ทำจริงไม่ได้</span></p>
      <div className="bti-view-controls" role="group" aria-label="เลือกมุมมองกราฟ">
        <button type="button" aria-pressed={view === 'equity'} aria-controls={chartId} onClick={() => setView('equity')}>มูลค่าพอร์ต</button>
        <button type="button" aria-pressed={view === 'drawdown'} aria-controls={chartId} onClick={() => setView('drawdown')}>Drawdown</button>
      </div>
    </div>
    <ul className="bti-legend" aria-label="คำอธิบายเส้นกราฟ">{results.map(result => <li key={result.id}><span className={`bti-swatch ${MODES[result.id].className}`} aria-hidden="true"/><span>{MODES[result.id].number}. {MODES[result.id].name}</span></li>)}</ul>
    <ComparisonChart results={results} view={view} selected={selected} chartId={chartId}/>

    <div className="bti-scrubber">
      <label htmlFor={`${id}-session`}>อ่านค่าที่ session <strong>{sessions[selected]}</strong></label>
      <input id={`${id}-session`} type="range" min="0" max={sessions.length - 1} step="1" value={selected} aria-valuetext={`session ${sessions[selected]}`} onChange={event => setSelected(Number(event.target.value))}/>
    </div>
    <dl className="bti-readout" aria-live="polite" aria-atomic="true">{results.map(result => <div key={result.id}>
      <dt><span className={`bti-swatch ${MODES[result.id].className}`} aria-hidden="true"/>{MODES[result.id].number}. {MODES[result.id].short}</dt>
      <dd>{view === 'equity' ? decimal(result.equity[selected] * 100) : percent(result.drawdowns[selected])}<small>{view === 'equity' ? 'ดัชนีมูลค่าพอร์ต' : 'จากยอดสูงสุด'}</small></dd>
    </div>)}</dl>

    <div className="bti-table-wrap" tabIndex={0} role="region" aria-label="ตารางสรุปผลทั้งสี่วิธี เลื่อนแนวนอนเพื่ออ่านทุกคอลัมน์">
      <table className="bti-table">
        <caption>ผลหลังต้นทุน · {results[0].returns.length} ช่วงผลตอบแทนเดียวกัน · session {firstSession}–{lastSession}</caption>
        <thead><tr><th scope="col">วิธีทดสอบ</th><th scope="col">Return</th><th scope="col">CAGR</th><th scope="col">Vol / ปี</th><th scope="col">Sharpe</th><th scope="col">Max DD</th><th scope="col">Turnover</th></tr></thead>
        <tbody>{results.map(result => <tr key={result.id}>
          <th scope="row"><span className={`bti-swatch ${MODES[result.id].className}`} aria-hidden="true"/>{MODES[result.id].number}. {MODES[result.id].name}{result.id.startsWith('biased') && <small>ตัวอย่างข้อผิดพลาด · ทำจริงไม่ได้</small>}</th>
          <td>{percent(result.metrics.totalReturn)}</td><td>{percent(result.metrics.cagr)}</td><td>{percent(result.metrics.volatility)}</td><td>{decimal(result.metrics.sharpe)}</td><td>{percent(result.metrics.maxDrawdown)}</td><td>{decimal(result.metrics.turnover)}×</td>
        </tr>)}<tr className="bti-benchmark-row"><th scope="row">ซื้อแล้วถือ · Buy and hold<small>แถวอ้างอิง · ไม่แสดงในกราฟ</small></th><td>{percent(benchmark.metrics.totalReturn)}</td><td>{percent(benchmark.metrics.cagr)}</td><td>{percent(benchmark.metrics.volatility)}</td><td>{decimal(benchmark.metrics.sharpe)}</td><td>{percent(benchmark.metrics.maxDrawdown)}</td><td>{decimal(benchmark.metrics.turnover)}×</td></tr></tbody>
      </table>
    </div>
    <p className="bti-metric-note">Return คือผลตอบแทนรวมในช่วงทดสอบ · CAGR, Vol และ Sharpe ใช้ 252 ช่วงต่อปี และอัตราปลอดความเสี่ยง 0% · Max DD วัดจากจุดมูลค่าพอร์ตที่ราคาเปิด ไม่รวมความเคลื่อนไหวระหว่างวัน และไม่ปรับเป็นรายปี · Turnover คือผลรวมสัดส่วนมูลค่าซื้อขายต่อพอร์ต ณ แต่ละการซื้อขาย รวมการเข้าครั้งแรกและปิดสถานะท้ายช่วง · ทุกวิธีใช้ต้นทุนต่อข้างเดียวกัน</p>

    <div className="bti-lesson-note"><strong>ผลสูงหรือต่ำ ก็ใช้ข้อมูลอนาคตไม่ได้</strong><p>วิธีรู้ข้อมูลตามเวลาใช้ราคาปิด t−1 ก่อนซื้อขายที่ราคาเปิด t ส่วนวิธีเส้นประใช้ราคาปิด t ย้อนกลับไปซื้อขายที่ราคาเปิด t จึงรู้สิ่งที่ยังไม่เกิดขึ้น ทั้งสัญญาณและค่า Vol ในวิธีเส้นประมี look-ahead bias ผลจึงใช้ประเมินการซื้อขายจริงไม่ได้ ไม่ว่าจะสูงหรือต่ำกว่า</p><p>Vol targeting ปรับขนาดการถือครอง และเป้าหมายอาจไม่เท่าความผันผวนที่เกิดจริง การปรับตัวเลื่อนนี้ใช้สำรวจสมมติฐาน ไม่ใช่ค้นหาค่าที่ทำให้ผลย้อนหลังสวยที่สุด</p></div>
    <footer className="bti-footnote">ชุดข้อมูลสังเคราะห์ {data.metadata.sessions} sessions · seed {data.metadata.seed} · ประเมิน open-to-open ช่วง {firstSession}→{firstSession + 1} ถึง {lastSession - 1}→{lastSession} · เริ่มดัชนี 100 ก่อนต้นทุนเข้า และรวมต้นทุนปิดสถานะท้ายช่วง · เงินสดให้ผลตอบแทน 0% · ไม่มีข้อมูลตลาดหรือคำสั่งซื้อขายจริง</footer>
  </section>;
}
