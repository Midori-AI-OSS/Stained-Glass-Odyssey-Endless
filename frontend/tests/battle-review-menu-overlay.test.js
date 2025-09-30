import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('OverlayHost battle review menu mount', () => {
  test('renders BattleReviewMenu inside an OverlaySurface', () => {
    const overlayHost = readFileSync(
      join(import.meta.dir, '../src/lib/components/OverlayHost.svelte'),
      'utf8'
    );

    expect(overlayHost).toContain(
      "import BattleReviewMenu from './battle-review/BattleReviewMenu.svelte';"
    );

    const block = overlayHost.match(
      /\{#if \$overlayView === 'battle-review-menu'\}([\s\S]*?)\{\/if\}/
    );

    expect(block).toBeTruthy();
    expect(block?.[1]).toContain('<OverlaySurface');
    expect(block?.[1]).toContain('<BattleReviewMenu');
    expect(block?.[1]).not.toContain('PopupWindow');
  });
});
