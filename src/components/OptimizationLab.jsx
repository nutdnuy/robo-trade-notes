import React, {useEffect, useId, useMemo, useRef, useState} from 'react';
import data from '../../public/downloads/optimization-results.json';
import {METRICS, PERIODS, RAMP, bestPair, colorScale, formatPercent, niceTicks, pairKey, percentile, rankBy, rebase} from '../lib/optimization.js';
import '../optimization.css';

const SERIES_CLASS = {pick: 'opt-pick', baseline: 'opt-baseline', hold: 'opt-hold', walk: 'opt-pick'};
const grid = data.grid;
const lookup = new Map(grid.map(row => [pairKey(row.f, row.s), row]));
const [pickFast, pickSlow] = data.highlights.bestInSample;
const pickKey = pairKey(pickFast, pickSlow);
const baselineKey = pairKey(20, 200);

function useWidth(initial = 700) {
  const ref = useRef(null);
  const [width, setWidth] = useState(initial);
  useEffect(() => {
    if (!ref.current || typeof ResizeObserver === 'undefined') return undefined;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(260, entry.contentRect.width)));
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}

function Segmented({label, options, value, onChange, controls}) {
  return <div className="opt-segmented" role="group" aria-label={label}>
    {options.map(([id, text]) => <button key={id} type="button" aria-pressed={value === id} aria-controls={controls} onClick={() => onChange(id)}>{text}</button>)}
  </div>;
}

function Frame({eyebrow, title, label, lead, children, id}) {
  return <section className="opt-lab" aria-labelledby={`${id}-title`}>
    <header className="opt-header">
      <div><span className="opt-eyebrow">{eyebrow}</span><h3 id={`${id}-title`}>{title}</h3></div>
      <span className="opt-data-label">{label}</span>
    </header>
    {lead && <p className="opt-lead">{lead}</p>}
    {children}
  </section>;
}

/* ------------------------------------------------------------------ heatmap */

