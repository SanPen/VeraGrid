from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional, Protocol

import requests

from VeraGrid.Gui.AiAgent.backend.types_and_tools import (
    ChatMessage,
    LLMResponse,
    ModelListResult,
    ProviderConfig,
    ProviderErrorCode,
    ProviderType,
    ToolCall,
    ToolSpec,
)


class LLMProviderProtocol(Protocol):
    """Protocol for LLM providers."""

    def complete(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        tool_specs: list[ToolSpec],
    ) -> LLMResponse:
        """Run one provider completion."""

    def complete_with_callback(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        tool_specs: list[ToolSpec],
        text_delta_callback: Optional[Callable[[str], None]],
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> LLMResponse:
        """Run one provider completion and emit text deltas when supported."""


class HTTPClient:
    """
    Simple explicit HTTP client wrapper.

    :param config: Provider configuration.
    """

    __slots__ = ("_config",)

    def __init__(self, config: ProviderConfig) -> None:
        self._config: ProviderConfig = config

    def build_headers(self) -> dict[str, str]:
        """
        Build the request headers.

        :returns: HTTP headers.
        """
        headers: dict[str, str] = dict()
        headers["Content-Type"] = "application/json"

        if self._config.provider_tpe == ProviderType.ANTHROPIC:
            headers["anthropic-version"] = "2023-06-01"
        else:
            headers["Content-Type"] = "application/json"

        if self._config.api_key is None:
            headers_result: dict[str, str] = headers
        else:
            if self._config.provider_tpe == ProviderType.ANTHROPIC:
                headers["x-api-key"] = self._config.api_key
                headers_result = headers
            else:
                headers["Authorization"] = f"Bearer {self._config.api_key}"
                headers_result = headers

        return headers_result

    def post_json(self, url: str, payload: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
        """
        Execute a POST request and decode the JSON response.

        :param url: Endpoint URL.
        :param payload: JSON payload.
        :returns: Tuple with success flag, decoded payload and error message.
        """
        response_obj: requests.Response
        result_obj: dict[str, Any] = dict()
        error_msg: str = ""
        is_ok: bool = False

        try:
            response_obj = requests.post(
                url,
                headers=self.build_headers(),
                json=payload,
                timeout=self._config.timeout_s,
            )
            if response_obj.status_code >= 400:
                result_obj = dict()
                error_msg = f"HTTP {response_obj.status_code}: {response_obj.text}"
                is_ok = False
            else:
                try:
                    decoded_obj: Any = response_obj.json()
                    if isinstance(decoded_obj, dict):
                        result_obj = decoded_obj
                        error_msg = ""
                        is_ok = True
                    else:
                        result_obj = dict()
                        error_msg = "Provider returned a non-object JSON payload."
                        is_ok = False
                except ValueError:
                    result_obj = dict()
                    error_msg = "Provider returned invalid JSON."
                    is_ok = False
        except requests.RequestException as exc:
            result_obj = dict()
            error_msg = str(exc)
            is_ok = False

        return is_ok, result_obj, error_msg

    def get_json(self, url: str) -> tuple[bool, dict[str, Any], str]:
        """
        Execute a GET request and decode the JSON response.

        :param url: Endpoint URL.
        :returns: Tuple with success flag, decoded payload and error message.
        """
        response_obj: requests.Response
        result_obj: dict[str, Any] = dict()
        error_msg: str = ""
        is_ok: bool = False

        try:
            response_obj = requests.get(
                url,
                headers=self.build_headers(),
                timeout=self._config.timeout_s,
            )
            if response_obj.status_code >= 400:
                result_obj = dict()
                error_msg = f"HTTP {response_obj.status_code}: {response_obj.text}"
                is_ok = False
            else:
                try:
                    decoded_obj: Any = response_obj.json()
                    if isinstance(decoded_obj, dict):
                        result_obj = decoded_obj
                        error_msg = ""
                        is_ok = True
                    else:
                        result_obj = dict()
                        error_msg = "Provider returned a non-object JSON payload."
                        is_ok = False
                except ValueError:
                    result_obj = dict()
                    error_msg = "Provider returned invalid JSON."
                    is_ok = False
        except requests.RequestException as exc:
            result_obj = dict()
            error_msg = str(exc)
            is_ok = False

        return is_ok, result_obj, error_msg

    def post_stream(self, url: str, payload: dict[str, Any]) -> tuple[bool, Optional[requests.Response], str]:
        """
        Execute a streaming POST request.

        :param url: Endpoint URL.
        :param payload: JSON payload.
        :returns: Tuple with success flag, response object and error message.
        """
        response_obj: Optional[requests.Response] = None
        error_msg: str = ""

        try:
            response_obj = requests.post(
                url,
                headers=self.build_headers(),
                json=payload,
                timeout=self._config.timeout_s,
                stream=True,
            )
            if response_obj.status_code >= 400:
                error_msg = f"HTTP {response_obj.status_code}: {response_obj.text}"
                response_obj.close()
                return False, None, error_msg
            else:
                return True, response_obj, ""
        except requests.RequestException as exc:
            if response_obj is None:
                pass
            else:
                response_obj.close()
            return False, None, str(exc)


class OpenAIProvider:
    """
    OpenAI Responses API provider.

    :param config: Provider configuration.
    """

    __slots__ = (
        "_config",
        "_http_client",
    )

    def __init__(self, config: ProviderConfig) -> None:
        self._config: ProviderConfig = config
        self._http_client: HTTPClient = HTTPClient(config)

    def complete(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        tool_specs: list[ToolSpec],
    ) -> LLMResponse:
        """
        Execute one OpenAI completion.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tools.
        :returns: Provider response.
        """
        base_url: Optional[str] = self._config.base_url
        message_count: int = len(messages)
        input_items: list[dict[str, Any]] = list()
        tool_items: list[dict[str, Any]] = list()
        index: int = 0

        if base_url is None:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.INVALID_CONFIGURATION,
                error_message="OpenAI base URL is not configured.",
            )
        else:
            while index < message_count:
                message_obj: ChatMessage = messages[index]
                input_item: dict[str, Any] = dict()
                content_item: dict[str, Any] = dict()
                content_items: list[dict[str, Any]] = list()
                input_item["role"] = message_obj.role
                content_item["type"] = "input_text"
                content_item["text"] = message_obj.content
                content_items.append(content_item)
                input_item["content"] = content_items
                input_items.append(input_item)
                index += 1

            index = 0
            while index < len(tool_specs):
                tool_items.append(tool_specs[index].build_openai_tool())
                index += 1

            payload: dict[str, Any] = dict()
            payload["model"] = self._config.model_name
            payload["instructions"] = system_prompt
            payload["input"] = input_items
            payload["tools"] = tool_items

            url: str = f"{base_url.rstrip('/')}/responses"
            ok_http: bool
            response_obj: dict[str, Any]
            http_error: str
            ok_http, response_obj, http_error = self._http_client.post_json(url, payload)

            if ok_http:
                return parse_openai_responses_payload(response_obj)
            else:
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.HTTP_ERROR,
                    error_message=http_error,
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
        Execute one completion and emit the final text when streaming is unavailable.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tools.
        :param text_delta_callback: Optional text-delta callback.
        :returns: Provider response.
        """
        del text_delta_callback
        del cancellation_check
        return self.complete(system_prompt=system_prompt, messages=messages, tool_specs=tool_specs)


class AnthropicProvider:
    """
    Anthropic Messages API provider.

    :param config: Provider configuration.
    """

    __slots__ = (
        "_config",
        "_http_client",
    )

    def __init__(self, config: ProviderConfig) -> None:
        self._config: ProviderConfig = config
        self._http_client: HTTPClient = HTTPClient(config)

    def complete(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        tool_specs: list[ToolSpec],
    ) -> LLMResponse:
        """
        Execute one Anthropic completion.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tools.
        :returns: Provider response.
        """
        base_url: Optional[str] = self._config.base_url
        payload_messages: list[dict[str, Any]] = list()
        tool_items: list[dict[str, Any]] = list()
        index: int = 0

        if base_url is None:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.INVALID_CONFIGURATION,
                error_message="Anthropic base URL is not configured.",
            )
        else:
            while index < len(messages):
                message_obj: ChatMessage = messages[index]
                item: dict[str, Any] = dict()
                item["role"] = message_obj.role
                item["content"] = message_obj.content
                payload_messages.append(item)
                index += 1

            index = 0
            while index < len(tool_specs):
                tool_items.append(tool_specs[index].build_anthropic_tool())
                index += 1

            payload: dict[str, Any] = dict()
            payload["model"] = self._config.model_name
            payload["system"] = system_prompt
            payload["messages"] = payload_messages
            payload["tools"] = tool_items
            payload["max_tokens"] = 2048

            url: str = f"{base_url.rstrip('/')}/messages"
            ok_http: bool
            response_obj: dict[str, Any]
            http_error: str
            ok_http, response_obj, http_error = self._http_client.post_json(url, payload)

            if ok_http:
                return parse_anthropic_payload(response_obj)
            else:
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.HTTP_ERROR,
                    error_message=http_error,
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
        Execute one completion and emit the final text when streaming is unavailable.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tools.
        :param text_delta_callback: Optional text-delta callback.
        :returns: Provider response.
        """
        del text_delta_callback
        del cancellation_check
        return self.complete(system_prompt=system_prompt, messages=messages, tool_specs=tool_specs)


class OpenAICompatibleProvider:
    """
    OpenAI-compatible provider for Ollama / LM Studio.

    :param config: Provider configuration.
    """

    __slots__ = (
        "_config",
        "_http_client",
    )

    def __init__(self, config: ProviderConfig) -> None:
        self._config: ProviderConfig = config
        self._http_client: HTTPClient = HTTPClient(config)

    def complete(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        tool_specs: list[ToolSpec],
    ) -> LLMResponse:
        """
        Execute one OpenAI-compatible chat completion.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tools.
        :returns: Provider response.
        """
        base_url: Optional[str] = self._config.base_url
        payload_messages: list[dict[str, Any]]
        tool_items: list[dict[str, Any]] = list()
        index: int = 0

        if base_url is None:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.INVALID_CONFIGURATION,
                error_message="OpenAI-compatible base URL is not configured.",
            )
        else:
            payload_messages = build_openai_compatible_messages(
                system_prompt,
                messages,
                provider_tpe=self._config.provider_tpe,
            )

            index = 0
            while index < len(tool_specs):
                tool_items.append(tool_specs[index].build_openai_tool())
                index += 1

            payload: dict[str, Any] = dict()
            payload["model"] = self._config.model_name
            payload["messages"] = payload_messages
            payload["tools"] = tool_items
            payload["tool_choice"] = "auto"
            payload["max_tokens"] = 2048

            url: str = f"{base_url.rstrip('/')}/chat/completions"
            ok_http: bool
            response_obj: dict[str, Any]
            http_error: str
            ok_http, response_obj, http_error = self._http_client.post_json(url, payload)

            if ok_http:
                return parse_openai_compatible_payload(response_obj)
            else:
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.HTTP_ERROR,
                    error_message=http_error,
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
        Execute one completion and emit the final text when streaming is unavailable.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tools.
        :param text_delta_callback: Optional text-delta callback.
        :returns: Provider response.
        """
        base_url: Optional[str] = self._config.base_url
        payload_messages: list[dict[str, Any]]
        tool_items: list[dict[str, Any]] = list()
        payload: dict[str, Any] = dict()
        url: str
        ok_http: bool
        response_obj: Optional[requests.Response]
        http_error: str
        chunk_line: Any
        chunk_text: str
        json_text: str
        chunk_obj: Any
        choices_obj: Any
        choice_obj: Any
        delta_obj: Any
        index: int = 0
        accumulated_text: str = ""
        tool_call_states: list[dict[str, str]] = list()

        if cancellation_check is not None:
            if cancellation_check():
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.CANCELED,
                    error_message="Generation stopped.",
                )
            else:
                pass
        else:
            pass

        if text_delta_callback is None:
            return self.complete(system_prompt=system_prompt, messages=messages, tool_specs=tool_specs)
        else:
            pass

        if base_url is None:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.INVALID_CONFIGURATION,
                error_message="OpenAI-compatible base URL is not configured.",
            )
        else:
            payload_messages = build_openai_compatible_messages(
                system_prompt,
                messages,
                provider_tpe=self._config.provider_tpe,
            )

        while index < len(tool_specs):
            tool_items.append(tool_specs[index].build_openai_tool())
            index += 1

        payload["model"] = self._config.model_name
        payload["messages"] = payload_messages
        payload["tools"] = tool_items
        payload["tool_choice"] = "auto"
        payload["max_tokens"] = 2048
        payload["stream"] = True

        url = f"{base_url.rstrip('/')}/chat/completions"
        ok_http, response_obj, http_error = self._http_client.post_stream(url, payload)

        if ok_http:
            pass
        else:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.HTTP_ERROR,
                error_message=http_error,
            )

        try:
            if response_obj is None:
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.HTTP_ERROR,
                    error_message="OpenAI-compatible streaming response was not available.",
                )
            else:
                for chunk_line in response_obj.iter_lines(decode_unicode=True):
                    if cancellation_check is not None:
                        if cancellation_check():
                            response_obj.close()
                            return LLMResponse(
                                text=accumulated_text,
                                tool_calls=list(),
                                error_code=ProviderErrorCode.CANCELED,
                                error_message="Generation stopped.",
                            )
                        else:
                            pass
                    else:
                        pass

                    if isinstance(chunk_line, bytes):
                        chunk_text = chunk_line.decode("utf-8", errors="ignore").strip()
                    else:
                        if isinstance(chunk_line, str):
                            chunk_text = chunk_line.strip()
                        else:
                            chunk_text = ""

                    if len(chunk_text) == 0:
                        continue
                    else:
                        pass

                    if chunk_text.startswith("data:"):
                        json_text = chunk_text[5:].strip()
                    else:
                        json_text = chunk_text

                    if json_text == "[DONE]":
                        continue
                    else:
                        pass

                    try:
                        chunk_obj = json.loads(json_text)
                    except json.JSONDecodeError:
                        continue

                    choices_obj = chunk_obj.get("choices", None)

                    if isinstance(choices_obj, list) and (len(choices_obj) > 0):
                        choice_obj = choices_obj[0]
                        if isinstance(choice_obj, dict):
                            delta_obj = choice_obj.get("delta", None)

                            if isinstance(delta_obj, dict):
                                text_delta: str
                                text_delta, tool_call_states = apply_openai_compatible_stream_delta(
                                    delta_obj=delta_obj,
                                    tool_call_states=tool_call_states,
                                )

                                if len(text_delta) > 0:
                                    accumulated_text += text_delta
                                    text_delta_callback(text_delta)
                                else:
                                    pass
                            else:
                                pass
                        else:
                            pass
                    else:
                        pass
        except Exception:
            if response_obj is None:
                pass
            else:
                response_obj.close()
            return self.complete(system_prompt=system_prompt, messages=messages, tool_specs=tool_specs)

        if response_obj is None:
            pass
        else:
            response_obj.close()

        return LLMResponse(
            text=accumulated_text,
            tool_calls=build_tool_calls_from_stream_state(tool_call_states),
            error_code=ProviderErrorCode.NONE,
            error_message="",
        )


def build_openai_compatible_messages(
    system_prompt: str,
    messages: list[ChatMessage],
    provider_tpe: ProviderType,
) -> list[dict[str, Any]]:
    """
    Build an OpenAI-compatible message array.

    :param system_prompt: System prompt.
    :param messages: Conversation messages.
    :returns: OpenAI-compatible message array.
    """
    payload_messages: list[dict[str, Any]] = list()
    system_item: dict[str, Any] = dict()
    index: int = 0

    # Keep the system message explicit and first so all backends see the same context.
    system_item["role"] = "system"
    system_item["content"] = system_prompt
    payload_messages.append(system_item)

    # Convert the internal transcript into the shape expected by OpenAI-style APIs.
    while index < len(messages):
        message_obj: ChatMessage = messages[index]
        item: dict[str, Any] = dict()

        if provider_tpe == ProviderType.GEMINI:
            # Gemini's OpenAI-compatible endpoint is stricter on transcript message shape.
            if message_obj.role == "tool":
                item["role"] = "assistant"
                if message_obj.name is None:
                    item["content"] = f"Tool output:\n{message_obj.content}"
                else:
                    item["content"] = f"Tool output ({message_obj.name}):\n{message_obj.content}"
            else:
                if message_obj.role in ("system", "user", "assistant"):
                    item["role"] = message_obj.role
                else:
                    item["role"] = "assistant"
                item["content"] = message_obj.content
        else:
            item["role"] = message_obj.role
            item["content"] = message_obj.content

            # Tool messages may carry the tool name and some local providers can use it.
            if message_obj.name is None:
                pass
            else:
                item["name"] = message_obj.name

        payload_messages.append(item)
        index += 1

    return payload_messages


def resolve_local_llama_model_path(config: ProviderConfig) -> tuple[bool, str, str]:
    """
    Resolve a local GGUF model path from the provider configuration.

    :param config: Provider configuration.
    :returns: Tuple with success flag, resolved model path and error message.
    """
    base_path_raw: Optional[str] = config.base_url
    model_name_raw: str = config.model_name.strip()
    base_path: str
    candidate_path: str
    alternate_path: str

    if base_path_raw is None:
        return False, "", "Local llama.cpp requires a model path or model directory."
    else:
        base_path = os.path.expanduser(base_path_raw.strip())

    if len(base_path) == 0:
        return False, "", "Local llama.cpp requires a model path or model directory."
    else:
        if os.path.isfile(base_path):
            return True, base_path, ""
        else:
            if os.path.isdir(base_path):
                if len(model_name_raw) == 0:
                    return False, "", "Select a model or type a GGUF file name for the chosen directory."
                else:
                    candidate_path = os.path.join(base_path, model_name_raw)
                    if os.path.isfile(candidate_path):
                        return True, candidate_path, ""
                    else:
                        if model_name_raw.endswith(".gguf"):
                            return False, "", f"Model file does not exist: {candidate_path}"
                        else:
                            alternate_path = os.path.join(base_path, f"{model_name_raw}.gguf")
                            if os.path.isfile(alternate_path):
                                return True, alternate_path, ""
                            else:
                                return False, "", f"Model file does not exist: {candidate_path}"
            else:
                return False, "", f"Configured local path does not exist: {base_path}"


def list_local_llama_models(config: ProviderConfig) -> ModelListResult:
    """
    List local GGUF models from a configured path.

    :param config: Provider configuration.
    :returns: Model discovery result.
    """
    base_path_raw: Optional[str] = config.base_url
    base_path: str
    entry_names: list[str]
    model_names: list[str]
    index: int

    if base_path_raw is None:
        return ModelListResult(
            success=False,
            model_names=list(),
            error_message="Local llama.cpp requires a model path or model directory.",
        )
    else:
        base_path = os.path.expanduser(base_path_raw.strip())

    if len(base_path) == 0:
        return ModelListResult(
            success=False,
            model_names=list(),
            error_message="Local llama.cpp requires a model path or model directory.",
        )
    else:
        if os.path.isfile(base_path):
            return ModelListResult(
                success=True,
                model_names=[os.path.basename(base_path)],
                error_message="",
            )
        else:
            if os.path.isdir(base_path):
                try:
                    entry_names = os.listdir(base_path)
                except OSError as exc:
                    return ModelListResult(
                        success=False,
                        model_names=list(),
                        error_message=str(exc),
                    )

                model_names = list()
                index = 0

                # Surface only GGUF files because llama.cpp loads those directly.
                while index < len(entry_names):
                    entry_name: str = entry_names[index]
                    entry_path: str = os.path.join(base_path, entry_name)
                    if os.path.isfile(entry_path) and entry_name.lower().endswith(".gguf"):
                        model_names.append(entry_name)
                    else:
                        pass
                    index += 1

                model_names.sort()

                if len(model_names) > 0:
                    return ModelListResult(
                        success=True,
                        model_names=model_names,
                        error_message="",
                    )
                else:
                    return ModelListResult(
                        success=False,
                        model_names=list(),
                        error_message="No GGUF files were found in the configured directory.",
                    )
            else:
                return ModelListResult(
                    success=False,
                    model_names=list(),
                    error_message=f"Configured local path does not exist: {base_path}",
                )


def import_llama_cpp_llama() -> tuple[bool, Any, str]:
    """
    Import the llama.cpp Python binding lazily.

    :returns: Tuple with success flag, imported Llama class and error message.
    """
    llama_class: Any = None

    # The local provider is optional, so the import stays lazy and recoverable.
    try:
        from llama_cpp import Llama

        llama_class = Llama
        return True, llama_class, ""
    except ImportError:
        return False, None, "llama-cpp-python is not installed."


def apply_openai_compatible_stream_delta(
    delta_obj: dict[str, Any],
    tool_call_states: list[dict[str, str]],
) -> tuple[str, list[dict[str, str]]]:
    """
    Apply one OpenAI-compatible streaming delta.

    :param delta_obj: Delta object from one stream chunk.
    :param tool_call_states: Mutable tool-call state list.
    :returns: Text delta and updated tool-call states.
    """
    text_delta: str = ""
    content_obj: Any = delta_obj.get("content", None)
    tool_calls_obj: Any = delta_obj.get("tool_calls", None)
    index: int = 0

    if isinstance(content_obj, str):
        text_delta = content_obj
    else:
        pass

    if isinstance(tool_calls_obj, list):
        while index < len(tool_calls_obj):
            tool_item: Any = tool_calls_obj[index]
            if isinstance(tool_item, dict):
                tool_index_obj: Any = tool_item.get("index", 0)
                tool_index: int = int(tool_index_obj) if isinstance(tool_index_obj, int) else 0

                while len(tool_call_states) <= tool_index:
                    tool_call_states.append(
                        {
                            "call_id": "",
                            "tool_name": "",
                            "arguments_json": "",
                        }
                    )

                function_obj: Any = tool_item.get("function", None)
                id_obj: Any = tool_item.get("id", None)

                if isinstance(id_obj, str):
                    tool_call_states[tool_index]["call_id"] = id_obj
                else:
                    pass

                if isinstance(function_obj, dict):
                    name_obj: Any = function_obj.get("name", None)
                    arguments_obj: Any = function_obj.get("arguments", None)

                    if isinstance(name_obj, str):
                        tool_call_states[tool_index]["tool_name"] = name_obj
                    else:
                        pass

                    if isinstance(arguments_obj, str):
                        tool_call_states[tool_index]["arguments_json"] += arguments_obj
                    else:
                        pass
                else:
                    pass
            else:
                pass
            index += 1
    else:
        pass

    return text_delta, tool_call_states


def build_tool_calls_from_stream_state(tool_call_states: list[dict[str, str]]) -> list[ToolCall]:
    """
    Build final tool calls from accumulated stream state.

    :param tool_call_states: Accumulated tool-call states.
    :returns: Parsed tool calls.
    """
    tool_calls: list[ToolCall] = list()
    index: int = 0

    while index < len(tool_call_states):
        call_state: dict[str, str] = tool_call_states[index]
        tool_name: str = call_state.get("tool_name", "")
        arguments_json: str = call_state.get("arguments_json", "")
        call_id: str = call_state.get("call_id", "")

        if len(tool_name) > 0:
            if len(call_id) == 0:
                call_id = f"stream_call_{index}"
            else:
                pass

            tool_calls.append(
                ToolCall(
                    call_id=call_id,
                    tool_name=tool_name,
                    arguments_json=arguments_json if len(arguments_json) > 0 else "{}",
                )
            )
        else:
            pass
        index += 1

    return tool_calls


class LocalLlamaCppProvider:
    """
    Local in-process provider backed by llama-cpp-python.

    :param config: Provider configuration.
    """

    __slots__ = (
        "_config",
        "_model_instance",
        "_loaded_model_path",
    )

    def __init__(self, config: ProviderConfig) -> None:
        self._config: ProviderConfig = config
        self._model_instance: Optional[Any] = None
        self._loaded_model_path: Optional[str] = None

    def _ensure_model(self) -> tuple[bool, str]:
        """
        Load the GGUF model lazily if required.

        :returns: Tuple with success flag and error message.
        """
        ok_import: bool
        llama_class: Any
        import_error: str
        ok_path: bool
        model_path: str
        path_error: str

        ok_path, model_path, path_error = resolve_local_llama_model_path(self._config)
        if ok_path:
            pass
        else:
            return False, path_error

        if (self._model_instance is not None) and (self._loaded_model_path == model_path):
            return True, ""
        else:
            ok_import, llama_class, import_error = import_llama_cpp_llama()
            if ok_import:
                pass
            else:
                return False, f"{import_error} Install it and configure a GGUF model path."

            try:
                # Keep the defaults explicit and conservative for desktop usage.
                self._model_instance = llama_class(
                    model_path=model_path,
                    n_ctx=self._config.context_window_tokens,
                    n_gpu_layers=self._config.gpu_layers,
                    verbose=False,
                )
                self._loaded_model_path = model_path
                return True, ""
            except Exception as exc:
                self._model_instance = None
                self._loaded_model_path = None
                return False, str(exc)

    def complete(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        tool_specs: list[ToolSpec],
    ) -> LLMResponse:
        """
        Execute one in-process llama.cpp chat completion.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tools.
        :returns: Provider response.
        """
        ok_model: bool
        model_error: str
        payload_messages: list[dict[str, Any]]
        tool_items: list[dict[str, Any]]
        payload: dict[str, Any]
        response_obj: Any
        index: int

        ok_model, model_error = self._ensure_model()
        if ok_model:
            pass
        else:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.INVALID_CONFIGURATION,
                error_message=model_error,
            )

        payload_messages = build_openai_compatible_messages(
            system_prompt,
            messages,
            provider_tpe=self._config.provider_tpe,
        )
        tool_items = list()
        index = 0

        # Reuse the OpenAI-style tool schema so the local provider stays aligned with the rest.
        while index < len(tool_specs):
            tool_items.append(tool_specs[index].build_openai_tool())
            index += 1

        payload = dict()
        payload["messages"] = payload_messages
        payload["max_tokens"] = self._config.completion_tokens
        payload["temperature"] = self._config.temperature
        payload["top_p"] = self._config.top_p

        if len(self._config.model_name.strip()) > 0:
            payload["model"] = self._config.model_name.strip()
        else:
            pass

        if len(tool_items) > 0:
            payload["tools"] = tool_items
            payload["tool_choice"] = "auto"
        else:
            pass

        try:
            if self._model_instance is None:
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.INVALID_CONFIGURATION,
                    error_message="Local llama.cpp model is not loaded.",
                )
            else:
                response_obj = self._model_instance.create_chat_completion(**payload)
        except Exception as exc:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.HTTP_ERROR,
                error_message=str(exc),
            )

        if isinstance(response_obj, dict):
            return parse_openai_compatible_payload(response_obj)
        else:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.PARSE_ERROR,
                error_message="Local llama.cpp provider returned an invalid response object.",
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
        Execute one in-process llama.cpp streamed chat completion.

        :param system_prompt: System prompt.
        :param messages: Conversation messages.
        :param tool_specs: Available tools.
        :param text_delta_callback: Optional callback for streamed text deltas.
        :returns: Provider response.
        """
        ok_model: bool
        model_error: str
        payload_messages: list[dict[str, Any]]
        tool_items: list[dict[str, Any]]
        payload: dict[str, Any]
        response_stream: Any
        chunk_obj: Any
        index: int
        accumulated_text: str = ""
        tool_call_states: list[dict[str, str]] = list()

        ok_model, model_error = self._ensure_model()
        if ok_model:
            pass
        else:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.INVALID_CONFIGURATION,
                error_message=model_error,
            )

        if cancellation_check is not None:
            if cancellation_check():
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.CANCELED,
                    error_message="Generation stopped.",
                )
            else:
                pass
        else:
            pass

        payload_messages = build_openai_compatible_messages(
            system_prompt,
            messages,
            provider_tpe=self._config.provider_tpe,
        )
        tool_items = list()
        index = 0

        while index < len(tool_specs):
            tool_items.append(tool_specs[index].build_openai_tool())
            index += 1

        payload = dict()
        payload["messages"] = payload_messages
        payload["max_tokens"] = self._config.completion_tokens
        payload["stream"] = True
        payload["temperature"] = self._config.temperature
        payload["top_p"] = self._config.top_p

        if len(self._config.model_name.strip()) > 0:
            payload["model"] = self._config.model_name.strip()
        else:
            pass

        if len(tool_items) > 0:
            payload["tools"] = tool_items
            payload["tool_choice"] = "auto"
        else:
            pass

        try:
            if self._model_instance is None:
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.INVALID_CONFIGURATION,
                    error_message="Local llama.cpp model is not loaded.",
                )
            else:
                response_stream = self._model_instance.create_chat_completion(**payload)
        except Exception:
            return self.complete(
                system_prompt=system_prompt,
                messages=messages,
                tool_specs=tool_specs,
            )

        try:
            for chunk_obj in response_stream:
                if cancellation_check is not None:
                    if cancellation_check():
                        return LLMResponse(
                            text=accumulated_text,
                            tool_calls=list(),
                            error_code=ProviderErrorCode.CANCELED,
                            error_message="Generation stopped.",
                        )
                    else:
                        pass
                else:
                    pass

                if isinstance(chunk_obj, dict):
                    choices_obj: Any = chunk_obj.get("choices", None)

                    if isinstance(choices_obj, list) and (len(choices_obj) > 0):
                        choice_obj: Any = choices_obj[0]

                        if isinstance(choice_obj, dict):
                            delta_obj: Any = choice_obj.get("delta", None)

                            if isinstance(delta_obj, dict):
                                text_delta: str
                                text_delta, tool_call_states = apply_openai_compatible_stream_delta(
                                    delta_obj=delta_obj,
                                    tool_call_states=tool_call_states,
                                )

                                if len(text_delta) > 0:
                                    accumulated_text += text_delta
                                    if text_delta_callback is None:
                                        pass
                                    else:
                                        text_delta_callback(text_delta)
                                else:
                                    pass
                            else:
                                pass
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
        except Exception:
            return self.complete(
                system_prompt=system_prompt,
                messages=messages,
                tool_specs=tool_specs,
            )

        return LLMResponse(
            text=accumulated_text,
            tool_calls=build_tool_calls_from_stream_state(tool_call_states),
            error_code=ProviderErrorCode.NONE,
            error_message="",
        )


