<script>
  export let lrmModel = '';
  export let lrmOptions = [];
  export let handleModelChange;
  export let handleTestModel;
  export let testReply = '';
</script>

<div class="settings-panel">
  <div class="control" title="Select language reasoning model.">
    <div class="control-left">
      <span class="label">LRM Model</span>
    </div>
    <div class="control-right">
      <select bind:value={lrmModel} on:change={handleModelChange}>
        {#each lrmOptions as opt}
          <option value={opt}>{opt}</option>
        {/each}
      </select>
    </div>
  </div>
  <div class="control" title="Send a sample prompt to the selected model.">
    <div class="control-left">
      <span class="label">Test Model</span>
    </div>
    <div class="control-right">
      <button class="icon-btn" on:click={handleTestModel}>Test</button>
    </div>
  </div>
  {#if testReply}
    <p class="status" data-testid="lrm-test-reply">{testReply}</p>
  {/if}
</div>

<style>
  @import './settings-shared.css';
</style>
