"""Build and execute the notebooks for course lessons 16-25 with standard Python.

Each `public/downloads/lesson_NN.py` is written in percent format:

    definitions ...                # first code cell
    # %% [markdown]
    # ## Heading                   # markdown cell, "# " prefix removed
    # %%
    code ...                       # code cell

The same file runs as a plain script (`python3 lesson_NN.py`), so its assert
cells double as the lesson's calculation tests. This builder executes every
code cell in order in one shared namespace, captures stdout and saves it as
the notebook output. No kernel, market API, network access or download.

Usage: python3 scripts/build_course_lessons.py [16 17 ...]
"""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "public" / "downloads"
LESSONS = [str(n) for n in range(16, 26)]


def split_cells(source):
    cells, kind, lines = [], "code", []

    def flush():
        text = "\n".join(lines).strip("\n")
        if text.strip():
            if kind == "markdown":
                text = "\n".join(line[2:] if line.startswith("# ") else line.lstrip("#") for line in text.splitlines())
            cells.append((kind, text + "\n"))

    for line in source.splitlines():
        if line.strip() == "# %% [markdown]":
            flush(); kind, lines = "markdown", []
        elif line.strip() == "# %%":
            flush(); kind, lines = "code", []
        else:
            lines.append(line)
    flush()
    return cells


def cell_id(number, index, text):
    return hashlib.sha256(f"{number}:{index}:{text}".encode()).hexdigest()[:12]


def build(number):
    path = DOWNLOADS / f"lesson_{number}.py"
    cells = split_cells(path.read_text(encoding="utf-8"))
    namespace = {"__name__": "__notebook__", "__file__": str(path)}
    notebook_cells, count = [], 0
    for index, (kind, text) in enumerate(cells):
        cell = {"cell_type": kind, "id": cell_id(number, index, text), "metadata": {},
                "source": text.splitlines(keepends=True)}
        if kind == "code":
            count += 1
            stream = io.StringIO()
            try:
                with contextlib.redirect_stdout(stream):
                    exec(compile(text, f"lesson_{number}.py cell {count}", "exec"), namespace)
            except Exception:
                sys.stderr.write(stream.getvalue())
                traceback.print_exc()
                raise SystemExit(f"lesson_{number}.py: cell {count} failed")
            output = stream.getvalue()
            cell.update(execution_count=count,
                        outputs=[{"output_type": "stream", "name": "stdout", "text": output.splitlines(keepends=True)}] if output else [])
        notebook_cells.append(cell)
    notebook = {"cells": notebook_cells, "nbformat": 4, "nbformat_minor": 5, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": platform.python_version()},
        "execution": {"method": "Each code cell executed in order by CPython in one shared namespace", "codeCells": count}}}
    target = DOWNLOADS / f"robo-trade-{number}.ipynb"
    target.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"PASS: {target.relative_to(ROOT)} - {count} code cells executed")


if __name__ == "__main__":
    for number in sys.argv[1:] or LESSONS:
        build(number)
