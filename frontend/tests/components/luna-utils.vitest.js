import { describe, expect, it } from 'vitest';
import { isCandidateLuna } from '$lib/components/battle/lunaUtils.js';

describe('isCandidateLuna', () => {
  it('matches the plain luna identifier', () => {
    expect(isCandidateLuna('luna')).toBe(true);
  });

  it('matches identifiers with a luna_ prefix', () => {
    expect(isCandidateLuna('luna_blade')).toBe(true);
    expect(isCandidateLuna('LUNA_SPELL')).toBe(true);
  });

  it('matches sword-specific identifiers', () => {
    expect(isCandidateLuna('luna_sword_alpha')).toBe(true);
    expect(isCandidateLuna('player:luna_sword_beta')).toBe(true);
  });

  it('ignores unrelated identifiers', () => {
    expect(isCandidateLuna('lunatic')).toBe(false);
    expect(isCandidateLuna('seluna')).toBe(false);
    expect(isCandidateLuna('sword_master')).toBe(false);
  });
});
