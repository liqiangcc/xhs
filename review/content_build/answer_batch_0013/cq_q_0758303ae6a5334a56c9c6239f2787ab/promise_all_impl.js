'use strict';

function interviewPromiseAll(iterable) {
  return new Promise((resolve, reject) => {
    const values = [];
    let remaining = 0;
    let index = 0;

    for (const item of iterable) {
      const currentIndex = index++;
      remaining++;
      Promise.resolve(item).then(
        (value) => {
          values[currentIndex] = value;
          remaining--;
          if (remaining === 0) resolve(values);
        },
        reject,
      );
    }

    if (index === 0) resolve([]);
  });
}

module.exports = { interviewPromiseAll };
