# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import json
from typing import Any, Optional, BinaryIO

from VeraGrid.AI.types_and_tools import (
    ChatMessage,
    LLMResponse,
    ModelListResult,
    ProviderConfig,
    ProviderErrorCode,
    ProviderType,
    ToolCall,
    ToolErrorCode,
    ToolExecutionResult,
    ToolHandlerProtocol,
    ToolRisk,
    ToolSpec,
)


class EmptyToolHandler:
    """
    Placeholder handler used when only a tool schema is needed by an LLM provider.
    """

    __slots__ = ()

    def execute(self, arguments: dict[str, Any]) -> ToolExecutionResult:
        """
        Return a deterministic failure because remote tool execution is owned by the GUI process.

        :param arguments: Tool arguments.
        :returns: Failed tool execution result.
        """
        del arguments
        return ToolExecutionResult(
            success=False,
            error_code=ToolErrorCode.EXECUTION_ERROR,
            error_message="MCP schema tool handlers cannot execute in the AI server process.",
            payload_json="{}",
        )


def provider_config_to_json(config: ProviderConfig) -> dict[str, Any]:
    """
    Convert provider configuration to a JSON-compatible dictionary.

    :param config: Provider configuration.
    :returns: JSON-compatible dictionary.
    """
    payload: dict[str, Any] = dict()
    payload["provider_tpe"] = config.provider_tpe.value
    payload["model_name"] = config.model_name
    payload["api_key"] = config.api_key
    payload["base_url"] = config.base_url
    payload["timeout_s"] = config.timeout_s
    payload["context_window_tokens"] = config.context_window_tokens
    payload["completion_tokens"] = config.completion_tokens
    payload["gpu_layers"] = config.gpu_layers
    payload["temperature"] = config.temperature
    payload["top_p"] = config.top_p
    payload["history_message_limit"] = config.history_message_limit
    payload["history_char_budget"] = config.history_char_budget
    payload["grounding_char_budget"] = config.grounding_char_budget
    return payload


def provider_config_from_json(payload: dict[str, Any]) -> ProviderConfig:
    """
    Build provider configuration from a JSON-compatible dictionary.

    :param payload: JSON-compatible provider payload.
    :returns: Provider configuration.
    """
    provider_value: object = payload.get("provider_tpe", ProviderType.OLLAMA.value)
    provider_tpe: ProviderType = ProviderType.OLLAMA
    provider_items: list[ProviderType] = list(ProviderType)
    index: int = 0

    # Map serialized provider names through the enum so old config can be migrated safely.
    while index < len(provider_items):
        provider_item: ProviderType = provider_items[index]
        if provider_value == provider_item.value:
            provider_tpe = provider_item
            index = len(provider_items)
        else:
            index += 1

    if provider_value == "local_llama_cpp":
        provider_tpe = ProviderType.OLLAMA
    else:
        pass

    api_key_obj: object = payload.get("api_key", None)
    base_url_obj: object = payload.get("base_url", None)

    return ProviderConfig(
        provider_tpe=provider_tpe,
        model_name=str(payload.get("model_name", "")),
        api_key=api_key_obj if isinstance(api_key_obj, str) and len(api_key_obj) > 0 else None,
        base_url=base_url_obj if isinstance(base_url_obj, str) else None,
        timeout_s=float(payload.get("timeout_s", 60.0)),
        context_window_tokens=int(payload.get("context_window_tokens", 4096)),
        completion_tokens=int(payload.get("completion_tokens", 1024)),
        gpu_layers=int(payload.get("gpu_layers", 0)),
        temperature=float(payload.get("temperature", 0.15)),
        top_p=float(payload.get("top_p", 0.90)),
        history_message_limit=int(payload.get("history_message_limit", 6)),
        history_char_budget=int(payload.get("history_char_budget", 2200)),
        grounding_char_budget=int(payload.get("grounding_char_budget", 1800)),
    )


