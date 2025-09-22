# Asset Pipeline

1. Research art styles: low-poly look reminiscent of *Final Fantasy VII* and *VIII* or pixelated 3D hybrids.
2. Evaluate free/CC model sources for web-friendly formats such as `.glb`/`.gltf`.
3. Establish conversion workflow (e.g., Blender → `.glb`/`.gltf`) with cached builds.
4. Create asset loading utilities and preload to reduce runtime stalls.
5. Code structure:
   - Maintain an `assets.toml` manifest mapping asset keys to file paths and hashes.
   - Build an `AssetManager` that loads and caches models, textures, and sounds on demand.
   - Expose `get_asset`, `get_model`, `get_texture`, and `get_audio` helpers with tests for missing entries and cache reuse.
