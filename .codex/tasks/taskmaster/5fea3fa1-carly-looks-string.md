# Add Looks String to Carly Character

## Description
Add a `looks` field to the Carly character class (`backend/plugins/characters/carly.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

## Background
The repository is standardizing character descriptions by adding a `looks` string that provides detailed visual descriptions for each character. This supports future AI-powered features and provides rich context for character appearance.

## Reference Examples
See these files for the expected format:
- `backend/plugins/characters/luna.py` (lines 193-201)
- `backend/plugins/characters/ryne.py` (lines 24-54)
- `backend/plugins/characters/lady_light.py` (lines 16-24)
- `backend/plugins/characters/lady_darkness.py` (lines 16-25)

## Appearance Description
**Character Details:**
- **Gender:** Female
- **Apparent Age:** Mid-20s
- **Hair:** Blonde, long and wavy, shoulder length
- **Eyes:** Green
- **Build:** Slender
- **Skin:** Fair and smooth with freckles on nose and cheeks
- **Makeup:** Minimal
- **Outfit:** White strapless sundress

**Reference Image:**
https://tea-cup.midori-ai.xyz/download/img_24e509b1-14c9-4512-8f47-f5cc0e00c2cc.png

**SDXL Prompt Reference:**
`(blonde haired), (green eyes), (female), (mid 20s), (long and wavy hair)++, (shoulder length), (slender build), (fair and smooth skin), (freckles on nose and cheeks), (minimal makeup), (white strapless sundress)`

## Acceptance Criteria
- [x] `looks` field added to the Carly dataclass
- [x] Content follows multi-paragraph format used in reference examples
- [x] Triple-quoted string format used for multiline text
- [x] Positioned after `summarized_about` and before `char_type`
- [x] No changes to existing functionality

## Task Type
Documentation / Character Enhancement

## Priority
Low - Quality of life improvement

## Notes
- This is part of a batch update to add looks strings to all characters
- User will provide the actual appearance description
- Task should only add the field, not modify any game mechanics

---

## Implementation Notes
**Completed:** 2025-11-13 (estimated based on code presence)
**Implemented by:** Coder Mode Agent (unmarked in task)

Added 5-paragraph visual description covering:
- Slender young woman (mid-20s) with fair skin and charming freckles
- Long, wavy shoulder-length blonde hair (sun-kissed, effortlessly kept)
- Bright green eyes radiating calm attentiveness and steady kindness
- White strapless sundress (simple, elegant, flowing, peaceful)
- Open, welcoming posture emphasizing protective guardian nature

Description accurately reflects SDXL reference image details and character's sim human guardian identity.

File location: `backend/plugins/characters/carly.py` (lines 16-26)

---

## Audit Report
**Audited:** 2025-11-13  
**Auditor:** Auditor Mode Agent  
**Status:** ✅ **APPROVED** - Ready for taskmaster

### Verification Checklist
- ✅ `looks` field added to Carly dataclass (line 16)
- ✅ Content follows multi-paragraph narrative prose format (5 paragraphs, 3,067 characters)
- ✅ Triple-quoted string format used correctly
- ✅ Positioned after `summarized_about` (line 15) and before `char_type` (line 27)
- ✅ No changes to existing functionality (verified via character instantiation test)
- ✅ Linting passes with no errors (ruff check)
- ✅ Character loads successfully without errors
- ✅ Literary quality matches reference examples

### Code Quality Assessment
**Excellent implementation.** The description:
1. Uses narrative prose style consistent with reference examples
2. Accurately captures key details: blonde hair, green eyes, mid-20s, slender, fair skin, freckles
3. Incorporates white strapless sundress from task specification
4. Reflects SDXL reference image details faithfully
5. Emphasizes protective guardian nature and sim human background
6. Length (3,067 chars) appropriate and well-balanced

### Technical Validation
- Python syntax: Valid
- Field positioning: Correct
- SDXL reference details accurately incorporated
- Character details match task specification exactly
- No regression in functionality

### Findings
**No issues found.** Implementation complete and meets all acceptance criteria. Reference image details successfully integrated. Task was completed but never marked as such.

### Recommendation
**APPROVE** - Move to `.codex/tasks/taskmaster/` for completion tracking.
