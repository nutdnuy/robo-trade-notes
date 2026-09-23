import React,{useEffect,useState} from 'react';
import config from '../content/book.json';
import welcomeSource from '../content/intro.md?raw';
import webullSource from '../content/chapters/11-webull-openapi-setup.md?raw';
import webullQuestions from '../content/quizzes/chapter-11.json';
import webullImages from '../references/webull-openapi-setup-images.json';
import {parsePage,assetUrl} from './lib/book.js';
import {pageHref,readRoute} from './lib/navigation.js';
import {isPublishedPage} from './lib/publishing.js';
import BookMarkdown from './components/BookMarkdown.jsx';
import {Quiz} from './components/LessonWidgets.jsx';

const sources={welcome:welcomeSource,'chapter-11':webullSource};
const pages=config.pages.map(page=>({...page,...(sources[page.id]?parsePage(sources[page.id]):{})}));
const publishedPages=pages.filter(page=>isPublishedPage(page.id));
const noop=()=>{};
const imageDimensions=Object.fromEntries(webullImages.images.map(image=>[image.file,image.size]));

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
    document.title=archived?'Robo Trade Notes':page.title+' | Robo Trade Notes';
    if(archived)return;
    const frame=requestAnimationFrame(()=>{
      if(route.section)document.getElementById(route.section)?.scrollIntoView();
      else window.scrollTo(0,0);
    });
    return()=>cancelAnimationFrame(frame);
  },[archived,page.title,route]);
  if(archived)return null;
  const widgets={quiz:<Quiz key={page.id} questions={webullQuestions} onComplete={noop} onReset={noop}/>};
  return <>
    <header className="book-mobile-header">
      <a href={pageHref('welcome')}>{config.title}</a>
      <button aria-expanded={menuOpen} aria-controls="book-navigation" onClick={()=>setMenuOpen(open=>!open)}>{menuOpen?'ปิดเมนู':'เมนูบทเรียน'}</button>
    </header>
    <div className={'book-layout'+(menuOpen?' menu-open':'')} onKeyDown={event=>{if(event.key==='Escape')setMenuOpen(false);}}>
      <aside id="book-navigation" className="book-sidebar" aria-label="เมนูเว็บไซต์">
        <a className="book-name" href={pageHref('welcome')}>{config.title}<span>{config.subtitle}</span></a>
        <nav className="book-pages">{publishedPages.map(item=><a key={item.id} className={'book-link'+(item.id===page.id?' current':'')} href={pageHref(item.id)} aria-current={item.id===page.id?'page':undefined}>{item.title}</a>)}</nav>
        {!welcome&&<details className="sidebar-local-toc" open><summary>หัวข้อในบทนี้</summary><nav className="chapter-sections">{page.sections.map(section=><a key={section.id} href={pageHref(page.id,section.id)} aria-current={route.section===section.id?'location':undefined} onClick={()=>setMenuOpen(false)}>{section.label}</a>)}</nav></details>}
      </aside>
      <main id="main-content" className={'book-main'+(welcome?' welcome-main':'')}>
        <article className={welcome?'welcome-article':'lesson-article'}>
          {welcome&&<figure className="welcome-art"><img src={assetUrl(page.heroImage)} alt={page.heroAlt} width="1942" height="809"/></figure>}
          {!welcome&&<div className="page-topline"><span>คู่มือภาพ · Webull OpenAPI</span><a href={pageHref(page.id,'practice')}>Notebook และไฟล์ประกอบ ↓</a></div>}
          <section className={'chapter-hero'+(welcome?' welcome-hero':'')} id="page-top">
            <h1>{page.title}</h1>
            {welcome&&<nav className="welcome-setup-links" aria-label="เปิดบัญชีและเตรียม API Key"><a href="https://www.webull.co.th/k/QuantCorner" target="_blank" rel="noreferrer">เปิดบัญชี Webull ผ่าน QuantCorner →</a><a href={pageHref('chapter-11')}>คู่มือภาพเริ่มต้นใช้ OpenAPI</a></nav>}
            <div className="chapter-lead"><BookMarkdown source={page.intro} pageId={page.id}/></div>
          </section>
          {page.sections.map(section=><section className="lesson-section" key={section.id}><div className="section-heading"><h2 id={section.id}>{section.label}</h2></div><BookMarkdown source={section.body} pageId={page.id} widgets={widgets} imageDimensions={imageDimensions}/></section>)}
          {!welcome&&<footer className="page-footer"><a href={pageHref('welcome')}>← กลับหน้า Welcome</a><a href={pageHref(page.id,'page-top')}>กลับด้านบน ↑</a></footer>}
        </article>
      </main>
    </div>
  </>;
}
