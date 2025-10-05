<script>
  import { createEventDispatcher } from 'svelte';

  export let selected = [];
  export let actionLabel = 'Continue';
  export let allowElementChange = false;
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  function commitSelection() {
    selected = ['unit-1', 'unit-2'];
    dispatch('editorChange', { damageType: 'fire' });
  }

  function emitSave() {
    dispatch('save');
  }

  function emitCancel() {
    dispatch('cancel');
  }
</script>

<div data-testid="party-picker-stub" data-action-label={actionLabel} data-allow-element-change={allowElementChange} data-reduced-motion={reducedMotion}>
  <button type="button" data-testid="set-party" on:click={commitSelection}>Set Party</button>
  <button type="button" data-testid="save-party" on:click={emitSave}>Save Party</button>
  <button type="button" data-testid="cancel-party" on:click={emitCancel}>Cancel</button>
</div>
