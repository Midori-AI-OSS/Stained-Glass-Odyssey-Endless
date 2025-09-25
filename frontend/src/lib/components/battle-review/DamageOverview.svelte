<script>
  import { Swords, User } from 'lucide-svelte';
  import ReviewOverlay from './ReviewOverlay.svelte';
  import { fmt, getElementBarColor } from './utils.js';

  export let totals = {};
  export let grandTotal = 0;
  export let summary = {};
  export let cards = [];
  export let relics = [];
  export let partyTotals = { partyDamage: {}, foeDamage: {}, partyTotal: 0, foeTotal: 0, combatTotal: 0 };
</script>

{#if Object.keys(totals).length > 0}
  <div class="entity-section">
    <h4 class="section-title">
      <Swords size={16} />
      Total Damage Output
    </h4>
    <div class="damage-bar-container">
      {#each Object.entries(totals).sort((a, b) => b[1] - a[1]) as [element, damage]}
        {@const percentage = grandTotal > 0 ? (damage / grandTotal) * 100 : 0}
        <div class="damage-bar">
          <div class="damage-bar-fill" style="width: {percentage}%; background-color: {getElementBarColor(element)};"></div>
          <div class="damage-bar-label">{element}</div>
          <div class="damage-bar-amount">{fmt(damage)}</div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<ReviewOverlay {summary} {cards} {relics} showDamageGraphs={false} />

{#if Object.keys(summary?.damage_by_type || {}).length > 0}
  <div class="entity-section">
    <h4 class="section-title">
      <User size={16} />
      Party vs Foe Damage Comparison
    </h4>
    <div class="damage-bar-container">
      {#if partyTotals.partyTotal > 0}
        {@const partyPercentage = partyTotals.combatTotal > 0 ? (partyTotals.partyTotal / partyTotals.combatTotal) * 100 : 0}
        <div class="damage-bar">
          <div class="damage-bar-fill" style="width: {partyPercentage}%; background-color: #4ade80;"></div>
          <div class="damage-bar-label">Player Party</div>
          <div class="damage-bar-amount">{fmt(partyTotals.partyTotal)}</div>
        </div>
      {/if}
      {#if partyTotals.foeTotal > 0}
        {@const foePercentage = partyTotals.combatTotal > 0 ? (partyTotals.foeTotal / partyTotals.combatTotal) * 100 : 0}
        <div class="damage-bar">
          <div class="damage-bar-fill" style="width: {foePercentage}%; background-color: #ef4444;"></div>
          <div class="damage-bar-label">Foe Party</div>
          <div class="damage-bar-amount">{fmt(partyTotals.foeTotal)}</div>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .entity-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    background: rgba(15, 23, 42, 0.35);
    border-radius: 12px;
    padding: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.18);
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
</style>
