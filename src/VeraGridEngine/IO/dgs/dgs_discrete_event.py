from __future__ import annotations

import re
from enum import Enum
from typing import Dict

from VeraGridEngine.Utils.Symbolic.symbolic import Expr


class DgsDiscreteEventCommand(Enum):
    """Represent a supported PowerFactory discrete equipment command."""

    __slots__ = ()

    Open = "Open"
    Close = "Close"


class DgsDiscreteEventAction:
    """Store one parsed PowerFactory DSL event without executing topology."""

    __slots__ = (
        "_trigger_signal_name",
        "_trigger_expression",
        "_target_slot_name",
        "_event_name",
        "_command",
        "_delay_expression",
        "_source_statement",
        "_root_dgs_id",
        "_target_element_dgs_id",
        "_actuated_device_dgs_id",
        "_actuated_terminal_index",
        "_symbolic_guard_expression",
        "_symbolic_trigger_expression",
        "_symbolic_delay_expression",
    )

    def __init__(
            self,
            trigger_signal_name: str,
            trigger_expression: str,
            target_slot_name: str,
            event_name: str,
            command: DgsDiscreteEventCommand,
            delay_expression: str,
            source_statement: str,
            root_dgs_id: str | None = None,
            target_element_dgs_id: str | None = None,
            actuated_device_dgs_id: str | None = None,
            actuated_terminal_index: int | None = None,
            symbolic_guard_expression: Expr | None = None,
            symbolic_trigger_expression: Expr | None = None,
            symbolic_delay_expression: Expr | None = None,
    ) -> None:
        """
        Build one immutable deferred discrete action.

        :param trigger_signal_name: DSL signal updated by the event statement.
        :param trigger_expression: Raw symbolic trigger expression.
        :param target_slot_name: BlkSlot name resolved later through the manifest.
        :param event_name: Native PowerFactory event display name.
        :param command: Typed open or close command.
        :param delay_expression: Raw delay parameter or expression.
        :param source_statement: Original normalized DSL statement.
        :param root_dgs_id: Owning composite FID when exact resolution is available.
        :param target_element_dgs_id: Direct slot element FID, such as ``StaSwitch``.
        :param actuated_device_dgs_id: Physical equipment FID reached through the cubicle.
        :param actuated_terminal_index: Optional PowerFactory ``obj_bus`` terminal index.
        :param symbolic_guard_expression: Parsed first ``event`` argument.
        :param symbolic_trigger_expression: Parsed trigger/threshold expression.
        :param symbolic_delay_expression: Parsed event delay expression.
        :return: None.
        """
        self._trigger_signal_name: str = trigger_signal_name
        self._trigger_expression: str = trigger_expression
        self._target_slot_name: str = target_slot_name
        self._event_name: str = event_name
        self._command: DgsDiscreteEventCommand = command
        self._delay_expression: str = delay_expression
        self._source_statement: str = source_statement
        self._root_dgs_id: str | None = root_dgs_id
        self._target_element_dgs_id: str | None = target_element_dgs_id
        self._actuated_device_dgs_id: str | None = actuated_device_dgs_id
        self._actuated_terminal_index: int | None = actuated_terminal_index
        self._symbolic_guard_expression: Expr | None = symbolic_guard_expression
        self._symbolic_trigger_expression: Expr | None = symbolic_trigger_expression
        self._symbolic_delay_expression: Expr | None = symbolic_delay_expression

    def get_trigger_signal_name(self) -> str:
        """Return the DSL event output signal."""
        return self._trigger_signal_name

    def get_trigger_expression(self) -> str:
        """Return the raw symbolic trigger expression."""
        return self._trigger_expression

    def get_target_slot_name(self) -> str:
        """Return the target BlkSlot name."""
        return self._target_slot_name

    def get_event_name(self) -> str:
        """Return the native event display name."""
        return self._event_name

    def get_command(self) -> DgsDiscreteEventCommand:
        """Return the typed equipment command."""
        return self._command

    def get_delay_expression(self) -> str:
        """Return the raw delay expression."""
        return self._delay_expression

    def get_source_statement(self) -> str:
        """Return the original normalized DSL statement."""
        return self._source_statement

    def get_root_dgs_id(self) -> str | None:
        """Return the owning composite FID used for exact slot resolution.

        :return: Owning ``ElmComp`` FID or ``None`` when unresolved.
        """
        return self._root_dgs_id

    def get_target_element_dgs_id(self) -> str | None:
        """Return the direct slot element FID, such as a ``StaSwitch`` FID.

        :return: Direct slot-element FID or ``None`` when unresolved.
        """
        return self._target_element_dgs_id

    def get_actuated_device_dgs_id(self) -> str | None:
        """Return the physical equipment FID reached through the target cubicle.

        :return: Physical equipment FID or ``None`` when unresolved.
        """
        return self._actuated_device_dgs_id

    def get_actuated_terminal_index(self) -> int | None:
        """Return the PowerFactory terminal index affected by the action.

        :return: ``obj_bus`` index or ``None`` when not applicable.
        """
        return self._actuated_terminal_index

    def get_symbolic_guard_expression(self) -> Expr | None:
        """Return the parsed first ``event`` argument.

        :return: Symbolic guard expression or ``None`` when parsing was deferred.
        """
        return self._symbolic_guard_expression

    def get_symbolic_trigger_expression(self) -> Expr | None:
        """Return the parsed trigger/threshold expression.

        :return: Symbolic trigger expression or ``None`` when parsing was deferred.
        """
        return self._symbolic_trigger_expression

    def get_symbolic_delay_expression(self) -> Expr | None:
        """Return the parsed delay expression.

        :return: Symbolic delay expression or ``None`` when parsing was deferred.
        """
        return self._symbolic_delay_expression

    def with_symbolic_expressions(
            self,
            guard_expression: Expr,
            trigger_expression: Expr,
            delay_expression: Expr,
    ) -> "DgsDiscreteEventAction":
        """Return an equivalent action carrying parsed symbolic expressions.

        :param guard_expression: Parsed first ``event`` argument.
        :param trigger_expression: Parsed trigger/threshold expression.
        :param delay_expression: Parsed event delay expression.
        :return: New immutable action with executable symbolic expressions.
        """

        return DgsDiscreteEventAction(
            trigger_signal_name=self._trigger_signal_name,
            trigger_expression=self._trigger_expression,
            target_slot_name=self._target_slot_name,
            event_name=self._event_name,
            command=self._command,
            delay_expression=self._delay_expression,
            source_statement=self._source_statement,
            root_dgs_id=self._root_dgs_id,
            target_element_dgs_id=self._target_element_dgs_id,
            actuated_device_dgs_id=self._actuated_device_dgs_id,
            actuated_terminal_index=self._actuated_terminal_index,
            symbolic_guard_expression=guard_expression,
            symbolic_trigger_expression=trigger_expression,
            symbolic_delay_expression=delay_expression,
        )

    def with_target_resolution(
            self,
            root_dgs_id: str,
            target_element_dgs_id: str,
            actuated_device_dgs_id: str,
            actuated_terminal_index: int | None,
    ) -> "DgsDiscreteEventAction":
        """Return an equivalent action carrying an exact physical target chain.

        :param root_dgs_id: Owning composite FID.
        :param target_element_dgs_id: Direct slot element FID.
        :param actuated_device_dgs_id: Physical equipment FID.
        :param actuated_terminal_index: Optional terminal index on that equipment.
        :return: New immutable action with target-resolution metadata.
        """

        # Preserve the parsed command byte-for-byte while adding only identities
        # derived from authoritative DGS pointers.
        return DgsDiscreteEventAction(
            trigger_signal_name=self._trigger_signal_name,
            trigger_expression=self._trigger_expression,
            target_slot_name=self._target_slot_name,
            event_name=self._event_name,
            command=self._command,
            delay_expression=self._delay_expression,
            source_statement=self._source_statement,
            root_dgs_id=root_dgs_id,
            target_element_dgs_id=target_element_dgs_id,
            actuated_device_dgs_id=actuated_device_dgs_id,
            actuated_terminal_index=actuated_terminal_index,
            symbolic_guard_expression=self._symbolic_guard_expression,
            symbolic_trigger_expression=self._symbolic_trigger_expression,
            symbolic_delay_expression=self._symbolic_delay_expression,
        )

    def to_dict(self) -> Dict[str, object]:
        """
        Serialize the action for the optional JSON validation snapshot.

        :return: JSON-compatible typed action fields.
        """
        payload: Dict[str, object] = dict()
        payload["trigger_signal_name"] = self._trigger_signal_name
        payload["trigger_expression"] = self._trigger_expression
        payload["target_slot_name"] = self._target_slot_name
        payload["event_name"] = self._event_name
        payload["command"] = self._command.value
        payload["delay_expression"] = self._delay_expression
        payload["source_statement"] = self._source_statement
        payload["root_dgs_id"] = self._root_dgs_id
        payload["target_element_dgs_id"] = self._target_element_dgs_id
        payload["actuated_device_dgs_id"] = self._actuated_device_dgs_id
        payload["actuated_terminal_index"] = self._actuated_terminal_index
        if self._symbolic_guard_expression is None:
            payload["symbolic_guard_expression"] = None
        else:
            payload["symbolic_guard_expression"] = self._symbolic_guard_expression.to_dict()
        if self._symbolic_trigger_expression is None:
            payload["symbolic_trigger_expression"] = None
        else:
            payload["symbolic_trigger_expression"] = self._symbolic_trigger_expression.to_dict()
        if self._symbolic_delay_expression is None:
            payload["symbolic_delay_expression"] = None
        else:
            payload["symbolic_delay_expression"] = self._symbolic_delay_expression.to_dict()
        return payload