def parse_openai_responses_payload(payload: dict[str, Any]) -> LLMResponse:
    """
    Parse an OpenAI Responses payload.

    :param payload: Provider payload.
    :returns: Parsed response.
    """
    output_obj: Any = payload.get("output", None)
    text_parts: list[str] = list()
    tool_calls: list[ToolCall] = list()

    if isinstance(output_obj, list):
        index: int = 0
        while index < len(output_obj):
            item: Any = output_obj[index]
            if isinstance(item, dict):
                item_tpe: Any = item.get("type", None)
                if item_tpe == "message":
                    content_obj: Any = item.get("content", None)
                    if isinstance(content_obj, list):
                        content_index: int = 0
                        while content_index < len(content_obj):
                            content_item: Any = content_obj[content_index]
                            if isinstance(content_item, dict):
                                content_tpe: Any = content_item.get("type", None)
                                text_obj: Any = content_item.get("text", None)
                                if (content_tpe in ("output_text", "text")) and isinstance(text_obj, str):
                                    text_parts.append(text_obj)
                                else:
                                    pass
                            else:
                                pass
                            content_index += 1
                    else:
                        pass
                else:
                    if item_tpe == "function_call":
                        tool_id_obj: Any = item.get("call_id", None)
                        tool_name_obj: Any = item.get("name", None)
                        tool_args_obj: Any = item.get("arguments", None)
                        if isinstance(tool_id_obj, str) and isinstance(tool_name_obj, str):
                            if isinstance(tool_args_obj, str):
                                tool_calls.append(
                                    ToolCall(
                                        call_id=tool_id_obj,
                                        tool_name=tool_name_obj,
                                        arguments_json=tool_args_obj,
                                    )
                                )
                            else:
                                tool_calls.append(
                                    ToolCall(
                                        call_id=tool_id_obj,
                                        tool_name=tool_name_obj,
                                        arguments_json="{}",
                                    )
                                )
                        else:
                            pass
                    else:
                        pass
            else:
                pass
            index += 1

        return LLMResponse(
            text="\n".join(text_parts).strip(),
            tool_calls=tool_calls,
            error_code=ProviderErrorCode.NONE,
            error_message="",
        )
    else:
        return LLMResponse(
            text="",
            tool_calls=list(),
            error_code=ProviderErrorCode.PARSE_ERROR,
            error_message="OpenAI response payload does not contain a valid output list.",
        )



