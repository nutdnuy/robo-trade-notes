(function(){
 'use strict';
 const $=id=>document.getElementById(id),r=JSON.parse($('lesson-results').textContent),data=JSON.parse($('lesson-data').textContent);
 const C=window.EMAcharts,V=window.EMAview,M=window.Metrics,{num:n,pct:p,signed:s}=V,bars=V.normalize(data),t=r.tradeMetrics,pm=r.portfolioMetrics;
 const equity=[r.parameters.initialEquity,...r.dailyEquity.map(x=>x.equity)];
 const box=(label,value,unit='',sign=0)=>`<div class="readout ${sign<0?'negative':sign>0?'positive':''}"><small>${label}</small><strong>${value}</strong><em>${unit}</em></div>`;
 const facts=rows=>'<dl class="month-facts">'+rows.map(([a,b])=>`<div><dt>${a}</dt><dd>${b}</dd></div>`).join('')+'</dl>';
 $('metric-group')?.addEventListener('change',()=>{const group=$('metric-group').value;document.querySelectorAll('.report-table tbody tr').forEach(row=>row.hidden=group!=='all'&&row.dataset.group!==group);});
 document.querySelectorAll('[data-metric]').forEach(button=>button.addEventListener('click',()=>{
  const help=$('metric-help'),row=button.closest('tr'),expanded=document.querySelector('.metric-expanded');
  help.innerHTML=V.metricHelp(r,button.dataset.metric);
  const detail=document.createElement('tr'),cell=document.createElement('td');
  detail.className='metric-expanded';detail.dataset.group=row.dataset.group;cell.colSpan=3;
  cell.append(help);detail.append(cell);if(expanded)expanded.remove();row.after(detail);
  document.querySelectorAll('[data-metric]').forEach(x=>{x.setAttribute('aria-pressed',String(x===button));x.setAttribute('aria-expanded',String(x===button));});
 }));
 function signal(){
  const i=+$('signal-bar').value,b=bars[i],next=bars[i+1],target=b.ema20>b.ema200?1:0,current=b.target;
  $('signal-bar-out').textContent=V.barLabel(b);$('signal-chart').innerHTML=C.signal(bars,i);
  const executions=r.transactions.filter(x=>x.bar===b.index);
  const action=executions.length?executions.map(x=>`${x.side==='buy'?'ซื้อ':'ขาย'}ที่ ${n(x.price,5)} จุด · ต้นทุน ${n(x.fee)} USD`).join('<br>'):'ไม่มีคำสั่งซื้อขายในแท่งนี้';
  const nextAction=!next?'จบช่วงทดสอบแล้ว ไม่มีแท่งถัดไปให้ส่งคำสั่ง':target===current?'เป้าหมายคงเดิม จึงไม่ซื้อขายเพิ่ม':`เป้าหมายเปลี่ยนเป็น ${target?'ถือสินทรัพย์':'ถือเงินสด'} จะ${target?'ซื้อ':'ขาย'}ที่ราคาเปิดแท่งถัดไป ${n(next.open,5)} จุด`;
  $('signal-detail').innerHTML=facts([['ราคาปิดแท่งที่เลือก',n(b.close,5)+' จุด'],['EMA 20 / EMA 200',n(b.ema20,5)+' / '+n(b.ema200,5)],['เป้าหมายที่ใช้ในแท่งนี้',b.warmup?'ช่วงเตรียม ยังไม่ลงทุน':current?'100% สินทรัพย์':'0% สินทรัพย์ (เงินสด)'],['สัญญาณเมื่อแท่งนี้ปิด',target?'EMA 20 > EMA 200':'EMA 20 ≤ EMA 200']])+`<p>${action}</p><p>${nextAction}</p>`;
  $('bar-back').disabled=i<=r.parameters.warmupBars-1;$('bar-next').disabled=i>=bars.length-1;
  $('signal-status').textContent=V.barLabel(b)+' '+(target?'สัญญาณถือสินทรัพย์':'สัญญาณถือเงินสด');
 }
 $('signal-bar')?.addEventListener('input',signal);$('signal-event')?.addEventListener('change',()=>{$('signal-bar').value=$('signal-event').value;signal();});
 $('bar-back')?.addEventListener('click',()=>{$('signal-bar').value=Math.max(r.parameters.warmupBars-1,+$('signal-bar').value-1);signal();});$('bar-next')?.addEventListener('click',()=>{$('signal-bar').value=Math.min(bars.length-1,+$('signal-bar').value+1);signal();});
 function trade(){const i=+$('trade-index').value-1,x=r.tradeLedger[i];$('trade-index-out').textContent=x.id;$('trade-chart').innerHTML=C.tradeBars(r.tradeLedger,i);$('trade-detail').innerHTML=facts([['ซื้อ → ขาย',x.entryTime+' → '+x.exitTime],['ราคาซื้อ → ราคาขาย',n(x.entryPrice,5)+' → '+n(x.exitPrice,5)+' จุด'],['จำนวนหน่วย',n(x.quantity,6)],['กำไรขาดทุนสุทธิ',s(x.netPnl)+' USD']])+`<p>ก่อนต้นทุน: ${n(x.quantity,6)} × (${n(x.exitPrice,5)} − ${n(x.entryPrice,5)}) ≈ ${s(x.grossPnl)} USD<br>หักต้นทุนซื้อ ${n(x.entryFee)} และขาย ${n(x.exitFee)} USD → สุทธิ <strong>${s(x.netPnl)} USD</strong></p><p class="formula-note">จำนวนและราคาแสดงแบบปัดเศษ การคำนวณจริงใช้ค่าความละเอียดเต็มใน CSV</p>`;$('trade-status').textContent=x.id+' กำไรขาดทุนสุทธิ '+s(x.netPnl)+' USD';}
 $('trade-index')?.addEventListener('input',trade);
 function distribution(){
  const i=+$('distribution-index').value-1,x=r.tradeLedger[i];
  $('distribution-index-out').textContent=x.id;
  $('distribution-chart').innerHTML=C.tradeDistribution(r.tradeLedger,i);
  $('distribution-detail').innerHTML=facts([['เทรดที่เลือก',x.id+' · '+(x.netPnl>0?'กำไร':x.netPnl<0?'ขาดทุน':'เสมอตัว')],['กำไรขาดทุนสุทธิ',s(x.netPnl)+' USD'],['วันซื้อ → วันขาย',x.entryTime+' → '+x.exitTime],['จำนวนหน่วยที่ถือ',n(x.quantity,6)]])+`<p>แต่ละจุดเป็นเทรดที่ปิดแล้วหนึ่งรายการ ตำแหน่งแนวนอนคือกำไรขาดทุนสุทธิ การวางจุดซ้อนแนวตั้งช่วยแยกจุดที่ใกล้กัน ไม่ได้แสดงเวลา${x.exitReason==='forced_end'?' เทรดนี้ปิดตามกติกาวันสิ้นสุดการทดสอบ':''}</p>`;
  $('distribution-status').textContent=x.id+' ผลสุทธิ '+s(x.netPnl)+' USD';
 }
 $('distribution-index')?.addEventListener('input',distribution);
 function cumulative(){
  const day=+$('cumulative-session').value,base=r.parameters.initialEquity,row=day?r.dailyEquity[day-1]:null;
  const a=(row?row.equity:base)/base-1,b=(row?row.benchmarkEquity:base)/base-1;
  $('cumulative-session-out').textContent=row?row.date:'ก่อนลงทุน';
  $('cumulative-chart').innerHTML=C.equity(r.dailyEquity,base,day,'cumulative');
  $('cumulative-detail').innerHTML=facts([['วันที่',row?row.date:r.parameters.startDate+' ก่อนเปิด'],['EMA 20/200 สะสม',p(a,2)],['S&P 500 ซื้อแล้วถือ สะสม',p(b,2)],['EMA ลบซื้อแล้วถือ',s((a-b)*100)+' จุดเปอร์เซ็นต์']])+`<p>ลงทุนเริ่มต้น 100 USD จะมีมูลค่า ${n(100*(1+a))} USD ใน EMA และ ${n(100*(1+b))} USD ในพอร์ตซื้อแล้วถือ ณ จุดนี้ ส่วนต่างเป็นจุดเปอร์เซ็นต์ ไม่ใช่อัตราการเติบโตต่อปี</p>`;
  $('cumulative-status').textContent=(row?row.date:'ก่อนลงทุน')+' ผลตอบแทนสะสม EMA '+p(a)+' ซื้อแล้วถือ '+p(b);
 }
 $('cumulative-session')?.addEventListener('input',cumulative);
 for(const [id,day]of [['cumulative-start',0],['cumulative-end',pm.periods]])$(id).addEventListener('click',()=>{$('cumulative-session').value=day;cumulative();});
 function expectancy(){
  const rate=+$('win-rate').value/100,w=+$('avg-win').value,l=+$('avg-loss').value,gain=rate*w,loss=(1-rate)*l,e=gain-loss,payoff=w/l,be=l/(w+l),scale=Math.max(gain,loss,1);
  $('win-rate-out').textContent=p(rate);$('avg-win-out').textContent=n(w);$('avg-loss-out').textContent=n(l);for(const id of ['win-rate','avg-win','avg-loss'])if(document.activeElement!==$(id+'-number'))$(id+'-number').value=Number($(id).value).toFixed(2);
  $('expectancy-chart').innerHTML=`<div class="contribution-row"><span>ส่วนจากเทรดชนะ</span><div><i style="width:${gain/scale*100}%;background:var(--secondary)"></i></div><strong>+${n(gain)} USD</strong></div><div class="contribution-row"><span>ส่วนจากเทรดแพ้</span><div><i style="width:${loss/scale*100}%;background:var(--error)"></i></div><strong>−${n(loss)} USD</strong></div><p class="formula-note">ความยาวแท่งใช้มาตราส่วนเดียวกัน เป็นส่วนเฉลี่ยต่อเทรดทั้งหมด</p>`;
  $('win-results').innerHTML=box('Payoff Ratio',n(payoff,4),'กำไรเฉลี่ย ÷ ขาดทุนเฉลี่ย')+box('Expectancy',s(e),'USD ต่อเทรด',e)+box('Win Rate ที่เสมอตัว',p(be),'เมื่อขนาดกำไร–ขาดทุนคงเดิม');
  $('win-explanation').innerHTML=`<p>${p(rate)} × ${n(w)} − ${p(1-rate)} × ${n(l)} = <strong>${s(e)} USD ต่อเทรด</strong></p><p>ต้องชนะมากกว่า ${p(be)} จึงมีค่าเฉลี่ยเป็นกำไร ภายใต้ขนาดกำไร–ขาดทุนที่เลือกและไม่มีเทรดเสมอ ค่าศูนย์หรือติดลบเป็นไปได้แม้ Win Rate เกิน 50%</p>`;
  $('win-status').textContent='Win Rate '+p(rate)+' Expectancy '+s(e)+' USD ต่อเทรด';
 }
 for(const id of ['win-rate','avg-win','avg-loss']){$(id).addEventListener('input',expectancy);$(id+'-number').addEventListener('input',()=>{const v=Number($(id+'-number').value);if($(id+'-number').value!==''&&Number.isFinite(v)&&v>=+$(id).min&&v<=+$(id).max){$(id).value=v;expectancy();}});$(id+'-number').addEventListener('change',()=>{const v=Number($(id+'-number').value);if(Number.isFinite(v))$(id).value=Math.max(+$(id).min,Math.min(+$(id).max,v));expectancy();});}
 function resetWin(){$('win-rate').value=t.winRate*100;$('avg-win').value=t.averageWin;$('avg-loss').value=t.averageLoss;expectancy();}
 $('reset-win')?.addEventListener('click',resetWin);
 function session(){const day=+$('session').value,eq=equity[day],peak=Math.max(...equity.slice(0,day+1));$('session-out').textContent=day?r.dailyEquity[day-1].date:'เงินเริ่มต้น';$('equity-chart').innerHTML=C.equity(r.dailyEquity,r.parameters.initialEquity,day);$('drawdown-chart').innerHTML=C.equity(r.dailyEquity,r.parameters.initialEquity,day,'drawdown');$('session-detail').innerHTML=facts([['มูลค่าพอร์ต EMA',n(eq)+' USD'],['ยอดสูงสุดที่ผ่านมา',n(peak)+' USD'],['Drawdown วันนี้',p(eq/peak-1,4)],['ผลตอบแทนวันนี้',day?p(r.dailyEquity[day-1].dailyReturn,4):'ยังไม่มีผลตอบแทน']])+`<p class="formula-note">ซื้อแล้วถือ ${n(day?r.dailyEquity[day-1].benchmarkEquity:r.parameters.initialEquity)} USD · ใช้มูลค่าที่สิ้นวันรวมสถานะที่ยังไม่ปิด</p>`;$('session-status').textContent='วัน '+day+' Drawdown '+p(eq/peak-1,4);}
 $('session')?.addEventListener('input',session);for(const [id,day]of [['peak-day',pm.maxDrawdownPeakIndex],['trough-day',pm.maxDrawdownTroughIndex],['recovery-day',pm.maxDrawdownRecoveryIndex],['last-day',pm.periods]])$(id).addEventListener('click',()=>{$('session').value=day;session();});
 function risk(){const rf=+$('rf').value/100,mar=+$('mar').value/100,s=M.periodStats(equity,{periodsPerYear:252,riskFreeAnnual:rf,marAnnual:mar}),below=s.returns.filter(x=>x<s.marPeriod).length;$('rf-out').textContent=p(rf);$('mar-out').textContent=p(mar);$('risk-chart').innerHTML=C.risk(s.returns,s.marPeriod,r.dailyEquity.map(x=>x.date));$('risk-results').innerHTML=box('Volatility ต่อปี',p(s.annualizedVolatility),'SD รายวัน × √252')+box('Sharpe Ratio',n(s.sharpe,3),'เทียบกับอัตราปลอดความเสี่ยง')+box('Sortino Ratio',n(s.sortino,3),'เทียบกับ MAR');$('risk-explanation').innerHTML=`<p>ค่าเฉลี่ยผลตอบแทนรายวัน ${p(s.meanReturn,4)} · SD รายวัน ${p(s.sampleStd,4)}<br>อัตราปลอดความเสี่ยงรายวัน ${p(s.riskFreePeriod,5)} · MAR รายวัน ${p(s.marPeriod,5)}</p><p>มี ${below} จาก ${pm.periods} วันที่ต่ำกว่า MAR ความเบี่ยงเบนต่ำกว่าเป้า (Downside Deviation) = ${p(s.downsideDeviation,4)} ต่อวัน โดยใช้ทั้ง ${pm.periods} วันเป็นตัวหาร</p>`;$('risk-status').textContent='Sharpe '+n(s.sharpe,3)+' Sortino '+n(s.sortino,3);}
 for(const id of ['rf','mar'])$(id).addEventListener('input',risk);$('reset-risk')?.addEventListener('click',()=>{$('rf').value=0;$('mar').value=0;risk();});
 $('theme-toggle')?.addEventListener('click',()=>{const dark=document.documentElement.dataset.theme!=='dark';document.documentElement.dataset.theme=dark?'dark':'light';$('theme-toggle').textContent=dark?'โหมดสว่าง':'โหมดมืด';$('theme-toggle').setAttribute('aria-pressed',String(dark));});
 $('nav-toggle')?.addEventListener('click',()=>{const hidden=document.body.classList.toggle('nav-hidden');$('nav-toggle').textContent=hidden?'แสดงสารบัญ':'ซ่อนสารบัญ';$('nav-toggle').setAttribute('aria-expanded',String(!hidden));});
 $('mobile-menu')?.addEventListener('click',()=>{const open=document.body.classList.toggle('menu-open');$('mobile-menu').setAttribute('aria-expanded',String(open));$('mobile-menu').textContent=open?'ปิดสารบัญ':'สารบัญ';});
 function closeMenu(){document.body.classList.remove('menu-open');$('mobile-menu').setAttribute('aria-expanded','false');$('mobile-menu').textContent='สารบัญ';}
 document.querySelectorAll('.local-toc a').forEach(a=>a.addEventListener('click',closeMenu));document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu();});
 if('IntersectionObserver'in window){const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){document.querySelectorAll('.local-toc a').forEach(a=>a.removeAttribute('aria-current'));const a=document.querySelector(`.local-toc a[href="#${e.target.id}"]`);if(a)a.setAttribute('aria-current','location');}}),{rootMargin:'-8% 0px -75% 0px'});document.querySelectorAll('.lesson h2[id]').forEach(h=>observer.observe(h));}
 if($('signal-bar'))signal();if($('trade-index'))trade();if($('distribution-index'))distribution();if($('cumulative-session'))cumulative();if($('win-rate'))resetWin();if($('session'))session();if($('rf'))risk();
})();
