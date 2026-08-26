'use strict';

const fs = require('fs');
const path = require('path');

const cid = 'cq_q_9035375af7ddaf17003586327dbb6f2d';
const candidatePath = path.resolve(__dirname, '../../../candidates/answers', `${cid}.md`);
const md = fs.readFileSync(candidatePath, 'utf8');
const blocks = [...md.matchAll(/```javascript\n([\s\S]*?)\n```/g)];
if (blocks.length !== 1) throw new Error(`expected exactly one javascript implementation block, got ${blocks.length}`);
const code = blocks[0][1];

const required = [
  /import\s*\{\s*useEffect\s*,\s*useRef\s*\}\s*from\s*['"]react['"]/,
  /function\s+usePrevious\s*\(\s*value\s*\)/,
  /const\s+previousRef\s*=\s*useRef\s*\(\s*\)/,
  /useEffect\s*\(\s*\(\s*\)\s*=>\s*\{\s*previousRef\.current\s*=\s*value\s*;\s*\}\s*,\s*\[\s*value\s*\]\s*\)/s,
  /return\s+previousRef\.current\s*;/,
];
for (const pattern of required) {
  if (!pattern.test(code)) throw new Error(`candidate implementation missing ${pattern}`);
}
if (/useState\s*\(/.test(code)) throw new Error('baseline usePrevious candidate unexpectedly uses state');
if (/previousRef\.current\s*=\s*value[\s\S]*useEffect/.test(code)) {
  throw new Error('ref is overwritten before Effect declaration');
}

function model(values) {
  const UNSET = Symbol('unset');
  let stored = UNSET;
  let dependency = UNSET;
  const outputs = [];
  for (const value of values) {
    outputs.push(stored === UNSET ? undefined : stored);
    if (dependency === UNSET || !Object.is(dependency, value)) {
      stored = value;
      dependency = value;
    }
  }
  return outputs;
}

const objectA = { id: 'a' };
const objectB = { id: 'b' };
const cases = [
  { values: ['A', 'B', 'C'], expected: [undefined, 'A', 'B'] },
  { values: [1, 1, 2, 2, 3], expected: [undefined, 1, 1, 2, 2] },
  { values: [objectA, objectB], expected: [undefined, objectA] },
  { values: [undefined, 'X'], expected: [undefined, undefined] },
];
for (const { values, expected } of cases) {
  const actual = model(values);
  if (actual.length !== expected.length || actual.some((value, i) => !Object.is(value, expected[i]))) {
    throw new Error(`model mismatch: ${JSON.stringify(actual)} vs ${JSON.stringify(expected)}`);
  }
}

console.log('PASS implementation=useRef+useEffect initial=undefined sequence=A->B->C previous=undefined,A,B same-value=stable object-reference=preserved ref-update=no-state');
