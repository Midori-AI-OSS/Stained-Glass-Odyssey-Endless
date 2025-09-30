import { describe, expect, test } from 'bun:test';
import { groupBattleSummariesByFloor } from '../src/lib/systems/uiApi.js';

describe('groupBattleSummariesByFloor', () => {
  test('splits floors when room index resets', () => {
    const summaries = [
      { battle_index: 1, room_index: 0, room_name: 'Entrance Scouts' },
      { battle_index: 2, room_index: 1, room_name: 'Hallway Patrol' },
      { battle_index: 3, room_index: 0, room_name: 'Atrium Ambush' },
      { battle_index: 4, room_index: 1 },
      { battle_index: 5, room_index: 0, room_name: 'Summit Guardian' }
    ];

    const floors = groupBattleSummariesByFloor(summaries);

    expect(floors.length).toBe(3);
    expect(floors.map((floor) => floor.floor)).toEqual([1, 2, 3]);
    expect(floors[0].fights.map((fight) => fight.battleIndex)).toEqual([1, 2]);
    expect(floors[1].fights.map((fight) => fight.battleIndex)).toEqual([3, 4]);
    expect(floors[2].fights.map((fight) => fight.battleIndex)).toEqual([5]);
    expect(floors[0].label).toBe('Floor 1');
    expect(floors[0].fights[0].label).toBe('Entrance Scouts');
    expect(floors[1].fights[1].label).toBe('Fight 4');
  });

  test('tolerates non-numeric room indices without creating false floors', () => {
    const summaries = [
      { battle_index: 7, room_index: '??', room_name: 'Unknown Encounter' },
      { battle_index: 8, room_index: '??', room_name: 'Still Unknown' },
      { battle_index: 9, room_index: 2, room_name: 'Mapped Battle' },
      { battle_index: 10, room_index: 0, room_name: 'Reset Floor' }
    ];

    const floors = groupBattleSummariesByFloor(summaries);

    expect(floors.length).toBe(2);
    expect(floors[0].fights.map((fight) => fight.battleIndex)).toEqual([7, 8, 9]);
    expect(floors[1].fights.map((fight) => fight.battleIndex)).toEqual([10]);
  });
});
