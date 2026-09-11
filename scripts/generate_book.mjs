/** Compile the canonical YAML sources into the reader's intermediate JSON. */
import { existsSync, readFileSync, realpathSync, statSync, writeFileSync, renameSync, unlinkSync } from 'node:fs';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseDocument } from 'yaml';
import { parsePage } from '../src/lib/book.js';

const PROJECT_ROOT = fileURLToPath(new URL('../', import.meta.url));
const GLOBAL_KEYS = ['title', 'subtitle', 'language', 'description', 'edition', 'apiDocs', 'defaultTheme', 'welcome'];
const PAGE_KEYS = ['id', 'title', 'eyebrow', 'heroImage', 'heroAlt', 'meta', 'primaryLabel', 'primaryHref', 'secondaryLabel', 'secondaryHref'];
const CHAPTER_KEYS = [...PAGE_KEYS, 'file', 'number', 'part', 'outcome', 'duration'];
const ID_PATTERN = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;

function fail(label, message) { throw new Error(`${label}: ${message}`); }
function object(value, label) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) fail(label, 'expected a YAML mapping');
}
function keys(value, allowed, label) {
  object(value, label);
  for (const key of Object.keys(value)) if (!allowed.includes(key)) fail(label, `unknown setting "${key}"`);
}
function text(value, label) {
  if (typeof value !== 'string' || !value.trim()) fail(label, 'expected nonempty text');
  return value;
}
function has(value, key) { return Object.prototype.hasOwnProperty.call(value, key); }

export function parseYaml(source, label) {
  const doc = parseDocument(source, { version: '1.2', strict: true, uniqueKeys: true, stringKeys: true });
  const problem = [...doc.errors, ...doc.warnings][0];
  if (problem) fail(label, problem.message);
  let value;
  try { value = doc.toJS({ maxAliasCount: 0 }); }
  catch (error) { fail(label, error.message); }
  object(value, label);
  return value;
}

