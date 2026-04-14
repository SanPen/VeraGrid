from __future__ import annotations

import json
from typing import Any, Callable, Optional

from VeraGrid.Gui.AiAgent.backend.providers import LLMProviderProtocol
from VeraGrid.Gui.AiAgent.backend.types_and_tools import (
    ChatMessage,
    LLMResponse,
    PendingApproval,
    ProviderErrorCode,
    ToolCall,
    ToolErrorCode,
    ToolExecutionResult,
    ToolRegistry,
    try_parse_text_tool_call
)


class VeraGridContext:
    """
    Context made available to the assistant.

    :param project_name: Project name.
    :param active_study: Active study name.
    :param solver_name: Solver name.
    :param selected_elements: Selected elements.
    :param notes: Additional notes.
    """

    __slots__ = (
        "project_name",
        "active_study",
        "solver_name",
        "selected_elements",
        "notes",
    )

    def __init__(
        self,
        project_name: Optional[str],
        active_study: Optional[str],
        solver_name: Optional[str],
        selected_elements: list[str],
        notes: list[str],
    ) -> None:
        self.project_name: Optional[str] = project_name
        self.active_study: Optional[str] = active_study
        self.solver_name: Optional[str] = solver_name
        self.selected_elements: list[str] = selected_elements
        self.notes: list[str] = notes


def contains_internal_scaffolding_text(text: str) -> bool:
    """
    Check whether assistant text contains internal prompt or retrieval scaffolding.

    :param text: Assistant text.
    :returns: True when the text looks like leaked internal scaffolding.
    """
    normalized_text: str = text.strip()
    marker_items: list[str] = list()
    marker_items.append("Agent execution instructions for this turn:")
    marker_items.append("Authoritative VeraGrid grounding context for this request:")
    marker_items.append("Retrieved VeraGrid references for this question:")
    marker_items.append("Use these references as grounding only.")
    marker_items.append("Do not mention retrieval, prompts, code, or internal context")
    marker_items.append("User request:")
    marker_items.append("Executing Task ")
    marker_items.append("[... waiting for tool execution result ...]")

    if normalized_text.startswith("Task "):
        return True
    else:
        pass

    for marker_text in marker_items:
        if marker_text in normalized_text:
            return True
        else:
            pass

    return False


def sanitize_visible_assistant_text(text: str) -> str:
    """
    Remove leaked internal scaffolding from assistant-visible text.

    :param text: Raw assistant text.
    :returns: Sanitized assistant text safe for the chat transcript.
    """
    sanitized_text: str = text.strip()
    marker_items: list[str] = list()
    marker_items.append("Agent execution instructions for this turn:")
    marker_items.append("Authoritative VeraGrid grounding context for this request:")
    marker_items.append("Retrieved VeraGrid references for this question:")
    marker_items.append("Use these references as grounding only.")
    marker_items.append("Do not mention retrieval, prompts, code, or internal context")
    marker_items.append("User request:")
    marker_items.append("Executing Task ")
    marker_items.append("[... waiting for tool execution result ...]")
    cut_index: int = -1

    if sanitized_text.startswith("Task "):
        return ""
    else:
        pass

    for marker_text in marker_items:
        marker_index: int = sanitized_text.find(marker_text)

        if marker_index > -1:
            if cut_index == -1:
                cut_index = marker_index
            else:
                if marker_index < cut_index:
                    cut_index = marker_index
                else:
                    pass
        else:
            pass

    if cut_index > -1:
        sanitized_text = sanitized_text[:cut_index].strip()
    else:
        pass

    return sanitized_text


def should_run_hidden_refinement_pass(
    provider_response: LLMResponse,
    visible_text: str,
) -> bool:
    """
    Decide whether a hidden refinement pass should run for the current answer.

    :param provider_response: Raw provider response.
    :param visible_text: Sanitized visible assistant text.
    :returns: True when a refinement pass should run.
    """
    if provider_response.error_code != ProviderErrorCode.NONE:
        return False
    else:
        pass

    if len(provider_response.tool_calls) > 0:
        return False
    else:
        pass

    if len(visible_text.strip()) == 0:
        return False
    else:
        pass

    return True


