'use strict';

function createIntervalApi(setTimeoutFn = setTimeout, clearTimeoutFn = clearTimeout) {
  const states = new WeakMap();

  function setIntervalPolyfill(callback, delay) {
    if (typeof callback !== 'function') throw new TypeError('callback must be a function');
    const handle = Object.freeze({});
    const state = { active: true, timer: null };
    states.set(handle, state);

    const schedule = () => {
      if (!state.active) return;
      state.timer = setTimeoutFn(tick, delay);
    };
    const tick = () => {
      if (!state.active) return;
      try {
        callback();
      } finally {
        if (state.active) schedule();
        else state.timer = null;
      }
    };

    schedule();
    return handle;
  }

  function clearIntervalPolyfill(handle) {
    const state = states.get(handle);
    if (!state || !state.active) return;
    state.active = false;
    if (state.timer !== null) {
      clearTimeoutFn(state.timer);
      state.timer = null;
    }
  }

  return { setIntervalPolyfill, clearIntervalPolyfill };
}

module.exports = { createIntervalApi };
