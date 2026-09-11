"""Execute the course's offline Python and notebook examples in clean processes.

Default requires only the pinned learning dependencies. --jupyter additionally
requires requirements-qa.txt and executes actual fresh kernels. --refresh saves
newly verified notebook outputs; source text is preserved.
"""
from pathlib import Path
import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / 'public/downloads'

def check_notebook(path):
    notebook = json.loads(path.read_text())
    code = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
    assert len(code) >= 5
    ids = [cell['id'] for cell in notebook['cells']]
    assert len(ids) == len(set(ids))
    for cell in code:
        assert isinstance(cell['execution_count'], int)
        assert not any(out.get('output_type') == 'error' for out in cell['outputs'])
    return len(code)

def run_kernel(path, refresh):
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    from jupyter_client.kernelspec import KernelSpecManager
    nb = nbformat.read(path, as_version=4)
    nbformat.validate(nb)
    with tempfile.TemporaryDirectory(prefix='robo-notebook-') as tmp:
        temp = Path(tmp)
        specdir = temp / 'kernels' / 'robo-course'
        specdir.mkdir(parents=True)
        (specdir / 'kernel.json').write_text(json.dumps({
            'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'Robo Trade Verification', 'language': 'python',
        }))
        manager = KernelManager(kernel_name='robo-course', kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(specdir.parent)]))
        client = NotebookClient(nb, km=manager, timeout=90, allow_errors=False,
                                resources={'metadata': {'path': tmp}})
        try:
            client.execute()
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
        nbformat.validate(nb)
        if refresh:
            nbformat.write(nb, path)
    return len([c for c in nb.cells if c.cell_type == 'code'])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jupyter', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    if args.refresh and not args.jupyter:
        parser.error('--refresh requires --jupyter')
    book = json.loads((ROOT / 'content/book.json').read_text())
    count = 0
    for page in book['pages']:
        if page['kind'] != 'lesson':
            continue
        n = page['number']
        script = DOWNLOADS / f'lesson_{n}.py'
        result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError(f'{script.name}: {result.stderr}')
        path = DOWNLOADS / f'robo-trade-{n}.ipynb'
        cells = run_kernel(path, args.refresh) if args.jupyter else check_notebook(path)
        count += cells
        print(f'PASS {n}: Python example, {cells} notebook code cells' + (' in a clean Jupyter kernel' if args.jupyter else ' with saved execution records'), flush=True)
    print(f'PASS complete course: {count} notebook code cells; Python {sys.version.split()[0]}', flush=True)

if __name__ == '__main__':
    main()
