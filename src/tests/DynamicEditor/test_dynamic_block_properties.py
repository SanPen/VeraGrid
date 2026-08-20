"""Regression tests for the modal Dynamic Editor block properties workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from PySide6 import QtCore, QtWidgets
import pytest

from VeraGrid.Gui.DynamicModelEditor.dynamic_block_properties import (
    BlockSymbolKind,
    BlockSymbolDraftRow,
    BlockCodeBuffer,
    BlockEquationDraft,
    BlockVariableRenameRequest,
    DaeCodeDiagnostic,
    DynamicBlockPropertiesDialog,
    build_block_symbol_namespace,
    build_equation_code,
    _get_documentation_relative_path,
    parse_equation_code,
    replace_dae_identifier,
    resolve_block_documentation_url,
    serialize_dae_expression,
    synchronize_dae_variable_declarations,
)
from VeraGrid.Gui.DynamicModelEditor.dynamic_equation_pdf import (
    EquationExportEntry,
    EquationExportSection,
    EquationPdfStyle,
    build_equation_pdf_suggested_name,
    build_list_equation_entries,
    build_mapping_equation_entries,
    build_state_equation_entries,
    encode_pdf_literal,
    expand_latex_fractions_for_wrapping,
    expand_latex_square_roots_for_wrapping,
    order_state_differential_variables,
    render_wrapped_equation,
    write_equation_pdf,
)
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_utilities import create_block_of_type
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_utilities import (
    create_default_template_builder,
    get_blocktype2template_builder_dict,
    initialize_template_builder_from_block,
)
from VeraGrid.Gui.DynamicModelEditor.dynamic_latex_renderer import (
    LatexRenderer,
    RenderedEquation,
    RenderedSvgEquation,
    normalize_mathtext_latex,
)
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.enumerations import (
    BlockType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, symbolic_to_string
from VeraGridEngine.Templates.Emt.generator_emt_type_template import get_governor_emt
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template_v2 import get_genqec_rms
from VeraGridEngine.Templates.template_definition import TemplateDefinition
from VeraGridEngine.Templates.BasicBlockCatalog import (
    BasicBlockTemplateDescriptor,
    get_editor_ready_basic_block_catalog_descriptors,
    load_basic_block_catalog_template,
)


def get_qt_application() -> QtWidgets.QApplication:
    """Return the process QApplication required by modal widget tests."""
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        return QtWidgets.QApplication(list())
    else:
        return application


class AliasRenameReceiver(QtCore.QObject):
    """Apply a complete connected-variable rename for a properties test."""

    __slots__ = ("_dialogue", "_new_name")

    def __init__(self,
                 dialogue: DynamicBlockPropertiesDialog,
                 new_name: str) -> None:
        """Store the dialogue and final name used by the synchronous request.

        :param dialogue: Properties dialogue containing the connected rows.
        :param new_name: Final name propagated to the complete alias component.
        :return: None.
        """
        super().__init__()
        self._dialogue: DynamicBlockPropertiesDialog = dialogue
        self._new_name: str = new_name

    @QtCore.Slot(object)
    def apply_rename(self, request: object) -> None:
        """Rename every displayed variable sharing the selected stable UID.

        :param request: Synchronous rename request emitted by Block Properties.
        :return: None.
        """
        if isinstance(request, BlockVariableRenameRequest):
            selected_variable: Var = request.get_variable()
            selected_stable_uid: int = selected_variable.non_mutable_uid
            row_index: int
            for row_index in range(self._dialogue._symbol_model.rowCount()):
                draft_row: BlockSymbolDraftRow | None = self._dialogue._symbol_model.get_row(row_index)
                if draft_row is not None:
                    draft_variable: Var | None = draft_row.get_variable()
                else:
                    draft_variable = None
                if (
                    draft_variable is not None
                    and draft_variable.non_mutable_uid == selected_stable_uid
                ):
                    draft_variable.set_name(self._new_name)
                else:
                    pass
            request.set_result(success=True, new_name=self._new_name)
        else:
            pass


@pytest.fixture(autouse=True)
def close_block_property_dialogues() -> Iterator[None]:
    """Destroy every modal created by a test before the next Qt test starts.

    :yield: Control to the individual test before deterministic Qt teardown.
    """
    yield

    # Qt owns binary children independently from Python's garbage collector.
    # Close every dialogue while its wrapper is still valid, then deliver the
    # deferred-delete events before another test can reuse the application.
    application: QtWidgets.QApplication = get_qt_application()
    top_level_widgets: list[QtWidgets.QWidget] = list(application.topLevelWidgets())
    widget: QtWidgets.QWidget
    for widget in top_level_widgets:
        if isinstance(widget, DynamicBlockPropertiesDialog):
            widget.close()
        else:
            pass
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    application.processEvents()


def build_test_block() -> tuple[Block, Var, Var, Const]:
    """Build a small block with equations and an editable numeric parameter."""
    state_variable: Var = Var("x")
    parameter_variable: Var = Var("gain")
    parameter_constant: Const = Const(2.0, name="gain")
    block: Block = Block(
        name="test_block",
        state_vars=[state_variable],
        state_eqs=[parameter_variable],
        parameters={parameter_variable: parameter_constant},
        init_eqs={state_variable: Const(1.0)},
    )
    return block, state_variable, parameter_variable, parameter_constant


def test_equation_code_roundtrip_preserves_variable_identity() -> None:
    """Dictionary keys parsed from code must reuse the block's existing Vars."""
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    _unused_parameter_variable: Var = parameter_variable
    _unused_parameter_constant: Const = parameter_constant

    code: str = build_equation_code(block)
    draft: BlockEquationDraft = parse_equation_code(code, build_block_symbol_namespace(block))
    initialization_keys: list[Var] = list(draft.get_init_eqs().keys())

    assert "state_vars = [x]" in code
    assert "algebraic_vars = []" in code
    assert "diff_vars = []" in code
    assert "State equations follow the order of state_vars" in code
    assert "Write each equation as a residual equal to zero" in code
    assert len(initialization_keys) == 1
    assert initialization_keys[0] is state_variable
    assert symbolic_to_string(draft.get_state_eqs()[0]) == "gain"
    state_declaration: list[Var] | None = draft.get_variable_declaration("state_vars")
    assert state_declaration == list([state_variable])


def test_dae_identifier_rename_updates_only_complete_symbol_tokens() -> None:
    """Variable renames must preserve comments and longer symbol names."""
    source_code: str = "state_vars = [x, x_ref]\nstate_eqs = [x + x_ref]\n# x remains explanatory"

    renamed_code: str = replace_dae_identifier(source_code, "x", "speed")

    assert "state_vars = [speed, x_ref]" in renamed_code
    assert "state_eqs = [speed + x_ref]" in renamed_code
    assert "# x remains explanatory" in renamed_code


def test_dialogue_rename_updates_each_connected_local_name_in_dae_code() -> None:
    """One shared stable UID must not hide distinct old names during rename."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    source_variable: Var = Var("const_CONST_1")
    connected_variable: Var = Var(
        "connected_signal",
        non_mutable_uid=source_variable.non_mutable_uid,
    )
    source_block: Block = Block(
        name="CONST_1",
        algebraic_vars=list((source_variable,)),
        algebraic_eqs=list((source_variable - Const(1.0),)),
    )
    connected_block: Block = Block(
        name="GAIN_1",
        algebraic_vars=list((connected_variable,)),
        algebraic_eqs=list((connected_variable - Const(2.0),)),
    )
    root_block: Block = Block(
        name="generic",
        children=list((source_block, connected_block)),
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        root_block,
        "CUSTOM",
        VarFactory(),
    )
    rename_receiver: AliasRenameReceiver = AliasRenameReceiver(dialogue, "k1")
    dialogue.variableRenameRequested.connect(rename_receiver.apply_rename)

    source_proxy_row: int | None = None
    proxy_row: int
    for proxy_row in range(dialogue._variable_symbol_proxy.rowCount()):
        displayed_name: object = dialogue._variable_symbol_proxy.index(proxy_row, 1).data()
        if displayed_name == "const_CONST_1":
            source_proxy_row = proxy_row
        else:
            pass
    assert source_proxy_row is not None

    dialogue._symbol_table.selectRow(source_proxy_row)
    dialogue._rename_selected_symbol(dialogue._symbol_table)

    assert source_variable.name == "k1"
    assert connected_variable.name == "k1"
    buffer_codes: list[str] = list()
    equation_buffer: BlockCodeBuffer
    for equation_buffer in dialogue._equation_buffers:
        buffer_codes.append(equation_buffer.get_code())
    combined_code: str = "\n".join(buffer_codes)
    assert "const_CONST_1" not in combined_code
    assert "connected_signal" not in combined_code
    assert "algebraic_vars = [k1]" in combined_code
    assert all(
        dialogue._symbol_model.index(row_index, 1).data() == "k1"
        for row_index in range(dialogue._symbol_model.rowCount())
    )
    dialogue.close()


def test_variable_declaration_synchronization_preserves_other_dae_source() -> None:
    """Managed declarations may change without rewriting equations or comments."""
    source_code: str = (
        "state_vars = [\n    old_x,\n]\n"
        "algebraic_vars = []\n"
        "diff_vars = []\n\n"
        "state_eqs = [\n    # User equation comment\n    old_x,\n]\n"
    )

    updated_code: str = synchronize_dae_variable_declarations(
        code=source_code,
        state_names=list(("old_x", "new_x",)),
        algebraic_names=list(("new_y",)),
        differential_names=list(("d_new_x",)),
    )

    assert "state_vars = [old_x, new_x]" in updated_code
    assert "algebraic_vars = [new_y]" in updated_code
    assert "diff_vars = [d_new_x]" in updated_code
    assert "# User equation comment\n    old_x," in updated_code


def test_equation_code_removes_only_redundant_root_parentheses() -> None:
    """DAE source must stay readable without changing expression precedence."""
    state_variable: Var = Var("x")
    input_variable: Var = Var("input_signal")
    divisor_variable: Var = Var("divisor")
    expression: Expr = (state_variable - input_variable) / divisor_variable
    block: Block = Block(
        name="precedence_test",
        state_vars=[state_variable],
        state_eqs=[expression],
        in_vars=[input_variable],
        parameters={divisor_variable: Const(2.0, name="divisor")},
    )

    code: str = build_equation_code(block)
    assert "    (x - input_signal) / divisor," in code
    assert "    ((x - input_signal) / divisor)," not in code
    assert serialize_dae_expression(expression) == "(x - input_signal) / divisor"

    draft: BlockEquationDraft = parse_equation_code(
        code,
        build_block_symbol_namespace(block),
    )
    assert symbolic_to_string(draft.get_state_eqs()[0]) == symbolic_to_string(expression)


def test_dialogue_footer_only_contains_apply_changes() -> None:
    """The native title-bar cross must be the only explicit close control."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    _unused_state_variable: Var = state_variable
    _unused_parameter_variable: Var = parameter_variable
    _unused_parameter_constant: Const = parameter_constant
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        VarFactory(),
    )

    assert dialogue.ui.apply_button.text() == "Apply changes"
    assert dialogue.findChild(QtWidgets.QPushButton, "close_button") is None
    assert dialogue.ui.button_layout.count() == 2
    dialogue.close()


