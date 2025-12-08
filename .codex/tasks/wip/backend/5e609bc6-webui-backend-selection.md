# Add Backend Selection to WebUI

## Task ID
`5e609bc6-webui-backend-selection`

## Priority
Medium

## Status
WIP

## Description
Update the existing LRM settings UI in the WebUI to support backend selection between OpenAI and HuggingFace agents, configure OpenAI API URL (optional), and select appropriate models based on the chosen backend.

## Context
After migrating to the Midori AI Agent Framework, the backend supports two agent backends:
1. **OpenAI agents** - For users with OpenAI API or compatible servers (Ollama, LocalAI, etc.)
2. **HuggingFace agents** - For local inference without external dependencies

**Existing UI Components:**
- `frontend/src/lib/components/LLMSettings.svelte` - Current LRM model selection UI
- `frontend/src/lib/components/SettingsMenu.svelte` - Settings menu that includes LLM settings
- `frontend/src/lib/systems/api.js` - API functions: `getLrmConfig()`, `setLrmModel()`, `testLrmModel()`

Currently, the UI only shows a model dropdown. It needs to be enhanced to support backend selection and optional API URL configuration.

## Rationale
- **User-Friendly**: GUI instead of editing config files or env vars
- **Flexibility**: Easy switching between local and remote backends
- **Discoverability**: Users can see what options are available
- **Validation**: UI can validate settings before saving
- **Existing Foundation**: Build on existing LLMSettings component

## Objectives
1. Enhance existing LLMSettings component to add backend selection dropdown (OpenAI / HuggingFace)
2. Add OpenAI API URL input field (optional, for custom servers)
3. Update model dropdown to show backend-appropriate models
4. Update backend API to support new parameters
5. Use recommended model for HuggingFace (openai/gpt-oss-20b with high reasoning)

## Implementation Steps

### Step 1: Review Existing UI Components
**Current implementation:**
- `frontend/src/lib/components/LLMSettings.svelte` - Displays LRM model dropdown and test button
  - Props: `lrmModel`, `lrmOptions`, `handleModelChange`, `handleTestModel`, `testReply`
  - Currently shows only model selection
- `frontend/src/lib/components/SettingsMenu.svelte` - Parent component managing settings
  - Functions: `handleModelChange()`, `handleTestModel()`
  - API calls: `getLrmConfig()`, `setLrmModel()`, `testLrmModel()`
- `frontend/src/lib/systems/api.js` - API interface functions
  - `getLrmConfig()` → GET `/config/lrm`
  - `setLrmModel(model)` → POST `/config/lrm`
  - `testLrmModel(prompt)` → POST `/config/lrm/test`

**Required enhancements:**
1. Add backend selection dropdown to LLMSettings.svelte
2. Add optional API URL input field
3. Update model dropdown to filter by backend
4. Extend backend API to return/accept backend and base_url parameters

### Step 2: Update Backend API Endpoints
Enhance existing `/config/lrm` endpoints in `backend/routes/config.py`:

```python
@bp.get("/lrm")
async def get_lrm_config():
    """Get current LRM configuration with backend info."""
    from llms.agent_loader import get_agent_config
    
    config = get_agent_config()
    
    # Enhanced response with backend information
    payload = {
        "current_model": config.model if config else os.getenv("AF_LLM_MODEL", "gpt-oss:20b"),
        "backend": config.backend if config else "openai",
        "base_url": config.base_url if config else os.getenv("OPENAI_API_URL"),
        "available_backends": ["openai", "huggingface"],
        "available_models": {
            "openai": ["gpt-oss:20b", "gpt-4", "gpt-3.5-turbo", "llama3:8b"],
            "huggingface": ["openai/gpt-oss-20b"],  # Recommended with high reasoning
        },
    }
    try:
        await log_menu_action("Settings", "view_lrm", {"backend": payload["backend"]})
    except Exception:
        pass
    return jsonify(payload)


@bp.post("/lrm")
async def set_lrm_model():
    """Set LRM configuration including backend and model."""
    data = await request.get_json()
    backend = data.get("backend")
    model = data.get("model", "")
    base_url = data.get("base_url")
    
    # Validate backend if provided
    if backend and backend not in ["openai", "huggingface"]:
        return jsonify({"error": "Invalid backend"}), 400
    
    old_model = get_option(OptionKey.LRM_MODEL, ModelName.OPENAI_20B.value)
    
    # Save configuration
    if backend:
        set_option("agent_backend", backend)
    if model:
        set_option(OptionKey.LRM_MODEL, model)
    if base_url is not None:  # Allow clearing URL
        set_option("agent_base_url", base_url)
    
    try:
        await log_settings_change("lrm_config", old_model, {"backend": backend, "model": model})
    except Exception:
        pass
    
    return jsonify({
        "current_model": model,
        "backend": backend,
        "base_url": base_url
    })
```

