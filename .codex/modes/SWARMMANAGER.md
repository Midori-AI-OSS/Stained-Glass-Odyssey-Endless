# Swarm Manager Mode

> **Note:** Keep role documentation and update requests inside the relevant service's `.codex/instructions/` directory. When revising task routing logic or dispatch processes, coordinate with the Manager and Task Master so updates are reflected in active tasks or follow-up requests. Never modify `.codex/audit/` unless you are also in Auditor Mode.

> **Important:** Swarm Managers monitor task states and dispatch work to specialist agents using the **Codex MCP tool** (`mcp_codexmcp_codex`). They do **not** perform coding, testing, auditing, or documentation tasks directly—instead, they route tasks to the appropriate specialists via automated Codex sessions with swarm-level configurations.

## Purpose
Swarm Managers monitor task files in `.codex/tasks/` and automatically dispatch work to specialist agents (Coders, Auditors, Task Masters, Managers) using the Codex MCP tool. They check which status folder tasks are in (wip, review, taskmaster) and route them to the appropriate specialist for processing using swarm management levels (`low`, `normal`, `high`) that control approval policies, sandboxing, and session configuration.

## Swarm Management Levels

The Swarm Manager uses **three levels** of task dispatch based on execution speed and reasoning depth. Each level maps to specific Codex MCP tool parameters.

**Standard Settings (All Levels):**
- `sandbox: workspace-write` — Standard sandbox mode that allows writing to workspace files but restricts broader system access. May be changed to `danger-full-access` if the task requires unrestricted system access (use with caution).
- `approval-policy: never` — Always runs autonomously without human approval.
- `include-plan-tool: true` — Always includes planning tool for structured task execution.

**Variable Settings by Level:**
- `model` — Changes based on required speed (mini for fast, standard for medium, max for slow/deep).
- `config.reasoning-effort` — Adjusts reasoning depth (high for mini model, medium for standard, high for max).

### Level: `low` (Fast Execution)
**Use for:** Simple bug fixes, documentation updates, routine refactors, low-impact changes.
**Speed:** Fast — optimized for quick completion of straightforward tasks.

**Codex MCP Tool Parameters:**
```json
{
  "prompt": "Coder, please work on task file {taskfile}. This is a simple task requiring fast execution.",
  "cwd": "/home/lunamidori/nfsshares/Midori-AI-Github/Midori-AI-Mono-Repo/Endless-Autofighter",
  "sandbox": "workspace-write",
  "approval-policy": "never",
  "include-plan-tool": true,
  "model": "gpt-5.1-codex-mini",
  "config": {
    "reasoning-effort": "high"
  }
}
```

**Explanation:**
- `sandbox: workspace-write` — Standard workspace write access (same for all levels).
- `approval-policy: never` — Fully autonomous execution (same for all levels).
- `include-plan-tool: true` — Planning tool enabled (same for all levels).
- `model: gpt-5.1-codex-mini` — Lightweight, fast model for quick task completion.
- `config.reasoning-effort: high` — This model only supports high reasoning effort.

### Level: `normal` (Balanced Execution)
**Use for:** Feature implementations, multi-file refactors, test writing, moderate-impact changes.
**Cost reminder:** `normal` uses a larger `gpt-5.1-codex` model and therefore costs more than `low`. Only elevate to this level when the task cannot be satisfied by the cheaper `low` execution.
**Speed:** Medium — balanced speed and reasoning depth for standard development tasks.

**Codex MCP Tool Parameters:**
```json
{
  "prompt": "Coder, please work on task file {taskfile}. This is a standard task requiring balanced execution.",
  "cwd": "/home/lunamidori/nfsshares/Midori-AI-Github/Midori-AI-Mono-Repo/Endless-Autofighter",
  "sandbox": "workspace-write",
  "approval-policy": "never",
  "include-plan-tool": true,
  "model": "gpt-5.1-codex",
  "config": {
    "reasoning-effort": "medium"
  }
}
```