@pytest.mark.parametrize(
    "invalid_code",
    [
        "import os",
        "state_eqs = []\nalgebraic_eqs = []\ninit_eqs = {}",
        (
            "state_eqs = []\n"
            "algebraic_eqs = []\n"
            "differential_eqs = []\n"
            "init_eqs = {}\n"
            "diff_init_eqs = {}"
        ),
        (
            "state_eqs = [unknown]\n"
            "algebraic_eqs = []\n"
            "init_eqs = {}\n"
            "diff_init_eqs = {}"
        ),
    ],
)
def test_equation_code_rejects_programs_outside_supported_dae_language(invalid_code: str) -> None:
    """The DAE editor is parsed as data and never accepts arbitrary Python."""
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    _unused_state_variable: Var = state_variable
    _unused_parameter_variable: Var = parameter_variable
    _unused_parameter_constant: Const = parameter_constant

    with pytest.raises(ValueError):
        parse_equation_code(invalid_code, build_block_symbol_namespace(block))


def test_invalid_dialog_draft_does_not_mutate_block() -> None:
    """A failed Apply must leave all symbolic and numeric source values untouched."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    original_state_equation: object = block.state_eqs[0]
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "GENERIC", VarFactory())
    assert dialogue._tabs.count() == 3
    assert dialogue._tabs.tabText(0) == "General options"
    assert dialogue._tabs.tabText(1) == "DAE model"
    assert dialogue._tabs.tabText(2) == "Runtime logic"
    assert dialogue._tabs.tabIcon(2).isNull()
    assert dialogue._block_info_button.isEnabled()
    assert "original predefined library block" in dialogue._block_info_button.toolTip()
    assert "may differ" in dialogue._block_info_button.toolTip()
    assert dialogue._block_info_button.sizePolicy().horizontalPolicy() == (
        QtWidgets.QSizePolicy.Policy.Fixed
    )
    assert dialogue._block_info_button.width() == dialogue._block_info_button.sizeHint().width()
    assert dialogue._block_info_button.width() < 180
    assert dialogue._dae_editor.get_line_number_area_width() > 0
    dialogue._dae_editor.setPlainText("state_eqs = [")
    assert dialogue._dae_editor.get_diagnostics() == list()
    dialogue._validate_code_button.click()
    assert len(dialogue._dae_editor.get_diagnostics()) == 1
    assert "closed" in dialogue._dae_editor.get_diagnostics()[0].get_message().lower()

    dialogue.apply_changes()

    assert block.state_eqs[0] is original_state_equation
    assert parameter_constant.value == 2.0
    dialogue.close()


def test_valid_dialog_draft_applies_equations_and_parameters_together() -> None:
    """A valid Apply updates the working block and emits its stable UID."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    emitted_uids: list[int] = list()
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "GENERIC", VarFactory())
    value_index = dialogue._parameter_model.index(0, 2)
    assert dialogue._parameter_model.setData(value_index, "3.5")
    dialogue._dae_editor.setPlainText(
        "state_eqs = [gain + 1]\n"
        "algebraic_eqs = []\n"
        "init_eqs = {x: 0}\n"
        "diff_init_eqs = {}"
    )
    dialogue.blockApplied.connect(emitted_uids.append)

    dialogue.apply_changes()

    assert parameter_constant.value == 3.5
    assert symbolic_to_string(block.state_eqs[0]) == "(gain + 1)"
    assert list(block.init_eqs.keys())[0] is state_variable
    assert emitted_uids == [block.uid]
    dialogue.close()


def test_governor_mapping_symbols_are_available_to_dae_parser() -> None:
    """Mapped symbols such as Pm_ref must parse even when not listed as events."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block = get_governor_emt(var_factory).block
    namespace: dict[str, Expr] = build_block_symbol_namespace(block)

    assert "Pm_ref" in namespace
    parse_equation_code(build_equation_code(block), namespace)

    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GOV_EMT",
        var_factory,
    )
    dialogue.apply_changes()
    assert "Nothing was applied" not in dialogue._status_label.text()
    dialogue.close()


def test_recursive_dialog_selects_child_with_equations_and_labels_output_role() -> None:
    """Composite blocks expose child equations and keep primary/output roles separate."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    child: Block = get_governor_emt(var_factory).block
    root: Block = Block(name="complete", children=[child])
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(root, "CUSTOM", var_factory)

    assert dialogue._equation_buffers[dialogue._active_equation_buffer_index].get_block() is child
    assert "Pm_ref" in dialogue._dae_editor.toPlainText()

    tm_row: int | None = None
    row_index: int
    for row_index in range(dialogue._symbol_model.rowCount()):
        if dialogue._symbol_model.index(row_index, 1).data() == "Tm":
            tm_row = row_index
        else:
            pass
    assert tm_row is not None
    assert dialogue._symbol_model.index(tm_row, 2).data() == BlockSymbolKind.ALGEBRAIC.value
    assert dialogue._symbol_model.index(tm_row, 3).data(
        QtCore.Qt.ItemDataRole.CheckStateRole
    ) == QtCore.Qt.CheckState.Checked

    dialogue._new_symbol_owner.setCurrentIndex(1)
    dialogue._new_symbol_name.setText("child_probe")
    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.ALGEBRAIC.value)
    dialogue.add_staged_symbol()

    # A newly staged algebraic variable is not a complete model until its
    # equation is added. Apply must reject that intermediate state without
    # mutating the live child block.
    dialogue.apply_changes()
    assert all(variable.name != "child_probe" for variable in child.algebraic_vars)
    assert "algebraic variables" in dialogue._dae_editor.toolTip()

    equation_code: str = dialogue._dae_editor.toPlainText()
    equation_code = equation_code.replace(
        "algebraic_vars = [y2_3_gov, Tm]",
        "algebraic_vars = [y2_3_gov, Tm, child_probe]",
        1,
    )
    equation_code = equation_code.replace(
        "algebraic_eqs = [",
        "algebraic_eqs = [\n    child_probe,",
        1,
    )
    dialogue._dae_editor.setPlainText(equation_code)
    dialogue.apply_changes()

    assert [variable.name for variable in child.algebraic_vars][-1] == "child_probe"
    assert all(variable.name != "child_probe" for variable in root.algebraic_vars)
    dialogue.close()


