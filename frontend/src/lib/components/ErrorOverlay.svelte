<script>
  import { createEventDispatcher } from 'svelte';
  import PopupWindow from './PopupWindow.svelte';
  import { FEEDBACK_URL } from '../systems/constants.js';

  export let message = '';
  export let traceback = '';
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();
  let reportUrl = '';

  $: reportUrl = `${FEEDBACK_URL}?title=${encodeURIComponent(message)}&body=${encodeURIComponent('```\n' + traceback + '\n```')}`;

  function report() {
    window.open(reportUrl, '_blank', 'noopener');
  }

  function close() {
    dispatch('close');
  }
</script>

<PopupWindow title="Error" {reducedMotion} on:close={close}>
  <div style="padding: 0.5rem 0.25rem; line-height: 1.4;">
    <pre>{message}\n{traceback}</pre>
    <div class="stained-glass-row" style="justify-content: flex-end; margin-top: 0.75rem;">
      <button class="icon-btn" on:click={report}>Report Issue</button>
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

  pre {
    white-space: pre-wrap;
    max-height: 60vh;
    overflow: auto;
    background: rgba(0,0,0,0.5);
    padding: 0.5rem;
    margin: 0;
  }
</style>
