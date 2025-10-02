<script>
  import PopupWindow from './PopupWindow.svelte';
  import { createEventDispatcher } from 'svelte';
  import { FEEDBACK_URL, CONTACT_EMAIL, BACKEND_LOGS_PATH_HINT } from '../systems/constants.js';

  export let message = 'The backend encountered a critical error.';
  export let traceback = '';
  export let status = 500;
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  $: githubIssueUrl = `${FEEDBACK_URL}?title=${encodeURIComponent(`Backend shutdown (${status})`)}&body=${encodeURIComponent(`### What happened?\nThe backend shut down after returning status ${status}.\n\n### Error message\n${message}\n\n### Traceback\n\n\`\`\`\n${traceback}\n\`\`\`\n\n### Logs\nPlease attach the JSON logs from ${BACKEND_LOGS_PATH_HINT}.`)}`;
  $: mailtoUrl = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent('Midori AI AutoFighter backend shutdown')}&body=${encodeURIComponent(`The backend shut down after returning status ${status}.\n\nError message: ${message}\n\nTraceback:\n${traceback}\n\nLogs: (please attach JSON files from ${BACKEND_LOGS_PATH_HINT})`)}`;

  function openIssue() {
    window.open(githubIssueUrl, '_blank', 'noopener');
  }

  function emailSupport() {
    window.open(mailtoUrl, '_blank', 'noopener');
  }

  async function copyLogsPath() {
    try {
      await navigator.clipboard.writeText(BACKEND_LOGS_PATH_HINT);
      copyState = 'copied';
      setTimeout(() => { copyState = 'idle'; }, 2000);
    } catch (error) {
      console.error('Failed to copy logs path:', error);
      copyState = 'error';
      setTimeout(() => { copyState = 'idle'; }, 2000);
    }
  }

  let copyState = 'idle';

  function close() {
    dispatch('close');
  }
</script>

<PopupWindow title="Backend Shutting Down" {reducedMotion} on:close={close}>
  <div class="content">
    <p class="lead">The backend reported a critical error (status {status}) and is shutting down.</p>
    <p>
      Please collect the JSON log files from <code>{BACKEND_LOGS_PATH_HINT}</code> (including any
      <code>battle_summary.json</code> and <code>events.json</code> files) and attach them when you reach out so we can investigate.
    </p>
    <p>
      You can <button class="link-btn" type="button" on:click={openIssue}>open a GitHub issue</button>
      or email us at <button class="link-btn" type="button" on:click={emailSupport}>{CONTACT_EMAIL}</button>.
    </p>

    <details class="error-details">
      <summary>Error details</summary>
      <pre>{message}\n\n{traceback}</pre>
    </details>

    <div class="actions">
      <button class="icon-btn" type="button" on:click={copyLogsPath}>
        {#if copyState === 'copied'}Copied path!{/if}
        {#if copyState === 'error'}Copy failed{/if}
        {#if copyState === 'idle'}Copy logs path{/if}
      </button>
      <button class="icon-btn" type="button" on:click={openIssue}>Report on GitHub</button>
      <button class="icon-btn" type="button" on:click={emailSupport}>Email support</button>
      <button class="icon-btn" type="button" on:click={close}>Close</button>
    </div>
  </div>
</PopupWindow>

<style>
  .content {
    padding: 0.75rem 0.5rem;
    line-height: 1.45;
  }

  .lead {
    font-weight: 600;
  }

  code {
    font-family: "Fira Code", "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.85rem;
    background: rgba(255, 255, 255, 0.12);
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
  }

  .link-btn {
    background: none;
    border: none;
    color: #8dd8ff;
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
    font: inherit;
  }

  .link-btn:hover,
  .link-btn:focus {
    color: #b4e5ff;
  }

  .error-details {
    margin: 0.75rem 0;
    background: rgba(0, 0, 0, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.15);
  }

  .error-details summary {
    cursor: pointer;
    padding: 0.35rem 0.5rem;
    font-weight: 600;
    list-style: none;
  }

  .error-details pre {
    margin: 0;
    padding: 0.5rem;
    max-height: 40vh;
    overflow: auto;
    white-space: pre-wrap;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 0.75rem;
    padding: 0.5rem 0.7rem;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
  }

  .icon-btn {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 0;
    color: #fff;
    padding: 0.35rem 0.6rem;
    cursor: pointer;
  }

  .icon-btn:hover,
  .icon-btn:focus {
    background: rgba(255, 255, 255, 0.2);
  }
</style>
