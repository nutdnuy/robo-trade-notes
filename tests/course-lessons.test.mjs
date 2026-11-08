import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

// Lessons 16-25 are standard-library Python files whose asserts check every
// number quoted in the matching chapter. Each must finish with this marker.
const lessons = Array.from({ length: 10 }, (_, i) => String(16 + i));

for (const number of lessons) {
  test(`lesson_${number}.py runs offline and passes its own checks`, () => {
    const result = spawnSync('python3', [`public/downloads/lesson_${number}.py`], { encoding: 'utf8', timeout: 60_000 });
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /ALL CHECKS PASSED\s*$/);
  });

  test(`robo-trade-${number}.ipynb was executed without errors`, () => {
    const notebook = JSON.parse(readFileSync(`public/downloads/robo-trade-${number}.ipynb`, 'utf8'));
    const code = notebook.cells.filter((cell) => cell.cell_type === 'code');
    assert.ok(code.length >= 5);
    for (const cell of code) {
      assert.ok(Number.isInteger(cell.execution_count));
      assert.ok(cell.outputs.every((output) => output.output_type !== 'error'));
    }
  });
}
