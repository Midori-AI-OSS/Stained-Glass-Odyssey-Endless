<script>
  import { createEventDispatcher } from 'svelte';
  import ErrorOverlay from './ErrorOverlay.svelte';
  import { FEEDBACK_URL } from '../systems/constants.js';
  import PopupWindow from './PopupWindow.svelte';

  export let errors = [];
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  $: latestError = errors.length > 0 ? errors[errors.length - 1] : null;
  $: issueUrl = latestError ? buildIssueUrl(latestError) : '';

  function buildIssueUrl(error) {
    if (!error) return FEEDBACK_URL;
    const title = encodeURIComponent(`[Crash] ${error.message || 'Unknown error'}`);
    const body = encodeURIComponent(formatIssueBody(error));
    return `${FEEDBACK_URL}?title=${title}&body=${body}`;
  }

  function formatIssueBody(error) {
    if (!error) return '';

    const lines = [
      '## Crash Report',
      '',
      `**Error:** ${error.message || 'Unknown error'}`,
      '',
      `**Timestamp:** ${error.timestamp || 'Unknown'}`,
      '',
      `**Error ID:** ${error.id || 'Unknown'}`,
      '',
    ];

    if (error.traceback) {
      lines.push('### Traceback', '```', error.traceback, '```', '');
    }

    if (error.context) {
      lines.push(
        '### Context',
        `- **File:** ${error.context.file || 'Unknown'}`,
        `- **Line:** ${error.context.line || 'Unknown'}`,
        `- **Function:** ${error.context.function || 'Unknown'}`,
        ''
      );

      if (Array.isArray(error.context.source) && error.context.source.length > 0) {
        lines.push('### Source', '```');
        for (const line of error.context.source) {
          const marker = line.highlight ? '>' : ' ';
          lines.push(`${marker} ${String(line.line).padStart(4, ' ')} | ${line.code || ''}`);
        }
        lines.push('```', '');
      }
    }

    if (error.metadata && Object.keys(error.metadata).length > 0) {
      lines.push('### Metadata', '```json', JSON.stringify(error.metadata, null, 2), '```');
    }

    return lines.join('\n');
  }

  function reportIssue() {
    window.open(issueUrl, '_blank', 'noopener');
  }

  async function acknowledgeAndClose() {
    try {
      await fetch('/api/acknowledge-errors', { method: 'POST' });
    } catch (e) {
      console.warn('Failed to acknowledge errors:', e);
    }
    dispatch('close');
  }
</script>

<PopupWindow title="Previous Session Crashed" {reducedMotion} on:close={acknowledgeAndClose}>
  <div class="crash-recovery">
    <p class="crash-message">
      The game encountered an error in your last session. Please consider reporting this issue to help us improve.
    </p>

    {#if latestError}
      <div class="error-details">
        <div class="error-header">
          <span class="error-severity {latestError.severity || 'error'}">{latestError.severity || 'error'}</span>
          <span class="error-time">{latestError.timestamp ? new Date(latestError.timestamp).toLocaleString() : ''}</span>
        </div>
        <p class="error-text">{latestError.message || 'Unknown error'}</p>
        {#if latestError.traceback}
          <pre class="error-traceback">{latestError.traceback}</pre>
        {/if}
        {#if latestError.context}
          <div class="context-block">
            <div class="context-header">
              <span class="context-file" title={latestError.context.file}>{latestError.context.file}</span>
              <span class="context-line">:{latestError.context.line}</span>
              {#if latestError.context.function}
                <span class="context-func"> · {latestError.context.function}</span>
              {/if}
            </div>
            {#if Array.isArray(latestError.context.source) && latestError.context.source.length > 0}
              <div class="context-source">
                {#each latestError.context.source as line (line.line)}
                  <div class:highlight={line.highlight}>
                    <span class="line-number">{line.line}</span>
                    <span class="line-code">{line.code}</span>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}

    {#if errors.length > 1}
      <p class="additional-errors">+ {errors.length - 1} more error(s) from previous sessions</p>
    {/if}

    <div class="actions">
      <button class="btn primary" on:click={reportIssue}>
        Report on GitHub
      </button>
      <button class="btn secondary" on:click={acknowledgeAndClose}>
        Dismiss
      </button>
    </div>
  </div>
</PopupWindow>

<style>
  .crash-recovery {
    padding: 0.5rem 0.25rem;
    line-height: 1.4;
  }

  .crash-message {
    margin: 0 0 1rem 0;
    color: rgba(255, 255, 255, 0.9);
  }

  .error-details {
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 0.75rem;
    margin-bottom: 1rem;
  }

  .error-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .error-severity {
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-size: 0.75rem;
    text-transform: uppercase;
    font-weight: 600;
  }

  .error-severity.critical {
    background: rgba(220, 38, 38, 0.3);
    color: #fca5a5;
  }

  .error-severity.error {
    background: rgba(234, 88, 12, 0.3);
    color: #fdba74;
  }

  .error-severity.warning {
    background: rgba(202, 138, 4, 0.3);
    color: #fde047;
  }

  .error-severity.info {
    background: rgba(37, 99, 235, 0.3);
    color: #93c5fd;
  }

  .error-time {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.6);
  }

  .error-text {
    margin: 0 0 0.5rem 0;
    font-weight: 600;
    color: #fff;
  }

  .error-traceback {
    white-space: pre-wrap;
    max-height: 30vh;
    overflow: auto;
    background: rgba(0, 0, 0, 0.5);
    padding: 0.5rem;
    margin: 0;
    font-size: 0.8rem;
  }

  .context-block {
    margin-top: 0.75rem;
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .context-header {
    font-family: var(--font-mono, 'Fira Code', monospace);
    font-size: 0.85rem;
    padding: 0.5rem 0.6rem;
    background: rgba(0, 0, 0, 0.45);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .context-source {
    font-family: var(--font-mono, 'Fira Code', monospace);
    max-height: 20vh;
    overflow: auto;
    padding: 0.35rem 0.6rem 0.6rem;
    background: rgba(0, 0, 0, 0.35);
  }

  .context-source div {
    display: grid;
    grid-template-columns: 3rem 1fr;
    gap: 0.5rem;
    align-items: baseline;
    padding: 0.2rem 0.25rem;
    border-left: 3px solid transparent;
  }

  .context-source div.highlight {
    background: rgba(235, 87, 87, 0.15);
    border-left-color: #eb5757;
  }

  .line-number {
    color: rgba(255, 255, 255, 0.6);
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .line-code {
    white-space: pre;
  }

  .additional-errors {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.6);
    margin: 0 0 1rem 0;
    font-style: italic;
  }

  .actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    padding: 0.5rem 0;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
  }

  .btn {
    background: rgba(255, 255, 255, 0.10);
    border: none;
    border-radius: 0;
    color: #fff;
    padding: 0.45rem 0.8rem;
    cursor: pointer;
    font-weight: 500;
  }

  .btn.primary {
    background: rgba(37, 99, 235, 0.3);
    border: 1px solid rgba(37, 99, 235, 0.5);
  }

  .btn.primary:hover {
    background: rgba(37, 99, 235, 0.5);
  }

  .btn.secondary:hover {
    background: rgba(255, 255, 255, 0.15);
  }
</style>
