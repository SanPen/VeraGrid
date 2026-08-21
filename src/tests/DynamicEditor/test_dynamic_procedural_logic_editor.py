"""Regression tests for the typed retained-mode and procedural-logic editor."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from PySide6 import QtWidgets

from VeraGrid.Gui.DynamicModelEditor.dynamic_block_properties import (
    DynamicBlockPropertiesDialog,
    build_block_symbol_namespace,
)
from VeraGrid.Gui.DynamicModelEditor.dynamic_procedural_logic import (
    ProceduralFieldDraft,
    ProceduralLogicDraft,
    RuntimeLogicDraftCollection,
    RuntimeLogicValidationResult,
    build_runtime_logic_entry,
    procedural_expression_to_text,
    get_default_procedural_fields,
)
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.enumerations import ProceduralLogicType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import (
    CmpOp,
    Comparison,
    Const,
    Expr,
    Var,
    get_symbolic_parser_function_names,
    string_to_symbolic,
)
from VeraGridEngine.Utils.procedural_logic import (
    AnalogFlipFlopLogic,
    DelayedThresholdLatchLogic,
    FixedSampleLogic,
    FlipFlopLogic,
    GradientLimiterLogic,
    HardSaturationLogic,
    MovingAverageLogic,
    PickupDropoffLogic,
    ProceduralLogicBase,
    ResetOnRisingEdgeLogic,
    SampledValueLogic,
    StartupHandoverLogic,
    ThreePhaseCarrierPwmLogic,
    ThreePhaseCarrierSampledModulationLogic,
    TimeDelayLogic,
    ValveStateLogic,
)
from VeraGridEngine.Templates.BasicBlockCatalog import (
    BasicBlockTemplateDescriptor,
    get_editor_ready_basic_block_catalog_descriptors,
    load_basic_block_catalog_template,
)


def get_qt_application() -> QtWidgets.QApplication:
    """Return the QApplication required by dialogue integration tests.

    :return: Existing or newly created Qt application.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        result: QtWidgets.QApplication = QtWidgets.QApplication(list())
    else:
        result = application
    return result


def build_complete_runtime_logic_block() -> tuple[Block, Dict[str, Expr]]:
    """Build one block exercising every concrete procedural-logic type.

    :return: Block and complete symbolic namespace used by the editor.
    """
    x: Var = Var("x")
    y: Var = Var("y")
    z: Var = Var("z")
    enable_time: Var = Var("enable_time")
    valve_type: Var = Var("valve_type")
    gate: Var = Var("gate")
    antiparallel: Var = Var("antiparallel")
    voltage_eps: Var = Var("voltage_eps")
    current_eps: Var = Var("current_eps")
    omega_sw: Var = Var("omega_sw")
    carrier_phase: Var = Var("carrier_phase")

    mode_names: List[str] = list([
        "fixed_mode", "sample_mode", "saturation_mode", "delay_mode",
        "average_mode", "gradient_mode", "flip_mode", "analog_mode",
        "relay_mode", "latch_mode", "handover_mode", "valve_mode",
        "gate_a", "gate_b", "gate_c", "sample_a", "sample_b", "sample_c",
    ])
    modes: List[Var] = list()
    mode_name: str
    for mode_name in mode_names:
        modes.append(Var(mode_name))

    event_variables: List[Var] = list([
        enable_time,
        valve_type,
        gate,
        antiparallel,
        voltage_eps,
        current_eps,
        omega_sw,
        carrier_phase,
    ])
    mode_dict: Dict[Var, Expr] = dict()
    mode_variable: Var
    for mode_variable in modes:
        mode_dict[mode_variable] = Const(0.0)
    event_dict: Dict[Var, Expr] = dict()
    event_variable: Var
    for event_variable in event_variables:
        event_dict[event_variable] = Const(0.0)

    entries: List[ProceduralLogicBase] = list([
        FixedSampleLogic("fixed_mode", x > Const(0.0), "fixed"),
        SampledValueLogic("sample_mode", x, "sample"),
        HardSaturationLogic("saturation_mode", x, Const(-1.0), Const(1.0), "saturation"),
        TimeDelayLogic("delay_mode", x, Const(0.01), "delay"),
        MovingAverageLogic("average_mode", x, Const(0.0), Const(0.02), "average"),
        GradientLimiterLogic("gradient_mode", x, Const(-2.0), Const(2.0), "gradient"),
        FlipFlopLogic("flip_mode", x > Const(1.0), x < Const(0.0), "flip"),
        AnalogFlipFlopLogic("analog_mode", x, x > Const(1.0), x < Const(0.0), "analog"),
        PickupDropoffLogic("relay_mode", x > Const(1.0), Const(0.1), Const(0.2), "relay"),
        ResetOnRisingEdgeLogic("x", y > Const(0.0), Const(0.0), "reset"),
        DelayedThresholdLatchLogic("x", "latch_mode", 1.0, 0.1, 0.2, "latch"),
        StartupHandoverLogic("handover_mode", "enable_time", "handover"),
        ValveStateLogic(
            "valve_mode", "valve_type", "gate", "antiparallel", "voltage_eps",
            "current_eps", "x", "y", "valve"),
        ThreePhaseCarrierPwmLogic(
            "x", "y", "z", "gate_a", "gate_b", "gate_c", "omega_sw",
            "carrier_phase", "pwm"),
        ThreePhaseCarrierSampledModulationLogic(
            "x", "y", "z", "sample_a", "sample_b", "sample_c", "omega_sw",
            "carrier_phase", "sampled_pwm"),
    ])
    block: Block = Block(
        name="runtime_root",
        algebraic_vars=list([x, y, z]),
        algebraic_eqs=list([x, y, z]),
        event_dict=event_dict,
        mode_dict=mode_dict,
        procedural_logic=entries,
    )
    namespace: Dict[str, Expr] = dict()
    namespace[x.name] = x
    namespace[y.name] = y
    namespace[z.name] = z
    for event_variable in event_variables:
        namespace[event_variable.name] = event_variable
    for mode_variable in modes:
        namespace[mode_variable.name] = mode_variable
    return block, namespace


