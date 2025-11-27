# Ready for Review

Tasks in this folder are complete and ready for auditor review.

## Folder Organization

This folder contains category-specific subfolders for organizing tasks ready for auditing:

- **cards/** - Card implementation tasks ready for review
- **chars/** - Character implementation tasks ready for review
- **docs/** - Documentation tasks ready for review
- **items/** - Item implementation tasks ready for review
- **passives/** - Passive ability tasks ready for review (see subfolders for tiers)
- **relics/** - Relic implementation tasks ready for review
- **tests/** - Test-related tasks ready for review

### Passive Tiers

The **passives/** folder is further organized by tier:

- **boss/** - Boss-tier passive modifier tasks ready for review
- **glitched/** - Glitched-tier passive modifier tasks ready for review
- **prime/** - Prime-tier passive modifier tasks ready for review
- **normal/** - Normal-tier (baseline) passive tasks ready for review

## Workflow

Tasks in this folder are awaiting review by auditors. After review:
- If the task passes review, it should be moved to `../taskmaster/` in the corresponding subfolder
- If the task needs more work, it should be moved back to `../wip/` in the corresponding subfolder with feedback
