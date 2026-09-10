# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
VeraGrid AI backend services.
"""

from VeraGrid.AI.mcp_client import McpBackedLLMProvider
from VeraGrid.AI.mcp_client import VeraGridMcpClient
from VeraGrid.AI.ollama import OllamaProcessManager
from VeraGrid.AI.orchestration import ConversationOrchestrator
from VeraGrid.AI.orchestration import ConversationRunResult
from VeraGrid.AI.orchestration import PromptFactory
from VeraGrid.AI.orchestration import VeraGridContext
from VeraGrid.AI.orchestration import sanitize_visible_assistant_text
from VeraGrid.AI.providers import AnthropicProvider
from VeraGrid.AI.providers import HTTPClient
from VeraGrid.AI.providers import LLMProviderProtocol
from VeraGrid.AI.providers import OpenAICompatibleProvider
from VeraGrid.AI.providers import OpenAIProvider
from VeraGrid.AI.providers import build_provider
from VeraGrid.AI.providers import list_provider_models
from VeraGrid.AI.tools import ApplyParameterPatchTool
from VeraGrid.AI.tools import ListBusesTool
from VeraGrid.AI.tools import RunPowerFlowTool
from VeraGrid.AI.tools import build_default_tool_registry
from VeraGrid.AI.types_and_tools import ApprovalPolicy
from VeraGrid.AI.types_and_tools import ChatMessage
from VeraGrid.AI.types_and_tools import LLMResponse
from VeraGrid.AI.types_and_tools import ModelListResult
from VeraGrid.AI.types_and_tools import PendingApproval
from VeraGrid.AI.types_and_tools import ProviderConfig
from VeraGrid.AI.types_and_tools import ProviderErrorCode
from VeraGrid.AI.types_and_tools import ProviderType
from VeraGrid.AI.types_and_tools import ToolCall
from VeraGrid.AI.types_and_tools import ToolErrorCode
from VeraGrid.AI.types_and_tools import ToolExecutionResult
from VeraGrid.AI.types_and_tools import ToolHandlerProtocol
from VeraGrid.AI.types_and_tools import ToolRegistry
from VeraGrid.AI.types_and_tools import ToolRisk
from VeraGrid.AI.types_and_tools import ToolSpec
from VeraGrid.AI.types_and_tools import strip_json_code_fence
from VeraGrid.AI.types_and_tools import try_parse_text_tool_call

__all__: list[str] = list()
__all__.append("AnthropicProvider")
__all__.append("ApplyParameterPatchTool")
__all__.append("ApprovalPolicy")
__all__.append("ChatMessage")
__all__.append("ConversationOrchestrator")
__all__.append("ConversationRunResult")
__all__.append("HTTPClient")
__all__.append("LLMProviderProtocol")
__all__.append("LLMResponse")
__all__.append("ListBusesTool")
__all__.append("McpBackedLLMProvider")
__all__.append("ModelListResult")
__all__.append("OllamaProcessManager")
__all__.append("OpenAICompatibleProvider")
__all__.append("OpenAIProvider")
__all__.append("PendingApproval")
__all__.append("PromptFactory")
__all__.append("ProviderConfig")
__all__.append("ProviderErrorCode")
__all__.append("ProviderType")
__all__.append("RunPowerFlowTool")
__all__.append("ToolCall")
__all__.append("ToolErrorCode")
__all__.append("ToolExecutionResult")
__all__.append("ToolHandlerProtocol")
__all__.append("ToolRegistry")
__all__.append("ToolRisk")
__all__.append("ToolSpec")
__all__.append("VeraGridContext")
__all__.append("VeraGridMcpClient")
__all__.append("build_default_tool_registry")
__all__.append("build_provider")
__all__.append("list_provider_models")
__all__.append("sanitize_visible_assistant_text")
__all__.append("strip_json_code_fence")
__all__.append("try_parse_text_tool_call")
