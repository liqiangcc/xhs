'use strict';

function groupBy(items, keySelector) {
  if (!Array.isArray(items)) {
    throw new TypeError('items must be an array');
  }
  if (typeof keySelector !== 'function') {
    throw new TypeError('keySelector must be a function');
  }

  const groups = new Map();
  for (let index = 0; index < items.length; index += 1) {
    const item = items[index];
    const key = keySelector(item, index, items);
    const bucket = groups.get(key);
    if (bucket === undefined) {
      groups.set(key, [item]);
    } else {
      bucket.push(item);
    }
  }
  return groups;
}

module.exports = { groupBy };
