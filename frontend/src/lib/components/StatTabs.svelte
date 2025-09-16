<script context="module">
  // Cache per-character editor values across component instances
  export const editorConfigs = new Map();
</script>

<script>
  /*
   * StatTabs.svelte
   *
   * Renders the character stats panel used by the Party Picker (right column).
   * Features:
   * - Tabbed view (Core, Offense, Defense).
   * - Shows the currently previewed character's stats.
   * - Embeds a slim Character Editor inside the panel for both player and
   *   non‑player characters, allowing percent tweaks to HP, Attack, Defense,
   *   Crit Rate, and Crit Damage. Player changes auto‑save via API.
   */
  import { getElementIcon, getElementColor } from '../systems/assetLoader.js';
  import { createEventDispatcher } from 'svelte';
  import CharacterEditor from './CharacterEditor.svelte';
  import { getPlayerConfig, savePlayerConfig, getCharacterConfig, saveCharacterConfig, getUpgrade, upgradeCharacter } from '../systems/api.js';

  /**
   * Renders the stats panel with category tabs and a toggle control.
   *
   * Props:
   * - roster: array of character objects
   * - previewId: ID of character to show stats for
   * - selected: array of selected character IDs
   *
   * Events:
  * - toggle: dispatched with the previewId when Add/Remove is clicked
  */
  export let roster = [];
  export let previewId;
  export let selected = [];
  export let userBuffPercent = 0;

  const statTabs = ['Core', 'Offense', 'Defense'];
  let activeTab = 'Core';
  const dispatch = createEventDispatcher();

  // Previewed character and inline editor overlay state
  let previewChar;
  let isPlayer = false;
  let editorVals = null; // { pronouns, damageType, hp, attack, defense, critRate, critDamage }
  let savedEditor = null; // snapshot of saved config to compute deltas
  let viewStats = {};    // stats object used for display (with overrides when player)
  let loadingEditorCfg = false;
  let saveTimer = null;
  let lastPreviewId = null; // track last character ID to detect switches

  // Upgrade system state
  let upgradeData = null;
  let loadingUpgrade = false;
  let upgradeMessage = '';

  function scheduleSave() {
    if (!editorVals || !previewChar) return;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      const payload = {
        pronouns: editorVals.pronouns || '',
        damage_type: editorVals.damageType || 'Light',
        hp: Number(editorVals.hp) || 0,
        attack: Number(editorVals.attack) || 0,
        defense: Number(editorVals.defense) || 0,
        crit_rate: Number(editorVals.critRate) || 0,
        crit_damage: Number(editorVals.critDamage) || 0,
      };
      try {
        await saveCharacterConfig(previewChar.id, payload);
        if (isPlayer) {
          await savePlayerConfig(payload);
        }
        editorConfigs.set(previewChar.id, { ...editorVals });
        savedEditor = { ...editorVals };
        if (!isPlayer) {
          dispatch('refresh-roster');
        }
      } catch {}
    }, 400);
  }

  // Load upgrade data for the current character
  async function loadUpgradeData() {
    if (!previewChar) {
      upgradeData = null;
      return;
    }
    
    loadingUpgrade = true;
    upgradeMessage = '';
    try {
      upgradeData = await getUpgrade(previewChar.id);
    } catch (e) {
      upgradeData = null;
      upgradeMessage = 'Failed to load upgrade data';
    } finally {
      loadingUpgrade = false;
    }
  }

  // Handle spending 4-star items to increase point cap (new button flow)
  async function handleUpgrade() {
    if (!previewChar || !canUpgrade) return;
    
    upgradeMessage = '';
    try {
      await upgradeCharacter(previewChar.id, 4, 1);
      await loadUpgradeData(); // Refresh upgrade data
      upgradeMessage = 'Upgrade successful! +1 point to allocation cap.';
    } catch (e) {
      upgradeMessage = e?.message || 'Upgrade failed';
    }
  }

  // Resolve selected entry and whether it's the Player
  $: previewChar = roster.find(r => r.id === previewId);
  $: isPlayer = !!previewChar?.is_player;

  // Load upgrade data when the previewed character changes (robust, independent of editor flow)
  let lastUpgradeForId = null;
  $: if (previewChar?.id && lastUpgradeForId !== previewChar.id && !loadingUpgrade) {
    lastUpgradeForId = previewChar.id;
    loadUpgradeData();
  }

  // Check if character can upgrade (has 4-star items available)
  $: canUpgrade = (() => {
    if (!previewChar || !upgradeData?.items || loadingUpgrade) return false;
    
    const items = upgradeData.items;
    if (isPlayer) {
      // Player can use 4-star items of any element
      return Object.entries(items)
        .filter(([k]) => k.endsWith('_4'))
        .some(([, v]) => (v || 0) > 0);
    } else {
      // Other characters need 4-star items matching their element
      const element = previewChar.element?.toLowerCase() || '';
      return (items[`${element}_4`] || 0) > 0;
    }
  })();

  // Calculate max points (base 100 + upgrade count)
  // Each 4-star item costs 3,375,000 points, convert back to upgrade count
  $: upgradeCount = Math.floor((upgradeData?.upgrade_points || 0) / 3375000);
  $: maxPoints = 100 + upgradeCount;

  // Lazy‑load the saved Player Editor config when the player is selected.
  $: if (previewChar) {
    if (lastPreviewId !== previewId) {
      editorVals = null;
      loadingEditorCfg = false;
      lastPreviewId = previewId;
    }

    const cached = editorConfigs.get(previewChar.id);
    if (cached) {
      editorVals = { ...cached };
      savedEditor = { ...cached };
    } else if (!loadingEditorCfg) {
      loadingEditorCfg = true;
      (async () => {
        try {
          let cfg;
          if (isPlayer) {
            cfg = await getPlayerConfig();
          } else {
            cfg = await getCharacterConfig(previewChar.id);
          }
          editorVals = {
            pronouns: isPlayer ? (cfg?.pronouns || '') : (previewChar.pronouns || ''),
            damageType: isPlayer ? (cfg?.damage_type || 'Light') : (previewChar.element || 'Light'),
            hp: Number(cfg?.hp) || 0,
            attack: Number(cfg?.attack) || 0,
            defense: Number(cfg?.defense) || 0,
            critRate: Number(cfg?.crit_rate) || 0,
            critDamage: Number(cfg?.crit_damage) || 0,
          };
          savedEditor = { ...editorVals };
          editorConfigs.set(previewChar.id, { ...editorVals });
          if (isPlayer) {
            try { dispatch('preview-element', { element: editorVals.damageType }); } catch {}
          }
        } catch {
          editorVals = {
            pronouns: previewChar.pronouns || '',
            damageType: previewChar.element || 'Light',
            hp: 0,
            attack: 0,
            defense: 0,
            critRate: 0,
            critDamage: 0,
          };
          savedEditor = { ...editorVals };
          editorConfigs.set(previewChar.id, { ...editorVals });
          if (isPlayer) {
            try { dispatch('preview-element', { element: editorVals.damageType }); } catch {}
          }
        } finally {
          loadingEditorCfg = false;
        }
      })();
    }
  } else {
    editorVals = null;
    lastPreviewId = null;
  }
  // Compute displayed stats - use backend-computed stats which already include all effects
  $: {
    const statsObj = previewChar?.stats || {};
    const baseStats = statsObj.base_stats || {};
    const result = { ...statsObj };

    // Apply live editor preview changes on top of computed stats
    if (editorVals) {
      const saved = savedEditor || { hp: 0, attack: 0, defense: 0, critRate: 0, critDamage: 0 };
      const hpDelta = (Number(editorVals.hp) || 0) - (Number(saved.hp) || 0);
      const atkDelta = (Number(editorVals.attack) || 0) - (Number(saved.attack) || 0);
      const defDelta = (Number(editorVals.defense) || 0) - (Number(saved.defense) || 0);
      const critRateDelta = (Number(editorVals.critRate) || 0) - (Number(saved.critRate) || 0);
      const critDamageDelta = (Number(editorVals.critDamage) || 0) - (Number(saved.critDamage) || 0);

      // Apply deltas to the already-computed stats (not base stats)
      const currentMax = Number(statsObj.max_hp) || Number(baseStats.max_hp) || 1000;
      const currentAtk = Number(statsObj.atk) || Number(baseStats.atk) || 100;
      const currentDef = Number(statsObj.defense) || Number(baseStats.defense) || 50;
      const currentCritRate = Number(statsObj.crit_rate) || Number(baseStats.crit_rate) || 0.05;
      const currentCritDamage = Number(statsObj.crit_damage) || Number(baseStats.crit_damage) || 2.0;

      result.max_hp = Math.round(currentMax * (1 + hpDelta / 100));
      result.atk = Math.round(currentAtk * (1 + atkDelta / 100));
      result.defense = Math.round(currentDef * (1 + defDelta / 100));
      result.crit_rate = currentCritRate * (1 + critRateDelta / 100);
      result.crit_damage = currentCritDamage * (1 + critDamageDelta / 100);

      // Preserve HP ratio against upgraded max
      const hpRatioBase = Number(statsObj.hp) / Math.max(1, currentMax);
      result.hp = Math.round(result.max_hp * Math.max(0, Math.min(1, isFinite(hpRatioBase) ? hpRatioBase : 1)));
    }

    viewStats = result;
  }

  function toggleMember() {
    if (!previewId) return;
    dispatch('toggle', previewId);
  }

  // Helper function to format stat display
  // Supports percentage-style values by multiplying by 100 when suffix === '%'.
  function formatStat(runtimeValue, baseValue, suffix = '') {
    const isPercent = suffix === '%';
    const rv = runtimeValue == null ? null : (isPercent ? runtimeValue * 100 : runtimeValue);
    const bv = baseValue == null ? null : (isPercent ? baseValue * 100 : baseValue);

    if (bv !== null && rv !== null && rv !== bv) {
      const modifier = rv - bv;
      const sign = modifier >= 0 ? '+' : '';
      const show = (v) => (Number.isInteger(v) ? v : v.toFixed(1));
      return `${show(rv)}${suffix} (${show(bv)}${sign}${show(modifier)})`;
    }
    if (rv === null) return '-';
    return `${Number.isInteger(rv) ? rv : rv.toFixed(1)}${suffix}`;
  }

  // Helper to format multiplier-style values (e.g., 1.0 -> 1x)
  function formatMult(runtimeValue, baseValue) {
    const rv = runtimeValue == null ? null : Number(runtimeValue);
    const bv = baseValue == null ? null : Number(baseValue);
    const show = (v) => {
      if (v == null || !isFinite(v)) return '-';
      // Prefer integer when close, else show up to 2 decimals
      const rounded = Math.round(v);
      return Math.abs(v - rounded) < 1e-6 ? String(rounded) : v.toFixed(2);
    };
    if (rv === null) return '-';
    if (bv !== null && rv !== bv) {
      const modifier = rv - bv;
      const sign = modifier >= 0 ? '+' : '';
      return `${show(rv)}x (${show(bv)}${sign}${show(modifier)})`;
    }
    return `${show(rv)}x`;
  }

  // Helper to get base stat value (legacy).
  // In current in-run refactor, base comparisons may be unavailable;
  // this returns undefined to suppress base deltas unless provided.
  function getBaseStat(character, statName) {
    return character.stats?.base_stats?.[statName];
  }