# def test_every_procedural_type_has_typed_fields_and_documentation() -> None:
#     """Every concrete enum must be constructible and documented in Markdown."""
#     repository_root: Path = Path(__file__).resolve().parents[3]
#     documentation_root: Path = repository_root / "doc" / "md_source" / "dyn_templates" / "procedural_logic"
#     concrete_count: int = 0
#     logic_tpe: ProceduralLogicType
#     for logic_tpe in ProceduralLogicType:
#         if logic_tpe == ProceduralLogicType.Base:
#             pass
#         else:
#             concrete_count += 1
#             assert len(get_default_procedural_fields(logic_tpe)) > 0
#             documentation_path: Path = documentation_root / f"{logic_tpe.value}.md"
#             assert documentation_path.is_file(), logic_tpe.value
#             documentation: str = documentation_path.read_text(encoding="utf-8")
#             assert "## Purpose" in documentation
#             assert "## Runtime behavior" in documentation
#     assert concrete_count == 15
#     assert (documentation_root / "dynamic_model_library_index.md").is_file()


def test_comparisons_are_serialized_with_python_parser_tokens() -> None:
    """Unicode presentation operators must not leak into executable draft source."""
    source: Var = Var("source")
    cases: List[tuple[CmpOp, str]] = list([
        (CmpOp.LE, "<="),
        (CmpOp.GE, ">="),
        (CmpOp.LT, "<"),
        (CmpOp.GT, ">"),
        (CmpOp.EQ, "=="),
    ])
    operator: CmpOp
    token: str
    for operator, token in cases:
        comparison: Comparison = Comparison(source, operator, Const(0.0))
        assert procedural_expression_to_text(comparison) == f"source {token} 0.0"


def test_every_existing_procedural_type_roundtrips_through_typed_drafts() -> None:
    """The editor must preserve all current engine entry classes and ordering."""
    block: Block
    namespace: Dict[str, Expr]
    block, namespace = build_complete_runtime_logic_block()
    drafts: RuntimeLogicDraftCollection = RuntimeLogicDraftCollection(block)

    validation: RuntimeLogicValidationResult = drafts.validate(namespace)

    assert validation.get_errors() == list()
    rebuilt: List[ProceduralLogicBase] = list()
    entry: ProceduralLogicDraft
    for entry in drafts.get_entries():
        rebuilt.append(build_runtime_logic_entry(entry, namespace))
    assert len(rebuilt) == 15
    assert [entry.logic_tpe for entry in rebuilt] == [entry.logic_tpe for entry in block.procedural_logic]


