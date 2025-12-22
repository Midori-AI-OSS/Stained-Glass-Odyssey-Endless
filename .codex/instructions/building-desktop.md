# Building Desktop Packages

**Note:** The Docker-based desktop build tooling has been removed. Please use the local build script `./build.sh` instead.

## Usage

Run the build script from the repository root:

```bash
# Build non-llm variant for current platform
./build.sh

# Build specific variant
./build.sh llm-cpu

# Build for specific platform
./build.sh non-llm linux
./build.sh llm-cuda windows
```

See `BUILD.md` in the repository root for complete build instructions.
