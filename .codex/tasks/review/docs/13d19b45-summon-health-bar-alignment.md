# Fix Summon Health Bar Alignment with Buffs/Debuffs

## Task ID
`13d19b45-summon-health-bar-alignment`

## Priority
Medium

## Status
WIP

## Description
There is a bug with summons: if they have lots of buffs/debuffs, the health bar moves or becomes unaligned. When summons accumulate multiple status effects, the visual indicators for buffs/debuffs push the health bar out of its expected position, causing visual misalignment in the battle UI.

## Context
Summons (like Luna's swords, Becca's menagerie, etc.) are displayed using the same `BattleFighterCard.svelte` component as regular fighters. When buffs/debuffs are applied to summons:
1. Passive indicators may stack up in the overlay
2. The layout calculation doesn't account for many indicators
3. The health bar or other UI elements get pushed out of alignment

This is a frontend layout issue in `frontend/src/lib/battle/BattleFighterCard.svelte`.

## Current Implementation

### BattleFighterCard.svelte Layout
The current overlay structure (around lines 445-505):
```svelte
<div class="overlay-ui">
  {#if (fighter.passives || []).length}
    <div class="passive-indicators">
      {#each fighter.passives as p (p.id)}
        <div class="passive">
          <!-- Passive indicator content -->
        </div>
      {/each}
    </div>
  {/if}
  
  <div class="ult-gauge">
    <!-- Ultimate gauge -->
  </div>
</div>
```

### CSS for Overlay (lines 1174-1183)
```css
.overlay-ui {
  position: absolute;
  bottom: 4px;
  right: 4px;
  display: flex;
  align-items: flex-end;
  gap: 6px;
  pointer-events: none;
  z-index: 3;
}
```

## Problem Analysis
1. **Fixed positioning**: The overlay is absolutely positioned at `bottom: 4px; right: 4px`
2. **Unbounded width**: Passive indicators can grow without limit
3. **No overflow handling**: When passives accumulate, they push other elements
4. **Summon size**: Summons may use "medium" size which has less space
5. **Missing max constraints**: No `max-width` or `overflow` rules for indicator container

## Objectives
1. Constrain passive indicator container to prevent overflow
2. Handle many buffs/debuffs gracefully (scrolling, grouping, or collapse)
3. Ensure health bar and other UI elements maintain position
4. Test specifically with summons that accumulate effects
5. Consider summon-specific sizing adjustments

## Implementation Options

### Option A: Constrain and Scroll (Simple)
Add max-width and overflow scrolling to passive indicators:
```css
.passive-indicators {
  max-width: 50%; /* Or calc(var(--portrait-size) * 0.4) */
  overflow-x: auto;
  overflow-y: hidden;
}
```

### Option B: Collapse to Number (Recommended)
When there are too many passives, show a count instead:
```svelte
{#if fighter.passives.length > 3}
  <div class="passive-count">{fighter.passives.length} effects</div>
{:else}
  {#each fighter.passives as p}
    <!-- Individual indicators -->
  {/each}
{/if}
```

### Option C: Wrap to Multiple Rows
Allow passive indicators to wrap:
```css
.passive-indicators {
  flex-wrap: wrap;
  max-height: calc(var(--portrait-size) * 0.3);
  overflow-y: auto;
}
```

### Option D: Summon-Specific Layout
Add summon-specific adjustments:
```css
.modern-fighter-card.medium .passive-indicators {
  /* Smaller indicators for summons */
  --pip-size: clamp(3px, calc(var(--portrait-size) * 0.06), 8px);
  max-width: 40%;
}
```

## Implementation Steps

### Step 1: Identify the Issue
Add debugging to understand current behavior:
```svelte
{#if fighter.passives?.length > 3}
  <!-- Debug: {fighter.passives.length} passives -->
{/if}
```

### Step 2: Add Container Constraints
Update `.passive-indicators` CSS:
```css
.passive-indicators {
  --pip-size: clamp(4px, calc(var(--portrait-size) * 0.09), 12px);
  --pip-gap: clamp(2px, calc(var(--portrait-size) * 0.03), 4px);
  display: flex;
  gap: 2px;
  pointer-events: none;
  
  /* New constraints */
  max-width: calc(var(--portrait-size) * 0.45);
  flex-wrap: wrap;
  justify-content: flex-end;
}
```

