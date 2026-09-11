import React,{useEffect,useRef,useState} from 'react';

export default function SignalChart({rows,shortWindow,longWindow,selected,onSelect}) {
  const holder=useRef(null);
  const [W,setWidth]=useState(760);
  useEffect(()=>{
    const observer=new ResizeObserver(entries=>setWidth(Math.max(290,entries[0].contentRect.width)));
    if(holder.current)observer.observe(holder.current);
    return()=>observer.disconnect();
  },[]);
  const H=W<480?245:300,pad={l:38,r:14,t:16,b:34};
  const min=Math.floor(Math.min(...rows.map(r=>r.close))/5)*5-5;
  const max=Math.ceil(Math.max(...rows.map(r=>r.close))/5)*5+5;
  const x=i=>pad.l+i/(rows.length-1)*(W-pad.l-pad.r);
  const y=v=>pad.t+(max-v)/(max-min)*(H-pad.t-pad.b);
  const path=key=>rows.map((r,i)=>r[key]===null?'':(i===0||rows[i-1][key]===null?'M':'L')+x(i).toFixed(2)+','+y(r[key]).toFixed(2)).join(' ');
  const chosen=rows[selected];
  const selectAt=e=>{
    const b=e.currentTarget.getBoundingClientRect();
    const pos=(e.clientX-b.left)/b.width*W;
    onSelect(Math.max(0,Math.min(rows.length-1,Math.round((pos-pad.l)/(W-pad.l-pad.r)*(rows.length-1)))));
  };
  return <div className="chart-wrap" ref={holder}>
    <svg className="signal-chart" viewBox={'0 0 '+W+' '+H} role="img" aria-label={'กราฟราคาจำลอง 120 แท่ง พร้อม SMA '+shortWindow+' และ '+longWindow+' ราคาหน่วยดอลลาร์สหรัฐ'} onPointerMove={selectAt}>
      <title>ราคาปิดจำลองและค่าเฉลี่ยเคลื่อนที่</title>
      <desc>แกนนอนคือแท่งที่ 1 ถึง 120 แกนตั้งคือราคาสมมติในหน่วย USD ดูค่ารายวันได้จากตัวเลื่อนหรือเปิดตารางข้อมูลใต้กราฟ</desc>
      {Array.from({length:(max-min)/5+1},(_,i)=>min+i*5).map(v=><g key={v}><line x1={pad.l} x2={W-pad.r} y1={y(v)} y2={y(v)} className="chart-grid"/><text x={pad.l-12} y={y(v)+4} textAnchor="end">{v}</text></g>)}
      {(W<480?[1,30,60,90,120]:[1,20,40,60,80,100,120]).map(d=><text key={d} x={x(d-1)} y={H-7} textAnchor="middle">{d}</text>)}
      <path d={path('close')} className="price-line"/><path d={path('short')} className="short-line"/><path d={path('long')} className="long-line"/>
      {rows.filter(r=>r.changed).map(r=><g key={r.day}><circle cx={x(r.day-1)} cy={y(r.close)} r={4.5} className={r.target?'entry-marker':'exit-marker'}/></g>)}
      {chosen&&<g><line x1={x(selected)} x2={x(selected)} y1={pad.t} y2={H-pad.b} className="cursor-line"/><circle cx={x(selected)} cy={y(chosen.close)} r={5} className="cursor-point"/></g>}
    </svg>
    <div className="chart-axis-label"><span>ราคา (USD) · ข้อมูลจำลอง</span><span>ลำดับแท่งรายวัน</span></div>
  </div>;
}