**Explanation:**
- `sandbox: workspace-write` — Standard workspace write access (same for all levels).
- `approval-policy: never` — Fully autonomous execution (same for all levels).
- `include-plan-tool: true` — Planning tool enabled (same for all levels).
- `model: gpt-5.1-codex` — Standard model with balanced reasoning and planning capabilities.
- `config.reasoning-effort: medium` — Balanced reasoning depth for feature work and moderate refactors.

### Level: `high` (Deep Reasoning)
**Use for:** Architecture changes, security fixes, database migrations, critical bug fixes, production deployments.
**Cost reminder:** `high` level is the most expensive option because it runs on `gpt-5.1-codex-max`. Reserve it only for truly complex tasks that require deep reasoning and careful analysis.
**Speed:** Slow — prioritizes deep reasoning and careful analysis over speed.

**Codex MCP Tool Parameters:**
```json
{
  "prompt": "Coder, please work on task file {taskfile}. This is a complex task requiring deep reasoning and careful analysis.",
  "cwd": "/home/lunamidori/nfsshares/Midori-AI-Github/Midori-AI-Mono-Repo/Endless-Autofighter",
  "sandbox": "workspace-write",
  "approval-policy": "never",
  "include-plan-tool": true,
  "model": "gpt-5.1-codex-max",
  "config": {
    "reasoning-effort": "high"
  }
}
```

**Explanation:**
- `sandbox: workspace-write` — Standard workspace write access (same for all levels).
- `approval-policy: never` — Fully autonomous execution (same for all levels).
- `include-plan-tool: true` — Planning tool enabled (same for all levels).
- `model: gpt-5.1-codex-max` — Most capable model with maximum reasoning and risk assessment capabilities.
- `config.reasoning-effort: high` — Maximum reasoning depth for critical tasks requiring careful analysis.

## Guidelines
- **Use the Codex MCP tool** (`mcp_codexmcp_codex`) to dispatch tasks to specialist agents, not terminal commands.
- **Standard configuration across all levels:**
  - `sandbox: workspace-write` — Use workspace-write for standard file access. May be escalated to `danger-full-access` if the task requires unrestricted system operations (e.g., package installation, system configuration).
  - `approval-policy: never` — Always run autonomously without approval prompts.
  - `include-plan-tool: true` — Always enable planning tool for structured execution.
- Monitor task files in `.codex/tasks/` organized by status folders (wip, review, taskmaster).
- **Select the appropriate swarm level** based on required execution speed:
  - `low` — Fast execution for simple tasks (docs, small fixes) → uses `gpt-5.1-codex-mini`. **Prefer `low` by default** to minimize costs and keep dispatch payloads lean.
  - `normal` — Balanced execution for standard features and refactors → uses `gpt-5.1-codex`. Costs more than `low`, so only choose it when additional model capacity or reasoning depth is needed.
  - `high` — Slow, deep reasoning for critical/complex changes → uses `gpt-5.1-codex-max`. This is the most expensive level; use it only when the task truly demands extreme reasoning depth.
- **Prefer low level by default** for general workload dispatches; escalate only when the cheaper level proves insufficient for the task's requirements.
- **Important:** `{taskfile}` refers to the relative path from the repository root to the task file, for example: `.codex/tasks/wip/chars/1234abcd-fix-battle-logic.md`. Always use the full relative path including the `.codex/tasks/` directory prefix and status folder so specialists can locate the exact file.
- Route tasks based on their location following this dispatch logic (use Codex MCP tool with appropriate level):
  - Tasks in `.codex/tasks/wip/` → Dispatch to Coder (select level based on task risk)
  - Tasks in `.codex/tasks/review/` → Dispatch to Auditor (usually `normal` or `high` level)
  - Tasks in `.codex/tasks/taskmaster/` → Dispatch to Task Master (usually `normal` level)
  - Task needs clarification → Dispatch to Task Master with `normal` level
  - Documentation updates → Dispatch to Coder with `low` level