### Step 3: Update LLMSettings Component
Enhance `frontend/src/lib/components/LLMSettings.svelte`:

```svelte
<script>
  export let lrmModel = '';
  export let lrmBackend = 'openai';  // NEW
  export let lrmBaseUrl = '';  // NEW
  export let lrmOptions = [];
  export let availableBackends = ['openai', 'huggingface'];  // NEW
  export let modelsByBackend = {};  // NEW
  export let handleModelChange;
  export let handleBackendChange;  // NEW
  export let handleBaseUrlChange;  // NEW
  export let handleTestModel;
  export let testReply = '';
  
  // Filter models based on selected backend
  $: filteredModels = modelsByBackend[lrmBackend] || lrmOptions;
</script>

<div class="settings-panel">
  <!-- Backend Selection -->
  <div class="control" title="Select agent backend type.">
    <div class="control-left">
      <span class="label">Backend</span>
    </div>
    <div class="control-right">
      <select bind:value={lrmBackend} on:change={handleBackendChange}>
        {#each availableBackends as backend}
          <option value={backend}>
            {backend === 'openai' ? 'OpenAI (API/Ollama/LocalAI)' : 'HuggingFace (Local)'}
          </option>
        {/each}
      </select>
    </div>
  </div>
  
  <!-- API URL (only for OpenAI backend) -->
  {#if lrmBackend === 'openai'}
    <div class="control" title="Optional: Custom OpenAI-compatible API URL">
      <div class="control-left">
        <span class="label">API URL</span>
      </div>
      <div class="control-right">
        <input 
          type="text" 
          bind:value={lrmBaseUrl} 
          on:blur={handleBaseUrlChange}
          placeholder="http://localhost:11434/v1 (optional)"
        />
      </div>
    </div>
  {/if}
  
  <!-- Model Selection -->
  <div class="control" title="Select language reasoning model.">
    <div class="control-left">
      <span class="label">Model</span>
    </div>
    <div class="control-right">
      <select bind:value={lrmModel} on:change={handleModelChange}>
        {#each filteredModels as opt}
          <option value={opt}>{opt}</option>
        {/each}
      </select>
    </div>
  </div>
  
  <!-- Test Model Button -->
  <div class="control" title="Send a sample prompt to the selected model.">
    <div class="control-left">
      <span class="label">Test Model</span>
    </div>
    <div class="control-right">
      <button class="icon-btn" on:click={handleTestModel}>Test</button>
    </div>
  </div>
  
  {#if testReply}
    <p class="status" data-testid="lrm-test-reply">{testReply}</p>
  {/if}
</div>

<style>
  @import './settings-shared.css';
  input[type="text"] {
    width: 100%;
    padding: 4px 8px;
    border: 1px solid var(--border-color, #ccc);
    border-radius: 4px;
    background: var(--input-bg, #fff);
    color: var(--text-color, #000);
  }
</style>
```

### Step 4: Update SettingsMenu Component
Enhance handler functions in `frontend/src/lib/components/SettingsMenu.svelte`:

