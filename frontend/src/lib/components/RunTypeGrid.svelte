<script>
  export let runTypes = [];
  export let activeId = '';
  export let loading = false;
  export let error = '';
  export let onRetry = null;
  export let onSelect = null;
  export let getModifierLabel = (id) => id;
</script>

{#if loading}
  <p class="loading">Loading configuration...</p>
{:else if error}
  <div class="error">
    <p>{error}</p>
    <button class="ghost" type="button" on:click={onRetry}>Retry</button>
  </div>
{:else}
  <div class="run-types" role="list">
    {#each runTypes as rt}
      <button
        type="button"
        class="run-type-card"
        class:active={rt.id === activeId}
        on:click={() => onSelect?.(rt.id)}
        role="listitem"
      >
        <div class="card-title">{rt.label}</div>
        <p class="card-description">{rt.description}</p>
        {#if Object.keys(rt.default_modifiers || {}).length > 0}
          <div class="card-defaults">
            <strong>Defaults</strong>
            <ul>
              {#each Object.entries(rt.default_modifiers || {}) as [key, value]}
                <li>{getModifierLabel(key)}: {value}</li>
              {/each}
            </ul>
          </div>
        {/if}
      </button>
    {/each}
  </div>
{/if}

<style>
  .loading {
    margin: 0;
    opacity: 0.7;
    font-size: 0.95rem;
  }

  .error {
    display: flex;
    flex-direction: column;
    gap: clamp(0.5rem, 1vw, 0.75rem);
    background: var(--wizard-error-bg, rgba(46, 12, 20, 0.85));
    border: 1px solid var(--wizard-error-border, rgba(255, 117, 133, 0.5));
    padding: clamp(0.75rem, 1.6vw, 1rem);
  }

  .error p {
    margin: 0;
    font-weight: 500;
  }

  .error .ghost {
    align-self: flex-start;
  }

  .run-types {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: clamp(0.55rem, 1.6vw, 0.95rem);
  }

  .run-type-card {
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.6rem);
    padding: clamp(0.75rem, 1.6vw, 1.1rem);
    background: var(--wizard-card-bg, rgba(17, 23, 38, 0.7));
    border: 1px solid var(--wizard-card-border, rgba(153, 201, 255, 0.18));
    text-align: left;
    color: inherit;
    cursor: pointer;
    transition: border-color 160ms ease, background 160ms ease, transform 120ms ease;
  }

  .run-type-card:hover,
  .run-type-card:focus-visible {
    outline: none;
    border-color: var(--wizard-card-hover-border, rgba(173, 211, 255, 0.6));
    background: var(--wizard-card-hover-bg, rgba(27, 37, 58, 0.82));
  }

  .run-type-card.active {
    border-color: var(--wizard-card-active-border, rgba(173, 211, 255, 0.8));
    background: var(--wizard-card-active-bg, rgba(27, 37, 58, 0.9));
  }

  .card-title {
    font-weight: 600;
    font-size: 1rem;
    letter-spacing: 0.01em;
  }

  .card-description {
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.4;
    opacity: 0.8;
  }

  .card-defaults {
    font-size: 0.85rem;
    opacity: 0.8;
    line-height: 1.35;
  }

  .card-defaults ul {
    margin: 0.4rem 0 0;
    padding-left: 1rem;
  }
</style>
