function hasLootAvailable(roomData) {
  if (!roomData || typeof roomData.loot !== 'object' || roomData.loot === null) {
    return false;
  }
  const gold = Number(roomData.loot.gold ?? 0);
  const items = Array.isArray(roomData.loot.items) ? roomData.loot.items : [];
  return gold > 0 || items.length > 0;
}

function shouldUseLegacyAutomation(snapshot) {
  if (!snapshot) return true;
  if (!Array.isArray(snapshot.sequence) || snapshot.sequence.length === 0) return true;
  if (!snapshot.current) return true;
  const diagnostics = Array.isArray(snapshot.diagnostics) ? snapshot.diagnostics : [];
  if (diagnostics.length > 0) return true;
  return false;
}

function computeLegacyAction({ roomData, stagedCards, stagedRelics }) {
  if (!roomData) return { type: 'none' };

  if (Array.isArray(roomData.card_choices) && roomData.card_choices.length > 0) {
    return { type: 'select-card', choice: roomData.card_choices[0] };
  }

  if (roomData.awaiting_card && Array.isArray(stagedCards) && stagedCards.length > 0) {
    return { type: 'confirm-card' };
  }

  if (!roomData.awaiting_card && Array.isArray(roomData.relic_choices) && roomData.relic_choices.length > 0) {
    return { type: 'select-relic', choice: roomData.relic_choices[0] };
  }

  if (roomData.awaiting_relic && Array.isArray(stagedRelics) && stagedRelics.length > 0) {
    return { type: 'confirm-relic' };
  }

  if (roomData.awaiting_loot || hasLootAvailable(roomData)) {
    return { type: 'ack-loot' };
  }

  if (roomData.result === 'shop') {
    return { type: 'next-room' };
  }

  if (roomData.awaiting_next) {
    return { type: 'next-room' };
  }

  return { type: 'none' };
}

function computePhaseAction({ roomData, snapshot, stagedCards, stagedRelics }) {
  if (!roomData || !snapshot || !snapshot.current) {
    return computeLegacyAction({ roomData, stagedCards, stagedRelics });
  }

  const phase = snapshot.current;

  switch (phase) {
    case 'drops': {
      if (roomData.awaiting_loot || hasLootAvailable(roomData) || roomData.awaiting_next) {
        return { type: 'advance', phase };
      }
      break;
    }
    case 'cards': {
      if (roomData.awaiting_card && stagedCards.length > 0) {
        return { type: 'confirm-card', phase };
      }
      if (Array.isArray(roomData.card_choices) && roomData.card_choices.length > 0) {
        return { type: 'select-card', choice: roomData.card_choices[0] };
      }
      if (!roomData.awaiting_card && stagedCards.length === 0 && ((roomData.card_choices?.length || 0) === 0)) {
        return { type: 'advance', phase };
      }
      break;
    }
    case 'relics': {
      if (roomData.awaiting_relic && stagedRelics.length > 0) {
        return { type: 'confirm-relic', phase };
      }
      if (!roomData.awaiting_card && Array.isArray(roomData.relic_choices) && roomData.relic_choices.length > 0) {
        return { type: 'select-relic', choice: roomData.relic_choices[0] };
      }
      if (!roomData.awaiting_relic && stagedRelics.length === 0 && ((roomData.relic_choices?.length || 0) === 0)) {
        return { type: 'advance', phase };
      }
      break;
    }
    case 'battle_review': {
      if (roomData.awaiting_next || !snapshot.next) {
        return { type: 'advance', phase };
      }
      break;
    }
    default: {
      break;
    }
  }

  if (roomData.awaiting_next && !hasLootAvailable(roomData)) {
    return { type: 'advance', phase };
  }

  if (roomData.result === 'shop') {
    return { type: 'next-room' };
  }

  return { type: 'none' };
}

function computeAutomationAction({ roomData, snapshot, stagedCards = [], stagedRelics = [] } = {}) {
  if (shouldUseLegacyAutomation(snapshot)) {
    return computeLegacyAction({ roomData, stagedCards, stagedRelics });
  }

  return computePhaseAction({ roomData, snapshot, stagedCards, stagedRelics });
}

export {
  computeAutomationAction,
  hasLootAvailable,
  shouldUseLegacyAutomation
};