def chat_message_to_json(message: ChatMessage) -> dict[str, Any]:
    """
    Convert one chat message to JSON.

    :param message: Chat message.
    :returns: JSON-compatible dictionary.
    """
    payload: dict[str, Any] = dict()
    payload["role"] = message.role
    payload["content"] = message.content
    payload["name"] = message.name
    return payload


def chat_message_from_json(payload: dict[str, Any]) -> ChatMessage:
    """
    Build one chat message from JSON.

    :param payload: JSON-compatible dictionary.
    :returns: Chat message.
    """
    name_obj: object = payload.get("name", None)
    return ChatMessage(
        role=str(payload.get("role", "user")),
        content=str(payload.get("content", "")),
        name=name_obj if isinstance(name_obj, str) else None,
    )


def tool_spec_to_json(tool_spec: ToolSpec) -> dict[str, Any]:
    """
    Convert one tool specification to JSON.

    :param tool_spec: Tool specification.
    :returns: JSON-compatible dictionary.
    """
    payload: dict[str, Any] = dict()
    payload["name"] = tool_spec.name
    payload["description"] = tool_spec.description
    payload["input_schema_json"] = tool_spec.input_schema_json
    payload["risk"] = tool_spec.risk.value
    return payload


def tool_spec_from_json(payload: dict[str, Any]) -> ToolSpec:
    """
    Build one schema-only tool specification from JSON.

    :param payload: JSON-compatible dictionary.
    :returns: Tool specification.
    """
    risk_value: object = payload.get("risk", ToolRisk.READ_ONLY.value)
    risk: ToolRisk = ToolRisk.READ_ONLY
    risk_items: list[ToolRisk] = list(ToolRisk)
    index: int = 0
    handler: ToolHandlerProtocol = EmptyToolHandler()

    # Keep risk parsing explicit because provider payloads should not compare raw strings.
    while index < len(risk_items):
        risk_item: ToolRisk = risk_items[index]
        if risk_value == risk_item.value:
            risk = risk_item
            index = len(risk_items)
        else:
            index += 1

    return ToolSpec(
        name=str(payload.get("name", "")),
        description=str(payload.get("description", "")),
        input_schema_json=str(payload.get("input_schema_json", "{}")),
        risk=risk,
        handler=handler,
    )


def tool_call_to_json(tool_call: ToolCall) -> dict[str, Any]:
    """
    Convert one tool call to JSON.

    :param tool_call: Tool call.
    :returns: JSON-compatible dictionary.
    """
    payload: dict[str, Any] = dict()
    payload["call_id"] = tool_call.call_id
    payload["tool_name"] = tool_call.tool_name
    payload["arguments_json"] = tool_call.arguments_json
    return payload


def tool_call_from_json(payload: dict[str, Any]) -> ToolCall:
    """
    Build one tool call from JSON.

    :param payload: JSON-compatible dictionary.
    :returns: Tool call.
    """
    return ToolCall(
        call_id=str(payload.get("call_id", "")),
        tool_name=str(payload.get("tool_name", "")),
        arguments_json=str(payload.get("arguments_json", "{}")),
    )


def llm_response_to_json(response: LLMResponse) -> dict[str, Any]:
    """
    Convert an LLM response to JSON.

    :param response: LLM response.
    :returns: JSON-compatible dictionary.
    """
    payload: dict[str, Any] = dict()
    tool_calls: list[dict[str, Any]] = list()
    index: int = 0

    while index < len(response.tool_calls):
        tool_calls.append(tool_call_to_json(response.tool_calls[index]))
        index += 1

    payload["text"] = response.text
    payload["tool_calls"] = tool_calls
    payload["error_code"] = response.error_code.value
    payload["error_message"] = response.error_message
    return payload


