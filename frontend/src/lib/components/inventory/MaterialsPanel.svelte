<script>
  import { getMaterialIcon, onIconError } from '../../systems/materialAssetLoader.js';
  export let materials = [];
  export let select = () => {};
</script>

<div class="materials-grid">
  {#each materials as [id, qty]}
    <div class="material" on:click={() => select(id, 'material', qty)}>
      <img src={getMaterialIcon(id)} alt={id} on:error={onIconError} />
      <span class="qty">{qty}</span>
    </div>
  {/each}
</div>