export function ParameterHeatmap() {
  const id = useId();
  const [period, setPeriod] = useState('full');
  const [metric, setMetric] = useState('sharpe');
  const [selected, setSelected] = useState(baselineKey);
  const [holder, width] = useWidth();
  const {fastSpans, slowSpans} = data.metadata;
  const values = grid.map(row => row[period][metric]);
  const color = useMemo(() => colorScale(values), [period, metric]);
  const ranks = useMemo(() => rankBy(grid, period, metric), [period, metric]);
  const best = useMemo(() => bestPair(grid, period, metric), [period, metric]);
  const row = lookup.get(selected);
  const compact = width < 560;
  const pad = {left: compact ? 34 : 44, right: 8, top: 8, bottom: compact ? 34 : 40};
  const cell = Math.max(8, Math.floor((width - pad.left - pad.right) / slowSpans.length));
  const plotW = cell * slowSpans.length;
  const plotH = cell * fastSpans.length;
  const height = pad.top + plotH + pad.bottom;
  const x = slow => pad.left + slowSpans.indexOf(slow) * cell;
  const y = fast => pad.top + (fastSpans.length - 1 - fastSpans.indexOf(fast)) * cell;
  const chartId = `${id}-heatmap`;
  const min = Math.min(...values);
  const max = Math.max(...values);

  function move(event) {
    const moves = {ArrowRight: [0, 1], ArrowLeft: [0, -1], ArrowUp: [1, 0], ArrowDown: [-1, 0]};
    const step = moves[event.key];
    if (!step) return;
    event.preventDefault();
    let fi = fastSpans.indexOf(row.f);
    let si = slowSpans.indexOf(row.s);
    for (let tries = 0; tries < 30; tries += 1) {
      fi = Math.max(0, Math.min(fastSpans.length - 1, fi + step[0]));
      si = Math.max(0, Math.min(slowSpans.length - 1, si + step[1]));
      const key = pairKey(fastSpans[fi], slowSpans[si]);
      if (lookup.has(key)) { setSelected(key); return; }
      if ((step[0] && (fi === 0 || fi === fastSpans.length - 1)) || (step[1] && (si === 0 || si === slowSpans.length - 1))) return;
    }
  }

  const xTicks = compact ? [50, 100, 150, 200, 250, 300] : [50, 80, 100, 120, 150, 200, 250, 300];
  const yTicks = compact ? [5, 25, 50, 75, 100] : [5, 20, 40, 60, 80, 100];

  return <Frame id={id} eyebrow="PARAMETER GRID / 484 PAIRS" title="ลองทุกคู่ EMA แล้วดูว่าคู่ไหนเด่น" label="SPY รายวัน · Webull" lead="แต่ละช่องคือกลยุทธ์ EMA หนึ่งคู่ แกนนอนคือ EMA ช้า แกนตั้งคือ EMA เร็ว ช่องสีเข้มคือค่าที่สูงกว่าในช่วงที่เลือก ลองสลับช่วงเวลาแล้วสังเกตว่าบริเวณสีเข้มย้ายไปไหน">
    <div className="opt-toolbar">
      <Segmented label="เลือกช่วงเวลา" controls={chartId} value={period} onChange={setPeriod} options={Object.entries(PERIODS).map(([key, item]) => [key, `${item.label} ${item.short}`])}/>
      <Segmented label="เลือกตัวชี้วัด" controls={chartId} value={metric} onChange={setMetric} options={Object.entries(METRICS).map(([key, item]) => [key, item.label])}/>
    </div>
    <div className="opt-chart" ref={holder}>
      <svg id={chartId} viewBox={`0 0 ${Math.max(width, pad.left + plotW + pad.right)} ${height}`} role="grid" tabIndex={0} aria-label={`Heatmap ${METRICS[metric].label} ${PERIODS[period].label} ใช้ลูกศรเพื่อเลื่อนเลือกคู่ EMA`} aria-activedescendant={`${id}-${selected.replace('/', '-')}`} onKeyDown={move}>
        {grid.map(item => {
          const key = pairKey(item.f, item.s);
          return <rect key={key} id={`${id}-${item.f}-${item.s}`} role="gridcell" aria-label={`EMA ${key} ${METRICS[metric].label} ${METRICS[metric].format(item[period][metric])}`} className="opt-cell" x={x(item.s) + 1} y={y(item.f) + 1} width={cell - 2} height={cell - 2} rx={2} fill={color(item[period][metric])} onPointerEnter={() => setSelected(key)} onClick={() => setSelected(key)}/>;
        })}
        {[[baselineKey, 'opt-mark-baseline'], [pickKey, 'opt-mark-pick'], [pairKey(best.f, best.s), 'opt-mark-best']].map(([key, className]) => {
          const item = lookup.get(key);
          return <rect key={className} className={`opt-mark ${className}`} x={x(item.s) - 1} y={y(item.f) - 1} width={cell + 2} height={cell + 2} rx={3} pointerEvents="none"/>;
        })}
        {row && <rect className="opt-mark opt-mark-selected" x={x(row.s) + 0.5} y={y(row.f) + 0.5} width={cell - 1} height={cell - 1} rx={2} pointerEvents="none"/>}
        {xTicks.map(tick => <text key={`x${tick}`} x={x(tick) + cell / 2} y={pad.top + plotH + 16} textAnchor="middle">{tick}</text>)}
        {yTicks.map(tick => <text key={`y${tick}`} x={pad.left - 6} y={y(tick) + cell / 2 + 4} textAnchor="end">{tick}</text>)}
        <text className="opt-axis-title" x={pad.left + plotW / 2} y={height - 4} textAnchor="middle">EMA ช้า (วัน)</text>
        <text className="opt-axis-title" x={10} y={pad.top + plotH / 2} textAnchor="middle" transform={`rotate(-90 10 ${pad.top + plotH / 2})`}>EMA เร็ว (วัน)</text>
      </svg>
    </div>
    <div className="opt-scale" aria-hidden="true">
      <span>{METRICS[metric].format(min)}</span>
      <span className="opt-scale-bar">{RAMP.map(step => <i key={step} style={{background: step}}/>)}</span>
      <span>{METRICS[metric].format(max)}</span>
    </div>
    <ul className="opt-legend">
      <li><span className="opt-box opt-mark-baseline" aria-hidden="true"/>EMA 20/200 จากบทที่ 14</li>
      <li><span className="opt-box opt-mark-pick" aria-hidden="true"/>EMA {pickKey} ดีที่สุดในช่วงฝึก</li>
      <li><span className="opt-box opt-mark-best" aria-hidden="true"/>ดีที่สุดในมุมมองนี้ ({pairKey(best.f, best.s)})</li>
    </ul>
    {row && <dl className="opt-readout" aria-live="polite" aria-atomic="true">
      <div><dt>คู่ที่เลือก</dt><dd>EMA {selected}<small>อันดับ {ranks.get(selected)} จาก {grid.length} ตาม {METRICS[metric].label}</small></dd></div>
      <div><dt>Sharpe</dt><dd>{row[period].sharpe.toFixed(2)}<small>{PERIODS[period].short}</small></dd></div>
      <div><dt>CAGR</dt><dd>{formatPercent(row[period].cagr)}<small>ต่อปี</small></dd></div>
      <div><dt>Max DD</dt><dd>{formatPercent(row[period].mdd, 1)}<small>{row[period].trades} เทรดที่ปิดแล้ว</small></dd></div>
    </dl>}
    <p className="opt-footnote">ช่องว่างมุมซ้ายบนคือคู่ที่ EMA เร็วยาวเท่าหรือยาวกว่า EMA ช้า ซึ่งไม่ได้ทดสอบ · สีคำนวณใหม่ตามค่าต่ำสุดถึงสูงสุดของมุมมองที่เลือก · ค่าธรรมเนียม 0.1% ต่อข้าง · Sharpe ใช้อัตราปลอดความเสี่ยง 0%</p>
  </Frame>;
}