def test_staged_symbol_is_created_only_when_apply_is_pressed() -> None:
    """Staged variables validate in code before Apply and can independently be outputs."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block = Block(name="editable")
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "GENERIC", var_factory)
    dialogue._new_symbol_name.setText("new_output")
    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.ALGEBRAIC.value)
    dialogue._new_symbol_exported.setChecked(True)

    dialogue.add_staged_symbol()
    assert len(block.algebraic_vars) == 0
    assert len(block.out_vars) == 0

    dialogue._dae_editor.setPlainText(
        "state_eqs = []\n"
        "algebraic_eqs = [new_output - 1]\n"
        "init_eqs = {}\n"
        "diff_init_eqs = {}"
    )
    dialogue._validate_code_button.click()
    assert dialogue._status_label.text() == "DAE code is valid."
    assert dialogue._dae_editor.get_diagnostics() == list()

    dialogue.apply_changes()
    assert [variable.name for variable in block.algebraic_vars] == ["new_output"]
    assert block.out_vars[0] is block.algebraic_vars[0]
    dialogue.close()


def test_new_state_derivative_is_visible_and_preserves_its_base_variable() -> None:
    """Creating a state derivative must stage and apply a visible differential row."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block = Block(name="editable_state")
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        var_factory,
    )
    dialogue._new_symbol_name.setText("d111")
    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.STATE.value)
    dialogue._new_state_derivative.setChecked(True)

    dialogue.add_staged_symbol()

    staged_variable_names: list[str] = list()
    proxy_row: int
    for proxy_row in range(dialogue._variable_symbol_proxy.rowCount()):
        name_index: QtCore.QModelIndex = dialogue._variable_symbol_proxy.index(proxy_row, 1)
        staged_variable_names.append(str(name_index.data()))
    assert staged_variable_names == ["d111", "d_d111"]
    assert dialogue._variable_symbol_proxy.index(1, 2).data() == BlockSymbolKind.DIFFERENTIAL.value
    assert block.state_vars == list()
    assert block.diff_vars == list()

    # The state equation stores the RHS. The separately staged derivative is
    # the corresponding LHS identity and therefore needs no extra equation.
    dialogue._dae_editor.setPlainText(
        "state_eqs = [0]\n"
        "algebraic_eqs = []\n"
        "init_eqs = {}\n"
        "diff_init_eqs = {}"
    )
    dialogue.apply_changes()

    assert [variable.name for variable in block.state_vars] == ["d111"]
    assert [variable.name for variable in block.diff_vars] == ["d_d111"]
    assert block.diff_vars[0].base_var is block.state_vars[0]
    assert block.state_vars[0].diff_var is block.diff_vars[0]
    assert [
        str(dialogue._variable_symbol_proxy.index(proxy_row, 1).data())
        for proxy_row in range(dialogue._variable_symbol_proxy.rowCount())
    ] == ["d111", "d_d111"]
    dialogue.close()


def test_new_variables_immediately_update_dae_variable_declarations() -> None:
    """Adding table rows must immediately synchronize the visible DAE declarations."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block = Block(name="automatic_declarations")
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        var_factory,
    )

    dialogue._new_symbol_name.setText("speed")
    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.STATE.value)
    dialogue._new_state_derivative.setChecked(True)
    dialogue.add_staged_symbol()

    state_code: str = dialogue._dae_editor.toPlainText()
    assert "state_vars = [speed]" in state_code
    assert "algebraic_vars = []" in state_code
    assert "diff_vars = [d_speed]" in state_code
    assert "# State equations follow the order of state_vars" in state_code

    dialogue._new_symbol_name.setText("torque")
    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.ALGEBRAIC.value)
    dialogue.add_staged_symbol()

    algebraic_code: str = dialogue._dae_editor.toPlainText()
    assert "state_vars = [speed]" in algebraic_code
    assert "algebraic_vars = [torque]" in algebraic_code
    assert "diff_vars = [d_speed]" in algebraic_code

    speed_proxy_row: int | None = None
    proxy_row: int
    for proxy_row in range(dialogue._variable_symbol_proxy.rowCount()):
        if dialogue._variable_symbol_proxy.index(proxy_row, 1).data() == "speed":
            speed_proxy_row = proxy_row
        else:
            pass
    assert speed_proxy_row is not None
    dialogue._symbol_table.selectRow(speed_proxy_row)
    dialogue._delete_selected_symbol(dialogue._symbol_table)
    staged_removal_code: str = dialogue._dae_editor.toPlainText()
    assert "state_vars = []" in staged_removal_code
    assert "algebraic_vars = [torque]" in staged_removal_code
    assert "diff_vars = []" in staged_removal_code
    dialogue.close()


def test_deleted_variables_immediately_update_dae_variable_declarations() -> None:
    """State deletion cascades to its derivative, but not in the reverse direction."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    speed_variable: Var = Var("speed")
    speed_differential: Var = Var("d_speed", base_var=speed_variable)
    angle_variable: Var = Var("angle")
    angle_differential: Var = Var("d_angle", base_var=angle_variable)
    algebraic_variable: Var = Var("torque")
    block: Block = Block(
        name="deleted_declarations",
        state_vars=list((speed_variable, angle_variable,)),
        state_eqs=list((speed_variable, angle_variable,)),
        algebraic_vars=list((algebraic_variable,)),
        algebraic_eqs=list((algebraic_variable,)),
        diff_vars=list((speed_differential, angle_differential,)),
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        var_factory,
    )

    names_to_remove: tuple[str, ...] = ("d_speed", "angle", "torque", "speed")
    expected_declarations: tuple[str, ...] = (
        "diff_vars = [d_angle]",
        "state_vars = [speed]",
        "algebraic_vars = []",
        "state_vars = []",
    )
    removal_index: int
    for removal_index in range(len(names_to_remove)):
        target_name: str = names_to_remove[removal_index]
        target_proxy_row: int | None = None
        proxy_row: int
        for proxy_row in range(dialogue._variable_symbol_proxy.rowCount()):
            if dialogue._variable_symbol_proxy.index(proxy_row, 1).data() == target_name:
                target_proxy_row = proxy_row
            else:
                pass
        assert target_proxy_row is not None
        dialogue._symbol_table.selectRow(target_proxy_row)
        dialogue._delete_selected_symbol(dialogue._symbol_table)
        updated_code: str = dialogue._dae_editor.toPlainText()
        assert expected_declarations[removal_index] in updated_code
        if target_name == "d_speed":
            assert "state_vars = [speed, angle]" in updated_code
        elif target_name == "angle":
            assert "diff_vars = []" in updated_code
        else:
            pass

    final_code: str = dialogue._dae_editor.toPlainText()
    assert "state_vars = []" in final_code
    assert "algebraic_vars = []" in final_code
    assert "diff_vars = []" in final_code
    assert "state_eqs = [" in final_code
    assert "algebraic_eqs = [" in final_code
    dialogue.close()


def test_new_input_is_applied_without_offering_external_mapping() -> None:
    """A user-created input must become a port and never request a PF mapping."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block | None = create_block_of_type(
        var_factory,
        BlockType.PI_CURRENT_CONTROLLER,
        "PI_CURRENT_CONTROLLER_test",
    )
    assert isinstance(block, Block)
    initial_input_count: int = len(block.in_vars)
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        BlockType.PI_CURRENT_CONTROLLER.name,
        var_factory,
    )
    dialogue._new_symbol_name.setText("additional_input")
    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.INPUT.value)

    assert dialogue._new_external_reference_label.isHidden()
    assert dialogue._new_external_reference.isHidden()
    dialogue.add_staged_symbol()
    dialogue.apply_changes()

    assert "Changes applied" in dialogue._status_label.text()
    assert len(block.in_vars) == initial_input_count + 1
    assert block.in_vars[-1].name == "additional_input"
    assert all(mapped_variable is not block.in_vars[-1] for mapped_variable in block.external_mapping.values())
    dialogue.close()


def test_add_symbol_fields_keep_one_width_across_symbol_categories() -> None:
    """Optional variable and parameter fields must share the form field column."""
    application: QtWidgets.QApplication = get_qt_application()
    var_factory: VarFactory = VarFactory()
    block: Block = Block(name="field_widths")
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        var_factory,
    )
    dialogue.resize(900, 700)
    dialogue.show()
    dialogue._tabs.setCurrentIndex(1)
    application.processEvents()

    stable_fields: tuple[QtWidgets.QWidget, ...] = (
        dialogue._new_symbol_owner,
        dialogue._new_symbol_name,
        dialogue._new_symbol_category,
        dialogue._new_symbol_kind,
    )
    dialogue._new_symbol_category.setCurrentText("Variables")
    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.INPUT.value)
    application.processEvents()
    variable_vertical_geometries: List[tuple[int, int]] = list()
    stable_field: QtWidgets.QWidget
    for stable_field in stable_fields:
        variable_position: QtCore.QPoint = stable_field.mapTo(
            dialogue,
            QtCore.QPoint(0, 0),
        )
        variable_vertical_geometries.append((variable_position.y(), stable_field.height()))

    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.STATE.value)
    application.processEvents()
    shared_field_geometry: tuple[int, int] = (
        dialogue._new_symbol_owner.x(),
        dialogue._new_symbol_owner.width(),
    )
    variable_fields: tuple[QtWidgets.QWidget, ...] = (
        dialogue._new_symbol_name,
        dialogue._new_symbol_category,
        dialogue._new_symbol_kind,
        dialogue._new_external_reference,
    )
    variable_field: QtWidgets.QWidget
    for variable_field in variable_fields:
        assert (variable_field.x(), variable_field.width()) == shared_field_geometry

    dialogue._new_symbol_category.setCurrentText("Parameters")
    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.EVENT_PARAMETER.value)
    application.processEvents()
    parameter_vertical_geometries: List[tuple[int, int]] = list()
    for stable_field in stable_fields:
        parameter_position: QtCore.QPoint = stable_field.mapTo(
            dialogue,
            QtCore.QPoint(0, 0),
        )
        parameter_vertical_geometries.append((parameter_position.y(), stable_field.height()))
    assert parameter_vertical_geometries == variable_vertical_geometries
    assert dialogue._new_parameter_value.isVisible()
    assert (
        dialogue._new_parameter_value.x(),
        dialogue._new_parameter_value.width(),
    ) == shared_field_geometry

    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.PARAMETER.value)
    application.processEvents()
    assert dialogue._new_static_reference.isVisible()
    assert (
        dialogue._new_static_reference.x(),
        dialogue._new_static_reference.width(),
    ) == shared_field_geometry
    assert dialogue._new_external_reference_label.text() == "Power-flow variable"
    dialogue.close()


def test_legacy_equation_backed_output_does_not_block_new_input() -> None:
    """A saved output-only variable with an equation must remain editable."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    algebraic_variable: Var = var_factory.add_var("algebraic_signal")
    legacy_output: Var = var_factory.add_var("legacy_signal")
    block: Block = Block(
        name="legacy_equation_output",
        algebraic_vars=list([algebraic_variable]),
        algebraic_eqs=list([algebraic_variable, legacy_output]),
        out_vars=list([legacy_output]),
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        var_factory,
    )
    dialogue._new_symbol_name.setText("additional_input")
    dialogue._new_symbol_kind.setCurrentText(BlockSymbolKind.INPUT.value)
    dialogue.add_staged_symbol()
    dialogue.apply_changes()

    assert "Changes applied" in dialogue._status_label.text()
    assert block.in_vars[-1].name == "additional_input"
    dialogue.close()


