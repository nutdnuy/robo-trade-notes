// Course numbers come from the outline in _toc.yml, not from file numbers.
// Prework entries are numbered P1, P2, ...; chapters are numbered 1, 2, ...

export function outlineEntry(outline, pageId) {
  for (const part of outline || []) {
    const entry = part.entries.find(item => item.page === pageId);
    if (entry) return entry;
  }
  return null;
}

/** "Prework P2" for prework, otherwise `${chapterWord} 3`; null when unlisted. */
export function courseLabel(outline, pageId, chapterWord = 'Chapter') {
  const entry = outlineEntry(outline, pageId);
  if (!entry) return null;
  return entry.number.startsWith('P') ? 'Prework ' + entry.number : chapterWord + ' ' + entry.number;
}
