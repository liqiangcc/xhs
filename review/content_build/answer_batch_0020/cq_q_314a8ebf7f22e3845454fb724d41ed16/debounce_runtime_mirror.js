'use strict';

function debounce(fn, waitMs, immediate = false) {
  if (!Number.isFinite(waitMs) || waitMs < 0) {
    throw new RangeError('waitMs must be a finite non-negative number');
  }

  let timer;
  return function (...args) {
    const callNow = immediate && timer === undefined;
    if (timer !== undefined) clearTimeout(timer);

    const receiver = this;
    timer = setTimeout(() => {
      timer = undefined;
      if (!immediate) fn.apply(receiver, args);
    }, waitMs);

    if (callNow) fn.apply(receiver, args);
  };
}

module.exports = { debounce };
