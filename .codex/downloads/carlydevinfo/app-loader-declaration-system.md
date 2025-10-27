#### App Loader Declaration System

`AppLoader` orchestrates the WebUI's multi-panel layout. It lazily imports each
app, decides which component should be visible, and keeps the hamburger menu in
sync with registered integrations. Every panel—built-in or external—declares
itself to the loader using a small descriptor so the UI can treat them uniformly.

### Loader Registration Flow

Apps register at startup via `AppLoader.register({ name, status, icon,
slotCount, niceness })`. The helper pushes into ChatContext's
`registeredApps` array so the hamburger menu builds itself from the active
descriptors.

`status` determines where an app appears:
- **System** – essential apps hidden from the menu (e.g. Chat)
- **App** – standard panels listed under **Apps**
- **Sidebar** – overlay utilities listed under **Sidebars**
- **Prototype** – experimental panels hidden until enabled in Settings

Prototype entries only surface when the **Show Prototype Apps** toggle in the
Settings panel is turned on. System apps mount automatically when the UI loads
and remain open until closed via `closeApp`.

### External Manifest Integration

External integrations place an `app.toml` manifest inside their package (see the
`external-app-manifests.md` guide for the schema). During startup `AppLoader`
scans `external-apps/**/app.toml`, validates each descriptor, and registers any
valid entries before the built-in defaults. Invalid manifests are logged with
the rejection reason and skipped so they cannot break startup.

Each manifest provides the same core fields as the runtime API:

- `name` – identifier used with `openApp` / `closeApp`
- `status` – controls menu placement using the statuses above
- `slot_count` – number of loader slots to reserve (clamped to `1–3`)
- `niceness` – priority used when all slots are full (`1`–`20`, lower is higher)
- `icon.module` – currently restricted to `"lucide-react"`
- `component.module` – module exporting the React panel component

Optional `export` keys select named exports for the icon or component modules.
Manifests may also include a free-form `metadata` table that is surfaced to
consuming components untouched.

### Working with the Loader

- Use the `openApp` and `closeApp` actions from `useChat` so the loader can keep
  slot ownership and niceness ordering accurate. Legacy toggles such as
  `toggleMemoryPanel` were removed.
- `lockApp` and `unlockApp` prevent an app from being evicted when the screen is
  full.
- Up to four horizontal slots are available. When an app requests more slots
  than remain, the loader automatically evicts the lowest-priority app that
  conflicts with the requested niceness.
- Chat starts with a niceness of `1` and yields slots on the right as other apps
  open. New apps appear from the rightmost available slot without shifting the
  existing panels.
- Clicking outside a panel never closes it—every panel must expose its own close
  affordance.

### Implementation Checklist

1. Extend `AppLoader` with a `register` helper and export it.
2. Surface `registeredApps` from ChatContext so the hamburger menu can enumerate
   them.
3. Update the hamburger menu to read from `registeredApps` instead of hardcoded
   lists.
4. Follow the layout rules in
   `.github/instructions/app-loader-guidelines.instructions.md` when opening or
   closing apps.
5. Register the built-in panels—Chat, History, Memory, Profile, Files, and
   Settings—using this system so their descriptors stay authoritative.
6. Gate prototype entries behind the **Show Prototype Apps** setting.