def dgs_discrete_event_action_from_dict(
        payload: Dict[str, object],
) -> DgsDiscreteEventAction | None:
    """
    Restore one deferred action from JSON-compatible fields.

    :param payload: Parsed action dictionary.
    :return: Typed action or ``None`` when a required field is invalid.
    """
    trigger_signal_name_raw: object | None = payload.get(
        "trigger_signal_name",
        None,
    )
    trigger_expression_raw: object | None = payload.get(
        "trigger_expression",
        None,
    )
    target_slot_name_raw: object | None = payload.get("target_slot_name", None)
    event_name_raw: object | None = payload.get("event_name", None)
    command_raw: object | None = payload.get("command", None)
    delay_expression_raw: object | None = payload.get("delay_expression", None)
    source_statement_raw: object | None = payload.get("source_statement", None)
    root_dgs_id_raw: object | None = payload.get("root_dgs_id", None)
    target_element_dgs_id_raw: object | None = payload.get(
        "target_element_dgs_id",
        None,
    )
    actuated_device_dgs_id_raw: object | None = payload.get(
        "actuated_device_dgs_id",
        None,
    )
    actuated_terminal_index_raw: object | None = payload.get(
        "actuated_terminal_index",
        None,
    )
    symbolic_guard_expression_raw: object | None = payload.get(
        "symbolic_guard_expression",
        None,
    )
    symbolic_trigger_expression_raw: object | None = payload.get(
        "symbolic_trigger_expression",
        None,
    )
    symbolic_delay_expression_raw: object | None = payload.get(
        "symbolic_delay_expression",
        None,
    )
    fields_ready: bool = (
        isinstance(trigger_signal_name_raw, str)
        and isinstance(trigger_expression_raw, str)
        and isinstance(target_slot_name_raw, str)
        and isinstance(event_name_raw, str)
        and isinstance(delay_expression_raw, str)
        and isinstance(source_statement_raw, str)
    )
    if not fields_ready:
        return None
    else:
        pass

    symbolic_guard_expression: Expr | None
    symbolic_trigger_expression: Expr | None
    symbolic_delay_expression: Expr | None
    symbolic_payloads_ready: bool = (
        (symbolic_guard_expression_raw is None or isinstance(symbolic_guard_expression_raw, dict))
        and (
            symbolic_trigger_expression_raw is None
            or isinstance(symbolic_trigger_expression_raw, dict)
        )
        and (
            symbolic_delay_expression_raw is None
            or isinstance(symbolic_delay_expression_raw, dict)
        )
    )
    if symbolic_payloads_ready:
        pass
    else:
        return None

    # A malformed optional symbolic tree invalidates only this action. Catalogue
    # restoration can then keep importing all independent models and actions.
    try:
        if isinstance(symbolic_guard_expression_raw, dict):
            symbolic_guard_expression = Expr.from_dict(symbolic_guard_expression_raw)
        else:
            symbolic_guard_expression = None
        if isinstance(symbolic_trigger_expression_raw, dict):
            symbolic_trigger_expression = Expr.from_dict(symbolic_trigger_expression_raw)
        else:
            symbolic_trigger_expression = None
        if isinstance(symbolic_delay_expression_raw, dict):
            symbolic_delay_expression = Expr.from_dict(symbolic_delay_expression_raw)
        else:
            symbolic_delay_expression = None
    except (KeyError, TypeError, ValueError):
        return None

    optional_fields_ready: bool = (
        (root_dgs_id_raw is None or isinstance(root_dgs_id_raw, str))
        and (
            target_element_dgs_id_raw is None
            or isinstance(target_element_dgs_id_raw, str)
        )
        and (
            actuated_device_dgs_id_raw is None
            or isinstance(actuated_device_dgs_id_raw, str)
        )
        and (
            actuated_terminal_index_raw is None
            or (
                isinstance(actuated_terminal_index_raw, int)
                and not isinstance(actuated_terminal_index_raw, bool)
            )
        )
    )
    if optional_fields_ready:
        pass
    else:
        return None

    if command_raw == DgsDiscreteEventCommand.Open.value:
        command: DgsDiscreteEventCommand = DgsDiscreteEventCommand.Open
    else:
        if command_raw == DgsDiscreteEventCommand.Close.value:
            command = DgsDiscreteEventCommand.Close
        else:
            return None

    return DgsDiscreteEventAction(
        trigger_signal_name=trigger_signal_name_raw,
        trigger_expression=trigger_expression_raw,
        target_slot_name=target_slot_name_raw,
        event_name=event_name_raw,
        command=command,
        delay_expression=delay_expression_raw,
        source_statement=source_statement_raw,
        root_dgs_id=root_dgs_id_raw,
        target_element_dgs_id=target_element_dgs_id_raw,
        actuated_device_dgs_id=actuated_device_dgs_id_raw,
        actuated_terminal_index=actuated_terminal_index_raw,
        symbolic_guard_expression=symbolic_guard_expression,
        symbolic_trigger_expression=symbolic_trigger_expression,
        symbolic_delay_expression=symbolic_delay_expression,
    )


