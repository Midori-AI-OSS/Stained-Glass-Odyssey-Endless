# Add "Concise Description" Setting to WebUI

## Objective

Add a new UI setting called "Concise Description" (or "Concise Descriptions") to the WebUI that allows users to toggle between using full descriptions (`full_about`) and concise descriptions (`summarized_about`) for cards, relics, and other game elements throughout the UI.

## Background

The game is transitioning from a single `about` field to dual fields (`full_about` and `summarized_about`) for all cards, relics, and game elements. This new setting will give players control over which description format they prefer to see in tooltips, information panels, and other UI elements.

## Task Details

### Backend Changes

**File to modify:** `backend/options.py`

1. Add a new option key to the `OptionKey` enum:
   ```python
   CONCISE_DESCRIPTIONS = "concise_descriptions"
   ```

2. Ensure the option defaults to `false` (showing full descriptions by default) when not set.

### Backend API Changes

**File to check/modify:** `backend/routes/config.py` (or relevant API routes)

1. Verify that the options API endpoints properly expose this new setting to the frontend
2. Ensure the setting can be read and written via the existing config/options API

### Frontend Changes

**File to modify:** `frontend/src/lib/components/UISettings.svelte`

1. Add a new checkbox control for "Concise Descriptions":
   ```svelte
   <div class="control" title="Show concise descriptions instead of full detailed descriptions for cards, relics, and effects.">
     <div class="control-left">
       <span class="label"><FileText /> Concise Descriptions</span>
     </div>
     <div class="control-right">
       <input
         type="checkbox"
         bind:checked={uiSettings.conciseDescriptions}
         on:change={(e) => updateUI({ conciseDescriptions: e.target.checked })}
       />
     </div>
   </div>
   ```

2. Import the appropriate icon (e.g., `FileText` from lucide-svelte)

**Files to check/modify:** Settings storage system

1. Update the settings storage system (`frontend/src/lib/systems/settingsStorage.js` or similar) to:
   - Include the `conciseDescriptions` setting in the appropriate settings object
   - Persist this setting to localStorage/backend
   - Provide getter/setter functions if needed

**Files to modify:** UI components that display descriptions

1. Update all components that display card, relic, or effect descriptions to:
   - Read the `conciseDescriptions` setting
   - Display `summarized_about` when the setting is enabled
   - Display `full_about` when the setting is disabled (default)

Example components to update:
- Card tooltips and info panels
- Relic tooltips and info panels
- Effect/buff/debuff tooltips
- Guidebook entries
- Any other location where `about` descriptions are shown

## Implementation Guidelines

- Follow the existing pattern used by other UI settings in `UISettings.svelte`
- Maintain consistency with the existing settings UI styling
- Ensure the setting persists across sessions
- Test that toggling the setting immediately updates all relevant UI elements
- Consider adding a comment explaining that this setting switches between `full_about` and `summarized_about` fields

## Acceptance Criteria

- [ ] New `CONCISE_DESCRIPTIONS` option key added to backend `OptionKey` enum
- [ ] Backend properly stores and retrieves the setting value
- [ ] New checkbox control added to UISettings.svelte with appropriate label and tooltip
- [ ] Setting value persists across browser sessions
- [ ] All UI components that display descriptions respect the new setting
- [ ] Toggling the setting updates the UI immediately without requiring a refresh
- [ ] Code follows existing style and conventions
- [ ] Setting defaults to showing full descriptions (concise = false)

## Related Work

This task is related to the ongoing documentation improvement work tracked in `.codex/tasks/cards/` and `.codex/tasks/relics/` where individual plugins are being updated to include both `full_about` and `summarized_about` fields.

## Notes

- The exact wording for the setting can be adjusted during implementation (e.g., "Concise Descriptions" vs "Use Brief Descriptions" vs "Simplified Text")
- Consider whether this setting should apply only to cards/relics or also to other game elements
- The implementation may require coordination with the ongoing `about` field migration work