def test_every_catalogue_runtime_entry_opens_as_a_valid_typed_draft() -> None:
    """Every draggable catalogue block with procedural logic must validate in the modal editor."""
    validated_entry_count: int = 0
    descriptor: BasicBlockTemplateDescriptor
    for descriptor in get_editor_ready_basic_block_catalog_descriptors():
        var_factory: VarFactory = VarFactory()
        template: EmtModelTemplate = load_basic_block_catalog_template(
            descriptor=descriptor,
            var_factory=var_factory,
        )
        block: Block = template.block
        entry_count: int = 0
        owner: Block
        for owner in block.get_all_blocks():
            entry_count += len(owner.procedural_logic)
        if entry_count > 0:
            drafts: RuntimeLogicDraftCollection = RuntimeLogicDraftCollection(block)
            namespace: Dict[str, Expr] = build_block_symbol_namespace(block)
            validation: RuntimeLogicValidationResult = drafts.validate(namespace)
            assert validation.get_errors() == list(), descriptor.display_label
            assert len(drafts.get_entries()) == entry_count
            validated_entry_count += entry_count
        else:
            pass
    assert validated_entry_count > 0


def test_safe_parser_accepts_every_exported_rounding_function() -> None:
    """The editor parser must accept the rounding functions serialized by the symbolic engine."""
    variable: Var = Var("x")
    namespace: Dict[str, Expr] = dict({variable.name: variable})
    parser_functions: set[str] = set(get_symbolic_parser_function_names())
    function_name: str
    for function_name in ("floor", "ceil", "round"):
        assert function_name in parser_functions
        parsed: Expr | Comparison = string_to_symbolic(f"{function_name}(x)", namespace)
        assert isinstance(parsed, Expr)


def test_new_mode_and_writer_are_applied_as_one_transaction() -> None:
    """A newly added mode must become authoritative before its writer is built."""
    var_factory: VarFactory = VarFactory()
    source: Var = var_factory.add_var("source")
    block: Block = Block(name="runtime_root", algebraic_vars=list([source]), algebraic_eqs=list([source]))
    namespace: Dict[str, Expr] = dict({source.name: source})
    drafts: RuntimeLogicDraftCollection = RuntimeLogicDraftCollection(block)
    drafts.add_mode(block, "held", "source + 1")
    entry: ProceduralLogicDraft = drafts.add_entry(
        block,
        ProceduralLogicType.SampledValue,
        "sample source",
    )
    output_field: ProceduralFieldDraft | None = entry.get_field("output_var_name")
    source_field: ProceduralFieldDraft | None = entry.get_field("source_expr")
    assert output_field is not None
    assert source_field is not None
    output_field.set_value("held")
    source_field.set_value("source * 2")

    validation: RuntimeLogicValidationResult = drafts.validate(namespace)
    assert validation.get_errors() == list()
    final_namespace: Dict[str, Expr] = drafts.apply_to_blocks(var_factory, namespace)

    assert "held" in final_namespace
    assert [variable.name for variable in block.mode_dict] == list(["held"])
    assert len(block.procedural_logic) == 1
    assert isinstance(block.procedural_logic[0], SampledValueLogic)
    assert block.procedural_logic[0].output_var_name == "held"


