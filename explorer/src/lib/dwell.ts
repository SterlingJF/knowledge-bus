export interface DwellClock {
  setTimeout(run: () => void, delay: number): unknown;
  clearTimeout(pending: unknown): void;
}

export interface Dwell<T> {
  shown(): T;
  offer(value: T): void;
  showNow(value: T): void;
}

const wallClock: DwellClock = {
  setTimeout: (run, delay) => globalThis.setTimeout(run, delay),
  clearTimeout: (pending) => globalThis.clearTimeout(pending as ReturnType<typeof globalThis.setTimeout>),
};

export function showAfterTheLastOfferRests<T>(first: T, rest: number, show: (value: T) => void, clock: DwellClock = wallClock): Dwell<T> {
  let shown = first;
  let pending: unknown = null;
  const forget = () => {
    if (pending !== null) clock.clearTimeout(pending);
    pending = null;
  };
  return {
    shown: () => shown,
    offer(value) {
      forget();
      if (value === shown) return;
      pending = clock.setTimeout(() => {
        pending = null;
        shown = value;
        show(value);
      }, rest);
    },
    showNow(value) {
      forget();
      shown = value;
    },
  };
}
