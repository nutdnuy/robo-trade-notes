import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath,pathToFileURL} from 'node:url';

const dir=path.dirname(fileURLToPath(import.meta.url));
fs.mkdirSync(path.join(dir,'qa'),{recursive:true});
const localRequire=createRequire(import.meta.url);
let depRequire=localRequire;
try{depRequire.resolve('react-markdown');}catch{
  const dependencyRoot=process.env.ROBO_DEPENDENCIES || path.resolve(dir,'../..');
  depRequire=createRequire(path.join(dependencyRoot,'package.json'));
}
const React=depRequire('react');
const {renderToStaticMarkup}=depRequire('react-dom/server');
const getDefault=async name=>(await import(pathToFileURL(depRequire.resolve(name)).href)).default;
const [Markdown,gfm,math,katex]=await Promise.all(['react-markdown','remark-gfm','remark-math','rehype-katex'].map(getDefault));
const M=localRequire('./performance-metrics.js'),C=localRequire('./ema-charts.js'),V=localRequire('./ema-view.js');
const data=JSON.parse(fs.readFileSync(path.join(dir,'ema-data.json'),'utf8'));
const results=JSON.parse(fs.readFileSync(path.join(dir,'ema-results.json'),'utf8'));
const n=V.num;
const canonical=path.resolve(dir,'../../content/chapters/14-backtest-performance-evaluation.md');
const chapterPath=fs.existsSync(canonical)?canonical:path.join(dir,'chapter.md');
const read=file=>fs.readFileSync(file==='chapter.md'?chapterPath:path.join(dir,file),'utf8');
const esc=V.esc;
const widgets=localRequire('./ema-widgets.js')(results,data);
let md=read('chapter.md');
if(/\{\{/.test(md))throw new Error('Unresolved lesson placeholders');
const title=md.match(/^# (.+)$/m)[1];
const headings=[...md.matchAll(/^## (.+?) \{#([a-z0-9-]+)\}$/gm)].map(m=>({title:m[1],id:m[2]}));
const detailBlocks=[];
let openDetail=null;
md=md.split('\n').map(line=>{
 const match=line.match(/^::: details (.+)$/);
 if(match){
  if(openDetail!==null)throw new Error('Nested details are not supported');
  openDetail=detailBlocks.length;
  detailBlocks.push(match[1]);
  return `ROBO_DETAILS_OPEN_${openDetail}`;
 }
 if(line===':::'){
  if(openDetail===null)throw new Error('Unexpected details closing marker');
  const token=`ROBO_DETAILS_CLOSE_${openDetail}`;
  openDetail=null;
  return token;
 }
 return line;
}).join('\n');
if(openDetail!==null)throw new Error('Unclosed details block');
md=md.replace(/^# .+\n/,'').replace(/^## (.+?) \{#[a-z0-9-]+\}$/gm,'## $1').replace(/^::: ([a-z-]+)$/gm,(_,k)=>{if(!widgets[k])throw new Error('Unknown widget '+k);return 'ROBO_WIDGET_'+k.replaceAll('-','_').toUpperCase();});
let headingIndex=0;
let html=renderToStaticMarkup(React.createElement(Markdown,{remarkPlugins:[gfm,math],rehypePlugins:[[katex,{throwOnError:true}]],components:{h2:({children})=>React.createElement('h2',{id:headings[headingIndex++].id},children),table:({children})=>React.createElement('div',{className:'table-scroll',tabIndex:0,role:'region','aria-label':'ตารางเนื้อหา เลื่อนแนวนอนได้'},React.createElement('table',null,children))}},md));
for(const [key,markup]of Object.entries(widgets))html=html.replace(`<p>ROBO_WIDGET_${key.replaceAll('-','_').toUpperCase()}</p>`,markup);
if(html.includes('ROBO_WIDGET_'))throw new Error('Unrendered widget');
detailBlocks.forEach((label,i)=>{
 html=html.replace(`<p>ROBO_DETAILS_OPEN_${i}</p>`,`<details class="reading-details"><summary>${esc(label)}</summary><div class="detail-content">`).replace(`<p>ROBO_DETAILS_CLOSE_${i}</p>`,'</div></details>');
});
if(html.includes('ROBO_DETAILS_'))throw new Error('Unrendered details block');
for(const file of ['robo-trade-14.ipynb','lesson_14.py','trades.csv','equity-daily.csv','ema-bars.csv']){
 if(fs.existsSync(path.join(dir,file))){
  const mime=file.endsWith('.csv')?'text/csv':file.endsWith('.ipynb')?'application/x-ipynb+json':'text/x-python';
  html=html.replaceAll(`href="${file}" download`,`href="data:${mime};charset=utf-8;base64,${Buffer.from(read(file)).toString('base64')}" download="${file}"`);
 }
}
const split=html.indexOf('<h2'),intro=html.slice(0,split),body=html.slice(split);
let fontCss='';
for(const [family,slug,subset,weights]of [['Roboto','roboto','latin',[400,500,700]],['Noto Sans Thai','noto-sans-thai','thai',[400,500,600,700]]])for(const w of weights){const buf=fs.readFileSync(path.join(dir,`assets/fonts/${slug}-${subset}-${w}-normal.woff2`));fontCss+=`@font-face{font-family:'${family}';font-style:normal;font-weight:${w};font-display:swap;src:url(data:font/woff2;base64,${buf.toString('base64')}) format('woff2');}`;}
const katexCssPath=depRequire.resolve('katex/dist/katex.min.css');
let katexCss=fs.readFileSync(katexCssPath,'utf8').replace(/url\(([^)]+)\)/g,(_,u)=>{const clean=u.replace(/["']/g,'');const file=path.resolve(path.dirname(katexCssPath),clean);return `url(data:font/${path.extname(file).slice(1)};base64,${fs.readFileSync(file).toString('base64')})`;});
const logo=theme=>`data:image/svg+xml;base64,${fs.readFileSync(path.join(dir,`assets/quantcorner-mark-${theme}.svg`)).toString('base64')}`;
const download=(file,mime='text/plain')=>`data:${mime};charset=utf-8;base64,${Buffer.from(read(file)).toString('base64')}`;
const doc=`<!doctype html><html lang="th" data-theme="light"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><meta name="robots" content="noindex,nofollow"/><meta name="description" content="ฉบับตรวจส่วนตัว: การอ่าน Return, Risk และ Trading Metrics จากราคาจริง S&P 500 ย้อนหลัง 20 ปี"/><title>${esc(title)} | Robo Trade Notes · Review</title><style>${fontCss}\n${katexCss}\n${read('style.css')}</style></head><body><a class="skip" href="#main-content">ข้ามไปยังเนื้อหา</a><header class="mobile-header"><a href="#page-top">Robo Trade Notes</a><button id="mobile-menu" aria-expanded="false" aria-controls="book-navigation" type="button">สารบัญ</button></header><div class="book-layout"><aside class="book-sidebar" id="book-navigation" aria-label="สารบัญหนังสือ"><a class="brand" href="https://nutdnuy.github.io/robo-trade-notes/"><img class="logo-light" src="${logo('light')}" alt="QuantCorner" width="44" height="44"/><img class="logo-dark" src="${logo('dark')}" alt="QuantCorner" width="44" height="44"/>Robo Trade Notes</a><p class="nav-title">Contents</p><nav class="book-pages" aria-label="บทเรียน"><a class="book-link" href="https://nutdnuy.github.io/robo-trade-notes/">Welcome</a><a class="book-link" href="https://nutdnuy.github.io/robo-trade-notes/chapter-11.html"><b>1</b>เริ่มต้นใช้ Webull OpenAPI ทีละขั้น</a><a class="book-link" href="https://nutdnuy.github.io/robo-trade-notes/chapter-12.html"><b>2</b>Why Robo Trade</a><a class="book-link" href="https://nutdnuy.github.io/robo-trade-notes/chapter-13.html"><b>3</b>Introduction of Backtest</a><a class="book-link current" href="#page-top" aria-current="page"><b>4</b>Backtest Performance Evaluation</a></nav><details class="local-toc" open><summary>On this page</summary><nav aria-label="หัวข้อในบท">${headings.map(h=>`<a href="#${h.id}">${esc(h.title)}</a>`).join('')}</nav></details><div class="side-files"><a href="${download('chapter.md','text/markdown')}" download="14-backtest-performance-evaluation.md">ดาวน์โหลดต้นฉบับ Markdown</a><a href="${download('ema-data.json','application/json')}" download="ema-data.json">ดาวน์โหลดข้อมูล S&P 500</a><a href="${download('SOURCES.md','text/markdown')}" download="SOURCES.md">ขอบเขตแหล่งข้อมูล</a></div></aside><main class="book-main" id="main-content"><div class="topline"><button id="nav-toggle" aria-expanded="true" aria-controls="book-navigation" type="button">ซ่อนสารบัญ</button><span>Chapter 4</span><span class="status">ฉบับตรวจ 6 · ยังไม่เผยแพร่</span><button class="theme" id="theme-toggle" aria-pressed="false" type="button">โหมดมืด</button></div><header class="chapter-hero" id="page-top"><p class="eyebrow">Backtesting / Return / Risk / Trading Metrics</p><h1>${esc(title)}</h1><div class="lead">${intro}</div><nav class="hero-actions" aria-label="เริ่มอ่านและทดลอง"><a href="${html.includes('id="read-report"')?'#read-report':'#win-loss-size'}">เริ่มอ่านรายงาน ↓</a><a href="#python-report">ลงมือทำด้วย Python ↗</a></nav></header><noscript><p class="draft-note">เนื้อหา สูตร ตาราง และภาพฐานอ่านได้โดยไม่ใช้ JavaScript หากต้องการปรับตัวเลื่อนให้เปิด JavaScript</p></noscript><p class="print-note">ค่าของภาพเป็นสถานะที่แสดงขณะพิมพ์ เนื้อหาอ้างอิงค่าตั้งต้นของ Backtest S&P 500</p><article class="lesson">${body}</article><footer class="footer"><a href="https://nutdnuy.github.io/robo-trade-notes/chapter-13.html">← บทก่อนหน้า: Introduction of Backtest</a><span>Robo Trade Notes · ฉบับตรวจในเครื่อง</span><a href="#page-top">กลับด้านบน ↑</a></footer></main></div><script id="lesson-data" type="application/json">${JSON.stringify(data).replaceAll('<','\\u003c')}</script><script id="lesson-results" type="application/json">${JSON.stringify(results).replaceAll('<','\\u003c')}</script><script>${read('performance-metrics.js')}</script><script>${read('ema-charts.js')}</script><script>${read('ema-view.js')}</script><script>${read('ema-ui.js')}</script></body></html>`;
fs.writeFileSync(path.join(dir,'chapter-14-review.html'),doc);
const bars=V.normalize(data);
const exports={
 '01-signal-at-close-execute-next-open.svg':C.signal(bars,results.tradeLedger[1].entryDecisionBar),
 '02-frequent-wins-can-still-lose.svg':C.tradeBars(results.tradeLedger,2),
 '03-portfolio-growth-versus-buy-and-hold.svg':C.equity(results.dailyEquity,results.parameters.initialEquity,results.portfolioMetrics.periods),
 '04-drawdown-from-the-previous-peak.svg':C.equity(results.dailyEquity,results.parameters.initialEquity,results.portfolioMetrics.maxDrawdownTroughIndex,'drawdown'),
 '05-daily-returns-versus-minimum-target.svg':C.risk(results.portfolioMetrics.returns,0,results.dailyEquity.map(x=>x.date)),
 '06-net-trade-pnl-distribution.svg':C.tradeDistribution(results.tradeLedger,0),
 '07-drawdown-and-recovery-duration.svg':C.drawdownEpisode(results.dailyEquity,results.parameters.initialEquity,results.portfolioMetrics),
 '08-cumulative-return-versus-sp500.svg':C.equity(results.dailyEquity,results.parameters.initialEquity,results.portfolioMetrics.periods,'cumulative')
};
fs.mkdirSync(path.join(dir,'figures-ema'),{recursive:true});
for(const [name,svg]of Object.entries(exports))fs.writeFileSync(path.join(dir,'figures-ema',name),svg.replace('<style>','<style>'+fontCss));
fs.writeFileSync(path.join(dir,'qa/build-result.json'),JSON.stringify({status:'passed',revision:6,title,headings:headings.length,widgets:Object.keys(widgets),htmlBytes:Buffer.byteLength(doc),selfContainedReading:true,route:'no-image-generator',designSystem:'QuantCorner / QuantSeras with existing Robo Trade Notes reading layout'},null,2));
console.log(`Built chapter-14-review.html (${n(Buffer.byteLength(doc),0)} bytes), ${headings.length} sections, ${Object.keys(exports).length} EMA SVG figures`);