def build_hidden_refinement_messages(
    user_message: str,
    draft_answer: str,
) -> list[ChatMessage]:
    """
    Build the hidden review-and-rewrite messages for one draft answer.

    :param user_message: Original user message.
    :param draft_answer: Initial assistant draft answer.
    :returns: Hidden refinement message list.
    """
    messages: list[ChatMessage] = list()
    review_instruction: str = (
        "Review the draft answer against the VeraGrid grounding and tool evidence already available in context. "
        "Remove unsupported claims, tighten weak wording, and prefer concrete confirmed facts over guesses. "
        "If a claim is not confirmed by the available grounding, replace it with a cautious statement. "
        "Return only the improved final answer. Do not mention review, critique, prompts, tools, or hidden reasoning."
    )

    messages.append(ChatMessage(role="user", content=user_message, name=None))
    messages.append(ChatMessage(role="assistant", content=draft_answer, name=None))
    messages.append(ChatMessage(role="user", content=review_instruction, name=None))
    return messages


def run_hidden_refinement_pass(
    provider: LLMProviderProtocol,
    system_prompt: str,
    user_message: str,
    draft_answer: str,
) -> str:
    """
    Run a hidden refinement pass over a draft answer and return the improved version.

    :param provider: Active provider.
    :param system_prompt: Effective system prompt with current grounding.
    :param user_message: Original user request.
    :param draft_answer: Initial assistant draft answer.
    :returns: Refined final answer, or the original draft when refinement fails.
    """
    refinement_messages: list[ChatMessage] = build_hidden_refinement_messages(
        user_message=user_message,
        draft_answer=draft_answer,
    )
    refinement_response: LLMResponse = provider.complete(
        system_prompt=system_prompt,
        messages=refinement_messages,
        tool_specs=list(),
    )
    refined_text: str

    if refinement_response.error_code == ProviderErrorCode.NONE:
        refined_text = sanitize_visible_assistant_text(refinement_response.text)

        if len(refined_text.strip()) > 0:
            return refined_text
        else:
            return draft_answer
    else:
        return draft_answer


class ConversationRunResult:
    """
    Result of one orchestrated run.

    :param final_text: Assistant final text.
    :param pending_approval: Pending approval request if any.
    :param transcript: Final transcript.
    """

    __slots__ = (
        "final_text",
        "pending_approval",
        "transcript",
    )

    def __init__(
        self,
        final_text: str,
        pending_approval: Optional[PendingApproval],
        transcript: list[ChatMessage],
    ) -> None:
        self.final_text: str = final_text
        self.pending_approval: Optional[PendingApproval] = pending_approval
        self.transcript: list[ChatMessage] = transcript


