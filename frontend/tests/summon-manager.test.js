import { describe, expect, it, vi } from 'vitest';
import {
  createSummonManager,
  filterPartyEntities,
  isSummon,
} from '../src/lib/systems/summonManager.js';

function createManager() {
  return createSummonManager({
    combatantKey: (kind, id, ownerId) => `${kind}:${ownerId}:${id}`,
    resolveEntityElement: (entity) => entity?.element ?? 'generic',
    applyLunaSwordVisuals: (entry) => ({ ...entry, visualized: true }),
    normalizeOwnerId: (value) => String(value ?? ''),
  });
}

describe('summonManager', () => {
  it('normalizes snapshot summons and tracks hp', () => {
    const manager = createManager();
    const hpCalls = [];

    const snapshot = {
      party_summons: {
        alpha: [{ owner_id: 'alpha', id: 'wolf', hp: 18, max_hp: 40, element: 'wind' }],
      },
      foe_summons: [
        { owner_id: 'omega', id: 'orb', instance_id: 'orb-1', hp: 5, max_hp: 5 },
      ],
    };

    const result = manager.processSnapshot(snapshot, {
      trackHp: (key, hp, max) => hpCalls.push({ key, hp, max }),
    });

    const partySummon = result.partySummons.get('alpha')?.[0];
    expect(partySummon).toMatchObject({
      id: 'wolf',
      hpKey: 'party-summon:alpha:wolf',
      element: 'wind',
      visualized: true,
    });
    expect(partySummon.renderKey).toContain('party-summon:alpha:wolf');

    const foeSummon = result.foeSummons.get('omega')?.[0];
    expect(foeSummon).toMatchObject({
      id: 'orb',
      hpKey: 'foe-summon:omega:orb-1',
      renderKey: 'orb-1',
      visualized: true,
    });

    expect(hpCalls).toEqual([
      { key: 'party-summon:alpha:wolf', hp: 18, max: 40 },
      { key: 'foe-summon:omega:orb-1', hp: 5, max: 5 },
    ]);

    expect(result.partySummonIds.has('wolf')).toBe(true);
    expect(result.foeSummonIds.has('orb-1')).toBe(true);
  });

  it('emits new summon events once per owner and dedupes repeats', () => {
    const manager = createManager();
    const onNewSummon = vi.fn();

    manager.processSnapshot(
      {
        party_summons: {
          hero: [
            { owner_id: 'hero', id: 'sprite-a' },
            { owner_id: 'hero', id: 'sprite-b' },
          ],
        },
      },
      { onNewSummon }
    );

    expect(onNewSummon).toHaveBeenCalledTimes(1);
    expect(onNewSummon).toHaveBeenCalledWith(
      expect.objectContaining({ side: 'party', ownerId: 'hero' })
    );

    onNewSummon.mockClear();

    manager.processSnapshot(
      {
        party_summons: {
          hero: [{ owner_id: 'hero', id: 'sprite-a' }],
        },
      },
      { onNewSummon }
    );

    expect(onNewSummon).not.toHaveBeenCalled();

    manager.processSnapshot(
      {
        foe_summons: [{ owner_id: 'foe', id: 'wisp' }],
      },
      { onNewSummon }
    );

    expect(onNewSummon).toHaveBeenCalledTimes(1);
    expect(onNewSummon).toHaveBeenLastCalledWith(
      expect.objectContaining({ side: 'foe', ownerId: 'foe' })
    );
  });

  it('preserves render keys across snapshots without explicit identifiers', () => {
    const manager = createManager();

    const first = manager.processSnapshot(
      {
        party_summons: {
          alpha: [{ owner_id: 'alpha', summon_type: 'shade' }],
        },
      },
      { trackHp: () => {} }
    );

    const initial = first.partySummons.get('alpha')?.[0];
    expect(initial?.renderKey).toBeTruthy();

    const second = manager.processSnapshot(
      {
        party_summons: {
          alpha: [{ owner_id: 'alpha', summon_type: 'shade' }],
        },
      },
      { trackHp: () => {} }
    );

    const next = second.partySummons.get('alpha')?.[0];
    expect(next?.renderKey).toBe(initial?.renderKey);
  });
});

describe('summon helpers', () => {
  it('identifies summons and filters party entities', () => {
    expect(isSummon({ summon_type: 'golem' })).toBe(true);
    expect(isSummon({ type: 'summon' })).toBe(true);
    expect(isSummon({ id: 'hero' })).toBe(false);

    const filtered = filterPartyEntities([
      { id: 'hero' },
      { id: 'phoenix', summon_type: 'companion' },
      { id: 'summoner', is_summon: false },
      null,
    ]);

    expect(filtered).toEqual([
      { id: 'hero' },
      { id: 'summoner', is_summon: false },
      null,
    ]);
  });
});