def test_existing_variable_can_stop_being_an_output_on_apply() -> None:
    """An existing algebraic variable must expose a staged removable Output flag."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    exported_variable: Var = var_factory.add_var("exported_signal")
    block: Block = Block(
        name="editable_output",
        algebraic_vars=list([exported_variable]),
        algebraic_eqs=list([exported_variable - Const(1.0)]),
        out_vars=list([exported_variable]),
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "CUSTOM", var_factory)
    output_index: QtCore.QModelIndex = dialogue._symbol_model.index(0, 3)

    assert output_index.flags() & QtCore.Qt.ItemFlag.ItemIsUserCheckable
    assert dialogue._symbol_model.setData(
        output_index,
        QtCore.Qt.CheckState.Unchecked,
        QtCore.Qt.ItemDataRole.CheckStateRole,
    )
    assert block.out_vars == list([exported_variable])
    export_changes: list[tuple[Block, Var, bool]] = dialogue._symbol_model.get_output_export_changes()
    assert export_changes == list([(block, exported_variable, False)])

    dialogue.apply_changes()

    assert block.out_vars == list()
    assert block.algebraic_vars == list([exported_variable])
    dialogue.close()

    # Reopening must still expose the primary algebraic variable so the user
    # can publish it again without recreating either the variable or equation.
    reopened_dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "CUSTOM",
        var_factory,
    )
    reopened_output_index: QtCore.QModelIndex = reopened_dialogue._symbol_model.index(0, 3)
    assert reopened_dialogue._symbol_model.setData(
        reopened_output_index,
        QtCore.Qt.CheckState.Checked,
        QtCore.Qt.ItemDataRole.CheckStateRole,
    )
    reopened_dialogue.apply_changes()

    assert block.algebraic_vars == list([exported_variable])
    assert block.out_vars == list([exported_variable])
    reopened_dialogue.close()


def test_input_and_parameter_cannot_be_exported() -> None:
    """Inputs and configuration parameters must never expose Output checkboxes."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    input_variable: Var = Var("input_signal")
    parameter_variable: Var = Var("gain")
    block: Block = Block(
        name="output_roles",
        in_vars=list([input_variable]),
        parameters=dict({parameter_variable: Const(1.0)}),
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "CUSTOM", VarFactory())
    input_output_index: QtCore.QModelIndex = dialogue._symbol_model.index(0, 3)
    parameter_output_index: QtCore.QModelIndex = dialogue._symbol_model.index(1, 3)

    assert not input_output_index.flags() & QtCore.Qt.ItemFlag.ItemIsUserCheckable
    assert not parameter_output_index.flags() & QtCore.Qt.ItemFlag.ItemIsUserCheckable
    dialogue.close()


def test_load_rms_operating_point_event_parameters_are_editable() -> None:
    """Expose Pl0 and Ql0 overrides without losing automatic initialization."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block | None = create_block_of_type(
        var_factory=var_factory,
        block_type=BlockType.LOAD_RMS,
        item_name="LOAD_RMS_test",
    )

    assert isinstance(block, Block)
    child: Block = block.children[0]
    event_variables: dict[str, Var] = dict((variable.name, variable) for variable in child.event_dict.keys())
    assert child.event_dict[event_variables["Pl0"]].value is None
    assert child.event_dict[event_variables["Ql0"]].value is None
    assert child.init_eqs[event_variables["Pl0"]].name == "Pl"
    assert child.init_eqs[event_variables["Ql0"]].name == "Ql"

    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        BlockType.LOAD_RMS.name,
        var_factory,
    )
    row_by_name: dict[str, int] = dict()
    row_index: int
    for row_index in range(dialogue._parameter_model.rowCount()):
        parameter_name: object = dialogue._parameter_model.index(row_index, 1).data()
        if isinstance(parameter_name, str):
            row_by_name[parameter_name] = row_index
        else:
            pass

    assert set(row_by_name.keys()) == set(["Pl0", "Ql0"])
    assert dialogue._parameter_model.setData(
        dialogue._parameter_model.index(row_by_name["Pl0"], 2),
        "-0.75",
    )
    assert dialogue._parameter_model.setData(
        dialogue._parameter_model.index(row_by_name["Ql0"], 2),
        "-0.2",
    )
    dialogue.apply_changes()

    assert child.event_dict[event_variables["Pl0"]].value == -0.75
    assert child.event_dict[event_variables["Ql0"]].value == -0.2
    assert child.init_eqs[event_variables["Pl0"]].name == "Pl"
    assert child.init_eqs[event_variables["Ql0"]].name == "Ql"
    dialogue.close()


def test_validate_button_rejects_unknown_symbols_and_python_syntax_errors() -> None:
    """Explicit validation reports both unresolved symbols and malformed Python code."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block = Block(name="validation_target")
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "GENERIC", var_factory)

    dialogue._dae_editor.setPlainText(
        "state_eqs = []\n"
        "algebraic_eqs = [missing_symbol]\n"
        "init_eqs = {}\n"
        "diff_init_eqs = {}"
    )
    assert dialogue._dae_editor.get_diagnostics() == list()
    dialogue._validate_code_button.click()
    assert "Unknown symbol 'missing_symbol'" in dialogue._dae_editor.toolTip()
    assert "line 2" in dialogue._status_label.text().lower()

    dialogue._dae_editor.setPlainText(
        "state_eqs = []\n"
        "algebraic_eqs = [(1 + 2]\n"
        "init_eqs = {}\n"
        "diff_init_eqs = {}"
    )
    assert dialogue._dae_editor.get_diagnostics() == list()
    dialogue._validate_code_button.click()
    assert len(dialogue._dae_editor.get_diagnostics()) == 1
    assert dialogue._dae_editor.get_diagnostics()[0].get_line() == 2
    assert "validate again" in dialogue._dae_editor.get_diagnostics()[0].get_message()
    selections: list[QtWidgets.QTextEdit.ExtraSelection] = dialogue._dae_editor.extraSelections()
    assert len(selections) == 1
    assert selections[0].cursor.hasSelection()
    assert selections[0].cursor.selectedText() == "("
    dialogue.close()


def test_validate_button_marks_the_expression_after_a_missing_comma() -> None:
    """A Python-valid implicit call must point at the actual missing-comma site."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    first: Var = Var("first")
    second: Var = Var("second")
    block: Block = Block(
        name="comma_target",
        algebraic_vars=list([first, second]),
        algebraic_eqs=list([first, second]),
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        VarFactory(),
    )
    dialogue._dae_editor.setPlainText(
        "state_eqs = []\n"
        "algebraic_eqs = [\n"
        "    (first - 1)\n"
        "    (second - 2),\n"
        "    (missing_name - 3),\n"
        "]\n"
        "init_eqs = {}\n"
        "diff_init_eqs = {}"
    )

    assert dialogue._dae_editor.get_diagnostics() == list()
    dialogue._validate_code_button.click()

    assert len(dialogue._dae_editor.get_diagnostics()) == 2
    diagnostic: DaeCodeDiagnostic = dialogue._dae_editor.get_diagnostics()[0]
    assert diagnostic.get_line() == 4
    assert "missing comma" in diagnostic.get_message().lower()
    assert dialogue._dae_editor.get_diagnostics()[1].get_line() == 5
    assert "missing_name" in dialogue._dae_editor.get_diagnostics()[1].get_message()
    assert "state_eqs" not in dialogue._status_label.text()
    dialogue.close()


def test_validate_button_marks_a_cross_line_unmatched_opening_parenthesis() -> None:
    """A later closing bracket must highlight the earlier unmatched opener."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        Block(name="parenthesis_target"),
        "GENERIC",
        VarFactory(),
    )
    dialogue._dae_editor.setPlainText(
        "state_eqs = []\n"
        "algebraic_eqs = [\n"
        "    (1 + 2,\n"
        "]\n"
        "init_eqs = {}\n"
        "diff_init_eqs = {}"
    )

    dialogue._validate_code_button.click()

    assert len(dialogue._dae_editor.get_diagnostics()) == 1
    diagnostic: DaeCodeDiagnostic = dialogue._dae_editor.get_diagnostics()[0]
    assert diagnostic.get_line() == 3
    assert "validate again" in diagnostic.get_message()
    selections: list[QtWidgets.QTextEdit.ExtraSelection] = dialogue._dae_editor.extraSelections()
    assert selections[0].cursor.selectedText() == "("
    assert "line 3" in dialogue._status_label.text().lower()
    dialogue.close()


