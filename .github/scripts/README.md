# Audit Workflow Scripts

This directory contains scripts used by GitHub Actions workflows to automate the audit process.

## check-ready-for-audit.js

Scans pull request files in `.codex/tasks/` for the "ready for review" marker.

### Purpose

When a PR is opened or updated, this script:
1. Fetches all changed files in the PR
2. Filters for files in `.codex/tasks/` that were added or modified
3. Checks each file's content for audit markers
4. Adds "auditable" label if markers are found
5. Posts a notification comment listing files ready for audit

### Usage

Called automatically by `.github/workflows/llm-labeler.yml`:

```yaml
- name: Check for audit markers in task files
  uses: actions/github-script@v7
  with:
    script: |
      const checkReadyForAudit = require('./.github/scripts/check-ready-for-audit.js');
      await checkReadyForAudit({ github, context, core });
```

### Detection Pattern

The script searches for this marker (case insensitive):
- `ready for review`

Using regex: `/ready\s+for\s+review/i`

Note: The implementation also accepts "ready to review" for backward compatibility, but the standard marker is "ready for review".

### Output

When markers are found:
- Adds "auditable" label to the PR
- Posts comment: "🔍 Detected task file(s) ready for audit: ..."
- Lists all matching files

When no markers found:
- No action taken
- Logs info message in workflow

### Example

Task file with marker:
```markdown
# Eclipse Reactor: burst-for-blood 5★ relic

## Summary
...

## Requirements
- Implement feature X
- Add tests for Y

---

ready for review
```

The script will:
1. Detect the marker
2. Add "auditable" label
3. Post notification comment
4. Trigger auto-audit workflow

### Error Handling

- Skips files that fail to fetch (logs warning)
- Handles PRs with no task files (exits cleanly)
- Validates PR context before running

### Dependencies

Requires GitHub Actions environment with:
- `@actions/github` - GitHub API client
- `@actions/core` - Workflow logging utilities

These are automatically available in `actions/github-script@v7` action.

### Related Files

- `.github/workflows/llm-labeler.yml` - Calls this script
- `.github/workflows/auto-audit.yml` - Triggered by the label this script adds
- `.codex/implementation/audit-workflow.md` - Full workflow documentation