def parse_anthropic_payload(payload: dict[str, Any]) -> LLMResponse:
    """
    Parse an Anthropic Messages payload.

    :param payload: Provider payload.
    :returns: Parsed response.
    """
    content_obj: Any = payload.get("content", None)
    text_parts: list[str] = list()
    tool_calls: list[ToolCall] = list()

    if isinstance(content_obj, list):
        index: int = 0
        while index < len(content_obj):
            item: Any = content_obj[index]
            if isinstance(item, dict):
                item_tpe: Any = item.get("type", None)
                if item_tpe == "text":
                    text_obj: Any = item.get("text", None)
                    if isinstance(text_obj, str):
                        text_parts.append(text_obj)
                    else:
                        pass
                else:
                    if item_tpe == "tool_use":
                        tool_id_obj: Any = item.get("id", None)
                        tool_name_obj: Any = item.get("name", None)
                        tool_input_obj: Any = item.get("input", None)
                        if isinstance(tool_id_obj, str) and isinstance(tool_name_obj, str):
                            if isinstance(tool_input_obj, dict):
                                tool_calls.append(
                                    ToolCall(
                                        call_id=tool_id_obj,
                                        tool_name=tool_name_obj,
                                        arguments_json=json.dumps(tool_input_obj, ensure_ascii=False),
                                    )
                                )
                            else:
                                tool_calls.append(
                                    ToolCall(
                                        call_id=tool_id_obj,
                                        tool_name=tool_name_obj,
                                        arguments_json="{}",
                                    )
                                )
                        else:
                            pass
                    else:
                        pass
            else:
                pass
            index += 1

        return LLMResponse(
            text="\n".join(text_parts).strip(),
            tool_calls=tool_calls,
            error_code=ProviderErrorCode.NONE,
            error_message="",
        )
    else:
        return LLMResponse(
            text="",
            tool_calls=list(),
            error_code=ProviderErrorCode.PARSE_ERROR,
            error_message="Anthropic response payload does not contain a valid content list.",
        )



