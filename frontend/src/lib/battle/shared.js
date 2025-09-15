export function hpPercent(hp, maxHp) {
  const max = Number(maxHp) || 1;
  return Math.max(0, Math.min(1, (Number(hp) || 0) / max));
}
