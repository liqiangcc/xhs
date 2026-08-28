'use strict';

class EventEmitter {
  constructor() {
    this.events = new Map();
  }

  on(event, listener) {
    this.#assertListener(listener);
    const list = this.events.get(event) ?? [];
    list.push({ listener, original: listener, once: false });
    this.events.set(event, list);
    return this;
  }

  once(event, listener) {
    this.#assertListener(listener);
    const list = this.events.get(event) ?? [];
    list.push({ listener, original: listener, once: true });
    this.events.set(event, list);
    return this;
  }

  off(event, listener) {
    this.#assertListener(listener);
    const list = this.events.get(event);
    if (!list) return this;

    const next = list.filter(record => record.original !== listener);
    if (next.length === 0) this.events.delete(event);
    else this.events.set(event, next);
    return this;
  }

  emit(event, ...args) {
    const list = this.events.get(event);
    if (!list || list.length === 0) return false;

    const snapshot = [...list];
    for (const record of snapshot) {
      if (record.once) this.#removeRecord(event, record);
      record.listener.apply(this, args);
    }
    return true;
  }

  #removeRecord(event, target) {
    const list = this.events.get(event);
    if (!list) return;
    const next = list.filter(record => record !== target);
    if (next.length === 0) this.events.delete(event);
    else this.events.set(event, next);
  }

  #assertListener(listener) {
    if (typeof listener !== 'function') {
      throw new TypeError('listener must be a function');
    }
  }
}

module.exports = { EventEmitter };
