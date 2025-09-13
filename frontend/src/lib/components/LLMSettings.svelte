<script>
  export let lrmModel = '';
  export let lrmOptions = [];
  export let handleModelChange;
  export let handleTestModel;
  export let testReply = '';
</script>

<div class="settings-panel">
  <div class="control" title="Select language reasoning model.">
    <label>LRM Model</label>
    <select bind:value={lrmModel} on:change={handleModelChange}>
      {#each lrmOptions as opt}
        <option value={opt}>{opt}</option>
      {/each}
    </select>
  </div>
  <div class="control" title="Send a sample prompt to the selected model.">
    <label>Test Model</label>
    <button on:click={handleTestModel}>Test</button>
  </div>
  {#if testReply}
    <p class="status" data-testid="lrm-test-reply">{testReply}</p>
  {/if}
</div>

<style src="./settings-shared.css"></style>
