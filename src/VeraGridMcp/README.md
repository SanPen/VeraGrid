# VeraGridMcp

## What this is

`VeraGridMcp` is a Model Context Protocol (MCP) server for VeraGrid.
It is a plain stdio server and does **not** include any chat/provider logic.

It exposes two tools:
- `veragrid_status`
- `veragrid_stack_status`

## 1) Install

Use the repo editables (recommended for local use):

```bash
cd /home/santi/Git/eRoots/VeraGrid
python -m pip install -e src/VeraGridEngine
python -m pip install -e src/VeraGridMcp
```

Or install from PyPI:

```bash
python -m pip install VeraGridMcp
```

## 2) Start the MCP server

```bash
veragridmcp
```

This runs the server.

`veragridmcp serve` does the same thing.

## 3) Register in clients (important)

This package adds a CLI register helper:

```bash
veragridmcp register --client codex
veragridmcp register --client claude
veragridmcp register --client cursor --cursor-scope global
veragridmcp register --client all
```

After register:

```bash
veragridmcp --help
```

If registration was for:
- `codex` → confirm `~/.codex/config.toml`
- `claude` → confirm `claude_desktop_config.json`
- `cursor`/`cursor-global` → confirm `~/.cursor/mcp.json`
- `cursor-project` → confirm `./.cursor/mcp.json`
- `claude-code` → confirm `./.mcp.json`

Common options:
- `--client` (`codex`, `claude`, `cursor`, `claude-code`, `cursor-project`, `cursor-global`)
- `--cursor-scope global|project` (used only when `--client cursor`)
- `--server-name` (default: `veragrid`)
- `--python` (interpreter used by MCP client)
- `--cwd` (working directory, defaults to current dir)
- `--dry-run` (preview only, does not write files)

Output paths:
- Codex → `~/.codex/config.toml`
- Claude Desktop → `claude_desktop_config.json`
- Cursor global → `~/.cursor/mcp.json`
- Cursor project → `./.cursor/mcp.json`
- Claude Code → `./.mcp.json`

## 4) Quick smoke test

Ask any connected client:
`Are you connected to the VeraGrid MCP server?`

Then call:
`veragrid_stack_status`

Expected output includes:
- `VeraGridMcp: <version>`
- `VeraGridEngine: <version>`

## 5) How to check Codex/Claude/Cursor is using VeraGridMcp

1) Confirm registration was written:

- Codex:
  - `~/.codex/config.toml` must contain `[mcp_servers.<your_server_name>]`
  - `command` must point to a Python executable from this environment.
  - `args` must point to `["-m", "VeraGridMcp.mcp_server"]`.

- Claude Desktop:
  - Open `claude_desktop_config.json`.
  - Confirm `mcpServers.<your_server_name>` exists and has the same command/args.

- Cursor:
  - Global config: `~/.cursor/mcp.json`
  - Project config: `./.cursor/mcp.json`
  - Confirm `mcpServers.<your_server_name>` exists.

- Claude Code:
  - Open `./.mcp.json`
  - Confirm `mcpServers.<your_server_name>` exists.

2) Restart the client app after editing config.

3) In each client chat, run:
   - `Are you connected to the VeraGrid MCP server?`
   - If the answer tool exists and returns text, the server is attached.

From Codex:
```bash
codex mcp list
```
Then in Codex chat, run `/mcp` to see active MCP servers.

4) Run:
   - `veragrid_stack_status`
   - Check it returns `VeraGridMcp:` and `VeraGridEngine:` lines.

5) If the server does not appear:
   - verify the `--python` path in registration matches your active CLI environment,
   - verify `veragridmcp` runs from that environment.

## 6) OpenAI/ChatGPT (publish path)

For ChatGPT custom MCP apps, this is **workspace registration**, not PyPI publishing.

You still must:
1. Enable Developer mode.
2. Register the MCP app.
3. Test in draft.
4. Publish in workspace.

ChatGPT currently expects remote MCP connections, so private/local servers usually
need a secure tunnel if not publicly reachable.

## 7) Remove this package from MCP client config

Open your client config file and delete the `veragrid` block (or run your own config overwrite manually).

## 8) Troubleshooting (fast)

- `veragridmcp` command not found: install the package in the active environment.
- Bad command path: use `--python` and `--cwd` to point to the exact Python and repo root.
- Missing version text from `veragrid_stack_status`: that means `VeraGridEngine` is not importable in the client environment.

## 9) Regenerate knowledge assets (optional)

```bash
cd /home/santi/Git/eRoots/VeraGrid
PYTHONPATH=src python -m VeraGridMcp.generate_knowledge_assets
```
