"""Package only commissioned learning materials; preserve editable notebook sources."""
from pathlib import Path
import json
import zipfile
root = Path(__file__).resolve().parents[1]
folder = root / 'public' / 'downloads'
book = json.loads((root / 'content/book.json').read_text())
paths = []
for page in book['pages']:
    paths.append((root / 'content' / page['file'], 'content/' + page['file']))
    if page['kind'] == 'lesson':
        n = page['number']
        paths += [(folder / f'robo-trade-{n}.ipynb', f'notebooks/robo-trade-{n}.ipynb'),
                  (folder / f'lesson_{n}.py', f'python/lesson_{n}.py')]
for name in ['requirements.txt', 'requirements-webull.txt', 'demo_prices.csv', 'README.md']:
    paths.append((folder / name, name))
paths += [(folder / name, name) for name in ['backtest-intro-data.json', 'backtest-intro-results.json']]
paths.append((folder / 'webull_bars.py', 'python/webull_bars.py'))
paths += [(root / 'EDITING.md', 'EDITING.md'), (root / 'content/book.json', 'content/book.json')]
paths += [(p, 'content/quizzes/' + p.name) for p in sorted((root / 'content/quizzes').glob('chapter-*.json'))]
paths += [(root / 'public/THIRD_PARTY_NOTICES.txt', 'THIRD_PARTY_NOTICES.txt')]
output = folder / 'robo-trade-complete-materials.zip'
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path, name in paths:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Missing regular learning file: {path.name}')
        archive.write(path, name)
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
print(f'Packaged {len(paths)} learning files: {output.name}')
