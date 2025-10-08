# Error Overlay

`src/lib/ErrorOverlay.svelte` wraps `PopupWindow.svelte` to present API or runtime errors.
The overlay now shows the error message, optional traceback, and when available an annotated
code snippet (from the backend `context.source` payload) with the faulting line highlighted.
The "Report Issue" button prepopulates a GitHub issue with the traceback and snippet using
the `FEEDBACK_URL` constant. It is opened via `openOverlay('error', { message, traceback, context })`,
but callers that omit `context` continue to render correctly.
