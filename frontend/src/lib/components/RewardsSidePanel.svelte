<script>
  import LoginRewardsPanel from './LoginRewardsPanel.svelte';
</script>

<div class="rewards-side-panel">
  <LoginRewardsPanel embedded={true} flat={true} />
  <div class="panel-spacer" aria-hidden="true"></div>
</div>

<style>
  .rewards-side-panel {
    position: absolute;
    left: calc(1.2rem + 420px + 2rem);
    top: calc(var(--ui-top-offset) + 1.2rem);
    width: 360px;
    height: 70%;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
    padding: 0.8rem;
    z-index: 10;
    overflow-y: auto;
  }

  .panel-spacer { flex: 1 1 auto; }

  @media (max-width: 1024px) {
    .rewards-side-panel { width: 320px; }
  }

  @media (max-width: 599px) {
    .rewards-side-panel {
      position: relative;
      left: 0;
      top: 0;
      width: 100%;
      height: auto;
      margin: 0.75rem 0 0 0;
    }
  }
</style>
