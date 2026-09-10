"""Check saved RMS mappings without launching a GUI or running a simulation."""

from __future__ import annotations

import pytest

from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Dynamic.static_parameter_mapping_unified import (
    assign_static_api_object_mapping_for_device,
)
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Templates.Rms.hvdc_vsc_gfl_rms_template_v2 import (
    build_hvdc_vsc_gfl_rms,
    build_vsc_dc_link_rms,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.Symbolic.templates_common_functions import (
    synchronize_saved_rms_root_mappings_from_children,
)
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import (
    ConverterControlType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)


@pytest.mark.parametrize("control1", (
    ConverterControlType.Vm_dc,
    ConverterControlType.Pdc,
    ConverterControlType.Pac,
))
def test_complete_vsc_owns_terminal_equations_without_adapter(
        control1: ConverterControlType,
) -> None:
    """Keep each physical terminal quantity in one component only.

    :param control1: Active controller variant used to check its feedback port.
    :return: None.
    """
    model: Block = build_hvdc_vsc_gfl_rms(
        vfactory=VarFactory(),
        control1=control1,
    ).block
    converter: Block = model.children[0]
    dc_link: Block = model.children[1]
    electrical: Block = converter.children[6]

    # The former third terminal-equations component is intentionally absent.
    assert len(model.children) == 2
    assert model.external_mapping[VarPowerFlowReferenceType.Pt] is electrical.out_vars[2]
    assert model.external_mapping[VarPowerFlowReferenceType.Qt] is electrical.out_vars[3]
    assert model.external_mapping[VarPowerFlowReferenceType.Pf] is dc_link.out_vars[1]
    assert dc_link.state_vars[0] is dc_link.out_vars[0]
    assert dc_link.algebraic_vars[0] is dc_link.out_vars[1]
    assert electrical.out_vars[2] not in electrical.init_eqs
    assert electrical.out_vars[3] not in electrical.init_eqs
    assert dc_link.out_vars[1] not in dc_link.init_eqs
    assert converter.children[1].in_vars[0] is electrical.out_vars[3]

    active_controller: Block = converter.children[0]
    if control1 == ConverterControlType.Vm_dc:
        assert active_controller.in_vars[0] is dc_link.out_vars[0]
    elif control1 == ConverterControlType.Pdc:
        assert active_controller.in_vars[0] is dc_link.out_vars[1]
    else:
        assert active_controller.in_vars[0] is electrical.out_vars[2]


@pytest.mark.parametrize("loss_coefficients", ((0.0, 0.0, 0.0), (0.001, 0.015, 0.20)))
def test_vsc_capacitor_resolves_static_loss_coefficients(
        loss_coefficients: tuple[float, float, float],
) -> None:
    """Resolve real static VSC values for a separately inserted capacitor.

    :param loss_coefficients: Static alpha1, alpha2 and alpha3 device values.
    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    device: VSC = VSC(
        bus_from=Bus(name="DC", is_dc=True),
        bus_to=Bus(name="AC"),
        alpha1=loss_coefficients[0],
        alpha2=loss_coefficients[1],
        alpha3=loss_coefficients[2],
    )
    capacitor: Block = build_vsc_dc_link_rms(vfactory=VarFactory())
    root: Block = Block(children=list((capacitor,)))
    device.rms_model = root
    original_events: dict[Var, Expr | Const] = dict(capacitor.event_dict)
    problem_mapping: dict[Var, Const] = dict()

    # Exercise the same root synchronization and dispatcher used by RMS,
    # rather than seeding the capacitor constants directly in the test.
    synchronize_saved_rms_root_mappings_from_children(device=device)
    assign_static_api_object_mapping_for_device(
        grid=grid, device=device, mdl=root, problem_mapping=problem_mapping,
        logger=Logger(),
    )

    key: ParamPowerFlowReferenceType
    expected_value: float
    for key, expected_value in zip((
            ParamPowerFlowReferenceType.alpha1,
            ParamPowerFlowReferenceType.alpha2,
            ParamPowerFlowReferenceType.alpha3,
    ), loss_coefficients):
        parameter: Var = capacitor.api_obj_mapping[key]
        assert root.api_obj_mapping[key] is parameter
        assert problem_mapping[parameter].value == expected_value
        # No fallback is written into the template; only the problem receives
        # the resolved static value, without duplicating constant owners.
        assert capacitor.parameters[parameter].value is None
    assert len(problem_mapping) == 3
    assert len(root.parameters) == 0
    assert capacitor.event_dict == original_events


@pytest.mark.parametrize("roundtrip", (False, True))
def test_rms_save_replaces_deleted_vsc_component_mappings(roundtrip: bool) -> None:
    """Repair stale root metadata after replacing a complete VSC with children.

    :param roundtrip: Whether to serialize and restore the stale tree first.
    :return: None.
    """
    factory: VarFactory = VarFactory()
    old_model: Block = build_hvdc_vsc_gfl_rms(vfactory=factory).block
    new_model: Block = build_hvdc_vsc_gfl_rms(vfactory=factory).block
    # The old complete model is no longer a child. Its root mappings survive,
    # reproducing a library rebuild with identical names but different UIDs.
    root: Block = Block(
        children=list((Block(children=list(new_model.children)),)),
        in_vars=list(new_model.in_vars),
        out_vars=list(new_model.out_vars),
        external_mapping=dict(old_model.external_mapping),
        api_obj_mapping=dict(old_model.api_obj_mapping),
    )
    root.api_obj_mapping[ParamPowerFlowReferenceType.R1] = factory.add_var("R")
    root.api_obj_mapping[ParamPowerFlowReferenceType.X1] = factory.add_var("L")
    expected_external_uids: dict[VarPowerFlowReferenceType, int] = dict(
        (key, variable.uid) for key, variable in new_model.external_mapping.items()
        if variable is not None
    )
    expected_api_uids: dict[ParamPowerFlowReferenceType, int] = dict(
        (key, variable.uid) for key, variable in new_model.api_obj_mapping.items()
    )
    if roundtrip:
        root = Block.parse(root.to_dict())
    else:
        pass
    device: VSC = VSC(alpha1=0.001, alpha2=0.015, alpha3=0.20)
    device.rms_model = root
    original_inputs: tuple[Var, ...] = tuple(root.in_vars)
    original_outputs: tuple[Var, ...] = tuple(root.out_vars)

    # A second save must preserve the repaired mappings, including references
    # to nested current-controller and electrical-model symbols.
    iteration: int
    for iteration in range(2):
        synchronize_saved_rms_root_mappings_from_children(device=device)
        assert dict(
            (key, variable.uid) for key, variable in root.external_mapping.items()
            if variable is not None
        ) == expected_external_uids
        assert dict(
            (key, variable.uid) for key, variable in root.api_obj_mapping.items()
        ) == expected_api_uids
        assert tuple(root.in_vars) == original_inputs
        assert tuple(root.out_vars) == original_outputs

    # After repairing metadata, the dispatcher must resolve the surviving
    # capacitor's constants, not just identically named deleted variables.
    problem_mapping: dict[Var, Const] = dict()
    assign_static_api_object_mapping_for_device(
        grid=MultiCircuit(), device=device, mdl=root,
        problem_mapping=problem_mapping, logger=Logger(),
    )
    assert set(variable.uid for variable in problem_mapping) == set(expected_api_uids.values())


def test_rms_save_preserves_live_root_choices_and_terminal_sides() -> None:
    """Keep valid root choices even when child mappings and names differ.

    :return: None.
    """
    factory: VarFactory = VarFactory()
    from_voltage: Var = factory.add_var("Vmf", reference=VarPowerFlowReferenceType.Vm)
    to_voltage: Var = factory.add_var("Vmt", reference=VarPowerFlowReferenceType.Vm)
    manual_loss: Var = factory.add_var("manual_a0")
    child_loss: Var = factory.add_var("child_a0")
    child: Block = Block(
        in_vars=list((from_voltage, to_voltage)),
        parameters=dict(((child_loss, Const(None)),)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Vmf, to_voltage),
            (VarPowerFlowReferenceType.Vmt, from_voltage),
        )),
        api_obj_mapping=dict(((ParamPowerFlowReferenceType.alpha1, child_loss),)),
    )
    root: Block = Block(
        children=list((child,)),
        in_vars=list((from_voltage, to_voltage)),
        parameters=dict(((manual_loss, Const(None)),)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Vmf, from_voltage),
            (VarPowerFlowReferenceType.Vmt, to_voltage),
        )),
        api_obj_mapping=dict(((ParamPowerFlowReferenceType.alpha1, manual_loss),)),
    )
    device: VSC = VSC()
    device.rms_model = root
    # The root remains authoritative for live symbols; shared Vm references
    # must never be used to swap its from/to bindings or reorder its inputs.
    synchronize_saved_rms_root_mappings_from_children(device=device)
    assert root.external_mapping[VarPowerFlowReferenceType.Vmf] is from_voltage
    assert root.external_mapping[VarPowerFlowReferenceType.Vmt] is to_voltage
    assert root.api_obj_mapping[ParamPowerFlowReferenceType.alpha1] is manual_loss
    assert tuple(root.in_vars) == (from_voltage, to_voltage)


def test_vsc_static_loss_mapping_does_not_write_event_parameters() -> None:
    """Keep dynamic event values unchanged if a model incorrectly maps them.

    :return: None.
    """
    parameter: Var = Var(name="a0")
    root: Block = Block(
        api_obj_mapping=dict(((ParamPowerFlowReferenceType.alpha1, parameter),)),
        event_dict=dict(((parameter, Const(0.25)),)),
    )
    problem_mapping: dict[Var, Const] = dict()
    logger: Logger = Logger()
    # Restoring VSC coefficient support must retain the static/event contract
    # already enforced by the unified assignment helper.
    assign_static_api_object_mapping_for_device(
        grid=MultiCircuit(), device=VSC(alpha1=0.001), mdl=root,
        problem_mapping=problem_mapping, logger=logger,
    )
    assert len(problem_mapping) == 0
    assert root.event_dict[parameter].value == 0.25
    assert len(root.parameters) == 0
    assert len(logger.entries) == 1
