# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from typing import Any, Callable, Optional

from VeraGrid.AI.mcp_protocol import (
    chat_message_to_json,
    llm_response_from_json,
    model_list_result_from_json,
    provider_config_to_json,
    read_mcp_message,
    tool_spec_to_json,
    write_mcp_message,
)
from VeraGrid.AI.types_and_tools import (
    ChatMessage,
    LLMResponse,
    ModelListResult,
    ProviderConfig,
    ProviderErrorCode,
    ToolSpec,
)


class VeraGridMcpClient:
    """
    Small stdio MCP client for the VeraGrid AI server process.
    """

    __slots__ = (
        "_process",
        "_request_id",
        "_lock",
        "_initialized",
        "_config_file_path",
    )

    def __init__(self, config_file_path: Optional[str] = None) -> None:
        """
        Build the client without starting the process.

        :param config_file_path: MCP server registration JSON path.
        """
        self._process: Optional[subprocess.Popen[bytes]] = None
        self._request_id: int = 0
        self._lock: threading.Lock = threading.Lock()
        self._initialized: bool = False
        self._config_file_path: Optional[str] = config_file_path

    def set_config_file_path(self, config_file_path: str) -> None:
        """
        Set the MCP server registration JSON path.

        :param config_file_path: MCP server registration JSON path.
        :returns: Nothing.
        """
        self._config_file_path = config_file_path

    def write_registration_config(self) -> None:
        """
        Write VeraGrid's MCP server registration JSON.

        :returns: Nothing.
        """
        config_file_path: Optional[str] = self._config_file_path

        if config_file_path is None:
            pass
        else:
            config_directory: str = os.path.dirname(config_file_path)
            if len(config_directory) > 0:
                os.makedirs(config_directory, exist_ok=True)
            else:
                pass

            server_obj: dict[str, Any] = dict()
            servers_obj: dict[str, Any] = dict()
            payload: dict[str, Any] = dict()
            server_obj["command"] = sys.executable
            server_obj["args"] = ["-u", "-m", "VeraGrid.AI.mcp_server"]
            server_obj["cwd"] = self.build_server_working_directory()
            server_obj["transport"] = "stdio"
            servers_obj["veragrid-ai"] = server_obj
            payload["mcpServers"] = servers_obj

            with open(config_file_path, "w", encoding="utf-8") as file_pointer:
                file_pointer.write(json.dumps(payload, indent=4))

    def start_server(self) -> bool:
        """
        Start the MCP server process if it is not already running.

        :returns: True when a process is available.
        """
        if self._process is None:
            try:
                self.write_registration_config()
                self._process = subprocess.Popen(
                    [sys.executable, "-u", "-m", "VeraGrid.AI.mcp_server"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    cwd=self.build_server_working_directory(),
                )
                self._initialized = False
            except OSError:
                self._process = None
                self._initialized = False
                return False
        else:
            if self._process.poll() is None:
                pass
            else:
                self._process = None
                self._initialized = False
                return self.start_server()

        return self._process is not None

    def build_server_working_directory(self) -> str:
        """
        Return the directory from which ``python -m VeraGrid.AI.mcp_server`` can import VeraGrid.

        :returns: Server working directory.
        """
        ai_directory: str = os.path.abspath(os.path.dirname(__file__))
        veragrid_directory: str = os.path.abspath(os.path.join(ai_directory, ".."))
        source_directory: str = os.path.abspath(os.path.join(veragrid_directory, ".."))
        return source_directory

    def stop_server(self) -> None:
        """
        Stop the MCP server process.

        :returns: Nothing.
        """
        process: Optional[subprocess.Popen[bytes]] = self._process

        if process is None:
            pass
        else:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1.0)
            else:
                pass

        self._process = None
        self._initialized = False

    def ensure_initialized(self) -> bool:
        """
        Ensure the MCP initialize handshake has completed.

        :returns: True when initialized.
        """
        if self._initialized:
            return True
        else:
            pass

        result: Optional[dict[str, Any]] = self.call_method("initialize", dict(), initialize_call=True)
        if result is None:
            return False
        else:
            self._initialized = True
            return True

    def call_method(
        self,
        method: str,
        params: dict[str, Any],
        initialize_call: bool = False,
    ) -> Optional[dict[str, Any]]:
        """
        Call one JSON-RPC method on the MCP server.

        :param method: Method name.
        :param params: Method parameters.
        :param initialize_call: Whether this is the initialize handshake.
        :returns: Result dictionary or None on failure.
        """
        with self._lock:
            if self.start_server():
                pass
            else:
                return None

            process: Optional[subprocess.Popen[bytes]] = self._process
            if process is None:
                return None
            else:
                pass

            if process.stdin is None or process.stdout is None:
                self.stop_server()
                return None
            else:
                pass

            if (not initialize_call) and (not self._initialized):
                init_result: Optional[dict[str, Any]] = self._call_method_unlocked(
                    method="initialize",
                    params=dict(),
                )
                if init_result is None:
                    return None
                else:
                    self._initialized = True
            else:
                pass

            return self._call_method_unlocked(method=method, params=params)

    def _call_method_unlocked(self, method: str, params: dict[str, Any]) -> Optional[dict[str, Any]]:
        """
        Call one method while the client lock is already held.

        :param method: Method name.
        :param params: Method parameters.
        :returns: Result dictionary or None on failure.
        """
        process: Optional[subprocess.Popen[bytes]] = self._process

        if process is None:
            return None
        else:
            pass

        if process.stdin is None or process.stdout is None:
            return None
        else:
            pass

        self._request_id += 1
        request: dict[str, Any] = dict()
        request["jsonrpc"] = "2.0"
        request["id"] = self._request_id
        request["method"] = method
        request["params"] = params

        try:
            write_mcp_message(process.stdin, request)
            response: Optional[dict[str, Any]] = read_mcp_message(process.stdout)
        except OSError:
            self.stop_server()
            return None
        except BrokenPipeError:
            self.stop_server()
            return None

        if response is None:
            self.stop_server()
            return None
        else:
            error_obj: object = response.get("error", None)
            if isinstance(error_obj, dict):
                return None
            else:
                result_obj: object = response.get("result", None)
                if isinstance(result_obj, dict):
                    return result_obj
                else:
                    return dict()

    def complete(
        self,
        config: ProviderConfig,
        system_prompt: str,
        messages: list[ChatMessage],
        tool_specs: list[ToolSpec],
    ) -> LLMResponse:
        """
        Run one LLM completion through the MCP server.

        :param config: Provider configuration.
        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tool schemas.
        :returns: LLM response.
        """
        message_payloads: list[dict[str, Any]] = list()
        tool_payloads: list[dict[str, Any]] = list()
        index: int = 0

        while index < len(messages):
            message_payloads.append(chat_message_to_json(messages[index]))
            index += 1

        index = 0
        while index < len(tool_specs):
            tool_payloads.append(tool_spec_to_json(tool_specs[index]))
            index += 1

        params: dict[str, Any] = dict()
        params["provider_config"] = provider_config_to_json(config)
        params["system_prompt"] = system_prompt
        params["messages"] = message_payloads
        params["tool_specs"] = tool_payloads

        result: Optional[dict[str, Any]] = self.call_method("llm/complete", params)
        if result is None:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.HTTP_ERROR,
                error_message="VeraGrid AI MCP server is not available.",
            )
        else:
            return llm_response_from_json(result)

    def list_provider_models(self, config: ProviderConfig) -> ModelListResult:
        """
        Query model names through the MCP server.

        :param config: Provider configuration.
        :returns: Model-list result.
        """
        params: dict[str, Any] = dict()
        params["provider_config"] = provider_config_to_json(config)
        result: Optional[dict[str, Any]] = self.call_method("llm/list_models", params)

        if result is None:
            return ModelListResult(
                success=False,
                model_names=list(),
                error_message="VeraGrid AI MCP server is not available.",
            )
        else:
            return model_list_result_from_json(result)


