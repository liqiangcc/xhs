'use strict';

function myPromiseAll(iterable) {
  return new Promise((resolve, reject) => {
    const results = [];
    let remaining = 1;
    let index = 0;

    for (const value of iterable) {
      const currentIndex = index++;
      results.push(undefined);
      remaining++;

      Promise.resolve(value).then(
        (resolvedValue) => {
          results[currentIndex] = resolvedValue;
          remaining--;
          if (remaining === 0) {
            resolve(results);
          }
        },
        reject,
      );
    }

    remaining--;
    if (remaining === 0) {
      resolve(results);
    }
  });
}

module.exports = { myPromiseAll };
