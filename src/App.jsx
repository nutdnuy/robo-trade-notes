import React,{useEffect,useState} from 'react';
import config from '../content/book.json';
import welcomeSource from '../content/intro.md?raw';
import webullSource from '../content/chapters/11-webull-openapi-setup.md?raw';
import performanceSource from '../content/chapters/14-backtest-performance-evaluation.md?raw';
import backtestSource from '../content/chapters/13-introduction-backtest.md?raw';
import backtestQuestions from '../content/quizzes/chapter-13.json';
import BacktestIntroLab from './components/BacktestIntroLab.jsx';
import {TimingViz,VolatilitySizingViz,DrawdownRecoveryViz} from './components/BacktestConceptViz.jsx';
import whyRoboSource from '../content/chapters/12-why-robo-trade.md?raw';
import whyRoboQuestions from '../content/quizzes/chapter-12.json';
import whyRoboVisuals from '../references/why-robo-visuals.json';
import backtestTypeVisuals from '../references/backtest-types-visuals.json';
const lessonVisuals={...whyRoboVisuals,...backtestTypeVisuals};
import webullQuestions from '../content/quizzes/chapter-11.json';
import webullImages from '../references/webull-openapi-setup-images.json';
import webullQuote from '../references/webull-learning-quote.json';
import {parsePage,assetUrl} from './lib/book.js';
import {pageHref,readRoute} from './lib/navigation.js';
import {isPublishedPage} from './lib/publishing.js';
import BookMarkdown from './components/BookMarkdown.jsx';
import {Quiz} from './components/LessonWidgets.jsx';
import WelcomeAtlas from './components/WelcomeAtlas.jsx';
import BookShell from './components/BookShell.jsx';

const sources={welcome:welcomeSource,'chapter-11':webullSource,'chapter-12':whyRoboSource,'chapter-13':backtestSource,'chapter-14':performanceSource};
const pages=config.pages.map(page=>({...page,navigationTitle:page.label,...(sources[page.id]?parsePage(sources[page.id]):{})}));
const publishedPages=pages.filter(page=>isPublishedPage(page.id));
const lessonPresentation={
  'chapter-13':{questions:backtestQuestions,meta:'Backtesting / Research / Validation',start:'research-before-backtest',startLabel:'หลักคิดก่อนทดสอบ',secondarySection:'lab',secondaryLabel:'เปิดห้องทดลอง',art:null},
  'chapter-11':{questions:webullQuestions,meta:'Python / Webull OpenAPI',start:'before-start',startLabel:'Start with the checklist',art:'images/deltaris-workshop-v2.png',width:1536,height:1024,alt:'โรงงานริมทะเลแห่ง Deltaris ช่างฝีมือกำลังประกอบโกเลมทองเหลือง ภาพประกอบโลก Quantara'},
  'chapter-12':{secondarySection:'summary',secondaryLabel:'สรุปท้ายบท',questions:whyRoboQuestions,meta:'Trading / Investing / Quant',start:'why-robo',startLabel:'ทำไมต้อง Robo Trade',art:'images/deltaris-masters.png',width:1024,height:1536,alt:'ช่างและหุ่นกลในโรงช่าง Deltaris ภาพประกอบโลกสมมติ Quantara'}
};
const noop=()=>{};
const imageDimensions={'images/quantara-story-backtest-exam.png':[1536,1024],'images/quantara-story-backtest-letter.png':[1536,1024],'images/quantara-story-backtest-cargo.png':[1536,1024],...Object.fromEntries(webullImages.images.map(image=>[image.file,image.size])),[webullQuote.file]:webullQuote.size,'images/quantara-story-horizons.png':[1536,1024],'images/quantara-story-discarded-plans.png':[1536,1024],'images/quantara-story-delivery.png':[1536,1024]};

