import { describe, expect, test, beforeEach } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Settings migration', () => {
  const file = join(import.meta.dir, '../src/lib/systems/settingsStorage.js');

  test('exports theme definitions', () => {
    const content = readFileSync(file, 'utf8');
    expect(content).toContain('export const THEMES');
    expect(content).toContain('default:');
    expect(content).toContain('solaris:');
    expect(content).toContain('nocturne:');
    expect(content).toContain('custom:');
  });

  test('includes migration logic', () => {
    const content = readFileSync(file, 'utf8');
    expect(content).toContain('migrateSettings');
    expect(content).toContain('SETTINGS_VERSION');
    expect(content).toContain('globalReducedMotion');
    expect(content).toContain('disableFloatingDamage');
  });

  test('provides helper functions', () => {
    const content = readFileSync(file, 'utf8');
    expect(content).toContain('getThemeSettings');
    expect(content).toContain('getMotionSettings');
    expect(content).toContain('updateThemeSettings');
    expect(content).toContain('updateMotionSettings');
  });

  test('maintains backward compatibility', () => {
    const content = readFileSync(file, 'utf8');
    expect(content).toContain('framerate');
    expect(content).toContain('reducedMotion');
    expect(content).toContain('animationSpeed');
  });
});