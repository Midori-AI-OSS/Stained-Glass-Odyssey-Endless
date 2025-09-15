<script>
  import { hpPercent } from '../../battle/shared.js';
  export let hp = 0;
  export let maxHp = 1;
</script>

<div class="stat hp-status">
  <label>HP:</label>
  <span>
    {hp}/{maxHp} ({Math.round(hpPercent(hp, maxHp) * 100)}%)
  </span>
</div>
