// Keep the withdrawn learning edition archived; only these pages are public.
export const publishedPageIds = ['welcome', 'chapter-11', 'chapter-12', 'chapter-13'];
export const isPublishedPage = id => publishedPageIds.includes(id);
