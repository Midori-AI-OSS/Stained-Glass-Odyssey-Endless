import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('StatTabs upgrade view', () => {
  const content = readFileSync(join(import.meta.dir, '../src/lib/components/StatTabs.svelte'), 'utf8');

  test('exposes upgrade flow dispatchers', () => {
    expect(content).toContain("dispatch('open-upgrade'");
    expect(content).toContain("dispatch('close-upgrade'");
    expect(content).toContain("dispatch('request-upgrade'");
  });

  test('renders upgrade overlay copy and actions', () => {
    expect(content).toContain('<h3>{activeStatLabel} Upgrade</h3>');
    expect(content).toContain('class="upgrade-summary"');
    expect(content).toContain('class="upgrade-actions"');
    expect(content).toContain('Upgrade stats');
  });

  test('shows global buff note after Regain row', () => {
    expect(content).toContain('export let userBuffPercent = 0');
    const regainIndex = content.indexOf('<div><span>Regain</span>');
    const buffIndex = content.indexOf('Global Buff: +{userBuffPercent}%');
    expect(regainIndex).toBeGreaterThanOrEqual(0);
    expect(buffIndex).toBeGreaterThan(regainIndex);
  });
});
