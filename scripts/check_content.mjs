import {readFileSync,existsSync} from 'node:fs';
import assert from 'node:assert/strict';
import katex from 'katex';
import {parsePage,splitWidgets} from '../src/lib/book.js';
const root=new URL('../',import.meta.url);
const book=JSON.parse(readFileSync(new URL('content/book.json',root),'utf8'));
const known=new Set(['chapter-card','api-example','sma-example','sma-formula','bar-question','lab','quiz','downloads','backtest-lab','drawdown-lab','execution-lab']);
assert(book.pages.length>0,'At least one book page is required');
assert.equal(new Set(book.pages.map(p=>p.id)).size,book.pages.length,'Page IDs must be unique');
const pages=book.pages.map(page=>{const raw=readFileSync(new URL('content/'+page.file,root),'utf8');return {...page,raw,...parsePage(raw)};});
let mathCount=0,questionCount=0;
for(const page of pages){
  assert.match(page.id,/^[a-z0-9-]+$/,'Use URL-safe page IDs');
  assert(page.sections.length>0,page.file+': add at least one ## section');
  const chunks=splitWidgets(page.raw);
  for(const chunk of chunks)if(chunk.widget)assert(known.has(chunk.widget),page.file+': unknown block '+chunk.widget);
  for(const match of page.raw.matchAll(/\]\(#([a-z0-9-]+)\)/g))assert(page.sections.some(s=>s.id===match[1]),page.file+': missing section '+match[1]);
  for(const match of page.raw.matchAll(/\]\(#\/([a-z0-9-]+)(?:\/([a-z0-9-]+))?\)/g)){
    const target=pages.find(p=>p.id===match[1]);assert(target,page.file+': missing page '+match[1]);if(match[2])assert(target.sections.some(s=>s.id===match[2]),page.file+': missing target section '+match[2]);
  }
  for(const match of page.raw.matchAll(/\]\((downloads\/[^)]+)\)/g))if(!match[1].endsWith('robo-trade-complete-materials.zip'))assert(existsSync(new URL('public/'+match[1],root)),page.file+': missing local download '+match[1]);
  const prose=page.raw.replace(/^```[^\n]*\n[\s\S]*?^```\s*$/gm,'');
  for(const match of prose.matchAll(/\$\$([\s\S]*?)\$\$|(?<![\\$])\$([^$\n]+)\$(?!\$)/g)){
    katex.renderToString(match[1]??match[2],{throwOnError:true,strict:'ignore',trust:false});mathCount++;
  }
  if(page.heroImage){assert(existsSync(new URL('public/'+page.heroImage,root)),'Missing hero image');assert(page.heroAlt,'Add descriptive heroAlt');}
  if(page.kind==='lesson'){
    const quiz=JSON.parse(readFileSync(new URL('content/quizzes/'+page.id+'.json',root),'utf8'));
    assert(quiz.length>=3,page.id+': at least three questions');
    for(const q of quiz){assert(q.title&&q.explanation);assert(Array.isArray(q.options)&&q.options.length>1);assert(Number.isInteger(q.answer)&&q.answer>=0&&q.answer<q.options.length);questionCount++;}
    // Why Robo Trade ends with a summary; its existing supplementary files stay validated.
    const expectedQuizCount=page.id==='chapter-12'?0:1;
    assert.equal(chunks.filter(c=>c.widget==='quiz').length,expectedQuizCount,page.id+': expected quiz count');
    const notebook=JSON.parse(readFileSync(new URL('public/downloads/robo-trade-'+page.number+'.ipynb',root),'utf8'));
    const code=notebook.cells.filter(c=>c.cell_type==='code');assert(code.length>=5,'Notebook needs worked examples');
    for(const cell of code){assert(Number.isInteger(cell.execution_count),page.id+': notebook has unexecuted cells');assert(!cell.outputs.some(o=>o.output_type==='error'),page.id+': notebook has errors');}
    assert(existsSync(new URL('public/downloads/lesson_'+page.number+'.py',root)),page.id+': missing Python example');
  }
  console.log('PASS:',page.file,'—',page.sections.length,'sections');
}
console.log(`PASS: ${pages.length} pages, ${questionCount} questions, ${mathCount} math expressions; chapter links, local assets and executed notebook structure`);
