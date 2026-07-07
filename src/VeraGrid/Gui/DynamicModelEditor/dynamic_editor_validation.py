from __future__ import annotations

import re
from typing import Optional, TYPE_CHECKING

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QScrollArea, QTableWidget, QTableWidgetItem, \
    QHBoxLayout, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.enumerations import VarPowerFlowReferenceType

if TYPE_CHECKING:
    from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI


def collect_block_tree(root_block: Block) -> list[Block]:
    """
    Collect one root block and all nested descendant blocks.

    :param root_block: Root block to traverse.
    :return: Flat block list in pre-order.
    """
    collected_blocks: list[Block] = list([root_block])
    child_block: Block

    for child_block in root_block.children:
        collected_blocks.extend(collect_block_tree(root_block=child_block))

    return collected_blocks


def format_validation_block_label(block: Block) -> str:
    """
    Return one stable validation label for a block.

    :param block: Block to label.
    :return: User-facing label with the block name and uid suffix.
    """
    block_name: str = block.name if block.name else "Unnamed block"
    uid_suffix: str = str(block.uid)[-8:]
    return f"{block_name} [{uid_suffix}]"


def get_var_reference(var: Var) -> VarPowerFlowReferenceType | None:
    """
    Return one power-flow reference carried by a symbolic variable.

    :param var: Candidate symbolic variable.
    :return: Power-flow reference or ``None`` when absent.
    """
    if isinstance(var.ref, VarPowerFlowReferenceType):
        return var.ref
    else:
        return None


def append_vars_to_name_uid_map(name_to_uids: dict[str, set[int]], vars_list: list[Var]) -> None:
    """
    Register one list of variables into the duplicate-name lookup map.

    :param name_to_uids: Mutable mapping from variable name to seen uid set.
    :param vars_list: Variables to register.
    :return: None.
    """
    var: Var
    for var in vars_list:
        uid_set: set[int] = name_to_uids.setdefault(var.name, set())
        uid_set.add(var.uid)


def append_port_vars_to_phase_count(phase_counts: dict[str, int], vars_list: list[Var]) -> None:
    """
    Count visible EMT ports by phase group.

    :param phase_counts: Mutable phase-count mapping.
    :param vars_list: Candidate port variables.
    :return: None.
    """
    var: Var
    for var in vars_list:
        reference: VarPowerFlowReferenceType | None = get_var_reference(var=var)
        phase_name: str | None = get_emt_phase_group(reference=reference)

        if phase_name is not None:
            phase_counts[phase_name] = phase_counts.get(phase_name, 0) + 1
        else:
            pass


def append_missing_port_messages_for_direction(
        missing_port_messages: list[str],
        emt_missing_by_phase: dict[str, list[str]],
        vars_list: list[Var],
        node_uid: int,
        connected_ports: set[tuple[int, int]],
        is_input: bool,
        mode: object,
) -> None:
    """
    Append missing-port labels for one port direction.

    :param missing_port_messages: Mutable flat missing-port message list.
    :param emt_missing_by_phase: Mutable EMT missing-port lookup by phase.
    :param vars_list: Candidate port variables.
    :param node_uid: Diagram node uid.
    :param connected_ports: Connected port lookup set for this direction.
    :param is_input: Whether the candidate list is for inputs.
    :param mode: Current dynamic simulation mode.
    :return: None.
    """
    direction_label: str = "input" if is_input else "output"
    port_index: int = 0
    var: Var
    reference: VarPowerFlowReferenceType | None
    phase_name: str | None
    message: str

    for var in vars_list:
        if (node_uid, port_index) in connected_ports:
            pass
        else:
            message = f"{direction_label} '{var.name}' is not connected"
            reference = get_var_reference(var=var)
            phase_name = get_emt_phase_group(reference=reference)

            if phase_name is not None and str(mode).endswith("EMT"):
                emt_missing_by_phase[phase_name].append(message)
            else:
                missing_port_messages.append(message)

        port_index = port_index + 1


def format_missing_port_detail(input_names: list[str], output_names: list[str]) -> str:
    """
    Format one grouped missing-port detail line.

    :param input_names: Missing input labels.
    :param output_names: Missing output labels.
    :return: Human-readable detail string.
    """
    detail_parts: list[str] = list()

    if len(input_names) > 0:
        detail_parts.append("Inputs: " + ", ".join(input_names))
    else:
        pass

    if len(output_names) > 0:
        detail_parts.append("Outputs: " + ", ".join(output_names))
    else:
        pass

    if len(detail_parts) > 0:
        return " | ".join(detail_parts)
    else:
        return "All connected"


