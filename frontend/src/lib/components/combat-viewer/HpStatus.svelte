<script>
  import { hpPercent } from '../../battle/shared.js';
  export let hp = 0;
  export let maxHp = 1;
</script>

<div class="hp-status">
  {Math.round(hpPercent(hp, maxHp) * 100)}%
</div>