/* ------------------------------------------------------------------ scatter */

export function InOutScatter() {
  const id = useId();
  const [holder, width] = useWidth();
  const [active, setActive] = useState(pickKey);
  const top10 = useMemo(() => new Set([...grid].sort((a, b) => b.is.sharpe - a.is.sharpe).slice(0, 10).map(row => pairKey(row.f, row.s))), []);
  const oosRank = useMemo(() => rankBy(grid, 'oos'), []);
  const isRank = useMemo(() => rankBy(grid, 'is'), []);
  const height = width < 480 ? 300 : 340;
  const pad = {left: 44, right: 16, top: 16, bottom: 42};
  const xs = grid.map(row => row.is.sharpe);
  const ys = grid.map(row => row.oos.sharpe);
  const holdIs = data.windows.is.hold.sharpe;
  const holdOos = data.windows.oos.hold.sharpe;
  const xTicks = niceTicks(Math.min(...xs, holdIs) - 0.02, Math.max(...xs) + 0.02, 4);
  const yTicks = niceTicks(Math.min(...ys) - 0.02, Math.max(...ys, holdOos) + 0.02, 4);
  const x = value => pad.left + (value - xTicks[0]) / (xTicks.at(-1) - xTicks[0]) * (width - pad.left - pad.right);
  const y = value => pad.top + (yTicks.at(-1) - value) / (yTicks.at(-1) - yTicks[0]) * (height - pad.top - pad.bottom);
  const row = lookup.get(active);
  const order = [...grid].sort((a, b) => {
    const weight = item => (pairKey(item.f, item.s) === active ? 3 : top10.has(pairKey(item.f, item.s)) || pairKey(item.f, item.s) === baselineKey ? 2 : 1);
    return weight(a) - weight(b);
  });

  return <Frame id={id} eyebrow="IN-SAMPLE VS OUT-OF-SAMPLE" title="อันดับในช่วงฝึก ข้ามไปช่วงทดสอบได้ไหม" label="484 คู่ · Sharpe" lead="จุดหนึ่งจุดคือคู่ EMA หนึ่งคู่ แกนนอนคือ Sharpe ช่วงฝึก 2006–2016 แกนตั้งคือ Sharpe ของคู่เดียวกันในช่วงทดสอบ 2016–2026 ถ้าคู่ที่เก่งในช่วงฝึกยังเก่งต่อ จุดสีม่วงจะไปกองอยู่มุมขวาบน">
    <div className="opt-chart" ref={holder}>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby={`${id}-desc`}>
        <desc id={`${id}-desc`}>Scatter 484 คู่ rank correlation {data.rankCorrelation.toFixed(2)} คู่ที่ดีที่สุดในช่วงฝึก {pickKey} อยู่อันดับ {oosRank.get(pickKey)} ในช่วงทดสอบ</desc>
        {yTicks.map(tick => <g key={`y${tick}`}><line className="opt-grid" x1={pad.left} x2={width - pad.right} y1={y(tick)} y2={y(tick)}/><text x={pad.left - 8} y={y(tick) + 4} textAnchor="end">{tick.toFixed(1)}</text></g>)}
        {xTicks.map(tick => <text key={`x${tick}`} x={x(tick)} y={height - 22} textAnchor="middle">{tick.toFixed(1)}</text>)}
        <line className="opt-ref" x1={x(holdIs)} x2={x(holdIs)} y1={pad.top} y2={height - pad.bottom}/>
        <line className="opt-ref" x1={pad.left} x2={width - pad.right} y1={y(holdOos)} y2={y(holdOos)}/>
        <text className="opt-ref-label" x={width - pad.right} y={y(holdOos) - 6} textAnchor="end">ซื้อแล้วถือ ช่วงทดสอบ {holdOos.toFixed(2)}</text>
        <text className="opt-ref-label" x={x(holdIs) + 6} y={pad.top + 10}>ซื้อแล้วถือ ช่วงฝึก {holdIs.toFixed(2)}</text>
        {order.map(item => {
          const key = pairKey(item.f, item.s);
          const className = key === baselineKey ? 'opt-dot opt-dot-baseline' : top10.has(key) ? 'opt-dot opt-dot-top' : 'opt-dot';
          return <g key={key} onPointerEnter={() => setActive(key)} onClick={() => setActive(key)}>
            <circle className="opt-hit" cx={x(item.is.sharpe)} cy={y(item.oos.sharpe)} r={8}/>
            <circle className={className + (key === active ? ' is-active' : '')} cx={x(item.is.sharpe)} cy={y(item.oos.sharpe)} r={key === active ? 6 : top10.has(key) || key === baselineKey ? 5 : 3.2}/>
          </g>;
        })}
        <text className="opt-axis-title" x={pad.left + (width - pad.left - pad.right) / 2} y={height - 4} textAnchor="middle">Sharpe ช่วงฝึก 2006–2016</text>
        <text className="opt-axis-title" x={12} y={pad.top + (height - pad.top - pad.bottom) / 2} textAnchor="middle" transform={`rotate(-90 12 ${pad.top + (height - pad.top - pad.bottom) / 2})`}>Sharpe ช่วงทดสอบ</text>
      </svg>
    </div>
    <ul className="opt-legend">
      <li><span className="opt-dot-key opt-dot-top" aria-hidden="true"/>10 คู่ที่ Sharpe ช่วงฝึกสูงสุด</li>
      <li><span className="opt-dot-key opt-dot-baseline" aria-hidden="true"/>EMA 20/200</li>
      <li><span className="opt-dot-key" aria-hidden="true"/>คู่อื่น</li>
    </ul>
    <label className="opt-select">
      <span>เลือกคู่จาก 10 อันดับแรกของช่วงฝึก</span>
      <select value={top10.has(active) || active === baselineKey ? active : ''} onChange={event => setActive(event.target.value)}>
        {!top10.has(active) && active !== baselineKey && <option value="">EMA {active} (เลือกจากกราฟ)</option>}
        {[...top10].map(key => <option key={key} value={key}>EMA {key} · อันดับช่วงฝึก {isRank.get(key)}</option>)}
        <option value={baselineKey}>EMA 20/200 · อันดับช่วงฝึก {isRank.get(baselineKey)}</option>
      </select>
    </label>
    {row && <dl className="opt-readout" aria-live="polite" aria-atomic="true">
      <div><dt>คู่ที่เลือก</dt><dd>EMA {active}</dd></div>
      <div><dt>ช่วงฝึก</dt><dd>{row.is.sharpe.toFixed(2)}<small>อันดับ {isRank.get(active)} จาก {grid.length}</small></dd></div>
      <div><dt>ช่วงทดสอบ</dt><dd>{row.oos.sharpe.toFixed(2)}<small>อันดับ {oosRank.get(active)} จาก {grid.length}</small></dd></div>
      <div><dt>Rank correlation</dt><dd>{data.rankCorrelation.toFixed(2)}<small>ทั้ง 484 คู่</small></dd></div>
    </dl>}
    <p className="opt-footnote">Rank correlation (Spearman) ใกล้ 0 แปลว่ารู้อันดับในช่วงฝึกแล้วเดาอันดับในช่วงทดสอบแทบไม่ได้ · เส้นประคือ Sharpe ของการซื้อแล้วถือ SPY ในแต่ละช่วง · ช่วงทดสอบทั้งช่วงเป็นตลาดขาขึ้น จึงทำให้คู่ส่วนใหญ่ได้ Sharpe สูงขึ้นพร้อมกัน</p>
  </Frame>;
}

