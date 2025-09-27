<script>
  import { getContext } from 'svelte';
  import {
    Zap,
    Skull,
    Flame,
    XOctagon,
    Shield,
    Heart,
    HeartOff,
    TrendingUp,
    Coins
  } from 'lucide-svelte';
  import { BATTLE_REVIEW_CONTEXT_KEY } from '../../systems/battleReview/state.js';
  import { fmt } from './utils.js';

  const { entityMetrics } = getContext(BATTLE_REVIEW_CONTEXT_KEY);
</script>

{#if $entityMetrics}
  <aside class="stats-panel">
    <div class="entity-stats-grid">
      <div class="stat-item">
        <Zap size={16} />
        <span>Critical Hits</span>
        <span class="stat-value">{$entityMetrics.criticals || 0}</span>
        {#if $entityMetrics.criticalDamage > 0}
          <span class="stat-detail">({fmt($entityMetrics.criticalDamage)} dmg)</span>
        {/if}
      </div>
      <div class="stat-item">
        <Skull size={16} />
        <span>Kills</span>
        <span class="stat-value">{$entityMetrics.kills || 0}</span>
      </div>
      <div class="stat-item">
        <Flame size={16} />
        <span>DoT Kills</span>
        <span class="stat-value">{$entityMetrics.dotKills || 0}</span>
      </div>
      <div class="stat-item">
        <Zap size={16} />
        <span>Ultimates Used</span>
        <span class="stat-value">{$entityMetrics.ultimatesUsed || 0}</span>
      </div>
      <div class="stat-item">
        <XOctagon size={16} />
        <span>Ultimate Failures</span>
        <span class="stat-value">{$entityMetrics.ultimateFailures || 0}</span>
      </div>
      <div class="stat-item">
        <Shield size={16} />
        <span>Shield Absorbed</span>
        <span class="stat-value">{fmt($entityMetrics.shieldAbsorbed || 0)}</span>
      </div>
      <div class="stat-item">
        <Flame size={16} />
        <span>DoT Damage</span>
        <span class="stat-value">{fmt($entityMetrics.dotDamage || 0)}</span>
      </div>
      <div class="stat-item">
        <Heart size={16} />
        <span>HoT Healing</span>
        <span class="stat-value">{fmt($entityMetrics.hotHealing || 0)}</span>
      </div>
      <div class="stat-item">
        <HeartOff size={16} />
        <span>Healing Prevented</span>
        <span class="stat-value">{fmt($entityMetrics.healingPrevented || 0)}</span>
      </div>
      <div class="stat-item">
        <TrendingUp size={16} />
        <span>Temp HP Granted</span>
        <span class="stat-value">{fmt($entityMetrics.tempHpGranted || 0)}</span>
      </div>
      {#if Object.keys($entityMetrics.resourcesSpent || {}).length > 0 || Object.keys($entityMetrics.resourcesGained || {}).length > 0}
        <div class="stat-item resources">
          <Coins size={16} />
          <span>Resources</span>
          <div class="resource-breakdown">
            {#each Array.from(new Set([
              ...Object.keys($entityMetrics.resourcesSpent || {}),
              ...Object.keys($entityMetrics.resourcesGained || {})
            ])) as type}
              <span class="resource-item">{type}: {fmt($entityMetrics.resourcesSpent[type] || 0)} spent / {fmt($entityMetrics.resourcesGained[type] || 0)} gained</span>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  </aside>
{/if}

<style>
  .stats-panel {
    background: rgba(15, 23, 42, 0.25);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.2);
  }

  .entity-stats-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(15, 23, 42, 0.55);
    border-radius: 10px;
    padding: 0.6rem 0.75rem;
    border: 1px solid rgba(148, 163, 184, 0.18);
    font-size: 0.78rem;
    color: rgba(226, 232, 240, 0.9);
  }

  .stat-value {
    margin-left: auto;
    font-weight: 700;
    color: #f8fafc;
  }

  .stat-detail {
    font-size: 0.7rem;
    color: rgba(226, 232, 240, 0.7);
  }

  .resources {
    flex-direction: column;
    align-items: flex-start;
  }

  .resource-breakdown {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-top: 0.4rem;
  }

  .resource-item {
    background: rgba(59, 130, 246, 0.16);
    border-radius: 6px;
    padding: 0.25rem 0.4rem;
    font-size: 0.72rem;
    border: 1px solid rgba(59, 130, 246, 0.3);
  }
</style>
