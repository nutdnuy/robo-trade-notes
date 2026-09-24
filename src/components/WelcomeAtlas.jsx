import React, {useState} from 'react';
import {assetUrl} from '../lib/book.js';
import {pageHref} from '../lib/navigation.js';
import BookMarkdown from './BookMarkdown.jsx';

// Fantasy locations decorate existing lessons; they do not define trading logic.
const destinations = [
  {id:'before-start', title:'The northern citadel', lesson:'Prepare for the journey', place:'Sigmora', x:57, y:16, description:'นครเหนือยอดเขา ที่ซึ่งนักเดินทางตรวจสัมภาระสามรอบ ก่อนพบว่าลืมคู่มือไว้ที่บ้าน', number:'01'},
  {id:'market-data', title:'The whispering forest', lesson:'Understand market data', place:'Covaria', x:36, y:33, description:'ป่าแห่งข่าวสารและข้อมูล ต้นไม้ที่นี่กระซิบเก่ง แต่ชาวเมืองก็ยังขอดูแหล่งอ้างอิงก่อนเชื่อ', number:'02'},
  {id:'create-key', title:'The city of crossings', lesson:'Create your API access', place:'Alphora', x:56, y:51, description:'ทุกเส้นทางมาบรรจบกันที่นครการค้าแห่งนี้ แม้แต่การเข้ากิลด์ก็ต้องมีกุญแจให้ถูกดอก', number:'03'},
  {id:'sdk-and-token', title:'Home of the machine makers', lesson:'Set up Python & the SDK', place:'Deltaris', x:84, y:43, description:'บ้านของ Algorithmic Trading Masters ผู้เปลี่ยนกฎให้เป็นโค้ด และโค้ดให้เป็นเครื่องจักร ส่วนเสียงกุกกักนั้น… กำลังแก้บั๊กอยู่', number:'04'},
  {id:'troubleshooting', title:'The watch at the edge', lesson:'Find and fix the problem', place:'Tailgard', x:39, y:69, description:'ป้อมยามชายแดนที่เฝ้าระวังสิ่งผิดปกติ โดยเฉพาะเครื่องจักรที่ประกาศว่า “ไม่น่ามีอะไรผิดพลาด”', number:'05'},
  {id:'first-call', title:'The tidebound port', lesson:'Read your first API response', place:'Arbitra', x:82, y:77, description:'ท่าเรือปลายแม่น้ำ จดหมายทุกฉบับต้องตรวจตราประทับ เหมือนผลลัพธ์ทุกครั้งที่ต้องอ่านให้เข้าใจ', number:'06'},
];
const machineStates = [
  {label:'OFF DUTY', line:'“ข้าไม่ได้หลับ ข้ากำลังประมวลผลด้วยตาปิด”', note:'One turn of the key should do it.'},
  {label:'BOOTING… PROBABLY', line:'“เครื่องพร้อมแล้ว อาจารย์! …อาจารย์เสียบกาต้มน้ำอยู่”', note:'The kettle has joined the engineering team.'},
  {label:'DIAGNOSTICS COMPLETE', line:'“พบบั๊กหนึ่งตัว มันอยู่ในรองเท้า ไม่ได้อยู่ในโค้ด”', note:'Please return the beetle to Covaria.'},
  {label:'COFFEE BREAK', line:'“ข้าไม่ต้องพัก แต่คนเขียนข้าต้องพัก ไปอ่านคู่มือก่อนเถอะ”', note:'A surprisingly sensible machine.'},
];

export function skipToMain(event) {
  event.preventDefault();
  const main = document.getElementById('main-content');
  main?.focus({preventScroll:true});
  main?.scrollIntoView();
}

export function AtlasHeader({welcome=false, menuOpen=false, onMenuToggle}) {
  return <header className="atlas-site-header" onKeyDown={event=>{if(event.key==='Escape'&&menuOpen){onMenuToggle();document.getElementById('contents-toggle')?.focus();}}}>
    <a className="atlas-brand" href={pageHref('welcome')} aria-label="Robo Trade Notes home">
      <img src={assetUrl('images/quantcorner-mark-light.svg')} width="44" height="44" alt="QuantCorner"/>
      <span>Robo Trade Notes<small>Dispatches from Quantara</small></span>
    </a>
    <nav className="atlas-navigation" aria-label="Main navigation">
      <a href={pageHref('welcome')} aria-current={welcome?'page':undefined}>The kingdom</a>
      <a href={pageHref('chapter-11')} aria-current={!welcome?'page':undefined}>Field guide</a>
      <a className="atlas-skill-link" href="https://www.quant-corner.com/skill-tree">Skill Tree <span aria-hidden="true">↗</span></a>
    </nav>
    <a className="atlas-community-link" href="https://www.quant-corner.com/">Back to QuantCorner <span aria-hidden="true">↗</span></a>
    {onMenuToggle&&<button id="contents-toggle" className="atlas-contents-toggle" aria-expanded={menuOpen} aria-controls="book-navigation" onClick={onMenuToggle}>{menuOpen?'Close':'Contents'}</button>}
  </header>;
}