/* ------------------------------------------------------------------ line chart */

function LineChart({dates, series, split, logScale, height: fixedHeight, unit, describe}) {
  const [holder, width] = useWidth();
  const [hover, setHover] = useState(null);
  const height = fixedHeight || (width < 480 ? 260 : 310);
  const pad = {left: 52, right: 16, top: 16, bottom: 30};
  const all = series.flatMap(item => item.values.filter(value => value != null));
  const transform = logScale ? Math.log10 : value => value;
  let ticks;
  if (logScale) {
    const candidates = [25, 50, 100, 200, 400, 800, 1600].filter(v => v >= Math.min(...all) * 0.8 && v <= Math.max(...all) * 1.25);
    ticks = candidates.length > 1 ? candidates : niceTicks(Math.min(...all), Math.max(...all));
  } else {
    ticks = niceTicks(Math.min(...all), Math.max(...all));
  }
  const lo = Math.min(transform(Math.min(...all)), transform(ticks[0]));
  const hi = Math.max(transform(Math.max(...all)), transform(ticks.at(-1)));
  const x = index => pad.left + index / (dates.length - 1) * (width - pad.left - pad.right);
  const y = value => pad.top + (hi - transform(value)) / (hi - lo) * (height - pad.top - pad.bottom);
  const splitIndex = split ? dates.findIndex(date => date >= split) : -1;
  const yearTicks = dates.map((date, index) => [date, index]).filter(([date], index, list) => index === 0 || date.slice(0, 4) !== list[index - 1][0].slice(0, 4)).filter(([date]) => Number(date.slice(0, 4)) % (width < 480 ? 5 : 2) === 0);

  function pointer(event) {
    const box = event.currentTarget.getBoundingClientRect();
    const px = (event.clientX - box.left) / box.width * width;
    const index = Math.round((px - pad.left) / (width - pad.left - pad.right) * (dates.length - 1));
    setHover(Math.max(0, Math.min(dates.length - 1, index)));
  }
  const index = hover ?? dates.length - 1;

  return <div className="opt-chart" ref={holder}>
    <p className="opt-chart-unit">{unit}</p>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={describe} onPointerMove={pointer} onPointerLeave={() => setHover(null)}>
      {splitIndex > 0 && <rect className="opt-train-zone" x={pad.left} y={pad.top} width={x(splitIndex) - pad.left} height={height - pad.top - pad.bottom}/>}
      {ticks.map(tick => <g key={tick}><line className="opt-grid" x1={pad.left} x2={width - pad.right} y1={y(tick)} y2={y(tick)}/><text x={pad.left - 8} y={y(tick) + 4} textAnchor="end">{tick}</text></g>)}
      {yearTicks.map(([date, i]) => <text key={date} x={x(i)} y={height - 10} textAnchor="middle">{date.slice(0, 4)}</text>)}
      {splitIndex > 0 && <><line className="opt-split" x1={x(splitIndex)} x2={x(splitIndex)} y1={pad.top} y2={height - pad.bottom}/><text className="opt-ref-label" x={x(splitIndex) - 6} y={pad.top + 12} textAnchor="end">ช่วงฝึก</text><text className="opt-ref-label" x={x(splitIndex) + 6} y={pad.top + 12}>ช่วงทดสอบ</text></>}
      {series.map(item => {
        let d = '';
        item.values.forEach((value, i) => { if (value == null) return; d += `${d ? 'L' : 'M'}${x(i).toFixed(1)},${y(value).toFixed(1)}`; });
        return <path key={item.id} className={`opt-line ${SERIES_CLASS[item.id]}`} d={d}/>;
      })}
      <line className="opt-cursor" x1={x(index)} x2={x(index)} y1={pad.top} y2={height - pad.bottom}/>
      {series.map(item => item.values[index] != null && <circle key={item.id} className={`opt-point ${SERIES_CLASS[item.id]}`} cx={x(index)} cy={y(item.values[index])} r={4.5}/>)}
    </svg>
    <dl className="opt-readout opt-readout-line" aria-live="polite" aria-atomic="true">
      <div><dt>วันที่</dt><dd>{dates[index]}</dd></div>
      {series.map(item => <div key={item.id}><dt><span className={`opt-swatch ${SERIES_CLASS[item.id]}`} aria-hidden="true"/>{item.label}</dt><dd>{item.values[index] == null ? '—' : item.values[index].toFixed(1)}</dd></div>)}
    </dl>
  </div>;
}