def parse_dgs_discrete_event_statement(
        statement: str,
) -> DgsDiscreteEventAction | None:
    """
    Parse one PowerFactory ``event(... create=EvtSwitch ...)`` statement.

    Unknown event families and incomplete commands are returned as ``None`` so
    the caller can retain them in its ordinary unsupported-statement report.

    :param statement: Normalized DSL statement.
    :return: Deferred typed switch action or ``None``.
    """
    event_match: re.Match[str] | None = re.match(
        (
            r"^event\(\s*(?P<signal>[^,]+)\s*,\s*(?P<trigger>[^,]+)\s*,\s*"
            r"(?P<quote>['\"])(?P<command_text>.+)(?P=quote)\s*\)$"
        ),
        statement.strip(),
    )
    if event_match is None:
        return None
    else:
        pass

    command_text: str = event_match.group("command_text").strip()
    command_match: re.Match[str] | None = re.match(
        (
            r"^create=EvtSwitch\s+target=(?P<target>\S+)\s+"
            r"name=(?P<name>.+?)\s+i_switch=(?P<switch>[01])\s+"
            r"dtime=(?P<delay>.+)$"
        ),
        command_text,
    )
    if command_match is None:
        return None
    else:
        pass

    switch_code: int = int(command_match.group("switch"))
    if switch_code == 0:
        command: DgsDiscreteEventCommand = DgsDiscreteEventCommand.Open
    else:
        command = DgsDiscreteEventCommand.Close

    return DgsDiscreteEventAction(
        trigger_signal_name=event_match.group("signal").strip(),
        trigger_expression=event_match.group("trigger").strip(),
        target_slot_name=command_match.group("target").strip(),
        event_name=command_match.group("name").strip(),
        command=command,
        delay_expression=command_match.group("delay").strip(),
        source_statement=statement.strip(),
    )
