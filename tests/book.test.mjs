import test from 'node:test';
import assert from 'node:assert/strict';
import {parsePage,parseRoute,splitWidgets} from '../src/lib/book.js';

test('Markdown code examples do not become headings or interactive blocks',()=>{
  const text='# Title\n\nIntro\n\n## First {#first}\n\n```python\n## Not a section\n::: lab\n```\n\n::: quiz\n';
  const page=parsePage(text);
  assert.equal(page.sections.length,1);
  assert.equal(page.sections[0].id,'first');
  assert.deepEqual(splitWidgets(page.sections[0].body).filter(p=>p.widget).map(p=>p.widget),['quiz']);
  assert.match(page.sections[0].body,/## Not a section/);
});

test('Welcome, chapter deep links and original lesson links route correctly',()=>{
  const pages=[{id:'welcome',sections:[{id:'about'}]},{id:'chapter-01',sections:[{id:'lab'}]}];
  assert.deepEqual(parseRoute('',pages),{page:'welcome',section:''});
  assert.deepEqual(parseRoute('#/chapter-01/lab',pages),{page:'chapter-01',section:'lab'});
  assert.deepEqual(parseRoute('#lab',pages),{page:'chapter-01',section:'lab'});
  assert.deepEqual(parseRoute('#chapter-top',pages),{page:'chapter-01',section:''});
});
