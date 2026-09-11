import React,{useMemo,useState} from 'react';
import {IconBook2,IconSearch,IconChevronRight,IconChevronLeft,IconMenu2,IconX,IconMoon,IconSun,IconDownload,IconArrowUpRight,IconCode,IconCheck,IconCopy,IconClock,IconChartLine,IconAdjustments,IconArrowRight,IconDatabase,IconInfoCircle,IconRefresh,IconListDetails,IconBookmark,IconExternalLink,IconPrinter} from '@tabler/icons-react';
import CountUp from './reactbits/CountUp.jsx';
import AnimatedList from './reactbits/AnimatedList.jsx';
import Stepper,{Step} from './reactbits/Stepper.jsx';
import SignalChart from './SignalChart.jsx';
import {makeFixture,calculateSignals,signalEvents} from '../lib/lesson.js';
import apiCode from '../../public/downloads/webull_bars.py?raw';
import lessonCode from '../../public/downloads/lesson_01.py?raw';



const SAMPLE_PAYLOAD=JSON.stringify({symbols:['AAPL'],category:'US_STOCK',timespan:'D',count:120,real_time_required:true,trading_sessions:'RTH'},null,2);
export function CodeBlock({code,title,language='python',label}) {
  const [copied,setCopied]=useState(false);
  async function copy(){try{await navigator.clipboard.writeText(code);setCopied(true);setTimeout(()=>setCopied(false),1800);}catch{setCopied(false);}}
  return <div className="code-block"><div className="code-heading"><span><IconCode size={16}/>{title}</span><div><small>{language}</small><button aria-label={'คัดลอกโค้ด '+title} title="คัดลอกโค้ด" onClick={copy}>{copied?<IconCheck size={17}/>:<IconCopy size={17}/>}<span>{copied?'คัดลอกแล้ว':'คัดลอก'}</span></button></div></div><pre tabIndex={0}><code>{code.split('\n').map((line,i)=><span className={'code-line '+(/^\s*#/.test(line)?'comment':/^(from|import|def|if|for|with|class)\b/.test(line)?'keyword':'')} key={i}><span className="line-number" aria-hidden="true">{i+1}</span><span>{line||' '}</span></span>)}</code></pre>{label&&<div className="code-label">{label}</div>}</div>;
}
export function Lab(){
  const [short,setShort]=useState(5),[long,setLong]=useState(20),[selected,setSelected]=useState(119);
  const rows=useMemo(()=>calculateSignals(makeFixture(),short,long),[short,long]);
  const events=useMemo(()=>signalEvents(rows),[rows]);
  const row=rows[selected];
  return <div className="lab">
    <div className="lab-header"><div><span className="eyebrow">INTERACTIVE LAB</span><h3>เมื่อเส้นเฉลี่ยเปลี่ยน สัญญาณก็เปลี่ยน</h3></div><span className="badge"><span className="status-dot"/>ข้อมูลจำลอง</span></div>
    <div className="lab-controls">
      <label><span><i className="legend-line short"/>SMA ระยะสั้น <strong>{short}</strong> แท่ง</span><input type="range" aria-label="SMA ระยะสั้น" min="3" max="15" value={short} onChange={e=>setShort(Number(e.target.value))}/><div className="range-ends"><small>ตอบสนองเร็ว</small><small>นุ่มนวลขึ้น</small></div></label>
      <label><span><i className="legend-line long"/>SMA ระยะยาว <strong>{long}</strong> แท่ง</span><input type="range" aria-label="SMA ระยะยาว" min="20" max="50" value={long} onChange={e=>setLong(Number(e.target.value))}/><div className="range-ends"><small>20 แท่ง</small><small>50 แท่ง</small></div></label>
      <button className="icon-btn reset" title="คืนค่า 5 / 20" aria-label="คืนค่าช่วง SMA" onClick={()=>{setShort(5);setLong(20);setSelected(119);}}><IconRefresh size={20}/></button>
    </div>
    <div className="chart-legend"><span><i className="legend-line price"/>ราคาปิด</span><span><i className="legend-line short"/>SMA {short}</span><span><i className="legend-line long"/>SMA {long}</span><span className="event-legend">○ เปลี่ยนสถานะเป้าหมาย</span></div>
    <SignalChart rows={rows} shortWindow={short} longWindow={long} selected={selected} onSelect={setSelected}/>
    <div className="day-scrubber"><label htmlFor="day">สำรวจแท่งที่ <strong>{selected+1}</strong></label><input id="day" type="range" min="0" max="119" value={selected} onChange={e=>setSelected(Number(e.target.value))}/></div>
    <div className="lab-readout" aria-live="polite">
      <div><span>ราคาปิด · USD</span><strong>{row.close.toFixed(2)}</strong></div>
      <div><span>SMA {short} / {long}</span><strong className="ma-readout">{row.short?.toFixed(2)??'—'} <em>/</em> {row.long?.toFixed(2)??'—'}</strong></div>
      <div><span>สถานะเป้าหมายหลังปิดแท่ง</span><strong className={'state-text '+(row.target?'long-state':'')}>{row.signal==='WARMUP'?'รอข้อมูล':row.target?'LONG':'CASH'}</strong></div>
      <div><span>จุดเปลี่ยนทั้งหมด · 120 แท่ง</span><strong><CountUp key={short+'-'+long} to={events.length} duration={0.35}/> <small>ครั้ง</small></strong></div>
    </div>
    <div className="lab-explanation"><IconInfoCircle size={19}/><p>{!row.ready?'ข้อมูลยังไม่ครบ '+long+' แท่ง จึงยังไม่ประเมิน SMA ระยะยาว':row.target?'เส้นระยะสั้นอยู่เหนือเส้นระยะยาว กติกาจึงให้สถานะเป้าหมายเป็น LONG': 'เส้นระยะสั้นไม่อยู่เหนือเส้นระยะยาว กติกาจึงให้สถานะเป้าหมายเป็น CASH'} <span>นี่คือผลของกติกา ไม่ใช่คำสั่งซื้อขายที่ส่งแล้ว</span></p></div>
    <details className="events-details"><summary><IconListDetails size={19}/>สำรวจจุดเปลี่ยนสถานะ ({events.length} จุด)<IconChevronRight size={17}/></summary><p className="small-copy">เลือกแถวเพื่อดูราคาที่เกิดสัญญาณบนกราฟ</p><AnimatedList items={events.map(r=>'แท่ง '+r.day+'  ·  '+(r.target?'LONG':'CASH')+'  ·  ราคาปิด '+r.close.toFixed(2)+' USD')} onItemSelect={(_,i)=>setSelected(events[i].day-1)} showGradients={false} enableArrowNavigation={false}/></details>
    <details className="data-details"><summary>ดูข้อมูลและค่าเฉลี่ยทั้ง 120 แท่ง<IconChevronRight size={17}/></summary><div className="table-scroll"><table><thead><tr><th>แท่ง</th><th>Close</th><th>SMA {short}</th><th>SMA {long}</th><th>เป้าหมาย</th></tr></thead><tbody>{rows.map(r=><tr key={r.day}><td>{r.day}</td><td>{r.close.toFixed(2)}</td><td>{r.short?.toFixed(2)??'—'}</td><td>{r.long?.toFixed(2)??'—'}</td><td>{r.signal}</td></tr>)}</tbody></table></div></details>
    <div className="lab-footnote">ชุดข้อมูลสังเคราะห์ DEMO · 120 แท่งรายวันสมมติ · หน่วย USD · สร้างจากสูตรคงที่ · ไม่ใช่ราคาจาก Webull และไม่มีผลตอบแทนจากการซื้อขาย</div>
  </div>;
}

export function Quiz({questions,onComplete,onReset}){
  const [answers,setAnswers]=useState({}),[checked,setChecked]=useState({}),[step,setStep]=useState(1),[done,setDone]=useState(false),[attempt,setAttempt]=useState(0);
  const score=questions.reduce((s,q,i)=>s+(answers[i]===q.answer?1:0),0);
  function reset(){setAnswers({});setChecked({});setStep(1);setDone(false);setAttempt(a=>a+1);onReset();}
  return <div className="quiz">
    <div className="quiz-top"><span className="eyebrow">KNOWLEDGE CHECK</span><span>{done?'ทบทวนครบแล้ว':'ข้อ '+step+' จาก '+questions.length}</span></div>
    {done?<div className="quiz-complete" aria-live="polite"><IconCheck size={28}/><h3>คุณทบทวนครบแล้ว</h3><p>ตอบถูก {score} จาก {questions.length} ข้อ{score===questions.length?' พร้อมนำแนวคิดไปทดลองต่อได้เลย':' ลองอ่านเฉลยและทำอีกครั้งเพื่อย้ำความเข้าใจ'}</p><button className="button secondary" onClick={reset}><IconRefresh size={18}/>ทำอีกครั้ง</button></div>:
    <Stepper key={attempt} initialStep={1} onStepChange={setStep} onFinalStepCompleted={()=>{setDone(true);onComplete(score);}} backButtonText="ข้อก่อนหน้า" nextButtonText="ข้อถัดไป" completeButtonText="ดูผลทบทวน" disableStepIndicators nextButtonProps={{disabled:!checked[step-1]}}>
      {questions.map((q,i)=><Step key={q.title}><fieldset><legend>{q.title}</legend><div className="quiz-options">{q.options.map((o,j)=><label key={o} className={(answers[i]===j?'chosen ':'')+(checked[i]&&q.answer===j?'correct':'')}><input type="radio" name={'question-'+i} value={j} checked={answers[i]===j} disabled={Boolean(checked[i])} onChange={()=>setAnswers({...answers,[i]:j})}/><span>{o}</span>{checked[i]&&q.answer===j&&<IconCheck size={19}/>}</label>)}</div></fieldset>{!checked[i]?<button className="button secondary check-answer" disabled={answers[i]===undefined} onClick={()=>setChecked({...checked,[i]:true})}>ตรวจคำตอบ<IconArrowRight size={17}/></button>:<div className="answer-feedback" aria-live="polite"><strong>{answers[i]===q.answer?'ถูกต้อง':'ลองทบทวนจุดนี้อีกครั้ง'}</strong><p>{q.explanation}</p></div>}</Step>)}
    </Stepper>}
  </div>;
}


export function ApiExample(){
  const [codeTab,setCodeTab]=useState("sdk");
  const apiExcerpt=apiCode.slice(apiCode.indexOf("def fetch_bars"),apiCode.indexOf("\ndef main")).trim();
  return <>
<div className="code-tabs" role="tablist" aria-label="ตัวอย่าง Webull" onKeyDown={e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();const next=e.key==='Home'?'sdk':e.key==='End'?'request':codeTab==='sdk'?'request':'sdk';setCodeTab(next);document.getElementById('code-tab-'+next)?.focus();}}}><button id="code-tab-sdk" role="tab" aria-controls="webull-code-panel" tabIndex={codeTab==='sdk'?0:-1} aria-selected={codeTab==='sdk'} onClick={()=>setCodeTab('sdk')}>Python SDK</button><button id="code-tab-request" role="tab" aria-controls="webull-code-panel" tabIndex={codeTab==='request'?0:-1} aria-selected={codeTab==='request'} onClick={()=>setCodeTab('request')}>Request body</button></div>
          <div id="webull-code-panel" role="tabpanel" aria-labelledby={'code-tab-'+codeTab}><CodeBlock title={codeTab==='sdk'?'webull_bars.py · ฟังก์ชันรับข้อมูล':'POST /market-data/stocks/bars/list'} language={codeTab==='sdk'?'python':'json'} code={codeTab==='sdk'?apiExcerpt:SAMPLE_PAYLOAD} label="ตรวจชื่อเมธอดกับ SDK 3.0.0 และเอกสารทางการแล้ว · การเชื่อมต่อ API ยังไม่ได้รันด้วยบัญชีของคุณ"/></div>
  </>;
}

export function SmaExample(){
  const excerpt="import pandas as pd\n\n"+lessonCode.slice(lessonCode.indexOf("def build_signals"),lessonCode.indexOf("\ndef main")).trim();
  return <CodeBlock title="lesson_01.py · คำนวณสัญญาณ" code={excerpt} label="รันกับข้อมูลจำลองที่ให้มาพร้อมบทเรียนได้ โดยไม่ต้องติดตั้ง Webull SDK"/>;
}
