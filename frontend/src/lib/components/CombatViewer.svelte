<!--
  CombatViewer.svelte
  Displays detailed combat information with pause/resume functionality.
  Shows character lists, stats, and status effects in a 3-part layout.
-->
<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import MenuPanel from './MenuPanel.svelte';
  import { getCatalogData } from '../systems/uiApi.js';
  import { getElementColor, getCharacterImage } from '../systems/assetLoader.js';
  import PartyRoster from './PartyRoster.svelte';
  import PlayerPreview from './PlayerPreview.svelte';
  import { Circle } from 'lucide-svelte';
  import Spinner from './Spinner.svelte';
  import PartyView from './combat-viewer/PartyView.svelte';
  import FoeView from './combat-viewer/FoeView.svelte';
  import HpStatus from './combat-viewer/HpStatus.svelte';

  export let party = [];
  export let foes = [];
  export let runId = '';
  export let battleSnapshot = null;

  const dispatch = createEventDispatcher();

  let selectedCharacterId = null;
  let activeTab = 'dots';
  let catalogData = {
    relics: [],
    cards: [],
    dots: [],
    hots: []
  };

  // Character selection
  $: allCharacters = [
    ...party.map(p => ({ ...p, type: 'player', element: p.element || p.damage_type || 'Generic' })),
    ...foes.map(f => ({ ...f, type: 'foe', element: f.element || f.damage_type || 'Generic' }))
  ];

  // Build a roster compatible with PartyRoster (read-only)
  $: viewerRoster = allCharacters.map(c => ({
    id: c.id,
    name: c.name || c.id,
    img: getCharacterImage(c.id, c.type === 'player'),
    owned: c.type === 'player',
    is_player: c.type === 'player',
    element: (typeof c.element === 'string' ? c.element : (c.element?.id || 'Generic')),
    stats: {
      level: c.level ?? 1,
      hp: c.hp,
      max_hp: c.max_hp ?? c.hp,
      atk: c.attack ?? c.atk ?? 0,
      defense: c.defense ?? c.def ?? 0,
    }
  }));

  $: selectedCharacter = allCharacters.find(c => c.id === selectedCharacterId) || allCharacters[0];

  // Auto-select first character if none selected
  $: if (!selectedCharacterId && allCharacters.length > 0) {
    selectedCharacterId = allCharacters[0].id;
  }

  // Status effect tabs
  const tabs = [
    { id: 'dots', label: 'DoTs' },
    { id: 'hots', label: 'HoTs' },
    { id: 'buffs', label: 'Buffs' },
    { id: 'debuffs', label: 'Debuffs' },
    { id: 'relics', label: 'Relics' },
    { id: 'cards', label: 'Cards' },
    { id: 'passives', label: 'Passives' }
  ];

  function getCatalogItem(type, id) {
    const items = catalogData[type] || [];
    return items.find(item => item.id === id);
  }

  function getStatusEffects(character, type) {
    if (!character) return [];
    
    switch (type) {
      case 'dots':
        return (character.dots || []).map(dot => {
          const catalogItem = getCatalogItem('dots', dot.id);
          return {
            ...dot,
            about: catalogItem?.about || `Deals ${dot.damage} damage per turn for ${dot.turns} turns`,
            source: 'dot'
          };
        });
      case 'hots':
        return (character.hots || []).map(hot => {
          const catalogItem = getCatalogItem('hots', hot.id);
          return {
            ...hot,
            about: catalogItem?.about || `Heals ${hot.healing} HP per turn for ${hot.turns} turns`,
            source: 'hot'
          };
        });
      case 'buffs':
        // Extract buffs from passives and other effects
        const buffs = [];
        if (character.passives) {
          character.passives.forEach(passive => {
            if (typeof passive === 'object' && passive.name) {
              // Check if it's a positive effect (rough heuristic)
              if (passive.name.toLowerCase().includes('buff') || 
                  passive.name.toLowerCase().includes('boost') ||
                  passive.name.toLowerCase().includes('enhance')) {
                buffs.push({
                  name: passive.name,
                  id: passive.id || passive.name,
                  duration: passive.duration || passive.turns_left || 'Permanent',
                  about: passive.description || 'Beneficial effect',
                  source: 'passive'
                });
              }
            }
          });
        }
        // Add stat modifiers that are positive
        if (character.mods) {
          character.mods.forEach(mod => {
            if (typeof mod === 'object' && mod.name) {
              buffs.push({
                name: mod.name,
                id: mod.id || mod.name,
                duration: mod.turns || 'Permanent',
                about: mod.description || 'Stat modification',
                source: 'modifier'
              });
            }
          });
        }
        return buffs;
      case 'debuffs':
        // Extract debuffs from effects
        const debuffs = [];
        if (character.passives) {
          character.passives.forEach(passive => {
            if (typeof passive === 'object' && passive.name) {
              // Check if it's a negative effect
              if (passive.name.toLowerCase().includes('debuff') ||
                  passive.name.toLowerCase().includes('curse') ||
                  passive.name.toLowerCase().includes('weaken')) {
                debuffs.push({
                  name: passive.name,
                  id: passive.id || passive.name,
                  duration: passive.duration || passive.turns_left || 'Permanent',
                  about: passive.description || 'Harmful effect',
                  source: 'passive'
                });
              }
            }
          });
        }
        return debuffs;
      case 'relics':
        // Get relic effects from battleSnapshot if available
        if (battleSnapshot && battleSnapshot.relics) {
          return battleSnapshot.relics.map(relicId => {
            const catalogItem = getCatalogItem('relics', relicId);
            return {
              name: catalogItem?.name || relicId,
              id: relicId,
              duration: 'Permanent',
              about: catalogItem?.about || 'Relic effect active',
              source: 'relic',
              stars: catalogItem?.stars || 1
            };
          });
        }
        return [];
      case 'cards':
        // Get card effects from battleSnapshot if available
        if (battleSnapshot && battleSnapshot.cards) {
          return battleSnapshot.cards.map(cardId => {
            const catalogItem = getCatalogItem('cards', cardId);
            return {
              name: catalogItem?.name || cardId,
              id: cardId,
              duration: 'Permanent',
              about: catalogItem?.about || 'Card effect active',
              source: 'card',
              stars: catalogItem?.stars || 1
            };
          });
        }
        return [];
      case 'passives':
        if (character.passives) {
          return character.passives.map(passive => {
            if (typeof passive === 'string') {
              return {
                name: passive,
                id: passive,
                duration: 'Permanent',
                about: 'Passive ability',
                source: 'passive',
                stacks: 1,
                max_stacks: 1,
                display: 'spinner',
                overcharged: false
              };
            }
            const stackData = passive.stacks;
            const count = typeof stackData === 'object' ? stackData.mitigation ?? 0 : stackData ?? 1;
            const overcharged = typeof stackData === 'object' && stackData.overcharged;
            const max = passive.max_stacks ?? count ?? 1;
            const display = passive.display ?? (
              passive.max_stacks == null ? 'pips' : passive.max_stacks === 1 ? 'spinner' : 'number'
            );
            return {
              name: passive.name || passive.id || 'Unknown',
              id: passive.id || passive.name || 'unknown',
              duration: passive.duration || passive.turns_left || 'Permanent',
              about: passive.description || 'Passive ability',
              source: 'passive',
              stacks: count,
              max_stacks: max,
              display,
              overcharged
            };
          });
        }
        return [];
      default:
        return [];
    }
  }

  function formatDuration(effect) {
    if (effect.duration !== undefined) {
      if (typeof effect.duration === 'number') {
        return effect.duration > 0 ? `${effect.duration} turns left` : 'Expired';
      }
      return String(effect.duration);
    }
    if (effect.turns_left !== undefined) {
      return `${effect.turns_left} turns left`;
    }
    if (effect.turns !== undefined) {
      return `${effect.turns} turns left`;
    }
    return 'Permanent';
  }

  function formatEffect(effect) {
    let description = effect.name || effect.id || 'Unknown Effect';
    
    // Add amount/damage information
    if (effect.damage !== undefined) {
      description += ` (${effect.damage} damage/turn)`;
    } else if (effect.healing !== undefined) {
      description += ` (${effect.healing} healing/turn)`;
    } else if (effect.amount !== undefined) {
      description += ` (${effect.amount} per turn)`;
    }
    
    // Add stacks information
    if (effect.stacks && effect.stacks > 1) {
      if (!(effect.source === 'passive' && effect.max_stacks && effect.max_stacks <= 5)) {
        description += ` x${effect.stacks}`;
      }
    }

    if (effect.overcharged) {
      description += ' (overcharged)';
    }

    return description;
  }

  function getEffectDetails(effect) {
    const details = [];
    
    if (effect.about) {
      details.push(`Description: ${effect.about}`);
    }
    
    if (effect.damage !== undefined) {
      details.push(`Damage per turn: ${effect.damage}`);
      if (effect.turns && typeof effect.turns === 'number') {
        const totalDamage = effect.damage * effect.turns * (effect.stacks || 1);
        details.push(`Total potential damage: ${totalDamage}`);
      }
    }
    
    if (effect.healing !== undefined) {
      details.push(`Healing per turn: ${effect.healing}`);
      if (effect.turns && typeof effect.turns === 'number') {
        const totalHealing = effect.healing * effect.turns * (effect.stacks || 1);
        details.push(`Total potential healing: ${totalHealing}`);
      }
    }
    
    if (effect.amount !== undefined) {
      details.push(`Amount per turn: ${effect.amount}`);
    }
    
    if (effect.source) {
      details.push(`Source: ${effect.source}`);
    }
    
    if (effect.element && effect.element !== 'Generic') {
      details.push(`Element: ${effect.element}`);
    }
    
    if (effect.stars) {
      details.push(`Stars: ${'★'.repeat(effect.stars)}`);
    }
    
    return details;
  }

  // Load catalog data on mount (no auto pause/resume)
  onMount(async () => {
    try {
      catalogData = await getCatalogData();
    } catch (error) {
      console.warn('Failed to load catalog data:', error);
    }
  });

  function handleClose() {
    dispatch('close');
  }

  function selectCharacter(id) {
    selectedCharacterId = id;
  }
