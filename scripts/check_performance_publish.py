"""Verify the published page, source download and bundled local links."""
from pathlib import Path
from html.parser import HTMLParser
import base64
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'
source = (ROOT / 'content/chapters/14-backtest-performance-evaluation.md').read_bytes()
html = (SITE / 'chapter-14.html').read_text()
assert 'noindex' not in html and 'ROBO_WIDGET_' not in html
assert 'data-standalone="true"' in html
assert 'href="./chapter-13.html"' in html

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.charts = 0
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'svg' and 'ema-chart' in a.get('class', ''):
            self.charts += 1
        if 'id' in a:
            assert a['id'] not in self.ids
            self.ids.add(a['id'])
        if tag == 'a' and 'href' in a:
            self.links.append(a['href'])

p = Page()
p.feed(html)
for link in p.links:
    if link.startswith('#'):
        assert link[1:] in p.ids, link
    elif not link.startswith(('data:', 'https:', 'http:', 'mailto:')):
        assert (SITE / link.split('#')[0]).exists(), link
downloads = [x for x in p.links if x.startswith('data:text/markdown')]
assert any(base64.b64decode(x.split(',', 1)[1]) == source for x in downloads)
with zipfile.ZipFile(SITE / 'downloads/performance/robo-trade-performance-review.zip') as z:
    assert z.read('chapter.md') == source
    assert not any(x.endswith('.pdf') or x.startswith('qa/') for x in z.namelist())
assert p.charts == 7
print('PASS: published chapter preserves owner Markdown; local links, seven charts and public source package verified.')
