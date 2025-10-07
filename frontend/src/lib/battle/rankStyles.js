const RANK_STYLES = {
  prime: {
    label: 'Prime',
    shortLabel: 'PR',
    icon: '★',
    color: '#c0c0c0',
    tier: 'silver',
    slug: 'prime'
  },
  glitched: {
    label: 'Glitched',
    shortLabel: 'GL',
    icon: '◆',
    color: '#ff9de2',
    tier: 'gold',
    slug: 'glitched',
    glitch: true
  },
  'glitched prime': {
    label: 'Glitched Prime',
    shortLabel: 'GP',
    icon: '★',
    color: '#ffd700',
    tier: 'gold',
    slug: 'glitched-prime',
    glitch: true
  },
  boss: {
    label: 'Boss',
    shortLabel: 'B',
    icon: '♛',
    color: '#e5e4e2',
    tier: 'platinum',
    slug: 'boss'
  },
  'prime boss': {
    label: 'Prime Boss',
    shortLabel: 'PB',
    icon: '♛',
    color: '#f0ecff',
    tier: 'diamond',
    slug: 'prime-boss'
  },
  'glitched boss': {
    label: 'Glitched Boss',
    shortLabel: 'GB',
    icon: '◆',
    color: '#b9f2ff',
    tier: 'diamond',
    slug: 'glitched-boss',
    glitch: true
  },
  'glitched prime boss': {
    label: 'Glitched Prime Boss',
    shortLabel: 'GPB',
    icon: '♛',
    color: '#c6f3ff',
    tier: 'diamond',
    slug: 'glitched-prime-boss',
    glitch: true
  }
};

const OMITTED_RANKS = new Set(['', 'normal', 'common', 'standard', 'default']);

function titleCase(value) {
  return value
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function getRankStyle(rank) {
  if (rank == null) return null;
  const normalized = String(rank).trim();
  if (!normalized) return null;
  const lowered = normalized.toLowerCase();
  if (OMITTED_RANKS.has(lowered)) {
    return null;
  }

  const preset = RANK_STYLES[lowered];
  if (preset) {
    return { ...preset };
  }

  const label = titleCase(normalized);
  const slug = lowered.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'unknown';
  const shortLabel = label
    .split(' ')
    .map((part) => part.charAt(0))
    .join('')
    .slice(0, 3)
    .toUpperCase();

  return {
    label,
    shortLabel: shortLabel || label.slice(0, 2).toUpperCase(),
    icon: '★',
    color: '#cd7f32',
    tier: 'bronze',
    slug,
    fallback: true
  };
}
