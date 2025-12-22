# Building Desktop Packages

Desktop builds for Linux and macOS can be created using the `build.sh` script.

## Usage

Run the helper script from the repository root:

```bash
./build.sh non-llm linux     # builds non-llm variant for Linux
./build.sh llm-cpu linux      # builds with CPU-based LLM support
```

The script:

1. Compiles the Python backend with PyInstaller using `uv`.
2. Bundles the Svelte frontend with `bun`.

Artifacts are written to `backend/dist/` on the host.