def append_emt_absent_phase_note(detail_parts: list[str], phase_name: str) -> None:
    """
    Append the informational note used for completely absent EMT phases.

    :param detail_parts: Mutable detail fragment list.
    :param phase_name: Phase group label.
    :return: None.
    """
    if phase_name == "N":
        detail_parts.append("the model has no neutral wire")
    else:
        detail_parts.append(f"the model has no phase {phase_name}")


def format_emt_phase_connectivity_detail(
        phase_name: str,
        input_names: list[str],
        output_names: list[str],
        phase_total_port_count: int,
) -> tuple[bool, str]:
    """
    Return the validation state and detail text for one EMT phase group.

    :param phase_name: Phase group label.
    :param input_names: Missing input labels for the phase.
    :param output_names: Missing output labels for the phase.
    :param phase_total_port_count: Total visible ports in that phase.
    :return: ``(ok, detail)`` pair.
    """
    if phase_total_port_count == 0:
        detail_parts: list[str] = list()
        append_emt_absent_phase_note(detail_parts=detail_parts, phase_name=phase_name)
        return True, " | ".join(detail_parts)
    else:
        pass

    if len(input_names) > 0 and len(output_names) > 0:
        detail_parts = list()
        append_emt_absent_phase_note(detail_parts=detail_parts, phase_name=phase_name)
        return True, " | ".join(detail_parts)
    else:
        pass

    if len(input_names) == 0 and len(output_names) == 0:
        if phase_name == "N":
            return True, "the model has this neutral wire"
        else:
            return True, f"the model has this phase {phase_name}"
    else:
        if len(input_names) > 0 and len(output_names) == 0:
            return False, f"inconsistent connection of phase {phase_name}, only I ports are connected"
        else:
            if len(input_names) == 0 and len(output_names) > 0:
                return False, f"inconsistent connection of phase {phase_name}, only V ports are connected"
            else:
                return False, format_missing_port_detail(input_names=input_names, output_names=output_names)


def get_phase_wire_description(phase_name: str) -> str:
    """
    Return one human-facing EMT phase description.

    :param phase_name: Phase group label.
    :return: Human-facing phase description.
    """
    if phase_name == "N":
        return "Neutral"
    elif phase_name == "A":
        return "A"
    elif phase_name == "B":
        return "B"
    elif phase_name == "C":
        return "C"
    else:
        return phase_name


def get_phase_table_label(phase_name: str) -> str:
    """
    Return the validation-table row label for one injection EMT phase.

    :param phase_name: Phase group label.
    :return: Table row label.
    """
    return get_phase_wire_description(phase_name=phase_name)


def get_branch_phase_table_label(side: str, phase_name: str) -> str:
    """
    Return the validation-table row label for one branch-side EMT phase.

    :param side: Branch side identifier.
    :param phase_name: Phase group label.
    :return: Table row label.
    """
    if side == "from":
        return f"{phase_name} bus from"
    else:
        if side == "to":
            return f"{phase_name} bus to"
        else:
            return f"{phase_name} {side}"


def classify_emt_injection_phase_wire_from_refs(
        phase_name: str,
        refs: set[VarPowerFlowReferenceType],
) -> tuple[bool, str]:
    """
    Classify one injection EMT phase from the current editor references.

    :param phase_name: Phase group label.
    :param refs: Current editor interface references.
    :return: ``(ok, detail)`` pair.
    """
    phase_to_inputs: dict[str, list[VarPowerFlowReferenceType]] = {
        "N": [VarPowerFlowReferenceType.v_N],
        "A": [VarPowerFlowReferenceType.v_A],
        "B": [VarPowerFlowReferenceType.v_B],
        "C": [VarPowerFlowReferenceType.v_C],
    }
    phase_to_outputs: dict[str, list[VarPowerFlowReferenceType]] = {
        "N": [VarPowerFlowReferenceType.i_N],
        "A": [VarPowerFlowReferenceType.i_A],
        "B": [VarPowerFlowReferenceType.i_B],
        "C": [VarPowerFlowReferenceType.i_C],
    }
    input_names: list[str] = list()
    output_names: list[str] = list()
    wire_description: str = get_phase_wire_description(phase_name=phase_name)
    input_ref: VarPowerFlowReferenceType
    output_ref: VarPowerFlowReferenceType

    for input_ref in phase_to_inputs.get(phase_name, list()):
        if input_ref in refs:
            pass
        else:
            input_names.append(f"{wire_description} input")

    for output_ref in phase_to_outputs.get(phase_name, list()):
        if output_ref in refs:
            pass
        else:
            output_names.append(f"{wire_description} output")

    phase_total_port_count: int = len(phase_to_inputs.get(phase_name, list())) + len(phase_to_outputs.get(phase_name, list()))
    return format_emt_phase_connectivity_detail(
        phase_name=phase_name,
        input_names=input_names,
        output_names=output_names,
        phase_total_port_count=phase_total_port_count,
    )


