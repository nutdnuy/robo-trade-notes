import React,{useEffect,useState} from 'react';
import config from '../content/book.json';
import source from '../content/intro.md?raw';
import {parsePage,assetUrl} from './lib/book.js';
import {pageHref} from './lib/navigation.js';
import BookMarkdown from './components/BookMarkdown.jsx';
const page=parsePage(source);
const isArchivedRoute=()=>/^#\/chapter-/.test(location.hash)||/\/chapter-[^/]+\.html$/.test(location.pathname);
export default function App(){
  const [archived,setArchived]=useState(isArchivedRoute);
  useEffect(()=>{
    document.documentElement.dataset.theme='light';
    const update=()=>setArchived(isArchivedRoute());
    window.addEventListener('hashchange',update);
    return()=>window.removeEventListener('hashchange',update);
  },[]);
  useEffect(()=>{document.title=archived?'Robo Trade Notes':'Welcome | Robo Trade Notes';},[archived]);
  if(archived)return null;
  return <div className="book-layout">
    <aside className="book-sidebar" aria-label="เมนูเว็บไซต์">
      <a className="book-name" href={pageHref('welcome')}>{config.title}<span>{config.subtitle}</span></a>
      <nav className="book-pages"><a className="book-link current" href={pageHref('welcome')} aria-current="page">Welcome</a></nav>
    </aside>
    <main id="main-content" className="book-main welcome-main">
      <article className="welcome-article">
        <figure className="welcome-art"><img src={assetUrl(config.pages[0].heroImage)} alt={config.pages[0].heroAlt} width="1942" height="809"/></figure>
        <section className="chapter-hero welcome-hero" id="page-top">
          <h1>{page.title}</h1>
          <nav className="welcome-setup-links" aria-label="เปิดบัญชีและเตรียม API Key"><a href="https://www.webull.co.th/k/QuantCorner" target="_blank" rel="noreferrer">เปิดบัญชี Webull ผ่าน QuantCorner →</a><a href={pageHref('welcome','webull-start')}>วิธีขอ API Key</a></nav>
          <div className="chapter-lead"><BookMarkdown source={page.intro} pageId="welcome"/></div>
        </section>
        {page.sections.map(section=><section className="lesson-section" key={section.id}><div className="section-heading"><h2 id={section.id}>{section.label}</h2></div><BookMarkdown source={section.body} pageId="welcome"/></section>)}
      </article>
    </main>
  </div>;
}
