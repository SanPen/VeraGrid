from __future__ import annotations

"""
Provider-agnostic LLM integration layers for VeraGrid.

This module implements the following components:

- Provider selection through enums
- Typed request/response wrapper classes
- OpenAI provider
- Anthropic provider
- OpenAI-compatible provider for Ollama / LM Studio
- Local llama.cpp provider for GGUF models loaded in-process
- Tool registry
- Approval gate for mutating tools
- Conversation orchestrator
- VeraGrid context builder

The module is intentionally written in a conservative style so it can be
integrated into VeraGrid with minimal hidden behaviour.
"""

from enum import Enum
import json
from typing import Any, Optional, Protocol


class ProviderType(Enum):
    """Supported LLM provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENAI_COMPATIBLE = "openai_compatible"
    GEMINI = "gemini"
    LOCAL_LLAMA_CPP = "local_llama_cpp"


class ToolRisk(Enum):
    """Risk classes for tool execution."""

    READ_ONLY = "read_only"
    COMPUTE = "compute"
    MUTATING = "mutating"
    DESTRUCTIVE = "destructive"


class ProviderErrorCode(Enum):
    """Error categories for provider execution."""

    NONE = "none"
    CANCELED = "canceled"
    HTTP_ERROR = "http_error"
    PARSE_ERROR = "parse_error"
    INVALID_CONFIGURATION = "invalid_configuration"


class ToolErrorCode(Enum):
    """Error categories for tool execution."""

    NONE = "none"
    UNKNOWN_TOOL = "unknown_tool"
    APPROVAL_REQUIRED = "approval_required"
    EXECUTION_ERROR = "execution_error"


class ProviderConfig:
    """
    Provider configuration.

    :param provider_tpe: Selected provider type.
    :param model_name: Model identifier.
    :param api_key: API key if required.
    :param base_url: Base URL for the provider endpoint.
    :param timeout_s: HTTP timeout in seconds.
    :param context_window_tokens: Local context-window token budget.
    :param completion_tokens: Completion token budget.
    :param gpu_layers: Local llama.cpp GPU layer count.
    :param temperature: Local llama.cpp sampling temperature.
    :param top_p: Local llama.cpp nucleus sampling factor.
    :param history_message_limit: Prompt history message budget.
    :param history_char_budget: Prompt history character budget.
    :param grounding_char_budget: Prompt grounding character budget.
    """

    __slots__ = (
        "provider_tpe",
        "model_name",
        "api_key",
        "base_url",
        "timeout_s",
        "context_window_tokens",
        "completion_tokens",
        "gpu_layers",
        "temperature",
        "top_p",
        "history_message_limit",
        "history_char_budget",
        "grounding_char_budget",
    )

    def __init__(
        self,
        provider_tpe: ProviderType,
        model_name: str,
        api_key: Optional[str],
        base_url: Optional[str],
        timeout_s: float,
        context_window_tokens: int = 4096,
        completion_tokens: int = 1024,
        gpu_layers: int = 33,
        temperature: float = 0.15,
        top_p: float = 0.90,
        history_message_limit: int = 6,
        history_char_budget: int = 2200,
        grounding_char_budget: int = 1800,
    ) -> None:
        self.provider_tpe: ProviderType = provider_tpe
        self.model_name: str = model_name
        self.api_key: Optional[str] = api_key
        self.base_url: Optional[str] = base_url
        self.timeout_s: float = timeout_s
        self.context_window_tokens: int = context_window_tokens
        self.completion_tokens: int = completion_tokens
        self.gpu_layers: int = gpu_layers
        self.temperature: float = temperature
        self.top_p: float = top_p
        self.history_message_limit: int = history_message_limit
        self.history_char_budget: int = history_char_budget
        self.grounding_char_budget: int = grounding_char_budget


class ChatMessage:
    """
    Conversation message.

    :param role: Message role.
    :param content: Message text.
    :param name: Optional message name.
    """

    __slots__ = (
        "role",
        "content",
        "name",
    )

    def __init__(self, role: str, content: str, name: Optional[str] = None) -> None:
        self.role: str = role
        self.content: str = content
        self.name: Optional[str] = name


class ToolCall:
    """
    Tool call returned by a model.

    :param call_id: Tool call identifier.
    :param tool_name: Tool name.
    :param arguments_json: Raw arguments encoded as JSON.
    """

    __slots__ = (
        "call_id",
        "tool_name",
        "arguments_json",
    )

    def __init__(self, call_id: str, tool_name: str, arguments_json: str) -> None:
        self.call_id: str = call_id
        self.tool_name: str = tool_name
        self.arguments_json: str = arguments_json

    def parse_arguments(self) -> tuple[bool, dict[str, Any], str]:
        """
        Parse the tool arguments.

        :returns: Tuple with success flag, parsed arguments and error message.
        """
        parsed_args: dict[str, Any] = dict()
        error_msg: str = ""
        is_ok: bool = False

        try:
            parsed_obj: Any = json.loads(self.arguments_json)
            if isinstance(parsed_obj, dict):
                parsed_args = parsed_obj
                error_msg = ""
                is_ok = True
            else:
                parsed_args = dict()
                error_msg = "Tool arguments are not a JSON object."
                is_ok = False
        except json.JSONDecodeError:
            parsed_args = dict()
            error_msg = "Could not decode tool arguments JSON."
            is_ok = False

        return is_ok, parsed_args, error_msg


class LLMResponse:
    """
    Provider response wrapper.

    :param text: Assistant text.
    :param tool_calls: Parsed tool calls.
    :param error_code: Provider error code.
    :param error_message: Provider error description.
    """

    __slots__ = (
        "text",
        "tool_calls",
        "error_code",
        "error_message",
    )

    def __init__(
        self,
        text: str,
        tool_calls: list[ToolCall],
        error_code: ProviderErrorCode,
        error_message: str,
    ) -> None:
        self.text: str = text
        self.tool_calls: list[ToolCall] = tool_calls
        self.error_code: ProviderErrorCode = error_code
        self.error_message: str = error_message


class ModelListResult:
    """
    Result wrapper for provider model discovery.

    :param success: Discovery success flag.
    :param model_names: Ordered list of discovered model identifiers.
    :param error_message: Error description when discovery fails.
    """

    __slots__ = (
        "success",
        "model_names",
        "error_message",
    )

    def __init__(
        self,
        success: bool,
        model_names: list[str],
        error_message: str,
    ) -> None:
        self.success: bool = success
        self.model_names: list[str] = model_names
        self.error_message: str = error_message


class ToolExecutionResult:
    """
    Result wrapper for tool execution.

    :param success: Execution success flag.
    :param error_code: Tool error code.
    :param error_message: Error message.
    :param payload_json: Tool result encoded as JSON.
    """

    __slots__ = (
        "success",
        "error_code",
        "error_message",
        "payload_json",
    )

    def __init__(
        self,
        success: bool,
        error_code: ToolErrorCode,
        error_message: str,
        payload_json: str,
    ) -> None:
        self.success: bool = success
        self.error_code: ToolErrorCode = error_code
        self.error_message: str = error_message
        self.payload_json: str = payload_json


class PendingApproval:
    """
    Approval request for a pending tool call.

    :param tool_name: Tool name.
    :param arguments_json: Arguments encoded as JSON.
    :param reason: Approval reason.
    """

    __slots__ = (
        "tool_name",
        "arguments_json",
        "reason",
    )

    def __init__(self, tool_name: str, arguments_json: str, reason: str) -> None:
        self.tool_name: str = tool_name
        self.arguments_json: str = arguments_json
        self.reason: str = reason


class ToolSpec:
    """
    Tool specification wrapper.

    :param name: Tool name.
    :param description: Tool description.
    :param input_schema_json: JSON schema as string.
    :param risk: Tool risk class.
    :param handler: Object implementing the tool behaviour.
    """

    __slots__ = (
        "name",
        "description",
        "input_schema_json",
        "risk",
        "handler",
    )

    def __init__(
        self,
        name: str,
        description: str,
        input_schema_json: str,
        risk: ToolRisk,
        handler: "ToolHandlerProtocol",
    ) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema_json: str = input_schema_json
        self.risk: ToolRisk = risk
        self.handler: ToolHandlerProtocol = handler

    def build_openai_tool(self) -> dict[str, Any]:
        """
        Build the OpenAI/OpenAI-compatible tool schema.

        :returns: Tool schema dictionary.
        """
        params_obj: Any = json.loads(self.input_schema_json)
        tool_obj: dict[str, Any] = dict()
        function_obj: dict[str, Any] = dict()
        tool_obj["type"] = "function"
        function_obj["name"] = self.name
        function_obj["description"] = self.description
        function_obj["parameters"] = params_obj
        tool_obj["function"] = function_obj
        return tool_obj

    def build_anthropic_tool(self) -> dict[str, Any]:
        """
        Build the Anthropic tool schema.

        :returns: Tool schema dictionary.
        """
        params_obj: Any = json.loads(self.input_schema_json)
        tool_obj: dict[str, Any] = dict()
        tool_obj["name"] = self.name
        tool_obj["description"] = self.description
        tool_obj["input_schema"] = params_obj
        return tool_obj


class ToolHandlerProtocol(Protocol):
    """Protocol for explicit tool handler objects."""

    def execute(self, arguments: dict[str, Any]) -> ToolExecutionResult:
        """Execute the tool with explicit arguments."""


class ApprovalPolicy:
    """
    Approval policy for tool execution.

    :param require_mutating: Whether mutating tools require approval.
    :param require_destructive: Whether destructive tools require approval.
    """

    __slots__ = (
        "require_mutating",
        "require_destructive",
    )

    def __init__(self, require_mutating: bool, require_destructive: bool) -> None:
        self.require_mutating: bool = require_mutating
        self.require_destructive: bool = require_destructive

    def requires_approval(self, tool_spec: ToolSpec) -> bool:
        """
        Check whether the tool requires approval.

        :param tool_spec: Tool specification.
        :returns: Approval requirement flag.
        """
        requires_flag: bool = False

        if tool_spec.risk == ToolRisk.MUTATING:
            requires_flag = self.require_mutating
        else:
            if tool_spec.risk == ToolRisk.DESTRUCTIVE:
                requires_flag = self.require_destructive
            else:
                requires_flag = False

        return requires_flag


class ToolRegistry:
    """
    Registry of available tools.

    :param approval_policy: Tool approval policy.
    """

    __slots__ = (
        "_approval_policy",
        "_tools_by_name",
        "_tool_order",
    )

    def __init__(self, approval_policy: ApprovalPolicy) -> None:
        self._approval_policy: ApprovalPolicy = approval_policy
        self._tools_by_name: dict[str, ToolSpec] = dict()
        self._tool_order: list[str] = list()

    def register(self, tool_spec: ToolSpec) -> bool:
        """
        Register a tool.

        :param tool_spec: Tool specification.
        :returns: True if the tool was added, False if it already existed.
        """
        was_added: bool = False

        if tool_spec.name in self._tools_by_name:
            was_added = False
        else:
            self._tools_by_name[tool_spec.name] = tool_spec
            self._tool_order.append(tool_spec.name)
            was_added = True

        return was_added

    def get_tool(self, tool_name: str) -> Optional[ToolSpec]:
        """
        Get a tool by name.

        :param tool_name: Tool name.
        :returns: Tool specification or None.
        """
        tool_spec: Optional[ToolSpec] = self._tools_by_name.get(tool_name, None)
        return tool_spec

    def list_tools(self) -> list[ToolSpec]:
        """
        Return the registered tools in insertion order.

        :returns: List of tool specifications.
        """
        tool_specs: list[ToolSpec] = list()
        index: int = 0
        tool_count: int = len(self._tool_order)

        while index < tool_count:
            tool_name: str = self._tool_order[index]
            tool_spec: ToolSpec = self._tools_by_name[tool_name]
            tool_specs.append(tool_spec)
            index += 1

        return tool_specs

    def execute(
        self,
        tool_name: str,
        arguments_json: str,
        is_approved: bool,
    ) -> ToolExecutionResult:
        """
        Execute a registered tool.

        :param tool_name: Tool name.
        :param arguments_json: Tool arguments JSON.
        :param is_approved: Approval flag.
        :returns: Tool execution result.
        """
        tool_spec: Optional[ToolSpec] = self.get_tool(tool_name)
        result: ToolExecutionResult

        if tool_spec is None:
            result = ToolExecutionResult(
                success=False,
                error_code=ToolErrorCode.UNKNOWN_TOOL,
                error_message=f"Unknown tool: {tool_name}",
                payload_json="{}",
            )
        else:
            if self._approval_policy.requires_approval(tool_spec) and (not is_approved):
                result = ToolExecutionResult(
                    success=False,
                    error_code=ToolErrorCode.APPROVAL_REQUIRED,
                    error_message=f"Tool '{tool_name}' requires approval.",
                    payload_json="{}",
                )
            else:
                parsed_ok: bool
                parsed_args: dict[str, Any]
                parse_error: str
                parser: ToolCall = ToolCall("", tool_name, arguments_json)
                parsed_ok, parsed_args, parse_error = parser.parse_arguments()

                if parsed_ok:
                    result = tool_spec.handler.execute(parsed_args)
                else:
                    result = ToolExecutionResult(
                        success=False,
                        error_code=ToolErrorCode.EXECUTION_ERROR,
                        error_message=parse_error,
                        payload_json="{}",
                    )

        return result


def strip_json_code_fence(text: str) -> str:
    """
    Remove a surrounding Markdown code fence from a JSON-like text block.

    :param text: Raw text block.
    :returns: Unwrapped text.
    """
    stripped_text: str = text.strip()
    newline_index: int

    if stripped_text.startswith("```") and stripped_text.endswith("```"):
        newline_index = stripped_text.find("\n")

        if newline_index > -1:
            return stripped_text[(newline_index + 1):-3].strip()
        else:
            return stripped_text[3:-3].strip()
    else:
        return stripped_text


def try_parse_text_tool_call(
    text: str,
    tool_registry: ToolRegistry,
) -> tuple[bool, Optional[ToolCall]]:
    """
    Parse a raw assistant text blob as a tool call when a local model emits JSON instead of structured tool use.

    :param text: Assistant text.
    :param tool_registry: Registered tool set.
    :returns: Tuple with success flag and parsed tool call.
    """
    normalized_text: str = strip_json_code_fence(text)
    parsed_obj: Any
    tool_name_obj: object
    arguments_obj: object
    tool_name: str

    if len(normalized_text) == 0:
        return False, None
    else:
        pass

    if normalized_text.startswith("{") and normalized_text.endswith("}"):
        pass
    else:
        return False, None

    try:
        parsed_obj = json.loads(normalized_text)
    except json.JSONDecodeError:
        return False, None

    if isinstance(parsed_obj, dict):
        tool_name_obj = parsed_obj.get("name", None)

        if tool_name_obj is None:
            tool_name_obj = parsed_obj.get("tool_name", None)
        else:
            pass

        if isinstance(tool_name_obj, str):
            tool_name = tool_name_obj.strip()
        else:
            return False, None

        if tool_registry.get_tool(tool_name) is None:
            return False, None
        else:
            pass

        arguments_obj = parsed_obj.get("parameters", None)

        if arguments_obj is None:
            arguments_obj = parsed_obj.get("arguments", None)
        else:
            pass

        if arguments_obj is None:
            arguments_obj = parsed_obj.get("input", None)
        else:
            pass

        if isinstance(arguments_obj, dict):
            return True, ToolCall(
                call_id="text_tool_call_0",
                tool_name=tool_name,
                arguments_json=json.dumps(arguments_obj, ensure_ascii=False),
            )
        else:
            if arguments_obj is None:
                return True, ToolCall(
                    call_id="text_tool_call_0",
                    tool_name=tool_name,
                    arguments_json="{}",
                )
            else:
                return False, None
    else:
        return False, None
