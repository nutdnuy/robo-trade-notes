#!/usr/bin/env python3
"""Set main-domain canonicals on approved exported pages; preserve body and robots."""
import json, re
from pathlib import Path
from html import escape
from html.parser import HTMLParser
ROOT = Path(__file__).resolve().parents[1]
MAPPING = json.loads((ROOT / 'scripts/library-canonicals.json').read_text())
class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(); self.canonicals = []; self.robots = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('rel', '').lower() == 'canonical': self.canonicals.append(attrs.get('href'))
        if tag == 'meta' and attrs.get('name', '').lower() == 'robots': self.robots.append(attrs.get('content'))
def update(source, canonical):
    match = re.search(r'(?is)(<head\b[^>]*>)(.*?)(</head\s*>)', source)
    if not match:
        # The toolkit license index uses HTML's valid implicit head syntax.
        metadata = Metadata(); metadata.feed(source)
        if metadata.canonicals == [canonical]: return source
        if metadata.canonicals: raise ValueError('Unexpected implicit-head canonical')
        title = re.search(r'(?is)</title\s*>', source)
        if not title: raise ValueError('Expected HTML head or title')
        tag = '\n<link rel="canonical" href="' + escape(canonical, quote=True) + '">\n'
        return source[:title.end()] + tag + source[title.end():]
    old = Metadata(); old.feed(source)
    if old.canonicals == [canonical]: return source
    head = match[2]
    def strip_tag(m):
        parsed = Metadata(); parsed.feed(m[0])
        return '' if parsed.canonicals else m[0]
    head = re.sub(r'(?is)<link\b[^>]*>', strip_tag, head)
    head += '\n<link rel="canonical" href="' + escape(canonical, quote=True) + '">\n'
    result = source[:match.start(2)] + head + source[match.end(2):]
    new = Metadata(); new.feed(result)
    assert new.canonicals == [canonical]
    assert new.robots == old.robots, 'Robots directive must be preserved'
    assert result[result.lower().index('</head>'):] == source[source.lower().index('</head>'):]
    return result
if __name__ == '__main__':
    output = ROOT / '_site'
    for filename, canonical in MAPPING.items():
        assert canonical.startswith('https://www.quant-corner.com/library/')
        assert '..' not in Path(filename).parts and not Path(filename).is_absolute()
        file = output / filename
        if not file.is_file(): raise FileNotFoundError(file)
        file.write_text(update(file.read_text(), canonical))
    # The older Node book builders also export intro.html as the welcome alias.
    intro = output / 'intro.html'
    if intro.is_file() and 'intro.html' not in MAPPING:
        intro.write_text(update(intro.read_text(), MAPPING['index.html']))
    print(f'Canonical URLs updated for {len(MAPPING)} approved Library pages; content and robots preserved.')
