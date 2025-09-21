import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('PartyPicker component', () => {
  test('contains party picker markup', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/PartyPicker.svelte'), 'utf8');
    expect(content).toContain('data-testid="party-picker"');
  });

  test('includes add/remove control', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/StatTabs.svelte'), 'utf8');
    expect(content).toContain('Add to party');
  });

  test('references updated stat keys', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/StatTabs.svelte'), 'utf8');
    expect(content).toContain('crit_damage');
    expect(content).toContain('effect_hit_rate');
    expect(content).toContain('dodge_odds');
    expect(content).toContain('effect_resistance');
  });

  test('filters unowned characters and normalizes element names', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/PartyPicker.svelte'), 'utf8');
    expect(content).toContain('filter((p) => (p.owned || p.is_player) && !isNonPlayable(p))');
    expect(content).toContain('selected = oldSelected.filter((id) => roster.some((c) => c.id === id))');
    expect(content).toContain('element: resolveElement(p)');
  });

  test('orders stats correctly', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/StatTabs.svelte'), 'utf8');
    const coreStart = content.indexOf("{#if activeTab === 'Core'}");
    const coreEnd = content.indexOf("{:else if activeTab === 'Offense'}");
    const coreSection = content.slice(coreStart, coreEnd);
    expect(coreSection).toMatch(/HP[\s\S]*EXP[\s\S]*Vitality[\s\S]*Regain/);
    expect(coreSection).not.toMatch(/DEF/);
    const defStart = content.indexOf("{:else if activeTab === 'Defense'}");
    const defEnd = content.indexOf('{/if}', defStart);
    const defSection = content.slice(defStart, defEnd);
    expect(defSection).toMatch(/<div><span>DEF<\/span><span>{formatStat\(viewStats.defense, getBaseStat\(sel, 'defense'\)\)}/);
  });

  test('uses element colors for icon and outline', () => {
    const rosterContent = readFileSync(join(import.meta.dir, '../src/lib/components/PartyRoster.svelte'), 'utf8');
    expect(rosterContent).toContain('style={`border-color: ${getElementColor(char.element)}; --el-color: ${getElementColor(char.element)}');
    expect(rosterContent).toContain('style={`color: ${getElementColor(char.element)}`}');
  });

  test('includes party count and sort controls', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/PartyRoster.svelte'), 'utf8');
    expect(content).toContain('{selected.length} / 5 party members');
    expect(content).toContain('<select bind:value={sortKey}>');
    expect(content).toContain('on:click={() => (sortDir = sortDir === \'asc\' ? \'desc\' : \'asc\')}');
  });

  test('roster uses transition group and fly animations', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/PartyRoster.svelte'), 'utf8');
    expect(content).toContain('animate:flip');
    expect(content).toContain('in:fly');
    expect(content).toContain('out:fly');
    expect(content).toContain('sparkleTrail');
  });

  test('roster layout snapshot', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/PartyRoster.svelte'), 'utf8');
    expect(content).toMatchSnapshot();
  });

  test('preserves preview and passes buff percent', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/PartyPicker.svelte'), 'utf8');
    expect(content).toContain('previewId = oldPreview ?? selected[0] ?? defaultPreview;');
    expect(content).toContain('<StatTabs {roster} {previewId} {selected} {userBuffPercent}');
  });

  test('declares preview mode store and upgrade handlers', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/PartyPicker.svelte'), 'utf8');
    expect(content).toContain("const previewMode = writable('portrait')");
    expect(content).toContain('previewMode.set(\'portrait\')');
    expect(content).toContain('previewMode.set(mode)');
    expect(content).toContain('on:open-upgrade={(e) => handlePreviewMode(e.detail, \'upgrade\')}');
    expect(content).toContain('on:close-upgrade={(e) => handlePreviewMode(e.detail, \'portrait\')}');
    expect(content).toContain('on:request-upgrade={(e) => forwardUpgradeRequest(e.detail)}');
  });

  test('wires upgrade requests to the API', () => {
    const content = readFileSync(join(import.meta.dir, '../src/lib/components/PartyPicker.svelte'), 'utf8');
    expect(content).toContain('import { getPlayers, getUpgrade, upgradeCharacter, upgradeStat }');
    expect(content).toContain('await upgradeStat(id, stat, { repeat: requestRepeats });');
    expect(content).toContain('upgradeContext?.pendingStat');
  });
});

