import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { stringify } from 'yaml';
import { compileBook, generateBook, parseYaml } from '../scripts/generate_book.mjs';

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'robo-book-config-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(join(root, 'content/chapters'), { recursive: true });
  mkdirSync(join(root, 'public/images'), { recursive: true });
  mkdirSync(join(root, 'public/downloads'), { recursive: true });
  writeFileSync(join(root, 'content/intro.md'), '# Welcome\n\nIntroduction.\n\n## Start {#start}\n\nRead.\n');
  writeFileSync(join(root, 'content/chapters/01.md'), '# บทเรียน\n\nคำอธิบาย\n\n## ทดลอง {#lab}\n\nข้อมูลจำลอง\n');
  writeFileSync(join(root, 'public/images/cover.png'), 'fixture');
  writeFileSync(join(root, 'public/downloads/robo-trade-01.ipynb'), '{}');
  const config = {
    title: 'Robo Trade Notes', subtitle: 'Python · Webull', language: 'ภาษาไทย',
    description: 'คำอธิบาย', edition: 'กันยายน 2026', apiDocs: 'https://example.com/docs/', defaultTheme: 'light',
    welcome: { id: 'welcome', title: 'ยินดีต้อนรับ', eyebrow: 'WELCOME', meta: ['1 บทเรียน'],
      heroImage: 'images/cover.png', heroAlt: 'ภาพหน้าปก', primaryLabel: 'เริ่มเรียน', primaryHref: '#/chapter-01/lab' },
  };
  const toc = { format: 'robo-trade-book', root: 'content/intro.md', chapters: [
    { id: 'chapter-01', file: 'content/chapters/01.md', title: 'บทแรก', number: '01', eyebrow: 'CHAPTER 01',
      part: 'พื้นฐาน', outcome: 'อ่านตารางได้', duration: '40–50', meta: ['Notebook'],
      secondaryLabel: 'ดาวน์โหลด', secondaryHref: 'downloads/robo-trade-01.ipynb' },
  ] };
  const write = () => {
    writeFileSync(join(root, '_config.yml'), stringify(config));
    writeFileSync(join(root, '_toc.yml'), stringify(toc));
  };
  write();
  return { root, config, toc, write };
}

test('real YAML supports Thai text and quoted chapter numbers without losing metadata', t => {
  const { root, config, toc } = fixture(t);
  const book = compileBook(parseYaml(stringify(config), 'config'), parseYaml(stringify(toc), 'toc'), { root });
  assert.equal(book.defaultTheme, 'light');
  assert.equal(book.pages[0].file, 'intro.md');
  assert.equal(book.pages[1].file, 'chapters/01.md');
  assert.equal(book.pages[1].number, '01');
  assert.equal(book.pages[1].label, 'บทแรก');
  assert.equal(book.pages[1].duration, '40–50');
  assert.equal(book.pages[0].heroAlt, 'ภาพหน้าปก');
  assert.equal(book.pages[0].primaryHref, '#/chapter-01/lab');
});

test('bad YAML, duplicate mapping keys, tags and aliases fail before compilation', () => {
  for (const source of ['title: first\ntitle: second\n', 'title: [unterminated', 'title: !command something', 'title: &a Name\nsubtitle: *a\n']) {
    assert.throws(() => parseYaml(source, '_config.yml'), /_config.yml/);
  }
});

test('rejects typo settings, numeric chapter IDs, invalid duration, duplicate routes and missing content', t => {
  const { root, config, toc } = fixture(t);
  assert.throws(() => compileBook({ ...config, defaultThem: 'light' }, toc, { root }), /unknown setting/);
  const withChapter = change => ({ ...toc, chapters: [{ ...toc.chapters[0], ...change }] });
  assert.throws(() => compileBook(config, withChapter({ number: 1 }), { root }), /quote the chapter number/);
  assert.throws(() => compileBook(config, withChapter({ id: '01-foundations' }), { root }), /start with a lowercase/);
  assert.throws(() => compileBook({ ...config, welcome: { ...config.welcome, id: 'home' } }, toc, { root }), /must remain welcome/);
  assert.throws(() => compileBook(config, withChapter({ duration: '50–20' }), { root }), /positive minutes/);
  assert.throws(() => compileBook(config, withChapter({ file: 'content/chapters/missing.md' }), { root }), /does not exist/);
  assert.throws(() => compileBook(config, { ...toc, chapters: [toc.chapters[0], { ...toc.chapters[0] }] }, { root }), /duplicate id/);
});

test('validates all configured routes and local downloads', t => {
  const { root, config, toc } = fixture(t);
  assert.throws(() => compileBook({ ...config, welcome: { ...config.welcome, primaryHref: '#/chapter-01/missing' } }, toc, { root }), /unknown section/);
  assert.throws(() => compileBook({ ...config, welcome: { ...config.welcome, primaryHref: 'javascript:alert(1)' } }, toc, { root }), /HTTPS URL/);
  assert.throws(() => compileBook(config, { ...toc, chapters: [{ ...toc.chapters[0], secondaryHref: 'downloads/missing.ipynb' }] }, { root }), /does not exist/);
});

test('content paths stay inside canonical content even through symlinks', t => {
  const { root, config, toc } = fixture(t);
  writeFileSync(join(root, 'outside.md'), '# Outside\n\n## Section {#start}\n');
  symlinkSync(join(root, 'outside.md'), join(root, 'content/escaped.md'));
  for (const source of ['../outside.md', '/tmp/outside.md', 'content/../outside.md']) {
    assert.throws(() => compileBook(config, { ...toc, root: source }, { root }), /project-relative|inside content/);
  }
  assert.throws(() => compileBook(config, { ...toc, root: 'content/escaped.md' }, { root }), /symlink/);
});

test('generation detects stale intermediates and leaves last good JSON intact after invalid edits', t => {
  const { root, config, write } = fixture(t);
  generateBook({ root, silent: true });
  const initial = readFileSync(join(root, 'content/book.json'), 'utf8');
  assert.doesNotThrow(() => generateBook({ root, check: true, silent: true }));
  config.title = 'Edited title'; write();
  assert.throws(() => generateBook({ root, check: true, silent: true }), /stale/);
  generateBook({ root, silent: true });
  const changed = readFileSync(join(root, 'content/book.json'), 'utf8');
  assert.notEqual(initial, changed);
  writeFileSync(join(root, '_config.yml'), 'title: [broken');
  assert.throws(() => generateBook({ root, silent: true }), /_config.yml/);
  assert.equal(readFileSync(join(root, 'content/book.json'), 'utf8'), changed);
});
