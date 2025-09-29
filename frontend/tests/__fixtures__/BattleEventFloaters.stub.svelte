<script>
  export let events = [];
  export let reducedMotion = false;
  export let paceMs = 0;
  export let anchors = {};
  export let baseOffsetX = 0;
  export let baseOffsetY = 0;
  export let staggerMs = 0;
</script>

<script>
  $: eventCount = Array.isArray(events) ? events.length : 0;
  $: eventTypes = Array.isArray(events) ? events.map(evt => evt?.type || '').join(',') : '';
  $: totalAmount = Array.isArray(events)
    ? events.reduce((sum, evt) => sum + Number(evt?.amount ?? 0), 0)
    : 0;
</script>

<div
  data-testid="floaters-probe"
  data-count={eventCount}
  data-types={eventTypes}
  data-total={totalAmount}
></div>