def llm_response_from_json(payload: dict[str, Any]) -> LLMResponse:
    """
    Build an LLM response from JSON.

    :param payload: JSON-compatible dictionary.
    :returns: LLM response.
    """
    error_value: object = payload.get("error_code", ProviderErrorCode.NONE.value)
    error_code: ProviderErrorCode = ProviderErrorCode.NONE
    error_items: list[ProviderErrorCode] = list(ProviderErrorCode)
    tool_calls_obj: object = payload.get("tool_calls", list())
    tool_calls: list[ToolCall] = list()
    index: int = 0

    while index < len(error_items):
        error_item: ProviderErrorCode = error_items[index]
        if error_value == error_item.value:
            error_code = error_item
            index = len(error_items)
        else:
            index += 1

    if isinstance(tool_calls_obj, list):
        index = 0
        while index < len(tool_calls_obj):
            tool_call_obj: object = tool_calls_obj[index]
            if isinstance(tool_call_obj, dict):
                tool_calls.append(tool_call_from_json(tool_call_obj))
            else:
                pass
            index += 1
    else:
        pass

    return LLMResponse(
        text=str(payload.get("text", "")),
        tool_calls=tool_calls,
        error_code=error_code,
        error_message=str(payload.get("error_message", "")),
    )


def model_list_result_to_json(result: ModelListResult) -> dict[str, Any]:
    """
    Convert a model-list result to JSON.

    :param result: Model-list result.
    :returns: JSON-compatible dictionary.
    """
    payload: dict[str, Any] = dict()
    payload["success"] = result.success
    payload["model_names"] = result.model_names
    payload["error_message"] = result.error_message
    return payload


def model_list_result_from_json(payload: dict[str, Any]) -> ModelListResult:
    """
    Build a model-list result from JSON.

    :param payload: JSON-compatible dictionary.
    :returns: Model-list result.
    """
    names_obj: object = payload.get("model_names", list())
    names: list[str] = list()
    index: int = 0

    if isinstance(names_obj, list):
        while index < len(names_obj):
            name_obj: object = names_obj[index]
            if isinstance(name_obj, str):
                names.append(name_obj)
            else:
                pass
            index += 1
    else:
        pass

    return ModelListResult(
        success=bool(payload.get("success", False)),
        model_names=names,
        error_message=str(payload.get("error_message", "")),
    )


def write_mcp_message(stream: BinaryIO, payload: dict[str, Any]) -> None:
    """
    Write one MCP-framed JSON-RPC payload.

    :param stream: Output byte stream.
    :param payload: JSON-RPC payload.
    :returns: Nothing.
    """
    encoded_payload: bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header: bytes = f"Content-Length: {len(encoded_payload)}\r\n\r\n".encode("ascii")

    # MCP stdio transport frames JSON-RPC with HTTP-like content headers.
    stream.write(header)
    stream.write(encoded_payload)
    stream.flush()


def read_mcp_message(stream: BinaryIO) -> Optional[dict[str, Any]]:
    """
    Read one MCP-framed JSON-RPC payload.

    :param stream: Input byte stream.
    :returns: JSON-RPC payload or None at EOF/invalid input.
    """
    header_lines: list[bytes] = list()
    content_length: int = -1
    line: bytes = stream.readline()

    if len(line) == 0:
        return None
    else:
        pass

    while len(line) > 0 and line not in (b"\r\n", b"\n"):
        header_lines.append(line)
        line = stream.readline()

    index: int = 0
    while index < len(header_lines):
        header_text: str = header_lines[index].decode("ascii", errors="ignore").strip()
        if header_text.lower().startswith("content-length:"):
            length_text: str = header_text.split(":", 1)[1].strip()
            try:
                content_length = int(length_text)
            except ValueError:
                content_length = -1
        else:
            pass
        index += 1

    if content_length <= 0:
        return None
    else:
        pass

    body: bytes = stream.read(content_length)
    if len(body) != content_length:
        return None
    else:
        pass

    try:
        decoded_obj: Any = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return None

    if isinstance(decoded_obj, dict):
        return decoded_obj
    else:
        return None