def test_every_block_properties_table_column_is_manually_resizable() -> None:
    """No table column in the modal may remain locked to stretch or contents."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    _unused_state_variable: Var = state_variable
    _unused_parameter_variable: Var = parameter_variable
    _unused_parameter_constant: Const = parameter_constant
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        VarFactory(),
    )
    dialogue.show()
    dialogue._tabs.setCurrentIndex(1)
    application.processEvents()

    initial_split_sizes: list[int] = dialogue._dae_splitter.sizes()
    initial_split_total: int = sum(initial_split_sizes)
    assert 0.64 <= initial_split_sizes[1] / initial_split_total <= 0.68
    assert [dialogue._symbol_table.columnWidth(index) for index in range(5)] == [
        65,
        55,
        80,
        50,
        110,
    ]

    table: QtWidgets.QTableView
    for table in dialogue.findChildren(QtWidgets.QTableView):
        header: QtWidgets.QHeaderView = table.horizontalHeader()
        column_index: int
        for column_index in range(header.count()):
            assert header.sectionResizeMode(column_index) == QtWidgets.QHeaderView.ResizeMode.Interactive
    latex_header: QtWidgets.QHeaderView = dialogue._latex_selection_tree.header()
    latex_column_index: int
    for latex_column_index in range(latex_header.count()):
        assert latex_header.sectionResizeMode(
            latex_column_index
        ) == QtWidgets.QHeaderView.ResizeMode.Interactive
    variable_page: QtWidgets.QWidget | None = dialogue._symbol_table.parentWidget()
    if variable_page is not None and variable_page.parentWidget() is not None:
        symbol_tabs_widget: QtWidgets.QWidget | None = variable_page.parentWidget().parentWidget()
    else:
        symbol_tabs_widget = None
    assert isinstance(symbol_tabs_widget, QtWidgets.QTabWidget)
    symbol_tabs_widget.setCurrentWidget(variable_page)
    application.processEvents()
    assert dialogue._symbol_table.horizontalScrollBar().maximum() == 0
    parameter_page: QtWidgets.QWidget | None = dialogue._parameter_symbol_table.parentWidget()
    assert parameter_page is not None
    symbol_tabs_widget.setCurrentWidget(parameter_page)
    application.processEvents()
    assert dialogue._parameter_symbol_table.horizontalScrollBar().maximum() == 0

    # The same splitter handle must support both requested directions instead
    # of pinning the symbol panel to its initial one-third allocation.
    dialogue._dae_splitter.setSizes(list([320, initial_split_total - 320]))
    application.processEvents()
    reduced_sizes: list[int] = dialogue._dae_splitter.sizes()
    assert reduced_sizes[0] < initial_split_sizes[0]
    dialogue._dae_splitter.setSizes(list([650, initial_split_total - 650]))
    application.processEvents()
    expanded_sizes: list[int] = dialogue._dae_splitter.sizes()
    assert expanded_sizes[0] > initial_split_sizes[0]

    # The vertical handle must likewise let the table consume space from the
    # add-symbol form, which remains usable at its minimum size.
    initial_vertical_sizes: list[int] = dialogue._symbol_panel_splitter.sizes()
    initial_vertical_total: int = sum(initial_vertical_sizes)
    dialogue._symbol_panel_splitter.setSizes(
        list([initial_vertical_total - 130, 130])
    )
    application.processEvents()
    enlarged_table_sizes: list[int] = dialogue._symbol_panel_splitter.sizes()
    assert enlarged_table_sizes[0] > initial_vertical_sizes[0]
    assert enlarged_table_sizes[1] < initial_vertical_sizes[1]
    dialogue.close()


def test_emt_generator_binary_functions_validate_in_dialogue() -> None:
    """The EMT generator's ``atan2`` expressions must use the safe GUI parser."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block | None = create_block_of_type(
        var_factory,
        BlockType.EMT_GENERATOR,
        "EMT_GENERATOR_test",
    )

    assert isinstance(block, Block)
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        BlockType.EMT_GENERATOR.name,
        var_factory,
    )
    dialogue.validate_complete_dae_code()
    assert dialogue._status_label.text() == "DAE code is valid."
    assert dialogue._dae_editor.get_diagnostics() == list()
    dialogue.close()


def test_rlc_combo_library_block_has_a_default_constructor() -> None:
    """Dragging RLC Combo must yield a balanced explicit/implicit DAE block."""
    var_factory: VarFactory = VarFactory()
    block: Block | None = create_block_of_type(
        var_factory,
        BlockType.RLC_COMBO_EMT,
        "RLC_combo_test",
    )

    assert isinstance(block, Block)
    assert len(block.in_vars) > 0
    assert len(block.out_vars) > 0
    assert len(block.state_vars) == len(block.state_eqs) == 3
    assert len(block.algebraic_vars) == len(block.algebraic_eqs) == 7
    assert [variable.name for variable in block.state_vars] == ["iL_A", "iL_B", "iL_C"]
    assert [variable.name for variable in block.algebraic_vars if variable.name.startswith("vCap")] == [
        "vCapA",
        "vCapB",
        "vCapC",
    ]