/* ------------------------------------------------------------------ equity */

export function OptimizationEquity() {
  const id = useId();
  const [view, setView] = useState('oos');
  const {dates, series, split} = data.equity;
  const splitIndex = dates.findIndex(date => date >= split);
  // The test view starts at the split so the chart shows only the unseen decade.
  const shownDates = view === 'oos' ? dates.slice(splitIndex) : dates;
  const shown = series.map(item => ({...item, values: view === 'oos' ? rebase(item.values, splitIndex).slice(splitIndex) : item.values.map(value => value / 1000)}));
  const oos = lookup.get(pickKey).oos;
  const base = lookup.get(baselineKey).oos;
  const hold = data.windows.oos.hold;
  return <Frame id={id} eyebrow="EQUITY / TRAIN THEN TEST" title={`EMA ${pickKey} ชนะในช่วงฝึก แล้วช่วงทดสอบเป็นอย่างไร`} label="ผลจำลองหลังค่าธรรมเนียม" lead={`เส้นม่วงคือคู่ที่ Sharpe ช่วงฝึกสูงสุด เราเลือกมันโดยไม่ได้เห็นข้อมูลหลังเดือนกันยายน 2016 ปุ่ม "เริ่มนับใหม่" ตั้งทุกเส้นเป็น 100 ในวันแรกของช่วงทดสอบ เพื่อเทียบเฉพาะส่วนที่ยังไม่เคยเห็น`}>
    <div className="opt-toolbar">
      <Segmented label="เลือกมุมมอง" value={view} onChange={setView} options={[['oos', 'เริ่มนับใหม่ที่ช่วงทดสอบ'], ['full', 'ทั้ง 20 ปี (พันดอลลาร์)']]}/>
    </div>
    <ul className="opt-legend">{series.map(item => <li key={item.id}><span className={`opt-swatch ${SERIES_CLASS[item.id]}`} aria-hidden="true"/>{item.label}</li>)}</ul>
    <LineChart dates={shownDates} series={shown} split={view === 'oos' ? null : split} logScale unit={view === 'oos' ? 'มูลค่าพอร์ต เริ่ม 100 ที่ 2016-09-26 · สเกล log' : 'มูลค่าพอร์ต พันดอลลาร์ เริ่ม 100 ที่ 2006-09-26 · สเกล log'} describe={`กราฟมูลค่าพอร์ตของ EMA ${pickKey} EMA 20/200 และซื้อแล้วถือ SPY`}/>
    <div className="opt-table-wrap" tabIndex={0} role="region" aria-label="ตารางผลช่วงทดสอบ">
      <table className="opt-table">
        <caption>ช่วงทดสอบ {data.windows.oos.start} ถึง {data.windows.oos.end} · เริ่มบัญชีใหม่ 100,000 USD</caption>
        <thead><tr><th scope="col">กลยุทธ์</th><th scope="col">Sharpe</th><th scope="col">CAGR</th><th scope="col">Max DD</th><th scope="col">เทรด</th></tr></thead>
        <tbody>
          <tr><th scope="row"><span className="opt-swatch opt-pick" aria-hidden="true"/>EMA {pickKey}</th><td>{oos.sharpe.toFixed(2)}</td><td>{formatPercent(oos.cagr)}</td><td>{formatPercent(oos.mdd, 1)}</td><td>{oos.trades}</td></tr>
          <tr><th scope="row"><span className="opt-swatch opt-baseline" aria-hidden="true"/>EMA 20/200</th><td>{base.sharpe.toFixed(2)}</td><td>{formatPercent(base.cagr)}</td><td>{formatPercent(base.mdd, 1)}</td><td>{base.trades}</td></tr>
          <tr><th scope="row"><span className="opt-swatch opt-hold" aria-hidden="true"/>ซื้อแล้วถือ SPY</th><td>{hold.sharpe.toFixed(2)}</td><td>{formatPercent(hold.cagr)}</td><td>{formatPercent(hold.mdd, 1)}</td><td>—</td></tr>
        </tbody>
      </table>
    </div>
    <p className="opt-footnote">ราคา SPY รายวันจาก Webull OpenAPI ดึงเมื่อ {data.metadata.retrievedAtUTC.slice(0, 10)} · ราคาปรับย้อนหลังแล้ว ปันผลอยู่ในราคา · ค่าธรรมเนียมสมมติ 0.1% ต่อข้าง ไม่รวม spread slippage และภาษี · แถบสีเทาคือช่วงฝึก</p>
  </Frame>;
}

