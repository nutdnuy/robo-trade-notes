import test from 'node:test';
import assert from 'node:assert/strict';
import {escapeHtml, htmlFilename, makeStandaloneHtml} from '../scripts/build_standalone.mjs';

test('HTML output uses local classic assets and escaped metadata', () => {
  const page={id:'welcome',kind:'welcome',file:'intro.md',title:'Costs < returns & "risk"'};
  const html=makeStandaloneHtml(page,{title:'ROBO TRADE',description:'Read & learn'},'assets/book.js',['assets/book.css']);
  assert.match(html,/data-standalone="true"/);
  assert.match(html,/data-theme="light"/);
  assert.match(html,/<script defer src="assets\/book.js"><\/script>/);
  assert.match(html,/href="assets\/book.css"/);
  assert.doesNotMatch(html,/type="module"/);
  assert.match(html,/Costs &lt; returns &amp; &quot;risk&quot;/);
  assert.match(html,/เปิด JavaScript/);
});

test('generated filename rules prevent traversal and map welcome to index', () => {
  assert.equal(htmlFilename('welcome'),'index.html');
  assert.equal(htmlFilename('chapter-10'),'chapter-10.html');
  assert.throws(()=>htmlFilename('../chapter-10'));
  assert.throws(()=>htmlFilename('https://example.com'));
  assert.equal(escapeHtml("<&\"'>"),'&lt;&amp;&quot;&#39;&gt;');
});

 test('withdrawn chapters have empty bodies and no lesson assets',()=>{
 const html=makeStandaloneHtml({id:'chapter-09',kind:'lesson',title:'Archived lesson'},{},'assets/book.js',['assets/book.css']);
 assert.match(html,/<body><\/body>/);
 assert.doesNotMatch(html,/<script|Archived lesson|downloads|book\.js/);
 });