def classify_emt_branch_phase_wire_from_refs(
        side: str,
        phase_name: str,
        refs: set[VarPowerFlowReferenceType],
) -> tuple[bool, str]:
    """
    Classify one branch-side EMT phase from the current editor references.

    :param side: Branch side identifier.
    :param phase_name: Phase group label.
    :param refs: Current editor interface references.
    :return: ``(ok, detail)`` pair.
    """
    if side == "from":
        phase_to_inputs: dict[str, list[VarPowerFlowReferenceType]] = {
            "N": [VarPowerFlowReferenceType.vf_N],
            "A": [VarPowerFlowReferenceType.vf_A],
            "B": [VarPowerFlowReferenceType.vf_B],
            "C": [VarPowerFlowReferenceType.vf_C],
        }
        phase_to_outputs: dict[str, list[VarPowerFlowReferenceType]] = {
            "N": [VarPowerFlowReferenceType.if_N],
            "A": [VarPowerFlowReferenceType.if_A],
            "B": [VarPowerFlowReferenceType.if_B],
            "C": [VarPowerFlowReferenceType.if_C],
        }
    elif side == "to":
        phase_to_inputs = {
            "N": [VarPowerFlowReferenceType.vt_N],
            "A": [VarPowerFlowReferenceType.vt_A],
            "B": [VarPowerFlowReferenceType.vt_B],
            "C": [VarPowerFlowReferenceType.vt_C],
        }
        phase_to_outputs = {
            "N": [VarPowerFlowReferenceType.it_N],
            "A": [VarPowerFlowReferenceType.it_A],
            "B": [VarPowerFlowReferenceType.it_B],
            "C": [VarPowerFlowReferenceType.it_C],
        }
    else:
        phase_to_inputs = dict()
        phase_to_outputs = dict()

    input_names: list[str] = list()
    output_names: list[str] = list()
    wire_description: str = get_phase_wire_description(phase_name=phase_name)
    input_ref: VarPowerFlowReferenceType
    output_ref: VarPowerFlowReferenceType

    for input_ref in phase_to_inputs.get(phase_name, list()):
        if input_ref in refs:
            pass
        else:
            input_names.append(f"{wire_description} input")

    for output_ref in phase_to_outputs.get(phase_name, list()):
        if output_ref in refs:
            pass
        else:
            output_names.append(f"{wire_description} output")

    phase_total_port_count: int = len(phase_to_inputs.get(phase_name, list())) + len(phase_to_outputs.get(phase_name, list()))
    return format_emt_phase_connectivity_detail(
        phase_name=phase_name,
        input_names=input_names,
        output_names=output_names,
        phase_total_port_count=phase_total_port_count,
    )


def has_ac_emt_phase_interface_refs(refs: set[VarPowerFlowReferenceType]) -> bool:
    """
    Return whether one EMT injection interface still exposes AC phase refs.

    :param refs: Current root interface references.
    :return: ``True`` when at least one AC phase reference exists.
    """
    phase_ref: VarPowerFlowReferenceType
    ac_phase_refs: tuple[VarPowerFlowReferenceType, ...] = (
        VarPowerFlowReferenceType.v_N,
        VarPowerFlowReferenceType.v_A,
        VarPowerFlowReferenceType.v_B,
        VarPowerFlowReferenceType.v_C,
        VarPowerFlowReferenceType.i_N,
        VarPowerFlowReferenceType.i_A,
        VarPowerFlowReferenceType.i_B,
        VarPowerFlowReferenceType.i_C,
        VarPowerFlowReferenceType.vf_N,
        VarPowerFlowReferenceType.vf_A,
        VarPowerFlowReferenceType.vf_B,
        VarPowerFlowReferenceType.vf_C,
        VarPowerFlowReferenceType.if_N,
        VarPowerFlowReferenceType.if_A,
        VarPowerFlowReferenceType.if_B,
        VarPowerFlowReferenceType.if_C,
        VarPowerFlowReferenceType.vt_N,
        VarPowerFlowReferenceType.vt_A,
        VarPowerFlowReferenceType.vt_B,
        VarPowerFlowReferenceType.vt_C,
        VarPowerFlowReferenceType.it_N,
        VarPowerFlowReferenceType.it_A,
        VarPowerFlowReferenceType.it_B,
        VarPowerFlowReferenceType.it_C,
    )

    for phase_ref in ac_phase_refs:
        if phase_ref in refs:
            return True
        else:
            pass

    return False


