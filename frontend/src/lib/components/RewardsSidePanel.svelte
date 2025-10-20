<script>
  import LoginRewardsPanel from './LoginRewardsPanel.svelte';
  import { rewardPhaseState } from '../systems/overlayState.js';

  const DEFAULT_PHASE_SEQUENCE = ['drops', 'cards', 'relics', 'battle_review'];
  const PHASE_LABELS = {
    drops: 'Drops',
    cards: 'Cards',
    relics: 'Relics',
    battle_review: 'Battle Review'
  };

  $: phaseSnapshot = $rewardPhaseState;
  $: phaseSequence =
    Array.isArray(phaseSnapshot?.sequence) && phaseSnapshot.sequence.length > 0
      ? phaseSnapshot.sequence
      : DEFAULT_PHASE_SEQUENCE;
  $: completedPhaseSet = new Set(Array.isArray(phaseSnapshot?.completed) ? phaseSnapshot.completed : []);
  $: currentPhase = phaseSnapshot?.current ?? null;
  $: phaseEntries = phaseSequence.map((phase, index) => {
    const label = PHASE_LABELS[phase] ?? phase.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    const status = completedPhaseSet.has(phase)
      ? 'complete'
      : phase === currentPhase
        ? 'active'
        : 'pending';
    return {
      phase,
      label,
      index: index + 1,
      status
    };
  });
</script>

<div class="rewards-side-panel">
  <LoginRewardsPanel embedded={true} flat={true} />
  <section class="phase-panel" aria-label="Reward flow">
    <h3>Reward Flow</h3>
    <ol class="phase-list" role="list">
      {#each phaseEntries as entry (entry.phase)}
        <li
          class={`phase-item ${entry.status}`}
          role="listitem"
          aria-current={entry.status === 'active' ? 'step' : undefined}
        >
          <span class="phase-index" aria-hidden="true">{entry.status === 'complete' ? '✓' : entry.index}</span>
          <span class="phase-label">{entry.label}</span>
        </li>
      {/each}
    </ol>
  </section>
  <div class="panel-spacer" aria-hidden="true"></div>
</div>

<style>
  .rewards-side-panel {
    position: relative;
    width: 360px;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    background: var(--glass-bg);
    box-shadow: var(--glass-shadow);
    border: var(--glass-border);
    backdrop-filter: var(--glass-filter);
    padding: 0.8rem;
    box-sizing: border-box;
    overflow-y: auto;
  }

  .phase-panel {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem 0.85rem;
    border-radius: 16px;
    background: rgba(12, 18, 28, 0.72);
    border: 1px solid rgba(153, 201, 255, 0.2);
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.28);
    color: rgba(241, 245, 255, 0.92);
  }

  .phase-panel h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .phase-list {
    margin: 0;
    padding: 0;
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  .phase-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0.6rem;
    border-radius: 12px;
    background: rgba(9, 14, 22, 0.68);
    border: 1px solid rgba(153, 201, 255, 0.18);
    font-size: 0.9rem;
  }

  .phase-item.complete {
    background: rgba(58, 164, 108, 0.22);
    border-color: rgba(76, 175, 80, 0.35);
  }

  .phase-item.active {
    background: rgba(52, 120, 207, 0.3);
    border-color: rgba(90, 170, 255, 0.45);
    box-shadow: 0 0 0 1px rgba(90, 170, 255, 0.3);
  }

  .phase-index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.6rem;
    height: 1.6rem;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.35);
    font-weight: 700;
  }

  .phase-item.complete .phase-index {
    background: rgba(76, 175, 80, 0.45);
  }

  .phase-item.active .phase-index {
    background: rgba(90, 170, 255, 0.45);
  }

  .phase-label {
    flex: 1 1 auto;
    font-weight: 600;
  }

  .panel-spacer { flex: 1 1 auto; }

  @media (max-width: 1024px) {
    .rewards-side-panel { width: 320px; }
  }

  @media (max-width: 599px) {
    .rewards-side-panel {
      position: relative;
      width: 100%;
      height: auto;
      margin: 0.5rem 0 0 0;
    }
  }
</style>
