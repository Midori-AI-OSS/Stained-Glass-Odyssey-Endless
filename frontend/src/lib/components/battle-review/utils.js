import { getElementColor } from '../../systems/assetLoader.js';

export const effectTooltips = {
  aftertaste: 'Deals a hit with random damage type (10% to 150% damage)',
  critical_boost: '+0.5% crit rate and +5% crit damage per stack. Removed when taking damage.',
  critboost: '+0.5% crit rate and +5% crit damage per stack. Removed when taking damage.',
  iron_guard: '+55% DEF; damage grants all allies +10% DEF for 1 turn.',
  phantom_ally: 'Summons a phantom copy of a random party member for one battle.',
  arc_lightning: 'Lightning attacks have a 50% chance to chain to another random foe for 50% damage.',
  critical_focus: 'Low HP allies gain +25% critical hit rate.',
  elemental_spark: 'One random ally gains +5% effect hit rate until they take damage.'
};

export function fmt(n) {
  try {
    return Number(n).toLocaleString();
  } catch {
    return String(n ?? 0);
  }
}

export function getElementBarColor(element) {
  const key = String(element || '').toLowerCase();
  const colorMap = {
    fire: '#ff6b35',
    ice: '#4fb3ff',
    lightning: '#ffd93d',
    wind: '#7dd3c0',
    light: '#fff2b3',
    dark: '#9b59b6',
    generic: '#8e44ad'
  };
  return colorMap[key] || getElementColor(element) || '#8e44ad';
}