def test_runtime_validation_rejects_duplicate_writers_and_unknown_references() -> None:
    """Invalid references and two writers for one mode must block Apply."""
    source: Var = Var("source")
    held: Var = Var("held")
    block: Block = Block(
        name="runtime_root",
        algebraic_vars=list([source]),
        algebraic_eqs=list([source]),
        mode_dict=dict({held: Const(0.0)}),
    )
    namespace: Dict[str, Expr] = dict({source.name: source, held.name: held})
    drafts: RuntimeLogicDraftCollection = RuntimeLogicDraftCollection(block)
    first: ProceduralLogicDraft = drafts.add_entry(block, ProceduralLogicType.SampledValue, "first")
    second: ProceduralLogicDraft = drafts.add_entry(block, ProceduralLogicType.SampledValue, "second")
    first_output: ProceduralFieldDraft | None = first.get_field("output_var_name")
    first_source: ProceduralFieldDraft | None = first.get_field("source_expr")
    second_output: ProceduralFieldDraft | None = second.get_field("output_var_name")
    second_source: ProceduralFieldDraft | None = second.get_field("source_expr")
    assert first_output is not None
    assert first_source is not None
    assert second_output is not None
    assert second_source is not None
    first_output.set_value("held")
    first_source.set_value("missing_symbol")
    second_output.set_value("held")
    second_source.set_value("source")

    validation: RuntimeLogicValidationResult = drafts.validate(namespace)
    errors: List[str] = validation.get_errors()

    assert any("missing_symbol" in error for error in errors)
    assert any("already written" in error for error in errors)


def test_mode_initialization_rejects_boolean_comparisons() -> None:
    """Retained modes require numeric initialization expressions."""
    source: Var = Var("source")
    block: Block = Block(name="runtime_root", algebraic_vars=list([source]), algebraic_eqs=list([source]))
    namespace: Dict[str, Expr] = dict({source.name: source})
    drafts: RuntimeLogicDraftCollection = RuntimeLogicDraftCollection(block)
    drafts.add_mode(block, "held", "source > 0")

    validation: RuntimeLogicValidationResult = drafts.validate(namespace)

    assert any("not a comparison" in error for error in validation.get_errors())


def test_mode_deletion_is_blocked_while_dae_equations_read_it() -> None:
    """Immediate deletion must preserve modes still consumed by existing DAE equations."""
    held: Var = Var("held")
    output: Var = Var("output")
    block: Block = Block(
        name="runtime_root",
        algebraic_vars=list([output]),
        algebraic_eqs=list([output - held]),
        mode_dict=dict({held: Const(0.0)}),
    )
    drafts: RuntimeLogicDraftCollection = RuntimeLogicDraftCollection(block)

    removed: bool
    message: str
    removed, message = drafts.remove_mode(0)

    assert not removed
    assert "DAE: runtime_root" in message


def test_dialogue_applies_dae_code_and_runtime_logic_together() -> None:
    """The modal Apply action must commit a new mode, writer and DAE reference atomically."""
    application: QtWidgets.QApplication = get_qt_application()
    var_factory: VarFactory = VarFactory()
    source: Var = var_factory.add_var("source")
    block: Block = Block(
        name="runtime_root",
        algebraic_vars=list([source]),
        algebraic_eqs=list([source]),
    )
    dialogue: DynamicBlockPropertiesDialog = DynamicBlockPropertiesDialog(
        block,
        "GENERIC",
        var_factory,
    )
    drafts: RuntimeLogicDraftCollection = dialogue._runtime_logic_editor._drafts
    drafts.add_mode(block, "held", "source + 1")
    entry: ProceduralLogicDraft = drafts.add_entry(
        block,
        ProceduralLogicType.SampledValue,
        "sample source",
    )
    output_field: ProceduralFieldDraft | None = entry.get_field("output_var_name")
    source_field: ProceduralFieldDraft | None = entry.get_field("source_expr")
    assert output_field is not None
    assert source_field is not None
    output_field.set_value("held")
    source_field.set_value("source * 2")
    dialogue._runtime_logic_editor.changed.emit()
    dialogue._dae_editor.setPlainText(
        "state_vars = []\n"
        "state_eqs = {}\n"
        "algebraic_eqs = [0 = source - held]\n"
        "init_eqs = {}\n"
        "diff_init_eqs = {}"
    )

    dialogue.apply_changes()

    assert [variable.name for variable in block.mode_dict] == list(["held"])
    assert len(block.procedural_logic) == 1
    assert isinstance(block.procedural_logic[0], SampledValueLogic)
    assert "held" in str(block.algebraic_eqs[0])
    dialogue.close()
    dialogue.deleteLater()
    application.processEvents()
