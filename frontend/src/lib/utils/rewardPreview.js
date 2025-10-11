export function toNumber(value, fallback = null) {
  if (value == null) return fallback;
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}

export function computeModifierRewardContribution(mod, stacks) {
  const totals = {
    foe_bonus: 0,
    player_bonus: 0,
    exp_bonus: 0,
    rdr_bonus: 0
  };

  if (!mod || !mod.reward_bonuses || typeof mod.reward_bonuses !== 'object') {
    return totals;
  }

  const bonuses = mod.reward_bonuses;
  const stackCount = Number.isFinite(Number(stacks)) ? Number(stacks) : 0;

  const perStackExp = toNumber(bonuses.exp_bonus_per_stack, 0) || 0;
  const perStackRdr = toNumber(bonuses.rdr_bonus_per_stack, 0) || 0;

  if (mod.grants_reward_bonus) {
    const foePerStack = perStackExp || perStackRdr;
    if (foePerStack) {
      totals.foe_bonus += stackCount * foePerStack;
    }
  }

  if (perStackExp) {
    totals.exp_bonus += stackCount * perStackExp;
  }

  if (perStackRdr) {
    totals.rdr_bonus += stackCount * perStackRdr;
  }

  const firstExp = toNumber(bonuses.exp_bonus_first_stack, 0) || 0;
  if (firstExp && stackCount > 0) {
    totals.exp_bonus += firstExp;
    const additionalExp = toNumber(bonuses.exp_bonus_additional_stack, 0) || 0;
    if (additionalExp && stackCount > 1) {
      totals.exp_bonus += (stackCount - 1) * additionalExp;
    }
  }

  const firstRdr = toNumber(bonuses.rdr_bonus_first_stack, 0) || 0;
  if (firstRdr && stackCount > 0) {
    totals.rdr_bonus += firstRdr;
    const additionalRdr = toNumber(bonuses.rdr_bonus_additional_stack, 0) || 0;
    if (additionalRdr && stackCount > 1) {
      totals.rdr_bonus += (stackCount - 1) * additionalRdr;
    }
    if (!mod.grants_reward_bonus) {
      totals.player_bonus += firstRdr;
      if (additionalRdr && stackCount > 1) {
        totals.player_bonus += (stackCount - 1) * additionalRdr;
      }
    }
  }

  if (!mod.grants_reward_bonus && mod.id === 'character_stat_down') {
    totals.player_bonus = totals.rdr_bonus;
  }

  return totals;
}

export function computeRewardPreview(values, availableModifiers = [], options = {}) {
  const result = {
    foe_bonus: 0,
    player_bonus: 0,
    exp_bonus: 0,
    rdr_bonus: 0
  };

  if (!Array.isArray(availableModifiers) || availableModifiers.length === 0) {
    return result;
  }

  const sanitize =
    typeof options.sanitizeStack === 'function'
      ? options.sanitizeStack
      : (_, rawValue) => {
          const numeric = Number(rawValue);
          return Number.isFinite(numeric) ? numeric : 0;
        };

  const modifierValues = values || {};

  for (const entry of availableModifiers) {
    if (!entry || typeof entry !== 'object') continue;
    const stacks = sanitize(entry.id, modifierValues[entry.id]);
    const contribution = computeModifierRewardContribution(entry, stacks);
    result.foe_bonus += contribution.foe_bonus;
    result.player_bonus += contribution.player_bonus;
    result.exp_bonus += contribution.exp_bonus;
    result.rdr_bonus += contribution.rdr_bonus;
  }

  result.foe_bonus = Number(result.foe_bonus.toFixed(4));
  result.player_bonus = Number(result.player_bonus.toFixed(4));
  result.exp_bonus = Number(result.exp_bonus.toFixed(4));
  result.rdr_bonus = Number(result.rdr_bonus.toFixed(4));

  return result;
}
