# Carly WebUI App Manifest Guide

The Carly WebUI registers built-in and external panels through a shared loader. External apps publish an `app.toml` manifest that declares how the integration should appear inside the interface. This guide combines the schema reference with an overview of the loader so you can validate manifests before submitting them.

## External App Manifest Specification

Place your manifest inside the integration package—for example, `external-apps/my-tool/app.toml`. During startup the loader reads each manifest, validates the contents, and registers valid entries.

### Vetted Repository Synchronisation

Administrators curate `external-apps/index.toml`, which lists approved repositories. Each entry specifies the repository name, clone URL, optional branch, and the manifest path. Running `bun run scripts/syncExternalApps.ts` (also triggered by `predev` and `prebuild`) ensures the repositories are cloned or fast-forwarded before validation.

### Required Fields

| Field | Type | Description |
| --- | --- | --- |
| `manifest_version` | integer | Must be set to `1` to match the active loader schema. |
| `name` | string | Unique identifier used with `openApp` / `closeApp`. Lowercase kebab-case is recommended. |
| `status` | string | Placement of the app in the UI. Allowed values: `system`, `app`, `sidebar`, `prototype`. |
| `slot_count` | integer | Number of loader slots requested (1–3). Invalid values are clamped. |
| `niceness` | integer | Priority used when all slots are full (1–20). Lower numbers have higher priority. |
| `icon.module` | string | Must be "lucide-react"; icons are restricted to the shared Lucide pack. |
| `component.module` | string | Module exporting the React panel component. Resolved relative to the manifest directory. |

Both `icon` and `component` tables may provide an optional `export` key when the desired export is not the module's default. A free-form `metadata` table is also supported and is passed through untouched.

### Example Manifest

```toml
manifest_version = 1
name = "example-app"
status = "app"
slot_count = 1
niceness = 7

[icon]
module = "lucide-react"
export = "NotebookText"

[component]
module = "./ExampleApp.jsx"
```

## App Loader Declaration System

`AppLoader` orchestrates the multi-panel layout. It lazily imports each app, decides which component should be visible, and keeps the hamburger menu synchronised with registered integrations. Every panel—built-in or external—declares itself to the loader so the UI can treat them uniformly.

### Loader Registration Flow

Apps register at startup via `AppLoader.register({ name, status, icon, slotCount, niceness })`. The helper pushes descriptors into ChatContext so the hamburger menu builds itself from the active entries.

- **System** apps are essential panels hidden from the menu.
- **App** entries are standard panels listed under **Apps**.
- **Sidebar** utilities appear under **Sidebars**.
- **Prototype** panels remain hidden until enabled in Settings.

Prototype entries surface only when **Show Prototype Apps** is enabled. System apps mount automatically and remain open until closed with `closeApp`.

### Working with the Loader

- Use the `openApp` and `closeApp` actions from `useChat` so the loader can keep slot ownership and niceness ordering accurate.
- `lockApp` and `unlockApp` prevent eviction when the layout is full.
- Up to four horizontal slots are available. When an app requests more slots than remain, the loader automatically evicts the lowest-priority conflicting panel.
- Chat starts with a niceness of `1` and yields slots on the right as other apps open.
- Clicking outside a panel never closes it—each panel must expose its own close affordance.

## Building an App

Follow these steps to host an external integration inside the loader:

1. Create a React component under `external-apps/<app-name>/`—for example `external-apps/chatgpt-demo/ChatGPTDemoPanel.jsx`. Panels gain loader awareness by calling `const { actions } = useChat();`.
2. Use the `actions.lockApp(name)` and `actions.unlockApp(name)` helpers to control eviction when your panel must stay visible, and wire the close affordance to `actions.closeApp(name)` so the loader can reclaim the reserved slots.
3. Render your external experience inside the shared layout shell. Most integrations embed an `<iframe>` that points at `https://chatgpt.com/` (or another approved endpoint) inside the shared `Viewport` region so styling stays consistent with built-in panels.
4. Define an `app.toml` manifest that maps your component into the loader and register the repository inside `external-apps/index.toml` so the sync script can fetch it.

### Manifest: ChatGPT Demo

```toml
manifest_version = 1
name = "chatgpt-demo"
status = "app"
slot_count = 2
niceness = 5

[icon]
module = "lucide-react"
export = "Bot"

[component]
module = "./ChatGPTDemoPanel.jsx"
export = "ChatGPTDemoPanel"
```

Setting `slot_count = 2` reserves a double-width surface for the panel. The component's close handler should invoke `actions.closeApp('chatgpt-demo')` so both slots are relinquished immediately when the user exits.

### React Component Example

```jsx
import React, { useEffect } from 'react';
import useChat from '../../src/context/ChatContext/useChat.js';
import {
  Container,
  Header,
  Title,
  CloseButton,
  Viewport,
} from '../../src/components/shared/AppStyles';

const ChatGPTDemoPanel = () => {
  const { actions } = useChat();

  useEffect(() => {
    actions.lockApp('chatgpt-demo');
    return () => {
      actions.unlockApp('chatgpt-demo');
    };
  }, [actions]);

  const handleClose = () => {
    actions.unlockApp('chatgpt-demo');
    actions.closeApp('chatgpt-demo');
  };

  return (
    <Container moodColor="#6C63FF">
      <Header moodColor="#6C63FF">
        <Title>ChatGPT Demo</Title>
        <CloseButton
          moodColor="#6C63FF"
          onClick={handleClose}
          aria-label="Close ChatGPT demo"
        >
          ×
        </CloseButton>
      </Header>
      <Viewport
        as="iframe"
        src="https://chatgpt.com/"
        title="ChatGPT Demo"
        allow="clipboard-read; clipboard-write; microphone"
      />
    </Container>
  );
};

export default ChatGPTDemoPanel;
```

For additional context or updates, refer to the .codex/implementation/external-app-manifests.md and .codex/implementation/app-loader-declaration-system.md documents in the repository.