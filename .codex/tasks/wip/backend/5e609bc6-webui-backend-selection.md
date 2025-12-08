# Add Backend Selection to WebUI

## Task ID
`5e609bc6-webui-backend-selection`

## Priority
Medium

## Status
WIP

## Description
Add a user interface in the WebUI to allow users to select between OpenAI and HuggingFace backends, configure OpenAI API URL (optional), and select appropriate models based on the chosen backend.

## Context
After migrating to the Midori AI Agent Framework, the backend supports two agent backends:
1. **OpenAI agents** - For users with OpenAI API or compatible servers (Ollama, LocalAI, etc.)
2. **HuggingFace agents** - For local inference without external dependencies

Currently, backend selection is done via environment variables. Users need a UI to configure this.

## Rationale
- **User-Friendly**: GUI instead of editing config files or env vars
- **Flexibility**: Easy switching between local and remote backends
- **Discoverability**: Users can see what options are available
- **Validation**: UI can validate settings before saving

## Objectives
1. Add backend selection dropdown (OpenAI / HuggingFace)
2. Add OpenAI API URL input field (optional, for custom servers)
3. Add model selection based on backend
4. Save settings to backend config
5. Show current backend status
6. Use recommended model for HuggingFace (openai/gpt-oss-20b with high reasoning)

## Implementation Steps

### Step 1: Design UI Layout
Add new settings section for agent backend:
- Dropdown: Backend selection (OpenAI / HuggingFace)
- Text input: OpenAI API URL (shown only when OpenAI selected)
- Dropdown: Model selection (populated based on backend)
- Button: Test connection
- Status indicator: Current backend status

### Step 2: Create Backend API Endpoints
Add new endpoints in `backend/routes/config.py`:

```python
@bp.get("/agent/backend")
async def get_agent_backend():
    """Get current agent backend configuration."""
    from llms.agent_loader import get_agent_config
    
    config = get_agent_config()
    
    payload = {
        "backend": config.backend if config else "openai",
        "model": config.model if config else "gpt-oss:20b",
        "base_url": config.base_url if config else None,
        "available_backends": ["openai", "huggingface"],
        "recommended_models": {
            "openai": ["gpt-oss:20b", "gpt-4", "gpt-3.5-turbo", "llama3:8b"],
            "huggingface": ["openai/gpt-oss-20b"],  # Recommended with high reasoning
        },
    }
    return jsonify(payload)


@bp.post("/agent/backend")
async def set_agent_backend():
    """Set agent backend configuration."""
    data = await request.get_json()
    backend = data.get("backend", "openai")
    model = data.get("model")
    base_url = data.get("base_url")
    
    if backend not in ["openai", "huggingface"]:
        return jsonify({"error": "Invalid backend"}), 400
    
    # Save to config or options
    set_option("agent_backend", backend)
    if model:
        set_option("agent_model", model)
    if base_url:
        set_option("agent_base_url", base_url)
    
    return jsonify({"backend": backend, "model": model, "base_url": base_url})


@bp.post("/agent/test")
async def test_agent_connection():
    """Test agent connection with current settings."""
    from llms.agent_loader import load_agent, validate_agent
    
    try:
        agent = await load_agent()
        is_valid = await validate_agent(agent)
        
        if is_valid:
            return jsonify({"status": "success", "message": "Connection successful"})
        else:
            return jsonify({"status": "error", "message": "Validation failed"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

### Step 3: Create Frontend Component
Create settings UI component (location depends on frontend framework):

```javascript
// Example structure (adapt to your frontend framework)
async function loadAgentSettings() {
    const response = await fetch('/config/agent/backend');
    const data = await response.json();
    
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

### Step 4: Add UI Elements
Add HTML structure (adapt to your frontend):

```html
<div class="agent-settings">
    <h3>Agent Backend Settings</h3>
    
    <div class="form-group">
        <label for="backend-select">Backend:</label>
        <select id="backend-select">
            <option value="openai">OpenAI (API / Ollama / LocalAI)</option>
            <option value="huggingface">HuggingFace (Local Inference)</option>
        </select>
        <span class="help-text">
            OpenAI for remote servers, HuggingFace for local models
        </span>
    </div>
    
    <div class="form-group" id="openai-url-field">
        <label for="openai-url">OpenAI API URL (optional):</label>
        <input type="text" id="openai-url" placeholder="http://localhost:11434/v1">
        <span class="help-text">
            Leave empty for OpenAI API, or enter custom URL (Ollama, LocalAI, etc.)
        </span>
    </div>
    
    <div class="form-group">
        <label for="model-select">Model:</label>
        <select id="model-select">
            <!-- Populated dynamically based on backend -->
        </select>
        <span class="help-text">
            HuggingFace: openai/gpt-oss-20b recommended (high reasoning)
        </span>
    </div>
    
    <div class="form-actions">
        <button onclick="saveAgentSettings()">Save Settings</button>
        <button onclick="testAgentConnection()">Test Connection</button>
    </div>
    
    <div id="agent-status" class="status-indicator">
        <!-- Status messages appear here -->
    </div>
</div>
```

### Step 5: Add Styling
Add CSS for the new UI elements:

```css
.agent-settings {
    padding: 20px;
    background: var(--panel-bg);
    border-radius: 8px;
}

.form-group {
    margin-bottom: 15px;
}

.form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.form-group select,
.form-group input {
    width: 100%;
    padding: 8px;
    border-radius: 4px;
    border: 1px solid var(--border-color);
}

.help-text {
    display: block;
    font-size: 0.9em;
    color: var(--text-secondary);
    margin-top: 4px;
}

.form-actions {
    margin-top: 20px;
    display: flex;
    gap: 10px;
}

.status-indicator {
    margin-top: 15px;
    padding: 10px;
    border-radius: 4px;
}

.status-indicator.success {
    background: var(--success-bg);
    color: var(--success-text);
}

.status-indicator.error {
    background: var(--error-bg);
    color: var(--error-text);
}
```

### Step 6: Test UI
1. Load settings page
2. Verify backend dropdown shows options
3. Switch between backends and verify model list updates
4. Enter OpenAI URL and verify it's saved
5. Test connection button works
6. Verify settings persist after page reload

## Acceptance Criteria
- [ ] Backend selection dropdown added (OpenAI / HuggingFace)
- [ ] OpenAI API URL field added (optional)
- [ ] Model selection dropdown populated based on backend
- [ ] HuggingFace recommends openai/gpt-oss-20b model
- [ ] Settings saved to backend config/options
- [ ] Test connection button validates settings
- [ ] UI shows current backend status
- [ ] URL field shown only when OpenAI backend selected
- [ ] Settings persist across page reloads
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
- Backend: `backend/routes/config.py`
- Agent loader: `backend/llms/agent_loader.py`
- Frontend settings: (location varies by framework)
- Agent framework: [Midori AI agents-packages](https://github.com/Midori-AI-OSS/agents-packages)

## Notes for Coder
- Adapt code examples to match your frontend framework (Svelte, React, Vue, etc.)
- Use existing settings page UI patterns
- For HuggingFace, emphasize openai/gpt-oss-20b as recommended model
- OpenAI URL is optional - empty means use default OpenAI API
- Test connection should provide clear error messages
- Consider adding a loading spinner during test
- Save API keys separately (don't expose in UI)
- Consider adding tooltips explaining each option