export default function WelcomeAtlas({page, imageDimensions}) {
  const [selected, setSelected] = useState(3);
  const [machineState, setMachineState] = useState(0);
  const destination = destinations[selected];
  const machine = machineStates[machineState];
  return <div className="atlas-page quantara-page">
    <a className="skip-link" href="#main-content" onClick={skipToMain}>Skip to content</a>
    <AtlasHeader welcome/>
    <main id="main-content" className="atlas-main quantara-main" tabIndex="-1">
      <section className="quantara-hero" aria-labelledby="quantara-title">
        <img className="quantara-hero-art" src={assetUrl('images/deltaris-workshop-v2.png')} alt="โรงงาน Deltaris ริมทะเล ช่างแคระกำลังสร้างหุ่นกลทองเหลือง ท่ามกลางเฟืองและผู้ช่วยจักรกลตัวจิ๋ว" width="1536" height="1024" fetchPriority="high"/>
        <div className="quantara-hero-copy">
          <span className="quantara-kicker">A QUANTCORNER CHRONICLE</span>
          <h1 id="quantara-title">Welcome to <br/><span>Quantara.</span></h1>
          <p className="quantara-hero-motto">Great minds. Ridiculous machines.</p>
          <p className="quantara-hero-thai" lang="th">อาณาจักรของนักคิด นักสร้าง และเครื่องจักร<br className="wide-only"/>ที่ยังแยกกาแฟออกจากน้ำมันเครื่องไม่ค่อยได้</p>
          <div className="quantara-hero-actions"><a href={pageHref('welcome','deltaris-workshop')}>Meet the makers <span aria-hidden="true">↗</span></a><a href={pageHref('welcome','quantara-map')}>Unfold the map <span aria-hidden="true">↓</span></a></div>
          <span className="quantara-hero-footnote">PYTHON · WEBULL OPENAPI · A LITTLE TOO MUCH STEAM</span>
        </div>
        <div className="quantara-location"><span>YOU ARE IN</span><strong>Deltaris</strong><small>The coastal foundry of Quantara</small></div>
        <span className="quantara-scene-label">ARTISAN DISTRICT / WORKSHOP 04</span>
      </section>
      <div className="quantara-dispatch"><span>NOTICE FROM THE GUILD</span><p lang="th">กรุณาอย่าให้อาหารหุ่นกลหลังเที่ยงคืน โดยเฉพาะไฟล์ CSV ที่ไม่มีหัวตาราง</p><span aria-hidden="true">◆</span></div>

      <section id="deltaris-workshop" className="deltaris-workshop" aria-labelledby="makers-title" tabIndex="-1">
        <div className="deltaris-portrait-panel">
          <div className="guild-portrait-top"><span>DELTARIS GUILD</span><span>EST. BEFORE THE FIRST BUG</span></div>
          <figure className={'deltaris-masters'+(machineState?' is-awake':'')}>
            <img key={machineState} src={assetUrl('images/deltaris-masters.png')} alt="Algorithmic Trading Master ชาว Deltaris ถือประแจ ยืนคู่หุ่นกลทองเหลืองขนาดใหญ่ที่มีแกนพลังงานสีฟ้า" width="1024" height="1536" loading="lazy"/>
            <figcaption><strong>The maker & the machine</strong><span>One writes the rules. The other takes them literally.</span></figcaption>
          </figure>
          <span className="guild-paper-stamp" aria-hidden="true">BUILT IN<br/><strong>DELTARIS</strong><br/>MOSTLY ON PURPOSE</span>
        </div>
        <div className="deltaris-workshop-copy">
          <span className="atlas-eyebrow">PEOPLE OF QUANTARA / THE MAKERS OF DELTARIS</span>
          <h2 id="makers-title">Algorithmic <br/>Trading Masters<span>.</span></h2>
          <p className="deltaris-lead" lang="th">บางเมืองสร้างปราสาท<br/>ชาว Deltaris สร้างเครื่องจักรที่ถามว่า<br/><strong>“แล้วถ้าลองเขียนเป็นกฎล่ะ?”</strong></p>
          <p lang="th">ในอาณาจักร Quantara เมืองโรงหลอมริมทะเลแห่งนี้คือบ้านของเหล่า Algorithmic Trading Masters พวกเขาใช้ตรรกะ ข้อมูล และ Python สร้างเครื่องจักรให้ทำงานตามกฎ ส่วนการเข้าใจว่ากฎนั้นผิดตรงไหน… ยังเป็นหน้าที่ของคนสร้าง</p>
          <div className="guild-craft"><span>THE CRAFT</span><p>Write a rule. Test it. Find the bug. Repeat.</p></div>
          <div className="machine-console">
            <div className="machine-console-heading"><span className={'machine-state-light'+(machineState?' is-awake':'')} aria-hidden="true"/><span>BRASS COMPANION / WORKSHOP TOY</span></div>
            <div className="machine-reply" role="status" aria-live="polite" aria-atomic="true"><span className="machine-state">{machine.label}</span><p lang="th">{machine.line}</p><small>{machine.note}</small></div>
            <div className="machine-actions"><button onClick={()=>setMachineState(state=>(state+1)%machineStates.length)}>{machineState?'Turn the key again':'Wake the automaton'} <span aria-hidden="true">↻</span></button>{machineState>0&&<button className="machine-reset" onClick={()=>setMachineState(0)}>Let it nap</button>}</div>
          </div>
          <a className="guild-guide-link" href={pageHref('chapter-11')}>Apprentices start here <span aria-hidden="true">↗</span><small>คู่มือ Python และ Webull OpenAPI ทีละขั้น</small></a>
        </div>
      </section>

      <section id="quantara-map" className="quantara-world" aria-labelledby="atlas-title" tabIndex="-1">
        <div className="quantara-section-heading"><div><span className="atlas-eyebrow">THE KINGDOM, AS FAR AS WE KNOW IT</span><h2 id="atlas-title">Six cities. Many questionable ideas.</h2></div><p lang="th">เปิดแผนที่ เลือกเมือง<br/>แล้วหยิบบทเรียนติดมือกลับไป</p></div>
        <div className="quantara-map-layout">
          <figure className="atlas-map">
            <img src={assetUrl(page.heroImage)} alt={page.heroAlt} width="1536" height="1024" loading="lazy"/>
            <div className="atlas-map-caption" aria-hidden="true"><span>KINGDOM OF QUANTARA</span><small>Here be dragons. And debugging.</small></div>
            <div className="atlas-map-pins" role="group" aria-label="Choose a city in Quantara">
              {destinations.map((item,index)=><button key={item.id} className={'atlas-map-pin'+(selected===index?' is-selected':'')} style={{'--pin-x':item.x+'%','--pin-y':item.y+'%'}} aria-label={item.place+' — '+item.lesson} aria-pressed={selected===index} aria-controls="atlas-topic-detail" onClick={()=>setSelected(index)}><span>{item.number}</span><small>{item.place}</small></button>)}
            </div>
            <figcaption>Quantara · The known lands <span>Illustrated world / learning destinations</span></figcaption>
          </figure>
          <div id="atlas-topic-detail" className="quantara-city-passport" aria-live="polite" aria-atomic="true">
            <span className="passport-kicker">FIELD PASSPORT / {destination.number}</span>
            {destination.place==='Deltaris'?<img className="passport-city-art" src={assetUrl('images/deltaris-card.png')} alt="การ์ดเมือง Deltaris โรงหลอมบนหน้าผาริมทะเล" width="1024" height="1536" loading="lazy"/>:<div className="passport-number" aria-hidden="true">{destination.number}</div>}
            <span className="atlas-eyebrow">{destination.title}</span><h3>{destination.place}</h3><p lang="th">{destination.description}</p>
            <div className="passport-lesson"><span>TAKE A FIELD NOTE</span><strong>{destination.lesson}</strong><a href={pageHref('chapter-11',destination.id)}>Open the lesson <span aria-hidden="true">↗</span><span className="atlas-sr-only">: {destination.lesson}</span></a></div>
          </div>
        </div>
        <div className="quantara-city-selector" role="group" aria-label="Cities of Quantara">
          {destinations.map((item,index)=><button key={item.id} aria-pressed={selected===index} aria-controls="atlas-topic-detail" onClick={()=>setSelected(index)}><span>{item.number}</span>{item.place}<small>{item.place==='Deltaris'?'MACHINE MAKERS':item.title}</small></button>)}
        </div>
      </section>

      <div className="atlas-reading-area quantara-reading">
        <div className="atlas-reading-label"><span className="atlas-eyebrow">THE APPRENTICE'S FIRST ASSIGNMENT</span><h2>Less guessing.<br/>More reading.</h2><p lang="th">หุ่นพร้อมแล้ว<br/>คนสร้างพร้อมหรือยัง?</p><a href={pageHref('chapter-11','before-start')}>Check your toolkit <span aria-hidden="true">↗</span></a></div>
        <article className="atlas-original-content" aria-label="Account and API setup" lang="th">
          <div className="quantara-source-intro"><BookMarkdown source={page.intro} pageId="welcome"/></div>
          {page.sections.map(section=><section className="lesson-section" key={section.id}><div className="section-heading"><h2 id={section.id}>{section.label}</h2></div><BookMarkdown source={section.body} pageId="welcome" imageDimensions={imageDimensions}/></section>)}
        </article>
      </div>
    </main>
    <footer className="atlas-footer"><span>Quantara <span aria-hidden="true">/</span> A QuantCorner world</span><span>Forged in Deltaris. Debugged eventually.</span><a href={pageHref('chapter-11')}>Back to the field guide <span aria-hidden="true">↗</span></a></footer>
  </div>;
}