def parse_openai_compatible_payload(payload: dict[str, Any]) -> LLMResponse:
    """
    Parse an OpenAI-compatible chat-completions payload.

    :param payload: Provider payload.
    :returns: Parsed response.
    """
    choices_obj: Any = payload.get("choices", None)

    if isinstance(choices_obj, list) and (len(choices_obj) > 0):
        first_choice: Any = choices_obj[0]
        if isinstance(first_choice, dict):
            message_obj: Any = first_choice.get("message", None)
            if isinstance(message_obj, dict):
                content_obj: Any = message_obj.get("content", None)
                tool_calls_obj: Any = message_obj.get("tool_calls", None)
                assistant_text: str = ""
                parsed_tool_calls: list[ToolCall] = list()

                if isinstance(content_obj, str):
                    assistant_text = content_obj
                else:
                    assistant_text = ""

                if isinstance(tool_calls_obj, list):
                    index: int = 0
                    while index < len(tool_calls_obj):
                        tool_item: Any = tool_calls_obj[index]
                        if isinstance(tool_item, dict):
                            tool_id_obj: Any = tool_item.get("id", None)
                            function_obj: Any = tool_item.get("function", None)
                            if isinstance(tool_id_obj, str) and isinstance(function_obj, dict):
                                tool_name_obj: Any = function_obj.get("name", None)
                                tool_args_obj: Any = function_obj.get("arguments", None)
                                if isinstance(tool_name_obj, str):
                                    if isinstance(tool_args_obj, str):
                                        parsed_tool_calls.append(
                                            ToolCall(
                                                call_id=tool_id_obj,
                                                tool_name=tool_name_obj,
                                                arguments_json=tool_args_obj,
                                            )
                                        )
                                    else:
                                        parsed_tool_calls.append(
                                            ToolCall(
                                                call_id=tool_id_obj,
                                                tool_name=tool_name_obj,
                                                arguments_json="{}",
                                            )
                                        )
                                else:
                                    pass
                            else:
                                pass
                        else:
                            pass
                        index += 1

                return LLMResponse(
                    text=assistant_text,
                    tool_calls=parsed_tool_calls,
                    error_code=ProviderErrorCode.NONE,
                    error_message="",
                )
            else:
                return LLMResponse(
                    text="",
                    tool_calls=list(),
                    error_code=ProviderErrorCode.PARSE_ERROR,
                    error_message="OpenAI-compatible payload does not contain a valid message object.",
                )
        else:
            return LLMResponse(
                text="",
                tool_calls=list(),
                error_code=ProviderErrorCode.PARSE_ERROR,
                error_message="OpenAI-compatible payload first choice is invalid.",
            )
    else:
        return LLMResponse(
            text="",
            tool_calls=list(),
            error_code=ProviderErrorCode.PARSE_ERROR,
            error_message="OpenAI-compatible payload does not contain valid choices.",
        )



