Coder, expose shareable battle log endpoints for completed runs.

## Context
- The current API only serves live run summaries; there is no `GET /logs/<run_id>` surface for the frontend to hydrate standalone battle reviews.

## Requirements
- Add backend routes `GET /logs/<run_id>` and `GET /logs/<run_id>/battles/<index>/{summary,events}` that mirror the data returned for active runs, including battle start/end timestamps, participants, and file-backed event payloads.
- Ensure the routes authenticate/authorize the same way as existing run endpoints and include pagination or streaming as needed for large logs.
- Provide integration tests covering the new routes and document the payload shape so the frontend can rely on it.
- Update the tracking database plan (task `5aa0a6dd-run-history-database`) to include a `logs_url` field referencing the new endpoint rather than duplicating combat data in SQLCipher.

## Notes
- Coordinate with storage owners if file-backed logs require new retention or cleanup policies.
