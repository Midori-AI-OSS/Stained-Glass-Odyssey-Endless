# Auto-Audit Workflow

The auto-audit workflow automatically triggers code audits for task files that are marked as "ready for review" in pull requests.

## Overview

The workflow is designed to catch task files in `.codex/tasks/` that contain the "ready for review" marker and automatically create agent tasks to audit them according to the Auditor mode guidelines.

## How It Works

### 1. Label-Based Trigger (Automatic)

When a pull request is opened or updated:

1. **Labeler Workflow** (`.github/workflows/llm-labeler.yml`) runs
2. **Custom Script** (`.github/scripts/check-ready-for-audit.js`) checks all changed files
3. For files in `.codex/tasks/` that are added or modified:
   - Fetches the file content from the PR branch
   - Searches for "ready for review" (case insensitive)
   - If found, adds the "auditable" label to the PR
   - Posts a notification comment listing the files ready for audit
4. **Auto-Audit Workflow** (`.github/workflows/auto-audit.yml`) triggers on the "auditable" label
5. Scans `.codex/tasks/` directory for files with the ready marker
6. Creates GitHub Copilot agent tasks for each file found
7. Posts a hold comment and adds a thumbs-down reaction to prevent premature merging

### 2. Comment-Based Trigger (Manual)

For manual override or re-running audits:

1. Any authorized user can comment `@auditor` on a PR
2. The auto-audit workflow triggers on the comment
3. Checks out the PR branch
4. Same audit process runs as with label trigger
5. Useful for:
   - Re-running audits after fixes
   - Manual override when labeler doesn't trigger
   - Forcing audit on specific PRs

## Technical Details

### Workflow Files

- **`.github/workflows/llm-labeler.yml`**: Applies path-based labels and checks for audit markers
- **`.github/workflows/auto-audit.yml`**: Runs the actual audit process
- **`.github/scripts/check-ready-for-audit.js`**: Custom script to detect audit markers in PR files

### Trigger Conditions

The auto-audit workflow runs when:
- A PR receives the "auditable" label, OR
- A comment containing "@auditor" is posted on a PR by a non-bot user (prevents self-triggering)

### User Authorization

Only users listed in `ALLOWED_USERS` environment variable can trigger audits:
```yaml
env:
  ALLOWED_USERS: |
    lunamidori5
```

### Agent Task Creation

For each task file with "ready for review":
```bash
gh agent-task create "As an Auditor (read the codex mode file) audit <filepath>" --follow
```

The agent follows the Auditor mode guidelines from `.codex/modes/AUDITOR.md`.

### Audit Marker Detection

The script searches for this pattern (case insensitive):
- `ready for review`

Using regex (with extended regex mode): `/ready[[:space:]]+(to|for)[[:space:]]+review/i`

Note: The implementation accepts both "ready for review" (standard) and "ready to review" (backward compatibility) variants.

## Workflow Behavior

### Label Trigger Flow

```
PR opened/updated
  ↓
llm-labeler workflow runs
  ↓
check-ready-for-audit.js script runs
  ↓
Checks PR changed files in .codex/tasks/
  ↓
If "ready for review" found:
  ├─ Add "auditable" label
  ├─ Post notification comment
  └─ Trigger auto-audit workflow
       ↓
     Find task files with marker
       ↓
     Create agent tasks
       ↓
     Post hold comment + thumbs-down
```

### Comment Trigger Flow

```
User posts "@auditor" comment
  ↓
auto-audit workflow triggered
  ↓
Checkout PR branch
  ↓
Scan .codex/tasks/ for markers
  ↓
If found:
  ├─ Create agent tasks
  └─ Post hold comment + thumbs-down
```

## Benefits

✅ **Solves the Original Problem**: Detects markers in PR files before merge, not after  
✅ **Manual Override**: `@auditor` comment allows re-running or forcing audits  
✅ **Clear Communication**: Comments and labels show audit status  
✅ **Automatic**: No manual intervention needed for normal workflow  
✅ **Flexible**: Works with both automatic and manual triggers  

## Example Usage

### Automatic Trigger

1. Developer creates task file `.codex/tasks/relics/new-relic.md`
2. Adds "ready for review" footer to the file
3. Opens PR with the changes
4. Labeler workflow runs and adds "auditable" label
5. Auto-audit workflow triggers automatically
6. Agent tasks created and PR marked with hold comment

### Manual Trigger

1. Audit needs to be re-run after fixes
2. User comments `@auditor` on the PR
3. Auto-audit workflow triggers immediately
4. New audit runs on current PR state

## Related Files

- `.codex/modes/AUDITOR.md` - Auditor mode guidelines
- `.codex/audit/` - Audit reports directory
- `.github/workflows/auto-merge.yml` - Respects thumbs-down reaction from audits

## Maintenance Notes

- The script requires `@actions/github` and `@actions/core` packages (provided by GitHub Actions)
- The "auditable" label is automatically created if it doesn't exist
- Failed audits should be addressed before the label is removed or before re-running
- The workflow runs in a container: `lunamidori5/pixelarch:quartz`
- **Bot Protection**: The workflow includes protection against self-triggering by excluding comments from bot users (`github.event.comment.user.type != 'Bot'`). This prevents the workflow's own comments from triggering additional runs.
