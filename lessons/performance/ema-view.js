(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.EMAview=api;})(typeof window!=='undefined'?window:null,function(){
  'use strict';
  const num=(v,d=2)=>v===null||v===undefined?'คำนวณไม่ได้':Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
  const pct=(v,d=2)=>v===null||v===undefined?'คำนวณไม่ได้':num(v*100,d)+'%';
  const signed=(v,d=2)=>(v>0?'+':'')+num(v,d);
  const esc=s=>String(s).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  function normalize(data){return data.bars.map(row=>Object.fromEntries(data.columns.map((key,i)=>[key,row[i]])));}
  function rows(r){
    const p=r.portfolioMetrics,b=r.benchmarkMetrics,t=r.tradeMetrics;
    return [
      ['totalReturn','ผลตอบแทนสะสม','Total Return','return',pct(p.totalReturn),pct(b.totalReturn),'เงินทั้งพอร์ตเปลี่ยนไปกี่เปอร์เซ็นต์ตลอดช่วงทดสอบ','เงินปลายทาง ÷ เงินเริ่มต้น − 1','เงินเริ่มต้น '+num(p.initialEquity,0)+' USD เหลือ '+num(p.finalEquity)+' USD ใช้ช่วงทดสอบเดียวกันเมื่อเปรียบเทียบ'],
      ['cagr','อัตราเติบโตทบต้นต่อปี','CAGR','return',pct(p.cagr),pct(b.cagr),'อัตราคงที่ต่อปีที่ทำให้เงินเริ่มต้นเป็นเงินปลายทาง','(เงินปลายทาง ÷ เงินเริ่มต้น)^(1 ÷ จำนวนปีปฏิทิน) − 1','ช่วง 2006-09-26 ถึง 2026-09-25 ใช้วันปฏิทินหาร 365.25 เพื่อหาอายุการลงทุนประมาณ 20 ปี'],
      ['meanReturn','ผลตอบแทนเฉลี่ยต่อวัน','Arithmetic Mean','return',pct(p.meanReturn,4),pct(b.meanReturn,4),'ค่าเฉลี่ยผลตอบแทนของแต่ละวัน','ผลรวมผลตอบแทนรายวัน ÷ จำนวนวัน','ใช้ผลตอบแทนแต่ละวันที่คำนวณจากมูลค่าพอร์ตต้นวัน ไม่ใช่ผลตอบแทนสะสมหาร 252'],
      ['annualizedVolatility','ความผันผวนต่อปี','Volatility','risk',pct(p.annualizedVolatility),pct(b.annualizedVolatility),'ผลตอบแทนรายวันกระจายห่างจากค่าเฉลี่ยเพียงใด','ส่วนเบี่ยงเบนมาตรฐานรายวัน × √252','นับความแกว่งทั้งขึ้นและลง ค่านี้ไม่ใช่เพดานขาดทุน'],
      ['sharpe','ผลตอบแทนส่วนเกินต่อความผันผวน','Sharpe Ratio','risk',num(p.sharpe),num(b.sharpe),'ผลตอบแทนเฉลี่ยเหนืออัตราปลอดความเสี่ยง เทียบกับความผันผวนทั้งหมด','ค่าเฉลี่ยผลตอบแทนส่วนเกินรายวัน ÷ SD รายวัน × √252','รายงานตั้งอัตราปลอดความเสี่ยงไว้ที่ 0% ค่าติดลบหมายถึงผลเฉลี่ยต่ำกว่าอัตรานี้ ไม่ใช่เปอร์เซ็นต์ขาดทุน'],
      ['sortino','ผลตอบแทนส่วนเกินต่อความเสี่ยงต่ำกว่าเป้า','Sortino Ratio','risk',num(p.sortino),num(b.sortino),'ผลตอบแทนเฉลี่ยเหนือเป้าหมาย เทียบกับส่วนที่ต่ำกว่าเป้าหมาย','(ผลตอบแทนเฉลี่ยรายวัน − เป้าหมายรายวัน) ÷ Downside Deviation × √252','เป้าหมายตั้งไว้ 0% และใช้จำนวนวันทั้งหมดหารผลรวมส่วนต่ำกว่าเป้ายกกำลังสอง'],
      ['maxDrawdown','ลดลงจากยอดสูงสุดมากที่สุด','Maximum Drawdown · รายวัน','risk',pct(p.maxDrawdown),pct(b.maxDrawdown),'พอร์ตเคยต่ำกว่ายอดสูงสุดที่ผ่านมาเท่าไร','ค่าต่ำที่สุดของ (มูลค่าพอร์ต ÷ ยอดสูงสุดที่ผ่านมา − 1)','แถวนี้วัดสิ้นวัน เปิดกราฟเพื่อดูช่วงที่ลดลงและเวลาที่รอให้กลับถึงยอด'],
      ['count','จำนวนเทรดที่ปิดครบ','Closed Trades','trade',num(t.count,0)+' เทรด','—','นับจากการซื้อเปิดจนขายปิดครบหนึ่งรอบ','จำนวนรายการใน trades.csv','การตรวจสัญญาณทุกวันไม่ได้สร้างเทรดใหม่ทุกแท่ง และคำสั่งซื้อกับคำสั่งขายของรอบเดียวกันนับเป็นหนึ่งเทรด'],
      ['winRate','สัดส่วนเทรดที่ชนะ','Win Rate','trade',pct(t.winRate),'—','มีเทรดกำไรสุทธิกี่ครั้งจากเทรดที่ปิดทั้งหมด','จำนวนเทรดชนะ ÷ จำนวนเทรดทั้งหมด',num(t.wins,0)+' ครั้งจาก '+num(t.count,0)+' เทรด ต้องอ่านขนาดกำไรขาดทุนประกอบ'],
      ['lossRate','สัดส่วนเทรดที่แพ้','Loss Rate','trade',pct(t.lossRate),'—','มีเทรดขาดทุนสุทธิกี่ครั้งจากเทรดที่ปิดทั้งหมด','จำนวนเทรดแพ้ ÷ จำนวนเทรดทั้งหมด','ถ้ามีเทรดเสมอตัว Win Rate กับ Loss Rate รวมกันจะต่ำกว่า 100%'],
      ['averageWin','กำไรเฉลี่ยเฉพาะเทรดชนะ','Average Win','trade',num(t.averageWin)+' USD','—','แต่ละครั้งที่ชนะ ได้กำไรสุทธิเฉลี่ยเท่าไร','กำไรรวมของเทรดชนะ ÷ จำนวนเทรดชนะ','ตัวหารใช้เฉพาะครั้งที่ชนะ ค่าเฉลี่ยหน่วย USD ขึ้นกับขนาดเงินที่ซื้อขายด้วย'],
      ['averageLoss','ขนาดขาดทุนเฉลี่ยเฉพาะเทรดแพ้','Average Loss','trade',num(t.averageLoss)+' USD','—','แต่ละครั้งที่แพ้ เสียเงินสุทธิเฉลี่ยเท่าไร','ขนาดขาดทุนรวม ÷ จำนวนเทรดแพ้','แสดงขนาดขาดทุนเป็นบวก แล้วนำไปลบในสูตร Expectancy'],
      ['payoffRatio','กำไรเฉลี่ยต่อขาดทุนเฉลี่ย','Payoff Ratio','trade',num(t.payoffRatio)+' เท่า','—','กำไรหนึ่งครั้งมีขนาดกี่เท่าของขาดทุนหนึ่งครั้ง','Average Win ÷ Average Loss','เมื่อเสียต่อครั้งมากกว่าได้ต่อครั้ง ต้องมีจำนวนชนะมากพอชดเชย'],
      ['expectancy','กำไรขาดทุนเฉลี่ยต่อเทรด','Expectancy','trade',signed(t.expectancy)+' USD','—','เมื่อนับทุกเทรดแล้ว ได้หรือเสียเฉลี่ยเท่าไรต่อครั้ง','Win Rate × Average Win − Loss Rate × Average Loss','ตรวจอีกทางด้วยกำไรขาดทุนสุทธิรวม ÷ จำนวนเทรด ค่าเฉลี่ยย้อนหลังไม่กำหนดผลของเทรดถัดไป'],
      ['profitFactor','กำไรรวมต่อขาดทุนรวม','Profit Factor','trade',num(t.profitFactor)+' เท่า','—','กำไรรวมชดเชยขาดทุนรวมได้กี่เท่า','กำไรรวมของเทรดชนะ ÷ ขนาดขาดทุนรวมของเทรดแพ้','มากกว่า 1 หมายถึงกำไรรวมมากกว่าขาดทุนรวมในชุดข้อมูลนี้ ไม่ใช่ผลตอบแทนพอร์ตเป็นเปอร์เซ็นต์'],
      ['totalFees','ต้นทุนซื้อขายรวม','Trading Costs','trade',num(t.totalFees)+' USD',num(b.totalFees)+' USD','หักค่าใช้จ่ายจากคำสั่งที่ซื้อขายจริงเท่าไร','ผลรวมมูลค่าซื้อขายแต่ละคำสั่ง × อัตราต้นทุน','ต้นทุนสมมติ 10 bps หรือ 0.10% ต่อด้าน Benchmark จ่ายตอนซื้อและตอนขาย ส่วน EMA จ่ายทุกครั้งที่ซื้อขายจริง']
    ];
  }
  function reportTable(r){return '<div class="table-scroll report-table" tabindex="0" role="region" aria-label="รายงานผล EMA และ Benchmark"><table><thead><tr><th scope="col">ตัวชี้วัด · กดชื่อเพื่ออ่านความหมาย</th><th scope="col">EMA 20/200</th><th scope="col">ซื้อแล้วถือ</th></tr></thead><tbody>'+rows(r).map(x=>'<tr data-group="'+x[3]+'"><td><button type="button" class="metric-link" data-metric="'+x[0]+'">'+esc(x[2])+'<small>'+esc(x[1])+'</small></button></td><td class="numeric">'+x[4]+'</td><td class="numeric">'+x[5]+'</td></tr>').join('')+'</tbody></table></div>';}
  function metricHelp(r,key){const x=rows(r).find(row=>row[0]===key);return '<h4>'+esc(x[2])+': '+esc(x[1])+'</h4><p>'+esc(x[6])+'</p><p class="inline-calculation">'+esc(x[7])+'</p><p>'+esc(x[8])+'</p>';}
  function barLabel(b){return b.date+(b.warmup?' · เตรียม EMA':'');}
  return {num,pct,signed,esc,normalize,rows,reportTable,metricHelp,barLabel};
});