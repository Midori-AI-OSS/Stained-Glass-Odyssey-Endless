import { isSummon } from './summonManager.js';

const PLACEHOLDER_IDS = new Set(['sample_player']);

function readId(entry) {
  if (typeof entry === 'string') {
    return entry;
  }
  if (!entry || typeof entry !== 'object') {
    return '';
  }
  if (entry.player_id != null && entry.player_id !== '') {
    return entry.player_id;
  }
  if (entry.id != null && entry.id !== '') {
    return entry.id;
  }
  if (entry.name != null && entry.name !== '') {
    return entry.name;
  }
  return '';
}

export function sanitizePartyIds(party) {
  if (!Array.isArray(party)) {
    return [];
  }
  const sanitized = [];
  const seen = new Set();
  for (const entry of party) {
    if (isSummon(entry)) {
      continue;
    }
    const id = String(readId(entry) || '').trim();
    if (!id) {
      continue;
    }
    const key = id.toLowerCase();
    if (PLACEHOLDER_IDS.has(key)) {
      continue;
    }
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    sanitized.push(id);
  }
  return sanitized;
}

function isSelectable(entry) {
  if (!entry || typeof entry !== 'object') return false;
  const id = entry.id ?? entry.name;
  if (!id) return false;
  const meta = entry.ui && typeof entry.ui === 'object' ? entry.ui : {};
  if (meta.non_selectable === true) return false;
  const rarity = Number(entry?.stats?.gacha_rarity);
  if (!Number.isNaN(rarity) && rarity === 0 && meta.allow_select !== true) {
    return false;
  }
  if (entry.owned || entry.is_player) {
    return true;
  }
  return false;
}

export function deriveSeedParty(currentParty, rosterPlayers = []) {
  const sanitized = sanitizePartyIds(currentParty);
  if (sanitized.length > 0) {
    return sanitized;
  }
  const playable = Array.isArray(rosterPlayers) ? rosterPlayers.filter(isSelectable) : [];
  if (!playable.length) {
    return [];
  }
  const prioritized = playable.find((p) => p?.is_player) ?? playable[0];
  const id = prioritized?.id ?? prioritized?.name;
  if (!id) {
    return [];
  }
  return [String(id)];
}

export const PARTY_PLACEHOLDERS = new Set(PLACEHOLDER_IDS);
