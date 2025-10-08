<script>
  import { onMount } from 'svelte';
  import OverlayHost from '$lib/components/OverlayHost.svelte';
  import { openOverlay, homeOverlay } from '$lib';

  // SvelteKit provides `error` and `status` to +error.svelte
  export let error;
  export let status;

  let message = '';
  let traceback = '';

  $: message = (error?.message || error?.toString?.() || 'Unexpected error');
  $: traceback = (error?.stack || '');

  onMount(() => {
    // Route the framework error through our standard popup overlay
    openOverlay('error', { message: `[${status || 'Error'}] ${message}`.trim(), traceback, context: error?.context ?? null });
  });

  function backHome() {
    // Ensure we land on a usable screen even if overlay cannot render
    homeOverlay();
  }
</script>

<div class="host">
  <!-- Mount our overlay system so the Error overlay can render -->
  <OverlayHost />

  <!-- Minimal fallback if overlays fail to mount -->
  <div class="fallback">
    <h2>Something went wrong</h2>
    <p>{message}</p>
    <pre>{traceback}</pre>
    <button on:click={backHome}>Back to Home</button>
  </div>
  
</div>

<style>
  .host { position: relative; min-height: 100vh; background: #000; color: #fff; }
  .fallback { position: absolute; inset: 0; display: grid; place-items: center; padding: 1rem; }
  .fallback pre { max-width: 90vw; max-height: 50vh; overflow: auto; background: rgba(255,255,255,0.05); padding: 0.5rem; }
  .fallback button { background: rgba(255,255,255,0.10); color: #fff; border: none; padding: 0.5rem 0.75rem; cursor: pointer; }
</style>

