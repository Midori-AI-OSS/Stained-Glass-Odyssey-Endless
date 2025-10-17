import { toNumber } from './rewardPreview.js';

const MODE_VALUES = new Set(['percent', 'flat', 'multiplier']);

const TARGET_LABELS = {
  party: 'Party',
  allies: 'Allies',
  foe: 'Foes',
  foes: 'Foes',
  self: 'Self',
  run: 'the run'
};

const STAT_LABEL_OVERRIDES = {
  atk: 'Attack',
  attack: 'Attack',
  def: 'Defense',
  defense: 'Defense',
  max_hp: 'Max HP',
  hp: 'HP',
  mitigation: 'Mitigation',
  crit_rate: 'Crit Rate',
  crit_damage: 'Crit Damage',
  effect_hit_rate: 'Effect Hit Rate',
  effect_resistance: 'Effect Resist',
  dodge_odds: 'Dodge Odds',
  regen: 'Regen',
  regain: 'Regain',
  speed: 'Speed'
};

function cleanString(value) {
  if (typeof value !== 'string') return '';
  return value.trim();
}

function normaliseMode(rawMode) {
  const mode = cleanString(rawMode).toLowerCase();
  return MODE_VALUES.has(mode) ? mode : 'percent';
}

function normaliseTarget(rawTarget) {
  const target = cleanString(rawTarget).toLowerCase();
  return target || 'party';
}

function safeNumber(value) {
  const numeric = toNumber(value, null);
  return numeric == null ? null : numeric;
}

function toTitleCase(identifier) {
  if (!identifier) return '';
  return identifier
    .split(/[_\-\s]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1).toLowerCase())
    .join(' ');
}

function formatStatName(stat) {
  const key = cleanString(stat).toLowerCase();
  if (!key) return 'Stat';
  if (STAT_LABEL_OVERRIDES[key]) {
    return STAT_LABEL_OVERRIDES[key];
  }
  return toTitleCase(key);
}

function formatTargetLabel(target) {
  const key = normaliseTarget(target);
  const mapped = TARGET_LABELS[key];
  if (mapped) {
    return mapped;
  }
  return toTitleCase(key || 'party');
}

function stripTrailingZeros(value) {
  return value.replace(/\.0+$/u, '').replace(/(\.\d*?)0+$/u, '$1');
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return null;
  const abs = Math.abs(value);
  const decimals = abs === 0 ? 0 : abs < 1 ? 2 : abs < 10 ? 1 : 0;
  const formatted = stripTrailingZeros(abs.toFixed(decimals));
  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  return `${sign}${formatted}%`;
}

function formatFlat(value) {
  if (!Number.isFinite(value)) return null;
  const abs = Math.abs(value);
  const decimals = Number.isInteger(value) ? 0 : abs < 1 ? 2 : abs < 10 ? 1 : 0;
  const formatted = stripTrailingZeros(abs.toFixed(decimals));
  const sign = value > 0 ? '+' : value < 0 ? '-' : '';
  return `${sign}${formatted}`;
}

function formatMultiplier(value) {
  if (!Number.isFinite(value)) return null;
  const decimals = Math.abs(value - Math.round(value)) > 0.001 ? 2 : 0;
  const formatted = stripTrailingZeros(Math.abs(value).toFixed(decimals));
  return `×${formatted}`;
}

function formatAmount(value, mode) {
  const normalisedMode = normaliseMode(mode);
  if (normalisedMode === 'flat') {
    return formatFlat(value);
  }
  if (normalisedMode === 'multiplier') {
    return formatMultiplier(value);
  }
  return formatPercent(value);
}

function normaliseStatEntry(entry) {
  if (!entry || typeof entry !== 'object') {
    return null;
  }
  const statName = cleanString(entry.stat);
  if (!statName) {
    return null;
  }
  const mode = normaliseMode(entry.mode);
  const amount = safeNumber(entry.amount);
  const totalAmount = safeNumber(entry.total_amount);
  const previousTotal = safeNumber(entry.previous_total);
  const stacks = Math.max(1, Math.floor(toNumber(entry.stacks, 1) || 1));
  const target = normaliseTarget(entry.target);

  return {
    stat: statName,
    mode,
    amount,
    total_amount: totalAmount,
    previous_total: previousTotal,
    stacks,
    target
  };
}

function normaliseTrigger(entry) {
  if (!entry || typeof entry !== 'object') {
    return null;
  }
  const event = cleanString(entry.event);
  if (!event) {
    return null;
  }
  const description = cleanString(entry.description) || null;
  return { event, description };
}

export function normalizeRewardPreview(source) {
  if (!source || typeof source !== 'object') {
    return {
      summary: null,
      stats: [],
      triggers: []
    };
  }

  const summaryText = cleanString(source.summary) || null;

  const stats = Array.isArray(source.stats)
    ? source.stats
        .map(normaliseStatEntry)
        .filter((entry) => entry !== null)
    : [];

  const triggers = Array.isArray(source.triggers)
    ? source.triggers
        .map(normaliseTrigger)
        .filter((entry) => entry !== null)
    : [];

  return {
    summary: summaryText,
    stats,
    triggers
  };
}

function buildStatDisplay(stat, index) {
  if (!stat) return null;
  const label = formatStatName(stat.stat);
  const targetLabel = formatTargetLabel(stat.target);
  const total = Number.isFinite(stat.total_amount) ? stat.total_amount : null;
  const perStack = Number.isFinite(stat.amount) ? stat.amount : null;
  const effective = total != null ? total : perStack;
  if (effective == null) {
    return null;
  }
  const change = formatAmount(effective, stat.mode);
  if (!change) {
    return null;
  }

  const changeText = targetLabel ? `${change} to ${targetLabel}` : change;
  const details = [];

  if (stat.stacks > 1) {
    if (perStack != null) {
      const perStackText = formatAmount(perStack, stat.mode);
      if (perStackText) {
        details.push(`Per stack ${perStackText}`);
      }
    }
    details.push(`Stacks ${stat.stacks}`);
  }

  if (
    total != null &&
    stat.previous_total != null &&
    Math.abs(stat.previous_total - total) > 1e-6
  ) {
    const previousText = formatAmount(stat.previous_total, stat.mode);
    if (previousText) {
      details.push(`Previously ${previousText}`);
    }
  }

  return {
    id: `${stat.stat}-${index}`,
    label,
    change: changeText,
    details
  };
}

function buildTriggerDisplay(trigger, index) {
  if (!trigger) return null;
  const eventName = toTitleCase(trigger.event);
  return {
    id: `${trigger.event}-${index}`,
    event: eventName || 'Event',
    description: trigger.description || null
  };
}

export function formatRewardPreview(source, options = {}) {
  const normalized = normalizeRewardPreview(source);
  const fallbackSummary = options.fallbackSummary ? cleanString(options.fallbackSummary) : '';
  const summary = normalized.summary || fallbackSummary || null;

  const stats = normalized.stats
    .map((entry, index) => buildStatDisplay(entry, index))
    .filter((entry) => entry !== null);

  const triggers = normalized.triggers
    .map((entry, index) => buildTriggerDisplay(entry, index))
    .filter((entry) => entry !== null);

  const hasContent = Boolean((summary && summary.length > 0) || stats.length > 0 || triggers.length > 0);

  return {
    summary,
    stats,
    triggers,
    hasContent
  };
}
