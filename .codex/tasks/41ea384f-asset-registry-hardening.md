Coder, finalize the asset registry rollout with documentation, QA, and metadata hooks.

## Context
- After portraits, rewards, and audio loaders migrate to the registry, the supporting docs and QA pipelines need to reflect the new architecture.

## Requirements
- Sweep the frontend codebase for any remaining direct `import.meta.glob` asset lookups and convert them to registry calls, or document why they must stay bespoke.
- Add regression/end-to-end tests covering a representative run (portraits, summons, rewards, audio) to ensure the registry wiring works in the browser bundle.
- Update developer onboarding docs and `.codex/instructions/` notes to explain how to register new asset families and how metadata flows into the registry.
- Ensure telemetry/logging captures registry lookup failures with actionable metadata, and document the troubleshooting steps for QA.
- Validate that metadata-injected overrides (alias descriptors, rarity-specific folders, rewards/audio annotations) round-trip t
  hrough the registry and call out the verification steps in your PR acceptance notes for QA.

## Notes
- Coordinate with concurrent metadata tasks (alias pipeline, music weighting) so documentation references the final descriptor shapes.