def test_rlc_combo_rendered_pdf_uses_matching_state_derivatives(tmp_path: Path) -> None:
    """RLC export must pair inductor RHS entries by identity and create a PDF."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block | None = create_block_of_type(
        var_factory,
        BlockType.RLC_COMBO_EMT,
        "RLC_COMBO_EMT_test",
    )
    assert isinstance(block, Block)
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        BlockType.RLC_COMBO_EMT.name,
        var_factory,
    )

    drafts: list[BlockEquationDraft] = dialogue._parse_all_equation_buffers_for_export()
    dialogue.select_all_latex_sections()
    entries: list[EquationExportEntry] = dialogue._build_selected_equation_entries(drafts)
    state_entries: list[EquationExportEntry] = list()
    entry: EquationExportEntry
    for entry in entries:
        if entry.get_section() == EquationExportSection.STATE:
            state_entries.append(entry)
        else:
            pass
    assert [entry.get_latex().split(" = ", maxsplit=1)[0] for entry in state_entries] == [
        r"d_{iL\_A}",
        r"d_{iL\_B}",
        r"d_{iL\_C}",
    ]

    destination: Path = tmp_path / "rlc_combo_rendered.pdf"
    write_equation_pdf(
        str(destination),
        block.name,
        entries,
        EquationPdfStyle.RENDERED,
    )
    payload: bytes = destination.read_bytes()
    assert payload.startswith(b"%PDF")
    assert b"/Subtype /Image" not in payload
    dialogue.close()


def test_every_builder_backed_library_block_has_a_valid_default() -> None:
    """Removing creation wizards requires every mapped builder to evaluate directly."""
    builder_classes: dict[BlockType, type[TemplateDefinition]] = get_blocktype2template_builder_dict()
    block_type: BlockType
    for block_type in builder_classes:
        builder: TemplateDefinition | None = create_default_template_builder(
            VarFactory(),
            block_type,
            block_type.name,
        )
        assert builder is not None
        template: EmtModelTemplate = builder.eval()
        assert isinstance(template.block, Block)


def test_every_phase_selective_builder_defaults_to_abc_without_neutral() -> None:
    """All phase-capable drag defaults must consistently represent an ABC network."""
    builder_classes: dict[BlockType, type[TemplateDefinition]] = get_blocktype2template_builder_dict()
    block_type: BlockType
    for block_type in builder_classes:
        builder: TemplateDefinition | None = create_default_template_builder(
            VarFactory(),
            block_type,
            block_type.name,
        )
        assert builder is not None
        phase_a: TemplateProp | None = builder.params_dict.get("phA", None)
        phase_b: TemplateProp | None = builder.params_dict.get("phB", None)
        phase_c: TemplateProp | None = builder.params_dict.get("phC", None)
        phase_n: TemplateProp | None = builder.params_dict.get("phN", None)
        if phase_a is not None or phase_b is not None or phase_c is not None:
            assert phase_a is not None and phase_a.value is True
            assert phase_b is not None and phase_b.value is True
            assert phase_c is not None and phase_c.value is True
            if phase_n is not None:
                assert phase_n.value is False
            else:
                pass
        else:
            pass


@pytest.mark.parametrize(
    ("template_name", "expected_suffix"),
    list([
        ("complete_generator_rms_template", "RMS\\complete_generator.md"),
        ("complete_generator_emt_template", "EMT\\complete_generator.md"),
        ("Genrow rms template", "RMS\\genrou_genrow.md"),
        ("Line_rms_template", "RMS\\line.md"),
        ("Load rms template", "RMS\\load.md"),
        ("PVD1 DC-MPPT RMS template", "RMS\\distributed_pv.md"),
        ("ESD1 RMS template", "RMS\\battery.md"),
        ("rms_trafo_template", "RMS\\2w_transformer.md"),
        ("vsc_rms_template", "RMS\\gfm_vsc.md"),
        ("emt_thevenin_eq_generator_template", "EMT\\thevenin_generator.md"),
        ("ideal_converter_emt", "EMT\\ideal_converter.md"),
        ("pseudo_converter_emt", "EMT\\full_pseudo_converter.md"),
        ("switched_converter_emt", "EMT\\switched_converter.md"),
        ("dc_load_emt_template", "EMT\\dc_load.md"),
        ("dc_line_power_input_emt", "EMT\\dc_line.md"),
        ("transformer_emt_template", "EMT\\transformer.md"),
        ("xfmr_emt_template", "EMT\\xfmr.md"),
        ("C_shunt", "EMT\\shunt_c_abc.md"),
        ("L_shunt", "EMT\\shunt_l_abc.md"),
        ("R_shunt", "EMT\\shunt_r_abc.md"),
        ("EXP_Load_EMT_3ph", "EMT\\exponential_load_abc.md"),
        ("ZIP_Load_EMT_3ph", "EMT\\zip_load_abc.md"),
        ("Pi", "EMT\\pi_line_abc.md"),
        ("Bergeron", "EMT\\bergeron_line_abc.md"),
        ("induction_motor_emt_template", "EMT\\single_cage_induction_motor.md"),
        ("induction_motor_double_cage_emt_template", "EMT\\double_cage_induction_motor.md"),
        ("bess_avm_grid_following_emt", "EMT\\bess.md"),
        ("pv_avm_grid_following_emt", "EMT\\pv_plant_grid_following.md"),
        ("VSC_GridForming", "EMT\\vsc_grid_forming_gfm.md"),
        ("Pll_transform_rms", "library\\pll_transformer.md"),
    ]),
)
def test_template_documentation_uses_composite_and_pll_online_page(template_name: str,
                                                                    expected_suffix: str) -> None:
    """Generic template nodes must resolve their exact online documentation page."""
    expected_html_suffix: str = expected_suffix.replace("\\", "/")[:-3] + ".html"
    documentation_url: str | None = resolve_block_documentation_url("TEMPLATE", template_name)

    assert documentation_url is not None
    assert documentation_url.startswith(
        "https://veragrid.readthedocs.io/en/latest/md_source/dyn_templates/"
    )
    assert documentation_url.endswith(expected_html_suffix)
    assert "\\" not in documentation_url


def test_all_explicit_native_documentation_paths_exist() -> None:
    """Keep every native BlockType documentation association on disk."""
    documentation_root: Path = Path(__file__).resolve().parents[3] / "doc" / "md_source" / "dyn_templates"
    mapped_count: int = 0
    block_type: BlockType
    for block_type in BlockType:
        relative_path: str | None = _get_documentation_relative_path(block_type.name, block_type.name)
        if relative_path is not None:
            mapped_count += 1
            assert (documentation_root / relative_path).is_file(), block_type.name
        else:
            pass

    assert mapped_count >= 60


# def test_every_dynamic_block_page_explains_the_block_and_its_use() -> None:
#     """Every published block page must explain what it represents and why it is used."""
#     documentation_root: Path = Path(__file__).resolve().parents[3] / "doc" / "md_source" / "dyn_templates"
#     documentation_paths: list[Path] = list(
#         documentation_path
#         for documentation_path in documentation_root.rglob("*.md")
#         if documentation_path.name not in ("dynamic_model_library_index.md", "dae_block_authoring.md")
#     )
#
#     assert len(documentation_paths) >= 780
#     documentation_path: Path
#     for documentation_path in documentation_paths:
#         documentation: str = documentation_path.read_text(encoding="utf-8")
#         assert documentation.count("<!-- veragrid-block-introduction:start -->") == 1, documentation_path
#         assert documentation.count("<!-- veragrid-block-introduction:end -->") == 1, documentation_path
#         assert "## Engineering context" not in documentation, documentation_path
#         assert "## Typical use" in documentation, documentation_path
#         assert len(documentation.split()) >= 75, documentation_path


def test_cigre_surge_source_uses_its_catalogue_markdown() -> None:
    """Resolve the CIGRE source to its exact online catalogue page."""
    documentation_url: str | None = resolve_block_documentation_url(
        BlockType.CIGRE_SURGE_CURRENT_SOURCE_EMT.name,
        "CIGRE_SURGE_CURRENT_SOURCE_EMT_1",
    )

    assert documentation_url is not None
    assert documentation_url.endswith("library/cigre_surge_current_source_emt.html")


def test_every_basic_catalogue_template_resolves_its_own_markdown() -> None:
    """Require one type-id-specific online page for every draggable template."""
    descriptor: BasicBlockTemplateDescriptor
    for descriptor in get_editor_ready_basic_block_catalog_descriptors():
        template: EmtModelTemplate = load_basic_block_catalog_template(
            descriptor=descriptor,
            var_factory=VarFactory(),
        )
        documentation_url: str | None = resolve_block_documentation_url(
            "TEMPLATE",
            template.block.name,
        )

        assert documentation_url is not None, descriptor.display_label
        assert documentation_url.endswith(
            f"library/catalog/typ_{descriptor.typ_id}.html"
        ), descriptor.display_label


def test_custom_block_disables_online_catalogue_documentation() -> None:
    """A genuinely custom node must not pretend to have catalogue documentation."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    custom_block: Block = Block(name="User-authored control model")
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        custom_block,
        "CUSTOM",
        VarFactory(),
    )

    assert resolve_block_documentation_url("CUSTOM", custom_block.name) is None
    assert not dialogue._block_info_button.isEnabled()
    assert "custom block" in dialogue._block_info_button.toolTip()
    dialogue.close()


def test_symbol_tables_are_separated_and_never_repeat_parameter_values() -> None:
    """The DAE page must separate symbols and leave values to General Options."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    _unused_state_variable: Var = state_variable
    _unused_parameter_variable: Var = parameter_variable
    _unused_parameter_constant: Const = parameter_constant
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "GENERIC", VarFactory())

    assert dialogue._symbol_model.columnCount() == 5
    assert dialogue._symbol_model.headerData(2, QtCore.Qt.Orientation.Horizontal) == "Type"
    assert dialogue._symbol_model.headerData(4, QtCore.Qt.Orientation.Horizontal) == "Mapping"
    assert dialogue._variable_symbol_proxy.headerData(4, QtCore.Qt.Orientation.Horizontal) == (
        "Power-flow derived initialization"
    )
    assert dialogue._parameter_symbol_proxy.headerData(4, QtCore.Qt.Orientation.Horizontal) == (
        "Static parameter mapping"
    )
    assert dialogue._variable_symbol_proxy.rowCount() == 1
    assert dialogue._parameter_symbol_proxy.rowCount() == 1
    assert dialogue._symbol_table.model() is dialogue._variable_symbol_proxy
    assert dialogue._parameter_symbol_table.model() is dialogue._parameter_symbol_proxy
    assert dialogue._parameter_symbol_table.isColumnHidden(3)
    dialogue.close()


def test_block_properties_searches_filter_tables_and_navigate_python_code() -> None:
    """Every requested Block properties search must act on its own data view."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    _unused_state_variable: Var = state_variable
    _unused_parameter_variable: Var = parameter_variable
    _unused_parameter_constant: Const = parameter_constant
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        VarFactory(),
    )

    dialogue._variable_symbol_search.setText("x")
    assert dialogue._variable_symbol_proxy.rowCount() == 1
    dialogue._variable_symbol_search.setText("missing")
    assert dialogue._variable_symbol_proxy.rowCount() == 0

    dialogue._parameter_symbol_search.setText("gain")
    assert dialogue._parameter_symbol_proxy.rowCount() == 1
    dialogue._parameter_symbol_search.setText("missing")
    assert dialogue._parameter_symbol_proxy.rowCount() == 0

    dialogue._general_parameter_search.setText("gain")
    assert dialogue._general_parameter_proxy.rowCount() == 1
    dialogue._general_parameter_search.setText("missing")
    assert dialogue._general_parameter_proxy.rowCount() == 0

    dialogue._dae_code_search.setText("state_eqs")
    active_match: int
    match_count: int
    active_match, match_count = dialogue._dae_editor.get_search_position()
    assert active_match == 1
    assert match_count >= 1
    assert dialogue._dae_search_status.text() == f"1 / {match_count}"
    dialogue.find_next_dae_code_match()
    next_match: int
    next_count: int
    next_match, next_count = dialogue._dae_editor.get_search_position()
    assert next_count == match_count
    assert next_match == (2 if match_count > 1 else 1)
    dialogue.close()


