import React,{useEffect,useMemo,useRef,useState} from 'react';
import {MotionConfig} from 'motion/react';
import {IconBook2,IconSearch,IconChevronRight,IconMenu2,IconX,IconMoon,IconSun,IconDownload,IconArrowUpRight,IconCode,IconArrowRight,IconPrinter,IconSchool,IconCheck} from '@tabler/icons-react';
import config from '../content/book.json';
import {parsePage,assetUrl} from './lib/book.js';
import {pageHref,readRoute} from './lib/navigation.js';
import {BacktestLab,DrawdownLab,ExecutionLab} from './components/CourseLabs.jsx';
import BookMarkdown from './components/BookMarkdown.jsx';
import {Lab,Quiz,ApiExample,SmaExample} from './components/LessonWidgets.jsx';

const files=import.meta.glob('../content/**/*.md',{query:'?raw',import:'default',eager:true});
const pages=config.pages.map(page=>({...page,...parsePage(files['../content/'+page.file]||'')}));
const quizzes=import.meta.glob('../content/quizzes/*.json',{eager:true,import:'default'});
const load=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback;}catch{return fallback;}};
const save=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));}catch{}};
const configuredHref=href=>{if(href?.startsWith('#/')){const [page,section]=href.slice(2).split('/');return pageHref(page,section);}return assetUrl(href||'');};

function Downloads({page}){return <div className="download-grid">
  <a href={assetUrl('downloads/robo-trade-'+page.number+'.ipynb')} download><IconCode size={24}/><div><strong>Notebook · บทที่ {page.number}</strong><span>คำอธิบาย โค้ด และผลการรัน</span></div><IconDownload size={20}/></a>
  <a href={assetUrl('downloads/content/'+page.file)} download><IconDownload size={24}/><div><strong>Markdown · บทที่ {page.number}</strong><span>ดาวน์โหลดต้นฉบับเพื่อแก้ไข</span></div><IconArrowRight size={20}/></a>
</div>;}
function ChapterCard(){return <div className="curriculum-list">{pages.filter(p=>p.kind==='lesson').map((chapter,i,all)=><React.Fragment key={chapter.id}>
  {(i===0||chapter.part!==all[i-1].part)&&<h3 className="curriculum-part">{chapter.part}</h3>}
  <a className="curriculum-row" href={pageHref(chapter.id)}><span className="welcome-chapter-number">{chapter.number}</span><div><h3>{chapter.title}</h3><p>{chapter.outcome}</p><span>{chapter.duration} นาที · Notebook + แบบทบทวน</span></div><IconArrowRight size={20}/></a>
</React.Fragment>)}</div>;}

