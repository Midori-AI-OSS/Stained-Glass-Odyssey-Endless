import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

const partyView = readFileSync(join(import.meta.dir, '../src/lib/components/combat-viewer/PartyView.svelte'), 'utf8');
const foeView = readFileSync(join(import.meta.dir, '../src/lib/components/combat-viewer/FoeView.svelte'), 'utf8');
const hpStatus = readFileSync(join(import.meta.dir, '../src/lib/components/combat-viewer/HpStatus.svelte'), 'utf8');

describe('combat viewer modules', () => {
  test('PartyView lists party members', () => {
    expect(partyView).toContain('party-view');
  });
  test('FoeView lists foes', () => {
    expect(foeView).toContain('foe-view');
  });
  test('HpStatus displays hp percentage', () => {
    expect(hpStatus).toContain('hp-status');
  });
});
