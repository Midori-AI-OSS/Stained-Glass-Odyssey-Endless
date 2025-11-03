# Standardize Card and Relic Description Format

## Objective

Update all existing card and relic documentation task files to follow a new standardized format for `full_about` and `summarized_about` fields.

## Background

The game currently has 62 card documentation tasks and 43 relic documentation tasks that need to migrate from the old `about` field to the new `full_about` and `summarized_about` fields. These task files need to be updated with new guidelines on how to format these descriptions.

## New Description Standards

### `summarized_about` Field
- Should provide a **qualitative** description without specific numbers
- Use phrases like "adds some atk", "lowers def", "boosts hp", "reduces damage"
- Keep it brief and suitable for quick scanning in the UI
- Focus on the general effect type, not the exact values

**Examples:**
- "Boosts atk and effect hit rate; allies surge with speed at battle start"
- "Grants some max hp; reduces lethal damage"
- "After an Ultimate, grants a shield based on max hp"

### `full_about` Field  
- Should provide a **detailed** description with all specific numbers and percentages
- Explain all mechanics, triggers, stacking behavior (for relics), and interactions
- Include exact values like "+500% ATK", "20% Max HP", "2 turns", etc.
- Provide comprehensive information for players who want to understand exact mechanics

**Examples:**
- "+500% ATK & +500% Effect Hit Rate; at the start of each battle, all allies gain +200% SPD for 2 turns."
- "+4% HP; If lethal damage would reduce you below 1 HP, reduce that damage by 10%"
- "After an Ultimate, grant a shield equal to 20% Max HP per stack."

## Task Details

**Files to update:** All task files in the following directories:
- `.codex/tasks/cards/` (62 files)
- `.codex/tasks/relics/` (43 files)

**Changes required for each task file:**

1. Update the "Guidelines" section to include the new standards for `full_about` and `summarized_about`
2. Add clear examples showing the difference between qualitative (summarized) and quantitative (full) descriptions
3. Ensure the guidelines emphasize:
   - `summarized_about`: NO specific numbers, use qualitative descriptions
   - `full_about`: Include ALL specific numbers and percentages

## Updated Guidelines Template

Add this section to each task file under "Guidelines":

```markdown
**Description Format Standards:**

- `summarized_about`: Use qualitative descriptions without numbers
  - Example: "Boosts atk" instead of "Boosts atk by 500%"
  - Example: "Lowers def" instead of "Reduces def by 20%"
  - Example: "Grants some shield" instead of "Grants shield equal to 20% max HP"
  
- `full_about`: Include all specific numbers and percentages
  - Example: "+500% ATK & +500% Effect Hit Rate"
  - Example: "Reduce damage by 10%"
  - Example: "Grant a shield equal to 20% Max HP per stack"
```

## Implementation Steps

1. Create a batch update plan for all 105 task files (62 cards + 43 relics)
2. For each task file:
   - Locate the "Guidelines" section
   - Insert the new description format standards
   - Update any existing examples to follow the new format
3. Ensure consistency across all task files
4. Verify that the changes don't break the existing structure or acceptance criteria

## Priority

This is a foundational change that affects how all future card and relic documentation will be written. It should be completed before coders begin implementing the individual card/relic documentation tasks.

## Acceptance Criteria

- [ ] All 62 card task files updated with new guidelines
- [ ] All 43 relic task files updated with new guidelines  
- [ ] Guidelines clearly distinguish between qualitative (summarized) and quantitative (full) descriptions
- [ ] Examples are provided for both description types
- [ ] All task files maintain their existing structure and acceptance criteria
- [ ] Changes are consistent across all task files

## Notes

- This task updates the **task files themselves**, not the actual card/relic plugin code
- Coders will use these updated task files as guidance when implementing the actual changes to card and relic plugins
- After this task is complete, coders can begin working on individual card/relic documentation tasks with the correct guidelines
