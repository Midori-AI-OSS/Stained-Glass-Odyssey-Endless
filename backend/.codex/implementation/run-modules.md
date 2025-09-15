# Run Management Modules

The backend's former `game.py` helpers have been split into focused modules under `runs/`:

- `runs/encryption.py` – provides `get_save_manager` and `get_fernet` with global caching.
- `runs/party_manager.py` – utilities for party and player customization, loading and saving parties, and passive descriptions.
- `runs/lifecycle.py` – manages run and battle state, map persistence, and exposes the `_run_battle` coroutine used by room services.

These modules are imported directly by services and tests, reducing coupling and clarifying responsibilities.