/* ------------------------------------------------------------------ noise */

export function NoiseTrialsViz() {
  const id = useId();
  const {trialCounts, summary, worldsData, worlds, days, pairs, seed} = data.noise;
  const [step, setStep] = useState(trialCounts.length - 1);
  const [holder, width] = useWidth();
  const height = width < 480 ? 240 : 270;
  const pad = {left: 44, right: 16, top: 16, bottom: 44};
  const bands = trialCounts.map((_, k) => ({
    is: [percentile(worldsData.map(w => w[k][0]), 0.25), percentile(worldsData.map(w => w[k][0]), 0.75)],
    oos: [percentile(worldsData.map(w => w[k][1]), 0.25), percentile(worldsData.map(w => w[k][1]), 0.75)],
  }));
  const all = bands.flatMap(band => [...band.is, ...band.oos]);
  const ticks = niceTicks(Math.min(...all), Math.max(...all), 4);
  const x = k => pad.left + k / (trialCounts.length - 1) * (width - pad.left - pad.right);
  const y = value => pad.top + (ticks.at(-1) - value) / (ticks.at(-1) - ticks[0]) * (height - pad.top - pad.bottom);
  const path = values => values.map((value, k) => `${k ? 'L' : 'M'}${x(k).toFixed(1)},${y(value).toFixed(1)}`).join('');
  const area = key => `${bands.map((band, k) => `${k ? 'L' : 'M'}${x(k).toFixed(1)},${y(band[key][1]).toFixed(1)}`).join('')}${[...bands].reverse().map((band, i) => `L${x(bands.length - 1 - i).toFixed(1)},${y(band[key][0]).toFixed(1)}`).join('')}Z`;
  const current = summary[step];
  const beatCount = worldsData.filter(w => w[step][1] < w[step][0]).length;

  return <Frame id={id} eyebrow="DATA SNOOPING / RANDOM WORLDS" title="ลองมากขึ้น ผลย้อนหลังยิ่งดูดี ทั้งที่ตลาดไม่มีสัญญาณ" label="ข้อมูลสังเคราะห์" lead={`เราสุ่มผลตอบแทนรายวันของ SPY มาเรียงใหม่ ${worlds} โลก โลกละ ${days.toLocaleString('en-US')} วัน ลำดับเวลาถูกทำลาย EMA จึงไม่มีแนวโน้มจริงให้จับ ในแต่ละโลก เราลอง N คู่ เลือกคู่ที่ Sharpe ครึ่งแรกดีที่สุด แล้วอ่านผลครึ่งหลัง`}>
    <div className="opt-controls">
      <label htmlFor={`${id}-trials`}>
        <span>จำนวนคู่ที่ลอง <strong>N = {trialCounts[step]}</strong></span>
        <input id={`${id}-trials`} type="range" min="0" max={trialCounts.length - 1} step="1" value={step} aria-valuetext={`ลอง ${trialCounts[step]} คู่`} onChange={event => setStep(Number(event.target.value))}/>
        <small>ขั้น: {trialCounts.join(', ')} คู่ · N = {pairs} คือลองครบทุกคู่ในโลกสมมติ</small>
      </label>
    </div>
    <dl className="opt-readout" aria-live="polite" aria-atomic="true">
      <div><dt><span className="opt-swatch opt-pick" aria-hidden="true"/>Sharpe ครึ่งแรก (ใช้เลือก)</dt><dd>{current.is.toFixed(2)}<small>เฉลี่ย {worlds} โลก</small></dd></div>
      <div><dt><span className="opt-swatch opt-baseline" aria-hidden="true"/>Sharpe ครึ่งหลัง (ไม่เคยเห็น)</dt><dd>{current.oos.toFixed(2)}<small>เฉลี่ย {worlds} โลก</small></dd></div>
      <div><dt>ส่วนต่าง</dt><dd>{(current.is - current.oos).toFixed(2)}<small>{beatCount} จาก {worlds} โลก ครึ่งหลังแย่กว่า</small></dd></div>
    </dl>
    <div className="opt-chart" ref={holder}>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Sharpe เฉลี่ยของคู่ที่ถูกเลือกเมื่อลอง 1 ถึง ${trialCounts.at(-1)} คู่`}>
        {ticks.map(tick => <g key={tick}><line className="opt-grid" x1={pad.left} x2={width - pad.right} y1={y(tick)} y2={y(tick)}/><text x={pad.left - 8} y={y(tick) + 4} textAnchor="end">{tick.toFixed(1)}</text></g>)}
        <path className="opt-band opt-pick" d={area('is')}/>
        <path className="opt-band opt-baseline" d={area('oos')}/>
        <path className="opt-line opt-pick" d={path(summary.map(s => s.is))}/>
        <path className="opt-line opt-baseline" d={path(summary.map(s => s.oos))}/>
        {trialCounts.map((n, k) => <text key={n} x={x(k)} y={height - 24} textAnchor="middle">{n}</text>)}
        <text className="opt-axis-title" x={pad.left + (width - pad.left - pad.right) / 2} y={height - 4} textAnchor="middle">จำนวนคู่ที่ลองก่อนเลือก (N)</text>
        <line className="opt-cursor" x1={x(step)} x2={x(step)} y1={pad.top} y2={height - pad.bottom}/>
        <circle className="opt-point opt-pick" cx={x(step)} cy={y(current.is)} r={5}/>
        <circle className="opt-point opt-baseline" cx={x(step)} cy={y(current.oos)} r={5}/>
      </svg>
    </div>
    <p className="opt-footnote">เส้นทึบคือค่าเฉลี่ย แถบจางคือช่วงครึ่งกลางของโลกทั้งหมด (เปอร์เซ็นไทล์ 25–75) · bootstrap ผลตอบแทนรายวัน SPY 2006–2026 แบบใส่คืน seed {seed} · ราคาเปิดเท่ากับราคาปิดวันก่อน · ค่าธรรมเนียม 0.1% ทุกครั้งที่เปลี่ยนสถานะ · Sharpe ของครึ่งหลังที่ยังบวกมาจาก drift ของ SPY ที่ติดมากับผลตอบแทนที่สุ่ม</p>
  </Frame>;
}

/* ------------------------------------------------------------------ walk-forward */

export function WalkForwardViz() {
  const id = useId();
  const wf = data.walkForward;
  const [active, setActive] = useState(0);
  const step = wf.steps[active];
  const metrics = wf.metrics;
  return <Frame id={id} eyebrow={`WALK-FORWARD / ${wf.trainYears} YEARS TRAIN / 1 YEAR TEST`} title="เลือกคู่ใหม่ทุกปี จากข้อมูล 5 ปีก่อนหน้า" label="SPY รายวัน · Webull" lead="ทุกวันที่ 26 กันยายน เราดู Sharpe ของทั้ง 484 คู่ในห้าปีก่อนหน้า เลือกคู่ที่ดีที่สุด แล้วใช้คู่นั้นเทรดไปหนึ่งปี กดแต่ละปีเพื่อดูว่าคู่ที่ถูกเลือกเปลี่ยนไปอย่างไร">
    <ol className="opt-years" aria-label="คู่ที่ถูกเลือกในแต่ละปี">
      {wf.steps.map((item, index) => <li key={item.testStart}>
        <button type="button" aria-pressed={index === active} onClick={() => setActive(index)}>
          <span>{item.testStart.slice(0, 4)}</span>
          <strong>{item.fast}/{item.slow}</strong>
          <small className={item.testReturn < 0 ? 'is-negative' : ''}>{formatPercent(item.testReturn, 1)}</small>
        </button>
      </li>)}
    </ol>
    <p className="opt-year-note" aria-live="polite">ปีทดสอบ {step.testStart} ถึง {step.testEnd}: ฝึกด้วยข้อมูล {step.trainStart} ถึงวันก่อนเริ่มปี เลือก EMA {step.fast}/{step.slow} (Sharpe ช่วงฝึก {step.trainSharpe.toFixed(2)}) ปีถัดมาพอร์ตเปลี่ยนไป {formatPercent(step.testReturn, 2)}</p>
    <ul className="opt-legend">{wf.series.map(item => <li key={item.id}><span className={`opt-swatch ${SERIES_CLASS[item.id]}`} aria-hidden="true"/>{item.label}</li>)}</ul>
    <LineChart dates={wf.dates} series={wf.series.map(item => ({...item, values: item.values.map(value => value / 1000)}))} logScale unit={`มูลค่าพอร์ต พันดอลลาร์ เริ่ม 100 ที่ ${wf.window[0]} · สเกล log`} describe="กราฟมูลค่าพอร์ต walk-forward เทียบ EMA 20/200 คงที่ และซื้อแล้วถือ SPY"/>
    <div className="opt-table-wrap" tabIndex={0} role="region" aria-label="ตารางสรุป walk-forward">
      <table className="opt-table">
        <caption>{wf.window[0]} ถึง {wf.window[1]} · ค่าธรรมเนียม 0.1% ต่อข้าง</caption>
        <thead><tr><th scope="col">วิธี</th><th scope="col">Sharpe</th><th scope="col">CAGR</th><th scope="col">Max DD</th><th scope="col">เทรด</th></tr></thead>
        <tbody>
          <tr><th scope="row"><span className="opt-swatch opt-pick" aria-hidden="true"/>Walk-forward</th><td>{metrics.walkForward.sharpe.toFixed(2)}</td><td>{formatPercent(metrics.walkForward.cagr)}</td><td>{formatPercent(metrics.walkForward.mdd, 1)}</td><td>{metrics.walkForward.trades}</td></tr>
          <tr><th scope="row"><span className="opt-swatch opt-baseline" aria-hidden="true"/>EMA 20/200 คงที่</th><td>{metrics.fixed.sharpe.toFixed(2)}</td><td>{formatPercent(metrics.fixed.cagr)}</td><td>{formatPercent(metrics.fixed.mdd, 1)}</td><td>{metrics.fixed.trades}</td></tr>
          <tr><th scope="row"><span className="opt-swatch opt-hold" aria-hidden="true"/>ซื้อแล้วถือ SPY</th><td>{metrics.hold.sharpe.toFixed(2)}</td><td>{formatPercent(metrics.hold.cagr)}</td><td>{formatPercent(metrics.hold.mdd, 1)}</td><td>—</td></tr>
        </tbody>
      </table>
    </div>
    <p className="opt-footnote">คะแนนช่วงฝึกใช้ผลตอบแทนรายวันของแต่ละคู่ที่รันต่อเนื่อง · พอร์ต walk-forward เป็นบัญชีเดียว เปลี่ยนคู่ได้เฉพาะวันเริ่มปีทดสอบ และเสียค่าธรรมเนียมเมื่อสถานะเปลี่ยน · ผลรายปีคือการเปลี่ยนแปลงของมูลค่าพอร์ตในปีนั้น</p>
  </Frame>;
}

export const optimizationWidgets = {
  'parameter-heatmap': <ParameterHeatmap/>,
  'is-oos-scatter': <InOutScatter/>,
  'optimization-equity': <OptimizationEquity/>,
  'noise-trials-viz': <NoiseTrialsViz/>,
  'walk-forward-viz': <WalkForwardViz/>,
};