export default function App(){
  const [route,setRoute]=useState(()=>readRoute(pages));
  const [menuOpen,setMenuOpen]=useState(false);
  const page=pages.find(page=>page.id===route.page);
  const archived=!isPublishedPage(route.page);
  const welcome=page.kind==='welcome';
  useEffect(()=>{
    document.documentElement.dataset.theme='light';
    const update=()=>{setRoute(readRoute(pages));setMenuOpen(false);};
    window.addEventListener('hashchange',update);
    return()=>window.removeEventListener('hashchange',update);
  },[]);
  useEffect(()=>{
    document.title=archived?'Robo Trade Notes':welcome?'Quantara | Robo Trade Notes':page.title+' | Robo Trade Notes';
    if(archived)return;
    if(page.id==='chapter-14'){window.location.replace(pageHref(page.id,route.section));return;}
    const frame=requestAnimationFrame(()=>{
      if(route.section)document.getElementById(route.section)?.scrollIntoView();
      else window.scrollTo(0,0);
    });
    return()=>cancelAnimationFrame(frame);
  },[archived,page.title,route,welcome]);
  if(archived||page.id==='chapter-14')return null;
  if(welcome)return <BookShell page={page} pages={publishedPages} route={route} menuOpen={menuOpen} setMenuOpen={setMenuOpen}><WelcomeAtlas page={page} imageDimensions={imageDimensions}/></BookShell>;
  const presentation=lessonPresentation[page.id];
  const readingOrder=publishedPages.filter(item=>item.kind==='lesson');
  const lessonIndex=readingOrder.findIndex(item=>item.id===page.id);
  const previousLesson=readingOrder[lessonIndex-1];
  const nextLesson=readingOrder[lessonIndex+1];
  const widgets={'timing-viz':<TimingViz/>,'volatility-sizing-viz':<VolatilitySizingViz/>,'drawdown-recovery-viz':<DrawdownRecoveryViz/>,'backtest-intro-lab':<BacktestIntroLab/>,quiz:<Quiz key={page.id} questions={presentation.questions} onComplete={noop} onReset={noop}/>};
  // Retain the canonical Markdown; only the former introductory illustration
  // is replaced in this presentation by the shared Deltaris workshop artwork.
  const lessonIntro=page.intro.split('\n').filter(line=>!line.trim().startsWith('![')||!line.includes(']('+webullQuote.file+')')).join('\n').trim();
  return <BookShell page={page} pages={publishedPages} route={route} menuOpen={menuOpen} setMenuOpen={setMenuOpen}>
        <article className={"lesson-article field-guide-article"+(page.id==='chapter-12'?' why-robo-article':page.id==='chapter-13'?' backtest-intro-article':'')}>
          <header className="field-guide-cover" id="page-top">
            {presentation.art&&<figure className="field-guide-art">
              <img src={assetUrl(presentation.art)} alt={presentation.alt} width={presentation.width} height={presentation.height} fetchPriority="high"/>
              <figcaption>DELTARIS WORKSHOP</figcaption>
            </figure>}
            <div className="field-guide-cover-copy">
              <div className="field-guide-cover-meta">{presentation.meta}</div>
              <h1>{page.title}</h1>
              <div className="chapter-lead" lang="th"><BookMarkdown source={lessonIntro} pageId={page.id} imageDimensions={imageDimensions} imageVariants={lessonVisuals}/></div>
              <nav className="field-guide-actions" aria-label="Start or practice"><a href={pageHref(page.id,presentation.start)}>{presentation.startLabel} <span aria-hidden="true">↓</span></a><a href={pageHref(page.id,presentation.secondarySection||'practice')}>{presentation.secondaryLabel||'Notebook & files'} <span aria-hidden="true">↗</span></a></nav>
            </div>
          </header>
          {page.id==='chapter-13'?null:page.id==='chapter-11'?<aside className="field-guide-lore" aria-labelledby="gem-story-title" lang="th">
            <h2 id="gem-story-title">เรื่องเล่าจาก Quantara: เสียงจากอัญมณีสีน้ำเงิน</h2>
            <p>ช่างแห่ง Deltaris หมุนสลักที่อกหุ่นกล อัญมณีสีน้ำเงินสว่างขึ้น ก่อนส่งเสียงของเขาไปยังหอกลางเมือง “ได้ยินหรือไม่?” เขาถาม เสียงตอบดังกลับมาทันที “ได้ยิน ตั้งแต่เจ้าบ่นว่าประแจหายเมื่อเช้าแล้ว”</p>
            <p>หุ่นกลก้มมองอัญมณีของตัวเอง แล้วกระซิบว่า “ถ้าอย่างนั้น ช่วยแจ้งหอกลางด้วยว่าข้าขอพัก” ช่างยื่นมือจะปิดสัญญาณ แต่ช้าไป เสียงหัวเราะจากหอส่งกลับมาถึงโรงงาน ตามด้วยคำถามว่า “หุ่นขอพัก หรือคนถือประแจ?”</p>
          </aside>:<aside className="field-guide-lore" aria-labelledby="gem-story-title" lang="th">
            <h2 id="gem-story-title">เรื่องเล่าจาก Quantara: คำสั่งที่ยังทำไม่ได้</h2>
            <p>เสียงจากหอกลางดังผ่านอัญมณีสีน้ำเงินที่อกหุ่น “วันนี้ซื้อทองเหลืองเมื่อราคาถูก” หุ่นจรดปากกาลงสมุดแล้วถามกลับ “ถูกกว่าเมื่อวาน หรือถูกใจท่านหัวหน้าหอ?”</p>
            <p>ปลายสายเงียบไปครู่หนึ่ง ก่อนตอบว่า “เดี๋ยวข้าเขียนใหม่” หุ่นหันไปบอกช่างว่า “ระหว่างรอ ข้าไปรอที่ร้านขนมได้ไหม?” ช่างมองมันแล้วเขียนเพิ่มว่า “ให้รออยู่กับที่”</p>
          </aside>}
          <div className="field-guide-reading">
            {page.sections.map(section=><section className="lesson-section" key={section.id}><div className="section-heading"><span className="field-guide-section-number" aria-hidden="true">{section.number}</span><h2 id={section.id}>{section.label}</h2></div><BookMarkdown source={section.body} pageId={page.id} widgets={widgets} imageDimensions={imageDimensions} imageVariants={lessonVisuals}/></section>)}
          </div>
          <nav className="lesson-pagination" aria-label="Reading order">
            {previousLesson&&<a href={pageHref(previousLesson.id)}><span>← บทก่อนหน้า</span>{previousLesson.title}</a>}
            {nextLesson&&<a className="lesson-next" href={pageHref(nextLesson.id)}><span>บทถัดไป →</span>{nextLesson.title}</a>}
          </nav>
          <footer className="page-footer"><a href={pageHref('welcome')}>← Back to Quantara</a><span>QUANTARA / DELTARIS</span><a href={pageHref(page.id,'page-top')}>Back to top ↑</a></footer>
        </article>
  </BookShell>;
}
