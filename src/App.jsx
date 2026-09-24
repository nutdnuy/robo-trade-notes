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
import WelcomeAtlas,{AtlasHeader,skipToMain} from './components/WelcomeAtlas.jsx';
import './field-guide.css';

const sources={welcome:welcomeSource,'chapter-11':webullSource};
const pages=config.pages.map(page=>({...page,...(sources[page.id]?parsePage(sources[page.id]):{})}));
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
  if(welcome)return <WelcomeAtlas page={page} imageDimensions={imageDimensions}/>;
  const widgets={quiz:<Quiz key={page.id} questions={webullQuestions} onComplete={noop} onReset={noop}/>};
  // Retain the canonical Markdown; only the former introductory illustration
  // is replaced in this presentation by the shared Deltaris workshop artwork.
  const lessonIntro=page.intro.split('\n').filter(line=>!line.trim().startsWith('![')||!line.includes(']('+webullQuote.file+')')).join('\n').trim();
  return <div className="field-guide-page">
    <a className="skip-link" href="#main-content" onClick={skipToMain}>Skip to content</a>
    <AtlasHeader menuOpen={menuOpen} onMenuToggle={()=>setMenuOpen(open=>!open)}/>
    <div className={'book-layout atlas-lesson-layout field-guide-layout'+(menuOpen?' menu-open':'')} onKeyDown={event=>{if(event.key==='Escape'&&menuOpen){setMenuOpen(false);document.getElementById('contents-toggle')?.focus();}}}>
      <aside id="book-navigation" className="book-sidebar" aria-label="เมนูเว็บไซต์">
        <div className="field-guide-sidebar-title"><span>DELTARIS / QUANTARA</span><p>OpenAPI field manual</p><small>Algorithmic Trading Masters</small></div>
        <nav className="book-pages" aria-label="Explore Quantara">{publishedPages.map(item=><a key={item.id} className={'book-link'+(item.id===page.id?' current':'')} href={pageHref(item.id)} aria-current={item.id===page.id?'page':undefined}><span aria-hidden="true">{item.kind==='welcome'?'↖':'11'}</span>{item.kind==='welcome'?'Back to Quantara':'OpenAPI field guide'}</a>)}</nav>
        <details className="sidebar-local-toc" open><summary>Inside this manual <span lang="th">หัวข้อในบทนี้</span></summary><nav className="chapter-sections" aria-label="หัวข้อในคู่มือ">{page.sections.map(section=><a key={section.id} href={pageHref(page.id,section.id)} aria-current={route.section===section.id?'location':undefined} onClick={()=>setMenuOpen(false)}><span className="field-guide-nav-number" aria-hidden="true">{section.number}</span><span>{section.label}</span></a>)}</nav></details>
        <a className="field-guide-sidebar-download" href={pageHref(page.id,'practice')} onClick={()=>setMenuOpen(false)}>Practice files <span aria-hidden="true">↓</span><small>Notebook & Python files</small></a>
      </aside>
      <main id="main-content" tabIndex="-1" className="book-main field-guide-main">
        <article className="lesson-article field-guide-article">
          <header className="field-guide-cover" id="page-top">
            <figure className="field-guide-art">
              <img src={assetUrl('images/deltaris-workshop-v2.png')} alt="โรงงานริมทะเลแห่ง Deltaris ช่างฝีมือกำลังประกอบโกเลมทองเหลือง ภาพประกอบโลก Quantara" width="1536" height="1024" fetchPriority="high"/>
              <figcaption><span>THE DELTARIS WORKSHOP</span><strong>Deltaris field manual.</strong><small>KINGDOM OF QUANTARA</small></figcaption>
            </figure>
            <div className="field-guide-cover-copy">
              <div className="field-guide-cover-meta"><span>FIELD MANUAL <b>11</b></span><span>PYTHON / WEBULL OPENAPI</span></div>
              <h1>{page.title}</h1>
              <div className="chapter-lead" lang="th"><BookMarkdown source={lessonIntro} pageId={page.id} imageDimensions={imageDimensions}/></div>
              <nav className="field-guide-actions" aria-label="Start or practice"><a href={pageHref(page.id,'before-start')}>Start with the checklist <span aria-hidden="true">↓</span></a><a href={pageHref(page.id,'practice')}>Notebook & files <span aria-hidden="true">↗</span></a></nav>
            </div>
          </header>
          <div className="field-guide-reading">
            {page.sections.map(section=><section className="lesson-section" key={section.id}><div className="section-heading"><span className="field-guide-section-number" aria-hidden="true">{section.number}</span><h2 id={section.id}>{section.label}</h2></div><BookMarkdown source={section.body} pageId={page.id} widgets={widgets} imageDimensions={imageDimensions}/></section>)}
          </div>
          <footer className="page-footer"><a href={pageHref('welcome')}>← Back to Quantara</a><span>QUANTARA / DELTARIS</span><a href={pageHref(page.id,'page-top')}>Back to top ↑</a></footer>
        </article>
      </main>
    </div>
  </div>;
}