def has_ac_emt_branch_side_refs(side: str, refs: set[VarPowerFlowReferenceType]) -> bool:
    """
    Return whether one EMT branch side still exposes AC phase refs.

    :param side: Branch side identifier.
    :param refs: Current root interface references.
    :return: ``True`` when at least one AC phase reference exists for that side.
    """
    if side == "from":
        side_refs: tuple[VarPowerFlowReferenceType, ...] = (
            VarPowerFlowReferenceType.vf_N,
            VarPowerFlowReferenceType.vf_A,
            VarPowerFlowReferenceType.vf_B,
            VarPowerFlowReferenceType.vf_C,
            VarPowerFlowReferenceType.if_N,
            VarPowerFlowReferenceType.if_A,
            VarPowerFlowReferenceType.if_B,
            VarPowerFlowReferenceType.if_C,
        )
    elif side == "to":
        side_refs = (
            VarPowerFlowReferenceType.vt_N,
            VarPowerFlowReferenceType.vt_A,
            VarPowerFlowReferenceType.vt_B,
            VarPowerFlowReferenceType.vt_C,
            VarPowerFlowReferenceType.it_N,
            VarPowerFlowReferenceType.it_A,
            VarPowerFlowReferenceType.it_B,
            VarPowerFlowReferenceType.it_C,
        )
    else:
        side_refs = tuple()

    phase_ref: VarPowerFlowReferenceType
    for phase_ref in side_refs:
        if phase_ref in refs:
            return True
        else:
            pass

    return False


class ValidationRow:
    """
    Row of validation output associated with one block.
    """

    __slots__ = ("_block_label", "_details", "_ok", "_highlight_ports", "_highlight_port_refs", "_highlight_block")

    def __init__(self, block_label: str) -> None:
        """
        Build one validation row.

        :param block_label: Human-readable block label.
        :return: None.
        """
        self._block_label: str = block_label
        self._details: list[str] = list()
        self._ok: bool = False
        self._highlight_ports: set[str] = set()
        self._highlight_port_refs: set[VarPowerFlowReferenceType] = set()
        self._highlight_block: bool = False

    def get_block_label(self) -> str:
        """
        Return the user-facing block label.

        :return: Block label.
        """
        return self._block_label

    def get_details(self) -> list[str]:
        """
        Return the row detail lines.

        :return: Detail lines.
        """
        return self._details

    def add_detail(self, detail: str) -> None:
        """
        Append one validation detail line.

        :param detail: Detail text to append.
        :return: None.
        """
        self._details.append(detail)

    def set_ok(self, val: bool) -> None:
        """
        Store the row status.

        :param val: Whether the row is informationally correct.
        :return: None.
        """
        self._ok = val

    def is_ok(self) -> bool:
        """
        Return whether the row is informationally correct.

        :return: Stored row status.
        """
        return self._ok

    def set_highlight_block(self, val: bool) -> None:
        """
        Store whether the owning block should be highlighted.

        :param val: Whether to highlight the whole block.
        :return: None.
        """
        self._highlight_block = val

    def get_highlight_block(self) -> bool:
        """
        Return whether the owning block should be highlighted.

        :return: Block highlight flag.
        """
        return self._highlight_block

    def add_highlight_port_name(self, port_name: str) -> None:
        """
        Register one port name that should be highlighted.

        :param port_name: Visible port variable name.
        :return: None.
        """
        self._highlight_ports.add(port_name)

    def get_highlight_port_names(self) -> set[str]:
        """
        Return the port names that should be highlighted.

        :return: Highlighted port names.
        """
        return self._highlight_ports

    def add_highlight_port_ref(self, port_ref: VarPowerFlowReferenceType) -> None:
        """
        Register one port reference type that should be highlighted.

        :param port_ref: Semantic power-flow reference.
        :return: None.
        """
        self._highlight_port_refs.add(port_ref)

    def get_highlight_port_refs(self) -> set[VarPowerFlowReferenceType]:
        """
        Return the port reference types that should be highlighted.

        :return: Highlighted port references.
        """
        return self._highlight_port_refs


