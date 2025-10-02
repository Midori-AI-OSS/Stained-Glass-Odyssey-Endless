<script>
  import PopupWindow from './PopupWindow.svelte';
  import { createEventDispatcher } from 'svelte';

  export let apiBase = '';
  export let message = 'Backend is not ready yet.';
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  function retry() {
    window.location.reload();
  }

  function close() {
    dispatch('close');
  }
</script>

<PopupWindow title="Backend Not Ready" {reducedMotion} on:close={close}>
  <div style="padding: 0.5rem 0.25rem; line-height: 1.4;">
    <p>The Web UI cannot reach the backend.</p>
    <p><strong>API:</strong> {apiBase}</p>
    <p style="opacity: 0.85;">{message}</p>
    <p style="margin-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
      <span class="spinner" aria-hidden="true"></span>
      <span>Start the backend service then choose Retry.</span>
    </p>
    <div class="stained-glass-row" style="justify-content: flex-end; margin-top: 0.75rem;">
      <button class="icon-btn" on:click={retry}>Retry</button>
      <button class="icon-btn" on:click={close}>Close</button>
    </div>
  </div>
</PopupWindow>

<style>
  .stained-glass-row {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 0.5rem;
    padding: 0.5rem 0.7rem;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
  }

  .icon-btn {
    background: rgba(255,255,255,0.10);
    border: none;
    border-radius: 0;
    color: #fff;
    padding: 0.35rem 0.6rem;
    cursor: pointer;
  }

  .spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid rgba(255,255,255,0.25);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
    display: inline-block;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>
