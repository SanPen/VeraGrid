# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from VeraGridMcp.mcp_server import run_server
from VeraGridMcp.__version__ import __VeraGridMcp_VERSION__


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Build and parse the CLI arguments.

    :param argv: Optional argv list. Defaults to ``sys.argv[1:]``.
    :returns: Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(description="VeraGrid MCP utilities.")
    subparsers = parser.add_subparsers(dest="command", required=False)
    register_parser = subparsers.add_parser("register", help="Register VeraGrid MCP in clients.")
    register_parser.add_argument(
        "--client",
        action="append",
        choices=(
            "all",
            "codex",
            "claude",
            "cursor",
            "cursor-project",
            "cursor-global",
            "claude-code",
        ),
        required=True,
        help="Target client.",
    )
    register_parser.add_argument(
        "--server-name",
        type=str,
        default="veragrid",
        help="MCP server name used inside client config.",
    )
    register_parser.add_argument(
        "--python",
        type=str,
        default=sys.executable,
        help="Python executable used to spawn VeraGridMcp.",
    )
    register_parser.add_argument(
        "--cwd",
        type=str,
        default=str(Path.cwd()),
        help="Working directory for the MCP server process.",
    )
    register_parser.add_argument(
        "--cursor-scope",
        type=str,
        choices=("global", "project"),
        default="global",
        help="Cursor scope when registering.",
    )
    register_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render payloads only; do not write files.",
    )
    serve_parser = subparsers.add_parser("serve", help="Run the VeraGrid MCP server.")
    serve_parser.set_defaults(run_subcommand="serve")
    normalized_argv: list[str] = list()
    if argv is None:
        normalized_argv = list(sys.argv[1:])
    else:
        normalized_argv = list(argv)

    if len(normalized_argv) >= 2:
        if normalized_argv[0] == "-m" and normalized_argv[1] == "VeraGridMcp.cli":
            normalized_argv = normalized_argv[2:]
        else:
            pass

    if len(normalized_argv) == 0:
        arguments: argparse.Namespace = parser.parse_args([])
    else:
        arguments = parser.parse_args(normalized_argv)

    if arguments.command is None:
        arguments.command = "serve"
    else:
        pass
    return arguments


def build_banner() -> str:
    """
    Build the CLI startup banner.

    :returns: Banner text.
    """
    lines: list[str] = [
        r"""VeraGrid MCP""" + " (" + __VeraGridMcp_VERSION__ + " Alpha)",
    ]
    return "\n".join(lines)


def print_banner() -> None:
    """
    Print startup banner to stdout.

    :returns: Nothing.
    """
    print(build_banner())


def _build_entry(command: str, cwd: str) -> dict[str, Any]:
    """
    Build a stdio MCP server entry for config files.

    :param command: Python interpreter command.
    :param cwd: Working directory.
    :returns: MCP server entry dictionary.
    """
    entry: dict[str, Any] = dict()
    entry["command"] = command
    entry["args"] = ["-m", "VeraGridMcp.mcp_server"]
    entry["cwd"] = cwd
    entry["env"] = dict()
    source_root: Path = Path(cwd) / "src"
    if source_root.exists() is True:
        entry["env"] = {"PYTHONPATH": str(source_root)}
    else:
        entry["env"] = dict()
    entry["type"] = "stdio"
    return entry


def _normalize_clients(raw_clients: list[str]) -> list[str]:
    """
    Resolve ``all`` into all supported targets.

    :param raw_clients: Raw client names from CLI.
    :returns: Normalized list.
    """
    clients: list[str] = list()
    if "all" in raw_clients:
        return list(("codex", "claude", "cursor", "claude-code"))
    for client in raw_clients:
        if client not in clients:
            clients.append(client)
        else:
            pass
    return clients


