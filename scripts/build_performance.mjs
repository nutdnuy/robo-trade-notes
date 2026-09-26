/** Publish the owner-reviewed chapter using its existing deterministic renderer. */
import {readFileSync,writeFileSync,mkdirSync,cpSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const root=fileURLToPath(new URL('../',import.meta.url));
const source=path.join(root,'lessons/performance');
mkdirSync(path.join(source,'qa'),{recursive:true});
execFileSync(process.execPath,['build.mjs'],{cwd:source,stdio:'inherit'});
let html=readFileSync(path.join(source,'chapter-14-review.html'),'utf8');
html=html.replace('<html lang="th" data-theme="light">','<html lang="th" data-theme="light" data-standalone="true">')
 .replace('<meta name="robots" content="noindex,nofollow"/>','')
 .replace(' | Robo Trade Notes · Review',' | Robo Trade Notes')
 .replace(/<span class="status">[^<]*<\/span>/,'')
 .replaceAll('Robo Trade Notes · ฉบับตรวจในเครื่อง','Robo Trade Notes')
 .replaceAll('ฉบับตรวจส่วนตัว: ','')
 .replaceAll('https://nutdnuy.github.io/robo-trade-notes/','./');
for(const file of ['robo-trade-performance-review.zip','performance-report.html','data/sp500-daily.csv','data/provenance.json']) {
 html=html.replaceAll(`href="${file}"`,`href="downloads/performance/${file}"`);
}
writeFileSync(path.join(root,'public/chapter-14.html'),html);
const downloads=path.join(root,'public/downloads/performance');
mkdirSync(downloads,{recursive:true});
for(const file of ['performance-report.html','data','figures-ema'])cpSync(path.join(source,file),path.join(downloads,file),{recursive:true});
for(const file of ['robo-trade-14.ipynb','lesson_14.py'])cpSync(path.join(source,file),path.join(root,'public/downloads',file));
execFileSync('python3',['scripts/package_performance.py'],{cwd:root,stdio:'inherit'});
console.log('Published chapter renderer: public/chapter-14.html');
