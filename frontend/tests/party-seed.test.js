import { describe, expect, test } from 'bun:test';
import { deriveSeedParty, sanitizePartyIds } from '../src/lib/systems/partySeed.js';

describe('party seeding helpers', () => {
  test('sanitizePartyIds removes placeholders, summons, and duplicates', () => {
    const result = sanitizePartyIds([
      'alpha',
      'sample_player',
      { id: 'beta' },
      { name: 'alpha' },
      { id: 'summoned', summon_type: 'golem' },
      { player_id: 'gamma' },
    ]);
    expect(result).toEqual(['alpha', 'beta', 'gamma']);
  });

  test('deriveSeedParty preserves existing sanitized parties', () => {
    const existing = ['omega'];
    expect(deriveSeedParty(existing, [])).toEqual(['omega']);
  });

  test('deriveSeedParty removes placeholders from persisted parties', () => {
    const roster = [{ id: 'hero', owned: true, is_player: true }];
    expect(deriveSeedParty(['sample_player', 'hero'], roster)).toEqual(['hero']);
  });

  test('deriveSeedParty prefers playable roster metadata', () => {
    const roster = [
      { id: 'npc-1', owned: false, is_player: false },
      { id: 'hero', owned: true, is_player: true },
      { id: 'backup', owned: true, is_player: false },
    ];
    expect(deriveSeedParty([], roster)).toEqual(['hero']);
  });

  test('deriveSeedParty falls back to first selectable entry', () => {
    const roster = [
      { id: 'blocked', owned: true, is_player: false, ui: { non_selectable: true } },
      { id: 'gr-zero', owned: true, stats: { gacha_rarity: 0 } },
      { id: 'approved', owned: true, stats: { gacha_rarity: 0 }, ui: { allow_select: true } },
    ];
    expect(deriveSeedParty([], roster)).toEqual(['approved']);
  });

  test('deriveSeedParty returns empty when nothing is selectable', () => {
    const roster = [
      { id: 'locked', owned: false, is_player: false },
      { id: 'summon', owned: true, ui: { non_selectable: true } },
    ];
    expect(deriveSeedParty([], roster)).toEqual([]);
  });
});