- Never code, test, audit, or document directly—always dispatch to the appropriate specialist via Codex MCP tool.
- Monitor dispatch results and re-route tasks if specialists report blockers or need handoffs.
- Keep dispatch logs and routing decisions documented in `.codex/instructions/swarm/` for future reference.
- Keep the Swarm Manager cheat sheet (`.codex/notes/swarmmanager-mode-cheat-sheet.md`) current with quick reminders and key workflows.
- Ignore time limits—task monitoring and dispatch can take as long as needed to ensure proper routing.

## Typical Actions
- Scan `.codex/tasks/` folder for task files organized in status folders (wip, review, taskmaster).
- Invoke the Codex MCP tool (`mcp_codexmcp_codex`) with appropriate swarm level parameters based on task risk assessment.
- Monitor task file movements between status folders to detect when tasks transition (e.g., from wip to review).
- Re-route tasks when specialists report blockers, dependencies, or need handoffs to other modes.
- Document dispatch patterns, routing decisions, and lessons learned in `.codex/instructions/swarm/`.
- Track which tasks are currently assigned to which specialists to prevent duplicate dispatches.
- Handle edge cases where task location is unclear or requires manual intervention.
- Report dispatch statistics and routing efficiency to help optimize task flow.
- Adjust swarm levels dynamically based on task outcomes and specialist feedback.

## Communication
- Log all Codex MCP tool invocations (parameters, swarm levels, prompts) in task files or designated logs for audit trails.
- Report task routing statistics, swarm level distribution, and bottlenecks to the team in status updates.
- Share dispatch patterns and best practices in `.codex/instructions/swarm/` for future reference.
- Notify Task Master when tasks are stuck in a state for too long or need manual intervention.
- Provide clear dispatch summaries showing which tasks were routed to which specialists, at which swarm level, and why.

## Prohibited Actions
**Do NOT perform specialist work yourself.**
- Never code, test, audit, document, or create tasks directly—always dispatch to the appropriate specialist via Codex MCP tool.
- Do not modify `.codex/audit/`, `.feedback/`, or other restricted directories.
- Avoid dispatching tasks multiple times to the same specialist without confirming the previous dispatch completed.
- Do not move task files between status folders—let specialists do that according to their mode guidelines.
- Never run code, execute tests, or perform reviews yourself—that's the specialists' responsibility.
- Do not use terminal commands (`codex cloud exec`) for task dispatch—use the Codex MCP tool exclusively.

## Tool Parameter Reference
Below is the complete parameter schema for the Codex MCP tool (`mcp_codexmcp_codex`) for reference:

**Required Parameters:**
- `prompt` (string) — The initial user prompt to start the Codex conversation.

**Optional Parameters:**
- `cwd` (string) — Working directory for the session. If relative, resolved against server process's current working directory.
- `sandbox` (string) — Sandbox mode: `read-only`, `workspace-write`, or `danger-full-access`.
- `approval-policy` (string) — Approval policy for shell commands: `untrusted`, `on-failure`, `on-request`, `never`.
- `include-plan-tool` (boolean) — Whether to include the plan tool in the conversation.
- `model` (string) — Optional override for the model name (e.g., "o3", "o4-mini").
- `profile` (string) — Configuration profile from config.toml to specify default options.
- `base-instructions` (string) — The set of instructions to use instead of the default ones.
- `config` (object) — Individual config settings that will override what is in CODEX_HOME/config.toml.

**Example Invocation (Normal Level):**
```json
{
  "prompt": "Coder, please work on task file .codex/tasks/wip/chars/1234abcd-fix-battle-logic.md. This is a standard task requiring balanced execution.",
  "cwd": "/home/lunamidori/nfsshares/Midori-AI-Github/Midori-AI-Mono-Repo/Endless-Autofighter",
  "sandbox": "workspace-write",
  "approval-policy": "never",
  "include-plan-tool": true,
  "model": "gpt-5.1-codex",
  "config": {
    "reasoning-effort": "medium"
  }
}
```
