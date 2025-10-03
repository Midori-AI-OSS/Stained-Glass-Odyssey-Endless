function coerceBattleIndex(entry, fallback) {
  const candidates = [
    entry?.battle_index,
    entry?.battleIndex,
    entry?.index,
    entry?.battle?.index,
    entry?.id,
  ];

  for (const candidate of candidates) {
    const n = Number(candidate);
    if (Number.isFinite(n) && n > 0) {
      return Math.floor(n);
    }
  }

  return fallback ?? null;
}

function deriveFightLabel(entry, fallbackIndex) {
  const candidates = [
    entry?.battle_name,
    entry?.battleName,
    entry?.room_name,
    entry?.roomName,
    entry?.room_type,
    entry?.roomType,
  ];

  for (const candidate of candidates) {
    if (candidate) {
      return String(candidate);
    }
  }

  return `Fight ${fallbackIndex}`;
}

export function deriveFightsFromRunDetails(runDetails) {
  const summaries =
    runDetails?.battles ??
    runDetails?.battle_summaries ??
    runDetails?.battleSummaries ??
    [];

  if (!Array.isArray(summaries) || summaries.length === 0) {
    return [];
  }

  return summaries.map((summary, idx) => {
    const fallback = idx + 1;
    const battleIndex = coerceBattleIndex(summary, fallback);

    return {
      battleIndex,
      label: deriveFightLabel(summary, battleIndex || fallback),
      summary,
    };
  });
}

export { coerceBattleIndex as deriveBattleIndex, deriveFightLabel };