</script>

<MenuPanel>
  <div class="combat-viewer">
    <div class="viewer-header">
      <h2>Combat Viewer</h2>
      <button class="close-btn" on:click={handleClose}>×</button>
    </div>
    
    <div class="viewer-content">
      <PartyView {party} />
      <FoeView {foes} />
      <!-- Left panel: Use PartyRoster styling (read-only) -->
      <div class="character-roster">
        <div class="roster-section">
          <h4 class="roster-title">Party</h4>
          <PartyRoster
            roster={viewerRoster.filter(r => r.is_player)}
            selected={[selectedCharacterId].filter(Boolean)}
            bind:previewId={selectedCharacterId}
            reducedMotion={true}
            on:toggle={() => { /* read-only: suppress */ }}
          />
        </div>
        <div class="roster-section">
          <h4 class="roster-title">Foes</h4>
          <PartyRoster
            roster={viewerRoster.filter(r => !r.is_player)}
            selected={[selectedCharacterId].filter(Boolean)}
            bind:previewId={selectedCharacterId}
            reducedMotion={true}
            on:toggle={() => { /* read-only: suppress */ }}
          />
        </div>
      </div>

      <!-- Center panel: Big portrait (use PlayerPreview from Party menu) -->
      <div class="character-preview">
        <PlayerPreview roster={viewerRoster} previewId={selectedCharacterId} />
      </div>

      <!-- Right panel: Stats + Status effects tabs -->
      <div class="status-effects">
        {#if selectedCharacter}
          <div class="stats-grid">
            <div class="stat-section">
              <h4>Health</h4>
              <HpStatus hp={selectedCharacter.hp} maxHp={selectedCharacter.max_hp || selectedCharacter.hp} />
              {#if selectedCharacter.shields}
                <div class="stat">
                  <label>Shield:</label>
                  <span>{selectedCharacter.shields}</span>
                </div>
              {/if}
            </div>

            <div class="stat-section">
              <h4>Combat Stats</h4>
              <div class="stat">
                <label>Attack:</label>
                <span>{selectedCharacter.attack || selectedCharacter.atk || 0}</span>
              </div>
              <div class="stat">
                <label>Defense:</label>
                <span>{selectedCharacter.defense || selectedCharacter.def || 0}</span>
              </div>
              {#if selectedCharacter.mitigation !== undefined}
                <div class="stat">
                  <label>Mitigation:</label>
                  <span>x{Number(selectedCharacter.mitigation ?? 1).toFixed(2)}</span>
                </div>
              {/if}
              {#if selectedCharacter.vitality !== undefined}
                <div class="stat">
                  <label>Vitality:</label>
                  <span>x{Number(selectedCharacter.vitality ?? 1).toFixed(2)}</span>
                </div>
              {/if}
              {#if selectedCharacter.crit_rate !== undefined}
                <div class="stat">
                  <label>Crit Rate:</label>
                  <span>{(selectedCharacter.crit_rate * 100).toFixed(1)}%</span>
                </div>
              {/if}
              {#if selectedCharacter.crit_damage !== undefined}
                <div class="stat">
                  <label>Crit Damage:</label>
                  <span>{((selectedCharacter.crit_damage - 1) * 100).toFixed(1)}%</span>
                </div>
              {/if}
              {#if selectedCharacter.effect_hit_rate !== undefined}
                <div class="stat">
                  <label>Effect Hit Rate:</label>
                  <span>{(selectedCharacter.effect_hit_rate * 100).toFixed(1)}%</span>
                </div>
              {/if}
              {#if selectedCharacter.effect_resistance !== undefined}
                <div class="stat">
                  <label>Effect Resistance:</label>
                  <span>{(selectedCharacter.effect_resistance * 100).toFixed(1)}%</span>
                </div>
              {/if}
            </div>

            <div class="stat-section">
              <h4>Action Points</h4>
              <div class="stat">
                <label>AP:</label>
                <span>{selectedCharacter.action_points ?? 0}</span>
              </div>
              <div class="stat">
                <label>APT:</label>
                <span>{selectedCharacter.actions_per_turn ?? 1}</span>
              </div>
            </div>

            <div class="stat-section">
              <h4>Battle Performance</h4>
              <div class="stat">
                <label>Damage Dealt:</label>
                <span>{selectedCharacter.damage_dealt ?? 0}</span>
              </div>
              <div class="stat">
                <label>Damage Taken:</label>
                <span>{selectedCharacter.damage_taken ?? 0}</span>
              </div>
              <div class="stat">
                <label>Kills:</label>
                <span>{selectedCharacter.kills ?? 0}</span>
              </div>
              {#if selectedCharacter.healing_done !== undefined}
                <div class="stat">
                  <label>Healing Done:</label>
                  <span>{selectedCharacter.healing_done}</span>
                </div>
              {/if}
            </div>

            <div class="stat-section">
              <h4>Element</h4>
              <div class="stat">
                <label>Type:</label>
                <span class="element-type" style={`color: ${getElementColor(selectedCharacter.element || 'Generic')}`}>
                  {selectedCharacter.element || selectedCharacter.damage_type || 'Generic'}
                </span>
              </div>
            </div>
          </div>
        {/if}
        <div class="tab-header">
          {#each tabs as tab}
            <button 
              class="tab-btn" 
              class:active={activeTab === tab.id}
              on:click={() => activeTab = tab.id}
            >
              {tab.label}
            </button>
          {/each}
        </div>

        <div class="tab-content">
          {#if selectedCharacter}
            {#each getStatusEffects(selectedCharacter, activeTab) as effect}
              <div class="effect-item">
                <div class="effect-header">
                  <div class="effect-name">
                    {formatEffect(effect)}
                    {#if activeTab === 'passives'}
                      {#if effect.display === 'spinner'}
                        <Spinner style="color: var(--el-color)" size="0.75rem" thickness="2px" />
                      {:else if effect.display === 'pips'}
                        {#if effect.stacks <= 5}
                          <span class="pips">
                            {#each Array(effect.stacks) as _, i (i)}
                              <Circle
                                class="pip-icon filled"
                                stroke="none"
                                fill="currentColor"
                                aria-hidden="true"
                              />
                            {/each}
                          </span>
                        {:else}
                          <span class="pip-count">{effect.stacks}</span>
                        {/if}
                      {:else if effect.display === 'number'}
                        <span class="pip-count">{effect.max_stacks ? `${effect.stacks}/${effect.max_stacks}` : effect.stacks}</span>
                      {/if}
                    {/if}
                  </div>
                  <div class="effect-duration">{formatDuration(effect)}</div>
                </div>
                <div class="effect-details">
                  {#each getEffectDetails(effect) as detail}
                    <div class="effect-detail">{detail}</div>
                  {/each}
                </div>
              </div>
            {:else}
              <div class="no-effects">
                <p>No {tabs.find(t => t.id === activeTab)?.label.toLowerCase()} effects</p>
              </div>
            {/each}
          {:else}
            <div class="no-effects">
              <p>Select a character to view effects</p>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
</MenuPanel>

<style>
  .combat-viewer {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden; /* prevent whole viewer from scrolling */
  }

  .viewer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }

  .close-btn {
    background: none;
    border: none;
    color: #fff;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0.5rem;
  }

  .viewer-content {
    display: grid;
    grid-template-columns: minmax(8rem, 22%) 1fr minmax(12rem, 26%);
    height: 100%;
    min-height: 0; /* allow inner columns to control scrolling */
    flex: 1;
    width: 100%;
    max-height: 98%;
    position: relative;
    z-index: 0;
  }

  /* Left panel: Character roster (like PartyRoster) */
  .character-roster {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.4rem;
    height: 100%;
    overflow-y: auto;
    min-width: 0;
  }

  .roster-section { margin-bottom: 0.5rem; }
  .roster-title {
    margin: 0.25rem 0 0.35rem 0.1rem;
    color: #fff;
    font-size: 0.9rem;
    opacity: 0.85;
  }

  .character-section {
    margin-bottom: 1rem;
  }

  .character-section h4 {
    margin: 0 0 0.5rem 0;
    color: #fff;
    font-size: 0.9rem;
    opacity: 0.8;
  }

  .char-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
    padding: 0.25rem 0.4rem;
    background: rgba(0,0,0,0.6);
    border: 2px solid transparent;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
    z-index: 0;
    width: 100%;
    margin-bottom: 0.25rem;
    --el-dark: color-mix(in srgb, var(--el-color) 20%, black 80%);
    --el-5darker: color-mix(in srgb, var(--el-color) 95%, black 5%);
    --el-5lighter: color-mix(in srgb, var(--el-color) 95%, white 5%);
  }

  .char-row:hover {
    background: rgba(20,20,20,0.8);
  }

  .char-row.selected {
    border-color: #ffd700;
    box-shadow: 0 0 8px rgba(255,215,0,0.5);
  }

  .char-row::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
      90deg,
      var(--el-dark) 0%,
      var(--el-5darker) 25%,
      var(--el-color) 50%,
      var(--el-5lighter) 75%,
      var(--el-dark) 100%
    );
    background-size: 200% 100%;
    background-position: -100% 0;
    opacity: 0;
    filter: brightness(1.0);
    mix-blend-mode: soft-light;
    animation: af-elm-sweep 12s linear infinite;
    animation-play-state: paused;
    pointer-events: none;
    z-index: 0;
    transition: opacity 280ms ease;
  }

  .char-row.selected::before {
    opacity: 0.82;
    animation-play-state: running;
  }

  @keyframes af-elm-sweep {
    0% { background-position: -100% 0; }
    100% { background-position: 100% 0; }
  }

  .row-name, .row-stats {
    position: relative;
    z-index: 1;
  }

  .row-name {
    color: #fff;
    font-size: 0.9rem;
    font-weight: bold;
    text-align: left;
  }

  .row-stats {
    color: #fff;
    font-size: 0.8rem;
    opacity: 0.8;
  }

  /* Center panel: Character preview (like PlayerPreview) */
  .character-preview {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    min-width: 0;
    min-height: 0;
    overflow: hidden; /* center column stays fixed; no scroll here */
  }

  .preview-container {
    width: 100%;
    max-width: 100%;
  }

  .character-portrait {
    background: rgba(0, 0, 0, 0.3);
    border: 3px solid var(--outline, #555);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow:
      0 8px 24px rgba(0,0,0,0.5),
      0 0 18px color-mix(in srgb, var(--outline, #888) 65%, transparent),
      0 0 36px color-mix(in srgb, var(--outline, #888) 35%, transparent);
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .portrait-image {
    width: 120px;
    height: 120px;
    object-fit: contain;
    border: 3px solid var(--outline, #555);
    border-radius: 8px;
    margin-bottom: 0.5rem;
    background: #222;
    display: block;
  }

  .character-name {
    font-size: 1.2rem;
    font-weight: bold;
    color: #fff;
    margin-bottom: 0.5rem;
  }

  .character-type {
    font-size: 0.8rem;
    opacity: 0.7;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #fff;
  }

  .stats-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .stat-section {
    background: rgba(255, 255, 255, 0.05);
    padding: 0.75rem;
    border-radius: 3px;
  }

  .stat-section h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.9rem;
    color: #fff;
    opacity: 0.8;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    padding-bottom: 0.25rem;
  }

  .stat {
    display: flex;
    justify-content: space-between;
    padding: 0.25rem 0;
    font-size: 0.9rem;
  }

  .stat label {
    font-weight: bold;
    opacity: 0.9;
    color: #fff;
  }

  .stat span {
    opacity: 0.8;
    color: #fff;
  }

  .element-type {
    text-transform: capitalize;
    font-weight: bold;
  }

  .placeholder {
    color: #888;
    font-style: italic;
    text-align: center;
  }

  /* Right panel: Status effects */
  .status-effects {
    display: flex;
    flex-direction: column;
    min-height: 0;
    padding: 0.4rem;
    gap: 0.6rem;
    height: 100%;
    overflow-y: auto; /* scroll independently from center portrait */
  }

  .tab-header {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    margin-bottom: 1rem;
  }

  .tab-btn {
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #fff;
    cursor: pointer;
    font-size: 0.8rem;
    border-radius: 3px;
  }

  .tab-btn:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  .tab-btn.active {
    background: rgba(120, 180, 255, 0.3);
    border-color: rgba(120, 180, 255, 0.5);
  }

  .tab-content {
    flex: 1;
    max-height: 400px;
    overflow-y: auto;
  }

  .effect-item {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 3px;
  }

  .effect-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .effect-name {
    font-weight: bold;
    flex: 1;
    margin-right: 0.5rem;
    color: #fff;
  }

  .pips {
    display: inline-flex;
    gap: 2px;
    margin-left: 0.25rem;
    line-height: 0;
  }

  :global(.pip-icon) {
    width: 0.7em;
    height: 0.7em;
    stroke-width: 2;
  }

  :global(.pip-icon.filled) {
    fill: currentColor;
  }

  .pip-count {
    margin-left: 0.25rem;
    font-size: 0.8rem;
  }

  .effect-duration {
    font-size: 0.8rem;
    opacity: 0.8;
    white-space: nowrap;
    color: #fff;
  }

  .effect-details {
    margin-top: 0.5rem;
  }

  .effect-detail {
    font-size: 0.8rem;
    line-height: 1.3;
    margin-bottom: 0.25rem;
    opacity: 0.9;
    color: #fff;
  }

  .no-effects {
    text-align: center;
    margin: 2rem 0;
    opacity: 0.8;
  }

  h2 {
    color: #fff;
    margin: 0 0 1rem 0;
  }

  p {
    color: #fff;
    opacity: 0.8;
    text-align: center;
    margin: 2rem 0;
  }
</style>