class ValidationSection:
    """
    Group of validation rows for one validation rule family.
    """

    __slots__ = ("_title", "_rows", "_first_column_title", "_show_issue_label")

    def __init__(self, title: str, first_column_title: str = "Block", show_issue_label: bool = True) -> None:
        """
        Build one validation section.

        :param title: Section title.
        :param first_column_title: First table-column title.
        :param show_issue_label: Whether to show the section issue summary label.
        :return: None.
        """
        self._title: str = title
        self._rows: list[ValidationRow] = list()
        self._first_column_title: str = first_column_title
        self._show_issue_label: bool = show_issue_label

    def get_title(self) -> str:
        """
        Return the section title.

        :return: Title text.
        """
        return self._title

    def get_rows(self) -> list[ValidationRow]:
        """
        Return the section rows.

        :return: Ordered validation rows.
        """
        return self._rows

    def get_first_column_title(self) -> str:
        """
        Return the first table-column title.

        :return: First column title.
        """
        return self._first_column_title

    def get_show_issue_label(self) -> bool:
        """
        Return whether the section should show its issue label.

        :return: Issue-label visibility flag.
        """
        return self._show_issue_label

    def get_or_create_row(self, block_label: str) -> ValidationRow:
        row: ValidationRow
        for row in self._rows:
            if row.get_block_label() == block_label:
                return row
            else:
                pass

        new_row: ValidationRow = ValidationRow(block_label=block_label)
        self._rows.append(new_row)
        return new_row


class ValidationTraversalNode:
    """
    Recursive validation context for one block and its inherited mappings.
    """

    __slots__ = ("_block", "_effective_external_vars", "_children")

    def __init__(self, block: Block, effective_external_vars: set[Var]) -> None:
        self._block: Block = block
        self._effective_external_vars: set[Var] = set(effective_external_vars)
        self._children: list[ValidationTraversalNode] = list()

    def get_block(self) -> Block:
        return self._block

    def get_effective_external_vars(self) -> set[Var]:
        return self._effective_external_vars

    def get_children(self) -> list["ValidationTraversalNode"]:
        return self._children

    def add_child(self, child_node: "ValidationTraversalNode") -> None:
        self._children.append(child_node)


def collect_local_external_vars(block: Block) -> set[Var]:
    """
    Collect the local external-mapping variables defined on one block.

    :param block: Block to inspect.
    :return: Local external variables.
    """
    local_external_vars: set[Var] = set()
    mapped_var: Var | None
    for mapped_var in block.external_mapping.values():
        if isinstance(mapped_var, Var):
            local_external_vars.add(mapped_var)
        else:
            pass
    return local_external_vars


def build_validation_traversal_node(block: Block, inherited_external_vars: set[Var]) -> ValidationTraversalNode:
    """
    Build one recursive validation traversal node from the block hierarchy.

    :param block: Block to convert.
    :param inherited_external_vars: External variables visible from parent levels.
    :return: Recursive traversal node.
    """
    effective_external_vars: set[Var] = set(inherited_external_vars)
    local_external_vars: set[Var] = collect_local_external_vars(block=block)
    effective_external_vars.update(local_external_vars)

    node: ValidationTraversalNode = ValidationTraversalNode(
        block=block,
        effective_external_vars=set(effective_external_vars),
    )

    child_block: Block
    for child_block in block.children:
        child_node: ValidationTraversalNode = build_validation_traversal_node(
            block=child_block,
            inherited_external_vars=set(effective_external_vars),
        )
        node.add_child(child_node=child_node)

    return node


def collect_validation_traversal_list(root_node: ValidationTraversalNode) -> list[ValidationTraversalNode]:
    """
    Flatten one recursive validation traversal tree.

    :param root_node: Root traversal node.
    :return: Flat traversal-node list.
    """
    flat_nodes: list[ValidationTraversalNode] = list([root_node])
    child_node: ValidationTraversalNode
    for child_node in root_node.get_children():
        flat_nodes.extend(collect_validation_traversal_list(root_node=child_node))
    return flat_nodes


def add_validation_detail(section: ValidationSection, block_label: str, detail: str) -> None:
    """
    Append one formatted validation detail to a section.

    :param section: Mutable validation section.
    :param block_label: Human-readable block identifier.
    :param detail: One validation detail for that block.
    :return: None.
    """
    row: ValidationRow = section.get_or_create_row(block_label=block_label)
    row.add_detail(detail=detail)


def add_validation_status_detail(section: ValidationSection, block_label: str, detail: str, ok: bool) -> None:
    """
    Append one formatted validation detail and status to a section.

    :param section: Mutable validation section.
    :param block_label: Human-readable block identifier.
    :param detail: One validation detail for that block.
    :param ok: Whether the row is informationally correct.
    :return: None.
    """
    row: ValidationRow = section.get_or_create_row(block_label=block_label)
    row.add_detail(detail=detail)
    row.set_ok(val=ok)


