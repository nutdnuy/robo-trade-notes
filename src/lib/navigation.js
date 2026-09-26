import {parseRoute} from './book.js';

// The optional context argument lets Node tests exercise routes without a DOM.
// In the browser, generated HTML declares data-standalone="true" on <html>.
function environment(context = {}) {
  return {
    standalone: context.standalone ?? globalThis.document?.documentElement?.dataset?.standalone === 'true',
    pathname: context.pathname ?? globalThis.location?.pathname ?? '/',
    hash: context.hash ?? globalThis.location?.hash ?? '',
  };
}

function decode(value) {
  try { return decodeURIComponent(value); }
  catch { return value; }
}

function validPageId(pageId) {
  if (!/^[a-z][a-z0-9-]*$/.test(pageId)) {
    throw new Error('Page IDs must contain lowercase letters, numbers, and hyphens');
  }
  return pageId;
}

/** Return a dev hash URL or a sibling standalone HTML URL. */
export function pageHref(pageId, section = '', context = {}) {
  const id = validPageId(pageId);
  const fragment = section ? encodeURIComponent(section) : '';
  if (id === 'chapter-14' || environment(context).standalone) {
    return (id === 'welcome' ? 'index' : id) + '.html' + (fragment ? '#' + fragment : '');
  }
  return '#/' + id + (fragment ? '/' + fragment : '');
}

/** Read native chapter-NN.html#section and all existing #/page/section URLs. */
export function readRoute(pages, context = {}) {
  if (!Array.isArray(pages) || pages.length === 0) {
    throw new Error('readRoute requires at least one content page');
  }
  const {pathname, hash} = environment(context);
  const safePages = pages.map(page => ({...page, sections: page.sections || []}));
  // Explicit legacy routes take precedence, even on a standalone filename.
  if (/^#\//.test(hash)) {
    return parseRoute(decode(hash), safePages);
  }
  const filename = decode(pathname.split('/').at(-1) || '');
  const filenameId = filename === 'index.html' ? 'welcome' : filename.replace(/\.html$/, '');
  const nativePage = /\.html$/.test(filename) && safePages.find(page => page.id === filenameId);
  if (nativePage) {
    const section = decode(hash.replace(/^#/, ''));
    return {page: nativePage.id, section: section === 'chapter-top' ? '' : section};
  }
  // This also preserves old one-chapter #lab / #quiz / #chapter-top links in dev.
  return parseRoute(decode(hash), safePages);
}
