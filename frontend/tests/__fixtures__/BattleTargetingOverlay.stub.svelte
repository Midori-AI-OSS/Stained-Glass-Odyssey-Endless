<script>
  export let activeId = null;
  export let activeTargetId = null;
  export let anchors = {};
  export let combatants = [];
  export let events = [];
  export let reducedMotion = false;
  export let turnPhase = null;
</script>

<div
  data-testid="overlay-probe"
  data-phase-state={turnPhase?.state ?? ''}
  data-phase-present={turnPhase ? 'yes' : 'no'}
  data-attacker={activeId ?? ''}
  data-target={activeTargetId ?? ''}
></div>
