<script>
  import Tooltip from './Tooltip.svelte';

  export let modifiers = [];
  export let values = {};
  export let onChange = null;
</script>

<div class="modifiers" role="list">
  {#each modifiers as mod}
    <article class="modifier" role="listitem" data-modifier-id={mod.id}>
      <div class="modifier-header">
        <div class="modifier-title">
          <span class="modifier-label">{mod.label || mod.id}</span>
          {#if mod.category}
            <span class="modifier-category">{mod.category}</span>
          {/if}
        </div>
        <div class="modifier-controls">
          {#if mod.meta?.tooltipText}
            <Tooltip text={mod.meta.tooltipText}>
              <button
                type="button"
                class="info-trigger"
                aria-label={mod.meta.tooltipLabel}
                data-tooltip={mod.meta.tooltipText}
              >
                <span aria-hidden="true">i</span>
              </button>
            </Tooltip>
          {/if}
          <label class="stack-input" for={`modifier-${mod.id}`}>
            <span class="stack-label">Stacks</span>
            <input
              id={`modifier-${mod.id}`}
              type="number"
              min={mod.stacking?.minimum ?? 0}
              step={mod.stacking?.step ?? 1}
              max={Number.isFinite(mod.stacking?.maximum) ? mod.stacking.maximum : undefined}
              value={values[mod.id] ?? ''}
              on:input={(event) => onChange?.(mod.id, event.target.value)}
            />
          </label>
        </div>
      </div>
      {#if mod.meta?.stackSummary || mod.meta?.effectsSummary || mod.meta?.rewardSummary || mod.meta?.diminishingSummary}
        <div class="modifier-meta">
          {#if mod.meta?.stackSummary}
            <span>{mod.meta.stackSummary}</span>
          {/if}
          {#if mod.meta?.effectsSummary}
            <span>{mod.meta.effectsSummary}</span>
          {/if}
          {#if mod.meta?.rewardSummary}
            <span>{mod.meta.rewardSummary}</span>
          {/if}
          {#if mod.meta?.diminishingSummary}
            <span>{mod.meta.diminishingSummary}</span>
          {/if}
        </div>
      {/if}
      {#if mod.description}
        <p class="modifier-description">{mod.description}</p>
      {/if}
    </article>
  {/each}
</div>

<style>
  .modifiers {
    display: grid;
    gap: clamp(0.65rem, 1.5vw, 0.9rem);
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .modifier {
    display: flex;
    flex-direction: column;
    gap: clamp(0.45rem, 1vw, 0.7rem);
    padding: clamp(0.7rem, 1.5vw, 0.95rem);
    background: var(--wizard-card-bg, rgba(17, 23, 38, 0.7));
    border: 1px solid var(--wizard-card-border, rgba(153, 201, 255, 0.18));
    color: inherit;
  }

  @media (max-width: 960px) {
    .modifiers {
      grid-template-columns: 1fr;
    }
  }

  .modifier-header {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: clamp(0.45rem, 1vw, 0.6rem);
  }

  .modifier-title {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: clamp(0.35rem, 1vw, 0.55rem);
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.01em;
  }

  .modifier-category {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.7;
  }

  .modifier-controls {
    display: inline-flex;
    align-items: center;
    gap: clamp(0.35rem, 0.9vw, 0.55rem);
  }

  .info-trigger {
    width: 1.75rem;
    height: 1.75rem;
    border: 1px solid var(--wizard-border-muted, rgba(255, 255, 255, 0.25));
    background: var(--wizard-ghost-bg, rgba(255, 255, 255, 0.02));
    color: inherit;
    font-weight: 600;
    border-radius: 0;
    cursor: pointer;
  }

  .info-trigger:hover,
  .info-trigger:focus-visible {
    border-color: var(--wizard-border-accent, rgba(173, 211, 255, 0.6));
    background: var(--wizard-ghost-hover-bg, rgba(173, 211, 255, 0.1));
    outline: none;
  }

  .stack-input {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .stack-input input {
    width: clamp(4.5rem, 8vw, 5.5rem);
    padding: 0.45rem 0.5rem;
    border: 1px solid var(--wizard-border-muted, rgba(255, 255, 255, 0.25));
    background: var(--wizard-input-bg, rgba(10, 15, 26, 0.85));
    color: inherit;
    font-size: 0.95rem;
    font-variant-numeric: tabular-nums;
  }

  .stack-input input:focus-visible {
    outline: 2px solid var(--wizard-focus-outline, rgba(180, 220, 255, 0.75));
    outline-offset: 2px;
  }

  .modifier-meta {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.85rem;
    opacity: 0.8;
    line-height: 1.35;
  }

  .modifier-description {
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.45;
    opacity: 0.85;
  }

</style>