class McpBackedLLMProvider:
    """
    Provider adapter that lets the existing orchestrator call the MCP server.
    """

    __slots__ = (
        "_client",
        "_config",
    )

    def __init__(self, client: VeraGridMcpClient, config: ProviderConfig) -> None:
        """
        Store the MCP client and provider configuration.

        :param client: MCP client.
        :param config: Provider configuration.
        """
        self._client: VeraGridMcpClient = client
        self._config: ProviderConfig = config

    def complete(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        tool_specs: list[ToolSpec],
    ) -> LLMResponse:
        """
        Execute one completion through MCP.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tool schemas.
        :returns: LLM response.
        """
        return self._client.complete(
            config=self._config,
            system_prompt=system_prompt,
            messages=messages,
            tool_specs=tool_specs,
        )

    def complete_with_callback(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        tool_specs: list[ToolSpec],
        text_delta_callback: Optional[Callable[[str], None]],
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> LLMResponse:
        """
        Execute one MCP completion.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tool schemas.
        :param text_delta_callback: Optional text-delta callback.
        :param cancellation_check: Optional cancellation check.
        :returns: LLM response.
        """
        del text_delta_callback

        if cancellation_check is None:
            pass
        else:
            if cancellation_check():
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.CANCELED,
                    error_message="Generation stopped.",
                )
            else:
                pass

        return self.complete(
            system_prompt=system_prompt,
            messages=messages,
            tool_specs=tool_specs,
        )
