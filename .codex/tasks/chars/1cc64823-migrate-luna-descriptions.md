# Migrate Luna Character Descriptions

## Objective

Add `full_about` and `summarized_about` fields to the Luna character class to support concise/verbose description modes in the frontend.

## Background

The roster endpoint now expects `full_about` and `summarized_about` attributes on all character classes, but currently only the `about` field exists. This causes empty strings to be sent to the frontend, breaking character descriptions in the Party Picker UI.

## File to Modify

`backend/plugins/characters/luna.py`

## Required Changes

1. **Rename existing `about` field to `full_about`**
   - Preserve the complete existing description text
   - This becomes the detailed version shown in verbose mode

2. **Add new `summarized_about` field**
   - Write a concise 1-2 sentence summary
   - Focus on character identity/hook
   - No numbers, mechanics, or stat details
   - Suitable for quick scanning in Party Picker

**Note:** Luna has exceptionally long description text including a separate `looks` field. The `looks` field should remain unchanged. Only migrate the `about` field.

## Pattern to Follow

**Before:**
```python
about: str = "Long detailed description..."
looks: str = "..." # Leave unchanged
```

**After:**
```python
full_about: str = "Long detailed description..."
summarized_about: str = "Short 1-2 sentence hook."
looks: str = "..." # Leave unchanged
```

## Acceptance Criteria

- [ ] `about` field renamed to `full_about`
- [ ] New `summarized_about` field added with concise summary
- [ ] `looks` field remains unchanged
- [ ] No lore or characterization lost from original description
- [ ] Character file still imports and instantiates correctly
- [ ] Roster endpoint returns non-empty strings for both fields
- [ ] Manual verification: Character description appears in Party Picker

## Testing

- Run relevant character plugin tests
- Verify character loads in roster endpoint
- Check Party Picker UI displays description

## Related

Part of the character description migration following the pattern established for cards and relics (see task 37c0d861-task-master-review-summary.md).