### Step 3: Add Collapse Behavior
Update the Svelte template:
```svelte
{#if (fighter.passives || []).length}
  <div class="passive-indicators" class:reduced={reducedMotion}>
    {#if fighter.passives.length > 5}
      <!-- Collapsed view for many passives -->
      <div class="passive number-mode effects-collapsed">
        <span class="count">{fighter.passives.length}</span>
      </div>
    {:else}
      {#each fighter.passives as p (p.id)}
        <!-- Individual passive rendering -->
      {/each}
    {/if}
  </div>
{/if}
```

### Step 4: Add Summon-Specific Adjustments
Add CSS for summon sizing:
```css
/* Summons (medium size) get tighter layout */
.modern-fighter-card.medium .passive-indicators {
  max-width: calc(var(--portrait-size) * 0.5);
}

.modern-fighter-card.medium .passive {
  padding: 0 3px;
  min-width: 12px;
  height: 12px;
  font-size: 0.75rem;
}
```

### Step 5: Ensure Overlay Stability
Update overlay positioning:
```css
.overlay-ui {
  position: absolute;
  bottom: 4px;
  right: 4px;
  left: 4px; /* New: constrain left side too */
  display: flex;
  align-items: flex-end;
  justify-content: flex-end; /* Keep right alignment */
  gap: 6px;
  pointer-events: none;
  z-index: 3;
}
```

### Step 6: Test with Summons
Create test scenario:
1. Spawn Luna with multiple swords
2. Apply 5+ buffs/debuffs to swords
3. Verify layout remains stable
4. Check different viewport sizes

## Files to Modify
- `frontend/src/lib/battle/BattleFighterCard.svelte` - Layout and CSS fixes
- Potentially `frontend/src/lib/components/BattleView.svelte` - If parent affects layout

## Acceptance Criteria
- [x] Health bar remains in correct position with 5+ passives
- [x] Passive indicators don't overflow the portrait boundary
- [x] Summons (medium size) display correctly with many effects
- [x] Layout works at different viewport sizes
- [x] Collapse or scrolling behavior works for many passives (wrapping implemented)
- [x] Visual appearance is consistent with regular fighter cards
- [x] No layout shift when passives are added/removed
- [x] Linting passes (BattleFighterCard.svelte has no linting errors)

## Implementation Notes (Completed 2025-12-03)

### Changes Made
1. **Added constraints to `.passive-indicators`** (line 1185-1194):
   - `max-width: calc(var(--portrait-size) * 0.45)` - Prevents overflow beyond portrait boundary
   - `flex-wrap: wrap` - Allows indicators to wrap to multiple rows
   - `justify-content: flex-end` - Maintains right alignment

2. **Updated `.overlay-ui`** (line 1174-1185):
   - Added `left: 4px` - Constrains left side to prevent overflow
   - Added `justify-content: flex-end` - Keeps right alignment while respecting left constraint

3. **Added summon-specific adjustments** (line 1373-1387):
   - `.modern-fighter-card.medium .passive-indicators` - Slightly larger max-width (50%) for medium cards
   - `.modern-fighter-card.medium .passive` - Smaller padding and font size for tighter layout
   - `.modern-fighter-card.medium .passive.number-mode` - Adjusted padding for number display

### Implementation Strategy
- Used Option A (Constrain and Wrap) from the task description
- Passive indicators now wrap when they exceed available space
- No changes needed to BattleView.svelte as the HP bar is already properly positioned
- Maintained backwards compatibility with all existing card sizes

### Technical Details
- CSS-only solution, no JavaScript changes required
- Leverages CSS flexbox wrapping for graceful degradation
- Uses CSS custom properties for responsive sizing
- Medium size cards (96px) used by summons get specialized treatment

## Testing Requirements

### Manual Verification
1. Create battle with Luna (spawns swords)
2. Apply buffs to swords via cards/relics
3. Observe health bar position with 0, 3, 5, 10 passives
4. Check on different screen sizes
5. Verify animations don't cause layout shift

### Visual Regression
Take screenshots of:
- Summon with 0 passives
- Summon with 3 passives
- Summon with 5+ passives
- Summon with 10+ passives

## Notes for Coder
- This is a CSS/layout issue, not a logic issue
- Test with actual summons in battle, not just mockups
- Consider mobile viewport behavior
- The `medium` size class is key for summons
- Preserve existing visual style while fixing layout
- Consider accessibility - don't hide important effect information
- May need coordination with health bar component if that's separate
