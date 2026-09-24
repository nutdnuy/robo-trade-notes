import React,{useEffect,useState} from 'react';
import config from '../content/book.json';
import welcomeSource from '../content/intro.md?raw';
import webullSource from '../content/chapters/11-webull-openapi-setup.md?raw';
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

const sources={welcome:welcomeSource,'chapter-11':webullSource};
const pages=config.pages.map(page=>({...page,navigationTitle:page.title,...(sources[page.id]?parsePage(sources[page.id]):{})}));
const publishedPages=pages.filter(page=>isPublishedPage(page.id));
const noop=()=>{};
const imageDimensions={...Object.fromEntries(webullImages.images.map(image=>[image.file,image.size])),[webullQuote.file]:webullQuote.size};

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
    const frame=requestAnimationFrame(()=>{
      if(route.section)document.getElementById(route.section)?.scrollIntoView();
      else window.scrollTo(0,0);
    });
    return()=>cancelAnimationFrame(frame);
  },[archived,page.title,route,welcome]);
  if(archived)return null;
  if(welcome)return <BookShell page={page} pages={publishedPages} route={route} menuOpen={menuOpen} setMenuOpen={setMenuOpen}><WelcomeAtlas page={page} imageDimensions={imageDimensions}/></BookShell>;
  const widgets={quiz:<Quiz key={page.id} questions={webullQuestions} onComplete={noop} onReset={noop}/>};
  // Retain the canonical Markdown; only the former introductory illustration
  // is replaced in this presentation by the shared Deltaris workshop artwork.
  const lessonIntro=page.intro.split('\n').filter(line=>!line.trim().startsWith('![')||!line.includes(']('+webullQuote.file+')')).join('\n').trim();
  return <BookShell page={page} pages={publishedPages} route={route} menuOpen={menuOpen} setMenuOpen={setMenuOpen}>
        <article className="lesson-article field-guide-article">
          <header className="field-guide-cover" id="page-top">
            <figure className="field-guide-art">
              <img src={assetUrl('images/deltaris-workshop-v2.png')} alt="โรงงานริมทะเลแห่ง Deltaris ช่างฝีมือกำลังประกอบโกเลมทองเหลือง ภาพประกอบโลก Quantara" width="1536" height="1024" fetchPriority="high"/>
              <figcaption>DELTARIS WORKSHOP</figcaption>
            </figure>
            <div className="field-guide-cover-copy">
              <div className="field-guide-cover-meta">Python / Webull OpenAPI</div>
              <h1>{page.title}</h1>
              <div className="chapter-lead" lang="th"><BookMarkdown source={lessonIntro} pageId={page.id} imageDimensions={imageDimensions}/></div>
              <nav className="field-guide-actions" aria-label="Start or practice"><a href={pageHref(page.id,'before-start')}>Start with the checklist <span aria-hidden="true">↓</span></a><a href={pageHref(page.id,'practice')}>Notebook & files <span aria-hidden="true">↗</span></a></nav>
            </div>
          </header>
          <aside className="field-guide-lore" aria-labelledby="gem-story-title" lang="th">
            <h2 id="gem-story-title">เรื่องเล่าจาก Quantara: เสียงจากอัญมณีสีน้ำเงิน</h2>
            <p>ช่างแห่ง Deltaris หมุนสลักที่อกหุ่นกล อัญมณีสีน้ำเงินสว่างขึ้น ก่อนส่งเสียงของเขาไปยังหอกลางเมือง “ได้ยินหรือไม่?” เขาถาม เสียงตอบดังกลับมาทันที “ได้ยิน ตั้งแต่เจ้าบ่นว่าประแจหายเมื่อเช้าแล้ว”</p>
            <p>หุ่นกลก้มมองอัญมณีของตัวเอง แล้วกระซิบว่า “ถ้าอย่างนั้น ช่วยแจ้งหอกลางด้วยว่าข้าขอพัก” ช่างยื่นมือจะปิดสัญญาณ แต่ช้าไป เสียงหัวเราะจากหอส่งกลับมาถึงโรงงาน ตามด้วยคำถามว่า “หุ่นขอพัก หรือคนถือประแจ?”</p>
          </aside>
          <div className="field-guide-reading">
            {page.sections.map(section=><section className="lesson-section" key={section.id}><div className="section-heading"><span className="field-guide-section-number" aria-hidden="true">{section.number}</span><h2 id={section.id}>{section.label}</h2></div><BookMarkdown source={section.body} pageId={page.id} widgets={widgets} imageDimensions={imageDimensions}/></section>)}
          </div>
          <footer className="page-footer"><a href={pageHref('welcome')}>← Back to Quantara</a><span>QUANTARA / DELTARIS</span><a href={pageHref(page.id,'page-top')}>Back to top ↑</a></footer>
        </article>
  </BookShell>;
}