function localFile(root, source, baseFolder, label, extension) {
  text(source, label);
  if (isAbsolute(source) || source.includes('\\') || /[?#\0]/.test(source) || source.split('/').some(part => part === '..' || part === '.')) {
    fail(label, 'use a project-relative path without .., query strings or fragments');
  }
  const folder = resolve(root, baseFolder);
  let pathname = source;
  if (extension && !pathname.endsWith(extension)) pathname += extension;
  const absolute = resolve(root, pathname);
  if (!absolute.startsWith(folder + sep)) fail(label, `file must be inside ${baseFolder}/`);
  if (!existsSync(absolute) || !statSync(absolute).isFile()) fail(label, `file does not exist: ${pathname}`);
  const actual = realpathSync(absolute);
  if (!actual.startsWith(realpathSync(folder) + sep)) fail(label, 'symlink resolves outside the allowed source folder');
  if (extension && !actual.endsWith(extension)) fail(label, `expected a ${extension} source`);
  return { absolute, relative: relative(folder, absolute).split(sep).join('/') };
}

function pageMetadata(value, label, kind, root) {
  keys(value, kind === 'welcome' ? PAGE_KEYS : CHAPTER_KEYS, label);
  for (const key of ['id', 'title', 'eyebrow']) text(value[key], `${label}.${key}`);
  if (!ID_PATTERN.test(value.id)) fail(`${label}.id`, 'start with a lowercase English letter; use lowercase letters, numbers and single hyphens');
  if (kind === 'welcome' && value.id !== 'welcome') fail(`${label}.id`, 'the Welcome page ID must remain welcome for index.html');
  if (!Array.isArray(value.meta) || !value.meta.length) fail(`${label}.meta`, 'expected a nonempty list of text labels');
  value.meta.forEach((item, index) => text(item, `${label}.meta[${index}]`));
  for (const prefix of ['primary', 'secondary']) {
    const caption = `${prefix}Label`, href = `${prefix}Href`;
    if (has(value, caption) !== has(value, href)) fail(label, `${caption} and ${href} must be supplied together`);
    if (has(value, caption)) { text(value[caption], `${label}.${caption}`); text(value[href], `${label}.${href}`); }
  }
  if (has(value, 'heroImage')) {
    localFile(root, 'public/' + text(value.heroImage, `${label}.heroImage`), 'public', `${label}.heroImage`);
    text(value.heroAlt, `${label}.heroAlt`);
  } else if (has(value, 'heroAlt')) fail(label, 'heroAlt requires heroImage');
  if (kind === 'lesson') {
    if (typeof value.number !== 'string' || !/^\d{2,}$/.test(value.number)) fail(`${label}.number`, 'quote the chapter number, for example "01"');
    for (const key of ['part', 'outcome']) text(value[key], `${label}.${key}`);
    if (typeof value.duration === 'number') {
      if (!Number.isFinite(value.duration) || value.duration <= 0) fail(`${label}.duration`, 'expected positive minutes');
    } else {
      const range = typeof value.duration === 'string' && value.duration.match(/^(\d+)\s*[–-]\s*(\d+)$/);
      if (!range || Number(range[1]) <= 0 || Number(range[2]) < Number(range[1])) fail(`${label}.duration`, 'use positive minutes or a range such as "50–65"');
    }
  }
  const { title, file, ...metadata } = value;
  return { ...metadata, kind, label: title };
}

function checkHref(href, label, pages, sections, root) {
  if (/^https:\/\//.test(href)) {
    try { new URL(href); } catch { fail(label, 'invalid HTTPS URL'); }
    return;
  }
  if (href.startsWith('#/')) {
    const match = href.match(/^#\/([a-z0-9-]+)(?:\/([a-z0-9-]+))?$/);
    if (!match || !pages.some(page => page.id === match[1])) fail(label, `unknown page route: ${href}`);
    if (match[2] && !sections.get(match[1]).has(match[2])) fail(label, `unknown section route: ${href}`);
    return;
  }
  if (/^[a-z]+:/i.test(href) || href.startsWith('//') || href.startsWith('#')) fail(label, 'use an existing #/page/section route, public file, or HTTPS URL');
  localFile(root, 'public/' + href, 'public', label);
}

export function compileBook(config, toc, { root = PROJECT_ROOT } = {}) {
  keys(config, GLOBAL_KEYS, '_config.yml');
  for (const key of GLOBAL_KEYS.filter(key => !['welcome', 'defaultTheme'].includes(key))) text(config[key], `_config.yml.${key}`);
  if (!['light', 'dark'].includes(config.defaultTheme)) fail('_config.yml.defaultTheme', 'choose light or dark');
  if (!/^https:\/\//.test(config.apiDocs)) fail('_config.yml.apiDocs', 'expected an HTTPS documentation URL');
  try { new URL(config.apiDocs); } catch { fail('_config.yml.apiDocs', 'invalid HTTPS URL'); }
  keys(toc, ['format', 'root', 'chapters'], '_toc.yml');
  if (toc.format !== 'robo-trade-book') fail('_toc.yml.format', 'expected robo-trade-book (the custom builder format)');
  if (!Array.isArray(toc.chapters) || !toc.chapters.length) fail('_toc.yml.chapters', 'add at least one chapter');
  const welcome = pageMetadata(config.welcome, '_config.yml.welcome', 'welcome', root);
  welcome.file = localFile(root, toc.root, 'content', '_toc.yml.root', '.md').relative;
  const pages = [welcome, ...toc.chapters.map((chapter, index) => {
    const label = `_toc.yml.chapters[${index}]`;
    const page = pageMetadata(chapter, label, 'lesson', root);
    page.file = localFile(root, chapter.file, 'content', `${label}.file`, '.md').relative;
    return page;
  })];
  for (const [key, scope] of [['id', pages], ['file', pages], ['number', pages.filter(page => page.kind === 'lesson')]]) {
    const seen = new Set();
    for (const page of scope) {
      if (seen.has(page[key])) fail('_toc.yml', `duplicate ${key}: ${page[key]}`);
      seen.add(page[key]);
    }
  }
  const sections = new Map(pages.map(page => {
    const parsed = parsePage(readFileSync(resolve(root, 'content', page.file), 'utf8'));
    if (!parsed.title || !parsed.sections.length) fail(page.file, 'add a page title and at least one section');
    if (new Set(parsed.sections.map(section => section.id)).size !== parsed.sections.length) fail(page.file, 'section IDs must be unique');
    return [page.id, new Set(parsed.sections.map(section => section.id))];
  }));
  for (const page of pages) for (const name of ['primaryHref', 'secondaryHref']) if (page[name]) checkHref(page[name], `${page.id}.${name}`, pages, sections, root);
  const { welcome: ignored, ...settings } = config;
  return { ...settings, pages };
}

export function generateBook({ root = PROJECT_ROOT, check = false, silent = false } = {}) {
  const config = parseYaml(readFileSync(resolve(root, '_config.yml'), 'utf8'), '_config.yml');
  const toc = parseYaml(readFileSync(resolve(root, '_toc.yml'), 'utf8'), '_toc.yml');
  const book = compileBook(config, toc, { root });
  const target = resolve(root, 'content/book.json');
  const output = JSON.stringify(book, null, 2) + '\n';
  const current = existsSync(target) ? readFileSync(target, 'utf8') : '';
  if (check && current !== output) fail('content/book.json', 'generated file is stale; run npm run generate:book');
  if (!check && current !== output) {
    const temporary = resolve(dirname(target), `.book-${process.pid}.json.tmp`);
    try { writeFileSync(temporary, output); renameSync(temporary, target); }
    finally { if (existsSync(temporary)) unlinkSync(temporary); }
  }
  if (!silent) console.log(`Validated ${pagesSummary(book)} from _config.yml and _toc.yml${check ? '; intermediate JSON is current' : '; generated content/book.json'}.`);
  return book;
}
function pagesSummary(book) { return `${book.pages.length} pages`; }

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.some(arg => arg !== '--check')) { console.error('Usage: node scripts/generate_book.mjs [--check]'); process.exitCode = 1; }
  else try { generateBook({ check: args.includes('--check') }); }
  catch (error) { console.error(`Book configuration error: ${error.message}`); process.exitCode = 1; }
}
