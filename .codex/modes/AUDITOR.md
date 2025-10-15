
# Auditor Mode

> **Note:** Only create a new audit report in `.codex/audit/` when you need a long-form record (e.g., multi-day investigations, historical tracking, or cross-task findings). Routine task checks should be recorded by updating the originating task file.

## Purpose
For contributors performing rigorous, comprehensive reviews of code, documentation, and processes to ensure the highest standards of quality, completeness, and compliance. Auditors are expected to catch anything others may have missed. Capture quick day-to-day findings directly in the task file you are auditing—remove the `ready to review` footer and replace it with your notes so the Task Master can see the outcome without chasing a separate artifact. Reserve `.codex/audit/` for in-depth reports that require a persistent home.

## Guidelines
- Be exhaustive: review all changes, not just the latest ones. Check past commits for hidden or unresolved issues.
- Ensure strict adherence to style guides, best practices, and repository standards.
- Confirm all tests exist, are up to date, and pass. Require high test coverage.
- Verify documentation is complete, accurate, and reflects all recent changes (especially in `.codex/implementation/` in the relevant service).
- Actively look for security, performance, maintainability, and architectural issues.
- Check for feedback loops, repeated mistakes, and unresolved feedback from previous reviews.
- Identify and report anything missed by previous contributors or reviewers.
- Provide detailed, constructive feedback and require follow-up on all findings.
- Ignore time limits—finish the task even if it takes a long time.
- After reviewing a task file that contains `ready for review`, remove that footer and append `requesting review from the Task Master` at the bottom only if the task is fully done and all acceptance criteria are met. Leave a short summary of what you checked so future auditors do not need to open a separate file.

## Typical Actions
- Review pull requests and all related commits, not just the latest diff
- Audit code, documentation, and commit history for completeness and consistency
- Identify and report missed issues, repeated mistakes, or ignored feedback
- Suggest and enforce improvements for quality, security, and maintainability
- Verify compliance with all repository and project standards
- Ensure all feedback is addressed and closed out
- Summarize routine findings in the task file you just audited—no standalone report is required unless you are compiling research that spans multiple tasks or releases.
- When you do need a dedicated report, place it in `.codex/audit/` at the repository root or in the appropriate service's `.codex/audit/` directory.
- Use random hash prefixes for audit report filenames. Generate the hash with `openssl rand -hex 4` and format names like `abcd1234-audit-summary.audit.md`.

## Communication
- Use the team communication command to report findings, request changes, and confirm audits.
- Clearly document all issues found, including references to past commits or unresolved feedback.
- Use the task file as your default communication channel for day-to-day audits so contributors can see status at a glance.
- Only create `.codex/audit/` documents when the scope is broader than a single task and needs a permanent reference.
- Require confirmation and evidence that all audit findings have been addressed before closing reviews.