</script>

<div class="stats-panel" data-testid="stats-panel">
  <div class="stats-tabs">
    {#each statTabs as tab}
      <button class="tab-btn" class:active={activeTab === tab} on:click={() => activeTab = tab}>
        {tab}
      </button>
    {/each}
  </div>
  {#if previewId}
    {#each roster.filter(r => r.id === previewId) as sel}
      <div class="stats-header">
        <span class="char-name">{sel.name}</span>
        <span class="char-level">Lv {sel.stats.level}</span>
        <svelte:component
          this={getElementIcon((isPlayer && editorVals?.damageType) ? editorVals.damageType : sel.element)}
          class="type-icon"
          style={`color: ${getElementColor((isPlayer && editorVals?.damageType) ? editorVals.damageType : sel.element)}`}
          aria-hidden="true" />
      </div>
      {#if sel.about}
        <div class="char-about">{sel.about}</div>
        <div class="inline-divider" aria-hidden="true"></div>
      {/if}
      <div class="stats-list">
        {#if activeTab === 'Core'}
          <div>
            <span>HP</span>
            <span>
              {#if viewStats.max_hp != null}
                {(viewStats.hp ?? 0) + '/' + formatStat(viewStats.max_hp, getBaseStat(sel, 'max_hp'))}
              {:else}
                {viewStats.hp ?? '-'}
              {/if}
            </span>
          </div>
          <div><span>EXP</span><span>{sel.stats.exp ?? sel.stats.xp ?? '-'}</span></div>
          <div><span>Vitality</span><span>{formatMult(sel.stats.vitality ?? sel.stats.vita, getBaseStat(sel, 'vitality'))}</span></div>
          <div><span>Regain</span><span>{formatStat(sel.stats.regain ?? sel.stats.regain_rate, getBaseStat(sel, 'regain'))}</span></div>
          <div class="buff-note">Global Buff: +{userBuffPercent}%</div>
        {:else if activeTab === 'Offense'}
          <div><span>ATK</span><span>{formatStat(viewStats.atk, getBaseStat(sel, 'atk'))}</span></div>
          <div><span>CRIT Rate</span><span>{formatStat(viewStats.crit_rate, getBaseStat(sel, 'crit_rate'), '%')}</span></div>
          <div><span>CRIT DMG</span><span>{formatStat(viewStats.crit_damage, getBaseStat(sel, 'crit_damage'), '%')}</span></div>
          <div><span>Effect Hit Rate</span><span>{formatStat(viewStats.effect_hit_rate, getBaseStat(sel, 'effect_hit_rate'), '%')}</span></div>
        {:else if activeTab === 'Defense'}
          <div><span>DEF</span><span>{formatStat(viewStats.defense, getBaseStat(sel, 'defense'))}</span></div>
          <div><span>Mitigation</span><span>{formatMult(viewStats.mitigation, getBaseStat(sel, 'mitigation'))}</span></div>
          <div><span>Dodge Odds</span><span>{formatStat(viewStats.dodge_odds, getBaseStat(sel, 'dodge_odds'), '%')}</span></div>
          <div><span>Effect Resist</span><span>{formatStat(viewStats.effect_resistance, getBaseStat(sel, 'effect_resistance'), '%')}</span></div>
        {/if}
      </div>
    {/each}
  {:else}
    <div class="stats-placeholder">Select a character to view stats</div>
  {/if}
  {#if previewId}
    <div class="stats-confirm">
      {#if selected.includes(previewId) && isPlayer}
        <button class="confirm" disabled title="The player must stay in the party">Player is required</button>
      {:else}
        <button class="confirm" on:click={toggleMember}>
          {selected.includes(previewId) ? 'Remove from party' : 'Add to party'}
        </button>
      {/if}
    </div>
  {/if}
  {#if previewId}
    {#each roster.filter(r => r.id === previewId) as sel}
      <!-- Inline editor and upgrade region -->
      <div class="hello-anchor">
        <div class="inline-divider" aria-hidden="true"></div>
        <div class="editor-wrap">
          <CharacterEditor
            embedded={true}
            showIdentity={sel.is_player}
            maxPoints={maxPoints}
            pronouns={editorVals?.pronouns || ''}
            damageType={editorVals?.damageType || 'Light'}
            hp={editorVals?.hp || 0}
            attack={editorVals?.attack || 0}
            defense={editorVals?.defense || 0}
            critRate={editorVals?.critRate || 0}
            critDamage={editorVals?.critDamage || 0}
            on:change={(e) => { editorVals = e.detail; editorConfigs.set(previewId, { ...editorVals }); if (sel.is_player) { try { dispatch('preview-element', { element: editorVals.damageType }); } catch {} } dispatch('editor-change', { id: previewId, config: editorVals }); scheduleSave(); }}
          />
          
          <!-- Upgrade button for spending 4-star items (always visible; disabled when unavailable) -->
          <div class="upgrade-section">
            <button class="upgrade-btn" on:click={handleUpgrade} disabled={!canUpgrade || loadingUpgrade}>
              Upgrade
            </button>
            <p class="upgrade-hint">
              {#if loadingUpgrade}
                Checking materials...
              {:else if !canUpgrade}
                Need 1× 4★ {isPlayer ? 'any element' : (sel.element || '').toLowerCase()} item
              {:else}
                Spend 1× 4★ damage item to increase allocation cap
              {/if}
            </p>
          </div>
          
          {#if upgradeMessage}
            <div class="upgrade-message" class:success={upgradeMessage.includes('successful')}>
              {upgradeMessage}
            </div>
          {/if}
        </div>
      </div>
    {/each}
  {/if}
</div>

<style>
.stats-panel {
  flex: 1;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.25);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-sizing: border-box;
  border-radius: 8px;
  position: relative; /* allow absolute positioning for anchored elements */
}
.stats-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-bottom: 1px solid rgba(255,255,255,0.2);
  padding-bottom: 0.5rem;
}
.char-name { font-size: 1.2rem; color: #fff; flex: 1; }
.char-level { font-size: 1rem; color: #ccc; }
.type-icon { width: 24px; height: 24px; }
.buff-note { font-size: 0.85rem; color: #ccc; margin-bottom: 0.3rem; }
.char-about { margin: 0.25rem 0; font-style: italic; }
.stats-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.stats-list div { display: flex; justify-content: space-between; color: #ddd; }
.stats-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  font-style: italic;
}
.stats-confirm {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  min-height: 32px;
  padding: 0.15rem 0;
  margin-top: 0.25rem;
}
button.confirm {
  background: rgba(0,0,0,0.5);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.35);
  padding: 0.45rem 0.8rem;
  align-self: flex-end;
  font-size: 0.95rem;
  min-height: 28px;
  border-radius: 0;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}
button.confirm:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.5); }
.stats-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.tab-btn {
  background: rgba(255,255,255,0.1);
  color: #ddd;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}
.tab-btn.active { background: rgba(255,255,255,0.3); color: #fff; }

/* Divider and inline half-height spacer below stats within panel */
.inline-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent);
  margin: 0 0 0.35rem 0;
}
/* Inline container flows naturally below stats */
.hello-anchor { margin-top: 0.5rem; }

/* Inline container occupying 50% of the stats panel width */
.editor-wrap { width: 100%; }

/* Upgrade section styling */
.upgrade-section {
  margin-top: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255,255,255,0.2);
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.upgrade-btn {
  background: rgba(0,0,0,0.5);
  color: #fff;
  border: 1px solid rgba(255,255,255,0.35);
  padding: 0.45rem 0.8rem;
  border-radius: 0;
  font-weight: 400;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
  align-self: flex-start;
}

.upgrade-btn:hover:not(:disabled) {
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.5);
}

.upgrade-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.upgrade-hint {
  margin: 0;
  font-size: 0.75rem;
  color: #ccc;
  opacity: 0.8;
}

.upgrade-message {
  margin-top: 0.5rem;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  background: rgba(255, 0, 0, 0.1);
  border: 1px solid rgba(255, 0, 0, 0.3);
  color: #ffaaaa;
}

.upgrade-message.success {
  background: rgba(0, 255, 0, 0.1);
  border-color: rgba(0, 255, 0, 0.3);
  color: #aaffaa;
}
</style>
