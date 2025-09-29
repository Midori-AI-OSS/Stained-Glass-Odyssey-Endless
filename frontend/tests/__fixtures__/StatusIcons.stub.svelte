<script>
  export let fighter = {};
  export let compact = false;
</script>

<div data-testid="status-icons" data-fighter={fighter?.id ?? ''} data-compact={compact ? 'yes' : 'no'}></div>