```javascript
    
    // Populate UI
    document.getElementById('backend-select').value = data.backend;
    document.getElementById('model-select').innerHTML = 
        data.recommended_models[data.backend]
            .map(m => `<option value="${m}">${m}</option>`)
            .join('');
    document.getElementById('model-select').value = data.model;
    
    // Show/hide OpenAI URL field
    const urlField = document.getElementById('openai-url-field');
    urlField.style.display = data.backend === 'openai' ? 'block' : 'none';
    if (data.base_url) {
        document.getElementById('openai-url').value = data.base_url;
    }
}

async function saveAgentSettings() {
    const backend = document.getElementById('backend-select').value;
    const model = document.getElementById('model-select').value;
    const base_url = backend === 'openai' 
        ? document.getElementById('openai-url').value 
        : null;
    
    const response = await fetch('/config/agent/backend', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({backend, model, base_url})
    });
    
    if (response.ok) {
        showNotification('Settings saved successfully');
    } else {
        showNotification('Failed to save settings', 'error');
    }
}

async function testAgentConnection() {
    showNotification('Testing connection...');
    
    const response = await fetch('/config/agent/test', {method: 'POST'});
    const data = await response.json();
    
    if (data.status === 'success') {
        showNotification('Connection successful!', 'success');
    } else {
        showNotification(`Connection failed: ${data.message}`, 'error');
    }
}

// Auto-update model list when backend changes
document.getElementById('backend-select').addEventListener('change', async (e) => {
    const response = await fetch('/config/agent/backend');
    const data = await response.json();
    const models = data.recommended_models[e.target.value];
    
    document.getElementById('model-select').innerHTML = 
        models.map(m => `<option value="${m}">${m}</option>`).join('');
    
    // Show/hide URL field
    const urlField = document.getElementById('openai-url-field');
    urlField.style.display = e.target.value === 'openai' ? 'block' : 'none';
});
```

### Step 4: Update SettingsMenu Component
Enhance handler functions in `frontend/src/lib/components/SettingsMenu.svelte`:

```javascript
// Add new state variables after existing ones
let lrmBackend = 'openai';
let lrmBaseUrl = '';
let modelsByBackend = {
  openai: [],
  huggingface: []
};

// Update onMount to load backend config
onMount(async () => {
  if (showLrm) {
    try {
      const cfg = await getLrmConfig();
      lrmOptions = cfg?.available_models?.openai || [];
      modelsByBackend = cfg?.available_models || {openai: [], huggingface: []};
      lrmBackend = cfg?.backend || 'openai';
      lrmBaseUrl = cfg?.base_url || '';
      lrmModel = cfg?.current_model || lrmModel;
      saveSettings({ lrmModel, lrmBackend, lrmBaseUrl });
    } catch {
      /* ignore */
    }
  }
  // ... rest of onMount
});

// Add new handler for backend changes
function handleBackendChange() {
  saveSettings({ lrmBackend });
  dispatch('save', { lrmBackend });
  // Update model list based on backend
  lrmOptions = modelsByBackend[lrmBackend] || [];
  // Set recommended model for HuggingFace
  if (lrmBackend === 'huggingface' && lrmOptions.includes('openai/gpt-oss-20b')) {
    lrmModel = 'openai/gpt-oss-20b';
    handleModelChange();
  }
  setLrmModel(lrmModel, lrmBackend, lrmBaseUrl).catch(() => {});
}

// Add handler for base URL changes
function handleBaseUrlChange() {
  saveSettings({ lrmBaseUrl });
  dispatch('save', { lrmBaseUrl });
  setLrmModel(lrmModel, lrmBackend, lrmBaseUrl).catch(() => {});
}

// Update existing handleModelChange to include backend info
function handleModelChange() {
  saveSettings({ lrmModel });
  dispatch('save', { lrmModel });
  setLrmModel(lrmModel, lrmBackend, lrmBaseUrl).catch(() => {});
}

// Update LLMSettings component props in template:
// <LLMSettings
//   {lrmModel}
//   {lrmBackend}
//   {lrmBaseUrl}
//   {lrmOptions}
//   availableBackends={['openai', 'huggingface']}
//   {modelsByBackend}
//   {handleModelChange}
//   {handleBackendChange}
//   {handleBaseUrlChange}
//   {handleTestModel}
//   {testReply}
// />
```

### Step 5: Update API Functions
Modify `frontend/src/lib/systems/api.js`:

```javascript
export async function getLrmConfig() {
  // Enhanced to return backend info
  return httpGet('/config/lrm', { cache: 'no-store' });
}

export async function setLrmModel(model, backend = null, baseUrl = null) {
  const payload = { model };
  if (backend) payload.backend = backend;
  if (baseUrl !== null) payload.base_url = baseUrl;
  return httpPost('/config/lrm', payload);
}

// testLrmModel stays the same
export async function testLrmModel(prompt) {
  return httpPost('/config/lrm/test', { prompt });
}
```

### Step 6: Test UI Changes
1. Start development server: `cd frontend && bun run dev`
2. Open settings menu and navigate to LLM settings tab
3. Verify new backend dropdown appears
4. Switch between OpenAI and HuggingFace backends
5. Verify model list updates based on backend selection
6. For OpenAI backend: verify API URL field appears
7. Enter custom URL and save
8. Test connection button
9. Verify settings persist after page reload

## Acceptance Criteria
- [ ] LLMSettings.svelte updated with backend selection
- [ ] Backend dropdown added (OpenAI / HuggingFace)
- [ ] OpenAI API URL field added (optional, shown only for OpenAI)
- [ ] Model dropdown filters by selected backend
- [ ] HuggingFace defaults to openai/gpt-oss-20b model
- [ ] Backend API endpoints updated to accept backend/base_url
- [ ] SettingsMenu.svelte updated with new handlers
- [ ] api.js updated to pass backend parameters
- [ ] Settings saved and persisted
- [ ] Test button works with new configuration
- [ ] URL field shown only when OpenAI backend selected
- [ ] Frontend linting passes (bun run lint)

## Testing Requirements

### Manual Testing
1. Open settings menu → LLM tab
2. Select OpenAI backend, enter custom URL, save
3. Test connection with valid/invalid URLs
4. Switch to HuggingFace backend
5. Verify recommended model is selected
6. Save and reload page - verify settings persist
7. Test with no URL (should use default OpenAI API)

### Integration Testing
1. Verify backend actually uses selected settings
2. Test chat with different backends
3. Verify error handling for invalid settings

## Dependencies
- Requires: `32e92203-migrate-llm-loader.md` (agent loader must exist)
- Requires: `656b2a7e-create-config-support.md` (config system helpful)
- Related: `96e5fdb9-update-config-routes.md` (shares backend endpoints)
- [ ] UI integrated into existing settings page
- [ ] Linting passes (frontend linter)

## Testing Requirements

### Manual Testing
1. Select OpenAI backend, enter URL, save
2. Test connection with valid/invalid URLs
3. Switch to HuggingFace backend
4. Verify recommended model selected
5. Save and reload page - verify settings persist
6. Test with no URL (OpenAI API default)

### Integration Testing
1. Verify backend actually uses selected settings
2. Test chat with different backends
3. Verify error handling for invalid settings

## Dependencies
- Requires: `32e92203-migrate-llm-loader.md` (agent loader must exist)
- Requires: `656b2a7e-create-config-support.md` (config system helpful)
- Related: `96e5fdb9-update-config-routes.md` (may share code)

## References
- **Existing Components**:
  - `frontend/src/lib/components/LLMSettings.svelte` - Current LRM UI (to be enhanced)
  - `frontend/src/lib/components/SettingsMenu.svelte` - Parent settings component
  - `frontend/src/lib/systems/api.js` - API interface functions
- **Backend**:
  - `backend/routes/config.py` - Config endpoints (to be enhanced)
  - `backend/llms/agent_loader.py` - Agent loader
- **Framework**: [Midori AI agents-packages](https://github.com/Midori-AI-OSS/agents-packages)

## Notes for Coder
- **Build on existing UI**: Enhance LLMSettings.svelte, don't create from scratch
- **Svelte patterns**: Use existing component patterns and styling from settings-shared.css
- **Backend dropdown**: "openai" for OpenAI/Ollama/LocalAI, "huggingface" for local inference
- **HuggingFace default**: openai/gpt-oss-20b is the recommended model with high reasoning
- **API URL**: Optional field, empty means use default OpenAI API
- **Test button**: Reuse existing testLrmModel functionality
- **Settings persistence**: Use existing saveSettings() system in SettingsMenu
- **Model filtering**: Update model list dynamically when backend changes
- **Error handling**: Provide clear error messages for connection failures