export default function App(){
  const [route,setRoute]=useState(()=>readRoute(pages));
  const page=pages.find(p=>p.id===route.page)||pages[0];
  const isWelcome=page.kind==='welcome';
  const [theme,setTheme]=useState(()=>load('rt-theme-v2',config.defaultTheme||'light')==='dark'?'dark':'light');
  const [mobile,setMobile]=useState(false),[search,setSearch]=useState(false),[query,setQuery]=useState('');
  const [active,setActive]=useState('');
  const [scores,setScores]=useState(()=>load('rt-scores',{}));
  const pageIndex=pages.findIndex(p=>p.id===page.id);
  const nextPage=pages[pageIndex+1];
  const previous=pages[pageIndex-1];
  const notebook='downloads/robo-trade-'+(page.number||'01')+'.ipynb';
  const dialog=useRef(null),searchInput=useRef(null),menuButton=useRef(null),searchFromMobile=useRef(false),previousPage=useRef(page.id);
  const closeNavigation=()=>{setMobile(false);setSearch(false);setQuery('');};
  useEffect(()=>{const change=()=>{setRoute(readRoute(pages));closeNavigation();};window.addEventListener('hashchange',change);window.addEventListener('popstate',change);return()=>{window.removeEventListener('hashchange',change);window.removeEventListener('popstate',change);};},[]);
  useEffect(()=>{document.documentElement.dataset.theme=theme;save('rt-theme-v2',theme);},[theme]);
  useEffect(()=>{const repeat=e=>{if(e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;const anchor=e.target.closest?.('a[href]');if(!anchor)return;const url=new URL(anchor.href,location.href);if(url.href!==location.href)return;e.preventDefault();const current=readRoute(pages);const behavior=window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth';if(current.section)document.getElementById(current.section)?.scrollIntoView({behavior});else window.scrollTo({top:0,behavior});};document.addEventListener('click',repeat);return()=>document.removeEventListener('click',repeat);},[]);

  useEffect(()=>{
    document.title=(isWelcome?page.title:'บทที่ '+page.number+' · '+page.title)+' | '+config.title;
    const id=requestAnimationFrame(()=>{
      if(previousPage.current!==page.id)document.getElementById('main-content')?.focus({preventScroll:true});
      if(!route.section)window.scrollTo({top:0,behavior:'instant'});
      else document.getElementById(route.section)?.scrollIntoView({behavior:previousPage.current===page.id&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches?'smooth':'instant'});
      previousPage.current=page.id;
    });return()=>cancelAnimationFrame(id);
  },[page.id,route.section]);
  useEffect(()=>{
    const update=()=>{const next=page.sections.filter(s=>(document.getElementById(s.id)?.getBoundingClientRect().top??Infinity)<180).at(-1);setActive(next?.id||'');};
    window.addEventListener('scroll',update,{passive:true});window.addEventListener('resize',update);update();return()=>{window.removeEventListener('scroll',update);window.removeEventListener('resize',update);};
  },[page.id]);
  useEffect(()=>{const key=e=>{if((e.metaKey||e.ctrlKey)&&e.key==='k'){e.preventDefault();if(mobile){searchFromMobile.current=true;setMobile(false);}setSearch(s=>!s);}if(e.key==='Escape'){setSearch(false);setMobile(false);if(mobile)menuButton.current?.focus();}};window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key);},[mobile]);
  useEffect(()=>{if(search){dialog.current?.showModal();searchInput.current?.focus();}else{dialog.current?.close();if(searchFromMobile.current){menuButton.current?.focus();searchFromMobile.current=false;}}},[search]);
  const results=useMemo(()=>pages.flatMap(p=>[{page:p.id,id:'',number:p.kind==='welcome'?'00':p.number,label:p.title,context:p.label,text:p.intro},...p.sections.map(s=>({...s,page:p.id,context:p.label,text:s.body}))]).filter(s=>(query.trim()||!s.id)&&(s.label+' '+s.context+' '+s.text).toLowerCase().includes(query.toLowerCase().trim())),[query]);
  const widgets={
    'chapter-card':<ChapterCard/>,
    'backtest-lab':<BacktestLab/>,
    'drawdown-lab':<DrawdownLab/>,
    'execution-lab':<ExecutionLab/>,
    'api-example':<ApiExample/>,
    'sma-example':<SmaExample/>,
    'sma-formula':<div className="formula" aria-label="SMA n ณ เวลา t เท่ากับผลรวมของราคาปิดล่าสุด n แท่ง หารด้วย n"><span>SMA<sub>n,t</sub> = </span><span className="fraction"><span>C<sub>t</sub> + C<sub>t−1</sub> + … + C<sub>t−n+1</sub></span><span>n</span></span></div>,
    'bar-question':<details className="reader-details"><summary>เปิดคำอธิบาย<IconChevronRight size={17}/></summary><p>ได้ เพราะราคาที่ใช้แทน close ยังเปลี่ยนอยู่ สัญญาณที่เห็นระหว่างแท่งอาจหายไปเมื่อแท่งปิด จึงต้องกำหนดให้ชัดว่าจะประเมินเมื่อใด</p></details>,
    lab:<Lab/>,
    quiz:<Quiz key={page.id} questions={quizzes['../content/quizzes/'+page.id+'.json']||[]} onComplete={score=>{const next={...scores,[page.id]:score};setScores(next);save('rt-scores',next);}} onReset={()=>{const next={...scores};delete next[page.id];setScores(next);save('rt-scores',next);}}/>,
    downloads:<Downloads page={page}/>,
  };
  return <MotionConfig reducedMotion="user">
    <a className="skip-link" href="#main-content" onClick={e=>{e.preventDefault();document.getElementById('main-content')?.focus();}}>ข้ามไปเนื้อหา</a>
    <header className="book-mobile-header"><a href={pageHref('welcome')} onClick={closeNavigation}>{config.title}</a><button ref={menuButton} aria-label={mobile?'ปิดสารบัญบทเรียน':'เปิดสารบัญบทเรียน'} aria-expanded={mobile} aria-controls="book-sidebar" onClick={()=>setMobile(v=>!v)}>{mobile?<IconX size={20}/>:<IconMenu2 size={20}/>}สารบัญ</button></header>
    <div className={'book-layout '+(mobile?'menu-open':'')}>
    <aside id="book-sidebar" className="book-sidebar" aria-label="สารบัญหนังสือ">
      {pages[0].heroImage&&<a className="cover-link" href={pageHref('welcome')} onClick={closeNavigation} aria-label="กลับหน้า Welcome"><img className="book-cover" src={assetUrl(pages[0].heroImage)} alt={pages[0].heroAlt} width="1942" height="809"/></a>}
      <a className="book-name" href={pageHref('welcome')} onClick={closeNavigation}>{config.title}<span>{config.subtitle}</span></a>
      <button className="search-trigger" onClick={()=>{searchFromMobile.current=mobile;setMobile(false);setSearch(true);}}><IconSearch size={19}/><span>ค้นหาในหนังสือ</span><kbd>⌘ K</kbd></button>
      <nav className="book-pages" onClick={closeNavigation}>{pages.map(p=><a key={p.id} className={'book-link '+(p.id===page.id?'current':'')} href={pageHref(p.id)} aria-current={p.id===page.id?'page':undefined}><span>{p.label}</span>{scores[p.id]!==undefined&&<IconCheck size={15} aria-label="ทบทวนแล้ว"/>}</a>)}</nav>
      {!isWelcome&&<details key={page.id} className="sidebar-local-toc" open><summary>ในหน้านี้</summary><nav className="chapter-sections" aria-label="หัวข้อในหน้านี้" onClick={closeNavigation}>{page.sections.map(s=><a key={s.id} href={pageHref(page.id,s.id)} aria-current={active===s.id?'location':undefined}>{s.label}</a>)}</nav></details>}
      <div className="book-sidebar-footer">
        <a href={assetUrl(isWelcome?'downloads/robo-trade-complete-materials.zip':notebook)} download><IconDownload size={16}/>{isWelcome?'ดาวน์โหลด Notebook ทุกบท':'ดาวน์โหลด Notebook'}</a>
        <a href={assetUrl('downloads/content/'+page.file)} download><IconCode size={16}/>ไฟล์ Markdown หน้านี้</a>
        <a href={assetUrl('downloads/EDITING.md')} download>คู่มือแก้ไขหนังสือ</a>
        <a href={config.apiDocs} target="_blank" rel="noreferrer">Webull API Docs <IconArrowUpRight size={14}/></a>
        <button aria-label={theme==='dark'?'เปลี่ยนเป็นโหมดสว่าง':'เปลี่ยนเป็นโหมดมืด'} onClick={()=>setTheme(t=>t==='dark'?'light':'dark')}>{theme==='dark'?<IconSun size={16}/>:<IconMoon size={16}/>} {theme==='dark'?'พื้นหลังสว่าง':'พื้นหลังมืด'}</button>
      </div>
    </aside>
    <main id="main-content" className={'book-main '+(isWelcome?'welcome-main':'')} tabIndex={-1}>
      <div className="page-topline"><span>{config.title}</span><button onClick={()=>window.print()}><IconPrinter size={15}/>พิมพ์หน้านี้</button></div>
      <article key={page.id} className={isWelcome?'welcome-article':'lesson-article'}>
        {page.heroImage&&<figure className="welcome-art"><img src={assetUrl(page.heroImage)} alt={page.heroAlt||''} width="1942" height="809" fetchPriority="high"/></figure>}
        <section className={'chapter-hero '+(isWelcome?'welcome-hero':'')} id="page-top">
          <h1>{page.title}</h1>
          <div className="chapter-lead"><BookMarkdown source={page.intro} pageId={page.id}/></div>
          <div className="chapter-meta">{page.meta?.map((m,i)=><span key={m}>{i===0?<IconSchool size={17}/>:i===1?<IconCode size={17}/>:<IconBook2 size={17}/>} {m}</span>)}</div>
          <div className="hero-actions">{page.primaryHref&&<a href={page.primaryHref==='#/'+page.id?pageHref(page.id,page.sections[0]?.id):configuredHref(page.primaryHref)}>{page.primaryLabel} <IconArrowRight size={17}/></a>}{page.secondaryHref&&<a href={configuredHref(page.secondaryHref)} download={page.secondaryHref?.endsWith('.ipynb')||undefined}>{page.secondaryLabel}</a>}</div>
        </section>
        {page.sections.map(s=><section className="lesson-section" key={s.id}><div className="section-heading"><h2 id={s.id}>{s.label}<a href={pageHref(page.id,s.id)} aria-label={'ลิงก์ไปยัง '+s.label}>#</a></h2></div><BookMarkdown source={s.body} pageId={page.id} widgets={widgets}/></section>)}
        <nav className="chapter-pagination" aria-label="เปลี่ยนบทเรียน">
          {previous&&<a href={pageHref(previous.id)}><small>หน้าก่อนหน้า</small><strong>← {previous.label}</strong></a>}
          {nextPage?<a className="next-chapter" href={pageHref(nextPage.id)}><small>อ่านต่อ</small><strong>{nextPage.label} →</strong></a>:<a className="next-chapter" href={pageHref('welcome','start')}><small>ครบทั้งเล่มแล้ว</small><strong>กลับสารบัญหนังสือ →</strong></a>}
        </nav>

      </article>
      <footer className="page-footer"><span>{config.title}</span><a href={assetUrl('THIRD_PARTY_NOTICES.txt')} target="_blank" rel="noreferrer">เครดิตและสิทธิ์การใช้งาน</a><button onClick={()=>window.scrollTo({top:0,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})}>กลับด้านบน ↑</button></footer>
    </main></div>
    <dialog ref={dialog} className="search-dialog" aria-label="ค้นหาในหนังสือ" onCancel={()=>setSearch(false)} onClick={e=>{if(e.target===dialog.current)setSearch(false);}}><div className="search-dialog-head"><IconSearch size={21}/><input ref={searchInput} placeholder="ค้นหา เช่น SMA, API, เวลา..." value={query} onChange={e=>setQuery(e.target.value)} aria-label="คำค้นหาในหนังสือ"/><button className="icon-btn" aria-label="ปิดการค้นหา" onClick={()=>setSearch(false)}><IconX size={20}/></button></div><div className="search-results">{results.length?results.map(s=><a href={pageHref(s.page,s.id)} onClick={closeNavigation} key={s.page+'/'+s.id}><span>{s.number}</span><div><strong>{s.label}</strong><small>{s.context}</small></div><IconArrowRight size={17}/></a>):<p>ไม่พบหัวข้อที่ตรงกับ “{query}” ลองค้นด้วยคำว่า SMA หรือ API</p>}</div><div className="search-dialog-foot">ค้นหาจากเนื้อหาในหนังสือ <kbd>ESC เพื่อปิด</kbd></div></dialog>
  </MotionConfig>;
}
