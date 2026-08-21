import { useState } from 'react';

export function usePrevious(value) {
  const [history, setHistory] = useState(() => ({
    current: value,
    previous: undefined,
  }));

  if (!Object.is(history.current, value)) {
    const previous = history.current;
    setHistory({ current: value, previous });
    return previous;
  }

  return history.previous;
}