def add_validation_port_detail(
        section: ValidationSection,
        block_label: str,
        detail: str,
        input_names: list[str],
        output_names: list[str],
        input_refs: list[VarPowerFlowReferenceType] | None = None,
        output_refs: list[VarPowerFlowReferenceType] | None = None,
) -> None:
    """
    Append one port-connectivity detail and store the exact port names to highlight.

    :param section: Mutable validation section.
    :param block_label: Human-readable block identifier.
    :param detail: One validation detail for that block.
    :param input_names: Missing input port names.
    :param output_names: Missing output port names.
    :param input_refs: Missing input port references.
    :param output_refs: Missing output port references.
    :return: None.
    """
    row: ValidationRow = section.get_or_create_row(block_label=block_label)
    row.add_detail(detail=detail)

    port_name: str
    for port_name in input_names:
        row.add_highlight_port_name(port_name=port_name)

    for port_name in output_names:
        row.add_highlight_port_name(port_name=port_name)

    if input_refs is not None:
        port_ref: VarPowerFlowReferenceType
        for port_ref in input_refs:
            row.add_highlight_port_ref(port_ref=port_ref)
    else:
        pass

    if output_refs is not None:
        port_ref: VarPowerFlowReferenceType
        for port_ref in output_refs:
            row.add_highlight_port_ref(port_ref=port_ref)
    else:
        pass