def _write_toml_section(
    path: Path,
    server_name: str,
    entry: dict[str, Any],
    dry_run: bool,
) -> int:
    """
    Register/replace one ``[mcp_servers.<name>]`` section in Codex TOML config.

    :param path: Destination config file.
    :param server_name: MCP server name.
    :param entry: MCP entry payload.
    :param dry_run: Print-only mode.
    :returns: Exit code.
    """
    section_name: str = "mcp_servers." + server_name
    command: str = "command = " + json.dumps(entry["command"], ensure_ascii=False)
    args_payload: str = "args = " + json.dumps(entry["args"], ensure_ascii=False)
    cwd_payload: str = "cwd = " + json.dumps(entry["cwd"], ensure_ascii=False)
    environment: Any = entry.get("env", dict())
    if environment is None:
        toml_env_payload: str = "env = {}"
    elif len(environment) == 0:
        toml_env_payload = "env = {}"
    elif len(environment) == 1:
        first_key: str = ""
        first_value: Any = ""
        for first_key, first_value in environment.items():
            break
        toml_value: str = json.dumps(first_value, ensure_ascii=False)
        toml_env_payload = "env = {" + first_key + " = " + toml_value + "}"
    else:
        toml_env_lines: list[str] = list()
        for key, value in environment.items():
            toml_env_lines.append(key + " = " + json.dumps(value, ensure_ascii=False))
        toml_env_payload = "env = { " + ", ".join(toml_env_lines) + " }"
    section_lines: list[str] = list()
    section_lines.append("[" + section_name + "]")
    section_lines.append(command)
    type_payload: str = "type = \"stdio\""
    section_lines.append(type_payload)
    section_lines.append(args_payload)
    section_lines.append(cwd_payload)
    section_lines.append("enabled = true")
    section_lines.append(toml_env_payload)
    section_text: str = "\n".join(section_lines)

    if path.exists() is True:
        current_content: str = path.read_text(encoding="utf-8")
    else:
        current_content = ""

    section_header: str = "[" + section_name + "]"
    lines: list[str] = current_content.splitlines()
    start_index: int = -1
    end_index: int = len(lines)
    target_lines: list[str] = section_text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == section_header:
            start_index = index
        else:
            pass

    if start_index < 0:
        if len(lines) == 0:
            new_content: str = section_text + "\n"
        else:
            if len(lines[-1].strip()) == 0:
                new_content = "\n".join(lines) + section_text + "\n"
            else:
                new_content = "\n".join(lines) + "\n\n" + section_text + "\n"
    else:
        for index in range(start_index + 1, len(lines)):
            if lines[index].startswith("[") and lines[index].endswith("]") is True:
                end_index = index
                break
            else:
                pass
        merged: list[str] = list()
        merged.extend(lines[0:start_index])
        merged.extend(target_lines)
        merged.extend(lines[end_index:])
        new_content = "\n".join(merged) + "\n"

    print("[codex] " + str(path) + " -> " + ("(dry-run)" if dry_run else "write"))
    print(section_text)
    if dry_run is False:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_content, encoding="utf-8")
    return 0


def _write_json_section(
    path: Path,
    server_name: str,
    entry: dict[str, Any],
    dry_run: bool,
) -> int:
    """
    Register/replace one server entry in a JSON ``mcpServers`` object.

    :param path: Destination config file.
    :param server_name: MCP server name.
    :param entry: MCP entry payload.
    :param dry_run: Print-only mode.
    :returns: Exit code.
    """
    if path.exists() is True:
        existing_raw: str = path.read_text(encoding="utf-8")
        if len(existing_raw.strip()) > 0:
            try:
                data: dict[str, Any] = json.loads(existing_raw)
            except json.JSONDecodeError as exc:
                print("[error] failed to parse JSON config: " + str(exc))
                return 2
        else:
            data = dict()
    else:
        data = dict()

    if "type" not in entry:
        entry["type"] = "stdio"
    else:
        pass

    if "mcpServers" in data:
        mcp_servers: Any = data["mcpServers"]
        if isinstance(mcp_servers, dict):
            current_servers: dict[str, Any] = mcp_servers
            current_servers[server_name] = entry
            data["mcpServers"] = current_servers
        else:
            mcp_servers = dict()
            mcp_servers[server_name] = entry
            data["mcpServers"] = mcp_servers
    else:
        mcp_servers = dict()
        mcp_servers[server_name] = entry
        data["mcpServers"] = mcp_servers

    if "type" not in entry:
        entry["type"] = "stdio"
    else:
        pass

    payload: str = json.dumps(data, indent=2)
    print("[json] " + str(path) + " -> " + ("(dry-run)" if dry_run else "write"))
    print(payload)
    if dry_run is False:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
    return 0


def register_codex(
    server_name: str,
    command: str,
    cwd: str,
    dry_run: bool,
) -> int:
    """
    Register VeraGrid MCP in Codex configuration.

    :param server_name: MCP server name.
    :param command: Python executable.
    :param cwd: Working directory.
    :param dry_run: Print-only mode.
    :returns: Exit code.
    """
    config_paths: tuple[Path, ...] = (
        Path.home() / ".codex" / "config.toml",
    )
    path: Path = config_paths[0]
    entry: dict[str, Any] = _build_entry(command=command, cwd=cwd)
    return _write_toml_section(path=path, server_name=server_name, entry=entry, dry_run=dry_run)


def _first_existing_path(candidates: tuple[Path, ...], fallback: Path) -> Path:
    """
    Pick the first existing path from a list; otherwise return fallback.

    :param candidates: Candidate paths.
    :param fallback: Fallback path.
    :returns: Selected path.
    """
    selected: Path = fallback
    has_selected: bool = False
    for candidate in candidates:
        if candidate.parent.exists() is True:
            if has_selected is False:
                selected = candidate
                has_selected = True
            else:
                pass
        else:
            pass
    return selected


