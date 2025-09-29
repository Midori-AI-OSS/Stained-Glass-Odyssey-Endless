<script>
  export let queue = [];
  export let combatants = [];
  export let reducedMotion = false;
  export let effectiveReducedMotion = false;
  export let showActionValues = false;
  export let activeId = null;
  export let currentTurn = null;
  export let enrage = { active: false, stacks: 0, turns: 0 };
  export let showTurnCounter = true;
  export let flashEnrageCounter = true;
</script>

<div
  data-testid="queue-probe"
  data-active-id={activeId ?? ''}
  data-queue-length={Array.isArray(queue) ? queue.length : 0}
></div>
