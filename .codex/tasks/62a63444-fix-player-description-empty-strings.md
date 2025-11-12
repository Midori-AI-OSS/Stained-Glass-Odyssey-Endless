# Fix Player Description Empty Strings in Roster Endpoint

## Problem

The roster endpoint (`/players`) now returns empty strings for both `full_about` and `summarized_about` description fields for all characters, breaking the frontend's ability to display character descriptions.

### Root Cause

In `backend/routes/players.py` (lines 190-192), the code attempts to retrieve `full_about` and `summarized_about` attributes from character instances:

```python
full_about_text = getattr(inst, "full_about", "")
summarized_about_text = getattr(inst, "summarized_about", "")
```

However:
- `PlayerBase` and all concrete character classes only define an `about` attribute
- No character has `full_about` or `summarized_about` attributes
- The `getattr` calls return empty strings (the default value)
- The frontend receives empty strings for all character descriptions

### Impact

- **All 20+ playable characters** lose their descriptions in the Party Picker UI
- The concise-description toggle becomes non-functional (both modes show empty strings)
- Players cannot read character lore or abilities when selecting their party

## Solution Options

### Option A: Fallback in Roster Endpoint (Recommended)

Modify `backend/routes/players.py` to provide fallback from `about` when new fields are missing:

```python
# Send both description fields to frontend for client-side switching
full_about_text = getattr(inst, "full_about", None) or getattr(inst, "about", "")
summarized_about_text = getattr(inst, "summarized_about", None) or getattr(inst, "about", "")
```

**Pros:**
- Single file change fixes all characters
- Maintains backward compatibility
- Quick fix with minimal testing burden
- Characters can still be individually migrated later

**Cons:**
- Doesn't provide true concise/verbose distinction
- Both description modes will show identical text until characters are migrated

### Option B: Migrate All Characters to New Fields

Add `full_about` and `summarized_about` attributes to each character class, following the pattern used for cards and relics.

**Pros:**
- Aligns with the established pattern (cards/relics already use these fields)
- Enables true concise/verbose description modes
- More maintainable long-term

**Cons:**
- Requires editing 20+ character files
- Requires writing condensed summaries for all characters
- Higher testing burden
- More chance for errors

## Recommendation

Start with **Option A** as an immediate fix to restore functionality, then create follow-up tasks for individual character migrations if concise descriptions are desired.

## Acceptance Criteria

- [ ] Roster endpoint returns non-empty descriptions for all characters
- [ ] Frontend displays character descriptions in Party Picker
- [ ] Existing `about` text is preserved and displayed
- [ ] No regressions in character loading or display
- [ ] Manual verification: Open Party Picker and verify descriptions appear

## Files to Modify

- `backend/routes/players.py` (lines 190-192)

## Testing

- Run existing player endpoint tests
- Manual verification in Party Picker UI
- Verify descriptions appear for Player, Luna, LadyEcho, Mezzy, and other characters

## Related

This issue mirrors the completed card/relic documentation migration project where items were updated to use `full_about` and `summarized_about` fields. If we want character descriptions to support concise/verbose modes, follow-up tasks should be created for individual character migrations.
