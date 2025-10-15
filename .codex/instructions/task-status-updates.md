# Task Status Update Protocol

To keep work-in-progress visibility consistent, every task file, planning
thread, or pull request description must end with a clear status indicator.
Coders, reviewers, and managers should verify these markers whenever a task is
touched.

## Required Status Markers
- `ready for review` &mdash; the implementation is complete and waiting for
  feedback.
- `more work needed` &mdash; the contributor is still iterating. Follow the tag
  with a short summary (and optionally a percentage complete) so the next
  person understands what remains.

Place one of the above phrases on its own line at the bottom of the document.
Do not add additional commentary after the marker.

## Review Checklist
Managers and reviewers should confirm that:
1. A status marker is present at the bottom of every active task file.
2. The marker reflects the current state of the work before leaving feedback or
   handing the task off.
3. Any time the status changes, the contributor updates the marker
   immediately.

If a marker is missing, request an update before proceeding so downstream
contributors have accurate visibility into task readiness.
