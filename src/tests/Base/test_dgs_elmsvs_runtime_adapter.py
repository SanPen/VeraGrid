from pathlib import Path

from VeraGridEngine.IO.dgs.dynamic_models.dgs_elmsvs_runtime_adapter import (
    build_dgs_elmsvs_rms_runtime_template,
    is_dgs_elmsvs_direct_slot_contract,
)
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import ElmSvs
from VeraGridEngine.IO.dgs.dgs_to_blocks import (
    DgsDirectRootBuildResult,
    ElmCompInstanceEntry,
)
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var
from VeraGridEngine.Utils.Symbolic.symbolic_io import duplicate_block
from VeraGridEngine.enumerations import (
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


def build_elmsvs_control_template_for_test() -> RmsModelTemplate:
    """Build the smallest complete graphical ElmSvs controller boundary.

    :return: Controller template exposing the physical ElmSvs cable surface.
    """

    bsvs: Var = Var(name="bsvs")
    control_block: Block = Block(
        name="ElmSvs controller",
        in_vars=[
            Var(name="u"),
            Var(name="uremote"),
            Var(name="ysvs"),
            Var(name="qreact"),
            Var(name="qcap"),
            Var(name="qfixcap"),
            Var(name="nxcap"),
            Var(name="nfixcap"),
        ],
        out_vars=[bsvs],
        algebraic_vars=[bsvs],
    )
    template: RmsModelTemplate = RmsModelTemplate(name="ElmSvs controller")
    template.block = control_block
    return template


def _build_elmsvs_direct_result(
        template: RmsModelTemplate,
        slot_outputs: list[str],
) -> DgsDirectRootBuildResult:
    """Build one exact transient static-var-system relation.

    :param template: Canonical controller template used by the relation.
    :param slot_outputs: Exact signals produced by the equipment slot.
    :return: Direct conversion result pointing into the template block.
    """
    equipment_entry: ElmCompInstanceEntry = ElmCompInstanceEntry(
        slot_id="svs_equipment_slot",
        slot_name="Static var system",
        element_id="svs_fid",
        element_name="SVS",
        element_kind="ElmSvs",
        element_outserv=0,
        type_id=None,
        type_name=None,
        slot_inputs=list(["bsvs"]),
        slot_outputs=slot_outputs,
        slot_reference_is_resolved=True,
        element_reference_is_resolved=True,
    )
    controller_entry: ElmCompInstanceEntry = ElmCompInstanceEntry(
        slot_id="svs_controller_slot",
        slot_name="SVS controller",
        element_id="controller_fid",
        element_name="Controller",
        element_kind="ElmDsl",
        element_outserv=0,
        type_id="controller_type_fid",
        type_name="Controller type",
        slot_outputs=list(["bsvs"]),
        slot_reference_is_resolved=True,
        element_reference_is_resolved=True,
    )
    return DgsDirectRootBuildResult(
        root_block=template.block,
        child_block_by_slot_id=dict([(
            "svs_controller_slot",
            template.block,
        )]),
        graphical_tree_by_slot_id=dict(),
        direct_entries=list([equipment_entry, controller_entry]),
    )


def _build_source_svs(
        qreact_mvar: float,
        qcap_mvar: float,
        qfixcap_mvar: float,
        nxcap: int,
        nfixcap: int,
) -> ElmSvs:
    """Build one transient source equipment row for adapter tests.

    :param qreact_mvar: Reactor limit in MVAr.
    :param qcap_mvar: Capacitor limit in MVAr.
    :param qfixcap_mvar: Fixed-capacitor rating in MVAr.
    :param nxcap: Switched-capacitor step count.
    :param nfixcap: Fixed-capacitor step count.
    :return: Source ElmSvs with the physical constants under test.
    """
    source_svs: ElmSvs = ElmSvs()
    source_svs.tcrmax = qreact_mvar
    source_svs.qmin = qcap_mvar
    source_svs.Qfixcap = qfixcap_mvar
    source_svs.nxcap = nxcap
    source_svs.nfixcap = nfixcap
    return source_svs


def test_elmsvs_slot_contract_accepts_complete_equipment_boundary() -> None:
    """Recognize a complete PowerFactory static-var-system slot.

    :return: None.
    """

    template: RmsModelTemplate = build_elmsvs_control_template_for_test()
    direct_result: DgsDirectRootBuildResult = _build_elmsvs_direct_result(
        template=template,
        slot_outputs=list(["ysvs;qreact;qcap;qfixcap;nxcap;nfixcap"]),
    )
    assert is_dgs_elmsvs_direct_slot_contract(direct_result=direct_result)


def test_elmsvs_slot_contract_rejects_incomplete_equipment_boundary() -> None:
    """Reject a static-var-system slot without its reactive-power output.

    :return: None.
    """

    template: RmsModelTemplate = build_elmsvs_control_template_for_test()
    direct_result: DgsDirectRootBuildResult = _build_elmsvs_direct_result(
        template=template,
        slot_outputs=list(["ysvs;qcap;qfixcap;nxcap;nfixcap"]),
    )
    assert not is_dgs_elmsvs_direct_slot_contract(direct_result=direct_result)


def test_elmsvs_susceptance_seed_uses_visible_safe_division() -> None:
    """Reconstruct susceptance from Q, Sbase and squared terminal voltage.

    :return: None.
    """

    control_template: RmsModelTemplate = build_elmsvs_control_template_for_test()
    direct_result: DgsDirectRootBuildResult = _build_elmsvs_direct_result(
        template=control_template,
        slot_outputs=list(["ysvs;qreact;qcap;qfixcap;nxcap;nfixcap"]),
    )
    adapted_template: RmsModelTemplate | None = (
        build_dgs_elmsvs_rms_runtime_template(
            control_template=control_template,
            clone_control_block=False,
            direct_result=direct_result,
            source_svs=_build_source_svs(
                qreact_mvar=100.0,
                qcap_mvar=0.0,
                qfixcap_mvar=0.0,
                nxcap=1,
                nfixcap=0,
            ),
        )
    )
    assert adapted_template is not None

    susceptance: Var = adapted_template.block.out_vars[-1]
    seed_expression: Expr = adapted_template.block.init_eqs[susceptance]
    assert adapted_template.block.post_init_seed_eqs[susceptance] is seed_expression

    reactive_power: Var = adapted_template.block.external_mapping[
        VarPowerFlowReferenceType.Q
    ]
    terminal_voltage: Var = adapted_template.block.external_mapping[
        VarPowerFlowReferenceType.Vm
    ]
    system_power_base: Var = adapted_template.block.api_obj_mapping[
        ParamPowerFlowReferenceType.Sbase
    ]
    bindings: dict[int, float] = {
        reactive_power.uid: -0.5,
        terminal_voltage.uid: 2.0,
        system_power_base.uid: 100.0,
    }

    assert seed_expression.eval_uid(bindings) == -12.5
    bindings[terminal_voltage.uid] = 0.0
    assert seed_expression.eval_uid(bindings) == -50.0e6

    duplicated_block: Block = duplicate_block(
        block=adapted_template.block,
        var_factory=VarFactory(),
    )
    duplicated_susceptance: Var = duplicated_block.out_vars[-1]
    duplicated_seed: Expr = duplicated_block.post_init_seed_eqs[
        duplicated_susceptance
    ]
    assert str(duplicated_seed) == str(seed_expression)


def test_elmsvs_adapter_preserves_equipment_values_from_real_dgs() -> None:
    """Carry the physical SVC constants from a tracked DGS into the wrapper.

    :return: None.
    """

    dgs_path: Path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "grids"
        / "test_ieee14_svs.dgs"
    )
    dgs_circuit: DgsCircuit = DgsCircuit()
    dgs_circuit.parse_dgs(path=str(dgs_path))
    source_svs: ElmSvs = next(
        svs
        for svs in dgs_circuit.elmsvss
        if svs.loc_name == "SVS_Droop"
    )
    control_template: RmsModelTemplate = build_elmsvs_control_template_for_test()
    direct_result: DgsDirectRootBuildResult = _build_elmsvs_direct_result(
        template=control_template,
        slot_outputs=list(["ysvs;qreact;qcap;qfixcap;nxcap;nfixcap"]),
    )

    adapted_template: RmsModelTemplate | None = (
        build_dgs_elmsvs_rms_runtime_template(
            control_template=control_template,
            clone_control_block=False,
            direct_result=direct_result,
            source_svs=source_svs,
        )
    )
    assert adapted_template is not None

    parameter_values: dict[str, float] = {
        parameter.name: constant.value
        for parameter, constant in adapted_template.block.parameters.items()
    }
    assert parameter_values["qreact"] == 10.0
    assert parameter_values["qcap"] == -20.0
    assert parameter_values["qfixcap"] == 0.0
    assert parameter_values["nxcap"] == 2.0
    assert parameter_values["nfixcap"] == 0.0
