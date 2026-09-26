"""Package public chapter sources without private PDFs, local QA or prior drafts."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'lessons/performance'
target = ROOT / 'public/downloads/performance/robo-trade-performance-review.zip'
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for item in sorted(SOURCE.rglob('*')):
        if not item.is_file() or item.is_symlink():
            continue
        relative = item.relative_to(SOURCE)
        if any(part in ('qa', '__pycache__', 'node_modules') for part in relative.parts) or item.name == '.DS_Store':
            continue
        archive.write(item, str(relative))
    archive.write(ROOT / 'content/chapters/14-backtest-performance-evaluation.md', 'chapter.md')
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
print('Packaged editable performance chapter and frozen public market data.')