def test_block_properties_dialogue_opens_at_a_moderate_size() -> None:
    """The modal must leave visible desktop space around its initial geometry."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    _unused_state_variable: Var = state_variable
    _unused_parameter_variable: Var = parameter_variable
    _unused_parameter_constant: Const = parameter_constant
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        VarFactory(),
    )

    assert dialogue.size() == QtCore.QSize(1200, 700)
    dialogue.close()


def test_symbol_mapping_column_applies_power_flow_and_device_references() -> None:
    """Mapping edits must update the actual block dictionaries used at initialization."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block
    state_variable: Var
    parameter_variable: Var
    parameter_constant: Const
    block, state_variable, parameter_variable, parameter_constant = build_test_block()
    _unused_parameter_constant: Const = parameter_constant
    block.external_mapping[VarPowerFlowReferenceType.P] = state_variable
    block.api_obj_mapping[ParamPowerFlowReferenceType.Pl0] = parameter_variable
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "GENERIC", VarFactory())

    state_mapping_index: QtCore.QModelIndex = dialogue._symbol_model.index(0, 4)
    parameter_mapping_index: QtCore.QModelIndex = dialogue._symbol_model.index(1, 4)
    assert state_mapping_index.data() == "VarPowerFlowReferenceType.P"
    assert parameter_mapping_index.data() == "ParamPowerFlowReferenceType.Pl0"
    assert dialogue._symbol_model.setData(
        state_mapping_index,
        "VarPowerFlowReferenceType.Q",
    )
    assert dialogue._symbol_model.setData(
        parameter_mapping_index,
        "ParamPowerFlowReferenceType.Ql0",
    )

    dialogue.apply_changes()

    assert block.external_mapping == {VarPowerFlowReferenceType.Q: state_variable}
    assert block.api_obj_mapping == {ParamPowerFlowReferenceType.Ql0: parameter_variable}
    dialogue.close()


def test_mapping_editability_matches_variable_and_parameter_semantics() -> None:
    """Only variables and static parameters may edit their respective mappings."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    algebraic_variable: Var = Var("power")
    static_parameter: Var = Var("rated_power")
    event_parameter: Var = Var("power_step")
    block: Block = Block(
        name="mapping_semantics",
        algebraic_vars=[algebraic_variable],
        algebraic_eqs=[algebraic_variable],
        parameters={static_parameter: Const(100.0, name="rated_power")},
        event_dict={event_parameter: Const(0.0, name="power_step")},
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        VarFactory(),
    )
    row_by_name: dict[str, int] = dict()
    row_index: int
    for row_index in range(dialogue._symbol_model.rowCount()):
        name_index: QtCore.QModelIndex = dialogue._symbol_model.index(row_index, 1)
        row_by_name[str(name_index.data())] = row_index

    variable_index: QtCore.QModelIndex = dialogue._symbol_model.index(row_by_name["power"], 4)
    static_index: QtCore.QModelIndex = dialogue._symbol_model.index(row_by_name["rated_power"], 4)
    event_index: QtCore.QModelIndex = dialogue._symbol_model.index(row_by_name["power_step"], 4)
    editable_flag: QtCore.Qt.ItemFlag = QtCore.Qt.ItemFlag.ItemIsEditable

    assert dialogue._symbol_model.flags(variable_index) & editable_flag
    assert dialogue._symbol_model.flags(static_index) & editable_flag
    assert not dialogue._symbol_model.flags(event_index) & editable_flag
    assert dialogue._symbol_model.setData(
        variable_index,
        "VarPowerFlowReferenceType.P",
    )
    assert not dialogue._symbol_model.setData(
        variable_index,
        "ParamPowerFlowReferenceType.Pl0",
    )
    assert dialogue._symbol_model.setData(
        static_index,
        "ParamPowerFlowReferenceType.Pl0",
    )
    assert not dialogue._symbol_model.setData(
        static_index,
        "VarPowerFlowReferenceType.P",
    )
    assert not dialogue._symbol_model.setData(
        event_index,
        "VarPowerFlowReferenceType.P",
    )

    dialogue.apply_changes()

    assert block.external_mapping == {VarPowerFlowReferenceType.P: algebraic_variable}
    assert block.api_obj_mapping == {ParamPowerFlowReferenceType.Pl0: static_parameter}
    dialogue.close()


def test_duplicate_power_flow_mapping_is_rejected_before_application() -> None:
    """One internal block cannot initialize two identities from the same PF reference."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    first_variable: Var = Var("x")
    second_variable: Var = Var("y")
    block: Block = Block(
        name="mapping_test",
        algebraic_vars=[first_variable, second_variable],
        algebraic_eqs=[first_variable, second_variable],
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "GENERIC", VarFactory())
    first_mapping_index: QtCore.QModelIndex = dialogue._symbol_model.index(0, 4)
    second_mapping_index: QtCore.QModelIndex = dialogue._symbol_model.index(1, 4)
    assert dialogue._symbol_model.setData(
        first_mapping_index,
        "VarPowerFlowReferenceType.P",
    )
    assert dialogue._symbol_model.setData(
        second_mapping_index,
        "VarPowerFlowReferenceType.P",
    )

    dialogue.apply_changes()

    assert len(block.external_mapping) == 0
    assert "assigned more than once" in dialogue._status_label.text()
    dialogue.close()


def test_external_mapping_only_identity_remains_visible_in_initialization_column() -> None:
    """A PF-mapped identity must never disappear because it has no displayed DAE role."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    mapped_variable: Var = Var("pf_seed")
    block: Block = Block(
        name="mapping_only_test",
        external_mapping={VarPowerFlowReferenceType.DcPathModeSeed: mapped_variable},
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(block, "GENERIC", VarFactory())

    assert dialogue._symbol_model.rowCount() == 1
    assert dialogue._symbol_model.index(0, 1).data() == "pf_seed"
    assert dialogue._symbol_model.index(0, 4).data() == (
        "VarPowerFlowReferenceType.DcPathModeSeed"
    )
    dialogue.close()


def test_equation_pdf_writer_creates_both_supported_pdf_styles(tmp_path: Path) -> None:
    """Selected equations must export as valid source and rendered PDF documents."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    source_name: str = build_equation_pdf_suggested_name(
        "Generator",
        EquationPdfStyle.LATEX_SOURCE,
    )
    rendered_name: str = build_equation_pdf_suggested_name(
        "Generator",
        EquationPdfStyle.RENDERED,
    )
    assert source_name == "Generator_dynamic_equations_latex_source.pdf"
    assert rendered_name == "Generator_dynamic_equations_latex_rendered.pdf"
    assert source_name != rendered_name
    entries: list[EquationExportEntry] = list([
        EquationExportEntry(
            "Generator",
            EquationExportSection.STATE,
            r"\frac{d\omega}{dt}=\frac{T_m-T_e}{M}",
        ),
    ])
    source_payload: bytes | None = None
    rendered_payload: bytes | None = None
    style: EquationPdfStyle
    for style in (EquationPdfStyle.LATEX_SOURCE, EquationPdfStyle.RENDERED):
        destination: Path = tmp_path / f"equations_{style.name.lower()}.pdf"
        write_equation_pdf(str(destination), "Generator template", entries, style)
        payload: bytes = destination.read_bytes()
        assert payload.startswith(b"%PDF")
        assert len(payload) > 1000
        if style == EquationPdfStyle.LATEX_SOURCE:
            source_payload = payload
        else:
            rendered_payload = payload

    # Source is painted as real PDF text, not a raster screenshot, so users
    # can copy a complete display-math block into a LaTeX editor.
    assert source_payload is not None
    assert encode_pdf_literal(r"\[") in source_payload
    assert encode_pdf_literal(r"  \frac{d\omega}{dt}=\frac{T_m-T_e}{M}") in source_payload
    assert encode_pdf_literal(r"\]") in source_payload
    assert b" Tj" in source_payload
    assert b"(Page " not in source_payload
    # Rendered documents contain native PDF text and SVG paths. No raster
    # image object may be embedded, otherwise zooming would pixelate content.
    assert rendered_payload is not None
    assert b"/Subtype /Image" not in rendered_payload


def test_state_and_algebraic_export_entries_use_dae_equation_sides() -> None:
    """State exports use diff-variable LHS while residual exports use zero."""
    first_state_rhs: Const = Const(2.0)
    second_state_rhs: Const = Const(3.0)
    first_state: Var = Var("x")
    first_differential: Var = Var("d_x", base_var=first_state)
    state_entries: list[EquationExportEntry] = build_state_equation_entries(
        "DAE block",
        list([first_state_rhs, second_state_rhs]),
        list([first_differential]),
    )
    algebraic_entries: list[EquationExportEntry] = build_list_equation_entries(
        "DAE block",
        EquationExportSection.ALGEBRAIC,
        list([Const(4.0)]),
    )

    assert state_entries[0].get_latex().startswith(r"d_{x} = ")
    assert state_entries[1].get_latex().startswith("0 = ")
    assert algebraic_entries[0].get_latex().startswith("0 = ")


