# Task Status Update Protocol

To keep work-in-progress visibility consistent, every task file, planning
thread, or pull request description must end with a clear status indicator.
Coders, reviewers, and managers should verify these markers whenever a task is
touched.

## Task Creation vs. In-Progress Updates

- **Task Master drafts:** Leave the status marker off entirely when creating a
  new task file. This signals to contributors that the work has not yet been
  started. The first coder or reviewer to touch the task should add the
  appropriate marker once they begin work.
- **Active or reviewed tasks:** After someone begins implementing, reviewing,
  or handing back a task, add exactly one marker from the list below on its own
  line at the bottom of the document. Do not append additional commentary after
  the marker.

### Allowed Status Markers
- `ready for review` — the implementation is complete and waiting for
  feedback.
- `requesting review from the Task Master` — reviewers append this when
  they hand a fully-audited task back to the Task Master. Treat it as an
  extension of the `ready for review` state rather than a missing marker.
- `more work needed` — the contributor is still iterating. Follow the tag
  with a short summary (and optionally a percentage complete) so the next
  person understands what remains.

## Review Checklist
Managers and reviewers should confirm that:
1. Newly authored Task Master files intentionally omit a status marker until a
   contributor starts work.
2. A marker is present at the bottom of every active task file after work
   begins.
3. The marker reflects the current state of the work before leaving feedback or
   handing the task off.
4. Any time the status changes, the contributor updates the marker
   immediately.

If a marker is missing, request an update before proceeding so downstream
contributors have accurate visibility into task readiness.

# Task Priority Guidance

Tasks placed directly in this folder are **high priority** and should be addressed before tasks in subfolders.
