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
    expect(content).toContain("safeLocalStorageGet('pulls-active-banner')");
    expect(content).toContain("safeLocalStorageSet('pulls-active-banner', activeTab)");
  });

  test('validates active banner after pull or reload', () => {
    const content = readFileSync(
      join(import.meta.dir, '../src/lib/components/PullsMenu.svelte'),
      'utf8'
    );
    expect(content).toMatch(/async function reloadData[\s\S]*ensureActiveTabValid\(\)/);
    expect(content).toMatch(/async function pull\([^)]*\)[\s\S]*ensureActiveTabValid\(\)/);
  });

  test('exposes warp info control with accessible label', () => {
    const content = readFileSync(
      join(import.meta.dir, '../src/lib/components/PullsMenu.svelte'),
      'utf8'
    );
    expect(content).toContain("import { PackageOpen, Star, Users, RotateCcw, Info }");
    expect(content).toContain('aria-label="Warp info"');
    expect(content).toContain("on:click={() => openOverlay('warp-info')}");
    expect(content).toContain('<span class="info-label">Info</span>');
  });
});

describe('OverlayHost warp info overlay', () => {
  test('ships warp info popup with explanatory text', () => {
    const overlayHost = readFileSync(
      join(import.meta.dir, '../src/lib/components/OverlayHost.svelte'),
      'utf8'
    );
    expect(overlayHost).toContain("$overlayView === 'warp-info'");
    expect(overlayHost).toContain('title="Warp Mechanics"');
    expect(overlayHost).toContain('warp-info-list');
    expect(overlayHost).toContain('Back to pulls');
  });
});
