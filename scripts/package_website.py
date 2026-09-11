"""Archive only the files recorded by the standalone website builder."""
import json
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
site = root / '_site'
manifest = json.loads((site / 'standalone-manifest.json').read_text())
output = root / 'outputs' / 'robo-trade-website.zip'
output.parent.mkdir(exist_ok=True)
files = sorted(set(manifest['files'] + ['standalone-manifest.json']))
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in files:
        path = site / name
        if path.is_symlink() or not path.is_file() or site.resolve() not in path.resolve().parents:
            raise ValueError('Invalid generated website path: ' + name)
        archive.write(path, Path('robo-trade-website') / name)
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    assert 'robo-trade-website/index.html' in archive.namelist()
    assert len([name for name in archive.namelist() if name.endswith('.html')]) == len(manifest['pages'])
print(f'{output.name}: {len(files)} generated website files, {output.stat().st_size:,} bytes; archive verified')
