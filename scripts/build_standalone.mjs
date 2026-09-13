/** Build the editable-source book into a website that opens directly from disk.
 *
 * Invoke through `npm run build:pages` so YAML/content/download preparation
 * runs first. `_site` is generated output; edit Markdown, YAML, and CSS sources.
 */
import {build} from 'vite';
import {createHash} from 'node:crypto';
import {mkdtemp, readFile, writeFile, mkdir, readdir, cp, rm, stat} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {parsePage} from '../src/lib/book.js';

const projectRoot=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
}

export function htmlFilename(pageId) {
  if (!/^[a-z][a-z0-9-]*$/.test(pageId)) throw new Error('Invalid page ID: '+pageId);
  return (pageId==='welcome'?'index':pageId)+'.html';
}

export function makeStandaloneHtml(page, book, jsFile, cssFiles) {
  if(page.kind!=='welcome') return '<!doctype html>\n<html lang="th" data-theme="light" data-standalone="true"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/><title>Robo Trade Notes</title></head><body></body></html>\n';
  const label=page.kind==='welcome'?'Welcome':'บทที่ '+page.number;
  const title=label+' · '+page.title+' | '+book.title;
  const styles=cssFiles.map(file=>`<link rel="stylesheet" href="${escapeHtml(file)}"/>`).join('\n');
  const source='downloads/content/'+page.file;
  return `<!doctype html>
<html lang="th" data-theme="light" data-standalone="true">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<meta name="theme-color" content="#ffffff"/>
<meta name="description" content="${escapeHtml(book.description)}"/>
<meta name="generator" content="Robo Trade offline book"/>
<title>${escapeHtml(title)}</title>
${styles}
</head>
<body>
<div id="root"></div>
<noscript><main><h1>${escapeHtml(page.title)}</h1><p>เปิด JavaScript เพื่ออ่านหน้า Welcome</p></main></noscript>
<script defer src="${escapeHtml(jsFile)}"></script>
</body>
</html>
`;
}

async function filesBelow(directory, prefix='') {
  const entries=await readdir(directory,{withFileTypes:true});
  const files=[];
  for (const entry of entries.sort((a,b)=>a.name.localeCompare(b.name))) {
    if (entry.name==='.DS_Store') continue;
    const relative=prefix?prefix+'/'+entry.name:entry.name;
    if (entry.isDirectory()) files.push(...await filesBelow(path.join(directory,entry.name),relative));
    else if (entry.isFile()) files.push(relative);
    else throw new Error('Standalone output cannot contain symlinks: '+relative);
  }
  return files;
}

function safeRelative(file) {
  return typeof file==='string' && file.length>0 && !path.isAbsolute(file) && !file.split(/[\\/]/).includes('..');
}

