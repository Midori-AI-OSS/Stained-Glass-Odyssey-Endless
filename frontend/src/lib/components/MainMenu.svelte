<script>
  export let items = [];

  $: primaryItems = items.filter((item) => item?.group !== 'quick-link');
  $: quickLinks = items.filter((item) => item?.group === 'quick-link');
</script>

<div class="stained-glass-side">
  <div class="primary-items">
    {#each primaryItems as item}
      <button
        type="button"
        class="icon-btn"
        title={item.label}
        aria-label={item.label}
        on:click={item.action}
        disabled={item.disabled}
      >
        <div class="btn-content">
          {#if item.icon}
            <div class="icon">
              <svelte:component this={item.icon} size={24} color="#fff" />
            </div>
            <span class="label">{item.label}</span>
          {:else}
            <span class="label">{item.label}</span>
          {/if}
        </div>
      </button>
    {/each}
  </div>

  {#if quickLinks.length}
    <div class="quick-links">
      {#each quickLinks as item}
        <button
          type="button"
          class="icon-square-btn"
          title={item.label}
          aria-label={item.label}
          on:click={item.action}
          disabled={item.disabled}
        >
          {#if item.icon}
            <svelte:component this={item.icon} size={22} color="#fff" />
          {/if}
          <span class="tooltip" aria-hidden="true">{item.label}</span>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .stained-glass-side {
    position: absolute;
    top: calc(var(--ui-top-offset) + 1.2rem);
    right: 1.2rem;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 0.6rem 0.5rem;
    border-radius: 0;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    z-index: 10;
    backdrop-filter: var(--glass-filter);
    max-height: calc(100% - var(--ui-top-offset) - 1.6rem);
    overflow: auto;
    align-items: center;
    min-width: 140px;
  }
  .primary-items {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    width: 100%;
    align-items: center;
  }
  .icon-btn {
    background: rgba(255,255,255,0.10);
    border: none;
    border-radius: 0;
    width: 100%;
    min-height: 3.2rem;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    cursor: pointer;
    transition: background 0.18s, box-shadow 0.18s;
    box-shadow: 0 1px 4px 0 rgba(0,40,120,0.10);
    padding: 0.4rem 0.6rem;
  }
  .btn-content {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
  }
  .icon {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .label {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 0.9rem;
    font-weight: 500;
    color: #fff;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    white-space: nowrap;
  }
  .icon-btn:hover {
    background: rgba(120,180,255,0.22);
  }
  .icon-btn:active {
    background: rgba(80,140,220,0.28);
  }
  .icon-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }
  .quick-links {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    padding-bottom: 0.8rem; /* more breathing room under the icons */
  }
  /* Quick links: match top-left nav icon button style */
  .icon-square-btn {
    background: rgba(255,255,255,0.10);
    border: none;
    border-radius: 0;
    width: 2.9rem;
    height: 2.9rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.18s, box-shadow 0.18s;
    box-shadow: 0 1px 4px 0 rgba(0,40,120,0.10);
    position: relative;
  }
  .icon-square-btn:hover,
  .icon-square-btn:focus-visible {
    background: rgba(120,180,255,0.22);
    outline: none;
  }
  .icon-square-btn:active {
    background: rgba(80,140,220,0.28);
  }
  .icon-square-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }
  .icon-square-btn .tooltip {
    position: absolute;
    bottom: calc(100% + 0.4rem);
    left: 50%;
    transform: translate(-50%, 0.2rem);
    background: rgba(20,30,60,0.92);
    color: #fff;
    padding: 0.2rem 0.5rem;
    border-radius: 0.35rem;
    font-size: 0.75rem;
    white-space: nowrap;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.18s ease, transform 0.18s ease;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
  }
  .icon-square-btn:hover .tooltip,
  .icon-square-btn:focus-visible .tooltip {
    opacity: 1;
    transform: translate(-50%, 0);
  }
</style>
