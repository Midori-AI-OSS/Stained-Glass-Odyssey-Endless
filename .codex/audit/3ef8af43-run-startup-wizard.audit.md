# Run Startup Wizard Audit

## Scope
- `.codex/tasks/33e45df1-run-start-flow.goal`
- `.codex/tasks/a45ae75f-run-startup-wizard.md`
- Frontend wizard implementation (`frontend/src/lib/components/RunChooser.svelte`)
- Supporting UI API changes (`frontend/src/lib/systems/uiApi.js`) and backend run configuration helpers
- Documentation updates under `.codex/implementation`

## Summary
The implementation delivers a feature-rich wizard with metadata-driven UI, telemetry hooks, and updated backend validation. Documentation now outlines the metadata contract and flow. However, key acceptance criteria remain unmet: the step indicator has a numbering defect when the resume step is hidden, and no automated frontend coverage exists for the wizard state machine despite the task requirements explicitly calling for it. These issues block readiness for Task Master review.

## Findings
1. **Step indicator numbering breaks without existing runs**  
   When there are no resumable runs, the `resume` step is skipped in the indicator markup but the component still renders `{index + 1}` for subsequent steps, causing the wizard to display step numbers beginning at `2` instead of `1`. This violates the wizard polish expectations and can confuse users during first-run onboarding. 【F:frontend/src/lib/components/RunChooser.svelte†L463-L475】

2. **Missing frontend automated coverage for the wizard**  
   Requirement 4 mandates adding frontend tests that exercise the wizard state machine and persistence, yet there are no new tests referencing the wizard or `RunChooser` component. Searches across the `frontend/tests` suite confirm the absence of any wizard-oriented specs, leaving critical flows unverified. 【F:.codex/tasks/a45ae75f-run-startup-wizard.md†L11-L26】【9ff29f†L1-L1】

## Recommendations
- Adjust the step indicator to derive its numbering from the set of visible steps (e.g., by tracking a filtered sequence or separate counter) so the first step always displays as `1`, even when skipping `resume`.
- Add Vitest coverage that walks through the wizard steps (resume bypass, party selection, run type selection, modifier adjustments, confirmation) and asserts local storage persistence, telemetry calls, and payload normalization. Include regression coverage for metadata failure handling.

## Conclusion
Because of the UI defect and missing automated tests, the task is **not ready** for Task Master review. Address the findings above and rerun the audit once resolved.
