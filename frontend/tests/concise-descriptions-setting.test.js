import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Concise Descriptions Setting', () => {
  const optionsFile = join(import.meta.dir, '../../backend/options.py');
  const configFile = join(import.meta.dir, '../../backend/routes/config.py');
  const catalogFile = join(import.meta.dir, '../../backend/routes/catalog.py');
  const playersFile = join(import.meta.dir, '../../backend/routes/players.py');
  const settingsStorageFile = join(import.meta.dir, '../src/lib/systems/settingsStorage.js');
  const uiSettingsFile = join(import.meta.dir, '../src/lib/components/UISettings.svelte');

  test('Backend: CONCISE_DESCRIPTIONS option key exists', () => {
    const content = readFileSync(optionsFile, 'utf8');
    expect(content).toContain('CONCISE_DESCRIPTIONS = "concise_descriptions"');
  });

  test('Backend: Config routes for concise_descriptions exist', () => {
    const content = readFileSync(configFile, 'utf8');
    expect(content).toContain('@bp.get("/concise_descriptions")');
    expect(content).toContain('@bp.post("/concise_descriptions")');
    expect(content).toContain('async def get_concise_descriptions()');
    expect(content).toContain('async def update_concise_descriptions()');
  });

  test('Backend: Catalog routes send both description fields for client-side selection', () => {
    const content = readFileSync(catalogFile, 'utf8');
    // Backend sends both fields to frontend for client-side switching
    expect(content).toContain('Send both description fields to frontend for client-side switching');
    expect(content).toContain('summarized_about');
    expect(content).toContain('full_about');
  });

  test('Backend: Players route sends both description fields for client-side selection', () => {
    const content = readFileSync(playersFile, 'utf8');
    // Backend sends both fields to frontend for client-side switching
    expect(content).toContain('Send both description fields to frontend for client-side switching');
    expect(content).toContain('summarized_about');
    expect(content).toContain('full_about');
  });

  test('Frontend: Settings storage includes ui.conciseDescriptions', () => {
    const content = readFileSync(settingsStorageFile, 'utf8');
    expect(content).toContain('ui: {');
    expect(content).toContain('conciseDescriptions: false');
    expect(content).toContain('export const uiStore');
    expect(content).toContain('export function getUISettings()');
    expect(content).toContain('export function updateUISettings(');
  });

  test('Frontend: UISettings.svelte has concise descriptions checkbox', () => {
    const content = readFileSync(uiSettingsFile, 'utf8');
    expect(content).toContain('FileText');
    expect(content).toContain('Concise Descriptions');
    expect(content).toContain('uiSettings.conciseDescriptions');
    expect(content).toContain('updateUI');
    expect(content).toContain('Show concise descriptions instead of full detailed descriptions');
  });

  test('Frontend: Settings storage properly initializes uiStore', () => {
    const content = readFileSync(settingsStorageFile, 'utf8');
    // Check that uiStore is set in loadSettings
    expect(content).toContain('uiStore.set(defaults.ui)');
    expect(content).toContain('uiStore.set(data.ui)');
  });

  test('Frontend: Settings storage saves ui settings', () => {
    const content = readFileSync(settingsStorageFile, 'utf8');
    // Check that ui settings are saved
    expect(content).toContain('if (merged.ui)');
    expect(content).toContain('uiStore.set(merged.ui)');
  });
});
