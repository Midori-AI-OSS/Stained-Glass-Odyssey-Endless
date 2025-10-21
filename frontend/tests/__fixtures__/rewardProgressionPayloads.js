export function fourPhaseProgression(overrides = {}) {
  return {
    available: ['drops', 'cards', 'relics', 'battle_review'],
    completed: [],
    current_step: 'drops',
    diagnostics: [],
    ...overrides
  };
}

export function afterDropsProgression(overrides = {}) {
  return fourPhaseProgression({
    completed: ['drops'],
    current_step: 'cards',
    ...overrides
  });
}

export function afterCardsProgression(overrides = {}) {
  return fourPhaseProgression({
    completed: ['drops', 'cards'],
    current_step: 'relics',
    ...overrides
  });
}

export function afterRelicsProgression(overrides = {}) {
  return fourPhaseProgression({
    completed: ['drops', 'cards', 'relics'],
    current_step: 'battle_review',
    ...overrides
  });
}

export function skipCardsProgression(overrides = {}) {
  return {
    available: ['drops', 'relics', 'battle_review'],
    completed: ['drops'],
    current_step: 'relics',
    diagnostics: [],
    ...overrides
  };
}

export function singlePhaseProgression(overrides = {}) {
  return {
    available: ['battle_review'],
    completed: [],
    current_step: 'battle_review',
    diagnostics: [],
    ...overrides
  };
}
