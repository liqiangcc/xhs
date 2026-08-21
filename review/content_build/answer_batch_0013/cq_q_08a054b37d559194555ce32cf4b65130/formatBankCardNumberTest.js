'use strict';

const { formatBankCardNumber } = require('./formatBankCardNumber');

const SEED = 0x08a054b3;

function oracle(digits) {
  let out = '';
  for (let i = 0; i < digits.length; i++) {
    out += digits[i];
    if ((i + 1) % 4 === 0 && i + 1 < digits.length) {
      out += ' ';
    }
  }
  return out;
}

function assertEqual(expected, actual, label) {
  if (expected !== actual) {
    throw new Error(`${label}: expected=${JSON.stringify(expected)} actual=${JSON.stringify(actual)}`);
  }
}

function assertThrows(fn, label) {
  try {
    fn();
    throw new Error(`${label}: expected TypeError`);
  } catch (error) {
    if (!(error instanceof TypeError)) {
      throw error;
    }
  }
}

function fixedCases() {
  const cases = [
    ['', ''],
    ['1', '1'],
    ['123', '123'],
    ['1234', '1234'],
    ['12345', '1234 5'],
    ['1234567812345678', '1234 5678 1234 5678'],
    ['1234567812345678123', '1234 5678 1234 5678 123'],
    ['000012340000', '0000 1234 0000'],
  ];
  for (const [input, expected] of cases) {
    assertEqual(expected, formatBankCardNumber(input), `fixed-${input}`);
  }
  assertThrows(() => formatBankCardNumber('1234 5678'), 'space-input');
  assertThrows(() => formatBankCardNumber('1234-5678'), 'hyphen-input');
  assertThrows(() => formatBankCardNumber('1234x567'), 'letter-input');
  assertThrows(() => formatBankCardNumber(12345678), 'number-input');
}

function lcg(seed) {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state;
  };
}

function randomizedCases() {
  const next = lcg(SEED);
  for (let round = 0; round < 5000; round++) {
    const length = next() % 65;
    let digits = '';
    for (let i = 0; i < length; i++) {
      digits += String(next() % 10);
    }
    assertEqual(oracle(digits), formatBankCardNumber(digits), `random-${round}`);
  }
}

fixedCases();
randomizedCases();
console.log('PASS fixed=8 invalid=4 randomized=5000 oracle=linear-scan');