def register_claude_desktop(server_name: str, command: str, cwd: str, dry_run: bool) -> int:
    """
    Register VeraGrid MCP in Claude Desktop config.

    :param server_name: MCP server name.
    :param command: Python executable.
    :param cwd: Working directory.
    :param dry_run: Print-only mode.
    :returns: Exit code.
    """
    candidates: tuple[Path, ...]
    if sys.platform == "darwin":
        candidates = (
            Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        )
    elif os.name == "nt":
        app_data: str = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        candidates = (Path(app_data) / "Claude" / "claude_desktop_config.json",)
    else:
        candidates = (Path.home() / ".config" / "Claude" / "claude_desktop_config.json",)
    path: Path = _first_existing_path(candidates, candidates[0])
    entry: dict[str, Any] = _build_entry(command=command, cwd=cwd)
    entry["type"] = "stdio"
    return _write_json_section(path=path, server_name=server_name, entry=entry, dry_run=dry_run)


def register_cursor_global(
    server_name: str,
    command: str,
    cwd: str,
    dry_run: bool,
) -> int:
    """
    Register VeraGrid MCP in Cursor global config (~/.cursor/mcp.json).

    :param server_name: MCP server name.
    :param command: Python executable.
    :param cwd: Working directory.
    :param dry_run: Print-only mode.
    :returns: Exit code.
    """
    path: Path = Path.home() / ".cursor" / "mcp.json"
    entry: dict[str, Any] = _build_entry(command=command, cwd=cwd)
    return _write_json_section(path=path, server_name=server_name, entry=entry, dry_run=dry_run)


def register_cursor_project(
    server_name: str,
    command: str,
    cwd: str,
    dry_run: bool,
) -> int:
    """
    Register VeraGrid MCP in project Cursor config (./.cursor/mcp.json).

    :param server_name: MCP server name.
    :param command: Python executable.
    :param cwd: Working directory.
    :param dry_run: Print-only mode.
    :returns: Exit code.
    """
    path: Path = Path.cwd() / ".cursor" / "mcp.json"
    entry: dict[str, Any] = _build_entry(command=command, cwd=cwd)
    return _write_json_section(path=path, server_name=server_name, entry=entry, dry_run=dry_run)


def register_claude_code(server_name: str, command: str, cwd: str, dry_run: bool) -> int:
    """
    Register VeraGrid MCP in Claude Code local `.mcp.json`.

    :param server_name: MCP server name.
    :param command: Python executable.
    :param cwd: Working directory.
    :param dry_run: Print-only mode.
    :returns: Exit code.
    """
    path: Path = Path.cwd() / ".mcp.json"
    entry: dict[str, Any] = _build_entry(command=command, cwd=cwd)
    entry["type"] = "stdio"
    return _write_json_section(path=path, server_name=server_name, entry=entry, dry_run=dry_run)


def _register_clients(clients: list[str], args: argparse.Namespace) -> int:
    """
    Dispatch register operations across selected targets.

    :param clients: List of normalized targets.
    :param args: Parsed args.
    :returns: First non-zero exit code, or 0.
    """
    normalized_clients: list[str] = _normalize_clients(raw_clients=clients)
    python_executable: str = args.python
    cwd: str = args.cwd
    server_name: str = args.server_name
    dry_run: bool = args.dry_run

    if len(normalized_clients) > 0:
        for client in normalized_clients:
            if client == "codex":
                result: int = register_codex(
                    server_name=server_name,
                    command=python_executable,
                    cwd=cwd,
                    dry_run=dry_run,
                )
            elif client == "claude-code":
                result = register_claude_code(
                    server_name=server_name,
                    command=python_executable,
                    cwd=cwd,
                    dry_run=dry_run,
                )
            elif client == "cursor":
                if args.cursor_scope == "project":
                    result = register_cursor_project(
                        server_name=server_name,
                        command=python_executable,
                        cwd=cwd,
                        dry_run=dry_run,
                    )
                else:
                    result = register_cursor_global(
                        server_name=server_name,
                        command=python_executable,
                        cwd=cwd,
                        dry_run=dry_run,
                    )
            else:
                if client == "cursor-global":
                    result = register_cursor_global(
                        server_name=server_name,
                        command=python_executable,
                        cwd=cwd,
                        dry_run=dry_run,
                    )
                else:
                    if client == "cursor-project":
                        result = register_cursor_project(
                            server_name=server_name,
                            command=python_executable,
                            cwd=cwd,
                            dry_run=dry_run,
                        )
                    elif client == "claude":
                        result = register_claude_desktop(
                            server_name=server_name,
                            command=python_executable,
                            cwd=cwd,
                            dry_run=dry_run,
                        )
                    else:
                        if client == "all":
                            result = 0
                        else:
                            print("Unsupported client: " + client)
                            return 2
            if result != 0:
                return result
    else:
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    """
    Entry point for the package CLI.

    Usage examples:
      veragridmcp register --client codex --client cursor
      veragridmcp register --client all
      veragridmcp serve

    :param argv: Optional explicit argument list.
    :returns: Process exit code.
    """
    arguments: argparse.Namespace = parse_args(argv=argv)
    if arguments.command == "serve":
        return run_server()
    else:
        print_banner()
        if arguments.command == "register":
            return _register_clients(clients=arguments.client, args=arguments)
        else:
            print("Unsupported command: " + arguments.command)
            return 2


if __name__ == "__main__":
    sys.exit(main())
