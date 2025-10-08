<script>
  import { createEventDispatcher } from 'svelte';
  import PopupWindow from './PopupWindow.svelte';
  import { FEEDBACK_URL } from '../systems/constants.js';

  export let message = '';
  export let traceback = '';
  export let reducedMotion = false;
  export let context = null;

  const dispatch = createEventDispatcher();
  let reportUrl = '';
  let issueBody = '';
  $: contextSource = Array.isArray(context?.source) ? context.source : [];

  $: issueBody = buildIssueBody(message, traceback, context);
  $: reportUrl = `${FEEDBACK_URL}?title=${encodeURIComponent(message)}&body=${encodeURIComponent(issueBody)}`;

  function report() {
    window.open(reportUrl, '_blank', 'noopener');
  }

  function close() {
    dispatch('close');
  }

  function buildIssueBody(msg, tb, ctx) {
    const lines = [];
    if (msg) {
      lines.push(msg, '');
    }
    if (tb) {
      lines.push('```', tb, '```', '');
    }
    if (ctx && ctx.file) {
      lines.push(`Context: ${ctx.file}:${ctx.line}${ctx.function ? ` (${ctx.function})` : ''}`);
    }
    if (ctx && Array.isArray(ctx.source) && ctx.source.length > 0) {
      lines.push('```');
      for (const line of ctx.source) {
        const marker = line.highlight ? '>' : ' ';
        lines.push(`${marker} ${line.line.toString().padStart(4, ' ')} | ${line.code || ''}`);
      }
      lines.push('```');
    }
    return lines.join('\n');
  }
</script>

<PopupWindow title="Error" {reducedMotion} on:close={close}>
  <div style="padding: 0.5rem 0.25rem; line-height: 1.4;">
    <div class="message-block">
      <p class="error-message">{message}</p>
      {#if traceback}
        <pre class="traceback">{traceback}</pre>
      {/if}
    </div>
    {#if context}
      <div class="context-block">
        <div class="context-header">
          <span class="context-file" title={context.file}>{context.file}</span>
          <span class="context-line">:{context.line}</span>
          {#if context.function}
            <span class="context-func"> · {context.function}</span>
          {/if}
        </div>
        <div class="context-source">
          {#each contextSource as line (line.line)}
            <div class:highlight={line.highlight}>
              <span class="line-number">{line.line}</span>
              <span class="line-code">{line.code}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
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

  .message-block {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .error-message {
    margin: 0;
    font-weight: 600;
    color: #fff;
  }

  .traceback {
    white-space: pre-wrap;
    max-height: 60vh;
    overflow: auto;
    background: rgba(0,0,0,0.5);
    padding: 0.5rem;
    margin: 0;
  }

  .context-block {
    margin-top: 0.75rem;
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.4);
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
    max-height: 50vh;
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
</style>
