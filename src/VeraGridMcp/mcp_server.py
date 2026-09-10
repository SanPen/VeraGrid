# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from VeraGridMcp.__version__ import __VeraGridMcp_VERSION__

from mcp.server.mcpserver import MCPServer


def veragrid_status() -> str:
    """
    Return a generic availability message for this MCP server.

    :returns: Server availability statement.
    """
    return "VeraGrid MCP server is connected."


def veragrid_stack_status() -> str:
    """
    Return the VeraGridEngine version available to this MCP server.

    :returns: Newline separated stack status text.
    """
    output_lines: list[str] = list()
    output_lines.append("VeraGridMcp: " + __VeraGridMcp_VERSION__)

    try:
        from VeraGridEngine.__version__ import __VeraGridEngine_VERSION__

        output_lines.append("VeraGridEngine: " + __VeraGridEngine_VERSION__)
    except ImportError as exc:
        output_lines.append("VeraGridEngine: unavailable (" + str(exc) + ")")

    return "\n".join(output_lines)


def _register_tools(server: Any) -> None:
    """
    Register all MCP tools on the provided MCP server instance.

    :param server: MCP server object.
    :returns: Nothing.
    """
    _ = server.tool(name="veragrid_status", description="Report whether the VeraGrid MCP server is reachable.")(veragrid_status)
    _ = server.tool(
        name="veragrid_stack_status",
        description="Report the VeraGridMcp and VeraGridEngine versions available to this MCP server.",
    )(veragrid_stack_status)


def build_server() -> MCPServer:
    """
    Build and configure the MCP server.

    :returns: Configured MCP server instance.
    """
    mcp_server: MCPServer = MCPServer(
        "VeraGridMcp",
        version=__VeraGridMcp_VERSION__,
    )
    _register_tools(server=mcp_server)
    return mcp_server


def run_server() -> int:
    """
    Run the MCP server on stdio.

    :returns: Exit code.
    """
    server: MCPServer = build_server()
    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_server())
