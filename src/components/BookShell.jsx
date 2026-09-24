import React,{useEffect,useState} from 'react';
import {assetUrl} from '../lib/book.js';
import {pageHref} from '../lib/navigation.js';

export default function BookShell({page, pages, route, menuOpen, setMenuOpen, children}) {
  const welcome = page.kind === 'welcome';
  const [sidebarCollapsed,setSidebarCollapsed]=useState(false);
  const chapterNumber=id=>pages.filter(item=>item.kind!=='welcome').findIndex(item=>item.id===id)+1;
  useEffect(()=>{
    if(!menuOpen)return;
    const mobile=window.matchMedia('(max-width:800px)');
    const closeOnDesktop=()=>{if(!mobile.matches)setMenuOpen(false);};
    closeOnDesktop();
    document.querySelector('#book-navigation a[aria-current=page]')?.focus();
    mobile.addEventListener('change',closeOnDesktop);
    return()=>mobile.removeEventListener('change',closeOnDesktop);
  },[menuOpen,setMenuOpen]);
  const sections = welcome
    ? [{id:'deltaris-workshop',label:'Deltaris workshop'}, {id:'quantara-map',label:'Quantara'}]
    : page.sections;
  const closeMenu = () => setMenuOpen(false);
  const onEscape = event => {
    if(menuOpen && event.key === 'Tab'){
      const controls=[document.getElementById('contents-toggle'),...document.querySelectorAll('#book-navigation a, #book-navigation summary')].filter(element=>element?.getClientRects().length);
      const index=controls.indexOf(document.activeElement);
      if(event.shiftKey && index<=0){event.preventDefault();controls.at(-1)?.focus();}
      else if(!event.shiftKey && index===controls.length-1){event.preventDefault();controls[0]?.focus();}
    }
    if (event.key === 'Escape' && menuOpen) {
      closeMenu();
      document.getElementById('contents-toggle')?.focus();
    }
  };
  const skipToMain = event => {
    event.preventDefault();
    closeMenu();
    const main = document.getElementById('main-content');
    main?.focus({preventScroll:true});
    main?.scrollIntoView();
  };
  return <div className="reading-site" onKeyDown={onEscape}>
    <a className="skip-link" href="#main-content" onClick={skipToMain}>Skip to content</a>
    <header className="reader-mobile-header">
      <a href={pageHref('welcome')} onClick={closeMenu}>Robo Trade Notes</a>
      <button id="contents-toggle" aria-expanded={menuOpen} aria-controls="book-navigation" onClick={()=>setMenuOpen(open=>!open)}>{menuOpen?'Close contents':'Contents'}</button>
    </header>
    <div className={'reader-layout'+(menuOpen?' menu-open':'')+(sidebarCollapsed?' sidebar-collapsed':'')}>
      <aside id="book-navigation" className="book-sidebar" aria-label="Book navigation">
        <a className="reader-brand" href={pageHref('welcome')} onClick={closeMenu}>
          <img src={assetUrl('images/quantcorner-mark-light.svg')} width="44" height="44" alt="QuantCorner"/>
          <span>Robo Trade Notes</span>
        </a>
        <div className="reader-contents-title">Contents</div>
        <nav className="book-pages" aria-label="Chapters">
          {pages.map(item=><a key={item.id} className={'book-link'+(item.id===page.id?' current':'')} href={pageHref(item.id)} aria-current={item.id===page.id?'page':undefined} onClick={closeMenu}>
            {item.kind!=='welcome'&&<span className="reader-chapter-number">{chapterNumber(item.id)}</span>}
            <span>{item.navigationTitle || item.title}</span>
          </a>)}
        </nav>
        {sections.length>0&&<details key={page.id} className="sidebar-local-toc" open>
          <summary>On this page</summary>
          <nav className="chapter-sections" aria-label="On this page">
            {sections.map(section=><a key={section.id} href={pageHref(page.id,section.id)} aria-current={route.section===section.id?'location':undefined} onClick={closeMenu}>{section.label}</a>)}
          </nav>
        </details>}
        <div className="book-sidebar-footer">
          {!welcome&&page.sections.some(section=>section.id==='practice')&&<a href={pageHref(page.id,'practice')} onClick={closeMenu}>Notebook & files <span aria-hidden="true">↓</span></a>}
          <a href="https://www.quant-corner.com/skill-tree">Skill Tree <span aria-hidden="true">↗</span></a>
          <a href="https://www.quant-corner.com/">QuantCorner <span aria-hidden="true">↗</span></a>
        </div>
      </aside>
      <main inert={menuOpen?true:undefined} id="main-content" className={'book-main reader-main'+(welcome?' reader-welcome':' reader-chapter')} tabIndex="-1">
        <div className="reader-page-label"><button className="reader-desktop-toggle" aria-expanded={!sidebarCollapsed} aria-controls="book-navigation" onClick={()=>setSidebarCollapsed(value=>!value)}>{sidebarCollapsed?'Show contents':'Hide contents'}</button><span>{welcome?'Welcome':`Chapter ${chapterNumber(page.id)}`}</span></div>
        {children}
      </main>
    </div>
  </div>;
}
