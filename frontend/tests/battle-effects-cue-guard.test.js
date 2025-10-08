import { describe, test, expect } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

const battleEffectsPath = join(import.meta.dir, '../src/lib/effects/BattleEffects.svelte');
const battleEffectsSource = readFileSync(battleEffectsPath, 'utf8');

describe('BattleEffects component', () => {
  test('uses lastProcessedCue to prevent infinite reactive loops', () => {
    // Verify that the component declares lastProcessedCue variable
    expect(battleEffectsSource).toContain('let lastProcessedCue');
    
    // Verify that the reactive statement checks against lastProcessedCue
    expect(battleEffectsSource).toMatch(/cue\s+!==\s+lastProcessedCue/);
    
    // Verify that lastProcessedCue is updated when cue changes
    expect(battleEffectsSource).toMatch(/lastProcessedCue\s*=\s*cue/);
  });

  test('clears lastProcessedCue when cue becomes empty', () => {
    // Verify that the component handles clearing the processed cue
    expect(battleEffectsSource).toMatch(/lastProcessedCue\s*=\s*['"]['"]|lastProcessedCue\s*=\s*['"]['"];/);
  });

  test('does not call playEffect unconditionally in reactive statement', () => {
    // Ensure the old pattern is not present
    expect(battleEffectsSource).not.toMatch(/\$:\s*if\s*\(\s*cue\s*\)\s*{\s*playEffect\(cue\)/);
  });
});
