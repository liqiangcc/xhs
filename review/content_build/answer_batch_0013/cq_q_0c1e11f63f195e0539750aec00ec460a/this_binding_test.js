const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, 'this_binding_snippet.js'), 'utf8');

function runClassicScript(code) {
  const logs = [];
  const context = {
    console: { log(value) { logs.push(value); } },
  };
  context.window = context;
  vm.createContext(context);
  vm.runInContext(code, context, { filename: 'this_binding_snippet.js' });
  return logs;
}

assert.deepEqual(runClassicScript(source), ['A', 'B', 'v']);

const strictVariant = `"use strict";\n${source}`;
assert.throws(
  () => runClassicScript(strictVariant),
  (error) => error && error.name === 'TypeError'
);

console.log('PASS classic=A,B,v strict=objC-call-TypeError');