def parse_model_list_payload(payload: dict[str, Any]) -> ModelListResult:
    """
    Parse a provider model-list payload.

    :param payload: Provider payload.
    :returns: Parsed model-list result.
    """
    data_obj: Any = payload.get("data", None)
    model_names: list[str] = list()

    if isinstance(data_obj, list):
        index: int = 0

        # Extract model identifiers in provider order to keep the UI list stable.
        while index < len(data_obj):
            item_obj: Any = data_obj[index]
            if isinstance(item_obj, dict):
                model_id_obj: Any = item_obj.get("id", None)
                if isinstance(model_id_obj, str):
                    model_names.append(model_id_obj)
                else:
                    pass
            else:
                pass
            index += 1

        if len(model_names) > 0:
            return ModelListResult(
                success=True,
                model_names=model_names,
                error_message="",
            )
        else:
            return ModelListResult(
                success=False,
                model_names=list(),
                error_message="Provider returned a model list without string identifiers.",
            )
    else:
        return ModelListResult(
            success=False,
            model_names=list(),
            error_message="Provider model-list payload does not contain a valid data list.",
        )


def list_provider_models(config: ProviderConfig) -> ModelListResult:
    """
    Query the configured provider for the list of available models.

    :param config: Provider configuration.
    :returns: Model discovery result.
    """
    base_url: Optional[str] = config.base_url

    if config.provider_tpe == ProviderType.LOCAL_LLAMA_CPP:
        return list_local_llama_models(config)
    else:
        if base_url is None:
            return ModelListResult(
                success=False,
                model_names=list(),
                error_message="Provider base URL is not configured.",
            )
        else:
            http_client: HTTPClient = HTTPClient(config)
            url: str = f"{base_url.rstrip('/')}/models"
            ok_http: bool
            response_obj: dict[str, Any]
            http_error: str
            ok_http, response_obj, http_error = http_client.get_json(url)

            if ok_http:
                return parse_model_list_payload(response_obj)
            else:
                return ModelListResult(
                    success=False,
                    model_names=list(),
                    error_message=http_error,
                )


def build_provider(config: ProviderConfig) -> LLMProviderProtocol:
    """
    Build the selected provider.

    :param config: Provider configuration.
    :returns: Provider instance.
    """
    provider: LLMProviderProtocol

    if config.provider_tpe == ProviderType.OPENAI:
        provider = OpenAIProvider(config)
    else:
        if config.provider_tpe == ProviderType.ANTHROPIC:
            provider = AnthropicProvider(config)
        else:
            if config.provider_tpe == ProviderType.OPENAI_COMPATIBLE:
                provider = OpenAICompatibleProvider(config)
            else:
                if config.provider_tpe == ProviderType.GEMINI:
                    provider = OpenAICompatibleProvider(config)
                else:
                    if config.provider_tpe == ProviderType.LOCAL_LLAMA_CPP:
                        provider = LocalLlamaCppProvider(config)
                    else:
                        provider = OpenAICompatibleProvider(config)

    return provider