class ValidationSectionDialog(QDialog):
    """
    Dialog showing model-consistency results grouped by validation section.
    """

    __slots__ = ("_section_results", "_show_issues_button")

    def __init__(self, section_results: list[ValidationSection], parent: Optional[QtWidgets.QWidget] = None) -> None:
        """
        Build one validation-results dialog.

        :param section_results: Ordered validation sections to render.
        :param parent: Optional parent widget.
        :return: None.
        """
        super().__init__(parent)
        self._section_results: list[ValidationSection] = section_results
        self.setWindowTitle("Model Consistency Validation")
        self.resize(860, 620)

        layout: QVBoxLayout = QVBoxLayout(self)
        # The outer layout keeps the scroll area and the close button compact so
        # the report can fit more validation content before requiring scrolling.
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        scroll_area: QScrollArea = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll_area)

        scroll_widget: QWidget = QWidget(scroll_area)
        scroll_area.setWidget(scroll_widget)
        scroll_layout: QVBoxLayout = QVBoxLayout(scroll_widget)
        # The inner layout uses tight spacing so each section title stays visually
        # attached to its content and the full report is denser to read.
        scroll_layout.setContentsMargins(6, 6, 6, 6)
        scroll_layout.setSpacing(2)

        intro_label: QLabel = QLabel(
            "Run an informational validation of the edited model structure, mappings, initialization, and port connectivity. "
            "This check reports issues but does not block saving the model."
        )
        intro_label.setWordWrap(True)
        scroll_layout.addWidget(intro_label)
        scroll_layout.addSpacing(2)

        section: ValidationSection
        for section in self._section_results:
            self._add_section_widget(layout=scroll_layout, section=section)

        # Keep the compact validation rows anchored to the top of the scroll
        # area so extra dialog height becomes empty space below the sections.
        scroll_layout.addStretch(1)

        button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, self)
        self._show_issues_button: QtWidgets.QPushButton = button_box.addButton(
            "Show Issues",
            QDialogButtonBox.ButtonRole.ActionRole,
        )
        self._show_issues_button.setToolTip("Show issues in the model")
        self._show_issues_button.setEnabled(self._has_any_issue_rows())
        self._show_issues_button.clicked.connect(self._show_issues_in_model)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _add_section_widget(self, layout: QVBoxLayout, section: ValidationSection) -> None:
        """
        Append one rendered validation section to the dialog layout.

        :param layout: Parent vertical layout receiving the widgets.
        :param section: Validation section to render.
        :return: None.
        """
        rows: list[ValidationRow] = section.get_rows()
        has_issues: bool = len(rows) > 0
        section_header_widget: QWidget = QWidget(self)
        section_header_layout: QHBoxLayout = QHBoxLayout(section_header_widget)
        title_background_color: QColor = section_header_widget.palette().color(QtGui.QPalette.ColorRole.Button)

        # The header row must stay compact and use the active Qt theme background
        # so the collapsed state visually matches the dynamic-editor toolbar style.
        section_header_layout.setContentsMargins(0, 0, 0, 0)
        section_header_layout.setSpacing(0)
        section_header_widget.setStyleSheet(
            f"background-color: {title_background_color.name()}; color: #173042;"
        )
        section_header_widget.setMinimumHeight(0)
        section_header_widget.setMaximumHeight(24)

        # The left control owns the expand/collapse state and shows the section
        # title using the standard Qt arrow affordance.
        title_button: QToolButton = QToolButton(section_header_widget)
        title_button.setText(section.get_title())
        title_button.setCheckable(True)
        title_button.setChecked(False)
        title_button.setArrowType(Qt.ArrowType.RightArrow)
        title_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        title_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        title_button.setContentsMargins(2, 0, 2, 0)
        title_button.setMinimumHeight(16)
        title_button.setMaximumHeight(20)
        title_button.setStyleSheet(
            "border: none; background: transparent; color: #173042; padding-top: 0px; padding-bottom: 0px;"
        )

        # The right status text keeps the collapsed overview readable without
        # requiring the user to expand every validation section.
        status_summary_label: QLabel = QLabel(section_header_widget)
        if has_issues:
            status_summary_label.setText("Issues found")
            status_summary_label.setStyleSheet("color: #b42318; background: transparent;")
        else:
            status_summary_label.setText("All good")
            status_summary_label.setStyleSheet("color: #027a48; background: transparent;")
        status_summary_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        status_summary_label.setContentsMargins(0, 0, 2, 0)
        status_summary_label.setMinimumHeight(16)
        status_summary_label.setMaximumHeight(20)

        section_header_layout.addWidget(title_button)
        section_header_layout.addWidget(status_summary_label)
        layout.addWidget(section_header_widget)

        # The content widget starts collapsed and is toggled only from the header
        # control so the report opens as a compact section summary list.
        section_content_widget: QWidget = QWidget(self)
        section_content_layout: QVBoxLayout = QVBoxLayout(section_content_widget)
        section_content_layout.setContentsMargins(0, 0, 0, 0)
        section_content_layout.setSpacing(0)
        section_content_widget.setVisible(False)

        if len(rows) == 0:
            # A successful section already exposes its status in the collapsed
            # header summary, so the expanded body stays empty instead of
            # repeating the same message.
            pass
        else:
            if section.get_show_issue_label():
                # The warning label is kept, but spacing is reduced so the table is
                # still visible together with the section title in normal cases.
                warning_label: QLabel = QLabel("Issues found in this section")
                warning_label.setStyleSheet("color: #b42318;")
                warning_label.setContentsMargins(4, 0, 4, 0)
                section_content_layout.addWidget(warning_label)
            else:
                pass

            table_widget: QTableWidget = QTableWidget(self)
            table_widget.setColumnCount(2)
            table_widget.setHorizontalHeaderLabels([section.get_first_column_title(), "Details"])
            table_widget.setRowCount(len(rows))
            table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table_widget.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
            table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            table_widget.verticalHeader().setVisible(False)
            table_widget.horizontalHeader().setStretchLastSection(True)
            table_widget.setContentsMargins(0, 0, 0, 0)
            table_widget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            table_widget.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

            row_index: int = 0
            row: ValidationRow
            for row in rows:
                details_text: str = "\n".join(row.get_details())
                block_item: QTableWidgetItem = QTableWidgetItem(row.get_block_label())
                detail_item: QTableWidgetItem = QTableWidgetItem(details_text)
                if row.is_ok():
                    ok_brush: QtGui.QBrush = QtGui.QBrush(QColor("#027a48"))
                    block_item.setForeground(ok_brush)
                    detail_item.setForeground(ok_brush)
                else:
                    error_brush: QtGui.QBrush = QtGui.QBrush(QColor("#b42318"))
                    block_item.setForeground(error_brush)
                    detail_item.setForeground(error_brush)

                table_widget.setItem(row_index, 0, block_item)
                table_widget.setItem(row_index, 1, detail_item)
                row_index = row_index + 1

            table_widget.resizeRowsToContents()
            table_widget.setMinimumHeight(
                table_widget.verticalHeader().length() + table_widget.horizontalHeader().height() + 8)
            table_widget.setMaximumHeight(
                table_widget.verticalHeader().length() + table_widget.horizontalHeader().height() + 8)
            section_content_layout.addWidget(table_widget)

        title_button.toggled.connect(section_content_widget.setVisible)
        title_button.toggled.connect(self._update_section_toggle_arrow)
        layout.addWidget(section_content_widget)
        layout.addSpacing(1)

    def get_section_results(self) -> list[ValidationSection]:
        """
        Return the rendered validation sections.

        :return: Ordered validation sections.
        """
        return self._section_results

    def _has_any_issue_rows(self) -> bool:
        """
        Return whether the dialog contains at least one issue row.

        :return: ``True`` when any section contains one issue row.
        """
        section: ValidationSection

        # The action button is only useful when the validation pipeline found at
        # least one row that can be projected back onto the visible scene.
        for section in self._section_results:
            if len(section.get_rows()) > 0:
                return True
            else:
                pass

        return False

    def _update_section_toggle_arrow(self, expanded: bool) -> None:
        """
        Update one section-header arrow to match its expanded state.

        :param expanded: Whether the controlled section content is visible.
        :return: None.
        """
        sender_button: QObject | None = self.sender()

        # The slot is shared by all section buttons, so the sender must be
        # resolved and checked before mutating the arrow visual state.
        if isinstance(sender_button, QToolButton):
            if expanded:
                sender_button.setArrowType(Qt.ArrowType.DownArrow)
            else:
                sender_button.setArrowType(Qt.ArrowType.RightArrow)
        else:
            pass

    def _show_issues_in_model(self) -> None:
        """
        Request issue highlighting on the owning dynamic editor.

        :return: None.
        """
        parent_widget: QObject | None = self.parent()

        # The dialog is created by the dynamic editor itself. The call remains
        # guarded so the action safely becomes a no-op if the parent changes.
        from VeraGrid.Gui.DynamicModelEditor.dynamic_block_editor import DynamicBlockEditorGUI

        if isinstance(parent_widget, DynamicBlockEditorGUI):
            parent_widget.show_validation_issues_in_model(section_results=self.get_section_results())
            self.accept()
        else:
            pass


