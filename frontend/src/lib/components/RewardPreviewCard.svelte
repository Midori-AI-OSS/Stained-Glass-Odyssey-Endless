<script>
  export let title = 'Reward Preview';
  export let preview = {
    exp_bonus: 0,
    rdr_bonus: 0
  };
  export let formatValue = (value) => value;
</script>

<section class="reward-card" aria-label={title}>
  <header>
    <h3>{title}</h3>
  </header>
  <div class="preview-grid">
    <div>
      <span class="preview-label">EXP Bonus</span>
      <span class="preview-value">{formatValue(preview.exp_bonus)}</span>
    </div>
    <div>
      <span class="preview-label">RDR Bonus</span>
      <span class="preview-value">{formatValue(preview.rdr_bonus)}</span>
    </div>
  </div>
</section>

<style>
  .reward-card {
    display: flex;
    flex-direction: column;
    gap: clamp(0.45rem, 1vw, 0.7rem);
    background: var(--wizard-summary-bg, rgba(17, 23, 38, 0.78));
    border: 1px solid var(--wizard-summary-border, rgba(153, 201, 255, 0.2));
    padding: clamp(0.65rem, 1.5vw, 0.95rem);
    color: inherit;
  }

  .reward-card h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    text-transform: uppercase;
  }

  .preview-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: clamp(0.4rem, 1vw, 0.6rem);
  }

  .preview-label {
    display: block;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.7;
  }

  .preview-value {
    font-size: 1.05rem;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.01em;
  }
</style>
