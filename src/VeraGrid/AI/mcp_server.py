# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import sys
from typing import Any, Optional

from VeraGrid.AI.mcp_protocol import (
    chat_message_from_json,
    llm_response_to_json,
    model_list_result_to_json,
    provider_config_from_json,
    read_mcp_message,
    tool_spec_from_json,
    write_mcp_message,
)
from VeraGrid.AI.providers import build_provider
from VeraGrid.AI.providers import list_provider_models
from VeraGrid.AI.types_and_tools import (
    ChatMessage,
    LLMResponse,
    ModelListResult,
    ProviderConfig,
    ProviderType,
    ToolSpec,
)


class VeraGridAiMcpServer:
    """
    Minimal MCP stdio server for VeraGrid AI completions.
    """

    __slots__ = (
        "_cached_provider",
        "_cached_signature",
    )

    def __init__(self) -> None:
        """
        Build the server with no loaded model/provider.
        """
        self._cached_provider: Any = None
        self._cached_signature: str = ""

    def _build_provider_signature(self, config: ProviderConfig) -> str:
        """
        Build a cache key for provider reuse.

        :param config: Provider configuration.
        :returns: Cache signature.
        """
        api_key_text: str = "" if config.api_key is None else config.api_key
        base_url_text: str = "" if config.base_url is None else config.base_url
        return (
            f"{config.provider_tpe.value}|{config.model_name}|{api_key_text}|"
            f"{base_url_text}|{config.timeout_s}"
        )

    def _get_provider(self, config: ProviderConfig) -> Any:
        """
        Reuse the provider for repeated calls with the same backend settings.

        :param config: Provider configuration.
        :returns: Provider instance.
        """
        signature: str = self._build_provider_signature(config)

        # Provider creation stays lazy so VeraGrid startup only starts a cheap idle process.
        if self._cached_signature == signature:
            if self._cached_provider is None:
                self._cached_provider = build_provider(config)
            else:
                pass
        else:
            self._cached_provider = build_provider(config)
            self._cached_signature = signature

        return self._cached_provider

    def handle_request(self, request: dict[str, Any]) -> Optional[dict[str, Any]]:
        """
        Handle one JSON-RPC request.

        :param request: JSON-RPC request object.
        :returns: JSON-RPC response object, or None for notifications.
        """
        request_id: object = request.get("id", None)
        method_obj: object = request.get("method", "")
        params_obj: object = request.get("params", dict())

        if request_id is None:
            return None
        else:
            pass

        if isinstance(method_obj, str):
            method: str = method_obj
        else:
            method = ""

        if isinstance(params_obj, dict):
            params: dict[str, Any] = params_obj
        else:
            params = dict()

        try:
            result: Any = self.dispatch_method(method=method, params=params)
            return self.build_result_response(request_id=request_id, result=result)
        except Exception as exc:
            return self.build_error_response(request_id=request_id, message=str(exc))

    def dispatch_method(self, method: str, params: dict[str, Any]) -> Any:
        """
        Dispatch a supported MCP/JSON-RPC method.

        :param method: Method name.
        :param params: Request parameters.
        :returns: Method result.
        """
        if method == "initialize":
            return self.handle_initialize()
        else:
            if method == "tools/list":
                return self.handle_tools_list()
            else:
                if method == "tools/call":
                    return self.handle_tools_call(params)
                else:
                    if method == "llm/complete":
                        return self.handle_llm_complete(params)
                    else:
                        if method == "llm/list_models":
                            return self.handle_llm_list_models(params)
                        else:
                            if method == "shutdown":
                                return dict()
                            else:
                                raise ValueError(f"Unsupported MCP method: {method}")

    def handle_initialize(self) -> dict[str, Any]:
        """
        Return the MCP initialize payload.

        :returns: Initialize result.
        """
        server_info: dict[str, Any] = dict()
        capabilities: dict[str, Any] = dict()
        tools: dict[str, Any] = dict()
        result: dict[str, Any] = dict()

        server_info["name"] = "veragrid-ai"
        server_info["version"] = "0.1"
        capabilities["tools"] = tools
        result["protocolVersion"] = "2024-11-05"
        result["serverInfo"] = server_info
        result["capabilities"] = capabilities
        return result

    def handle_tools_list(self) -> dict[str, Any]:
        """
        Return the standard MCP tools exposed by the VeraGrid AI server.

        :returns: MCP tools/list result.
        """
        result: dict[str, Any] = dict()
        tools: list[dict[str, Any]] = list()
        status_tool: dict[str, Any] = dict()
        status_schema: dict[str, Any] = dict()
        model_tool: dict[str, Any] = dict()
        model_schema: dict[str, Any] = dict()
        model_properties: dict[str, Any] = dict()
        base_url_property: dict[str, Any] = dict()
        stack_tool: dict[str, Any] = dict()
        stack_schema: dict[str, Any] = dict()

        status_schema["type"] = "object"
        status_schema["properties"] = dict()
        status_schema["additionalProperties"] = False
        status_tool["name"] = "veragrid_status"
        status_tool["description"] = "Report whether the VeraGrid AI MCP server is reachable."
        status_tool["inputSchema"] = status_schema
        tools.append(status_tool)

        base_url_property["type"] = "string"
        base_url_property["description"] = "Ollama OpenAI-compatible base URL."
        model_properties["base_url"] = base_url_property
        model_schema["type"] = "object"
        model_schema["properties"] = model_properties
        model_schema["additionalProperties"] = False
        model_tool["name"] = "ollama_models"
        model_tool["description"] = "List the models reported by the local Ollama server."
        model_tool["inputSchema"] = model_schema
        tools.append(model_tool)

        stack_schema["type"] = "object"
        stack_schema["properties"] = dict()
        stack_schema["additionalProperties"] = False
        stack_tool["name"] = "veragrid_stack_status"
        stack_tool["description"] = "Report the VeraGrid and VeraGridEngine packages available to this external MCP server."
        stack_tool["inputSchema"] = stack_schema
        tools.append(stack_tool)

        result["tools"] = tools
        return result

    def handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Execute one standard MCP tool call.

        :param params: Tool-call parameters.
        :returns: MCP tools/call result.
        """
        name_obj: object = params.get("name", "")
        arguments_obj: object = params.get("arguments", dict())
        name: str = str(name_obj) if isinstance(name_obj, str) else ""
        arguments: dict[str, Any]
        result_text: str

        if isinstance(arguments_obj, dict):
            arguments = arguments_obj
        else:
            arguments = dict()

        if name == "veragrid_status":
            result_text = "VeraGrid AI MCP server is connected."
        else:
            if name == "ollama_models":
                result_text = self.build_ollama_models_tool_text(arguments)
            else:
                if name == "veragrid_stack_status":
                    result_text = self.build_veragrid_stack_status_text()
                else:
                    result_text = f"Unknown VeraGrid AI MCP tool: {name}"

        return self.build_text_tool_result(result_text)

    def build_veragrid_stack_status_text(self) -> str:
        """
        Build the VeraGrid package-stack status response.

        :returns: Human-readable package-stack status.
        """
        lines: list[str] = list()

        try:
            from VeraGrid.__version__ import __VeraGrid_VERSION__
            lines.append("VeraGrid: " + __VeraGrid_VERSION__)
        except ImportError as exc:
            lines.append("VeraGrid: unavailable (" + str(exc) + ")")

        try:
            from VeraGridEngine.__version__ import __VeraGridEngine_VERSION__
            lines.append("VeraGridEngine: " + __VeraGridEngine_VERSION__)
        except ImportError as exc:
            lines.append("VeraGridEngine: unavailable (" + str(exc) + ")")

        return "\n".join(lines)

    def build_ollama_models_tool_text(self, arguments: dict[str, Any]) -> str:
        """
        Build the Ollama model-list tool response.

        :param arguments: Tool-call arguments.
        :returns: Human-readable model-list text.
        """
        base_url_obj: object = arguments.get("base_url", "http://localhost:11434/v1")
        base_url: str = str(base_url_obj) if isinstance(base_url_obj, str) else "http://localhost:11434/v1"
        config: ProviderConfig = ProviderConfig(
            provider_tpe=ProviderType.OLLAMA,
            model_name="",
            api_key=None,
            base_url=base_url,
            timeout_s=15.0,
        )
        model_result: ModelListResult = list_provider_models(config)
        text: str

        if model_result.success:
            if len(model_result.model_names) > 0:
                text = "Ollama reported these models: " + ", ".join(model_result.model_names)
            else:
                text = "Ollama is reachable, but it reported no installed models."
        else:
            text = f"Ollama model discovery failed: {model_result.error_message}"

        return text

    def build_text_tool_result(self, text: str) -> dict[str, Any]:
        """
        Build a standard MCP text tool result.

        :param text: Tool result text.
        :returns: MCP tools/call result.
        """
        result: dict[str, Any] = dict()
        content: list[dict[str, str]] = list()
        text_content: dict[str, str] = dict()

        text_content["type"] = "text"
        text_content["text"] = text
        content.append(text_content)
        result["content"] = content
        result["isError"] = False
        return result

    def handle_llm_complete(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Run one provider completion.

        :param params: Completion parameters.
        :returns: Serialized LLM response.
        """
        config_obj: object = params.get("provider_config", dict())
        messages_obj: object = params.get("messages", list())
        tools_obj: object = params.get("tool_specs", list())
        messages: list[ChatMessage] = list()
        tool_specs: list[ToolSpec] = list()
        index: int = 0

        if isinstance(config_obj, dict):
            config: ProviderConfig = provider_config_from_json(config_obj)
        else:
            config = provider_config_from_json(dict())

        if isinstance(messages_obj, list):
            while index < len(messages_obj):
                message_obj: object = messages_obj[index]
                if isinstance(message_obj, dict):
                    messages.append(chat_message_from_json(message_obj))
                else:
                    pass
                index += 1
        else:
            pass

        if isinstance(tools_obj, list):
            index = 0
            while index < len(tools_obj):
                tool_obj: object = tools_obj[index]
                if isinstance(tool_obj, dict):
                    tool_specs.append(tool_spec_from_json(tool_obj))
                else:
                    pass
                index += 1
        else:
            pass

        provider: Any = self._get_provider(config)
        response: LLMResponse = provider.complete(
            system_prompt=str(params.get("system_prompt", "")),
            messages=messages,
            tool_specs=tool_specs,
        )
        return llm_response_to_json(response)

    def handle_llm_list_models(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Query models through the selected provider.

        :param params: Model-list parameters.
        :returns: Serialized model-list result.
        """
        config_obj: object = params.get("provider_config", dict())

        if isinstance(config_obj, dict):
            config: ProviderConfig = provider_config_from_json(config_obj)
        else:
            config = provider_config_from_json(dict())

        result: ModelListResult = list_provider_models(config)
        return model_list_result_to_json(result)

    def build_result_response(self, request_id: object, result: Any) -> dict[str, Any]:
        """
        Build a successful JSON-RPC response.

        :param request_id: JSON-RPC request id.
        :param result: Method result.
        :returns: JSON-RPC response.
        """
        response: dict[str, Any] = dict()
        response["jsonrpc"] = "2.0"
        response["id"] = request_id
        response["result"] = result
        return response

    def build_error_response(self, request_id: object, message: str) -> dict[str, Any]:
        """
        Build an error JSON-RPC response.

        :param request_id: JSON-RPC request id.
        :param message: Error message.
        :returns: JSON-RPC response.
        """
        error_obj: dict[str, Any] = dict()
        response: dict[str, Any] = dict()
        error_obj["code"] = -32000
        error_obj["message"] = message
        response["jsonrpc"] = "2.0"
        response["id"] = request_id
        response["error"] = error_obj
        return response

    def serve(self) -> int:
        """
        Serve MCP requests until stdin closes.

        :returns: Process exit code.
        """
        while True:
            request: Optional[dict[str, Any]] = read_mcp_message(sys.stdin.buffer)
            if request is None:
                return 0
            else:
                response: Optional[dict[str, Any]] = self.handle_request(request)
                if response is None:
                    pass
                else:
                    write_mcp_message(sys.stdout.buffer, response)


def run_server() -> int:
    """
    Run the VeraGrid AI MCP server.

    :returns: Process exit code.
    """
    server: VeraGridAiMcpServer = VeraGridAiMcpServer()
    return server.serve()


if __name__ == "__main__":
    raise SystemExit(run_server())
