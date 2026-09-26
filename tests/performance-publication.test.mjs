import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {publishedPageIds} from '../src/lib/publishing.js';
import {pageHref,readRoute} from '../src/lib/navigation.js';
import {parsePage} from '../src/lib/book.js';

test('performance lesson follows Introduction of Backtest and keeps its direct HTML route',()=>{
  assert.equal(publishedPageIds.indexOf('chapter-14'),publishedPageIds.indexOf('chapter-13')+1);
  for(const standalone of [false,true])assert.equal(pageHref('chapter-14','benchmark',{standalone}),'chapter-14.html#benchmark');
  const parsed=parsePage(readFileSync(new URL('../content/chapters/14-backtest-performance-evaluation.md',import.meta.url),'utf8'));
  const pages=[{id:'welcome',sections:[]},{id:'chapter-14',...parsed}];
  assert.deepEqual(readRoute(pages,{pathname:'/robo-trade-notes/index.html',hash:'#/chapter-14/benchmark'}),{page:'chapter-14',section:'benchmark'});
  assert.ok(parsed.sections.some(x=>x.id==='benchmark'));
});