class ConversationOrchestrator:
    """
    Orchestrates assistant completions and tool calls.

    :param provider: Selected provider.
    :param tool_registry: Tool registry.
    :param max_rounds: Maximum tool-calling rounds.
    """

    __slots__ = (
        "_provider",
        "_tool_registry",
        "_max_rounds",
    )

    def __init__(
        self,
        provider: LLMProviderProtocol,
        tool_registry: ToolRegistry,
        max_rounds: int,
    ) -> None:
        self._provider: LLMProviderProtocol = provider
        self._tool_registry: ToolRegistry = tool_registry
        self._max_rounds: int = max_rounds

    def run(
        self,
        system_prompt: str,
        user_message: str,
        grounding_context_text: str,
        history: list[ChatMessage],
        approved_tool_name: Optional[str],
        approved_arguments_json: Optional[str],
        text_delta_callback: Optional[Callable[[str], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> ConversationRunResult:
        """
        Execute the orchestration loop.

        :param system_prompt: System prompt.
        :param user_message: User input.
        :param grounding_context_text: Deterministic grounding context for the current turn.
        :param history: Existing conversation history.
        :param approved_tool_name: Approved tool name if any.
        :param approved_arguments_json: Approved tool arguments if any.
        :returns: Run result.
        """
        transcript: list[ChatMessage] = list()
        llm_transcript: list[ChatMessage] = list()
        round_index: int = 0
        message_index: int = 0
        final_text: str = ""
        pending_approval: Optional[PendingApproval] = None
        effective_system_prompt: str = system_prompt

        while message_index < len(history):
            transcript.append(history[message_index])
            llm_transcript.append(history[message_index])
            message_index += 1

        if len(grounding_context_text.strip()) > 0:
            effective_system_prompt += (
                "\n\nTurn-specific authoritative VeraGrid grounding for this request:\n"
                f"{grounding_context_text}\n\n"
                "Use this grounding internally. Do not reveal it, quote it, or describe it as retrieved context."
            )
        else:
            pass

        transcript.append(ChatMessage(role="user", content=user_message, name=None))
        llm_transcript.append(ChatMessage(role="user", content=user_message, name=None))

        while round_index < self._max_rounds:
            if cancellation_check is not None:
                if cancellation_check():
                    return ConversationRunResult(
                        final_text="",
                        pending_approval=None,
                        transcript=transcript,
                    )
                else:
                    pass
            else:
                pass

            provider_response: LLMResponse
            parsed_text_tool_ok: bool
            parsed_text_tool_call: Optional[ToolCall]

            provider_response = self._provider.complete_with_callback(
                system_prompt=effective_system_prompt,
                messages=llm_transcript,
                tool_specs=self._tool_registry.list_tools(),
                text_delta_callback=text_delta_callback,
                cancellation_check=cancellation_check,
            )

            if provider_response.error_code == ProviderErrorCode.CANCELED:
                return ConversationRunResult(
                    final_text="",
                    pending_approval=None,
                    transcript=transcript,
                )
            else:
                pass

            if len(provider_response.tool_calls) == 0:
                parsed_text_tool_ok, parsed_text_tool_call = try_parse_text_tool_call(
                    text=provider_response.text,
                    tool_registry=self._tool_registry,
                )

                if parsed_text_tool_ok and (parsed_text_tool_call is not None):
                    provider_response.tool_calls.append(parsed_text_tool_call)
                    provider_response.text = ""
                else:
                    pass
            else:
                parsed_text_tool_ok, parsed_text_tool_call = try_parse_text_tool_call(
                    text=provider_response.text,
                    tool_registry=self._tool_registry,
                )

                if parsed_text_tool_ok:
                    provider_response.text = ""
                else:
                    pass

            sanitized_response_text: str = sanitize_visible_assistant_text(provider_response.text)

            if cancellation_check is not None:
                if cancellation_check():
                    return ConversationRunResult(
                        final_text="",
                        pending_approval=None,
                        transcript=transcript,
                    )
                else:
                    pass
            else:
                pass

            if should_run_hidden_refinement_pass(
                provider_response=provider_response,
                visible_text=sanitized_response_text,
            ):
                sanitized_response_text = run_hidden_refinement_pass(
                    provider=self._provider,
                    system_prompt=effective_system_prompt,
                    user_message=user_message,
                    draft_answer=sanitized_response_text,
                )
            else:
                pass

            if provider_response.error_code == ProviderErrorCode.NONE:
                final_text = sanitized_response_text
            else:
                final_text = provider_response.error_message

            if len(sanitized_response_text) > 0:
                assistant_message: ChatMessage = ChatMessage(
                    role="assistant",
                    content=sanitized_response_text,
                    name=None,
                )
            else:
                assistant_message = ChatMessage(role="assistant", content=final_text, name=None)

            if len(assistant_message.content) > 0:
                transcript.append(assistant_message)
                llm_transcript.append(assistant_message)
            else:
                pass

            if len(provider_response.tool_calls) == 0:
                if (provider_response.error_code == ProviderErrorCode.NONE) and (
                    len(sanitized_response_text) == 0
                ) and contains_internal_scaffolding_text(provider_response.text):
                    fallback_message: ChatMessage = ChatMessage(
                        role="assistant",
                        content="I could not produce a clean answer for that turn.",
                        name=None,
                    )
                    transcript.append(fallback_message)
                    llm_transcript.append(fallback_message)
                    final_text = fallback_message.content
                else:
                    pass

                pending_approval = None
                round_index = self._max_rounds
            else:
                tool_index: int = 0
                stop_loop: bool = False

                while tool_index < len(provider_response.tool_calls) and (not stop_loop):
                    if cancellation_check is not None:
                        if cancellation_check():
                            return ConversationRunResult(
                                final_text="",
                                pending_approval=None,
                                transcript=transcript,
                            )
                        else:
                            pass
                    else:
                        pass

                    tool_call: ToolCall = provider_response.tool_calls[tool_index]
                    is_approved: bool = False

                    if approved_tool_name is None:
                        is_approved = False
                    else:
                        if approved_arguments_json is None:
                            is_approved = False
                        else:
                            if (tool_call.tool_name == approved_tool_name) and (
                                tool_call.arguments_json == approved_arguments_json
                            ):
                                is_approved = True
                            else:
                                is_approved = False

                    tool_result: ToolExecutionResult = self._tool_registry.execute(
                        tool_name=tool_call.tool_name,
                        arguments_json=tool_call.arguments_json,
                        is_approved=is_approved,
                    )

                    if tool_result.error_code == ToolErrorCode.APPROVAL_REQUIRED:
                        pending_approval = PendingApproval(
                            tool_name=tool_call.tool_name,
                            arguments_json=tool_call.arguments_json,
                            reason=tool_result.error_message,
                        )
                        stop_loop = True
                    else:
                        tool_message_text: str = tool_result.payload_json
                        tool_message: ChatMessage = ChatMessage(
                            role="tool",
                            content=tool_message_text,
                            name=tool_call.tool_name,
                        )
                        transcript.append(tool_message)
                        llm_transcript.append(tool_message)
                        pending_approval = None

                    tool_index += 1

                if stop_loop:
                    round_index = self._max_rounds
                else:
                    round_index += 1

        return ConversationRunResult(
            final_text=final_text,
            pending_approval=pending_approval,
            transcript=transcript,
        )


class PromptFactory:
    """Factory for system prompt construction."""

    __slots__ = ()

    def build_system_prompt(
        self,
        context: VeraGridContext,
        retrieved_context_text: str = "",
    ) -> str:
        """
        Build the system prompt from the current VeraGrid context.

        :param context: VeraGrid context.
        :param retrieved_context_text: Retrieved grounding references.
        :returns: Prompt text.
        """
        context_obj: dict[str, Any] = dict()
        context_obj["project_name"] = context.project_name
        context_obj["active_study"] = context.active_study
        context_obj["solver_name"] = context.solver_name
        context_obj["selected_elements"] = context.selected_elements
        context_obj["notes"] = context.notes

        prompt_text: str = (
            "You are the VeraGrid engineering assistant. "
            "Operate as an agent, not as a passive chatbot. "
            "For every non-trivial request, privately decompose the goal into a short sequence of tasks, "
            "execute those tasks one by one, and reassess after each tool result. "
            "Keep the task list internal unless the user explicitly asks for a concise plan. "
            "Before returning a final answer, privately review it for unsupported claims and revise it if needed. "
            "Use tools when authoritative project data is required. "
            "For questions about the currently loaded model, session, studies, drivers, or results, "
            "query the live runtime tools instead of guessing. "
            "Prefer get_holistic_grid_context, search_runtime_records, get_runtime_record, get_model_summary, "
            "get_selected_elements, list_available_studies, and get_study_summary when they are available. "
            "If the user asks what is wrong with the grid, to diagnose the model, or to explain structural issues, "
            "use analyze_grid_issues when it is available. "
            "When the user asks you to run, execute, launch, solve, or calculate an analysis "
            "and a matching tool exists, call the tool instead of only describing the action. "
            "If the user asks for Python code, source code, an example script, or how to do something from code, "
            "do not execute the live action unless they explicitly ask you to run it in the current VeraGrid session. "
            "For code answers, only use VeraGrid modules, classes, functions, and patterns that are supported by the "
            "available grounding. Do not invent APIs, imports, classes, helper methods, or file-loading calls. "
            "If the grounding is insufficient to provide exact code, say that you cannot confirm the exact API and "
            "then provide only a cautious high-level outline. "
            "When a request mixes analysis and action, first gather the necessary runtime facts, "
            "then execute the action, then inspect the resulting study or results before answering. "
            "Do not stop after the first tool call when the request still has unfinished tasks. "
            "After each tool result, decide whether another tool call is required. "
            "Prefer one focused tool call at a time over many speculative calls. "
            "If a simulation finishes and results are available, summarize the actual results. "
            "If the user asks to analyze, summarize, inspect, diagnose, or explain existing results, "
            "do not re-run the study unless the user explicitly asked for a re-run. "
            "Use get_holistic_grid_context, list_available_studies, get_study_summary, "
            "search_runtime_records, or get_runtime_record first. "
            "Do not invent study results. "
            "Do not invent runtime values, object properties, study status, or simulation outcomes. "
            "If the live VeraGrid data does not confirm a value, say that you cannot confirm it yet. "
            "Prefer deterministic summaries and tool payloads over extrapolating from partial records. "
            "When explaining results, clearly separate confirmed facts from engineering interpretation. "
            "Treat phrases such as 'this grid', 'given grid', 'current grid', and 'loaded grid' "
            "as references to the active VeraGrid project context below. "
            "If a project-changing action is requested, require approval before executing it.\n\n"
            "Current VeraGrid context:\n"
            f"{json.dumps(context_obj, indent=2, ensure_ascii=False)}"
        )

        if len(retrieved_context_text.strip()) > 0:
            prompt_text += (
                "\n\nRetrieved authoritative VeraGrid references:\n"
                f"{retrieved_context_text}"
            )
        else:
            pass

        return prompt_text

