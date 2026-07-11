'use strict';

const assert = require('node:assert/strict');

class Model {
    constructor() {
        this.db = new Map([['profile:7', { version: 1, name: 'old' }]]);
        this.cache = new Map([['profile:7', { version: 1, name: 'old' }]]);
        this.outbox = [];
        this.completedEventIds = new Set();
    }

    commitChange(key, value) {
        const next = { version: this.db.get(key).version + 1, ...value };
        const event = { eventId: `${key}:${next.version}`, key, version: next.version };
        this.db.set(key, next);
        this.outbox.push(event);
        return event;
    }

    invalidate(event) {
        // A Redis DEL-style invalidation is safe for an absent key. Tracking the
        // event only prevents needless delivery work; repeating deletion is valid.
        this.cache.delete(event.key);
        this.completedEventIds.add(event.eventId);
    }

    readThrough(key) {
        if (!this.cache.has(key)) this.cache.set(key, this.db.get(key));
        return this.cache.get(key);
    }
}

const model = new Model();
const event = model.commitChange('profile:7', { name: 'new' });
assert.equal(model.cache.get('profile:7').name, 'old', 'a committed DB write may precede invalidation');
model.invalidate(event);
model.invalidate(event);
assert.equal(model.cache.has('profile:7'), false, 'duplicate invalidation keeps the cache absent');
assert.deepEqual(model.readThrough('profile:7'), { version: 2, name: 'new' }, 'post-invalidation refill reads the DB version');
assert.equal(model.completedEventIds.has(event.eventId), true, 'event completion can be recorded for retries');
