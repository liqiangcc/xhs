export function debounce<TThis, TArgs extends unknown[]>(
  fn: (this: TThis, ...args: TArgs) => void,
  waitMs: number,
  immediate = false,
): (this: TThis, ...args: TArgs) => void {
  if (!Number.isFinite(waitMs) || waitMs < 0) {
    throw new RangeError('waitMs must be a finite non-negative number');
  }

  let timer: ReturnType<typeof setTimeout> | undefined;

  return function (this: TThis, ...args: TArgs): void {
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
