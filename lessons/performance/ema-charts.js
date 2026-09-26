(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EMAcharts = api;
})(typeof window !== 'undefined' ? window : globalThis, function () {
  'use strict';

  // All geometry comes from supplied observations. No sampling or smoothing is used.
  const WIDTH = 760;
  const LEFT = 80;
  const RIGHT = 725;
  const COLORS = {
    strategy: 'var(--primary,#6200ee)',
    benchmark: 'var(--secondary,#006f65)',
    price: 'var(--chart-grey,#666)',
    loss: 'var(--error,#b00020)',
    surface: 'var(--surface,#fff)'
  };
  const CSS = `.ema-chart{font-family:Roboto,'Noto Sans Thai',sans-serif;background:var(--surface,#fff)}.ema-chart text{fill:var(--text,rgba(0,0,0,.87));font-size:13px}.ema-chart .muted{fill:var(--muted,rgba(0,0,0,.60));font-size:12px}.ema-chart .tick{font-variant-numeric:tabular-nums;font-size:12px}.ema-chart .grid{stroke:var(--line,rgba(0,0,0,.13));stroke-width:1}.ema-chart .zero{stroke:var(--muted,rgba(0,0,0,.60));stroke-width:1.2}.ema-chart .selection{stroke:var(--text,rgba(0,0,0,.87));stroke-width:1;stroke-dasharray:3 4}.ema-chart path{stroke-linejoin:round;stroke-linecap:round}`;
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const esc = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  const num = (value, digits = 0) => value.toLocaleString('en-US', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  const signed = (value, digits = 0) => (value > 0 ? '+' : '') + num(value, digits);
  const coord = value => Number(value.toFixed(3));
  const txt = (x, y, value, cls = '', anchor = 'start') => `<text x="${coord(x)}" y="${coord(y)}"${cls ? ` class="${cls}"` : ''} text-anchor="${anchor}">${esc(value)}</text>`;
  const line = (x1, y1, x2, y2, cls = 'grid', extra = '') => `<line x1="${coord(x1)}" y1="${coord(y1)}" x2="${coord(x2)}" y2="${coord(y2)}" class="${cls}" ${extra}/>`;
  const circle = (x, y, color, radius = 4) => `<circle cx="${coord(x)}" cy="${coord(y)}" r="${radius}" fill="${COLORS.surface}" stroke="${color}" stroke-width="2"/>`;
  const path = (points, color, dashed = false, width = 2.3) => {
    let open = false;
    const d = points.map(point => {
      if (!point || !point.every(finite)) { open = false; return ''; }
      const command = open ? 'L' : 'M';
      open = true;
      return `${command}${coord(point[0])},${coord(point[1])}`;
    }).join(' ');
    return `<path d="${d}" fill="none" stroke="${color}" stroke-width="${width}"${dashed ? ' stroke-dasharray="7 5"' : ''}/>`;
  };
  function svg(title, description, body, height = 320) {
    return `<svg xmlns="http://www.w3.org/2000/svg" class="chart ema-chart" viewBox="0 0 ${WIDTH} ${height}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title><desc>${esc(description)}</desc><style>${CSS}</style>${body}</svg>`;
  }
  function empty(title, message, height = 320) {
    return svg(title, message, txt(WIDTH / 2, height / 2, message, 'muted', 'middle'), height);
  }
  function extent(values, includeZero = false) {
    const usable = values.filter(finite);
    if (!usable.length) return [-1, 1];
    let low = Math.min(...usable), high = Math.max(...usable);
    if (includeZero) { low = Math.min(0, low); high = Math.max(0, high); }
    const span = high - low || Math.max(Math.abs(high) * .1, 1);
    return [low - span * .1, high + span * .1];
  }
  const scale = (low, high, start, end) => value => start + (value - low) / (high - low || 1) * (end - start);
  function ticks(first, last, count = 5) {
    return [...new Set(Array.from({length: count}, (_, i) => Math.round(first + (last - first) * i / (count - 1))))];
  }
  function yGrid(low, high, y, format, count = 5) {
    let body = '';
    for (let i = 0; i < count; i++) {
      const value = low + (high - low) * i / (count - 1);
      body += line(LEFT, y(value), RIGHT, y(value), Math.abs(value) < 1e-12 ? 'zero' : 'grid');
      body += txt(LEFT - 10, y(value) + 4, format(value), 'muted tick', 'end');
    }
    return body;
  }
  function legend(x, y, color, label, dashed = false) {
    return `<line x1="${x}" y1="${y - 4}" x2="${x + 25}" y2="${y - 4}" stroke="${color}" stroke-width="2.6"${dashed ? ' stroke-dasharray="6 4"' : ''}/>` + txt(x + 33, y, label, 'muted');
  }
  function drawdowns(values) {
    let high = values[0];
    return values.map(value => { high = Math.max(high, value); return value / high - 1; });
  }

  // Supply one end-of-session row for each session, excluding initial equity.
  // A session 0 row is accepted but replaced with the explicit common initial value.
  function equity(dailyRows, initial, selectedSession = 252, mode = 'equity') {
    if (!Array.isArray(dailyRows)) throw new TypeError('dailyRows must be an array');
    if (!finite(initial) || initial <= 0) throw new RangeError('initial must be positive');
    if (!['equity', 'drawdown', 'cumulative'].includes(mode)) throw new RangeError('mode must be equity, drawdown or cumulative');
    const rows = dailyRows.filter(row => row.session !== 0);
    if (!rows.length) return empty('มูลค่าพอร์ตและผลเทียบเคียงรายวัน', 'ยังไม่มีมูลค่าพอร์ตสิ้นวันให้แสดง');
    let previous = 0;
    for (const row of rows) {
      if (!finite(row.session) || row.session <= previous || !finite(row.equity) || row.equity <= 0 || !finite(row.benchmarkEquity) || row.benchmarkEquity <= 0) {
        throw new RangeError('daily rows must be ordered positive sessions with positive equity for both series');
      }
      previous = row.session;
    }
    const sessions = [0, ...rows.map(row => row.session)];
    const dateLabel = i => i ? (rows[i-1]?.date || i) : 'เริ่มต้น';
    const strategyEquity = [initial, ...rows.map(row => row.equity)];
    const benchmarkEquity = [initial, ...rows.map(row => row.benchmarkEquity)];
    const convert = values => mode === 'drawdown' ? drawdowns(values) : mode === 'cumulative' ? values.map(value => value / initial - 1) : values;
    const strategy = convert(strategyEquity);
    const benchmark = convert(benchmarkEquity);
    const isPercent = mode !== 'equity';
    let selected = 0;
    sessions.forEach((session, i) => {
      if (Math.abs(session - selectedSession) < Math.abs(sessions[selected] - selectedSession)) selected = i;
    });
    const top = 65, bottom = 246;
    const cumulativeLow = Math.floor(Math.min(...strategy, ...benchmark));
    const cumulativeHigh = Math.max(cumulativeLow + 1, Math.ceil(Math.max(...strategy, ...benchmark)));
    const limits = mode === 'drawdown' ? [Math.min(-.01, ...strategy, ...benchmark) * 1.12, 0] : mode === 'cumulative' ? [cumulativeLow, cumulativeHigh] : extent([...strategy, ...benchmark]);
    const y = scale(limits[0], limits[1], bottom, top);
    const x = scale(0, sessions.at(-1), LEFT, RIGHT);
    const unit = mode === 'drawdown' ? 'ลดลงจากยอดสูงสุด (%)' : mode === 'cumulative' ? 'ผลตอบแทนสะสมสุทธิ (%)' : 'มูลค่าพอร์ต (USD)';
    let body = txt(LEFT, 20, unit, 'muted') + txt(RIGHT, 20, `${rows.length} วันซื้อขาย · เลือก ${dateLabel(selected)}`, 'muted', 'end');
    body += legend(LEFT, 43, COLORS.strategy, 'EMA 20/200') + legend(280, 43, COLORS.benchmark, 'S&P 500 ซื้อแล้วถือ', true);
    body += yGrid(limits[0], limits[1], y, value => isPercent ? num(value * 100, mode === 'cumulative' ? 0 : 1) + '%' : num(value), mode === 'cumulative' ? cumulativeHigh - cumulativeLow + 1 : 5);
    if (mode === 'cumulative') body += line(LEFT, y(0), RIGHT, y(0), 'zero');
    body += path(benchmark.map((value, i) => [x(sessions[i]), y(value)]), COLORS.benchmark, true);
    body += path(strategy.map((value, i) => [x(sessions[i]), y(value)]), COLORS.strategy);
    body += line(x(sessions[selected]), top, x(sessions[selected]), bottom, 'selection');
    body += circle(x(sessions[selected]), y(benchmark[selected]), COLORS.benchmark, 5.5);
    body += circle(x(sessions[selected]), y(strategy[selected]), COLORS.strategy, 3.5);
    ticks(0, sessions.at(-1)).forEach((session, i, labels) => { body += txt(x(session), 270, dateLabel(Math.round(session)), 'muted tick', i === 0 ? 'start' : i === labels.length - 1 ? 'end' : 'middle'); });
    body += txt(RIGHT, 304, 'วันที่ซื้อขาย', 'muted', 'end');
    body += txt(LEFT, 293, mode === 'drawdown' ? '0% = กลับถึงยอดเดิม · ค่าลบ = ยังต่ำกว่ายอด' : mode === 'cumulative' ? 'เริ่มที่ 0% ก่อนซื้อ · S&P 500 ไม่รวมเงินปันผล · ทั้งคู่หักค่าธรรมเนียม' : 'จุด 0 คือเงินเริ่มต้น · แต่ละจุดถัดไปคือมูลค่าสิ้นวัน', 'muted');
    const title = mode === 'drawdown' ? 'พอร์ตแต่ละเส้นเคยลดลงจากยอดเดิมลึกเพียงใด' : mode === 'cumulative' ? 'ผลตอบแทนสะสมของ EMA 20/200 เทียบกับ S&P 500 ซื้อแล้วถือ' : 'เงินพอร์ตของกลยุทธ์ EMA และพอร์ตอ้างอิงเปลี่ยนไปอย่างไร';
    const valueText = isPercent ? `กลยุทธ์ ${num(strategy[selected] * 100, 4)}% พอร์ตอ้างอิง ${num(benchmark[selected] * 100, 4)}%` : `กลยุทธ์ ${num(strategy[selected], 2)} USD พอร์ตอ้างอิง ${num(benchmark[selected], 2)} USD`;
    return svg(title, `ข้อมูลสิ้นวัน ${rows.length} วันซื้อขายและจุดเงินเริ่มต้น ไม่มีการลดจำนวนจุด เส้นทึบสีม่วงคือกลยุทธ์ เส้นประสีเขียวคือพอร์ตอ้างอิง เลือก ${dateLabel(selected)} ${valueText}${mode === 'drawdown' ? ' วัดจากยอดสะสมของแต่ละพอร์ต ไม่แปลงเป็นรายปี' : ''}`, body);
  }

  function tradeBars(trades, selectedIndex = 0) {
    if (!Array.isArray(trades)) throw new TypeError('trades must be an array');
    if (!trades.length) return empty('จำนวนครั้งที่ชนะต้องอ่านคู่กับขนาดกำไรขาดทุน', 'ยังไม่มีเทรดที่ปิดให้แสดง');
    if (trades.some(trade => !finite(trade.netPnl))) throw new TypeError('every trade must contain finite netPnl');
    const pnls = trades.map(trade => trade.netPnl);
    const selected = Math.max(0, Math.min(trades.length - 1, Math.round(selectedIndex)));
    const limits = extent(pnls, true), top = 62, bottom = 246;
    const y = scale(limits[0], limits[1], bottom, top);
    const step = (RIGHT - LEFT) / trades.length;
    const x = i => LEFT + (i + .5) * step;
    const width = Math.min(28, step * .7);
    const total = pnls.reduce((sum, value) => sum + value, 0);
    const winners = pnls.filter(value => value > 0).length, losers = pnls.filter(value => value < 0).length;
    let body = txt(LEFT, 20, 'กำไรขาดทุนสุทธิรายเทรด (USD)', 'muted');
    body += txt(RIGHT, 20, `เทรด ${selected + 1}: ${signed(pnls[selected], 2)} USD`, 'muted', 'end');
    body += txt(LEFT, 43, `ชนะ ${winners} · แพ้ ${losers} · เสมอตัว ${trades.length - winners - losers} · รวม ${trades.length} เทรด`, 'muted');
    body += yGrid(limits[0], limits[1], y, value => num(value));
    body += line(LEFT, y(0), RIGHT, y(0), 'zero');
    pnls.forEach((value, i) => {
      const color = value > 0 ? COLORS.benchmark : value < 0 ? COLORS.loss : COLORS.price;
      const rect = value === 0 ? `<line x1="${coord(x(i) - width / 2)}" y1="${coord(y(0))}" x2="${coord(x(i) + width / 2)}" y2="${coord(y(0))}" stroke="${color}" stroke-width="2"/>` : `<rect x="${coord(x(i) - width / 2)}" y="${coord(Math.min(y(0), y(value)))}" width="${coord(width)}" height="${coord(Math.abs(y(value) - y(0)))}" fill="${color}"/>`;
      body += `<g><title>เทรด ${i + 1}: ${signed(value, 2)} USD</title>${rect}</g>`;
    });
    body += line(x(selected), top, x(selected), bottom, 'selection') + circle(x(selected), y(pnls[selected]), COLORS.strategy);
    ticks(0, trades.length - 1).forEach(i => { body += txt(x(i), 270, i + 1, 'muted tick', 'middle'); });
    body += txt(LEFT, 303, `ผลรวมสุทธิ ${signed(total, 2)} USD`, 'muted') + txt(RIGHT, 303, 'ลำดับเทรดที่ปิด', 'muted', 'end');
    return svg('จำนวนครั้งที่ชนะต้องอ่านคู่กับขนาดกำไรขาดทุน', `เทรดที่ปิด ${trades.length} รายการ ชนะ ${winners} แพ้ ${losers} เสมอตัว ${trades.length - winners - losers} รวมสุทธิ ${num(total, 2)} USD แท่งเหนือศูนย์คือกำไร ใต้ศูนย์คือขาดทุน เลือกเทรด ${selected + 1} ผล ${signed(pnls[selected], 2)} USD`, body);
  }

  function tradeDistribution(trades, selectedIndex = 0) {
    if (!Array.isArray(trades)) throw new TypeError('trades must be an array');
    if (!trades.length) return empty('กำไรขาดทุนแต่ละไม้กระจุกอยู่ตรงไหน', 'ยังไม่มีเทรดที่ปิดให้แสดง');
    if (trades.some(trade => !finite(trade.netPnl))) throw new TypeError('every trade must contain finite netPnl');
    const pnls = trades.map(trade => trade.netPnl);
    const selected = Math.max(0, Math.min(trades.length - 1, Math.round(selectedIndex)));
    const wins = pnls.filter(value => value > 0), losses = pnls.filter(value => value < 0);
    const average = values => values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
    const winMean = average(wins), lossMean = average(losses);
    // Equal-width bins with zero as a boundary; only the final bin includes its right edge.
    const min = Math.min(0, ...pnls), max = Math.max(0, ...pnls);
    const rawWidth = (max - min || Math.max(Math.abs(max), 1)) / 6;
    const power = 10 ** Math.floor(Math.log10(rawWidth));
    const binWidth = [1, 2, 5, 10].find(value => value * power >= rawWidth) * power;
    const low = Math.floor(min / binWidth) * binWidth;
    const high = Math.max(low + binWidth, Math.ceil(max / binWidth) * binWidth);
    const count = Math.max(1, Math.round((high - low) / binWidth));
    const bins = Array.from({length: count}, (_, i) => ({low: low + i * binWidth, high: low + (i + 1) * binWidth, count: 0}));
    pnls.forEach(value => { bins[Math.min(count - 1, Math.max(0, Math.floor((value - low) / binWidth)))].count++; });
    const x = scale(low, high, LEFT, RIGHT), top = 101, bottom = 239;
    const maxCount = Math.max(1, ...bins.map(bin => bin.count));
    const y = scale(0, maxCount, bottom, top);
    const tradeId = i => trades[i].id || `T${i + 1}`;
    let body = txt(LEFT, 20, 'จำนวนเทรดในแต่ละช่วงกำไร–ขาดทุน', 'muted');
    body += txt(RIGHT, 20, `${tradeId(selected)}: ${signed(pnls[selected], 2)} USD`, 'muted', 'end');
    body += legend(LEFT, 45, COLORS.loss, lossMean === null ? 'Average Loss: ไม่มีเทรดแพ้' : `−Average Loss = ${num(lossMean, 2)} USD`, true);
    body += legend(LEFT, 68, COLORS.benchmark, winMean === null ? 'Average Win: ไม่มีเทรดชนะ' : `Average Win = ${num(winMean, 2)} USD`, true);
    body += txt(RIGHT, 68, `ช่วงละ ${num(binWidth)} USD · ${trades.length} เทรด`, 'muted', 'end');
    ticks(0, maxCount, Math.min(5, maxCount + 1)).forEach(value => {
      body += line(LEFT, y(value), RIGHT, y(value), value ? 'grid' : 'zero');
      body += txt(LEFT - 10, y(value) + 4, num(value), 'muted tick', 'end');
    });
    bins.forEach((bin, i) => {
      const color = bin.high <= 0 ? COLORS.loss : COLORS.benchmark;
      const label = `[${num(bin.low)}, ${num(bin.high)}${i === count - 1 ? ']' : ')'} USD: ${bin.count} เทรด`;
      body += `<g data-bin-count="${bin.count}"><title>${esc(label)}</title><rect x="${coord(x(bin.low) + 1)}" y="${coord(y(bin.count))}" width="${coord(x(bin.high) - x(bin.low) - 2)}" height="${coord(bottom - y(bin.count))}" fill="${color}" fill-opacity=".18" stroke="${color}" stroke-width="1"/></g>`;
      if (bin.count) body += txt((x(bin.low) + x(bin.high)) / 2, y(bin.count) - 7, bin.count, 'tick', 'middle');
    });
    for (let i = 0; i <= count; i++) {
      body += txt(x(low + i * binWidth), 262, num(low + i * binWidth), 'muted tick', i === 0 ? 'start' : i === count ? 'end' : 'middle');
    }
    body += txt(LEFT, 289, 'จุดด้านล่าง = ผลแต่ละไม้ตามตำแหน่ง USD จริง · วางซ้อนเมื่อจุดอยู่ใกล้กัน', 'muted');
    // Stack by horizontal proximity without shifting any observed P&L on the x-axis.
    const occupied = [];
    const dots = pnls.map((value, i) => ({value, i, x: x(value)})).sort((a, b) => a.x - b.x || a.i - b.i).map(dot => {
      let lane = 0;
      while (occupied.some(other => other.lane === lane && Math.abs(other.x - dot.x) < 13)) lane++;
      const placed = {...dot, lane, y: 314 + lane * 14};
      occupied.push(placed);
      return placed;
    });
    const dotBottom = Math.max(330, ...dots.map(dot => dot.y + 13));
    body += line(x(0), top - 6, x(0), dotBottom, 'zero');
    [ [lossMean, COLORS.loss], [winMean, COLORS.benchmark] ].forEach(([value, color]) => {
      if (finite(value)) body += `<line x1="${coord(x(value))}" y1="${top - 6}" x2="${coord(x(value))}" y2="${coord(dotBottom)}" stroke="${color}" stroke-width="1.5" stroke-dasharray="6 4"/>`;
    });
    dots.forEach(dot => {
      const color = dot.value > 0 ? COLORS.benchmark : dot.value < 0 ? COLORS.loss : COLORS.price;
      body += `<g data-trade-id="${esc(tradeId(dot.i))}"><title>${esc(tradeId(dot.i))}: ${signed(dot.value, 2)} USD</title>${circle(dot.x, dot.y, color, 4.5)}${dot.i === selected ? `<circle cx="${coord(dot.x)}" cy="${coord(dot.y)}" r="8" fill="none" stroke="${COLORS.strategy}" stroke-width="2"/>` : ''}</g>`;
    });
    body += txt(x(0), dotBottom + 18, '0', 'muted tick', 'middle');
    body += txt(RIGHT, dotBottom + 40, 'กำไร–ขาดทุนสุทธิต่อไม้ (USD)', 'muted', 'end');
    return svg('กำไรขาดทุนแต่ละไม้กระจุกอยู่ตรงไหน', `Histogram ของ ${trades.length} เทรด ช่วงกว้างเท่ากัน ${num(binWidth)} USD ช่วงรวมขอบซ้ายและไม่รวมขอบขวา ยกเว้นช่วงสุดท้ายรวมทั้งสองขอบ แท่งสูงคือมีเทรดจำนวนมาก ไม่ได้หมายถึงกำไรมาก จุดแสดงผลสุทธิแต่ละไม้ครบทุกไม้ แกนแนวนอนเป็น USD แกนแนวตั้งของแท่งเป็นจำนวนเทรด เส้นศูนย์แยกกำไรและขาดทุน เส้นประเป็นค่าเฉลี่ยของแต่ละกลุ่ม`, body, dotBottom + 56);
  }

  function drawdownEpisode(dailyRows, initial, metrics) {
    if (!Array.isArray(dailyRows)) throw new TypeError('dailyRows must be an array');
    if (!finite(initial) || initial <= 0) throw new RangeError('initial must be positive');
    const rows = dailyRows.filter(row => row.session !== 0);
    if (!rows.length) return empty('ช่วงลดลง ช่วงฟื้น และเวลาที่ยังต่ำกว่ายอดเดิม', 'ยังไม่มีมูลค่าพอร์ตสิ้นวันให้แสดง');
    if (rows.some(row => !finite(row.equity) || row.equity <= 0)) throw new RangeError('daily rows must contain positive equity');
    const values = [initial, ...rows.map(row => row.equity)];
    const peak = metrics?.maxDrawdownPeakIndex, trough = metrics?.maxDrawdownTroughIndex;
    if (peak === null || peak === undefined || trough === null || trough === undefined) {
      return empty('ช่วงลดลง ช่วงฟื้น และเวลาที่ยังต่ำกว่ายอดเดิม', 'ไม่มีรอบ Maximum Drawdown ให้แสดง');
    }
    const recovered = metrics?.maxDrawdownRecoveryIndex !== null && metrics?.maxDrawdownRecoveryIndex !== undefined;
    const recovery = recovered ? metrics.maxDrawdownRecoveryIndex : values.length - 1;
    if (![peak, trough, recovery].every(value => Number.isInteger(value) && value >= 0 && value < values.length) || peak > trough || trough > recovery) {
      throw new RangeError('drawdown episode indices must refer to initial equity followed by daily rows');
    }
    if (values[trough] >= values[peak]) return empty('ช่วงลดลง ช่วงฟื้น และเวลาที่ยังต่ำกว่ายอดเดิม', 'ข้อมูลนี้ไม่มีช่วงลดลงจากยอดเดิม');
    const date = i => i === 0 ? 'เงินเริ่มต้น' : rows[i - 1].date || `วัน ${i}`;
    const declineDays = trough - peak, recoveryDays = recovery - trough, underwaterDays = recovery - peak;
    const relative = values.slice(peak, recovery + 1).map(value => value / values[peak] - 1);
    const top = 104, bottom = 245;
    const y = scale(Math.min(...relative) * 1.15, Math.max(.02, ...relative) * 1.1, bottom, top);
    const x = scale(peak, Math.max(peak + 1, recovery), LEFT, RIGHT);
    let body = txt(LEFT, 20, 'มูลค่าพอร์ตเทียบกับยอดเดิม (%)', 'muted');
    body += txt(RIGHT, 20, `Maximum Drawdown ${num((values[trough] / values[peak] - 1) * 100, 2)}%`, 'muted', 'end');
    body += txt(LEFT, 50, 'ยอดเดิม', 'muted') + txt(LEFT, 72, date(peak), 'tick');
    body += txt((LEFT + RIGHT) / 2, 50, 'จุดต่ำสุด', 'muted', 'middle') + txt((LEFT + RIGHT) / 2, 72, date(trough), 'tick', 'middle');
    body += txt(RIGHT, 50, recovered ? 'กลับถึงยอดเดิม' : 'สิ้นสุดข้อมูล: ยังไม่ฟื้น', 'muted', 'end') + txt(RIGHT, 72, date(recovery), 'tick', 'end');
    const tickLow = Math.floor(Math.min(...relative) * 100 / 10) * 10;
    for (let percent = tickLow; percent <= 0; percent += 10) {
      body += line(LEFT, y(percent / 100), RIGHT, y(percent / 100), percent === 0 ? 'zero' : 'grid');
      body += txt(LEFT - 10, y(percent / 100) + 4, `${percent}%`, 'muted tick', 'end');
    }
    body += `<rect x="${LEFT}" y="${top}" width="${coord(x(trough) - LEFT)}" height="${bottom - top}" fill="${COLORS.loss}" opacity=".045"/>`;
    body += `<rect x="${coord(x(trough))}" y="${top}" width="${coord(RIGHT - x(trough))}" height="${bottom - top}" fill="${COLORS.benchmark}" opacity=".045"/>`;
    body += path(relative.map((value, i) => [x(peak + i), y(value)]), COLORS.strategy);
    [peak, trough, recovery].forEach(i => {
      const value = values[i] / values[peak] - 1;
      body += line(x(i), top, x(i), bottom, 'selection') + circle(x(i), y(value), COLORS.strategy);
    });
    body += txt(LEFT, 270, date(peak), 'muted tick', 'start');
    body += txt(x(trough), 270, date(trough), 'muted tick', 'middle');
    body += txt(RIGHT, 270, date(recovery), 'muted tick', 'end');
    const bracket = (a, b, yy, color, label) => `<line x1="${coord(x(a))}" y1="${yy}" x2="${coord(x(b))}" y2="${yy}" stroke="${color}" stroke-width="2"/>` + [a,b].map(i => `<line x1="${coord(x(i))}" y1="${yy - 5}" x2="${coord(x(i))}" y2="${yy + 5}" stroke="${color}" stroke-width="2"/>`).join('') + txt((x(a) + x(b)) / 2, yy + 23, label, 'muted', 'middle');
    body += bracket(peak, trough, 296, COLORS.loss, `Drawdown period: ${declineDays} วัน`);
    body += bracket(trough, recovery, 296, COLORS.benchmark, recovered ? `Recovery period: ${recoveryDays} วัน` : `หลังจุดต่ำสุด: ${recoveryDays} วัน (ยังไม่ฟื้น)`);
    body += bracket(peak, recovery, 347, COLORS.strategy, recovered ? `Underwater period: ${underwaterDays} วันซื้อขาย` : `Underwater: อย่างน้อย ${underwaterDays} วันซื้อขาย`);
    body += txt(LEFT, 401, recovered ? `${declineDays} วันลง + ${recoveryDays} วันฟื้น = ${underwaterDays} วันต่ำกว่ายอดเดิม` : 'ยังวัด Recovery period ที่เสร็จสมบูรณ์ไม่ได้', 'muted');
    body += txt(LEFT, 423, '0% อ้างอิงยอดเดิมของรอบนี้ · เส้นรายวันอาจขึ้นลงระหว่างแต่ละช่วง', 'muted');
    return svg('ช่วงลดลง ช่วงฟื้น และเวลาที่ยังต่ำกว่ายอดเดิม', `ขยายรอบที่เกิด Maximum Drawdown ของ EMA 20/200 ยอดเดิม ${date(peak)} ${num(values[peak], 2)} USD จุดต่ำสุด ${date(trough)} ${num(values[trough], 2)} USD ${recovered ? `กลับถึงยอดเดิม ${date(recovery)}` : `ยังไม่ฟื้น ณ ${date(recovery)}`} Drawdown period ${declineDays} วันซื้อขาย ${recovered ? `Recovery period ${recoveryDays} วันซื้อขาย Underwater period ${underwaterDays} วันซื้อขาย` : `Underwater อย่างน้อย ${underwaterDays} วันซื้อขาย ไม่ทราบระยะฟื้นตัวครบถ้วน`} ระยะเวลานับจากผลต่างตำแหน่งวันซื้อขาย`, body, 446);
  }

  // Engine target is already computed from the previous completed close.
  // Use it without an additional shift; it is not proof of actual holdings.
  function signal(bars, selectionIndex = 0) {
    if (!Array.isArray(bars)) throw new TypeError('bars must be an array');
    if (!bars.length) return empty('อ่านเส้น EMA แล้วดูเป้าหมายของแท่งถัดไป', 'ยังไม่มีแท่งราคาให้แสดง', 382);
    if (bars.some(bar => !finite(bar.close))) throw new TypeError('every bar must contain finite close');
    let selected = bars.findIndex(bar => bar.index === selectionIndex);
    if (selected < 0) selected = Math.max(0, Math.min(bars.length - 1, Math.round(selectionIndex)));
    const count = Math.min(160, bars.length);
    const start = Math.max(0, Math.min(selected - Math.floor(count / 2), bars.length - count));
    const visible = bars.slice(start, start + count);
    const localSelected = selected - start;
    const top = 65, bottom = 211;
    const limits = extent(visible.flatMap(bar => [bar.close, bar.ema20, bar.ema200]));
    const y = scale(limits[0], limits[1], bottom, top), x = scale(0, Math.max(1, count - 1), LEFT, RIGHT);
    const selectedBar = bars[selected];
    const barNumber = (bar, fallback) => finite(bar.index) ? bar.index + 1 : fallback + 1;
    let body = txt(LEFT, 20, 'S&P 500 และ EMA (จุด)', 'muted');
    body += txt(RIGHT, 20, selectedBar.date+(selectedBar.warmup?' · เตรียม EMA':''), 'muted', 'end');
    body += legend(LEFT, 43, COLORS.price, 'ราคาปิด') + legend(235, 43, COLORS.strategy, 'EMA 20') + legend(390, 43, COLORS.benchmark, 'EMA 200', true);
    const dx = (RIGHT - LEFT) / Math.max(1, count - 1);
    visible.forEach((bar, i) => {
      if (bar.warmup) body += `<rect x="${coord(Math.max(LEFT, x(i) - dx / 2))}" y="${top}" width="${coord(Math.min(RIGHT, x(i) + dx / 2) - Math.max(LEFT, x(i) - dx / 2))}" height="${bottom - top}" fill="${COLORS.price}" opacity=".055"/>`;
    });
    body += yGrid(limits[0], limits[1], y, value => num(value, limits[1] - limits[0] < 10 ? 2 : 0));
    body += path(visible.map((bar, i) => [x(i), y(bar.close)]), COLORS.price, false, 1.5);
    body += path(visible.map((bar, i) => finite(bar.ema20) ? [x(i), y(bar.ema20)] : null), COLORS.strategy);
    body += path(visible.map((bar, i) => finite(bar.ema200) ? [x(i), y(bar.ema200)] : null), COLORS.benchmark, true);
    body += line(x(localSelected), top, x(localSelected), 342, 'selection') + circle(x(localSelected), y(selectedBar.close), COLORS.price);
    ticks(0, count - 1).forEach(i => { body += txt(x(i), 237, visible[i].date || barNumber(visible[i], start + i), 'muted tick', 'middle'); });
    body += txt(RIGHT, 259, 'วันที่ซื้อขาย', 'muted', 'end');
    body += txt(LEFT, 283, 'เป้าหมายจากแท่งก่อนหน้า', 'muted');
    body += line(LEFT, 306, RIGHT, 306) + line(LEFT, 334, RIGHT, 334);
    body += txt(LEFT - 10, 310, 'ถือ', 'muted', 'end') + txt(LEFT - 10, 338, 'เงินสด', 'muted', 'end');
    const targetOf = position => {
      if (position < 0) return null;
      const value = bars[position].target;
      return value === true || value === 1 ? 1 : value === false || value === 0 ? 0 : null;
    };
    let lane = [], lastTarget = null;
    visible.forEach((bar, i) => {
      const target = targetOf(start + i);
      if (target === null) { lane.push(null); lastTarget = null; return; }
      const yy = target ? 306 : 334;
      if (lastTarget !== null && lastTarget !== target) lane.push([x(i), lastTarget ? 306 : 334]);
      lane.push([x(i), yy]);
      lastTarget = target;
    });
    body += path(lane, COLORS.strategy, false, 2.6);
    const target = targetOf(selected);
    if (target !== null) body += circle(x(localSelected), target ? 306 : 334, COLORS.strategy);
    body += txt(LEFT, 370, 'แถบล่างเป็นเป้าหมาย ไม่ได้ยืนยันสถานะที่ซื้อขายสำเร็จ', 'muted');
    const laneDescription = target === null ? 'ยังไม่มีเป้าหมายจากแท่งก่อนหน้า' : target ? 'เป้าหมายจากแท่งก่อนหน้าคือถือสถานะ Long' : 'เป้าหมายจากแท่งก่อนหน้าคือถือเงินสด';
    return svg('อ่านเส้น EMA แล้วดูเป้าหมายของแท่งถัดไป', `แสดง ${count} แท่งโดยไม่ลดจำนวนจุด จากแท่ง ${barNumber(visible[0], start)} ถึง ${barNumber(visible.at(-1), start + count - 1)} เลือกแท่ง ${barNumber(selectedBar, selected)} ราคาปิด ${num(selectedBar.close, 4)} เส้นสีเทาคือราคาปิด สีม่วง EMA 20 เส้นประสีเขียว EMA 200 ${laneDescription} การซื้อขายจริงต้องตรวจการจับคู่คำสั่งแยกต่างหาก`, body, 382);
  }

  function risk(returns, marPeriod = 0, dates = []) {
    if (!Array.isArray(returns) || returns.some(value => !finite(value))) throw new TypeError('returns must be an array of finite daily returns');
    if (!finite(marPeriod)) throw new TypeError('marPeriod must be a finite daily rate');
    if (!returns.length) return empty('ผลตอบแทนวันใดต่ำกว่าเกณฑ์ที่กำหนด', 'ยังไม่มีผลตอบแทนรายวันให้แสดง');
    const n = returns.length, below = returns.filter(value => value < marPeriod).length;
    const top = 65, bottom = 246, limits = extent([...returns, marPeriod], true);
    const y = scale(limits[0], limits[1], bottom, top), step = (RIGHT - LEFT) / n, x = i => LEFT + (i + .5) * step;
    let body = txt(LEFT, 20, 'ผลตอบแทนรายวัน (%)', 'muted') + txt(RIGHT, 20, `ต่ำกว่าเป้าหมาย ${below} จาก ${n} วัน`, 'muted', 'end');
    body += `<rect x="${LEFT}" y="32" width="15" height="11" fill="${COLORS.loss}"/>` + txt(LEFT + 23, 43, 'ต่ำกว่าเป้าหมาย', 'muted');
    body += `<rect x="275" y="32" width="15" height="11" fill="${COLORS.price}"/>` + txt(298, 43, 'ถึงหรือสูงกว่าเป้าหมาย', 'muted');
    body += yGrid(limits[0], limits[1], y, value => num(value * 100, 2) + '%');
    body += line(LEFT, y(0), RIGHT, y(0), 'zero');
    returns.forEach((value, i) => {
      const width = step * .72, color = value < marPeriod ? COLORS.loss : COLORS.price;
      const shape = value === 0 ? `<line x1="${coord(x(i) - width / 2)}" y1="${coord(y(0))}" x2="${coord(x(i) + width / 2)}" y2="${coord(y(0))}" stroke="${color}" stroke-width="1.5"/>` : `<rect x="${coord(x(i) - width / 2)}" y="${coord(Math.min(y(0), y(value)))}" width="${coord(width)}" height="${coord(Math.abs(y(value) - y(0)))}" fill="${color}"/>`;
      body += `<g><title>${dates[i] || i + 1}: ${signed(value * 100, 4)}% ${value < marPeriod ? 'ต่ำกว่าเป้าหมาย' : 'ถึงหรือสูงกว่าเป้าหมาย'}</title>${shape}</g>`;
    });
    body += `<line x1="${LEFT}" y1="${coord(y(marPeriod))}" x2="${RIGHT}" y2="${coord(y(marPeriod))}" stroke="${COLORS.strategy}" stroke-width="1.6" stroke-dasharray="7 4"/>`;
    ticks(0, n - 1).forEach(i => { body += txt(x(i), 270, dates[i] || i + 1, 'muted tick', 'middle'); });
    body += txt(LEFT, 300, `เส้นประ = เป้าหมาย ${num(marPeriod * 100, 3)}% ต่อวัน`, 'muted') + txt(RIGHT, 300, 'ลำดับวันซื้อขาย', 'muted', 'end');
    return svg('ผลตอบแทนวันใดต่ำกว่าเกณฑ์ที่กำหนด', `แสดงผลตอบแทนทุกวันครบ ${n} ค่า รวมวันผลตอบแทนศูนย์ เป้าหมาย ${num(marPeriod * 100, 6)}% ต่อวัน มี ${below} วันที่ต่ำกว่าเป้าหมาย อีก ${n - below} วันถึงหรือสูงกว่าเป้าหมาย แท่งไม่แปลงเป็นรายปีและไม่ได้ใช้ผลตอบแทนระหว่างวันมาปะปน`, body);
  }

  return {equity, tradeBars, tradeDistribution, drawdownEpisode, signal, risk};
});
