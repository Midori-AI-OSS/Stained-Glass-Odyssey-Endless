<script>
  export let backLabel = 'Back';
  export let nextLabel = 'Next';
  export let onBack = null;
  export let onNext = null;
  export let backDisabled = false;
  export let nextDisabled = false;
  export let nextVariant = 'primary';
</script>

<nav class="wizard-navigation">
  <button type="button" class="btn ghost" disabled={backDisabled} on:click={onBack}>{backLabel}</button>
  <button
    type="button"
    class={`btn ${nextVariant}`}
    disabled={nextDisabled}
    on:click={onNext}
  >
    {nextLabel}
  </button>
</nav>

<style>
  .wizard-navigation {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: clamp(0.5rem, 1.2vw, 0.75rem);
  }

  .btn {
    appearance: none;
    border: 1px solid transparent;
    border-radius: 0;
    padding: clamp(0.55rem, 1.5vw, 0.85rem) clamp(1.1rem, 2.8vw, 1.75rem);
    font-size: 0.95rem;
    font-weight: 550;
    letter-spacing: 0.01em;
    text-transform: uppercase;
    background: transparent;
    color: inherit;
    cursor: pointer;
    transition: background 160ms ease, color 160ms ease, border-color 160ms ease, transform 120ms ease;
  }

  .btn:focus-visible {
    outline: 2px solid var(--wizard-focus-outline, rgba(180, 220, 255, 0.75));
    outline-offset: 2px;
  }

  .btn:disabled {
    opacity: 0.55;
    cursor: default;
  }

  .ghost {
    border-color: var(--wizard-border-muted, rgba(255, 255, 255, 0.25));
    background: var(--wizard-ghost-bg, rgba(255, 255, 255, 0.02));
  }

  .ghost:not(:disabled):hover {
    border-color: var(--wizard-border-accent, rgba(153, 201, 255, 0.6));
    background: var(--wizard-ghost-hover-bg, rgba(153, 201, 255, 0.08));
  }

  .primary {
    background: var(--wizard-primary-bg, linear-gradient(120deg, rgba(153, 201, 255, 0.6), rgba(113, 169, 240, 0.6)));
    border-color: var(--wizard-primary-border, rgba(153, 201, 255, 0.8));
    color: var(--wizard-primary-color, #0b0f19);
  }

  .primary:not(:disabled):hover {
    transform: translateY(-1px);
    background: var(--wizard-primary-hover-bg, linear-gradient(120deg, rgba(173, 211, 255, 0.75), rgba(133, 189, 250, 0.75)));
    border-color: var(--wizard-primary-hover-border, rgba(173, 211, 255, 0.9));
  }
</style>
