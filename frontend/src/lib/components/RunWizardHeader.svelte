<script>
  export let title = '';
  export let steps = [];
  export let activeStep = '';
  export let currentIndex = 0;
</script>

<header class="wizard-header">
  <h2>{title}</h2>
  <div class="step-indicator" aria-hidden="true">
    {#each steps as key, index}
      <span class:selected={key === activeStep} class:done={index < currentIndex}>{index + 1}</span>
    {/each}
  </div>
</header>

<style>
  .wizard-header {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: clamp(0.5rem, 1.4vw, 0.85rem);
  }

  .wizard-header h2 {
    flex: 1 1 14rem;
    margin: 0;
    font-size: clamp(1.2rem, 2vw, 1.55rem);
    font-weight: 600;
    letter-spacing: -0.015em;
  }

  .step-indicator {
    display: inline-flex;
    flex-wrap: wrap;
    gap: clamp(0.3rem, 0.9vw, 0.5rem);
    justify-content: flex-end;
  }

  .step-indicator span {
    width: 1.75rem;
    height: 1.75rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    border: 1px solid var(--wizard-step-border, rgba(255, 255, 255, 0.28));
    background: var(--wizard-step-bg, transparent);
    color: inherit;
    opacity: 0.6;
    transition: background 160ms ease, opacity 160ms ease, border-color 160ms ease;
  }

  .step-indicator span.selected {
    background: var(--wizard-step-active-bg, rgba(153, 201, 255, 0.25));
    border-color: var(--wizard-step-active-border, rgba(153, 201, 255, 0.65));
    opacity: 1;
  }

  .step-indicator span.done {
    opacity: 0.85;
    border-color: var(--wizard-step-done-border, rgba(153, 201, 255, 0.4));
    background: var(--wizard-step-done-bg, rgba(153, 201, 255, 0.12));
  }
</style>
