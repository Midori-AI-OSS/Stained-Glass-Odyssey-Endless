<script>
  import { browser } from '$app/environment';
  import { createEventDispatcher, onDestroy, onMount } from 'svelte';

  import MenuPanel from './MenuPanel.svelte';
  import PartyPicker from './PartyPicker.svelte';
  import { formatPercent } from '../utils/upgradeFormatting.js';
  import {
    getRunConfigurationMetadata,
    logMenuAction
  } from '../systems/uiApi.js';

  const STORAGE_KEY = 'run_wizard_defaults_v1';
  const STEP_SEQUENCE = ['resume', 'party', 'run-type', 'modifiers', 'confirm'];

  export let runs = [];
  export let reducedMotion = false;

  const dispatch = createEventDispatcher();

  let step = 'resume';
  let metadataLoading = false;
  let metadataError = '';
  let metadata = null;
  let runTypes = [];
  let modifiers = [];
  let modifierMap = new Map();
  let runTypeId = '';
  let modifierValues = {};
  let modifierDirty = {};
  let partySelection = [];
  let damageType = '';
  let resumeIndex = -1;
  let submitting = false;
  let persistedDefaults = null;
  let visitedSteps = new Set();
  let wizardSessionId = '';
  let completed = false;

  const hasOwn = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);

  let normalizedRuns = [];
  let visibleSteps = STEP_SEQUENCE;
  let currentStepIndex = 0;

  $: normalizedRuns = Array.isArray(runs) ? runs : [];
  $: if (normalizedRuns.length === 0 && step === 'resume') {
    step = 'party';
  }
  $: if (normalizedRuns.length > 0 && (resumeIndex < 0 || resumeIndex >= normalizedRuns.length)) {
    resumeIndex = 0;
  } else if (normalizedRuns.length === 0 && resumeIndex !== -1) {
    resumeIndex = -1;
  }

  $: hasRuns = normalizedRuns.length > 0;
  $: visibleSteps = STEP_SEQUENCE.filter((key) => !(key === 'resume' && !hasRuns));
  $: totalSteps = visibleSteps.length;
  $: currentStepIndex = Math.max(0, visibleSteps.indexOf(step));
  $: activeRunType = runTypes.find((rt) => rt.id === runTypeId) || runTypes[0] || null;
  $: selectedModifiers = modifiers.map((mod) => ({
    ...mod,
    value: sanitizeStack(mod.id, modifierValues[mod.id])
  }));
  $: pressureValue = sanitizeStack('pressure', modifierValues.pressure);
  $: rewardPreview = computeRewardPreview(modifierValues);
  $: stepTitle = deriveStepTitle(step);
  $: resumeDisabled = resumeIndex < 0 || resumeIndex >= normalizedRuns.length;
  $: partySummary = partySelection.slice(0, 5);

  onMount(() => {
    resumeIndex = normalizedRuns.length > 0 ? 0 : -1;
    wizardSessionId = createSessionId();
    loadPersistedDefaults();
    initializeFromPersistence();
    if (!hasRuns) {
      step = 'party';
    }
    void fetchMetadata();
    logStepImpression(step);
    logWizardEvent('opened', { run_count: normalizedRuns.length });
  });

  onDestroy(() => {
    if (!completed) {
      logWizardEvent('abandoned', { step, run_type: runTypeId });
    }
  });

  function createSessionId() {
    if (typeof crypto !== 'undefined' && crypto?.randomUUID) {
      return crypto.randomUUID();
    }
    return `wizard-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
  }

  function deriveStepTitle(current) {
    switch (current) {
      case 'resume':
        return 'Resume or Start';
      case 'party':
        return 'Build Your Party';
      case 'run-type':
        return 'Choose Run Type';
      case 'modifiers':
        return 'Configure Modifiers';
      case 'confirm':
        return 'Review & Start';
      default:
        return 'Run Setup';
    }
  }

  function loadPersistedDefaults() {
    if (!browser) return;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        persistedDefaults = parsed;
        if (Array.isArray(parsed.party)) {
          partySelection = [...parsed.party].slice(0, 5);
        }
        if (parsed.damageType) {
          damageType = String(parsed.damageType);
        }
      }
    } catch (err) {
      console.warn('Failed to load run wizard defaults', err);
    }
  }

  function initializeFromPersistence() {
    if (persistedDefaults?.runTypeId) {
      runTypeId = String(persistedDefaults.runTypeId);
    }
  }

  async function fetchMetadata() {
    metadataLoading = true;
    metadataError = '';
    try {
      const payload = await getRunConfigurationMetadata({ suppressOverlay: true });
      metadata = payload || {};
      runTypes = Array.isArray(payload?.run_types) ? payload.run_types : [];
      modifiers = Array.isArray(payload?.modifiers) ? payload.modifiers : [];
      modifierMap = new Map(modifiers.map((entry) => [entry.id, entry]));

      if (!runTypeId || !runTypes.some((rt) => rt.id === runTypeId)) {
        runTypeId = runTypes[0]?.id || 'standard';
      }

      const baseState = buildBaseModifierState();
      modifierValues = baseState.values;
      modifierDirty = baseState.dirty;

      applyRunTypeDefaults(runTypeId, { resetDirty: true });

      if (persistedDefaults?.modifiers && typeof persistedDefaults.modifiers === 'object') {
        const overrides = persistedDefaults.modifiers;
        for (const [modId, raw] of Object.entries(overrides)) {
          if (!modifierMap.has(modId)) continue;
          const sanitized = sanitizeStack(modId, raw);
          modifierValues = { ...modifierValues, [modId]: sanitized };
          modifierDirty = { ...modifierDirty, [modId]: true };
        }
      }

      persistDefaults();
      logWizardEvent('metadata_loaded', {
        version: payload?.version || null,
        run_type: runTypeId
      });
    } catch (err) {
      metadataError = err?.message || 'Failed to load run configuration metadata.';
      logWizardEvent('metadata_error', { message: metadataError });
    } finally {
      metadataLoading = false;
    }
  }

  function buildBaseModifierState() {
    const values = {};
    const dirty = {};
    for (const entry of modifiers) {
      const def = entry?.stacking || {};
      const base = sanitizeStack(entry.id, hasOwn(def, 'default') ? def.default : def.minimum);
      values[entry.id] = base;
      dirty[entry.id] = false;
    }
    return { values, dirty };
  }

  function sanitizeStack(modId, rawValue) {
    const definition = modifierMap.get(modId);
    if (!definition) {
      if (modId === 'pressure') {
        return Number.isFinite(Number(rawValue)) ? Math.max(0, Math.floor(Number(rawValue))) : 0;
      }
      return 0;
    }
    const stacking = definition.stacking || {};
    const minimum = Number.isFinite(Number(stacking.minimum)) ? Number(stacking.minimum) : 0;
    const maximum = Number.isFinite(Number(stacking.maximum)) ? Number(stacking.maximum) : null;
    const step = Number.isFinite(Number(stacking.step)) && Number(stacking.step) > 0 ? Number(stacking.step) : 1;
    let value = Number(rawValue);
    if (!Number.isFinite(value)) {
      value = Number(stacking.default ?? minimum ?? 0);
    }
    if (!Number.isFinite(value)) value = 0;
    value = Math.floor(value);
    if (value < minimum) value = minimum;
    if (maximum !== null && value > maximum) value = maximum;
    if (step > 1) {
      value = Math.round(value / step) * step;
      if (value < minimum) value = minimum;
      if (maximum !== null && value > maximum) value = maximum;
    }
    return value;
  }

  function applyRunTypeDefaults(targetId, { resetDirty = false } = {}) {
    const runType = runTypes.find((rt) => rt.id === targetId);
    if (!runType) return;
    const defaults = runType.default_modifiers || {};
    const nextValues = { ...modifierValues };
    const nextDirty = resetDirty ? { ...modifierDirty } : modifierDirty;

    // Reset non-dirty modifiers to their base defaults
    if (resetDirty) {
      for (const entry of modifiers) {
        if (!nextDirty[entry.id]) {
          nextValues[entry.id] = sanitizeStack(entry.id, entry.stacking?.default ?? entry.stacking?.minimum ?? 0);
        }
      }
    }

    for (const [modId, raw] of Object.entries(defaults)) {
      if (!modifierMap.has(modId)) continue;
      nextValues[modId] = sanitizeStack(modId, raw);
      if (resetDirty) {
        nextDirty[modId] = false;
      }
    }

    modifierValues = nextValues;
    if (resetDirty) {
      modifierDirty = nextDirty;
    }
  }

  function persistDefaults() {
    if (!browser) return;
    try {
      const payload = {
        runTypeId,
        modifiers: modifierValues,
        party: partySelection.slice(0, 5),
        damageType
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (err) {
      console.warn('Failed to persist run wizard defaults', err);
    }
  }

  function logStepImpression(targetStep) {
    if (!targetStep || visitedSteps.has(targetStep)) return;
    visitedSteps = new Set(visitedSteps).add(targetStep);
    logWizardEvent('step_impression', { step: targetStep, run_type: runTypeId });
  }

  function logWizardEvent(event, detail = {}) {
    const payload = {
      session: wizardSessionId,
      step,
      run_type: runTypeId,
      metadata_version: metadata?.version || null,
      ...detail
    };
    logMenuAction('RunWizard', event, payload).catch(() => {});
  }

  function goToStep(target) {
    if (!STEP_SEQUENCE.includes(target)) return;
    if (target === 'resume' && !hasRuns) {
      step = 'party';
    } else {
      step = target;
    }
    logStepImpression(step);
    persistDefaults();
  }

  function handleResume() {
    if (resumeDisabled) return;
    const selected = normalizedRuns[resumeIndex];
    if (!selected) return;
    completed = true;
    logWizardEvent('resume_selected', { run_id: selected.run_id });
    dispatch('choose', { run: selected });
    dispatch('load', { run: selected });
  }

  function handlePartySave() {
    if (!partySelection.length) return;
    logWizardEvent('party_confirmed', { party_size: partySelection.length });
    goToStep('run-type');
  }

  function handlePartyCancel() {
    if (hasRuns) {
      goToStep('resume');
    } else {
      completed = true;
      dispatch('cancel');
    }
  }

  function handleRunTypeSelect(id) {
    if (!id || id === runTypeId) return;
    if (!runTypes.some((rt) => rt.id === id)) return;
    runTypeId = id;
    applyRunTypeDefaults(runTypeId, { resetDirty: true });
    persistDefaults();
    logWizardEvent('run_type_selected', { run_type: runTypeId });
  }

  function handleModifierChange(modId, raw) {
    if (!modifierMap.has(modId)) return;
    const sanitized = sanitizeStack(modId, raw);
    modifierValues = { ...modifierValues, [modId]: sanitized };
    modifierDirty = { ...modifierDirty, [modId]: true };
    persistDefaults();
    logWizardEvent('modifier_adjusted', { modifier: modId, value: sanitized });
  }

  function resetModifiers() {
    for (const entry of modifiers) {
      modifierDirty[entry.id] = false;
    }
    modifierDirty = { ...modifierDirty };
    applyRunTypeDefaults(runTypeId, { resetDirty: true });
    persistDefaults();
    logWizardEvent('modifiers_reset', { run_type: runTypeId });
  }

  function goToModifiers() {
    logWizardEvent('run_type_confirmed', { run_type: runTypeId });
    goToStep('modifiers');
  }

  function goToConfirm() {
    logWizardEvent('modifiers_confirmed', {
      run_type: runTypeId,
      modifiers: summarizeActiveModifiers()
    });
    goToStep('confirm');
  }

  function summarizeActiveModifiers() {
    const summary = {};
    for (const entry of modifiers) {
      const value = sanitizeStack(entry.id, modifierValues[entry.id]);
      if (value > (entry.stacking?.minimum ?? 0)) {
        summary[entry.id] = value;
      }
    }
    return summary;
  }

  function startRun() {
    if (submitting) return;
    submitting = true;
    const payload = {
      party: partySelection.slice(0, 5),
      damageType,
      pressure: pressureValue,
      runType: runTypeId,
      modifiers: normalizeModifierPayload(),
      metadataVersion: metadata?.version || null
    };
    completed = true;
    logWizardEvent('start_submitted', {
      run_type: runTypeId,
      modifiers: payload.modifiers,
      party_size: payload.party.length,
      pressure: payload.pressure
    });
    dispatch('startRun', payload);
    setTimeout(() => {
      submitting = false;
    }, 500);
  }

  function normalizeModifierPayload() {
    const payload = {};
    for (const entry of modifiers) {
      payload[entry.id] = sanitizeStack(entry.id, modifierValues[entry.id]);
    }
    return payload;
  }

  function handleCancel() {
    completed = true;
    logWizardEvent('cancelled', { step });
    dispatch('cancel');
  }

  function computeRewardPreview(values) {
    const result = {
      foe_bonus: 0,
      player_bonus: 0,
      exp_bonus: 0,
      rdr_bonus: 0
    };
    if (!modifiers.length) return result;
    let foeStacks = 0;
    for (const entry of modifiers) {
      const stacks = sanitizeStack(entry.id, values[entry.id]);
      if (entry.grants_reward_bonus) {
        foeStacks += stacks;
      }
      if (entry.id === 'character_stat_down') {
        const bonus = stacks > 0 ? 0.05 + Math.max(0, stacks - 1) * 0.06 : 0;
        result.player_bonus = Number(bonus.toFixed(4));
      }
    }
    result.foe_bonus = Number((foeStacks * 0.5).toFixed(4));
    result.exp_bonus = Number((result.foe_bonus + result.player_bonus).toFixed(4));
    result.rdr_bonus = result.exp_bonus;
    return result;
  }

  function modifierLabel(mod) {
    return mod?.label || mod?.id || 'Modifier';
  }

  function modifierDescription(mod) {
    return mod?.description || '';
  }

  function pressureTooltip() {
    return metadata?.pressure?.tooltip || '';
  }

  function isActiveModifier(mod) {
    const value = sanitizeStack(mod.id, modifierValues[mod.id]);
    return value > (mod.stacking?.minimum ?? 0);
  }

  function formatRewardBonus(value) {
    if (!Number.isFinite(value)) return '0%';
    return formatPercent(value);
  }
</script>

<svelte:window on:keydown={(event) => {
  if (event.key === 'Escape') {
    handleCancel();
  }
}} />

<MenuPanel
  class="run-wizard"
  data-step={step}
  padding="var(--menu-panel-padding, clamp(0.65rem, 1.8vw, 1.1rem))"
  {reducedMotion}
>
  <div class="wizard">
    <header class="wizard-header">
      <h2>{stepTitle}</h2>
      <div class="step-indicator" aria-hidden="true">
        {#each visibleSteps as key, index}
          <span class:selected={key === step} class:done={index < currentStepIndex}>
            {index + 1}
          </span>
        {/each}
      </div>
    </header>

    {#if step === 'resume'}
      <div class="resume-panel step-surface">
        {#if normalizedRuns.length > 0}
          <div class="runs" role="list">
            {#each normalizedRuns as run, i}
              <label class="run-item" role="listitem">
                <input
                  type="radio"
                  name="resume-run"
                  bind:group={resumeIndex}
                  value={i}
                />
                <div class="summary">
                  <div class="id">{run.run_id}</div>
                  <div class="details">
                    Floor {run?.map?.floor || 1}, Room {run?.map?.current || 1}, Pressure {run?.map?.rooms?.[0]?.pressure ?? 0}
                  </div>
                </div>
              </label>
            {/each}
          </div>
          <div class="actions">
            <button class="icon-btn" on:click={handleResume} disabled={resumeDisabled}>Resume Run</button>
            <button class="icon-btn primary" on:click={() => goToStep('party')}>Start Guided Setup</button>
          </div>
        {:else}
          <p>No active runs found.</p>
          <div class="actions">
            <button class="icon-btn primary" on:click={() => goToStep('party')}>Start Guided Setup</button>
          </div>
        {/if}
      </div>
    {:else if step === 'party'}
      <div class="party-step">
        <PartyPicker
          bind:selected={partySelection}
          allowElementChange={true}
          actionLabel="Continue"
          {reducedMotion}
          on:save={handlePartySave}
          on:cancel={handlePartyCancel}
          on:editorChange={(event) => {
            const detail = event.detail || {};
            if (detail?.damageType) {
              damageType = String(detail.damageType);
              persistDefaults();
            }
          }}
        />
      </div>
    {:else if step === 'run-type'}
      <div class="run-type-panel step-surface">
        {#if metadataLoading}
          <p class="loading">Loading configuration...</p>
        {:else if metadataError}
          <div class="error">
            <p>{metadataError}</p>
            <button class="icon-btn" on:click={() => fetchMetadata()}>Retry</button>
          </div>
        {:else}
          <div class="run-types" role="list">
            {#each runTypes as rt}
              <button
                type="button"
                class="run-type-card"
                class:active={rt.id === runTypeId}
                on:click={() => handleRunTypeSelect(rt.id)}
                role="listitem"
              >
                <div class="card-title">{rt.label}</div>
                <p class="card-description">{rt.description}</p>
                {#if Object.keys(rt.default_modifiers || {}).length > 0}
                  <div class="card-defaults">
                    <strong>Defaults</strong>
                    <ul>
                      {#each Object.entries(rt.default_modifiers || {}) as [key, value]}
                        <li>{modifierMap.get(key)?.label || key}: {value}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <div class="navigation">
        <button class="ghost" on:click={() => goToStep('party')}>Back</button>
        <button class="primary" on:click={goToModifiers} disabled={!runTypeId || metadataLoading || metadataError}>Next</button>
      </div>
    {:else if step === 'modifiers'}
      <div class="modifier-panel step-surface">
        {#if metadataLoading}
          <p class="loading">Loading configuration...</p>
        {:else if metadataError}
          <div class="error">
            <p>{metadataError}</p>
            <button class="icon-btn" on:click={() => fetchMetadata()}>Retry</button>
          </div>
        {:else}
          <div class="modifier-toolbar">
            <div>
              <strong>Pressure:</strong>
              <span class="pressure-value">{pressureValue}</span>
            </div>
            {#if pressureTooltip()}
              <p class="pressure-tooltip">{pressureTooltip()}</p>
            {/if}
            <button class="icon-btn" on:click={resetModifiers}>Reset to {activeRunType?.label || 'defaults'}</button>
          </div>
          <div class="modifiers" role="list">
            {#each selectedModifiers as mod}
              <div class="modifier" role="listitem">
                <div class="modifier-header">
                  <div>
                    <span class="modifier-label">{modifierLabel(mod)}</span>
                    {#if mod.category}
                      <span class="modifier-category">{mod.category}</span>
                    {/if}
                  </div>
                  <div class="modifier-inputs">
                    <label>
                      <span class="sr-only">Stacks</span>
                      <input
                        type="number"
                        min={mod.stacking?.minimum ?? 0}
                        step={mod.stacking?.step ?? 1}
                        max={Number.isFinite(mod.stacking?.maximum) ? mod.stacking.maximum : undefined}
                        value={sanitizeStack(mod.id, modifierValues[mod.id])}
                        on:change={(event) => handleModifierChange(mod.id, event.target.value)}
                      />
                    </label>
                  </div>
                </div>
                {#if modifierDescription(mod)}
                  <p class="modifier-description">{modifierDescription(mod)}</p>
                {/if}
              </div>
            {/each}
          </div>
          <div class="reward-preview">
            <div>
              <strong>Reward Preview</strong>
            </div>
            <div class="preview-grid">
              <div>
                <span class="preview-label">EXP Bonus</span>
                <span class="preview-value">{formatRewardBonus(rewardPreview.exp_bonus)}</span>
              </div>
              <div>
                <span class="preview-label">RDR Bonus</span>
                <span class="preview-value">{formatRewardBonus(rewardPreview.rdr_bonus)}</span>
              </div>
              <div>
                <span class="preview-label">Foe Bonus</span>
                <span class="preview-value">{formatRewardBonus(rewardPreview.foe_bonus)}</span>
              </div>
              <div>
                <span class="preview-label">Player Bonus</span>
                <span class="preview-value">{formatRewardBonus(rewardPreview.player_bonus)}</span>
              </div>
            </div>
          </div>
        {/if}
      </div>
      <div class="navigation">
        <button class="ghost" on:click={() => goToStep('run-type')}>Back</button>
        <button class="primary" on:click={goToConfirm} disabled={metadataLoading || metadataError}>Next</button>
      </div>
    {:else if step === 'confirm'}
      <div class="confirm-panel step-surface">
        <section>
          <h3>Party</h3>
          <ul>
            {#each partySummary as member}
              <li>{member}</li>
            {/each}
          </ul>
        </section>
        <section>
          <h3>Run Type</h3>
          <p>{activeRunType?.label || runTypeId}</p>
          <p class="card-description">{activeRunType?.description}</p>
        </section>
        <section>
          <h3>Modifiers</h3>
          {#if selectedModifiers.some(isActiveModifier)}
            <ul>
              {#each selectedModifiers.filter(isActiveModifier) as mod}
                <li>{modifierLabel(mod)}: {sanitizeStack(mod.id, modifierValues[mod.id])}</li>
              {/each}
            </ul>
          {:else}
            <p>No additional modifiers selected.</p>
          {/if}
        </section>
        <section>
          <h3>Reward Preview</h3>
          <div class="preview-grid">
            <div>
              <span class="preview-label">EXP Bonus</span>
              <span class="preview-value">{formatRewardBonus(rewardPreview.exp_bonus)}</span>
            </div>
            <div>
              <span class="preview-label">RDR Bonus</span>
              <span class="preview-value">{formatRewardBonus(rewardPreview.rdr_bonus)}</span>
            </div>
            <div>
              <span class="preview-label">Foe Bonus</span>
              <span class="preview-value">{formatRewardBonus(rewardPreview.foe_bonus)}</span>
            </div>
            <div>
              <span class="preview-label">Player Bonus</span>
              <span class="preview-value">{formatRewardBonus(rewardPreview.player_bonus)}</span>
            </div>
          </div>
        </section>
      </div>
      <div class="navigation">
        <button class="ghost" on:click={() => goToStep('modifiers')}>Back</button>
        <button class="primary" on:click={startRun} disabled={submitting}>Start Run</button>
      </div>
    {/if}
  </div>
</MenuPanel>

<style>
  .wizard {
    --wizard-max-width: 100%;
    --wizard-inner-max-width: 100%;
    --wizard-section-gap: clamp(0.65rem, 1.8vw, 1.1rem);
    --wizard-item-gap: clamp(0.45rem, 1.4vw, 0.8rem);
    --wizard-action-gap: clamp(0.55rem, 1.6vw, 0.95rem);
    display: flex;
    flex-direction: column;
    gap: var(--wizard-section-gap);
    width: var(--wizard-max-width);
    max-width: var(--wizard-max-width);
    flex: 1 1 auto;
    align-self: stretch;
    margin: 0;
    min-height: 0;
  }

  .wizard > * {
    min-width: 0;
  }

  .wizard-header,
  .step-surface,
  .navigation {
    width: min(100%, var(--wizard-inner-max-width));
    margin-left: auto;
    margin-right: auto;
  }

  .wizard-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: clamp(0.6rem, 1.6vw, 1rem);
    flex-wrap: wrap;
  }

  .wizard-header h2 {
    margin: 0;
    font-size: clamp(1.25rem, 2.2vw, 1.6rem);
    font-weight: 600;
    flex: 1 1 auto;
    min-width: min(12rem, 100%);
  }

  .step-indicator {
    display: inline-flex;
    flex-wrap: wrap;
    gap: clamp(0.35rem, 1vw, 0.55rem);
    justify-content: flex-end;
  }

  .step-indicator span {
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.3);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    opacity: 0.5;
  }

  .step-indicator span.selected {
    background: rgba(120, 180, 255, 0.3);
    opacity: 1;
  }

  .step-indicator span.done {
    background: rgba(120, 180, 255, 0.16);
    opacity: 0.85;
  }

  .step-surface {
    width: 100%;
    box-sizing: border-box;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: clamp(0.65rem, 1.8vw, 1.1rem);
    display: flex;
    flex-direction: column;
    gap: var(--wizard-section-gap);
  }

  .resume-panel {
    padding: clamp(0.55rem, 1.6vw, 0.9rem);
  }

  .runs {
    display: flex;
    flex-direction: column;
    gap: var(--wizard-item-gap);
    margin: 0;
  }

  .run-item {
    display: flex;
    gap: clamp(0.55rem, 1.4vw, 0.9rem);
    align-items: flex-start;
    background: rgba(255, 255, 255, 0.06);
    padding: clamp(0.5rem, 1.5vw, 0.85rem);
    min-width: 0;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .run-item input {
    margin-top: 0.25rem;
  }

  .summary {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    flex: 1 1 auto;
    min-width: 0;
  }

  .id {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 0.8rem;
    opacity: 0.9;
    word-break: break-word;
  }

  .details {
    font-size: 0.85rem;
    opacity: 0.85;
    line-height: 1.35;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--wizard-action-gap);
    margin-top: clamp(0.35rem, 1vw, 0.6rem);
    flex-wrap: wrap;
  }

  .icon-btn {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 0;
    padding: clamp(0.45rem, 1.4vw, 0.75rem) clamp(0.75rem, 2vw, 1.2rem);
    cursor: pointer;
    color: inherit;
    transition: background 0.18s ease;
  }

  .actions .icon-btn {
    flex: 1 1 160px;
    min-width: min(220px, 100%);
  }

  .icon-btn:hover {
    background: rgba(120, 180, 255, 0.22);
  }

  .icon-btn.primary {
    background: rgba(120, 180, 255, 0.28);
  }

  .icon-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .party-step {
    display: flex;
    flex-direction: column;
    gap: var(--wizard-section-gap);
  }

  .navigation {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: var(--wizard-action-gap);
    flex-wrap: wrap;
    margin-top: clamp(0.35rem, 1vw, 0.6rem);
  }

  .navigation button {
    padding: clamp(0.5rem, 1.5vw, 0.85rem) clamp(1rem, 2.6vw, 1.6rem);
    border: none;
    cursor: pointer;
    border-radius: 0;
    font-size: 0.95rem;
    flex: 1 1 160px;
    min-width: min(220px, 100%);
  }

  .navigation .ghost {
    background: transparent;
    color: inherit;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .navigation .primary {
    background: rgba(120, 180, 255, 0.35);
    color: inherit;
  }

  .navigation button:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .run-types {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: var(--wizard-item-gap);
  }

  .run-type-card {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid transparent;
    padding: clamp(0.65rem, 1.6vw, 1rem);
    text-align: left;
    cursor: pointer;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.6rem);
    min-width: 0;
  }

  .run-type-card:hover,
  .run-type-card.active {
    border-color: rgba(120, 180, 255, 0.5);
    background: rgba(120, 180, 255, 0.12);
  }

  .card-title {
    font-weight: 600;
    margin: 0;
  }

  .card-description {
    font-size: 0.9rem;
    opacity: 0.85;
    margin: 0;
    line-height: 1.45;
  }

  .card-defaults {
    margin: 0;
    font-size: 0.85rem;
    opacity: 0.85;
    line-height: 1.35;
  }

  .card-defaults ul {
    margin: 0.25rem 0 0;
    padding-left: 1rem;
  }

  .modifier-panel {
    display: flex;
    flex-direction: column;
    gap: var(--wizard-section-gap);
  }

  .modifier-toolbar {
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.6rem);
    background: rgba(255, 255, 255, 0.05);
    padding: clamp(0.55rem, 1.6vw, 0.9rem) clamp(0.7rem, 2vw, 1.2rem);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .pressure-value {
    font-weight: 600;
    margin-left: 0.35rem;
  }

  .pressure-tooltip {
    font-size: 0.85rem;
    opacity: 0.8;
    margin: 0;
  }

  .modifiers {
    display: flex;
    flex-direction: column;
    gap: var(--wizard-item-gap);
    max-height: clamp(260px, 50vh, 420px);
    overflow-y: auto;
    padding-right: 0.35rem;
  }

  .modifier {
    background: rgba(255, 255, 255, 0.05);
    padding: clamp(0.6rem, 1.6vw, 1rem);
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.55rem);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .modifier-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: clamp(0.45rem, 1.2vw, 0.75rem);
    flex-wrap: wrap;
  }

  .modifier-label {
    font-weight: 600;
  }

  .modifier-category {
    font-size: 0.75rem;
    opacity: 0.7;
    margin-left: 0.4rem;
    text-transform: uppercase;
  }

  .modifier-inputs {
    display: flex;
    flex-wrap: wrap;
    gap: clamp(0.35rem, 1vw, 0.6rem);
    align-items: center;
  }

  .modifier-inputs input {
    width: 5rem;
    padding: 0.35rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: inherit;
  }

  .modifier-description {
    font-size: 0.85rem;
    opacity: 0.82;
    margin: 0;
    line-height: 1.4;
  }

  .reward-preview {
    display: flex;
    flex-direction: column;
    gap: clamp(0.4rem, 1.2vw, 0.7rem);
  }

  .preview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: var(--wizard-item-gap);
  }

  .preview-label {
    font-size: 0.75rem;
    opacity: 0.75;
    display: block;
  }

  .preview-value {
    font-size: 1rem;
    font-weight: 600;
  }

  .confirm-panel {
    display: grid;
    gap: var(--wizard-section-gap);
  }

  .confirm-panel section {
    background: rgba(255, 255, 255, 0.05);
    padding: clamp(0.65rem, 1.6vw, 1rem);
    display: flex;
    flex-direction: column;
    gap: clamp(0.35rem, 1vw, 0.6rem);
  }

  .confirm-panel h3 {
    margin: 0;
  }

  .confirm-panel ul,
  .confirm-panel p {
    margin: 0;
  }

  .loading {
    opacity: 0.8;
  }

  .error {
    display: flex;
    flex-direction: column;
    gap: clamp(0.45rem, 1.2vw, 0.7rem);
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  @media (min-width: 768px) {
    .actions .icon-btn,
    .navigation button {
      flex: 0 0 auto;
      min-width: 0;
    }
  }

  @media (max-width: 720px) {
    .wizard {
      --wizard-inner-max-width: 100%;
    }

    .wizard-header {
      align-items: flex-start;
    }

    .step-indicator {
      justify-content: flex-start;
    }

    .actions,
    .navigation {
      justify-content: stretch;
    }

    .actions .icon-btn,
    .navigation button {
      flex: 1 1 120px;
    }
  }

  @media (max-width: 480px) {
    .step-indicator span {
      width: 1.5rem;
      height: 1.5rem;
      font-size: 0.8rem;
    }

    .run-types {
      grid-template-columns: minmax(0, 1fr);
    }

    .modifier-inputs input {
      width: min(100%, 5.5rem);
    }
  }
</style>