def test_latex_selection_has_no_differential_section() -> None:
    """Legacy differential residuals are absent from the editable DAE and export groups."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    state_variable: Var = Var("x")
    differential_variable: Var = Var("d_x", base_var=state_variable)
    algebraic_variable: Var = Var("y")
    legacy_differential_expression: Expr = differential_variable - algebraic_variable
    block: Block = Block(
        name="section_test",
        state_vars=list([state_variable]),
        state_eqs=list([Const(1.0)]),
        algebraic_vars=list([algebraic_variable]),
        algebraic_eqs=list([algebraic_variable]),
        diff_vars=list([differential_variable]),
        differential_eqs=list([legacy_differential_expression]),
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        VarFactory(),
    )
    root_item: QtWidgets.QTreeWidgetItem = dialogue._latex_selection_tree.topLevelItem(0)
    section_labels: list[str] = list()
    section_counts: dict[str, str] = dict()
    child_index: int
    for child_index in range(root_item.childCount()):
        child_item: QtWidgets.QTreeWidgetItem = root_item.child(child_index)
        label: str = child_item.text(0)
        section_labels.append(label)
        section_counts[label] = child_item.text(1)

    assert "Differential equations" not in section_labels
    assert "differential_eqs" not in dialogue._dae_editor.toPlainText()
    assert section_counts["State equations"] == "1"
    assert section_counts["Algebraic equations"] == "1"

    # Applying the four editable sections must not erase or reinterpret a
    # legacy Engine field that the dialogue deliberately does not expose.
    dialogue.apply_changes()
    assert "Nothing was applied" not in dialogue._status_label.text()
    assert len(block.differential_eqs) == 1
    assert block.differential_eqs[0] is legacy_differential_expression
    dialogue.close()


def test_rendered_pdf_equations_wrap_before_scaling() -> None:
    """Long rendered equations must become readable lines that all fit the page width."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    renderer: LatexRenderer = LatexRenderer(font_size=10, dpi=144)
    latex: str = (
        r"0 = \frac{alpha + beta + gamma + delta + epsilon + zeta + eta + theta "
        r"+ iota + kappa + lambda + mu + nu + xi + omicron + pi}{tau + sigma}"
    )
    maximum_width: int = 260
    rendered_lines: list[RenderedSvgEquation] = render_wrapped_equation(
        renderer,
        latex,
        maximum_width,
    )

    expanded_latex: str = expand_latex_fractions_for_wrapping(latex)
    assert r"\frac" not in expanded_latex
    assert "/" in expanded_latex
    assert len(rendered_lines) > 1
    rendered_line: RenderedSvgEquation
    for rendered_line in rendered_lines:
        assert rendered_line.get_size().width() <= maximum_width
    with pytest.raises(ValueError, match="Invalid LaTeX equation"):
        render_wrapped_equation(
            renderer,
            r"\command_that_mathtext_does_not_support{Vm}",
            maximum_width,
        )


def test_genqec_equations_compile_as_mathtext_and_wrap_long_roots() -> None:
    """GENQEC export must never expose raw LaTeX or clip a long radicand."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block = get_genqec_rms(VarFactory()).block.children[0]
    entries: list[EquationExportEntry] = list()
    entries.extend(build_state_equation_entries(
        block.name,
        block.state_eqs,
        block.diff_vars,
    ))
    entries.extend(build_list_equation_entries(
        block.name,
        EquationExportSection.ALGEBRAIC,
        block.algebraic_eqs,
    ))
    entries.extend(build_mapping_equation_entries(
        block.name,
        EquationExportSection.INITIALIZATION,
        block.init_eqs,
    ))
    renderer: LatexRenderer = LatexRenderer(font_size=10, dpi=144)
    assert "Pg - (Vd" in entries[8].get_latex()
    assert "Qg - (Vq" in entries[9].get_latex()
    assert "Te - (Psid" in entries[14].get_latex()
    assert "Sat - (1 + Sa)" in entries[17].get_latex()
    assert r"1 \times 10^{-5}" in entries[25].get_latex()
    assert r"\mathrm{j}" in entries[28].get_latex()
    entry: EquationExportEntry
    for entry in entries:
        rendered: RenderedEquation = renderer.render(entry.get_latex())
        assert rendered.get_uses_mathtext(), entry.get_latex()

    long_root: str = entries[28].get_latex()
    wrapped_root: str = expand_latex_square_roots_for_wrapping(long_root)
    assert r"\sqrt" not in wrapped_root
    wrapped_lines: list[RenderedSvgEquation] = render_wrapped_equation(
        renderer,
        long_root,
        520,
    )
    assert len(wrapped_lines) > 1
    wrapped_line: RenderedSvgEquation
    for wrapped_line in wrapped_lines:
        assert wrapped_line.get_size().width() <= 520


def test_lookup_and_jmarti_builders_expose_conditional_special_settings() -> None:
    """Structured lookup data and JMarti options belong in the optional fourth tab."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block_type: BlockType
    for block_type in (BlockType.LOOKUP_ARRAY_LINEAR, BlockType.EMT_JMARTI_LINE):
        var_factory: VarFactory = VarFactory()
        builder: TemplateDefinition | None = create_default_template_builder(
            var_factory,
            block_type,
            block_type.name,
        )
        assert builder is not None
        template: EmtModelTemplate = builder.eval()
        block: Block = template.block
        initialize_template_builder_from_block(builder, block, block_type)
        dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
            block,
            block_type.name,
            var_factory,
            structural_block_type=block_type,
            structural_builder=builder,
        )
        tab_names: list[str] = list()
        tab_index: int
        for tab_index in range(dialogue._tabs.count()):
            tab_names.append(dialogue._tabs.tabText(tab_index))
        assert "Special settings" in tab_names
        if block_type == BlockType.EMT_JMARTI_LINE:
            assert dialogue._special_structural_model.rowCount() > 20
        else:
            assert dialogue._special_structural_model.rowCount() > 0
        dialogue.close()


def test_genraw_properties_dialogue_opens_with_absolute_value_latex() -> None:
    """GENRAW equations containing adjacent absolute delimiters must render safely."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    var_factory: VarFactory = VarFactory()
    block: Block | None = create_block_of_type(var_factory, BlockType.GENRAW, "GENRAW_test")

    assert isinstance(block, Block)
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        BlockType.GENRAW.name,
        var_factory,
    )
    assert dialogue._latex_model.rowCount() > 0
    assert dialogue.validate_dae_code()
    dialogue.close()


def test_genraw_rendered_pdf_accepts_absolute_value_initialization(tmp_path: Path) -> None:
    """GENRAW absolute-value initialization must compile in rendered export."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    block: Block | None = create_block_of_type(
        VarFactory(),
        BlockType.GENRAW,
        "GENRAW_test",
    )
    assert isinstance(block, Block)
    entries: list[EquationExportEntry] = list()
    owner: Block
    for owner in block.get_all_blocks():
        entries.extend(build_state_equation_entries(
            owner.name,
            owner.state_eqs,
            owner.diff_vars,
        ))
        residual_expressions: list[Expr] = list(owner.algebraic_eqs)
        entries.extend(build_list_equation_entries(
            owner.name,
            EquationExportSection.ALGEBRAIC,
            residual_expressions,
        ))
        entries.extend(build_mapping_equation_entries(
            owner.name,
            EquationExportSection.INITIALIZATION,
            owner.init_eqs,
        ))
        entries.extend(build_mapping_equation_entries(
            owner.name,
            EquationExportSection.DERIVATIVE_INITIALIZATION,
            owner.diff_init_eqs,
        ))

    destination: Path = tmp_path / "genraw_rendered.pdf"
    write_equation_pdf(
        str(destination),
        block.name,
        entries,
        EquationPdfStyle.RENDERED,
    )

    payload: bytes = destination.read_bytes()
    assert payload.startswith(b"%PDF")
    assert len(payload) > 1000


def test_latex_renderer_separates_delimiters_and_falls_back_for_unsupported_mathtext() -> None:
    """LaTeX limitations must degrade to readable text instead of escaping into Qt."""
    application: QtWidgets.QApplication = get_qt_application()
    _unused_application: QtWidgets.QApplication = application
    renderer: LatexRenderer = LatexRenderer()

    assert normalize_mathtext_latex(r"\lvertVm\rvert") == r"\left|Vm\right|"
    rendered: RenderedEquation = renderer.render(r"\command_that_mathtext_does_not_support{Vm}")
    assert not rendered.get_pixmap().isNull()
    assert rendered.get_size().height() >= 24
    assert not rendered.get_uses_mathtext()

    oversized_latex: str = " + ".join(["very_long_symbol"] * 1000)
    oversized_rendering: RenderedEquation = renderer.render(oversized_latex)
    assert not oversized_rendering.get_pixmap().isNull()
    assert oversized_rendering.get_size().width() < 1000
    assert not oversized_rendering.get_uses_mathtext()
