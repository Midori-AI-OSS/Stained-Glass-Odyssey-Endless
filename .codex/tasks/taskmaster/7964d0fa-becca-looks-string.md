# Add Looks String to Becca Character

## Description
Add a `looks` field to the Becca character class (`backend/plugins/characters/becca.py`) following the format used in Luna, Ryne, Lady Light, and Lady Darkness.

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
- **Hair:** Blonde with blue ombre ponytail
- **Eyes:** Purple
- **Build:** Slender
- **Skin:** Fair and smooth with freckles on nose and cheeks
- **Makeup:** Light
- **Outfit:** Space strapless loose sundress
- **Accessory:** Paintbrush

**SDXL Prompt Reference:**
`(blonde-- with blue--- ombre-- ponytail hair)++, (purple- eyes)++, (female), (mid 20s), (slender build), (fair and smooth skin), (freckles on nose and cheeks), (light makeup), (space+ strapless lose sundress)+++, (paint brush)++`

## Acceptance Criteria
- [x] `looks` field added to the Becca dataclass
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

## Implementation Notes
**Completed:** 2025-11-13  
**Implemented by:** Coder Mode Agent

Added 7-paragraph visual description covering:
- Slender sim human build with idealized proportions (5'5", mid-20s)
- Signature blonde-to-blue ombre ponytail with smooth color transition
- Purple eyes with artistic focus and light makeup with freckles
- Space-themed strapless sundress with nebula patterns
- Paintbrush accessory as working tool and identity marker
- Menagerie bond visual effects (elemental creature silhouettes, fractal patterns)
- Artistic behavioral patterns (canvas analysis, fluid gestures, compositional thinking)

Description integrates SDXL prompt details and character's artistic/organizational nature while matching repository's literary standards.

File location: `backend/plugins/characters/becca.py` (lines 18-25)

---

## Audit Report
**Audited:** 2025-11-13  
**Auditor:** Auditor Mode Agent  
**Status:** ✅ **APPROVED** - Ready for taskmaster

### Verification Checklist
- ✅ `looks` field added to Becca dataclass (line 18)
- ✅ Content follows multi-paragraph narrative prose format (7 paragraphs, 5,794 characters)
- ✅ Triple-quoted string format used correctly
- ✅ Positioned after `summarized_about` (line 17) and before `char_type` (line 27)
- ✅ No changes to existing functionality (verified via character instantiation test)
- ✅ Linting passes with no errors (ruff check)
- ✅ Character loads successfully without errors
- ✅ Literary quality matches Luna/Lady Light reference examples

### Code Quality Assessment
**Exceptional implementation with technical integration.** The description:
1. Uses narrative prose style consistent with reference examples
2. Accurately incorporates SDXL prompt details (blonde-blue ombre, purple eyes, etc.)
3. Integrates character's "sim human" and SDXL art bot background into visual presentation
4. Covers physical appearance, signature ombre hair, purple eyes, space dress, paintbrush
5. Weaves artistic identity throughout (compositional thinking, canvas analysis)
6. Menagerie bond abilities visualized with elemental creature silhouettes
7. Total length (5,794 chars) appropriate, slightly longer than references for added detail
8. Successfully balances SDXL technical specifications with narrative literary quality

### Technical Validation
- Python syntax: Valid
- Import structure: Correct (dataclass pattern maintained)
- Field positioning: Correct (after `summarized_about`, before `char_type`)
- SDXL prompt details accurately reflected in prose
- No regression in character loading or game functionality
- Documentation (player-foe-reference.md) already includes Becca
- Character backstory (sim human, former SDXL bot) elegantly woven into appearance

### Findings
**No issues found.** Implementation successfully merges technical SDXL specifications with literary prose while maintaining high quality standards and character consistency.

### Recommendation
**APPROVE** - Move to `.codex/tasks/taskmaster/` for completion tracking.

