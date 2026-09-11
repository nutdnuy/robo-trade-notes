// Markdown structure is parsed only outside fenced code blocks.
export function parsePage(source) {
  const lines = source.replace(/\r\n/g, '\n').split('\n');
  let title = '', section = null, fence = null;
  const intro = [], sections = [];
  for (const line of lines) {
    const delimiter = line.match(/^\s{0,3}(`{3,}|~{3,})/);
    if (delimiter) {
      const mark = delimiter[1];
      if (!fence) fence = mark;
      else if (mark[0] === fence[0] && mark.length >= fence.length) fence = null;
      (section ? section.lines : intro).push(line);
      continue;
    }
    if (!fence) {
      if (!title && /^# /.test(line)) { title = line.slice(2).trim(); continue; }
      const heading = line.match(/^## (.+?)(?:\s+\{#([a-z0-9-]+)\})?\s*$/);
      if (heading) {
        section = {id:heading[2] || 'section-'+(sections.length+1), label:heading[1], lines:[]};
        sections.push(section); continue;
      }
    }
    (section ? section.lines : intro).push(line);
  }
  if (!title) throw new Error('Each content page requires a # title');
  if (new Set(sections.map(s=>s.id)).size !== sections.length) throw new Error('Section IDs must be unique');
  return {title, intro:intro.join('\n').trim(), sections:sections.map(({lines,...s},i)=>({...s,number:String(i+1).padStart(2,'0'),body:lines.join('\n').trim()}))};
}

export function splitWidgets(markdown) {
  const chunks=[]; let buffer=[], fence=null;
  for (const line of markdown.split('\n')) {
    const delimiter=line.match(/^\s{0,3}(`{3,}|~{3,})/);
    if(delimiter){const mark=delimiter[1];if(!fence)fence=mark;else if(mark[0]===fence[0]&&mark.length>=fence.length)fence=null;}
    const widget=!fence && line.match(/^::: ([a-z][a-z0-9-]*)\s*$/);
    if(widget){if(buffer.length)chunks.push({markdown:buffer.join('\n')});buffer=[];chunks.push({widget:widget[1]});}
    else buffer.push(line);
  }
  if(buffer.length)chunks.push({markdown:buffer.join('\n')});
  return chunks;
}

export function parseRoute(hash, pages) {
  const path=hash.replace(/^#\/?/,'');
  const [id,section]=path.split('/');
  if(!id) return {page:pages[0].id,section:''};
  if(pages.some(p=>p.id===id)) return {page:id,section:section||''};
  // Keep links from the original single-chapter preview working.
  const chapter=pages.find(p=>p.id==='chapter-01');
  if(chapter && (id==='chapter-top'||chapter.sections.some(s=>s.id===id))) return {page:chapter.id,section:id==='chapter-top'?'':id};
  return {page:pages[0].id,section:''};
}

export function assetUrl(path) {
  if(/^(https?:|#|data:)/.test(path)) return path;
  return import.meta.env.BASE_URL + path.replace(/^\//,'');
}
