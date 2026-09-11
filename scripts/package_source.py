"""Package an editable project from an explicit allowlist; never collect local inputs."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
output = root / 'outputs' / 'robo-trade-editable.zip'
output.parent.mkdir(exist_ok=True)
folders = ['.github/workflows', 'src', 'content', 'tests', 'scripts', 'public/images', 'public/downloads', 'references']
files = ['README.md', 'EDITING.md', 'DEPLOYMENT.md', 'Preview.command', '_config.yml', '_toc.yml', 'book.css', 'requirements-qa.txt', 'package.json', 'package-lock.json', 'index.html', 'vite.config.js',
         'components.json', '.gitignore', 'public/THIRD_PARTY_NOTICES.txt',
         'references/source-review.md', 'references/design-manifest.md',
         'references/welcome-design.md', 'references/welcome-image-prompt.md',
         'references/licenses/react-bits.txt']
excluded_parts = {'__pycache__', 'node_modules', '.git', '.venv', '.codex', '.agents', 'private'}
excluded_names = {'AGENTS.md', '.DS_Store', 'credentials.json', 'secrets.json', 'token.json', 'tokens.json', 'service-account.json'}
excluded_suffixes = {'.pdf', '.log', '.pem', '.key', '.p12', '.pfx', '.keychain', '.keychain-db'}

def excluded(path):
    """Keep local documents, credentials, caches and logs out of source archives."""
    relative = path.relative_to(root)
    return (bool(set(relative.parts) & excluded_parts)
            or path.name in excluded_names
            or path.name.startswith('.env')
            or path.suffix.lower() in excluded_suffixes)

paths = [root / name for name in files]
for folder in folders:
    paths += [p for p in (root / folder).rglob('*') if p.is_file() and not p.is_symlink()
              and not excluded(p)]
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(set(paths)):
        if path.is_symlink() or not path.is_file() or excluded(path):
            raise ValueError('Missing or symlink source: ' + str(path.relative_to(root)))
        archive.write(path, Path('robo-trade-learning') / path.relative_to(root))
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert not any(name.endswith('.pdf') or '/node_modules/' in name or name.endswith('AGENTS.md') for name in names)
print(f'{output.name}: {len(names)} editable files, {output.stat().st_size:,} bytes; archive verified')
