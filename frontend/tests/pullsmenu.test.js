import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('PullsMenu component', () => {
  test('renders pity and buttons', () => {
    const content = readFileSync(
      join(import.meta.dir, '../src/lib/components/PullsMenu.svelte'),
      'utf8'
    );
    expect(content).toContain('data-testid="pulls-menu"');
    expect(content).toContain('Pull ×1');
    expect(content).toContain('Pull ×5');
    expect(content).toContain('Pull ×10');
    expect(content).toContain('(items.ticket || 0) < 1');
    expect(content).toContain('(items.ticket || 0) < 5');
    expect(content).toContain("openOverlay('pull-results'");
    expect(content).not.toContain('<ul>');
  });

  test('persists selected banner via localStorage', () => {
    const content = readFileSync(
      join(import.meta.dir, '../src/lib/components/PullsMenu.svelte'),
      'utf8'
    );
    expect(content).toContain("localStorage.getItem('pulls-active-banner')");
    expect(content).toContain("localStorage.setItem('pulls-active-banner', activeTab)");
  });

  test('validates active banner after pull or reload', () => {
    const content = readFileSync(
      join(import.meta.dir, '../src/lib/components/PullsMenu.svelte'),
      'utf8'
    );
    expect(content).toMatch(/async function reloadData[\s\S]*ensureActiveTabValid\(\)/);
    expect(content).toMatch(/async function pull\([^)]*\)[\s\S]*ensureActiveTabValid\(\)/);
  });
});
