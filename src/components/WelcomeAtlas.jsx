import React, {useState} from 'react';
import {assetUrl} from '../lib/book.js';
import {pageHref} from '../lib/navigation.js';

const machineStates = [
  {label:'OFF DUTY', line:'“ข้าไม่ได้หลับ ข้ากำลังประมวลผลด้วยตาปิด”', note:'One turn of the key should do it.'},
  {label:'BOOTING… PROBABLY', line:'“เครื่องพร้อมแล้ว อาจารย์! …อาจารย์เสียบกาต้มน้ำอยู่”', note:'The kettle has joined the engineering team.'},
  {label:'DIAGNOSTICS COMPLETE', line:'“พบบั๊กหนึ่งตัว มันอยู่ในรองเท้า ไม่ได้อยู่ในโค้ด”', note:'Please return the beetle to Covaria.'},
  {label:'COFFEE BREAK', line:'“ข้าไม่ต้องพัก แต่คนเขียนข้าต้องพัก ไปอ่านคู่มือก่อนเถอะ”', note:'A surprisingly sensible machine.'},
];

export default function WelcomeAtlas({page}) {
  const [machineState, setMachineState] = useState(0);
  const machine = machineStates[machineState];
  return <div className="quantara-page">
      <section id="webull-start" className="quantara-hero" aria-labelledby="quantara-title">
        <img className="quantara-hero-art" src={assetUrl('images/deltaris-workshop-v2.png')} alt="โรงงาน Deltaris ริมทะเล ช่างแคระกำลังสร้างหุ่นกลทองเหลือง ท่ามกลางเฟืองและผู้ช่วยจักรกลตัวจิ๋ว" width="1536" height="1024" fetchPriority="high"/>
        <div className="quantara-hero-copy">
          <span className="quantara-kicker">KINGDOM OF QUANTARA</span>
          <h1 id="quantara-title">Welcome to <br/><span>Quantara.</span></h1>
          <p className="quantara-hero-thai" lang="th">อาณาจักรของนักคิด นักสร้าง และเครื่องจักร<br className="wide-only"/>ที่ยังแยกกาแฟออกจากน้ำมันเครื่องไม่ค่อยได้</p>
          <div className="quantara-hero-actions"><a href={pageHref('welcome','deltaris-workshop')}>Meet the makers <span aria-hidden="true">↗</span></a><a href={pageHref('welcome','quantara-map')}>Unfold the map <span aria-hidden="true">↓</span></a></div>
        </div>
        <span className="quantara-scene-label">DELTARIS WORKSHOP</span>
      </section>
      <div className="quantara-dispatch"><span>NOTICE FROM THE GUILD</span><p lang="th">กรุณาอย่าให้อาหารหุ่นกลหลังเที่ยงคืน โดยเฉพาะไฟล์ CSV ที่ไม่มีหัวตาราง</p></div>

      <section id="deltaris-workshop" className="deltaris-workshop" aria-labelledby="makers-title" tabIndex="-1">
        <div className="deltaris-portrait-panel">
          <figure className={'deltaris-masters'+(machineState?' is-awake':'')}>
            <img key={machineState} src={assetUrl('images/deltaris-masters.png')} alt="Algorithmic Trading Master ชาว Deltaris ถือประแจ ยืนคู่หุ่นกลทองเหลืองขนาดใหญ่ที่มีแกนพลังงานสีฟ้า" width="1024" height="1536" loading="lazy"/>
            <figcaption><strong>The maker & the machine</strong><span lang="th">เรื่องเล่าใน Quantara: อัญมณีสีน้ำเงินที่อกหุ่นกล Deltaris ส่งสัญญาณไปยังหอกลางเมืองได้ บางทีก็ส่งไปถามว่า “พักกาแฟหรือยัง?”</span></figcaption>
          </figure>
        </div>
        <div className="deltaris-workshop-copy">
          <span className="atlas-eyebrow">PEOPLE OF QUANTARA / THE MAKERS OF DELTARIS</span>
          <h2 id="makers-title">Algorithmic <br/>Trading Masters<span>.</span></h2>
          <p className="deltaris-lead" lang="th">บางเมืองสร้างปราสาท<br/>ชาว Deltaris สร้างเครื่องจักรที่ถามว่า<br/><strong>“แล้วถ้าลองเขียนเป็นกฎล่ะ?”</strong></p>
          <p lang="th">ในอาณาจักร Quantara เมืองโรงหลอมริมทะเลแห่งนี้คือบ้านของเหล่า Algorithmic Trading Masters พวกเขาใช้ตรรกะ ข้อมูล และ Python สร้างเครื่องจักรให้ทำงานตามกฎ ส่วนการเข้าใจว่ากฎนั้นผิดตรงไหน… ยังเป็นหน้าที่ของคนสร้าง</p>
          <div className="machine-console">
            <div className="machine-console-heading"><span className={'machine-state-light'+(machineState?' is-awake':'')} aria-hidden="true"/><span>BRASS COMPANION / WORKSHOP TOY</span></div>
            <div className="machine-reply" role="status" aria-live="polite" aria-atomic="true"><span className="machine-state">{machine.label}</span><p lang="th">{machine.line}</p><small>{machine.note}</small></div>
            <div className="machine-actions"><button onClick={()=>setMachineState(state=>(state+1)%machineStates.length)}>{machineState?'Turn the key again':'Wake the automaton'} <span aria-hidden="true">↻</span></button>{machineState>0&&<button className="machine-reset" onClick={()=>setMachineState(0)}>Let it nap</button>}</div>
          </div>
          <a className="guild-guide-link" href={pageHref('chapter-11')}>Apprentices start here <span aria-hidden="true">↗</span><small>คู่มือ Python และ Webull OpenAPI ทีละขั้น</small></a>
        </div>
      </section>

      <section id="quantara-map" className="quantara-world" aria-labelledby="atlas-title" tabIndex="-1">
        <div className="quantara-section-heading"><h2 id="atlas-title">Quantara</h2></div>
        <div className="quantara-map-layout">
          <figure className="atlas-map">
            <img src={assetUrl(page.heroImage)} alt={page.heroAlt} width="1536" height="1024" loading="lazy"/>
            <figcaption>KINGDOM OF QUANTARA</figcaption>
          </figure>
          <aside id="atlas-topic-detail" className="quantara-city-passport" aria-labelledby="deltaris-city-title">
            <img className="passport-city-art" src={assetUrl('images/deltaris-card.png')} alt="การ์ดเมือง Deltaris โรงหลอมบนหน้าผาริมทะเล" width="1024" height="1536" loading="lazy"/>
            <h3 id="deltaris-city-title">Deltaris</h3>
            <p lang="th">บ้านของ Algorithmic Trading Masters ผู้เปลี่ยนกฎให้เป็นโค้ด และโค้ดให้เป็นเครื่องจักร ส่วนเสียงกุกกักนั้น… กำลังแก้บั๊กอยู่</p>
            <a href={pageHref('chapter-11','sdk-and-token')}>OpenAPI field guide <span aria-hidden="true">↗</span></a>
          </aside>
        </div>
      </section>

    <footer className="atlas-footer"><span>Quantara <span aria-hidden="true">/</span> A QuantCorner world</span><a href={pageHref('chapter-11')}>Back to the field guide <span aria-hidden="true">↗</span></a></footer>
  </div>;
}
