<script>
  import LoginRewardsPanel from './LoginRewardsPanel.svelte';
</script>

<div class="rewards-side-panel">
  <LoginRewardsPanel embedded={true} flat={true} />
  <div class="panel-spacer" aria-hidden="true"></div>
</div>

<style>
  .rewards-side-panel {
    position: relative;
    width: 360px;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
    padding: 0.8rem;
    box-sizing: border-box;
    overflow-y: auto;
  }

  .panel-spacer { flex: 1 1 auto; }

  @media (max-width: 1024px) {
    .rewards-side-panel { width: 320px; }
  }

  @media (max-width: 599px) {
    .rewards-side-panel {
      position: relative;
      width: 100%;
      height: auto;
      margin: 0.5rem 0 0 0;
    }
  }
</style>
