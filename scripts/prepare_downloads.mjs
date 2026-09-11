import {readFileSync,mkdirSync,copyFileSync,writeFileSync} from 'node:fs';
import {dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=new URL('../',import.meta.url);
const book=JSON.parse(readFileSync(new URL('content/book.json',root),'utf8'));
for(const page of book.pages){const dest=new URL('public/downloads/content/'+page.file,root);mkdirSync(dirname(fileURLToPath(dest)),{recursive:true});copyFileSync(new URL('content/'+page.file,root),dest);}
copyFileSync(new URL('EDITING.md',root),new URL('public/downloads/EDITING.md',root));
const complete=book.pages.map(p=>readFileSync(new URL('content/'+p.file,root),'utf8')).join('\n\n---\n\n');
writeFileSync(new URL('public/downloads/robo-trade-complete.md',root),complete);
console.log(`Prepared editable Markdown downloads for ${book.pages.length} pages.`);