async function assertLocalResource(directory, resource, relativeTo='') {
  if (/^(data:|#)/.test(resource)) return;
  if (/^(?:[a-z][a-z0-9+.-]*:|\/)/i.test(resource)) throw new Error('Non-local standalone asset: '+resource);
  const clean=decodeURIComponent(resource.split(/[?#]/)[0]);
  const resolved=path.resolve(directory,relativeTo,clean);
  if (!resolved.startsWith(path.resolve(directory)+path.sep)) throw new Error('Asset escapes output folder: '+resource);
  const info=await stat(resolved);
  if (!info.isFile()) throw new Error('Missing standalone file: '+resource);
}

export async function verifyStandalone(directory, pages) {
  for (const page of pages) {
    const html=await readFile(path.join(directory,htmlFilename(page.id)),'utf8');
    if (!html.includes('data-standalone="true"') || !html.includes('data-theme="light"')) {
      throw new Error('Missing standalone/light declarations for '+page.id);
    }
    if (/<script\b[^>]*type\s*=\s*["']module["']/i.test(html)) throw new Error('ES modules do not load reliably from file URLs');
    for (const tag of html.matchAll(/<(?:script|link)\b[^>]*>/gi)) {
      const resource=tag[0].match(/(?:src|href)=["']([^"']+)["']/i)?.[1];
      if (resource) await assertLocalResource(directory,resource);
    }
  }
  const cssFiles=(await filesBelow(directory)).filter(file=>file.endsWith('.css'));
  let localOrInlineFonts=0;
  for (const file of cssFiles) {
    const css=await readFile(path.join(directory,file),'utf8');
    if (/@import\s+(?:url\()?\s*["']?https?:/i.test(css)) throw new Error('CSS contains a remote import');
    for (const match of css.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)) {
      const resource=match[1].trim();
      await assertLocalResource(directory,resource,path.dirname(file));
      if (/^data:font\/|\.(?:woff2?|ttf|otf)(?:[?#]|$)/i.test(resource)) localOrInlineFonts++;
    }
  }
  if (localOrInlineFonts===0) throw new Error('No bundled font assets found');
  return {htmlPages:pages.length,stylesheets:cssFiles.length,fontReferences:localOrInlineFonts};
}

export async function buildStandalone() {
  const book=JSON.parse(await readFile(path.join(projectRoot,'content/book.json'),'utf8'));
  const pages=await Promise.all(book.pages.map(async page=>({
    ...page,
    ...parsePage(await readFile(path.join(projectRoot,'content',page.file),'utf8')),
  })));
  const names=pages.map(page=>htmlFilename(page.id));
  if (new Set(names).size!==names.length || !names.includes('index.html')) {
    throw new Error('Standalone page filenames must be unique and include a welcome page');
  }
  const staging=await mkdtemp(path.join(tmpdir(),'robo-trade-standalone-'));
  const destination=path.join(projectRoot,'_site');
  try {
    // A single classic IIFE avoids module-script CORS restrictions under file://.
    // Library mode also embeds imported font assets in the extracted stylesheet.
    const result=await build({
      configFile:false,
      root:projectRoot,
      base:'./',
      publicDir:false,
      esbuild:{jsx:'automatic'},
      define:{'process.env.NODE_ENV':JSON.stringify('production')},
      build:{
        outDir:staging,
        emptyOutDir:true,
        target:'es2020',
        sourcemap:false,
        cssCodeSplit:false,
        lib:{entry:path.join(projectRoot,'src/main.jsx'),name:'RoboTradeBook',formats:['iife'],fileName:()=> 'assets/book.js',cssFileName:'book'},
        rollupOptions:{output:{inlineDynamicImports:true,assetFileNames:'assets/[name][extname]'}},
      },
    });
    const outputs=(Array.isArray(result)?result:[result]).flatMap(result=>result.output||[]);
    const chunks=outputs.filter(output=>output.type==='chunk');
    const styles=outputs.filter(output=>output.type==='asset'&&output.fileName.endsWith('.css')).map(output=>output.fileName);
    if (chunks.length!==1 || chunks[0].imports.length || chunks[0].dynamicImports.length || styles.length===0) {
      throw new Error('Offline build must contain one self-contained script and local CSS');
    }
    // Content-based names prevent browsers from reusing the previous lesson bundle.
    const versionedFiles=new Map();
    for (const file of [chunks[0].fileName,...styles]) {
      const bytes=await readFile(path.join(staging,file));
      const digest=createHash('sha256').update(bytes).digest('hex').slice(0,12);
      const extension=path.extname(file);
      const versioned=file.slice(0,-extension.length)+'.'+digest+extension;
      await writeFile(path.join(staging,versioned),bytes);
      await rm(path.join(staging,file));
      versionedFiles.set(file,versioned);
    }
    await cp(path.join(projectRoot,'public'),staging,{recursive:true,filter:source=>!['.DS_Store','downloads'].includes(path.basename(source))});
    for (const page of pages) {
      await writeFile(path.join(staging,htmlFilename(page.id)),makeStandaloneHtml(page,book,versionedFiles.get(chunks[0].fileName),styles.map(file=>versionedFiles.get(file))));
    }
    const verification=await verifyStandalone(staging,pages);
    const generatedFiles=await filesBelow(staging);
    let previous=[];
    try { previous=JSON.parse(await readFile(path.join(destination,'standalone-manifest.json'),'utf8')).files||[]; }
    catch(error) { if(error.code!=='ENOENT' && !(error instanceof SyntaxError)) throw error; }
    await mkdir(destination,{recursive:true});
    // Only stale paths previously recorded by this builder are removed. Unknown
    // user files in _site are preserved; current generated files are rebuilt.
    for (const file of previous) {
      if (safeRelative(file) && !generatedFiles.includes(file)) await rm(path.join(destination,file),{force:true});
    }
    await cp(staging,destination,{recursive:true});
    const manifest={
      format:'robo-trade-standalone-v1',
      generatedAt:new Date().toISOString(),
      entry:'index.html',
      defaultTheme:'light',
      runtime:'classic-script-iife; no module loader or local server required',
      sourceOfTruth:'Markdown content, YAML book settings, and book.css; HTML is generated',
      verification,
      pages:pages.map(page=>({id:page.id,html:htmlFilename(page.id),source:'content/'+page.file,title:page.title})),
      files:generatedFiles,
    };
    await writeFile(path.join(destination,'standalone-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
    console.log(`Standalone book ready: ${path.relative(projectRoot,destination)}/index.html (${verification.htmlPages} pages, ${verification.fontReferences} local/embedded font references).`);
    return manifest;
  } finally {
    await rm(staging,{recursive:true,force:true});
  }
}

if (process.argv[1] && import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href) {
  buildStandalone().catch(error=>{console.error(error);process.exitCode=1;});
}
