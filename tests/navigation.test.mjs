import test from 'node:test';
import assert from 'node:assert/strict';
import {pageHref, readRoute} from '../src/lib/navigation.js';

const pages = [
  {id:'welcome',sections:[{id:'start'}]},
  {id:'chapter-01',sections:[{id:'lab'},{id:'quiz'}]},
  {id:'chapter-05',sections:[{id:'drawdown'},{id:'quiz'}]},
];

test('development links retain existing hash navigation', () => {
  assert.equal(pageHref('welcome', '', {standalone:false}), '#/welcome');
  assert.equal(pageHref('chapter-05', 'drawdown', {standalone:false}), '#/chapter-05/drawdown');
});

test('standalone links are sibling HTML files with native section fragments', () => {
  assert.equal(pageHref('welcome', '', {standalone:true}), 'index.html');
  assert.equal(pageHref('welcome', 'start', {standalone:true}), 'index.html#start');
  assert.equal(pageHref('chapter-05', 'drawdown', {standalone:true}), 'chapter-05.html#drawdown');
  assert.throws(() => pageHref('../outside', '', {standalone:true}));
});

test('native file URLs select the filename page, including a local folder with spaces', () => {
  const pathname='/Users/learner/Desktop/Robo%20Trade/chapter-05.html';
  assert.deepEqual(readRoute(pages,{pathname,hash:'#drawdown'}),{page:'chapter-05',section:'drawdown'});
  assert.deepEqual(readRoute(pages,{pathname,hash:'#quiz'}),{page:'chapter-05',section:'quiz'});
  assert.deepEqual(readRoute(pages,{pathname,hash:''}),{page:'chapter-05',section:''});
  assert.deepEqual(readRoute(pages,{pathname:'/book/index.html',hash:'#start'}),{page:'welcome',section:'start'});
});

test('legacy page routes retain precedence on any filename', () => {
  assert.deepEqual(readRoute(pages,{pathname:'/book/index.html',hash:'#/chapter-05/drawdown'}),{page:'chapter-05',section:'drawdown'});
  assert.deepEqual(readRoute(pages,{pathname:'/book/chapter-05.html',hash:'#/chapter-01/lab'}),{page:'chapter-01',section:'lab'});
  assert.deepEqual(readRoute(pages,{pathname:'/',hash:'#quiz'}),{page:'chapter-01',section:'quiz'});
  assert.deepEqual(readRoute(pages,{pathname:'/',hash:'#chapter-top'}),{page:'chapter-01',section:''});
});

test('unknown or absent routes fall back predictably without losing native fragments', () => {
  assert.deepEqual(readRoute(pages,{pathname:'/',hash:''}),{page:'welcome',section:''});
  assert.deepEqual(readRoute(pages,{pathname:'/book/no-such-page.html',hash:''}),{page:'welcome',section:''});
  assert.deepEqual(readRoute(pages,{pathname:'/book/chapter-05.html',hash:'#unknown-heading'}),{page:'chapter-05',section:'unknown-heading'});
  assert.deepEqual(readRoute(pages,{pathname:'/book/chapter-05.html',hash:'#chapter-top'}),{page:'chapter-05',section:''});
  assert.deepEqual(readRoute(pages,{pathname:'/',hash:'#/not-found'}),{page:'welcome',section:''});
  assert.throws(() => readRoute([]));
});

test('encoded fragments round-trip and malformed percent escapes do not throw', () => {
  const href=pageHref('chapter-05','section space',{standalone:true});
  assert.equal(href,'chapter-05.html#section%20space');
  assert.deepEqual(readRoute(pages,{pathname:'/chapter-05.html',hash:'#section%20space'}),{page:'chapter-05',section:'section space'});
  assert.deepEqual(readRoute(pages,{pathname:'/chapter-05.html',hash:'#bad%escape'}),{page:'chapter-05',section:'bad%escape'});
});
