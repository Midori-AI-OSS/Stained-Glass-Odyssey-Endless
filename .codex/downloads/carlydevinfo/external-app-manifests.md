# External App Manifest Specification

External integrations declare themselves by placing an `app.toml` file inside
their package (for example `external-apps/my-tool/app.toml`). The loader reads
these manifests during startup, validates the contents, and registers any valid
entries with `AppLoader`.

> **Maintenance note:** The Settings UI bundles a copy of these instructions in
> `react-app/src/utils/appManifestDocs.ts`. Update that helper whenever this
> document—or the accompanying `app-loader-declaration-system.md` guide—changes
> so the downloadable reference stays in sync.

The **Settings → Manifest Resources** card hosts downloads for the manifest
template and the accompanying app-building documentation. Use **Download App
Manifest Template** to generate a commented starter manifest that matches the
active schema. Save the file as `app.toml` and customise the placeholders
before publishing. The **Download App-Building Docs** action provides the latest
guide for preparing and submitting integrations.

## Vetted Repository Synchronisation

Administrators maintain `external-apps/index.toml`, a vetted list of external
repositories. Each `[[apps]]` entry specifies the repository name, clone URL,
optional branch, and the relative path to its manifest:

```toml
[[apps]]
name = "markdown-viewer"
url = "https://github.com/example/markdown-viewer.git"
branch = "main" # optional – defaults to the repo's primary branch
manifest = "apps/markdown/app.toml"
```

Running `bun run scripts/syncExternalApps.ts` (automatically invoked by the
`predev` and `prebuild` hooks) clones any missing repositories into
`external-apps/<name>/` and performs a `git pull --ff-only` for existing
checkouts. Manifests must live at the declared relative path so the loader can
locate them.

## Required Fields

| Field | Type | Description |
| --- | --- | --- |
| `manifest_version` | integer | Schema version expected by the loader. The Settings template always matches the active loader version. |
| `name` | string | Unique identifier used with `openApp` / `closeApp`. Lowercase kebab-case is recommended. |
| `status` | string | Placement of the app in the UI. Allowed values: `system`, `app`, `sidebar`, `prototype` (case-insensitive). |
| `slot_count` | integer | Number of loader slots requested (1–3). Invalid values are clamped. |
| `niceness` | integer | Priority used when all slots are full (1–20). Lower numbers have higher priority. |
| `icon.module` | string | Must be `"lucide-react"`; icons are restricted to the shared Lucide pack. |
| `component.module` | string | Path to the module exporting the React panel component. Resolved relative to the manifest directory. |

Both `icon.module` and `component.module` may provide an optional `export` field
when the desired export is not the module's default. For icons this should match
the Lucide component name (for example `Sparkles` or `NotebookText`).

## Optional Metadata

Additional data can be supplied under the `metadata` table. The loader stores
this object unchanged on the registered descriptor so consuming components can
read any service-specific settings.

```toml
[metadata]
docs = "https://example.com/docs"
requires_auth = true
```

## Example Manifest

```toml
manifest_version = 1
name = "markdown-viewer"
status = "app"
slot_count = 1
niceness = 7

[icon]
module = "lucide-react"
export = "NotebookText"

[component]
module = "./MarkdownViewer.jsx"
```

## Validation Rules

- Manifests must be valid TOML documents. Files that fail to parse are rejected.
- Relative module paths are resolved against the manifest directory. The loader
  normalises separators and enforces absolute paths for dynamic imports.
- Duplicate app names—including collisions with built-in apps—are rejected.
- Unknown statuses or missing required fields cause the manifest to be logged
  and ignored.

Refer to `app-loader-declaration-system.md` for the conceptual overview of the
loader and how registered apps appear in the UI.
