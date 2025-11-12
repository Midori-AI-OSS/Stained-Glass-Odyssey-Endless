# Character Looks String Task Summary

**Created:** 2025-11-12  
**Task Master:** GitHub Copilot Agent  
**Requested By:** User (lunamidori5)

## Overview

This document tracks the batch creation of 18 task files for adding `looks` strings to characters that are currently missing them. The `looks` string provides detailed visual descriptions for each character, supporting future AI-powered features and providing rich context for character appearance.

## Purpose

The repository is standardizing character descriptions by adding a `looks` field to all character classes. This field contains multi-paragraph, detailed visual descriptions following the format established in:
- Luna (`backend/plugins/characters/luna.py`)
- Ryne (`backend/plugins/characters/ryne.py`)
- Lady Light (`backend/plugins/characters/lady_light.py`)
- Lady Darkness (`backend/plugins/characters/lady_darkness.py`)
- Lady Storm (`backend/plugins/characters/lady_storm.py`)
- Lady Wind (`backend/plugins/characters/lady_wind.py`)

## Characters Already Complete (6)

These characters already have `looks` strings and require no action:
1. ✅ Luna
2. ✅ Ryne
3. ✅ Lady Light
4. ✅ Lady Darkness
5. ✅ Lady Storm
6. ✅ Lady Wind

## Task Files Created (18)

| # | Character | File Path | Hash Prefix |
|---|-----------|-----------|-------------|
| 1 | Ally | `.codex/tasks/chars/1436e59d-ally-looks-string.md` | 1436e59d |
| 2 | Becca | `.codex/tasks/chars/7964d0fa-becca-looks-string.md` | 7964d0fa |
| 3 | Bubbles | `.codex/tasks/chars/6ef351bd-bubbles-looks-string.md` | 6ef351bd |
| 4 | Carly | `.codex/tasks/chars/5fea3fa1-carly-looks-string.md` | 5fea3fa1 |
| 5 | Casno | `.codex/tasks/chars/09532005-casno-looks-string.md` | 09532005 |
| 6 | GrayGray | `.codex/tasks/chars/e49e0043-graygray-looks-string.md` | e49e0043 |
| 7 | Hilander | `.codex/tasks/chars/af8ab3a9-hilander-looks-string.md` | af8ab3a9 |
| 8 | Ixia | `.codex/tasks/chars/e9e535da-ixia-looks-string.md` | e9e535da |
| 9 | Kboshi | `.codex/tasks/chars/a1566ae2-kboshi-looks-string.md` | a1566ae2 |
| 10 | Lady Echo | `.codex/tasks/chars/66f5f544-lady-echo-looks-string.md` | 66f5f544 |
| 11 | Lady Fire and Ice | `.codex/tasks/chars/79c9b46a-lady-fire-and-ice-looks-string.md` | 79c9b46a |
| 12 | Lady Lightning | `.codex/tasks/chars/6e92d712-lady-lightning-looks-string.md` | 6e92d712 |
| 13 | Lady of Fire | `.codex/tasks/chars/f82421d0-lady-of-fire-looks-string.md` | f82421d0 |
| 14 | Mezzy | `.codex/tasks/chars/295660bd-mezzy-looks-string.md` | 295660bd |
| 15 | Mimic | `.codex/tasks/chars/e882b62f-mimic-looks-string.md` | e882b62f |
| 16 | Persona Ice | `.codex/tasks/chars/575bd801-persona-ice-looks-string.md` | 575bd801 |
| 17 | Persona Light and Dark | `.codex/tasks/chars/19301a97-persona-light-and-dark-looks-string.md` | 19301a97 |
| 18 | Slime | `.codex/tasks/chars/4ff13c74-slime-looks-string.md` | 4ff13c74 |

## Task File Structure

Each task file includes:

### Description
- Clear title indicating which character needs a looks string
- Target file path for implementation

### Background
- Context about the standardization effort
- Purpose of the looks string feature

### Reference Examples
- Links to Luna, Ryne, Lady Light, and Lady Darkness files
- Line number references for exact format

### Placeholder Section
- Clearly marked section for user to provide appearance description
- Checklist of elements to include:
  - Physical build and proportions
  - Facial features and coloring
  - Hair style, color, and length
  - Clothing and outfit details
  - Signature gear or accessories
  - Posture and mannerisms
  - Visual effects or magical elements

### Acceptance Criteria
- [ ] `looks` field added to the character dataclass
- [ ] Content follows multi-paragraph format used in reference examples
- [ ] Triple-quoted string format used for multiline text
- [ ] Positioned after `summarized_about` and before `char_type`
- [ ] No changes to existing functionality

### Metadata
- Task type: Documentation / Character Enhancement
- Priority: Low - Quality of life improvement
- Notes about batch update and implementation scope

## Next Steps

### For the User
1. Review each task file in `.codex/tasks/chars/`
2. Provide detailed appearance descriptions for each character
3. Assign tasks to Coder mode contributors for implementation

### For Coder Mode Contributors
1. Pick a task from `.codex/tasks/chars/`
2. Read the referenced example files to understand the format
3. Add the `looks` field to the appropriate character class
4. Follow the acceptance criteria checklist
5. Mark task as "ready for review" when complete

### For Auditor/Reviewer
1. Verify `looks` field is present in the character class
2. Check formatting matches reference examples
3. Confirm field is positioned correctly (after `summarized_about`, before `char_type`)
4. Ensure no game mechanics were modified
5. Request Task Master review when audit is complete

## Implementation Guidelines

### Format Requirements
```python
@dataclass
class CharacterName(PlayerBase):
    id = "character_id"
    name = "Character Name"
    full_about = "..."
    summarized_about = "..."
    looks = """
    [Multi-paragraph visual description here]
    """
    char_type: CharacterType = CharacterType.X
    # ... rest of class definition
```

### Content Guidelines
- Use multi-paragraph format (2-4 paragraphs typical)
- Include rich sensory details
- Cover all visual aspects listed in placeholder
- Match the tone and depth of existing examples
- Use triple-quoted strings for multiline text
- Maintain consistent indentation

### Things to Avoid
- Do not modify any game mechanics
- Do not change any existing fields
- Do not add any other documentation
- Do not run tests (documentation-only change)
- Do not modify character stats or abilities

## Metrics

- **Total Characters Reviewed:** 24
- **Characters with Looks String:** 6 (25%)
- **Characters Needing Looks String:** 18 (75%)
- **Task Files Created:** 18
- **Estimated Implementation Time:** ~15 minutes per character
- **Total Estimated Effort:** ~4.5 hours for all 18 characters

## Status

- **Task Creation:** ✅ Complete (2025-11-12)
- **User Review:** ⏳ Pending
- **Implementation:** ⏳ Pending
- **Review/Audit:** ⏳ Pending
- **Task Master Review:** ⏳ Pending

## References

- **Task Master Guidelines:** `.codex/modes/TASKMASTER.md`
- **Character Directory:** `backend/plugins/characters/`
- **Task Directory:** `.codex/tasks/chars/`
- **Example Characters:** luna.py, ryne.py, lady_light.py, lady_darkness.py

---

**Document ID:** 02aa64b5-character-looks-string-summary  
**Last Updated:** 2025-11-12  
**Status:** Active - Awaiting user input on character descriptions