def extract_port_names_from_validation_detail(detail: str) -> set[str]:
    """
    Extract the visible port names referenced by one connectivity detail line.

    :param detail: Validation detail string.
    :return: Port names referenced by the message.
    """
    port_names: set[str] = set()
    match_text: str

    # Connectivity details are rendered as comma-separated input/output labels.
    # The highlighter parses those labels so the same validation report can be
    # projected back onto the scene without adding a parallel data structure.
    for match_text in re.findall(r"(?:Inputs|Outputs):\s*([^|]+)", detail):
        raw_name: str
        for raw_name in match_text.split(","):
            cleaned_name: str = raw_name.strip()
            if len(cleaned_name) > 0:
                port_names.add(cleaned_name)
            else:
                pass

    return port_names


def build_validation_row_highlight_metadata(section_results: list[ValidationSection]) -> None:
    """
    Populate per-row scene-highlight metadata from the rendered section details.

    :param section_results: Validation sections to annotate.
    :return: None.
    """
    section: ValidationSection
    for section in section_results:
        row: ValidationRow
        for row in section.get_rows():
            detail: str
            port_names: set[str] = set()

            # Port-connectivity problems map to concrete ports, while all other
            # reported issues are shown at block granularity with a red border.
            if section.get_title() == "Port Connectivity":
                for detail in row.get_details():
                    port_names.update(extract_port_names_from_validation_detail(detail=detail))

                if len(port_names) > 0:
                    port_name: str
                    for port_name in port_names:
                        row.add_highlight_port_name(port_name=port_name)
                else:
                    row.set_highlight_block(val=True)
            else:
                row.set_highlight_block(val=True)


def get_emt_phase_group(reference: VarPowerFlowReferenceType | None) -> str | None:
    """
    Map one EMT interface reference to its phase group.

    :param reference: Variable power-flow reference.
    :return: ``N``, ``A``, ``B``, ``C`` or ``None``.
    """
    if reference in (VarPowerFlowReferenceType.v_N, VarPowerFlowReferenceType.i_N,
                     VarPowerFlowReferenceType.vf_N, VarPowerFlowReferenceType.if_N,
                     VarPowerFlowReferenceType.vt_N, VarPowerFlowReferenceType.it_N):
        return "N"
    elif reference in (VarPowerFlowReferenceType.v_A, VarPowerFlowReferenceType.i_A,
                       VarPowerFlowReferenceType.vf_A, VarPowerFlowReferenceType.if_A,
                       VarPowerFlowReferenceType.vt_A, VarPowerFlowReferenceType.it_A):
        return "A"
    elif reference in (VarPowerFlowReferenceType.v_B, VarPowerFlowReferenceType.i_B,
                       VarPowerFlowReferenceType.vf_B, VarPowerFlowReferenceType.if_B,
                       VarPowerFlowReferenceType.vt_B, VarPowerFlowReferenceType.it_B):
        return "B"
    elif reference in (VarPowerFlowReferenceType.v_C, VarPowerFlowReferenceType.i_C,
                       VarPowerFlowReferenceType.vf_C, VarPowerFlowReferenceType.if_C,
                       VarPowerFlowReferenceType.vt_C, VarPowerFlowReferenceType.it_C):
        return "C"
    else:
        return None
