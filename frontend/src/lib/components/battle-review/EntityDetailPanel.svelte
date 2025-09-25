<script>
  import { getContext } from 'svelte';
  import { Swords } from 'lucide-svelte';
  import BattleReviewFighterChip from './BattleReviewFighterChip.svelte';
  import { BATTLE_REVIEW_CONTEXT_KEY } from '../../systems/battleReview/state.js';
  import { fmt, getElementBarColor } from './utils.js';

  const { currentTab, entityMetrics, reducedMotion } = getContext(BATTLE_REVIEW_CONTEXT_KEY);
</script>

{#if $currentTab && $entityMetrics}
  <div class="entity-breakdown">
    <div class="entity-header">
      {#if $currentTab.entity}
        <div class="portrait-large">
          <BattleReviewFighterChip
            fighter={$currentTab.entity}
            rankTag={$currentTab.rank ?? $currentTab.entity.rank}
            reducedMotion={$reducedMotion}
            position={$currentTab.type === 'foe' ? 'top' : 'bottom'}
            sizePx={104}
          />
        </div>
      {/if}
      <h3>
        {$currentTab.label}
        {#if $currentTab.rank}
          <span class="rank-inline">— {$currentTab.rank}</span>
        {/if}
      </h3>
    </div>

    {#if Object.keys($entityMetrics.damage || {}).length > 0}
      {@const totalDamage = Object.values($entityMetrics.damage).reduce((a, b) => a + b, 0)}
      <div class="entity-section">
        <h4 class="section-title">Damage Output by Source</h4>
        <div class="damage-bar-container">
          {#each Object.entries($entityMetrics.damage).sort((a, b) => b[1] - a[1]) as [element, damage]}
            {@const percentage = totalDamage > 0 ? (damage / totalDamage) * 100 : 0}
            <div class="damage-bar">
              <div class="damage-bar-fill" style="width: {percentage}%; background-color: {getElementBarColor(element)};"></div>
              <div class="damage-bar-label">{element}</div>
              <div class="damage-bar-amount">{fmt(damage)}</div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    {#if Object.keys($entityMetrics.actions || {}).length > 0}
      <div class="entity-section">
        <h4 class="section-title">
          <Swords size={16} />
          Damage by Action
        </h4>
        <div class="damage-breakdown">
          {#each Object.entries($entityMetrics.actions).sort((a, b) => b[1] - a[1]) as [action, amount]}
            <div class="damage-item">
              <span class="damage-element">{action}</span>
              <span class="damage-amount">{fmt(amount)}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .entity-breakdown {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    background: rgba(15, 23, 42, 0.35);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.2);
  }

  .entity-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  }

  .entity-header h3 {
    margin: 0;
    font-size: 1.1rem;
    color: #f8fafc;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .portrait-large {
    --portrait-size: 6.5rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .portrait-large :global(.review-fighter-chip) {
    --portrait-size: var(--portrait-size);
  }

  .rank-inline {
    font-size: 0.95rem;
    color: rgba(226, 232, 240, 0.75);
  }

  .entity-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .section-title {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.95rem;
    font-weight: 600;
    color: #e2e8f0;
  }

  .damage-bar-container {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .damage-bar {
    position: relative;
    height: 16px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    overflow: hidden;
  }

  .damage-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .damage-bar-label,
  .damage-bar-amount {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    font-size: 0.7rem;
    font-weight: 600;
    color: #f8fafc;
    text-shadow: 0 0 4px rgba(15, 23, 42, 0.8);
  }

  .damage-bar-label {
    left: 6px;
  }

  .damage-bar-amount {
    right: 6px;
  }

  .damage-breakdown {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.5rem;
  }

  .damage-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    font-size: 0.78rem;
  }
</style>
