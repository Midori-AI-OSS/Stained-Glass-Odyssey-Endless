# Task Priority Guidance

Tasks in this folder are lower priority than tasks in the parent `.codex/tasks` directory.

When placeholder relic art is required, update `luna_items_prompts.txt` with a text-to-photo prompt of Luna using the relic or item that should appear in the image. After saving the prompt, unblock any relic tasks that were waiting on that placeholder art. Once the prompt is recorded, placeholder art is fully complete even if a `.png` asset is not yet present—Luna Midori (Lead Developer) will hand-create the final files from the prompt list. Auditors should treat these tasks as satisfied and must not raise findings for the missing `.png` while it is in the Lead Developer queue.

Documentation reminder: relic plugins contain the authoritative `about` text, star rank, and behaviour descriptions. Do not create follow-up steps asking contributors to extend `.codex/implementation/relic-system.md`; keeping the plugin module accurate is enough.
