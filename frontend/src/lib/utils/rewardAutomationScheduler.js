const DEFAULT_DELAY_BOUNDS = {
  'ack-loot': {
    normal: [600, 900],
    reduced: [260, 420]
  },
  'select-card': {
    normal: [750, 1200],
    reduced: [320, 480]
  },
  'confirm-card': {
    normal: [520, 820],
    reduced: [260, 420]
  },
  'select-relic': {
    normal: [750, 1200],
    reduced: [320, 480]
  },
  'confirm-relic': {
    normal: [520, 820],
    reduced: [260, 420]
  },
  advance: {
    normal: [520, 780],
    reduced: [240, 360]
  },
  'next-room': {
    normal: [650, 950],
    reduced: [300, 460]
  },
  default: {
    normal: [500, 720],
    reduced: [220, 320]
  }
};

function clamp01(value) {
  if (!Number.isFinite(value)) return 0;
  if (value <= 0) return 0;
  if (value >= 1) return 1;
  return value;
}

function pickDelay(bounds, reducedMotion, random = Math.random) {
  const [min, max] = reducedMotion ? bounds.reduced : bounds.normal;
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return 0;
  }
  if (max <= min) {
    return Math.round(min);
  }
  const roll = clamp01(typeof random === 'function' ? random() : Math.random());
  const value = min + (max - min) * roll;
  return Math.round(value);
}

export function resolveAutomationDelay(action, { reducedMotion = false, random = Math.random } = {}) {
  if (!action || typeof action.type !== 'string') {
    const fallback = DEFAULT_DELAY_BOUNDS.default;
    return pickDelay(fallback, reducedMotion, random);
  }
  const typeKey = action.type in DEFAULT_DELAY_BOUNDS ? action.type : 'default';
  const bounds = DEFAULT_DELAY_BOUNDS[typeKey] || DEFAULT_DELAY_BOUNDS.default;
  return pickDelay(bounds, reducedMotion, random);
}

export function actionsEqual(a, b) {
  if (a === b) return true;
  if (!a || !b) return false;
  if (a.type !== b.type) return false;
  if (a.type === 'select-card' || a.type === 'select-relic') {
    const aId = a.choice?.id ?? a.choice?.value ?? null;
    const bId = b.choice?.id ?? b.choice?.value ?? null;
    if (aId !== bId) return false;
  }
  if (a.type === 'confirm-card' || a.type === 'confirm-relic') {
    return true;
  }
  if (a.type === 'advance') {
    if ((a.phase ?? null) !== (b.phase ?? null)) {
      return false;
    }
  }
  return true;
}

export class RewardAutomationScheduler {
  constructor({
    getDelay = resolveAutomationDelay,
    equals = actionsEqual,
    setTimeoutFn = (fn, delay) => setTimeout(fn, delay),
    clearTimeoutFn = (handle) => clearTimeout(handle)
  } = {}) {
    this._getDelay = getDelay;
    this._equals = equals;
    this._setTimeout = setTimeoutFn;
    this._clearTimeout = clearTimeoutFn;
    this._reducedMotion = false;
    this._timer = null;
    this._pending = null;
    this._running = false;
    this._token = 0;
  }

  updateReducedMotion(value) {
    this._reducedMotion = Boolean(value);
  }

  cancel() {
    if (this._timer) {
      try {
        this._clearTimeout(this._timer);
      } catch {
        /* ignore */
      }
      this._timer = null;
    }
    this._pending = null;
    this._token += 1;
  }

  isBusy() {
    return this._running;
  }

  getPendingAction() {
    return this._pending;
  }

  schedule(action, { execute, validate, onSettled } = {}) {
    if (!action || action.type === 'none') {
      this.cancel();
      return;
    }
    if (this._running) {
      return;
    }
    if (this._pending && this._equals(this._pending, action)) {
      return;
    }
    this.cancel();
    if (typeof execute !== 'function') {
      throw new Error('RewardAutomationScheduler.schedule requires an execute callback');
    }
    const delay = this._getDelay(action, {
      reducedMotion: this._reducedMotion
    });
    const token = ++this._token;
    this._pending = action;
    this._timer = this._setTimeout(async () => {
      if (token !== this._token) {
        return;
      }
      this._timer = null;
      this._running = true;
      try {
        if (!validate || validate(action)) {
          await execute(action);
        }
      } catch (error) {
        console.error('Idle automation action failed', error);
      } finally {
        this._running = false;
        this._pending = null;
        if (typeof onSettled === 'function') {
          try {
            onSettled();
          } catch {
            /* ignore */
          }
        }
      }
    }, Math.max(0, delay));
  }
}

export const __INTERNAL_DELAY_BOUNDS__ = DEFAULT_DELAY_BOUNDS;
