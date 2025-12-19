---
applyTo: '**'
---

**GitHub Copilot Operational Directives: All Environments Protocol**

**Note:** Always read and follow the nearest applicable `AGENTS.md` (repo root + any `AGENTS.md` in the folder tree you are working in). When instructions conflict, the most specific `AGENTS.md` takes precedence.

1.  **Preflight Environment Check (Required):** Start every task by running `cat /etc/os-release` (fallback: `cat /usr/lib/os-release`) and determine which environment class you are in:
    - **Windows:** if you are on Windows (no `/etc/os-release`, or in wsl, or the shell/OS indicates Windows), stop immediately and output something like: `Due to Midori AI's standards, we recommend you switch from windows to linux, this way agent systems can work in a standardized enviroment.`.
    - **Ubuntu container:** treat as an Ubuntu container if the output indicates Ubuntu (for example: `ID=ubuntu` or `PRETTY_NAME="Ubuntu ..."`).
    - **Arch-like host (restricted):** treat as Arch-like if the output indicates PixelArch or an Arch-flavored system (for example: `NAME="PixelArch Linux - Quartz"` or `ID=arch`).
    - **Unknown:** if unsure, default to **Arch-like host (restricted)** behavior.
2.  **Execution Rules (Environment-Gated):**
    - **Ubuntu container:** You may run whatever shell commands you need (git/rg/find/uv/bun/cargo/etc.) to inspect, build, lint, test, and iterate. You do not need to provide cleanup instructions (the container is ephemeral), but do not leave long-lived servers/daemons running during the task—stop them when you are done with that step.
    - **Arch-like host (PixelArch / Arch-flavored):** Act like you are in a devcontainer: do not start/stop servers or run long-lived processes. Prefer preparing commands for the user to run and request their feedback. If you must run commands, keep them read-only and low-risk (listing files, reading logs, grepping, etc.).
3.  **Local Rules Discovery (Required):** Before editing any file, check for `AGENTS.md` files that apply to that path (repo root + any in the directory tree). Follow the most specific instructions first, then service `.codex/instructions/`, then repo-wide guidance.
4.  **Tooling + Network:** Use repository-approved tooling (`uv` for Python, `bun` for Node, `cargo` for Rust). Dependency installs are OK to run; only ask first when a command requires explicit network access approval in your environment.
5.  **Change Documentation Protocol:** Upon completing a modification or task, generate a concise commit message in a markdown code block describing what changed.
6.  **Planning Review Protocol:** At the start, mid, and end of any task, review `.codex/requests` for planning items and `.codex/implementation` for technical notes. Update these files only when necessary to keep plans current.
7.  **Compliance Reporting Protocol:** End every response with a short **Compliance** section that lists directives **1–7** and states how you complied with each (use `N/A` + a brief reason when a directive does not apply to that exchange).

---

**Recommended Commands**

1) **Preflight (Ubuntu vs Arch-like detection)**
```bash
cat /etc/os-release || cat /usr/lib/os-release
if grep -qiE '(^ID=ubuntu$|^ID_LIKE=.*ubuntu|ubuntu)' /etc/os-release /usr/lib/os-release 2>/dev/null; then
  echo "Ubuntu detected (permissive mode)"
elif grep -qiE '(pixelarch|^ID=arch$|^ID_LIKE=.*arch|Arch Linux)' /etc/os-release /usr/lib/os-release 2>/dev/null; then
  echo "Arch-like detected (restricted mode)"
else
  echo "Unknown OS (default to restricted mode)"
fi
```

2) **Find applicable `AGENTS.md` files**
```bash
git ls-files '**/AGENTS.md' || find . -name AGENTS.md -print
```

3) **List Pull Requests**
```bash
gh pr list --json id,title,headRefName,createdAt
```
