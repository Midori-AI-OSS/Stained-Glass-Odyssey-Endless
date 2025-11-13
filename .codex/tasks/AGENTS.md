# Task Organization System

Tasks are organized by status into three main folders:

## Status Folders

### wip/ - Work In Progress
Tasks that are actively being developed by coders. When a task is complete and ready for review, move it to the corresponding subfolder in `review/`.

### review/ - Ready for Review
Tasks that are complete and awaiting auditor review. After review:
- If approved, move to the corresponding subfolder in `taskmaster/`
- If changes are needed, move back to the corresponding subfolder in `wip/` with feedback

### taskmaster/ - Task Master Review
Tasks that have been fully audited and are awaiting final Task Master sign-off. The Task Master can either:
- Close the task as complete (delete the task file)
- Request additional changes (move back to the corresponding subfolder in `wip/` with clarifications)

## Category Organization

Each status folder contains category-specific subfolders:

- **cards/** - Card implementation tasks
- **chars/** - Character implementation tasks
- **docs/** - Documentation tasks
- **items/** - Item implementation tasks
- **passives/** - Passive ability tasks (organized by tier: boss, glitched, normal, prime)
- **relics/** - Relic implementation tasks
- **tests/** - Test-related tasks

## Workflow

1. **Task Creation**: Task Master creates new tasks in the appropriate category subfolder within `wip/`
2. **Development**: Coders work on tasks in `wip/` and move them to `review/` when complete
3. **Auditing**: Auditors review tasks in `review/` and move them to `taskmaster/` if approved, or back to `wip/` if changes are needed
4. **Completion**: Task Master reviews tasks in `taskmaster/` and closes them when satisfied

## Legacy Files

Tasks placed directly in this folder (not in wip, review, or taskmaster subfolders) are legacy files from the old tag-based system. These should be moved into the appropriate status and category folders.
