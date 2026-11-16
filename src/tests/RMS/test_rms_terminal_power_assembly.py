
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pytest
from pathlib import Path

from VeraGridEngine.api import power_flow
from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.IO.file_save import FileSave
from VeraGridEngine.basic_structures import BoolVec, ObjVec, Logger, LogEntry
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.static_parameter_mapping_unified import assign_static_api_object_mapping_for_device
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import (
    RmsProblemDae,
    _evaluate_rms_runtime_parameter_value_from_events,
)
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_vectorized import RmsProblemDaeVec
from VeraGridEngine.Simulations.Rms.problems.rms_problem_phasor import RmsProblemPhasor
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_full_vectorized import (
    RmsProblemDaeFullVec,
)
from VeraGridEngine.Simulations.Rms.problems.rms_terminal_power_assembly import (
    assemble_rms_mapped_power_references,
    convert_rms_ac_power_balance_to_current_balance,
)
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.rms_problem_factory import build_rms_problem
from VeraGridEngine.Simulations.Rms.problems.rms_problem_multilinear import RmsProblemMultilinear
from VeraGridEngine.Simulations.Rms.initialization_rms import project_initial_algebraic_state
from VeraGridEngine.Simulations.Rms.problems.rms_problem_template import RmsProblemTemplate
from VeraGridEngine.Templates.Rms.synchronous_machines.genqec_exc_gov_sat_template import (
    get_complete_generator_template_rms,
)
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.line.line_phasor_rms_template import get_line_phasor_rms_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.buses.bus_phasor_rms_template import initialize_bus_phasor_rms
from VeraGridEngine.Templates.Rms.load_characteristics.load_phasor_current_rms_template import get_load_phasor_current_rms_template
from VeraGridEngine.Templates.Rms.renewable_controls.current_source_host import build_renewable_current_source_host
from VeraGridEngine.Templates.Rms.induction_machines.wt2g1_electrical_core import Wt2g1ElectricalSettings, derive_wt2g1_operating_point
from VeraGridEngine.Templates.Rms.renewable_controls.wt12a1u_b_active_stall import Wt12a1uBSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wt2_current_balance_host import build_wt2_current_balance_host
from VeraGridEngine.Templates.Rms.renewable_controls.wt2e1_rotor_resistance import Wt2e1Settings
from VeraGridEngine.Templates.Rms.renewable_controls.regca1_low_voltage import (
    Regca1LowVoltageSettings,
    build_regca1_low_voltage_template,
)
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_active_power import Reeca1ActivePowerMode, Reeca1ActivePowerSettings
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_q import Reeca1ConstantQSettings
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_constant_pf import Reeca1ConstantPfSettings
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_coordinated_qv import Reeca1CoordinatedQvSettings
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_local_voltage import Reeca1LocalVoltageSettings
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_current_limit import Reeca1CurrentLimitSettings
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_voltage_support import Reeca1VoltageSupportSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wtdta1_drive_train import Wtdta1DriveTrainSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wtara1_aerodynamic import Wtara1AerodynamicSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wttqa1_torque import Wttqa1TorqueMode, Wttqa1TorqueSettings
from VeraGridEngine.Templates.Rms.renewable_controls.wtpta1_pitch import Wtpta1PitchSettings
from VeraGridEngine.Templates.Rms.renewable_controls.repca1_active_plant import Repca1ActivePlantSettings
from VeraGridEngine.Templates.Rms.renewable_controls.repca1_reactive_plant import Repca1ReactiveMode, Repca1ReactivePlantSettings, Repca1VoltageCompensation, build_repca1_reactive_plant_template, repca1_line_drop_voltage
from VeraGridEngine.Templates.Rms.renewable_controls.renewable_partial_chain import build_renewable_partial_chain
from VeraGridEngine.Templates.Rms.converters.vsc_gfl_dclinked import build_vsc_rms
from VeraGridEngine.Templates.Rms.converters.vsc_gfm import VscGfmBuild
from VeraGridEngine.Templates.Rms.converters.hvdc_vsc_gfl_rms_template_v2 import build_hvdc_vsc_gfl_rms
from VeraGridEngine.Utils.Symbolic.block import Block, DynamicModelContract
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicCodec
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, get_expression_vars
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model
from VeraGridEngine.enumerations import (
    DynamicEventTransitionType, LogSeverity, ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType, RmsProblemTypes,
)

from tests.symbolic_block_roundtrip import roundtrip_block


def build_current_balance_load_case(
        powers: tuple[tuple[float, float], ...], system_base: float,
        nominal_ratio: float, mapped: tuple[bool, bool] = (True, True), equivalent_uid: bool = False,
        hierarchical: bool = False, active: bool = True, use_kw: bool = False,
        dc: bool = False, authored: bool = False) -> tuple[MultiCircuit, PowerFlowResults]:
    """Build a native phasor network with unfilled standard load parameters.

    :param powers: Per-load physical powers in the units selected by use_kw.
    :param system_base: Network MVA base used by the existing mapping provider.
    :param nominal_ratio: Receiving-to-source nominal voltage ratio.
    :param mapped: Retain P and Q API mappings independently, in that order.
    :param equivalent_uid: Use distinct API target instances with canonical UIDs.
    :param hierarchical: Declare two independent P/Q pairs in child blocks.
    :param active: Initial load activity used by both PF and RMS.
    :param use_kw: Store source powers in kW/kVAr instead of MW/MVAr.
    :param dc: Legacy DC flag applied after AC model assignment and PF.
    :param authored: Supply deliberately different initial P/Q expressions.
    :return: Physical grid and converged PF seed, with assigned native Blocks.
    """
    grid: MultiCircuit = MultiCircuit(Sbase=system_base)
    source: Bus = grid.add_bus(Bus(Vnom=10.0, is_slack=True))
    target: Bus = grid.add_bus(Bus(Vnom=10.0 * nominal_ratio))
    line: Line = grid.add_line(Line(bus_from=source, bus_to=target, r=0.02, x=0.15))
    generator: Generator = grid.add_generator(bus=source, api_obj=Generator(vset=1.0))
    active_power: float
    reactive_power: float
    for active_power, reactive_power in powers:
        physical_load: Load = grid.add_load(
            bus=target, api_obj=Load(P=active_power, Q=reactive_power, active=active))
        # PF and RMS must see the same physical units and initial activity.
        physical_load.use_kw = use_kw
    pf: PowerFlowResults = power_flow(grid)
    assert pf.converged
    initialize_bus_phasor_rms(source, grid.var_factory)
    initialize_bus_phasor_rms(target, grid.var_factory)
    set_rms_model(line, get_line_phasor_rms_template(grid.var_factory).block, grid.var_factory)

    # Share only the existing ideal-voltage boundary pattern. Loads keep the
    # production builder's unfilled declarations for the normal regression.
    current_real: Var = grid.var_factory.add_var("source Ir")
    current_imaginary: Var = grid.var_factory.add_var("source Ii")
    generator.rms_model = Block(
        algebraic_vars=list((current_real, current_imaginary)),
        algebraic_eqs=list((source.rms_model.E(VarPowerFlowReferenceType.Vr) - Const(float(pf.voltage[0].real)),
                           source.rms_model.E(VarPowerFlowReferenceType.Vi) - Const(float(pf.voltage[0].imag)))),
        out_vars=list((current_real, current_imaginary)),
        external_mapping=dict(((VarPowerFlowReferenceType.Ir, current_real),
                               (VarPowerFlowReferenceType.Ii, current_imaginary))))
    load: Load
    for load in grid.loads:
        model: Block = get_load_phasor_current_rms_template(grid.var_factory).block
        if authored or not mapped[0]:
            model.set_parameter_in_model(var_name="Pl0", new_value=-0.137)
        else:
            pass
        if authored or not mapped[1]:
            model.set_parameter_in_model(var_name="Ql0", new_value=0.023)
        else:
            pass
        if mapped[0]:
            pass
        else:
            del model.api_obj_mapping[ParamPowerFlowReferenceType.Pl0]
        if mapped[1]:
            pass
        else:
            del model.api_obj_mapping[ParamPowerFlowReferenceType.Ql0]
        if hierarchical:
            # The main equations still consume the first pair. A second child
            # declares distinct event targets with the same API enum keys;
            # flattening must not lose the earlier child's initialization.
            first_child: Block = Block(event_dict=model.event_dict, api_obj_mapping=model.api_obj_mapping)
            second_p: Var = grid.var_factory.add_var("child Pl0")
            second_q: Var = grid.var_factory.add_var("child Ql0")
            second_child: Block = Block(
                event_dict=dict(((second_p, Const(None)), (second_q, Const(None)))),
                api_obj_mapping=dict(((ParamPowerFlowReferenceType.Pl0, second_p),
                                      (ParamPowerFlowReferenceType.Ql0, second_q))))
            model.event_dict = dict()
            model.api_obj_mapping = dict()
            model.children = list((first_child, second_child))
        else:
            pass
        # This unrelated supported mapping must retain its authored expression;
        # CurrentBalance supplies only load P/Q in this increment.
        frequency: Var = grid.var_factory.add_var("authored load frequency")
        model.event_dict[frequency] = Const(12.5)
        model.api_obj_mapping[ParamPowerFlowReferenceType.freq] = frequency
        set_rms_model(load, model, grid.var_factory)
        if equivalent_uid:
            owner: Block
            for owner in load.rms_model.get_all_blocks():
                reference: ParamPowerFlowReferenceType
                parameter: Var
                for reference, parameter in tuple(owner.api_obj_mapping.items()):
                    owner.api_obj_mapping[reference] = Var(name=parameter.name, uid=parameter.uid)
        else:
            pass
    target.is_dc = dc
    return grid, pf


@pytest.mark.parametrize(
    "powers,system_base,nominal_ratio,mapped,equivalent_uid,hierarchical,active,use_kw,dc,authored",
    (
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), False, False, True, False, False, False),
        (((-0.2, -0.02), (0.0, 0.0)), 5.0, 1.0 / 0.97, (True, True), False, False, True, False, False, False),
        (((0.0, 0.02), (0.35, 0.0)), 1.0, 1.0, (True, True), False, False, True, False, False, False),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), True, False, True, False, False, False),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), True, True, True, False, False, False),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), False, False, True, False, False, True),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (False, False), False, False, True, False, False, True),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, False), False, False, True, False, False, False),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (False, True), False, False, True, False, False, False),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), False, False, False, False, False, True),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), False, False, True, True, False, True),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), False, False, True, False, True, True),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), False, False, False, False, False, False),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), False, False, True, True, False, False),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (True, True), False, False, True, False, True, False),
        (((200.0, 20.0), (350.0, -40.0)), 2.0, 0.97, (True, True), True, True, True, True, False, False),
        (((200.0, 20.0), (350.0, -40.0)), 2.0, 0.97, (True, True), True, True, False, True, False, False),
        (((200.0, 20.0), (350.0, -40.0)), 2.0, 0.97, (True, False), False, False, True, True, False, False),
        (((200.0, 20.0), (350.0, -40.0)), 2.0, 0.97, (False, True), False, False, False, True, False, False),
        (((0.2, 0.02), (0.35, -0.04)), 2.0, 0.97, (False, True), False, False, False, False, False, False),
    ))
def test_current_balance_load_parameter_supply(
        powers: tuple[tuple[float, float], ...], system_base: float,
        nominal_ratio: float, mapped: tuple[bool, bool], equivalent_uid: bool,
        hierarchical: bool, active: bool, use_kw: bool, dc: bool, authored: bool) -> None:
    """Qualify native load initialization, hierarchy identity and scope boundaries.

    :param powers: Physical per-device active/reactive load powers.
    :param system_base: MVA normalization base.
    :param nominal_ratio: Terminal voltage-base ratio.
    :param mapped: Whether P and Q independently retain their API mappings.
    :param equivalent_uid: Exercise distinct instances of the same target UID.
    :param hierarchical: Exercise repeated enum keys in different children.
    :param active: Initial physical activity; inactive mapped power is zero.
    :param use_kw: Exercise equivalent source powers expressed in kW/kVAr.
    :param dc: Exercise the explicitly excluded DC path.
    :param authored: Retain or override deliberately authored event expressions.
    :return: None.
    """
    grid: MultiCircuit
    pf: PowerFlowResults
    grid, pf = build_current_balance_load_case(
        powers, system_base, nominal_ratio, mapped, equivalent_uid,
        hierarchical, active, use_kw, dc, authored)
    # Retain declarations and owner-local target identities before the normal
    # flattening operation; tree shape itself is intentionally not preserved.
    declarations: dict[int, Const] = dict()
    declaration_values: dict[int, float | None] = dict()
    targets: list[tuple[Block, ParamPowerFlowReferenceType, int]] = list()
    load: Load
    for load in grid.loads:
        owner: Block
        for owner in load.rms_model.get_all_blocks():
            parameter: Var
            expression: Expr | Const
            for parameter, expression in owner.event_dict.items():
                assert isinstance(expression, Const)
                declarations[parameter.uid] = expression
                declaration_values[parameter.uid] = None if expression.value is None else float(expression.value)
            reference: ParamPowerFlowReferenceType
            for reference, parameter in owner.api_obj_mapping.items():
                targets.append((owner, reference, parameter.uid))
    eligible: bool = not dc
    unit_scale: float = 1000.0 if use_kw else 1.0
    options: RmsOptions = RmsOptions(problem_type=RmsProblemTypes.CurrentBalance)
    if not eligible and not authored:
        # The DC default-builder path remains outside balanced AC supply.
        with pytest.raises(Exception, match="Event parameter Pl0 has None Value"):
            build_rms_problem(grid=grid, options=options, pf_results=pf)
    else:
        problem: RmsProblemTemplate = build_rms_problem(grid=grid, options=options, pf_results=pf)
        assert isinstance(problem, RmsProblemPhasor)
        problem.set_events_group(RmsEventsGroup())
        seed: np.ndarray = problem.get_x0()
        derivatives: np.ndarray = np.zeros(problem.get_diff_var_number())
        for load in grid.loads:
            for parameter, expression in load.rms_model.event_dict.items():
                assert expression is declarations[parameter.uid]
                index: int = problem._uid2idx_event_params[parameter.uid]
                if parameter.name in ("Pl0", "child Pl0"):
                    expected: float = (-load.P / (system_base * unit_scale) if active else 0.0) if eligible and mapped[0] else -0.137
                elif parameter.name in ("Ql0", "child Ql0"):
                    expected = (-load.Q / (system_base * unit_scale) if active else 0.0) if eligible and mapped[1] else 0.023
                else:
                    expected = 12.5
                assert problem._variable_parameters_values[index] == pytest.approx(expected)
        if eligible:
            projected: np.ndarray
            initialized: bool
            residual: float
            projected, initialized, residual = project_initial_algebraic_state(
                problem=problem, initial_values=seed, differential_values=derivatives,
                tolerance=1.0e-9, max_iter=25)
            assert initialized and residual <= 1.0e-9
            voltage: complex = complex(
                projected[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vr))],
                projected[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vi))])
            if mapped[0] and mapped[1]:
                assert abs(voltage - pf.voltage[1]) < 1.0e-9
            else:
                pass
            for load in grid.loads:
                power: complex = complex(
                    (-load.P / (system_base * unit_scale) if active else 0.0) if mapped[0] else -0.137,
                    (-load.Q / (system_base * unit_scale) if active else 0.0) if mapped[1] else 0.023)
                current: complex = complex(
                    projected[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ir))],
                    projected[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ii))])
                assert abs(current - np.conj(power / voltage)) < 1.0e-9
                assert abs(voltage * np.conj(current) - power) < 1.0e-9
        else:
            pass
        problem.close_fmu_cs_devices()
        problem.close_fmu_me_devices()
    owner: Block
    reference: ParamPowerFlowReferenceType
    target_uid: int
    for owner, reference, target_uid in targets:
        assert owner.api_obj_mapping[reference].uid == target_uid
    for load in grid.loads:
        for parameter, expression in load.rms_model.event_dict.items():
            assert expression is declarations[parameter.uid]
            assert expression.value == declaration_values[parameter.uid]
    assert tuple((load.P, load.Q) for load in grid.loads) == powers
    assert all(load.active == active and load.use_kw == use_kw for load in grid.loads)


@pytest.mark.parametrize("active,use_kw", ((True, False), (True, True), (False, False), (False, True)))
def test_current_balance_load_parameter_events(active: bool, use_kw: bool) -> None:
    """Project independent step P/Q events and restore mapped baseline values.

    :param active: Initial physical activity retained during explicit steps.
    :param use_kw: Store equivalent source powers in kW/kVAr.
    :return: None.
    """
    grid: MultiCircuit
    pf: PowerFlowResults
    unit_scale: float = 1000.0 if use_kw else 1.0
    powers: tuple[tuple[float, float], ...] = ((0.2 * unit_scale, 0.02 * unit_scale),
                                            (0.35 * unit_scale, -0.04 * unit_scale))
    grid, pf = build_current_balance_load_case(powers, 2.0, 0.97, active=active, use_kw=use_kw)
    baseline: complex = complex(-0.1, -0.01) if active else complex(0.0, 0.0)
    load: Load = grid.loads[0]
    active_parameter: Var = load.rms_model.api_obj_mapping[ParamPowerFlowReferenceType.Pl0]
    reactive_parameter: Var = load.rms_model.api_obj_mapping[ParamPowerFlowReferenceType.Ql0]
    declared_active: Expr | Const = load.rms_model.event_dict[active_parameter]
    declared_reactive: Expr | Const = load.rms_model.event_dict[reactive_parameter]
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(device=load, parameter=active_parameter, time=0.1, value=-0.16, group=group))
    grid.add_rms_event(RmsEvent(device=load, parameter=reactive_parameter, time=0.2, value=0.015, group=group))
    problem: RmsProblemTemplate = build_rms_problem(
        grid=grid, options=RmsOptions(problem_type=RmsProblemTypes.CurrentBalance), pf_results=pf)
    assert isinstance(problem, RmsProblemPhasor)
    problem.set_events_group(group)
    state: np.ndarray = problem.get_x0()
    derivatives: np.ndarray = np.zeros(problem.get_diff_var_number())
    time_value: float
    expected_power: complex
    for time_value, expected_power in ((0.0, baseline),
                                       (0.15, complex(-0.16, baseline.imag)),
                                       (0.25, complex(-0.16, 0.015))):
        problem.update_variable_params(time_value)
        assert problem._variable_parameters_values[problem._uid2idx_event_params[active_parameter.uid]] == pytest.approx(expected_power.real)
        assert problem._variable_parameters_values[problem._uid2idx_event_params[reactive_parameter.uid]] == pytest.approx(expected_power.imag)
        initialized: bool
        residual: float
        state, initialized, residual = project_initial_algebraic_state(
            problem=problem, initial_values=state, differential_values=derivatives,
            tolerance=1.0e-9, max_iter=25)
        assert initialized and residual <= 1.0e-9
        voltage: complex = complex(
            state[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vr))],
            state[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vi))])
        current: complex = complex(
            state[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ir))],
            state[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ii))])
        assert abs(current - np.conj(expected_power / voltage)) < 1.0e-9
        assert abs(voltage * np.conj(current) - expected_power) < 1.0e-9
        assert isinstance(declared_active, Const) and declared_active.value is None
        assert isinstance(declared_reactive, Const) and declared_reactive.value is None
    # Selecting an empty group must recover provider initialization even after
    # the previous group's events changed both runtime set-points.
    problem.set_events_group(RmsEventsGroup())
    assert problem._variable_parameters_values[problem._uid2idx_event_params[active_parameter.uid]] == pytest.approx(baseline.real)
    assert problem._variable_parameters_values[problem._uid2idx_event_params[reactive_parameter.uid]] == pytest.approx(baseline.imag)
    state, initialized, residual = project_initial_algebraic_state(
        problem=problem, initial_values=state, differential_values=derivatives,
        tolerance=1.0e-9, max_iter=25)
    assert initialized and residual <= 1.0e-9
    assert load.rms_model.event_dict[active_parameter] is declared_active
    assert load.rms_model.event_dict[reactive_parameter] is declared_reactive
    assert load.rms_model.api_obj_mapping[ParamPowerFlowReferenceType.Pl0].uid == active_parameter.uid
    assert load.rms_model.api_obj_mapping[ParamPowerFlowReferenceType.Ql0].uid == reactive_parameter.uid
    assert (load.P, load.Q, load.active, load.use_kw) == (powers[0][0], powers[0][1], active, use_kw)
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


@pytest.mark.parametrize('active_stall', (False, True))
def test_wt2_unsaturated_host_matches_connected_power_flow_q_with_hidden_shunt(
        active_stall: bool) -> None:
    """Attach a Type 2 machine to a live bus and preserve initial PF P/Q.

    :param active_stall: Select the WT12A1U_B mechanical controller.
    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_current_balance_load_case(
        powers=((10., 1.),), system_base=100., nominal_ratio=1.,
    )
    wind: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='WT2 source', P=30., Snom=50.),
    )
    wind.is_controlled = False
    pf: PowerFlowResults
    machine_settings: Wt2g1ElectricalSettings
    pf = power_flow(grid=grid)
    assert pf.converged
    machine_settings = derive_wt2g1_operating_point(
        source=Wt2g1ElectricalSettings(),
        target_power=float(pf.gen_p[1] / wind.Snom),
        voltage_d=-float(pf.voltage[1].imag),
        voltage_q=float(pf.voltage[1].real),
        curve=Wt2e1Settings().curve,
    )
    stall_vt4: float = abs(pf.voltage[1]) - .02
    host: RmsModelTemplate = build_wt2_current_balance_host(
        grid.var_factory, name='WT2 source', machine_settings=machine_settings,
        active_stall_settings=Wt12a1uBSettings(
            tr=0., t0=.01, pset=.4,
            curve=((stall_vt4 - .3, .006), (stall_vt4 - .2, .005),
                   (stall_vt4 - .1, .004), (stall_vt4, .003)),
        ) if active_stall else None,
    )
    if active_stall:
        assert len(host.block.procedural_logic) == 1
    else:
        assert len(host.block.procedural_logic) == 0
    grid.add_rms_model(host)
    wind.rms_template = host
    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid, options=RmsOptions(problem_type=RmsProblemTypes.CurrentBalance), pf_results=pf,
    )
    group: RmsEventsGroup = RmsEventsGroup()
    if active_stall:
        load_q: Var = next(parameter for parameter in grid.loads[0].rms_model.event_dict
                           if parameter.name.startswith('Ql0'))
        grid.add_rms_event(RmsEvent(
            device=grid.loads[0], parameter=load_q, time=.001, value=-.3,
            group=group,
        ))
        grid.add_rms_event(RmsEvent(
            device=grid.loads[0], parameter=load_q, time=.005, value=.01,
            group=group,
        ))
    else:
        pass
    problem.set_events_group(rms_events_group=group)
    projected: np.ndarray
    initialized: bool
    residual: float
    projected, initialized, residual = project_initial_algebraic_state(
        problem=problem, initial_values=problem.get_x0(),
        differential_values=problem.get_dx0(), tolerance=1.0e-8, max_iter=25,
    )
    assert initialized and residual <= 1.0e-8
    if active_stall:
        assert len(wind.rms_model.procedural_logic) == 1
        assert problem._procedural_logic_updater is not None
        assert wind.rms_model.procedural_logic[0].trigger_expr in wind.rms_model.algebraic_vars
        qualification: Var = next(variable for variable in wind.rms_model.algebraic_vars
                                  if variable.name.startswith('QualifiedVoltageDip_'))
        duration: Var = next(variable for variable in wind.rms_model.algebraic_vars
                             if variable.name.startswith('DurationSeconds_'))
        assert projected[problem.get_var_idx(qualification)] == pytest.approx(0.)
        assert projected[problem.get_var_idx(duration)] == pytest.approx(0.)
    else:
        pass
    network_p: Var = wind.rms_model.E(VarPowerFlowReferenceType.P)
    network_q: Var = wind.rms_model.E(VarPowerFlowReferenceType.Q)
    assert projected[problem.get_var_idx(network_p)] == pytest.approx(pf.gen_p[1] / grid.Sbase, abs=1e-7)
    assert projected[problem.get_var_idx(network_q)] == pytest.approx(pf.gen_q[1] / grid.Sbase, abs=1e-7)
    machine_q: Var = wind.rms_model.out_vars[1]
    machine_q_seed: Expr = wind.rms_model.init_eqs[machine_q]
    assert isinstance(machine_q_seed, Const)
    shunt: Var | None = None
    event_parameter: Var
    for event_parameter in wind.rms_model.event_dict:
        if event_parameter.name.startswith('HiddenQShuntMachinePu_'):
            shunt = event_parameter
        else:
            pass
    assert shunt is not None
    shunt_index: int = problem._uid2idx_event_params[shunt.uid]
    shunt_value: float = problem._variable_parameters_values[shunt_index]
    assert shunt_value == pytest.approx(pf.gen_q[1] / wind.Snom - float(machine_q_seed.value), abs=1e-7)
    initial_voltage: complex = complex(
        projected[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vr))],
        projected[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vi))],
    )
    problem._variable_parameters_values[shunt_index] += .02
    disturbed: np.ndarray
    disturbed, initialized, residual = project_initial_algebraic_state(
        problem=problem, initial_values=projected,
        differential_values=problem.get_dx0(), tolerance=1.0e-8, max_iter=25,
    )
    assert initialized and residual <= 1e-8
    assert disturbed[problem.get_var_idx(network_q)] > projected[problem.get_var_idx(network_q)]
    disturbed_voltage: complex = complex(
        disturbed[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vr))],
        disturbed[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vi))],
    )
    assert abs(disturbed_voltage - initial_voltage) > 1e-8
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.008 if active_stall else .002,
        h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    assert np.all(np.isfinite(values))
    if active_stall:
        ramp: Var = next(variable for variable in wind.rms_model.state_vars
                         if variable.name.startswith('PowerRampPu_'))
        ramp_index: int = problem.get_var_idx(ramp)
        voltage_real_index: int = problem.get_var_idx(
            grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vr),
        )
        voltage_imag_index: int = problem.get_var_idx(
            grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vi),
        )
        voltage_magnitudes: np.ndarray = np.hypot(
            values[:, voltage_real_index], values[:, voltage_imag_index],
        )
        assert voltage_magnitudes[2] < voltage_magnitudes[0] - .02
        assert voltage_magnitudes[6] > voltage_magnitudes[2] + .02
        assert values[2, problem.get_var_idx(qualification)] == pytest.approx(1.)
        assert values[6, problem.get_var_idx(qualification)] == pytest.approx(0.)
        assert float(np.min(values[:, ramp_index])) < values[0, ramp_index] - 1e-4
        stall_mode: Var = next(iter(wind.rms_model.mode_dict))
        assert problem._variable_parameters_values[
            problem._uid2idx_event_params[stall_mode.uid]
        ] == pytest.approx(0.)
    else:
        pass
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


@pytest.mark.parametrize("select_group", (False, True))
@pytest.mark.parametrize("active,use_kw", ((True, False), (True, True), (False, False), (False, True)))
@pytest.mark.parametrize("resolved_source_expr", (False, True))
@pytest.mark.parametrize("start,end_time,stored_none", (
    (0.1, 0.2, False), (0.1, None, True), (0.1, 0.1, False),
    (0.1, 0.05, False), (0.0, None, False), (0.1, None, False),
))
def test_current_balance_ramp_event_runtime(
        select_group: bool, active: bool, use_kw: bool, resolved_source_expr: bool,
        start: float, end_time: float | None, stored_none: bool) -> None:
    """Qualify native numeric ramps and retained-expression compatibility.

    :param select_group: Select the concrete group after constructor setup.
    :param active: Initial physical load activity, separate from later events.
    :param use_kw: Supply equivalent physical kW rather than MW source values.
    :param resolved_source_expr: Author P as a source Expr resolved by Explicit initialization.
    :param start: Event start, including zero for the tiny default duration.
    :param end_time: Constructor endpoint; None deliberately exercises omission.
    :param stored_none: Use the public setter to store actual None after construction.
    :return: None; assert independent runtime/power profiles and source invariants.
    """
    unit_scale: float = 1000.0 if use_kw else 1.0
    powers: tuple[tuple[float, float], ...] = ((0.2 * unit_scale, 0.02 * unit_scale),)
    grid: MultiCircuit
    pf: PowerFlowResults
    grid, pf = build_current_balance_load_case(
        powers, 2.0, 0.97, mapped=(not resolved_source_expr, True), active=active, use_kw=use_kw)
    load: Load = grid.loads[0]
    line: Line = grid.lines[0]
    q_target: Var = load.rms_model.api_obj_mapping[ParamPowerFlowReferenceType.Ql0]
    p_target: Var | None = None
    if resolved_source_expr:
        # Author the existing owner-local declaration before flattening; the
        # established initializer resolves its numeric value without rewriting it.
        variable: Var
        for variable in load.rms_model.event_dict:
            if variable.name == "Pl0":
                p_target = variable
            else:
                pass
        assert p_target is not None
        source_expression: Expr = q_target + Const(-0.127)
        owner: Block
        for owner in load.rms_model.get_all_blocks():
            for variable in owner.event_dict:
                if variable.uid == p_target.uid:
                    owner.event_dict[variable] = source_expression
                else:
                    pass
    else:
        p_target = load.rms_model.api_obj_mapping[ParamPowerFlowReferenceType.Pl0]
    assert p_target is not None
    declared_p: Expr | Const = load.rms_model.event_dict[p_target]
    declared_q: Expr | Const = load.rms_model.event_dict[q_target]
    # A Line-owned runtime declaration actually remains Expr in the native
    # Explicit route, unlike the load declaration resolved to Const above.
    dependent_target: Var = grid.var_factory.add_var("retained branch runtime dependency")
    dependent_expression: Expr = q_target + Const(-0.127)
    line.rms_model.event_dict[dependent_target] = dependent_expression
    group: RmsEventsGroup = RmsEventsGroup()
    events: list[RmsEvent] = list((
        RmsEvent(device=load, parameter=p_target, time=start, end_time=end_time,
                 value=-0.16, group=group, transition_type=DynamicEventTransitionType.Ramp),
        RmsEvent(device=load, parameter=q_target, time=start, end_time=end_time,
                 value=-0.04, group=group, transition_type=DynamicEventTransitionType.Ramp),
        RmsEvent(device=line, parameter=dependent_target, time=start, end_time=end_time,
                 value=-0.18, group=group, transition_type=DynamicEventTransitionType.Ramp),
    ))
    event: RmsEvent
    for event in events:
        if stored_none:
            event.end_time = None
        else:
            pass
        grid.add_rms_event(event)
    source_event_state: tuple[tuple[float, float | None, float, DynamicEventTransitionType], ...] = tuple(
        (event.time, event.end_time, event.value, event.transition_type) for event in events)
    logger: Logger = Logger()
    problem: RmsProblemTemplate = build_rms_problem(
        grid, RmsOptions(problem_type=RmsProblemTypes.CurrentBalance), pf, logger=logger)
    assert isinstance(problem, RmsProblemPhasor)
    if select_group:
        problem.set_events_group(group)
    else:
        pass
    p_index: int = problem._uid2idx_event_params[p_target.uid]
    q_index: int = problem._uid2idx_event_params[q_target.uid]
    dependent_index: int = problem._uid2idx_event_params[dependent_target.uid]
    baseline_q: float = -0.01 if active else 0.0
    baseline_p: float = baseline_q - 0.127 if resolved_source_expr else (-0.1 if active else 0.0)
    assert isinstance(problem._event_parameters_eqs0[p_index], Const)
    assert problem._event_parameters_eqs0[p_index].value == pytest.approx(baseline_p)
    assert problem._event_parameters_eqs0[dependent_index] is dependent_expression
    state: np.ndarray = problem.get_x0()
    derivatives: np.ndarray = np.zeros(problem.get_diff_var_number())
    initialized: bool
    residual: float
    resolved_end: float | None = events[0].end_time
    sample_times: tuple[float, ...] = (0.0, 0.1, 0.125, 0.15, 0.175, 0.2, 0.25)
    if start == 0.0:
        assert resolved_end == 1e-20
        sample_times = (0.0, 5e-21, 1e-20, 2e-20)
    else:
        pass
    sample: float
    for sample in sample_times:
        if resolved_end is not None and resolved_end > start:
            progress: float = min(1.0, max(0.0, (sample - start) / (resolved_end - start)))
            expected_power: complex = complex(
                baseline_p + progress * (-0.16 - baseline_p),
                baseline_q + progress * (-0.04 - baseline_q))
        else:
            expected_power = complex(-0.16, -0.04) if sample > start else complex(baseline_p, baseline_q)
        previous_q: float = float(problem._variable_parameters_values[q_index])
        expected_dependent: float = -0.18 if sample > start else previous_q - 0.127
        problem.update_variable_params(sample, scheduled_t=0.0)
        assert problem._variable_parameters_values[p_index] == pytest.approx(expected_power.real, abs=1e-12, rel=0.0)
        assert problem._variable_parameters_values[q_index] == pytest.approx(expected_power.imag, abs=1e-12, rel=0.0)
        assert problem._variable_parameters_values[dependent_index] == pytest.approx(expected_dependent, abs=1e-12, rel=0.0)
        state, initialized, residual = project_initial_algebraic_state(problem, state, derivatives, 1e-9, 25)
        assert initialized and residual <= 1e-9
        voltage: complex = complex(
            state[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vr))],
            state[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vi))])
        current: complex = complex(
            state[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ir))],
            state[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ii))])
        assert abs(voltage * np.conj(current) - expected_power) <= 1e-9
        assert abs(current - np.conj(expected_power / voltage)) <= 1e-9
    entry: LogEntry
    warning_count: int = sum(entry.severity == LogSeverity.Warning and "Ramp" in entry.msg for entry in logger.entries)
    assert warning_count == (2 if select_group else 1)
    assert dependent_index not in problem._continuous_runtime_events
    # Empty selection restores initialized numeric values and the original Expr,
    # without a warning for an event that is no longer selected.
    problem.set_events_group(RmsEventsGroup())
    assert problem._variable_parameters_values[p_index] == pytest.approx(baseline_p, abs=1e-12, rel=0.0)
    assert problem._variable_parameters_values[q_index] == pytest.approx(baseline_q, abs=1e-12, rel=0.0)
    assert problem._variable_parameters_values[dependent_index] == pytest.approx(baseline_q - 0.127, abs=1e-12, rel=0.0)
    assert sum(entry.severity == LogSeverity.Warning and "Ramp" in entry.msg for entry in logger.entries) == warning_count
    assert load.rms_model.event_dict[p_target] is declared_p
    assert load.rms_model.event_dict[q_target] is declared_q
    assert line.rms_model.event_dict[dependent_target] is dependent_expression
    assert (load.P, load.Q, load.active, load.use_kw) == (powers[0][0], powers[0][1], active, use_kw)
    assert tuple((event.time, event.end_time, event.value, event.transition_type) for event in grid.rms_events) == source_event_state
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


@pytest.mark.parametrize("select_group,reverse_order", ((False, False), (False, True), (True, False), (True, True)))
@pytest.mark.parametrize("history", tuple(range(8)))
def test_current_balance_ramp_event_sequences(select_group: bool, reverse_order: bool, history: int) -> None:
    """Qualify replay, ordering, legacy Steps and runtime selection/reset.

    :param select_group: Exercise constructor-only or concrete-group setup.
    :param reverse_order: Reverse stored mixed histories without changing chronology.
    :param history: Nonoverlap, mixed, overlap, ties, Steps, duration or initial-time case.
    :return: None; assert independent ordinary profiles and established-owner parity.
    """
    grid: MultiCircuit
    pf: PowerFlowResults
    grid, pf = build_current_balance_load_case(((0.2, 0.02),), 2.0, 0.97)
    load: Load = grid.loads[0]
    line: Line = grid.lines[0]
    p_target: Var = load.rms_model.api_obj_mapping[ParamPowerFlowReferenceType.Pl0]
    q_target: Var = load.rms_model.api_obj_mapping[ParamPowerFlowReferenceType.Ql0]
    group: RmsEventsGroup = RmsEventsGroup()
    specifications: tuple[tuple[DynamicEventTransitionType, float, float | None, float], ...]
    if history == 0:
        specifications = ((DynamicEventTransitionType.Ramp, 0.1, 0.2, -0.16),
                          (DynamicEventTransitionType.Ramp, 0.3, 0.4, -0.04))
    elif history == 1:
        specifications = ((DynamicEventTransitionType.Step, 0.05, None, -0.08),
                          (DynamicEventTransitionType.Ramp, 0.1, 0.2, -0.16),
                          (DynamicEventTransitionType.Step, 0.25, None, -0.02))
    elif history == 2:
        specifications = ((DynamicEventTransitionType.Ramp, 0.1, 0.2, -0.16),
                          (DynamicEventTransitionType.Ramp, 0.15, 0.25, 0.0))
    elif history == 3:
        specifications = ((DynamicEventTransitionType.Ramp, 0.1, 0.2, -0.16),
                          (DynamicEventTransitionType.Ramp, 0.1, 0.2, -0.04))
    elif history == 4:
        specifications = ((DynamicEventTransitionType.Step, 0.25, None, -0.02),
                          (DynamicEventTransitionType.Step, 0.05, None, -0.08))
    elif history == 5:
        specifications = ((DynamicEventTransitionType.Ramp, 0.1, 0.2, -0.16),
                          (DynamicEventTransitionType.Ramp, 0.1, 0.3, -0.04))
    elif history == 6:
        specifications = ((DynamicEventTransitionType.Ramp, 0.0, None, -0.16),
                          (DynamicEventTransitionType.Step, 0.05, None, -0.08))
    else:
        specifications = ((DynamicEventTransitionType.Ramp, -0.2, -0.1, -0.16),
                          (DynamicEventTransitionType.Step, 0.25, None, -0.02))
    tpe: DynamicEventTransitionType
    start: float
    end: float | None
    final: float
    ordered: list[RmsEvent] = list(RmsEvent(device=load, parameter=p_target, transition_type=tpe,
        time=start, end_time=end, value=final, group=group) for tpe, start, end, final in specifications)
    stored: list[RmsEvent] = list(reversed(ordered)) if reverse_order else ordered.copy()
    event: RmsEvent
    for event in stored:
        grid.add_rms_event(event)
    expected_order: list[RmsEvent] = stored if history in (3, 4) else ordered
    dependent_target: Var = grid.var_factory.add_var("mixed retained branch runtime dependency")
    declaration: Expr = q_target + Const(-0.127)
    line.rms_model.event_dict[dependent_target] = declaration
    branch_transition: DynamicEventTransitionType = DynamicEventTransitionType.Step if history == 4 else DynamicEventTransitionType.Ramp
    branch_events: list[RmsEvent] = list((
        RmsEvent(device=line, parameter=dependent_target, time=0.1, end_time=0.2, value=-0.18,
                 group=group, transition_type=branch_transition),
        RmsEvent(device=line, parameter=dependent_target, time=0.25, value=-0.02, group=group)))
    for event in branch_events:
        grid.add_rms_event(event)
    source_order: tuple[RmsEvent, ...] = tuple(grid.rms_events)
    logger: Logger = Logger()
    problem: RmsProblemTemplate = build_rms_problem(
        grid, RmsOptions(problem_type=RmsProblemTypes.CurrentBalance), pf, logger=logger)
    assert isinstance(problem, RmsProblemPhasor)
    if select_group:
        problem.set_events_group(group)
    else:
        pass
    p_index: int = problem._uid2idx_event_params[p_target.uid]
    dependent_index: int = problem._uid2idx_event_params[dependent_target.uid]
    assert problem._event_parameters_eqs0[dependent_index] is declaration
    assert dependent_index not in problem._continuous_runtime_events
    # Negative-time history proves constructor/group initialization runs replay.
    assert problem._variable_parameters_values[p_index] == pytest.approx(-0.16 if history == 7 else -0.1, abs=1e-12, rel=0.0)
    state: np.ndarray = problem.get_x0()
    derivatives: np.ndarray = np.zeros(problem.get_diff_var_number())
    initialized: bool
    residual: float
    sample_times: tuple[float, ...] = (0.0, 5e-21, 0.05, np.nextafter(0.05, np.inf), 0.075,
        0.1, 0.15, 0.175, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.175, 0.175, 0.0)
    sample: float
    for sample in sample_times:
        expected: float = -0.1
        if history == 4:
            # Legacy piecewise applies stored order, including strict Step edges.
            for event in stored:
                if sample > event.time:
                    expected = event.value
                else:
                    pass
        else:
            expected = _evaluate_rms_runtime_parameter_value_from_events(-0.1, expected_order, sample)
            if history == 0:
                if sample <= 0.1:
                    independent: float = -0.1
                elif sample < 0.2:
                    independent = -0.1 - 0.06 * (sample - 0.1) / 0.1
                elif sample <= 0.3:
                    independent = -0.16
                elif sample < 0.4:
                    independent = -0.16 + 0.12 * (sample - 0.3) / 0.1
                else:
                    independent = -0.04
                assert expected == pytest.approx(independent, abs=1e-12, rel=0.0)
            elif history == 1 and sample != np.nextafter(0.05, np.inf):
                if sample <= 0.05:
                    independent = -0.1
                elif sample <= 0.1:
                    independent = -0.08
                elif sample < 0.2:
                    independent = -0.08 - 0.08 * (sample - 0.1) / 0.1
                elif sample <= 0.25:
                    independent = -0.16
                else:
                    independent = -0.02
                assert expected == pytest.approx(independent, abs=1e-12, rel=0.0)
            elif history == 2 and sample == 0.175:
                # This is known owner compatibility, not a linear-overlap oracle.
                assert expected == pytest.approx(-0.10875, abs=1e-12, rel=0.0)
                assert abs(expected - (-0.0975)) > 1e-3
            else:
                pass
        problem.update_variable_params(sample, scheduled_t=0.0)
        assert problem._variable_parameters_values[p_index] == pytest.approx(expected, abs=1e-12, rel=0.0)
        expected_dependent: float = -0.02 if sample > 0.25 else (-0.18 if sample > 0.1 else -0.137)
        assert problem._variable_parameters_values[dependent_index] == pytest.approx(expected_dependent, abs=1e-12, rel=0.0)
        state, initialized, residual = project_initial_algebraic_state(problem, state, derivatives, 1e-9, 25)
        assert initialized and residual <= 1e-9
        voltage: complex = complex(
            state[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vr))],
            state[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vi))])
        current: complex = complex(
            state[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ir))],
            state[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ii))])
        assert abs(voltage * np.conj(current) - complex(expected, -0.01)) <= 1e-9
    entry: LogEntry
    warning_count: int = sum(entry.severity == LogSeverity.Warning and "Ramp" in entry.msg for entry in logger.entries)
    assert warning_count == (0 if history == 4 else (2 if select_group else 1))
    problem.reset_boundary_update_state(0.175)
    reset_expected: float = _evaluate_rms_runtime_parameter_value_from_events(-0.1, expected_order, 0.175) if history != 4 else -0.08
    assert problem._variable_parameters_values[p_index] == pytest.approx(reset_expected, abs=1e-12, rel=0.0)
    problem.reset_boundary_update_state(0.175)
    assert problem._variable_parameters_values[p_index] == pytest.approx(reset_expected, abs=1e-12, rel=0.0)
    problem.set_events_group(RmsEventsGroup())
    assert len(problem._continuous_runtime_events) == 0
    assert problem._variable_parameters_values[p_index] == pytest.approx(-0.1, abs=1e-12, rel=0.0)
    problem.set_events_group(group)
    problem.update_variable_params(0.175)
    assert problem._variable_parameters_values[p_index] == pytest.approx(reset_expected, abs=1e-12, rel=0.0)
    assert tuple(grid.rms_events) == source_order
    assert line.rms_model.event_dict[dependent_target] is declaration
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


@pytest.mark.parametrize("problem_tpe", (RmsProblemTypes.PowerBalance,
                                       RmsProblemTypes.PowerBalanceVectorized,
                                       RmsProblemTypes.PowerBalanceFullVectorized,
                                       RmsProblemTypes.CurrentBalance))
@pytest.mark.parametrize("active,use_kw", ((True, False), (True, True), (False, False), (False, True)))
def test_balanced_ac_load_native_consumers(
        problem_tpe: RmsProblemTypes, active: bool, use_kw: bool) -> None:
    """Compare four native consumers with fresh physical operating points.

    :param problem_tpe: Existing RMS formulation selected through the factory.
    :param active: Initial physical activity used by both PF and RMS.
    :param use_kw: Store equivalent source powers in kW/kVAr.
    :return: None.
    """
    grid: MultiCircuit
    pf: PowerFlowResults
    if problem_tpe == RmsProblemTypes.CurrentBalance:
        grid, pf = build_current_balance_load_case(((0.2, 0.02),), 2.0, 0.97)
        equivalent_power: complex = complex(-0.1, -0.01)
    else:
        grid, pf = build_supported_vectorized_ac_load_case()
        equivalent_power = complex(-0.09999999, -0.00999999)
        # Replace the historical fixture's numeric initialization workaround
        # with the production builder's unset, API-backed event declarations.
        set_rms_model(grid.loads[0], get_load_rms_template(grid.var_factory).block, grid.var_factory)
    load: Load = grid.loads[0]
    load.active = active
    load.use_kw = use_kw
    if use_kw:
        load.P *= 1000.0
        load.Q *= 1000.0
    else:
        pass
    # Recompute PF after changing the physical representation/activity so its
    # seed cannot conceal a disagreement with the mapped runtime baseline.
    pf = power_flow(grid)
    assert pf.converged
    original: tuple[float, float, bool, bool] = (load.P, load.Q, load.active, load.use_kw)
    declarations: dict[Var, Expr | Const] = dict()
    owner: Block
    for owner in load.rms_model.get_all_blocks():
        declarations.update(owner.event_dict)
    problem: RmsProblemTemplate = build_rms_problem(grid, RmsOptions(problem_type=problem_tpe), pf)
    problem.set_events_group(RmsEventsGroup())
    problem.reset_boundary_update_state(0.0)
    indices: dict[int, int]
    if isinstance(problem, RmsProblemPhasor):
        indices = problem._uid2idx_event_params
    else:
        assert isinstance(problem, (RmsProblemDae, RmsProblemDaeVec, RmsProblemDaeFullVec))
        indices = problem.uid2idx_event_params
    expected_power: complex = equivalent_power if active else complex(0.0, 0.0)
    parameter: Var
    expression: Expr | Const
    for parameter, expression in declarations.items():
        if parameter.name == "Pl0":
            expected_value: float = expected_power.real
        elif parameter.name == "Ql0":
            expected_value = expected_power.imag
        else:
            expected_value = 12.5
        assert problem._variable_parameters_values[indices[parameter.uid]] == pytest.approx(expected_value)
        if parameter.name in ("Pl0", "Ql0"):
            assert isinstance(expression, Const) and expression.value is None
        else:
            pass
    state: np.ndarray = problem.get_x0()
    derivatives: np.ndarray = np.zeros(problem.get_diff_var_number())
    assert float(np.max(np.abs(problem.rhs_algebraic(state, derivatives)))) <= 1.0e-6
    projected: np.ndarray
    initialized: bool
    residual: float
    if isinstance(problem, RmsProblemPhasor):
        projected, initialized, residual = project_initial_algebraic_state(
            problem, state, derivatives, tolerance=1.0e-9, max_iter=25)
        assert initialized and residual <= 1.0e-9
    else:
        # The complete generator fixture is qualified at the PF tolerance;
        # load equations below retain their independent, tighter bound.
        projected = state
    # Check the load's own equations independently of global convergence, then
    # compare the exposed electrical power/current against the physical oracle.
    uid: int
    index: int
    bindings: dict[int, float] = dict((uid, float(projected[index])) for uid, index in problem.uid2idx_vars.items())
    for parameter in declarations:
        bindings[parameter.uid] = float(problem._variable_parameters_values[indices[parameter.uid]])
    for owner in load.rms_model.get_all_blocks():
        equation: Expr
        for equation in owner.algebraic_eqs:
            assert abs(float(equation.eval_uid(bindings))) <= 1.0e-9
    if isinstance(problem, RmsProblemPhasor):
        voltage: complex = complex(
            projected[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vr))],
            projected[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vi))])
        current: complex = complex(
            projected[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ir))],
            projected[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Ii))])
        assert abs(voltage * np.conj(current) - expected_power) <= 1.0e-9
    else:
        assert projected[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.P))] == pytest.approx(expected_power.real)
        assert projected[problem.get_var_idx(load.rms_model.E(VarPowerFlowReferenceType.Q))] == pytest.approx(expected_power.imag)
    for owner in load.rms_model.get_all_blocks():
        for parameter, expression in owner.event_dict.items():
            assert expression is declarations[parameter]
    assert (load.P, load.Q, load.active, load.use_kw) == original
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_rms_shunts_use_network_injection_sign() -> None:
    """Require fixed and controllable RMS shunts to seed injected power.

    Conductance is active-power consumption and therefore has a negative
    injection sign. Positive susceptance is capacitive and therefore has a
    positive reactive-power injection sign.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit(Sbase=100.0)
    bus: Bus = Bus(name="Shunt bus")
    fixed_shunt: Shunt = Shunt(name="Fixed", G=10.0, B=20.0)
    controllable_shunt: ControllableShunt = ControllableShunt(
        name="Controlled",
        number_of_steps=0,
        G=5.0,
        B=-15.0,
    )
    grid.add_bus(bus)
    grid.add_shunt(bus=bus, api_obj=fixed_shunt)
    grid.add_controllable_shunt(bus=bus, api_obj=controllable_shunt)

    # Only the bus voltage participates in the shunt operating-point formula.
    power_flow_results: PowerFlowResults = PowerFlowResults(
        n=1,
        m=0,
        n_hvdc=0,
        n_vsc=0,
        n_gen=0,
        n_batt=0,
        n_sh=2,
        bus_names=np.array((bus.name,), dtype=object),
        branch_names=np.empty(0, dtype=object),
        hvdc_names=np.empty(0, dtype=object),
        vsc_names=np.empty(0, dtype=object),
        gen_names=np.empty(0, dtype=object),
        batt_names=np.empty(0, dtype=object),
        sh_names=np.array(
            (fixed_shunt.name, controllable_shunt.name),
            dtype=object,
        ),
        bus_types=np.zeros(1, dtype=int),
    )
    power_flow_results.voltage[0] = complex(1.0, 0.0)
    problem: RmsProblemTemplate = RmsProblemTemplate()
    problem.grid = grid
    problem.power_flow_results = power_flow_results
    bus_dict: dict[Bus, int] = dict(((bus, 0),))

    fixed_power: complex = problem.get_shunt_injection_data(
        elm=fixed_shunt,
        bus_dict=bus_dict,
    )
    controllable_power: complex = problem.get_controllable_shunt_injection_data(
        elm=controllable_shunt,
        bus_dict=bus_dict,
    )

    assert fixed_power == pytest.approx(complex(-0.10, 0.20))
    assert controllable_power == pytest.approx(complex(-0.05, -0.15))


def test_mapped_power_assembly_uses_physical_topology() -> None:
    """Map DC and AC powers to buses without dynamic diagram connections.

    :return: None.
    """
    dc_power: Var = Var(name="Pdc")
    ac_active_power: Var = Var(name="Pac")
    ac_reactive_power: Var = Var(name="Qac")
    model: Block = Block(
        algebraic_vars=list((dc_power, ac_active_power, ac_reactive_power)),
        algebraic_eqs=list((dc_power, ac_active_power, ac_reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Pf, dc_power),
            (VarPowerFlowReferenceType.Pt, ac_active_power),
            (VarPowerFlowReferenceType.Qt, ac_reactive_power),
        )),
    )
    active_balance: ObjVec = np.zeros(2, dtype=object)
    reactive_balance: ObjVec = np.zeros(2, dtype=object)
    active_used: BoolVec = np.zeros(2, dtype=bool)
    reactive_used: BoolVec = np.zeros(2, dtype=bool)

    assemble_rms_mapped_power_references(
        model=model,
        bus_from_index=0,
        bus_to_index=1,
        bus_from_is_dc=True,
        bus_to_is_dc=False,
        active_power_balance=active_balance,
        active_power_balance_used=active_used,
        reactive_power_balance=reactive_balance,
        reactive_power_balance_used=reactive_used,
    )

    assert active_used.tolist() == [True, True]
    assert reactive_used.tolist() == [False, True]
    assert active_balance[0].eval(Pdc=0.25) == pytest.approx(-0.25)
    assert active_balance[1].eval(Pac=-0.24) == pytest.approx(0.24)
    assert reactive_balance[1].eval(Qac=0.1) == pytest.approx(-0.1)


def test_mapped_power_assembly_rejects_reactive_power_on_dc_bus_atomically() -> None:
    """Reject a domain mismatch before mutating any nodal balance.

    :return: None.
    """
    active_power: Var = Var(name="Pf")
    reactive_power: Var = Var(name="Qf")
    model: Block = Block(
        algebraic_vars=list((active_power, reactive_power)),
        algebraic_eqs=list((active_power, reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Pf, active_power),
            (VarPowerFlowReferenceType.Qf, reactive_power),
        )),
    )
    active_balance: ObjVec = np.zeros(2, dtype=object)
    reactive_balance: ObjVec = np.zeros(2, dtype=object)
    active_used: BoolVec = np.zeros(2, dtype=bool)
    reactive_used: BoolVec = np.zeros(2, dtype=bool)

    with pytest.raises(ValueError, match="reactive power on a DC bus"):
        assemble_rms_mapped_power_references(
            model=model,
            bus_from_index=0,
            bus_to_index=1,
            bus_from_is_dc=True,
            bus_to_is_dc=False,
            active_power_balance=active_balance,
            active_power_balance_used=active_used,
            reactive_power_balance=reactive_balance,
            reactive_power_balance_used=reactive_used,
        )

    assert active_used.tolist() == [False, False]
    assert reactive_used.tolist() == [False, False]


def test_single_bus_device_assembly_uses_selected_power_interface() -> None:
    """Assemble a one-terminal physical device without graphical connections.

    :return: None.
    """
    active_power: Var = Var(name="P")
    reactive_power: Var = Var(name="Q")
    model: Block = Block(
        algebraic_vars=list((active_power, reactive_power)),
        algebraic_eqs=list((active_power, reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.P, active_power),
            (VarPowerFlowReferenceType.Q, reactive_power),
        )),
    )
    active_balance: ObjVec = np.zeros(2, dtype=object)
    reactive_balance: ObjVec = np.zeros(2, dtype=object)
    active_used: BoolVec = np.zeros(2, dtype=bool)
    reactive_used: BoolVec = np.zeros(2, dtype=bool)

    assemble_rms_mapped_power_references(
        model=model,
        active_power_balance=active_balance,
        active_power_balance_used=active_used,
        reactive_power_balance=reactive_balance,
        reactive_power_balance_used=reactive_used,
        bus_index=1,
        bus_is_dc=False,
    )
    assert active_used.tolist() == [False, True]
    assert reactive_used.tolist() == [False, True]
    assert active_balance[1].eval(P=0.2) == pytest.approx(0.2)
    assert reactive_balance[1].eval(Q=-0.1) == pytest.approx(-0.1)


def test_standard_vsc_template_uses_mapped_terminal_powers() -> None:
    """Keep VSC topology separate from its mapped dynamic quantities.

    :return: None.
    """
    model: Block = build_vsc_rms(vfactory=VarFactory()).block
    assert model.out_vars == list()
    assert "rms_terminal_power_contributions" not in DynamicModelContract.__slots__
    assert VarPowerFlowReferenceType.Pf in model.external_mapping
    assert VarPowerFlowReferenceType.Pt in model.external_mapping
    assert VarPowerFlowReferenceType.Qt in model.external_mapping


def test_mapped_bus_power_requires_one_terminal_topology() -> None:
    """Reject a P/Q mapping when its static bus topology is absent."""
    active_power = Var(name="P")
    model = Block(external_mapping={VarPowerFlowReferenceType.P: active_power})

    with pytest.raises(
        ValueError,
        match="RMS bus terminal requires one-terminal device topology",
    ):
        assemble_rms_mapped_power_references(
            model=model,
            active_power_balance=np.zeros(1, dtype=object),
            active_power_balance_used=np.zeros(1, dtype=bool),
            reactive_power_balance=np.zeros(1, dtype=object),
            reactive_power_balance_used=np.zeros(1, dtype=bool),
        )


def test_mapped_to_power_requires_two_terminal_topology() -> None:
    """Reject a Pt/Qt mapping when its static to-side topology is absent."""
    active_power = Var(name="Pt")
    model = Block(external_mapping={VarPowerFlowReferenceType.Pt: active_power})

    with pytest.raises(
        ValueError,
        match="RMS to terminal requires two-terminal device topology",
    ):
        assemble_rms_mapped_power_references(
            model=model,
            active_power_balance=np.zeros(1, dtype=object),
            active_power_balance_used=np.zeros(1, dtype=bool),
            reactive_power_balance=np.zeros(1, dtype=object),
            reactive_power_balance_used=np.zeros(1, dtype=bool),
        )


def test_mapped_reactive_power_rejects_dc_topology() -> None:
    """Reject Q at a DC bus before mutating either nodal balance."""
    reactive_power = Var(name="Q")
    model = Block(external_mapping={VarPowerFlowReferenceType.Q: reactive_power})

    with pytest.raises(
        ValueError,
        match="RMS terminal declares reactive power on a DC bus",
    ):
        assemble_rms_mapped_power_references(
            model=model,
            active_power_balance=np.zeros(1, dtype=object),
            active_power_balance_used=np.zeros(1, dtype=bool),
            reactive_power_balance=np.zeros(1, dtype=object),
            reactive_power_balance_used=np.zeros(1, dtype=bool),
            bus_index=0,
            bus_is_dc=True,
        )


def test_vsc_dc_from_reactive_fallback_keeps_ac_reactive_balance() -> None:
    """A legacy VSC Qf mapping must not enter the DC nodal balance."""
    model = Block(external_mapping={
        VarPowerFlowReferenceType.Pf: Var(name="Pf"),
        VarPowerFlowReferenceType.Qf: Var(name="Qf"),
        VarPowerFlowReferenceType.Pt: Var(name="Pt"),
        VarPowerFlowReferenceType.Qt: Var(name="Qt"),
    })
    active = np.zeros(2, dtype=object)
    reactive = np.zeros(2, dtype=object)
    active_used = np.zeros(2, dtype=bool)
    reactive_used = np.zeros(2, dtype=bool)

    assemble_rms_mapped_power_references(
        model=model,
        active_power_balance=active,
        active_power_balance_used=active_used,
        reactive_power_balance=reactive,
        reactive_power_balance_used=reactive_used,
        bus_from_index=0,
        bus_to_index=1,
        bus_from_is_dc=True,
        bus_to_is_dc=False,
        ignore_dc_from_reactive=True,
    )

    assert active_used.tolist() == [True, True]
    assert reactive_used.tolist() == [False, True]


def test_mapped_power_rejects_mixed_terminal_reference_families() -> None:
    """Reject an ambiguous physical model even when topology is available."""
    model = Block(external_mapping={
        VarPowerFlowReferenceType.P: Var(name="P"),
        VarPowerFlowReferenceType.Pf: Var(name="Pf"),
    })

    with pytest.raises(
        ValueError,
        match="mixes one-terminal and two-terminal power references",
    ):
        assemble_rms_mapped_power_references(
            model=model,
            active_power_balance=np.zeros(2, dtype=object),
            active_power_balance_used=np.zeros(2, dtype=bool),
            reactive_power_balance=np.zeros(2, dtype=object),
            reactive_power_balance_used=np.zeros(2, dtype=bool),
            bus_from_index=0,
            bus_to_index=1,
            bus_from_is_dc=False,
            bus_to_is_dc=False,
        )


def test_gfm_vsc_root_exposes_only_branch_power_references() -> None:
    """Keep internal converter P/Q out of the physical VSC root mapping."""
    model = VscGfmBuild(vfactory=VarFactory()).block

    assert VarPowerFlowReferenceType.P not in model.external_mapping
    assert VarPowerFlowReferenceType.Q not in model.external_mapping
    assert VarPowerFlowReferenceType.Pf in model.external_mapping
    assert VarPowerFlowReferenceType.Qf in model.external_mapping
    assert VarPowerFlowReferenceType.Pt in model.external_mapping
    assert VarPowerFlowReferenceType.Qt in model.external_mapping


def test_hvdc_vsc_v2_declares_reactive_power_only_at_ac_terminal() -> None:
    """The DC terminal has active power but no reactive power reference."""
    model = build_hvdc_vsc_gfl_rms(vfactory=VarFactory()).block

    assert VarPowerFlowReferenceType.Pf in model.external_mapping
    assert VarPowerFlowReferenceType.Qf not in model.external_mapping
    assert VarPowerFlowReferenceType.Pt in model.external_mapping
    assert VarPowerFlowReferenceType.Qt in model.external_mapping

    active = np.zeros(2, dtype=object)
    reactive = np.zeros(2, dtype=object)
    active_used = np.zeros(2, dtype=bool)
    reactive_used = np.zeros(2, dtype=bool)
    assemble_rms_mapped_power_references(
        model=model,
        active_power_balance=active,
        active_power_balance_used=active_used,
        reactive_power_balance=reactive,
        reactive_power_balance_used=reactive_used,
        bus_from_index=0,
        bus_to_index=1,
        bus_from_is_dc=True,
        bus_to_is_dc=False,
    )
    assert active_used.tolist() == [True, True]
    assert reactive_used.tolist() == [False, True]


def build_legacy_vsc_dae_case(
        capacitive_dc_bus: bool = False,
) -> tuple[MultiCircuit, PowerFlowResults]:
    """Build one v1-style VSC case for power-balance constructors.

    :param capacitive_dc_bus: Whether the DC voltage is a capacitive state.
    :return: Grid and power-flow seed data containing a contract-free VSC.
    """
    grid: MultiCircuit = MultiCircuit()
    from_bus: Bus = Bus(name="Legacy VSC DC bus", is_dc=True)
    ac_bus: Bus = Bus(name="Legacy VSC AC bus", is_dc=False)
    grid.add_bus(obj=from_bus)
    grid.add_bus(obj=ac_bus)
    if capacitive_dc_bus:
        initialize_bus_rms(
            bus=from_bus,
            vf=grid.var_factory,
            dc_shunt_capacitance_pu_seconds=0.1,
        )
    else:
        initialize_bus_rms(bus=from_bus, vf=grid.var_factory)
    initialize_bus_rms(bus=ac_bus, vf=grid.var_factory)

    converter: VSC = VSC(
        name="Legacy VSC",
        bus_from=from_bus,
        bus_to=ac_bus,
    )
    from_active_power: Var = grid.var_factory.add_var(
        name="Pf",
        reference=VarPowerFlowReferenceType.Pf,
    )
    to_active_power: Var = grid.var_factory.add_var(
        name="Pt",
        reference=VarPowerFlowReferenceType.Pt,
    )
    to_reactive_power: Var = grid.var_factory.add_var(
        name="Qt",
        reference=VarPowerFlowReferenceType.Qt,
    )
    converter.rms_model = Block(
        algebraic_vars=list((from_active_power, to_active_power, to_reactive_power)),
        algebraic_eqs=list((
            from_active_power,
            to_active_power,
            to_reactive_power,
        )),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Pf, from_active_power),
            (VarPowerFlowReferenceType.Pt, to_active_power),
            (VarPowerFlowReferenceType.Qt, to_reactive_power),
        )),
    )
    grid.add_vsc(obj=converter)

    power_flow_results: PowerFlowResults = PowerFlowResults(
        n=2,
        m=0,
        n_hvdc=0,
        n_vsc=1,
        n_gen=0,
        n_batt=0,
        n_sh=0,
        bus_names=np.array((from_bus.name, ac_bus.name)),
        branch_names=np.array(tuple()),
        hvdc_names=np.array(tuple()),
        vsc_names=np.array((converter.name,)),
        gen_names=np.array(tuple()),
        batt_names=np.array(tuple()),
        sh_names=np.array(tuple()),
        bus_types=np.zeros(2, dtype=int),
    )
    power_flow_results.voltage = np.array((1.0 + 0.0j, 1.0 + 0.0j))
    power_flow_results.Pfp_vsc[0] = 0.20
    power_flow_results.St_vsc[0] = complex(-0.19, 0.03)
    return grid, power_flow_results


def build_legacy_vsc_current_seed_case() -> tuple[MultiCircuit, PowerFlowResults]:
    """Build a VSC case whose RMS model exposes AC current magnitude.

    :return: Grid and power-flow data with a non-unit VSC current seed.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    grid, power_flow_results = build_legacy_vsc_dae_case()
    converter: VSC = grid.get_vsc()[0]
    current_magnitude: Var = grid.var_factory.add_var(
        name="Im",
        reference=VarPowerFlowReferenceType.Im,
    )
    converter.rms_model.algebraic_vars.append(current_magnitude)
    converter.rms_model.algebraic_eqs.append(current_magnitude)
    converter.rms_model.external_mapping[
        VarPowerFlowReferenceType.Im
    ] = current_magnitude
    power_flow_results.It_vsc[0] = complex(7.5, 0.0)
    return grid, power_flow_results


def build_supported_vectorized_ac_load_case(physical_conductance: float = 0.0) -> tuple[MultiCircuit, PowerFlowResults]:
    """Build a supported square RMS case for vectorized initial projection.

    The established generator, line, and load templates provide a physical
    two-bus AC system with a converged power-flow seed. This avoids using the
    independently underdetermined legacy partial-VSC topology as an adapter
    test.

    :param physical_conductance: Total line shunt conductance in per unit.
    :return: Grid and converged power-flow results for vectorized RMS problems.
    """
    # Build the smallest established network fixture that has a voltage angle
    # reference and non-trivial network coupling.
    grid: MultiCircuit = MultiCircuit(Sbase=100.0, fbase=50.0)
    slack_bus: Bus = Bus(name="Bus0", Vnom=10.0, is_slack=True)
    load_bus: Bus = Bus(name="Bus1", Vnom=10.0)
    grid.add_bus(obj=slack_bus)
    grid.add_bus(obj=load_bus)
    initialize_bus_rms(bus=slack_bus, vf=grid.var_factory)
    initialize_bus_rms(bus=load_bus, vf=grid.var_factory)

    # Reuse the same static devices and RMS templates exercised by the
    # established RMS simulation regression.
    line: Line = Line(
        name="line 0-1",
        bus_from=slack_bus,
        bus_to=load_bus,
        r=0.029585798816568046,
        x=0.07100591715976332,
        b=0.03,
        g=physical_conductance,
        rate=900.0,
    )
    load: Load = Load(name="Load1", P=9.999999, Q=0.999999)
    generator: Generator = Generator(
        name="Gen0",
        P=10.0,
        vset=1.0,
        Snom=900.0,
        x1=0.86138701,
        r1=0.3,
        freq=50.0,
    )
    grid.add_line(obj=line)
    grid.add_load(bus=load_bus, api_obj=load)
    grid.add_generator(bus=slack_bus, api_obj=generator)

    generator_model: Block = get_complete_generator_template_rms(
        grid.var_factory
    ).block
    line_model: Block = get_line_rms_template(grid.var_factory).block
    load_model: Block = get_load_rms_template(grid.var_factory).block
    load_model.set_parameter_in_model(var_name="Pl0", new_value=-0.0999999)
    load_model.set_parameter_in_model(
        var_name="Ql0",
        new_value=-0.009999999862208533,
    )
    set_rms_model(
        device=generator,
        model=generator_model,
        var_factory=grid.var_factory,
    )
    set_rms_model(device=line, model=line_model, var_factory=grid.var_factory)
    set_rms_model(device=load, model=load_model, var_factory=grid.var_factory)

    # A real power-flow seed exercises the same initialization boundary used
    # by the driver instead of inventing algebraic values in the test.
    power_flow_results: PowerFlowResults = power_flow(grid=grid)
    return grid, power_flow_results


def test_regca1_high_voltage_current_tracks_khv_on_connected_phasor_network() -> None:
    """Apply the bounded KHV current correction on the live network voltage.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_current_balance_load_case(
        powers=((.5, .05),), system_base=100., nominal_ratio=1.,
    )
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1],
        api_obj=Generator(name='REGCA1 high-voltage boundary', P=.5, Q=.05, Snom=50.),
    )
    renewable.is_controlled = False
    group: RmsEventsGroup = RmsEventsGroup()
    template: RmsModelTemplate = build_regca1_low_voltage_template(
        vf=grid.var_factory,
        name='REGCA1 high-voltage boundary',
        settings=Regca1LowVoltageSettings(volim=.999),
        problem_type=RmsProblemTypes.CurrentBalance,
    )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid)
    assert pf.converged

    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid,
        options=RmsOptions(problem_type=RmsProblemTypes.CurrentBalance),
        pf_results=pf,
    )
    problem.set_events_group(group)
    projected: np.ndarray
    initialized: bool
    residual: float
    projected, initialized, residual = project_initial_algebraic_state(
        problem=problem,
        initial_values=problem.get_x0(),
        differential_values=problem.get_dx0(),
        tolerance=1.e-8,
        max_iter=50,
    )
    assert initialized and residual <= 1.e-8
    voltage_real: Var = renewable.rms_model.E(VarPowerFlowReferenceType.Vr)
    voltage_imaginary: Var = renewable.rms_model.E(VarPowerFlowReferenceType.Vi)
    terminal_voltage: float = float(np.hypot(
        projected[problem.get_var_idx(voltage_real)],
        projected[problem.get_var_idx(voltage_imaginary)],
    ))
    correction: Var = next(
        signal for signal in renewable.rms_model.algebraic_vars
        if signal.name.startswith('HighVoltageReactiveCorrection_')
    )
    assert projected[problem.get_var_idx(correction)] > 0.
    reactive_state: Var = next(
        signal for signal in renewable.rms_model.state_vars
        if signal.name.startswith('ConverterReactiveCurrent_')
    )
    reactive_state_value: float = projected[problem.get_var_idx(reactive_state)]
    expected_correction: float = min(.7 * max(terminal_voltage - .999, 0.),
                                     max(reactive_state_value + 1.2, 0.))
    assert projected[problem.get_var_idx(correction)] == pytest.approx(
        expected_correction, abs=1.e-8,
    )
    load_reactive_order: Var = next(
        parameter for parameter in grid.loads[0].rms_model.event_dict
        if parameter.name.startswith('Ql0')
    )
    load_reactive_index: int = problem._uid2idx_event_params[load_reactive_order.uid]
    problem._variable_parameters_values[load_reactive_index] = -.3
    undervoltage: np.ndarray
    undervoltage_initialized: bool
    undervoltage_residual: float
    undervoltage, undervoltage_initialized, undervoltage_residual = project_initial_algebraic_state(
        problem=problem,
        initial_values=projected,
        differential_values=problem.get_dx0(),
        tolerance=1.e-8,
        max_iter=50,
    )
    assert undervoltage_initialized and undervoltage_residual <= 1.e-8
    assert undervoltage[problem.get_var_idx(correction)] == pytest.approx(0., abs=1.e-8)
    undervoltage_magnitude: float = float(np.hypot(
        undervoltage[problem.get_var_idx(voltage_real)],
        undervoltage[problem.get_var_idx(voltage_imaginary)],
    ))
    assert undervoltage_magnitude < terminal_voltage
    problem._variable_parameters_values[load_reactive_index] = .01
    overvoltage: np.ndarray
    overvoltage_initialized: bool
    overvoltage_residual: float
    overvoltage, overvoltage_initialized, overvoltage_residual = project_initial_algebraic_state(
        problem=problem,
        initial_values=undervoltage,
        differential_values=problem.get_dx0(),
        tolerance=1.e-8,
        max_iter=50,
    )
    assert overvoltage_initialized and overvoltage_residual <= 1.e-8
    overvoltage_magnitude: float = float(np.hypot(
        overvoltage[problem.get_var_idx(voltage_real)],
        overvoltage[problem.get_var_idx(voltage_imaginary)],
    ))
    overvoltage_state_value: float = overvoltage[problem.get_var_idx(reactive_state)]
    expected_overvoltage_correction: float = min(
        .7 * max(overvoltage_magnitude - .999, 0.),
        max(overvoltage_state_value + 1.2, 0.),
    )
    assert overvoltage[problem.get_var_idx(correction)] == pytest.approx(
        expected_overvoltage_correction, abs=1.e-8,
    )
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_renewable_current_host_initializes_from_connected_power_flow(tmp_path: Path) -> None:
    """Verify current and power bases on a loaded two-bus RMS network.

    :param tmp_path: Directory for a native persistence round trip.
    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_current_balance_load_case(
        powers=((10.0, 1.0),), system_base=100.0, nominal_ratio=1.0,
    )
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1],
        api_obj=Generator(name="Renewable", P=4.0, Snom=50.0),
    )
    renewable.is_controlled = False
    host_template: RmsModelTemplate = build_renewable_current_source_host(
        vf=grid.var_factory, name="Renewable", problem_type=RmsProblemTypes.CurrentBalance,
    )
    grid.add_rms_model(host_template)
    renewable.rms_template = host_template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged

    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid, options=RmsOptions(problem_type=RmsProblemTypes.CurrentBalance), pf_results=pf
    )
    problem.set_events_group(rms_events_group=RmsEventsGroup())
    seed: np.ndarray = problem.get_x0()
    projected: np.ndarray
    initialized: bool
    residual: float
    projected, initialized, residual = project_initial_algebraic_state(
        problem=problem, initial_values=seed,
        differential_values=problem.get_dx0(), tolerance=1.0e-8, max_iter=25,
    )
    assert initialized and residual <= 1.0e-8
    active_power: float = projected[
        problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    ]
    reactive_power: float = projected[
        problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.Q))
    ]
    voltage: float = abs(pf.voltage[1])
    machine_ratio: float = renewable.Snom / grid.Sbase
    assert active_power == pytest.approx(pf.gen_p[1] / grid.Sbase, abs=1.0e-8)
    assert reactive_power == pytest.approx(pf.gen_q[1] / grid.Sbase, abs=1.0e-8)
    commands: list[Var] = list(renewable.rms_model.event_dict)
    active_command_index: int = problem._uid2idx_event_params[commands[0].uid]
    reactive_command_index: int = problem._uid2idx_event_params[commands[1].uid]
    assert problem._variable_parameters_values[active_command_index] == pytest.approx(
        pf.gen_p[1] / (voltage * renewable.Snom)
    )
    assert problem._variable_parameters_values[reactive_command_index] == pytest.approx(
        pf.gen_q[1] / (voltage * renewable.Snom)
    )

    # Changing a machine-base current command must change the connected
    # network solution and the injected system-base power together.
    problem._variable_parameters_values[active_command_index] += 0.02
    disturbed: np.ndarray
    disturbed, initialized, residual = project_initial_algebraic_state(
        problem=problem, initial_values=projected,
        differential_values=problem.get_dx0(), tolerance=1.0e-8, max_iter=25,
    )
    assert initialized and residual <= 1.0e-8
    disturbed_power: float = disturbed[
        problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    ]
    assert disturbed_power > active_power
    disturbed_voltage: float = np.hypot(
        disturbed[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vr))],
        disturbed[problem.get_var_idx(grid.buses[1].rms_model.E(VarPowerFlowReferenceType.Vi))],
    )
    assert disturbed_power == pytest.approx(
        disturbed_voltage * problem._variable_parameters_values[active_command_index] * machine_ratio,
        abs=1.0e-8,
    )
    assert abs(disturbed_voltage - voltage) > 1.0e-8
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()

    # The generator keeps the same symbolic host association after both
    # archive loading and a deep circuit clone.
    archive: Path = tmp_path / "renewable-current-host.veragrid"
    FileSave(circuit=grid, file_name=str(archive)).save()
    restored: MultiCircuit = FileOpen(str(archive)).open()
    circuit: MultiCircuit
    for circuit in (restored, restored.copy()):
        restored_generator: Generator = circuit.generators[1]
        assert restored_generator.rms_template is circuit.rms_models[0]
        assert ParamPowerFlowReferenceType.generator_snom_mva in restored_generator.rms_model.api_obj_mapping
        assert ParamPowerFlowReferenceType.Sbase in restored_generator.rms_model.api_obj_mapping
        assert VarPowerFlowReferenceType.P in restored_generator.rms_model.external_mapping
        assert VarPowerFlowReferenceType.Q in restored_generator.rms_model.external_mapping


def test_renewable_current_host_uses_machine_base_in_power_balance() -> None:
    """Verify the polar RMS formulation uses the same current and MVA bases.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name="Polar renewable", P=4.0, Snom=50.0),
    )
    renewable.is_controlled = False
    host: RmsModelTemplate = build_renewable_current_source_host(
        vf=grid.var_factory, name="Polar renewable"
    )
    grid.add_rms_model(host)
    renewable.rms_template = host
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged

    problem: RmsProblemDaeVec = RmsProblemDaeVec(grid=grid, options=RmsOptions(), pf_results=pf)
    problem.set_events_group(rms_events_group=RmsEventsGroup())
    projected: np.ndarray
    initialized: bool
    residual: float
    projected, initialized, residual = project_initial_algebraic_state(
        problem=problem, initial_values=problem.get_x0(),
        differential_values=problem.get_dx0(), tolerance=1.0e-8, max_iter=25,
    )
    assert initialized and residual <= 1.0e-8
    current_command: Var = list(renewable.rms_model.event_dict)[0]
    assert problem._variable_parameters_values[
        problem._uid2idx_event_params[current_command.uid]
    ] == pytest.approx(pf.gen_p[1] / (abs(pf.voltage[1]) * renewable.Snom))
    assert projected[
        problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    ] == pytest.approx(pf.gen_p[1] / grid.Sbase)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0.0, t_end=0.001, h=0.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    assert np.all(np.isfinite(values))
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_renewable_current_host_rejects_unconnected_formulation() -> None:
    """Avoid constructing a current host for a network with no matching ports.

    :return: None.
    """
    with pytest.raises(ValueError, match="network formulation"):
        build_renewable_current_source_host(
            vf=VarFactory(), problem_type=RmsProblemTypes.Tensygrid,
        )


def test_regca1_low_voltage_core_initializes_on_connected_phasor_network() -> None:
    """Keep converter states and network injection at the solved P/Q operating point.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_current_balance_load_case(
        powers=((10.0, 1.0),), system_base=100.0, nominal_ratio=1.0,
    )
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='REGCA core', P=4.0, Snom=50.0),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_regca1_low_voltage_template(
        vf=grid.var_factory, name='REGCA core', problem_type=RmsProblemTypes.CurrentBalance,
    )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid, options=RmsOptions(problem_type=RmsProblemTypes.CurrentBalance),
        pf_results=pf,
    )
    problem.set_events_group(rms_events_group=RmsEventsGroup())
    projected: np.ndarray
    initialized: bool
    residual: float
    projected, initialized, residual = project_initial_algebraic_state(
        problem=problem, initial_values=problem.get_x0(),
        differential_values=problem.get_dx0(), tolerance=1.0e-8, max_iter=25,
    )
    assert initialized and residual <= 1.0e-8
    assert projected[
        problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    ] == pytest.approx(pf.gen_p[1] / grid.Sbase, abs=1.0e-8)
    assert projected[
        problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.Q))
    ] == pytest.approx(pf.gen_q[1] / grid.Sbase, abs=1.0e-8)
    assert len(renewable.rms_model.state_vars) == 3
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_regca1_initializes_active_current_state_from_limited_pf_command() -> None:
    """Use the LVPL-limited current as the initial converter lag state.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit(Sbase=100., fbase=50.)
    source_bus: Bus = grid.add_bus(Bus(name='LVPL source', Vnom=10., is_slack=True))
    renewable_bus: Bus = grid.add_bus(Bus(name='LVPL renewable', Vnom=10.))
    grid.add_line(Line(bus_from=source_bus, bus_to=renewable_bus, r=.02, x=.5))
    source: Generator = grid.add_generator(
        bus=source_bus, api_obj=Generator(name='LVPL source', vset=1.),
    )
    load: Load = grid.add_load(
        bus=renewable_bus, api_obj=Load(name='LVPL load', P=20., Q=4.),
    )
    initialize_bus_phasor_rms(source_bus, grid.var_factory)
    initialize_bus_phasor_rms(renewable_bus, grid.var_factory)
    set_rms_model(
        device=grid.lines[0], model=get_line_phasor_rms_template(grid.var_factory).block,
        var_factory=grid.var_factory,
    )
    set_rms_model(
        device=load, model=get_load_phasor_current_rms_template(grid.var_factory).block,
        var_factory=grid.var_factory,
    )
    source_real: Var = grid.var_factory.add_var('LVPL source Ir')
    source_imaginary: Var = grid.var_factory.add_var('LVPL source Ii')
    source.rms_model = Block(
        algebraic_vars=list((source_real, source_imaginary)),
        algebraic_eqs=list((
            source_bus.rms_model.E(VarPowerFlowReferenceType.Vr) - Const(1.),
            source_bus.rms_model.E(VarPowerFlowReferenceType.Vi) - Const(0.),
        )),
        out_vars=list((source_real, source_imaginary)),
        external_mapping=dict(((VarPowerFlowReferenceType.Ir, source_real),
                              (VarPowerFlowReferenceType.Ii, source_imaginary))),
    )
    renewable: Generator = grid.add_generator(
        bus=renewable_bus,
        api_obj=Generator(name='LVPL renewable', P=100., Snom=50.),
    )
    renewable.is_controlled = False
    settings: Regca1LowVoltageSettings = Regca1LowVoltageSettings(
        brkpt=.99, zerox=.4, lvpl1=.5,
    )
    template: RmsModelTemplate = build_regca1_low_voltage_template(
        vf=grid.var_factory, name='LVPL renewable', settings=settings,
        problem_type=RmsProblemTypes.CurrentBalance,
    )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid)
    assert pf.converged and abs(pf.voltage[1]) < settings.brkpt
    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid, options=RmsOptions(problem_type=RmsProblemTypes.CurrentBalance),
        pf_results=pf,
    )
    problem.set_events_group(RmsEventsGroup())
    active_state: Var = renewable.rms_model.state_vars[0]
    initial_active: float = problem.init_guess[active_state.uid]
    active_command: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('IpCommand_')
    )
    initial_command: float = problem.event_params_init_dict[active_command.uid]
    lvpl_target: float = settings.lvpl1 * (
        abs(pf.voltage[1]) - settings.zerox
    ) / (settings.brkpt - settings.zerox)
    assert initial_command > lvpl_target
    assert initial_active == pytest.approx(lvpl_target, abs=1.e-8)
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_renewable_partial_chain_initializes_regca_from_reeca_limited_current() -> None:
    """Preserve REECA current limiting in the composed REGCA state seed.

    :return: None.
    """
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=VarFactory(), name='Composed LVPL seed',
        converter_settings=Regca1LowVoltageSettings(
            brkpt=.99, zerox=.4, lvpl1=.5,
        ),
        current_limit_settings=Reeca1CurrentLimitSettings(
            reactive_curve=((.2, 1.2), (1.2, 1.2)),
            active_curve=((.2, 1.2), (1.2, 1.2)),
        ),
    )
    block: Block = template.block
    active_state: Var = block.state_vars[0]
    limited_current: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name.startswith('LimitedActiveCommandPu_')
    )
    raw_command: Var = next(
        parameter for parameter in block.event_dict
        if parameter.name.startswith('IpCommand_')
    )
    initialized_active: Expr = block.init_eqs[active_state]
    initialized_variables: set[Var] = set(get_expression_vars(initialized_active))
    assert limited_current in initialized_variables
    assert raw_command not in initialized_variables


def test_renewable_partial_chain_applies_lvpl_to_connected_active_state_seed() -> None:
    """Keep the connected REGCA state within LVPL after REECA composition.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_current_balance_load_case(
        powers=((10., 8.),), system_base=100., nominal_ratio=1.,
    )
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Composed LVPL seed', P=100., Snom=50.),
    )
    renewable.is_controlled = False
    converter_settings: Regca1LowVoltageSettings = Regca1LowVoltageSettings(
        brkpt=.999, zerox=.4, lvpl1=.5,
    )
    current_settings: Reeca1CurrentLimitSettings = Reeca1CurrentLimitSettings(
        imax=2., reactive_curve=((.2, 2.), (1.2, 2.)),
        active_curve=((.2, 2.), (1.2, 2.)),
    )
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Composed LVPL seed',
        converter_settings=converter_settings, current_limit_settings=current_settings,
        problem_type=RmsProblemTypes.CurrentBalance,
    )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid)
    assert pf.converged and abs(pf.voltage[1]) < converter_settings.brkpt
    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid, options=RmsOptions(problem_type=RmsProblemTypes.CurrentBalance),
        pf_results=pf,
    )
    problem.set_events_group(RmsEventsGroup())
    attached: Block = renewable.rms_model
    active_state: Var = attached.state_vars[0]
    limited_output: Var = next(
        variable for variable in attached.algebraic_vars
        if variable.name.startswith('LimitedActiveCommandPu_')
    )
    raw_order: Var = next(
        parameter for parameter in attached.event_dict
        if parameter.name.startswith('IpCommand_')
    )
    assert problem.event_params_init_dict[raw_order.uid] > converter_settings.lvpl1
    assert problem.init_guess[limited_output.uid] > converter_settings.lvpl1
    lvpl_target: float = converter_settings.lvpl1 * (
        abs(pf.voltage[1]) - converter_settings.zerox
    ) / (converter_settings.brkpt - converter_settings.zerox)
    assert problem.init_guess[active_state.uid] == pytest.approx(lvpl_target)
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_regca1_low_voltage_core_integrates_on_connected_polar_network() -> None:
    """Keep all converter memories finite through a network-coupled RMS step.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Polar REGCA core', P=4.0, Snom=50.0),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_regca1_low_voltage_template(
        vf=grid.var_factory, name='Polar REGCA core',
    )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf,
    )
    problem.set_events_group(rms_events_group=RmsEventsGroup())
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.002, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    assert np.all(np.isfinite(values))
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_renewable_partial_chain_integrates_current_limits_on_polar_network() -> None:
    """Connect electrical current limits to converter states and the AC network.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Renewable partial chain', P=4., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Renewable partial chain',
        current_limit_settings=Reeca1CurrentLimitSettings(trv=.03, thld2=.002),
        active_power_settings=Reeca1ActivePowerSettings(tpord=.04),
        reactive_power_settings=Reeca1ConstantQSettings(tiq=.04),
        voltage_support_settings=Reeca1VoltageSupportSettings(
            vdip=.98, kqv=2., thld=.002, iqfrz=.1,
        ),
    )
    assert len(template.block.procedural_logic) == 3
    restored_logic: Block = roundtrip_block(template.block, procedural_logic_codec=ProceduralLogicCodec())
    assert len(restored_logic.procedural_logic) == 3
    assert len(template.block.state_vars) == 6
    limited_active: Var = next(
        signal for signal in template.block.algebraic_vars
        if signal.name.startswith('LimitedActiveCommandPu_')
    )
    assert limited_active.name.startswith('LimitedActiveCommandPu_')
    assert limited_active in get_expression_vars(template.block.state_eqs[0])
    support_current: Var = next(
        signal for signal in template.block.algebraic_vars
        if signal.name.startswith('FaultReactiveCurrentPu_')
    )
    assert support_current in get_expression_vars(template.block.algebraic_eqs[-2])
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    pref_order: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('PrefOrder_')
    )
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=pref_order, time=.001,
        value=pf.gen_p[1] / renewable.Snom + .1, group=group,
    ))
    qext_order: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('QextOrder_')
    )
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=qext_order, time=.002,
        value=pf.gen_q[1] / renewable.Snom + .1, group=group,
    ))
    reactive_load: Var = next(
        parameter for parameter in grid.loads[0].rms_model.children[0].event_dict
        if parameter.name.startswith('Ql0')
    )
    grid.add_rms_event(RmsEvent(
        device=grid.loads[0], parameter=reactive_load, time=.004,
        value=-.3, group=group,
    ))
    grid.add_rms_event(RmsEvent(
        device=grid.loads[0], parameter=reactive_load, time=.008,
        value=.01, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf,
    )
    problem.set_events_group(rms_events_group=group)
    pref_index: int = problem._uid2idx_event_params[pref_order.uid]
    assert problem._variable_parameters_values[pref_index] == pytest.approx(
        pf.gen_p[1] / renewable.Snom, abs=1.e-8,
    )
    qext_index: int = problem._uid2idx_event_params[qext_order.uid]
    assert problem._variable_parameters_values[qext_index] == pytest.approx(
        pf.gen_q[1] / renewable.Snom, abs=1.e-8,
    )
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.014, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    assert np.all(np.isfinite(values))
    p_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    assert values[2, p_index] > values[0, p_index]
    q_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.Q))
    assert values[3, q_index] > values[0, q_index]
    runtime_pord: Var = next(
        state for state in renewable.rms_model.state_vars
        if state.name.startswith('PordPu_')
    )
    pord_index: int = problem.get_var_idx(runtime_pord)
    assert values[-1, pord_index] > values[0, pord_index]
    runtime_support: Var = next(
        signal for signal in renewable.rms_model.algebraic_vars
        if signal.name.startswith('FaultReactiveCurrentPu_')
    )
    support_index: int = problem.get_var_idx(runtime_support)
    runtime_fault: Var = next(
        signal for signal in renewable.rms_model.algebraic_vars
        if signal.name.startswith('VoltageDipFlag_')
    )
    fault_index: int = problem.get_var_idx(runtime_fault)
    assert values[5, fault_index] == pytest.approx(1.)
    assert values[9, fault_index] == pytest.approx(0.)
    assert abs(values[5, support_index]) > 1.e-4
    assert values[9, support_index] == pytest.approx(.1)
    assert values[10, support_index] == pytest.approx(.1)
    assert values[-1, support_index] == pytest.approx(0., abs=1.e-8)
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_renewable_speed_mode_changes_network_power() -> None:
    """Drive the PFLAG speed input through a connected generator event.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Speed-coupled renewable', P=4., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Speed-coupled renewable',
        active_power_settings=Reeca1ActivePowerSettings(
            tpord=.02, mode=Reeca1ActivePowerMode.TORQUE_TIMES_SPEED,
        ),
    )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    speed_order: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('TurbineSpeedOrder_')
    )
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=speed_order, time=.001, value=1.1, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf,
    )
    problem.set_events_group(rms_events_group=group)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.006, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    p_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    assert values[-1, p_index] > values[0, p_index]
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


@pytest.mark.parametrize('initial_speed', (1., 1.05))
def test_renewable_drive_train_feeds_reeca_speed_mode(initial_speed: float) -> None:
    """Connect shaft speed to PFLAG and electrical power to shaft torque.

    :param initial_speed: Shaft speed at the solved operating point.
    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Shaft-coupled renewable', P=4., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Shaft-coupled renewable',
        active_power_settings=Reeca1ActivePowerSettings(
            tpord=.02, mode=Reeca1ActivePowerMode.TORQUE_TIMES_SPEED,
        ),
        drive_train_settings=Wtdta1DriveTrainSettings(
            h=1., htfrac=.25, freq1=2., initial_speed=initial_speed,
        ),
    )
    speed_state: Var = next(
        state for state in template.block.state_vars
        if state.name.startswith('GeneratorSpeedPu_')
    )
    pord_state: Var = next(
        state for state in template.block.state_vars
        if state.name.startswith('PordPu_')
    )
    assert speed_state in get_expression_vars(template.block.state_eqs[
        template.block.state_vars.index(pord_state)
    ])
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    mechanical_order: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('MechanicalPowerOrder_')
    )
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=mechanical_order, time=.001,
        value=pf.gen_p[1] / renewable.Snom + .2, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf,
    )
    problem.set_events_group(rms_events_group=group)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.05, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    runtime_speed: Var = next(
        state for state in renewable.rms_model.state_vars
        if state.name.startswith('GeneratorSpeedPu_')
    )
    speed_index: int = problem.get_var_idx(runtime_speed)
    assert values[-1, speed_index] != pytest.approx(values[0, speed_index], abs=1.e-6)
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_renewable_pitch_drives_aerodynamic_shaft_power() -> None:
    """Route a pitch change through WTARA1 and WTDTA1 into generator speed.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Pitch-coupled renewable', P=4., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Pitch-coupled renewable',
        active_power_settings=Reeca1ActivePowerSettings(
            tpord=.02, mode=Reeca1ActivePowerMode.TORQUE_TIMES_SPEED,
        ),
        drive_train_settings=Wtdta1DriveTrainSettings(h=1., htfrac=.25, freq1=2.),
        aerodynamic_settings=Wtara1AerodynamicSettings(ka=.02, theta0=2.),
    )
    mechanical_signal: Var = next(
        signal for signal in template.block.algebraic_vars
        if signal.name.startswith('MechanicalPowerPu_')
    )
    turbine_speed: Var = next(
        state for state in template.block.state_vars
        if state.name.startswith('TurbineSpeedPu_')
    )
    assert mechanical_signal in get_expression_vars(template.block.state_eqs[
        template.block.state_vars.index(turbine_speed)
    ])
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    pitch_order: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('PitchAngleOrder_')
    )
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=pitch_order, time=.001, value=4., group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf,
    )
    problem.set_events_group(rms_events_group=group)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.05, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    runtime_mechanical: Var = next(
        signal for signal in renewable.rms_model.algebraic_vars
        if signal.name.startswith('MechanicalPowerPu_')
    )
    mechanical_index: int = problem.get_var_idx(runtime_mechanical)
    assert values[-1, mechanical_index] < values[0, mechanical_index] - .1
    runtime_speed: Var = next(
        state for state in renewable.rms_model.state_vars
        if state.name.startswith('GeneratorSpeedPu_')
    )
    speed_index: int = problem.get_var_idx(runtime_speed)
    assert values[-1, speed_index] < values[0, speed_index]
    p_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    assert values[-1, p_index] < values[0, p_index]
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


@pytest.mark.parametrize('torque_mode', (Wttqa1TorqueMode.POWER_ERROR, Wttqa1TorqueMode.SPEED_ERROR))
def test_renewable_torque_controller_feeds_reeca_power_order(torque_mode: Wttqa1TorqueMode) -> None:
    """Connect WTTQA1 filtered Pe, shaft speed and fault flag to REECA1.

    :param torque_mode: Source TFLAG power or speed error path.
    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Torque-coupled renewable', P=4., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Torque-coupled renewable',
        active_power_settings=Reeca1ActivePowerSettings(tpord=.02),
        drive_train_settings=Wtdta1DriveTrainSettings(h=1., htfrac=.25, freq1=2.),
        torque_settings=Wttqa1TorqueSettings(
            tp=.02, twref=.1, mode=torque_mode,
        ),
        voltage_support_settings=Reeca1VoltageSupportSettings(),
    )
    torque_pref: Var = next(
        signal for signal in template.block.algebraic_vars
        if signal.name.startswith('PowerReferencePu_')
    )
    pord_state: Var = next(
        state for state in template.block.state_vars
        if state.name.startswith('PordPu_')
    )
    assert torque_pref in get_expression_vars(template.block.state_eqs[
        template.block.state_vars.index(pord_state)
    ])
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    group: RmsEventsGroup = RmsEventsGroup()
    event_parameter: Var
    event_value: float
    if torque_mode is Wttqa1TorqueMode.POWER_ERROR:
        event_parameter = next(
            parameter for parameter in renewable.rms_model.event_dict
            if parameter.name.startswith('TorquePref0Order_')
        )
        event_value = float(pf.gen_p[1] / renewable.Snom + .1)
    else:
        event_parameter = next(
            parameter for parameter in renewable.rms_model.event_dict
            if parameter.name.startswith('MechanicalPowerOrder_')
        )
        event_value = float(pf.gen_p[1] / renewable.Snom + .2)
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=event_parameter, time=.001,
        value=event_value, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf,
    )
    problem.set_events_group(rms_events_group=group)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.03, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    p_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    assert values[-1, p_index] > values[0, p_index]
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


@pytest.mark.parametrize('plant_enabled', (False, True))
def test_renewable_pitch_controller_drives_aerodynamic_power(plant_enabled: bool) -> None:
    """Route a Type 3 power order through WTPTA1 into WTARA1 and the shaft.

    :param plant_enabled: Route Pref through the REPCTA1 active plant path.
    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Pitch-controlled renewable', P=4., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Pitch-controlled renewable',
        active_power_settings=Reeca1ActivePowerSettings(tpord=.02),
        drive_train_settings=Wtdta1DriveTrainSettings(h=1., htfrac=.25, freq1=2.),
        aerodynamic_settings=Wtara1AerodynamicSettings(ka=.02, theta0=2.),
        torque_settings=Wttqa1TorqueSettings(tp=.02, twref=.1,
                                              mode=Wttqa1TorqueMode.POWER_ERROR),
        pitch_settings=Wtpta1PitchSettings(kiw=1., kpw=2., kic=1., kpc=2.),
        plant_settings=Repca1ActivePlantSettings(kpg=1., kig=5.) if plant_enabled else None,
        voltage_support_settings=Reeca1VoltageSupportSettings(),
    )
    blade: Var = next(state for state in template.block.state_vars
                      if state.name.startswith('PitchAngleDeg_'))
    aerodynamic_power: Var = next(signal for signal in template.block.algebraic_vars
                                  if signal.name.startswith('MechanicalPowerPu_'))
    assert blade in get_expression_vars(template.block.algebraic_eqs[
        template.block.algebraic_vars.index(aerodynamic_power)
    ])
    assert not any(parameter.name.startswith('PitchAngleOrder_') for parameter in template.block.event_dict)
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    pref0: Var
    if plant_enabled:
        pref0 = next(parameter for parameter in renewable.rms_model.event_dict
                     if parameter.name.startswith('PlantPowerOrder_'))
    else:
        pref0 = next(parameter for parameter in renewable.rms_model.event_dict
                     if parameter.name.startswith('TorquePref0Order_'))
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=pref0, time=.001,
        value=float(pf.gen_p[1] / renewable.Snom - .05), group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(grid=grid, options=RmsOptions(), pf_results=pf)
    problem.set_events_group(rms_events_group=group)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.05, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    runtime_blade: Var = next(state for state in renewable.rms_model.state_vars
                              if state.name.startswith('PitchAngleDeg_'))
    blade_index: int = problem.get_var_idx(runtime_blade)
    assert np.max(np.abs(values[:, blade_index] - values[0, blade_index])) > 1.e-5
    runtime_aerodynamic: Var = next(signal for signal in renewable.rms_model.algebraic_vars
                                    if signal.name.startswith('MechanicalPowerPu_'))
    aerodynamic_index: int = problem.get_var_idx(runtime_aerodynamic)
    assert np.max(np.abs(values[:, aerodynamic_index] - values[0, aerodynamic_index])) > 1.e-6
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_reeca1_pref_slew_limits_connected_reference_steps() -> None:
    """Hold Pref rise and fall to the REECA1 source rate bounds.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Slew-limited renewable', P=4., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Slew-limited renewable',
        active_power_settings=Reeca1ActivePowerSettings(
            tpord=0., dpmax=.5, dpmin=-.25,
        ),
    )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    pref_order: Var = next(parameter for parameter in renewable.rms_model.event_dict
                           if parameter.name.startswith('PrefOrder_'))
    group: RmsEventsGroup = RmsEventsGroup()
    initial_pref: float = float(pf.gen_p[1] / renewable.Snom)
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=pref_order, time=.001,
        value=initial_pref + .2, group=group,
    ))
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=pref_order, time=.101,
        value=initial_pref - .2, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(grid=grid, options=RmsOptions(), pf_results=pf)
    problem.set_events_group(rms_events_group=group)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.201, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    runtime_slew: Var = next(state for state in renewable.rms_model.state_vars
                             if state.name.startswith('PrefSlewPu_'))
    slew_index: int = problem.get_var_idx(runtime_slew)
    rise: np.ndarray = np.diff(values[2:101, slew_index]) / np.diff(times[2:101])
    fall: np.ndarray = np.diff(values[103:201, slew_index]) / np.diff(times[103:201])
    assert np.max(rise) <= .50001
    assert np.min(rise) >= -.00001
    assert np.min(fall) >= -.25001
    assert np.max(fall) <= .00001
    assert values[100, slew_index] > values[0, slew_index] + .04
    assert values[200, slew_index] < values[100, slew_index] - .02
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


@pytest.mark.parametrize('frequency_step,order_step,direction', (
    (0., .1, 1.),
    (.01, 0., -1.),
))
def test_repca1_active_plant_path_feeds_connected_reeca1(
        frequency_step: float, order_step: float, direction: float,
) -> None:
    """Feed REPCA1 plant dispatch and frequency droop into REECA1 Pref.

    :param frequency_step: Plant frequency event above nominal.
    :param order_step: Plant power-order event above the solved output.
    :param direction: Expected sign of generator active-power response.
    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Plant-controlled renewable', P=4., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Plant-controlled renewable',
        active_power_settings=Reeca1ActivePowerSettings(tpord=.02),
        plant_settings=Repca1ActivePlantSettings(
            kpg=.5, kig=5., tp=.02, tg=.02, ddn=5., dup=5.,
            frequency_enabled=True,
        ),
    )
    plant_pref: Var = next(state for state in template.block.state_vars
                           if state.name.startswith('PlantPrefPu_'))
    pord: Var = next(state for state in template.block.state_vars
                     if state.name.startswith('PordPu_'))
    assert plant_pref in get_expression_vars(template.block.state_eqs[
        template.block.state_vars.index(pord)
    ])
    assert not any(parameter.name.startswith('PrefOrder_') for parameter in template.block.event_dict)
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    group: RmsEventsGroup = RmsEventsGroup()
    event_parameter: Var
    event_value: float
    if order_step > 0:
        event_parameter = next(parameter for parameter in renewable.rms_model.event_dict
                               if parameter.name.startswith('PlantPowerOrder_'))
        event_value = float(pf.gen_p[1] / renewable.Snom + order_step)
    else:
        event_parameter = next(parameter for parameter in renewable.rms_model.event_dict
                               if parameter.name.startswith('PlantFrequencyOrder_'))
        event_value = 1. + frequency_step
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=event_parameter, time=.001,
        value=event_value, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(grid=grid, options=RmsOptions(), pf_results=pf)
    problem.set_events_group(rms_events_group=group)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.08, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    p_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    assert direction * (values[-1, p_index] - values[0, p_index]) > .001
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


@pytest.mark.parametrize('plant_mode,compensation', (
    (Repca1ReactiveMode.Q_CONTROL, Repca1VoltageCompensation.REACTIVE_DROOP),
    (Repca1ReactiveMode.VOLTAGE_CONTROL, Repca1VoltageCompensation.REACTIVE_DROOP),
    (Repca1ReactiveMode.VOLTAGE_CONTROL, Repca1VoltageCompensation.LINE_DROP),
))
def test_repca1_reactive_plant_modes_feed_connected_reeca1(
        plant_mode: Repca1ReactiveMode, compensation: Repca1VoltageCompensation,
) -> None:
    """Route plant Q or local voltage dispatch through REPCA1 and REECA1.

    :param plant_mode: Source RefFlag path.
    :param compensation: Source VCFlag path in voltage mode.
    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Plant-Q renewable', P=4., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Plant-Q renewable',
        reactive_power_settings=Reeca1ConstantQSettings(tiq=.02),
        plant_reactive_settings=Repca1ReactivePlantSettings(
            kp=1., ki=5., kc=.05, rc=.1, xc=.2,
            mode=plant_mode, compensation=compensation,
        ),
    )
    plant_qext: Var = next(signal for signal in template.block.algebraic_vars
                           if signal.name.startswith('PlantQextPu_'))
    base_iq: Var = next(state for state in template.block.state_vars
                        if state.name.startswith('BaseReactiveCurrentPu_'))
    assert plant_qext in get_expression_vars(template.block.state_eqs[
        template.block.state_vars.index(base_iq)
    ])
    assert not any(parameter.name.startswith('QextOrder_') for parameter in template.block.event_dict)
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    order: Var
    order_value: float
    if plant_mode is Repca1ReactiveMode.VOLTAGE_CONTROL:
        voltage_filter: Var = next(state for state in template.block.state_vars
                                   if state.name.startswith('FilteredPlantVoltagePu_'))
        compensated_parameters: set[Var] = set(get_expression_vars(template.block.state_eqs[
            template.block.state_vars.index(voltage_filter)
        ]))
        order = next(parameter for parameter in renewable.rms_model.event_dict
                     if parameter.name.startswith('PlantVoltageOrder_'))
        if compensation is Repca1VoltageCompensation.LINE_DROP:
            rc_parameter: Var = next(parameter for parameter in template.block.event_dict
                                     if parameter.name.startswith('RC_'))
            assert rc_parameter in compensated_parameters
            vm_initial: float = float(abs(pf.voltage[1]))
            p_initial: float = float(pf.gen_p[1] / renewable.Snom)
            q_initial: float = float(pf.gen_q[1] / renewable.Snom)
            order_value = float(((vm_initial - (.1 * p_initial + .2 * q_initial) / vm_initial) ** 2
                                 + ((.2 * p_initial - .1 * q_initial) / vm_initial) ** 2) ** .5 + .02)
        else:
            kc_parameter: Var = next(parameter for parameter in template.block.event_dict
                                     if parameter.name.startswith('KC_'))
            assert kc_parameter in compensated_parameters
            order_value = float(abs(pf.voltage[1]) + .05 * pf.gen_q[1] / renewable.Snom + .02)
    else:
        order = next(parameter for parameter in renewable.rms_model.event_dict
                     if parameter.name.startswith('PlantReactiveOrder_'))
        order_value = float(pf.gen_q[1] / renewable.Snom + .1)
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=order, time=.001,
        value=order_value, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(grid=grid, options=RmsOptions(), pf_results=pf)
    problem.set_events_group(rms_events_group=group)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.08, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    q_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.Q))
    assert values[-1, q_index] > values[0, q_index] + .001
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_repca1_line_drop_compensation_uses_complex_current() -> None:
    """Retain the quadrature current term in source line-drop voltage.

    :return: None.
    """
    compensated: Expr = repca1_line_drop_voltage(
        Const(1.), Const(.8), Const(.4), Const(.1), Const(.2),
    )
    assert compensated.eval() == pytest.approx((.84 ** 2 + .12 ** 2) ** .5)


def test_repca1_reactive_plant_freezes_pi_below_vfrz() -> None:
    """Stop the source s2 integrator below the monitored voltage threshold.

    :return: None.
    """
    controller: RmsModelTemplate = build_repca1_reactive_plant_template(
        vf=VarFactory(), name='freeze', settings=Repca1ReactivePlantSettings(),
    )
    memory: Var = next(state for state in controller.block.state_vars
                        if state.name.startswith('PlantReactiveIntegral_'))
    derivative: Expr = controller.block.state_eqs[controller.block.state_vars.index(memory)]
    assert derivative.eval(
        PlantReactiveOrderPu_freeze=.2, FilteredPlantReactivePowerPu_freeze=0.,
        DBD1_freeze=0., DBD2_freeze=0., EMIN_freeze=-1., EMAX_freeze=1.,
        VFRZ_freeze=.5, MonitoredVoltagePu_freeze=.4, KI_freeze=1.,
        PlantReactiveIntegral_freeze=0., QMIN_freeze=-1.2, QMAX_freeze=1.2,
    ) == pytest.approx(0.)
    assert derivative.eval(
        PlantReactiveOrderPu_freeze=.2, FilteredPlantReactivePowerPu_freeze=0.,
        DBD1_freeze=0., DBD2_freeze=0., EMIN_freeze=-1., EMAX_freeze=1.,
        VFRZ_freeze=.5, MonitoredVoltagePu_freeze=.6, KI_freeze=1.,
        PlantReactiveIntegral_freeze=0., QMIN_freeze=-1.2, QMAX_freeze=1.2,
    ) == pytest.approx(.2)


@pytest.mark.parametrize('coordinated,local_voltage', ((False, False), (True, False), (False, True)))
def test_renewable_partial_chain_reads_phasor_voltage_without_duplicate_bus(
        coordinated: bool, local_voltage: bool,
) -> None:
    """Feed VDL current limits from the same Vr/Vi bus used by converter power.

    :param coordinated: Exercise Q/V PI rather than the constant-pf branch.
    :param local_voltage: Exercise local voltage PI with a biased reference.
    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_current_balance_load_case(
        powers=((10., 1.),), system_base=100., nominal_ratio=1.,
    )
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Phasor partial chain', P=4., Q=1., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate
    if coordinated:
        template = build_renewable_partial_chain(
            vf=grid.var_factory, name='Phasor partial chain',
            current_limit_settings=Reeca1CurrentLimitSettings(trv=.03),
            active_power_settings=Reeca1ActivePowerSettings(tpord=.04),
            coordinated_qv_settings=Reeca1CoordinatedQvSettings(),
            voltage_support_settings=Reeca1VoltageSupportSettings(kqv=2.),
            problem_type=RmsProblemTypes.CurrentBalance,
        )
    elif local_voltage:
        template = build_renewable_partial_chain(
            vf=grid.var_factory, name='Phasor partial chain',
            current_limit_settings=Reeca1CurrentLimitSettings(trv=.03),
            active_power_settings=Reeca1ActivePowerSettings(tpord=.04),
            local_voltage_settings=Reeca1LocalVoltageSettings(vbias=.01),
            voltage_support_settings=Reeca1VoltageSupportSettings(kqv=2.),
            problem_type=RmsProblemTypes.CurrentBalance,
        )
    else:
        template = build_renewable_partial_chain(
            vf=grid.var_factory, name='Phasor partial chain',
            current_limit_settings=Reeca1CurrentLimitSettings(trv=.03),
            active_power_settings=Reeca1ActivePowerSettings(tpord=.04),
            reactive_power_settings=Reeca1ConstantQSettings(tiq=.04),
            power_factor_settings=Reeca1ConstantPfSettings(tp=.03),
            voltage_support_settings=Reeca1VoltageSupportSettings(kqv=2.),
            problem_type=RmsProblemTypes.CurrentBalance,
        )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid, options=RmsOptions(problem_type=RmsProblemTypes.CurrentBalance),
        pf_results=pf,
    )
    problem.set_events_group(rms_events_group=RmsEventsGroup())
    projected: np.ndarray
    initialized: bool
    residual: float
    projected, initialized, residual = project_initial_algebraic_state(
        problem=problem, initial_values=problem.get_x0(),
        differential_values=problem.get_dx0(), tolerance=1.e-8, max_iter=25,
    )
    assert initialized and residual <= 1.e-8
    assert projected[
        problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.P))
    ] == pytest.approx(pf.gen_p[1] / grid.Sbase, abs=1.e-8)
    assert projected[
        problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.Q))
    ] == pytest.approx(pf.gen_q[1] / grid.Sbase, abs=1.e-8)
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_renewable_constant_pf_mode_tracks_active_power_on_connected_network() -> None:
    """Use filtered generator Pe to preserve the initial Q/P ratio after a Pref step.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Renewable constant pf', P=4., Q=1., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Renewable constant pf',
        current_limit_settings=Reeca1CurrentLimitSettings(trv=.03),
        active_power_settings=Reeca1ActivePowerSettings(tpord=.02),
        reactive_power_settings=Reeca1ConstantQSettings(tiq=.02),
        power_factor_settings=Reeca1ConstantPfSettings(tp=.02),
    )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged and pf.gen_q[1] > 0.
    pref_order: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('PrefOrder_')
    )
    pf_angle: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('PfAngle_')
    )
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=pref_order, time=.001,
        value=pf.gen_p[1] / renewable.Snom + .1, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf,
    )
    problem.set_events_group(rms_events_group=group)
    angle_index: int = problem._uid2idx_event_params[pf_angle.uid]
    assert problem._variable_parameters_values[angle_index] == pytest.approx(
        np.arctan2(pf.gen_q[1], pf.gen_p[1]), abs=1.e-8,
    )
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.012, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    q_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.Q))
    assert values[-1, q_index] > values[0, q_index]
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_renewable_coordinated_qv_mode_tracks_q_reference_on_connected_network() -> None:
    """Feed the Q/V PI cascade from generator Q and live current capability.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Renewable coordinated Q V', P=4., Q=1., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Renewable coordinated Q V',
        current_limit_settings=Reeca1CurrentLimitSettings(trv=.03),
        coordinated_qv_settings=Reeca1CoordinatedQvSettings(kqi=2., kvi=2.),
        voltage_support_settings=Reeca1VoltageSupportSettings(kqv=0.),
    )
    assert len(template.block.state_vars) == 7
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    q_reference: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('QReferenceOrder_')
    )
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=q_reference, time=.001,
        value=pf.gen_q[1] / renewable.Snom + .1, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf,
    )
    problem.set_events_group(rms_events_group=group)
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.008, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    q_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.Q))
    assert values[-1, q_index] > values[0, q_index]
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_renewable_local_voltage_mode_tracks_reference_on_connected_network() -> None:
    """Initialize Vref plus Vbias at PF voltage and respond to a voltage step.

    :return: None.
    """
    grid: MultiCircuit
    ignored_pf: PowerFlowResults
    grid, ignored_pf = build_supported_vectorized_ac_load_case()
    renewable: Generator = grid.add_generator(
        bus=grid.buses[1], api_obj=Generator(name='Renewable local voltage', P=4., Q=1., Snom=50.),
    )
    renewable.is_controlled = False
    template: RmsModelTemplate = build_renewable_partial_chain(
        vf=grid.var_factory, name='Renewable local voltage',
        current_limit_settings=Reeca1CurrentLimitSettings(trv=.03),
        local_voltage_settings=Reeca1LocalVoltageSettings(kvp=2., kvi=3., vbias=.01),
        voltage_support_settings=Reeca1VoltageSupportSettings(kqv=0.),
    )
    grid.add_rms_model(template)
    renewable.rms_template = template
    pf: PowerFlowResults = power_flow(grid=grid)
    assert pf.converged
    voltage_reference: Var = next(
        parameter for parameter in renewable.rms_model.event_dict
        if parameter.name.startswith('VoltageReferenceOrder_')
    )
    group: RmsEventsGroup = RmsEventsGroup()
    grid.add_rms_event(RmsEvent(
        device=renewable, parameter=voltage_reference, time=.001,
        value=abs(pf.voltage[1]) + .01, group=group,
    ))
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf,
    )
    problem.set_events_group(rms_events_group=group)
    reference_index: int = problem._uid2idx_event_params[voltage_reference.uid]
    assert problem._variable_parameters_values[reference_index] == pytest.approx(
        abs(pf.voltage[1]) - .01, abs=1.e-8,
    )
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0., t_end=.008, h=.001, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized and converged and times.size >= 2
    q_index: int = problem.get_var_idx(renewable.rms_model.E(VarPowerFlowReferenceType.Q))
    assert values[-1, q_index] > values[0, q_index]
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()


def test_dae_constructors_preserve_power_flow_vsc_current_base() -> None:
    """Seed every power-balance DAE with the PF VSC current base unchanged.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    current_magnitude: Var
    current_index: int

    grid, power_flow_results = build_legacy_vsc_current_seed_case()
    scalar_problem: RmsProblemDae = RmsProblemDae(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    current_magnitude = grid.get_vsc()[0].rms_model.E(
        VarPowerFlowReferenceType.Im
    )
    current_index = scalar_problem._uid2idx_vars[current_magnitude.uid]
    assert scalar_problem.get_x0()[current_index] == pytest.approx(7.5)
    assert sum(child is grid.get_vsc()[0].rms_model for child in scalar_problem.sys_block.children) == 1

    grid, power_flow_results = build_legacy_vsc_current_seed_case()
    vectorized_problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    current_magnitude = grid.get_vsc()[0].rms_model.E(
        VarPowerFlowReferenceType.Im
    )
    current_index = vectorized_problem._uid2idx_vars[current_magnitude.uid]
    assert vectorized_problem.get_x0()[current_index] == pytest.approx(7.5)
    assert sum(child is grid.get_vsc()[0].rms_model for child in vectorized_problem.sys_block.children) == 1

    grid, power_flow_results = build_legacy_vsc_current_seed_case()
    full_vectorized_problem: RmsProblemDaeFullVec = RmsProblemDaeFullVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    current_magnitude = grid.get_vsc()[0].rms_model.E(
        VarPowerFlowReferenceType.Im
    )
    current_index = full_vectorized_problem._uid2idx_vars[
        current_magnitude.uid
    ]
    assert full_vectorized_problem.get_x0()[current_index] == pytest.approx(7.5)
    assert sum(child is grid.get_vsc()[0].rms_model for child in full_vectorized_problem.sys_block.children) == 1


def test_dae_constructors_preserve_legacy_vsc_power_coupling() -> None:
    """Keep v1/custom VSC models runnable in all power-balance DAE paths.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    grid, power_flow_results = build_legacy_vsc_dae_case()
    scalar_problem: RmsProblemDae = RmsProblemDae(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    assert len(scalar_problem._algebraic_eqs) > 0

    grid, power_flow_results = build_legacy_vsc_dae_case()
    vectorized_problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    assert len(vectorized_problem._algebraic_eqs) > 0

    grid, power_flow_results = build_legacy_vsc_dae_case()
    full_vectorized_problem: RmsProblemDaeFullVec = RmsProblemDaeFullVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    assert len(full_vectorized_problem._mapped_power_layout_by_model_type) == 1
    full_vectorized_problem.set_events_group(rms_events_group=RmsEventsGroup())
    assert set(full_vectorized_problem._mapped_power_layout_by_model_type.keys()).issubset(
        set(full_vectorized_problem._rhs_algeb_fn_by_types.keys())
    )
    converter: VSC = grid.get_vsc()[0]
    from_active_power: Var = converter.rms_model.E(VarPowerFlowReferenceType.Pf)
    to_active_power: Var = converter.rms_model.E(VarPowerFlowReferenceType.Pt)
    to_reactive_power: Var = converter.rms_model.E(VarPowerFlowReferenceType.Qt)
    variables: np.ndarray = full_vectorized_problem.get_x0()
    from_active_index: int = full_vectorized_problem._uid2idx_vars[from_active_power.uid]
    to_active_index: int = full_vectorized_problem._uid2idx_vars[to_active_power.uid]
    to_reactive_index: int = full_vectorized_problem._uid2idx_vars[to_reactive_power.uid]
    variables[from_active_index] = 0.20
    variables[to_active_index] = -0.19
    variables[to_reactive_index] = 0.03
    differentials: np.ndarray = np.zeros(full_vectorized_problem.get_diff_var_number())
    full_vectorized_problem.update_input_matrices_by_model(
        x=variables,
        dx=differentials,
    )
    legacy_model_type: int = next(
        iter(full_vectorized_problem._mapped_power_layout_by_model_type.keys())
    )
    class_residual: np.ndarray = full_vectorized_problem._rhs_algeb_fn_by_types[
        legacy_model_type
    ](
        full_vectorized_problem._input_matrices_by_model[legacy_model_type][0],
        full_vectorized_problem._input_matrices_by_model[legacy_model_type][1],
        full_vectorized_problem._input_matrices_by_model[legacy_model_type][2],
        full_vectorized_problem._input_matrices_by_model[legacy_model_type][3],
    )
    assert class_residual[:, 0].tolist() == pytest.approx((
        0.20,
        -0.19,
        0.03,
        -0.20,
        0.19,
        -0.03,
    ))
    residual: np.ndarray = full_vectorized_problem.rhs_algebraic_vec(
        x=variables,
        dx=differentials,
    )
    jacobian: np.ndarray = full_vectorized_problem.get_j22_vec(
        x=variables,
        dx=differentials,
        h=1.0e-3,
    ).toarray()
    generic_residual: np.ndarray = full_vectorized_problem.rhs_algebraic(
        x=variables,
        dx=differentials,
    )
    generic_jacobian: np.ndarray = full_vectorized_problem.get_j22(
        x=variables,
        dx=differentials,
        h=1.0e-3,
    ).toarray()

    assert np.array_equal(generic_residual, residual)
    assert np.array_equal(generic_jacobian, jacobian)
    assert residual[:3].tolist() == pytest.approx((0.20, -0.19, 0.03))
    assert full_vectorized_problem.Q_vec[1] == pytest.approx(-0.03)
    # The physical AC converter bus retains both Q and P nodal rows; converter
    # control equations do not replace either network balance.
    assert residual[-3:].tolist() == pytest.approx((-0.20, -0.03, 0.19))
    assert jacobian[-3, from_active_index] == pytest.approx(-1.0)
    assert jacobian[-2, to_reactive_index] == pytest.approx(-1.0)
    assert jacobian[-1, to_active_index] == pytest.approx(-1.0)


def test_vectorized_integrators_use_supported_initial_projection() -> None:
    """Exercise the shared algebraic projector with both vectorized problems.

    A zero-macro-step run isolates initialization and cleanup while still
    dispatching the real ``rhs_algebraic`` projection interface selected by
    each solver.

    :return: None.
    """
    partial_grid: MultiCircuit
    partial_power_flow_results: PowerFlowResults
    partial_grid, partial_power_flow_results = (
        build_supported_vectorized_ac_load_case()
    )
    assert partial_power_flow_results.converged
    partial_problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=partial_grid,
        options=RmsOptions(),
        pf_results=partial_power_flow_results,
    )
    partial_problem.set_events_group(rms_events_group=RmsEventsGroup())

    # Compare the generic projection boundary with the established vectorized
    # owner on the same gathered non-trivial operating point.
    partial_variables: np.ndarray = partial_problem.get_x0()
    partial_differentials: np.ndarray = partial_problem.get_dx0()
    partial_problem.update_input_matrices_by_model(
        x=partial_variables,
        dx=partial_differentials,
    )
    partial_vectorized_residual: np.ndarray = partial_problem.rhs_algebraic_vec(
        x=partial_variables,
        dx=partial_differentials,
    )
    partial_vectorized_jacobian: np.ndarray = partial_problem.get_j22_vec(
        x=partial_variables,
        dx=partial_differentials,
        h=1.0e-3,
    ).toarray()
    partial_generic_residual: np.ndarray = partial_problem.rhs_algebraic(
        x=partial_variables,
        dx=partial_differentials,
    )
    partial_generic_jacobian: np.ndarray = partial_problem.get_j22(
        x=partial_variables,
        dx=partial_differentials,
        h=1.0e-3,
    ).toarray()
    assert np.array_equal(partial_generic_residual, partial_vectorized_residual)
    assert np.array_equal(partial_generic_jacobian, partial_vectorized_jacobian)
    assert np.any(np.abs(partial_vectorized_jacobian) > 0.0)

    partial_solver: BackEulerImplicitIntegration = (
        BackEulerImplicitIntegration(
            problem=partial_problem,
            t0=0.0,
            t_end=0.0,
            h=1.0e-3,
            max_iter=25,
        )
    )
    partial_times: np.ndarray
    partial_values: np.ndarray
    partial_well_initialized: bool
    partial_converged: bool
    (
        partial_times,
        partial_values,
        partial_well_initialized,
        partial_converged,
    ) = partial_solver.simulate()

    assert partial_times.tolist() == pytest.approx((0.0,))
    assert partial_values.shape == (1, partial_problem.get_all_vars_number())
    assert np.all(np.isfinite(partial_values))
    assert partial_well_initialized
    assert not partial_converged

    full_grid: MultiCircuit
    full_power_flow_results: PowerFlowResults
    full_grid, full_power_flow_results = build_supported_vectorized_ac_load_case()
    assert full_power_flow_results.converged
    full_problem: RmsProblemDaeFullVec = RmsProblemDaeFullVec(
        grid=full_grid,
        options=RmsOptions(),
        pf_results=full_power_flow_results,
    )
    full_problem.set_events_group(rms_events_group=RmsEventsGroup())
    full_solver: BackEulerImplicitIntegration = (
        BackEulerImplicitIntegration(
            problem=full_problem,
            t0=0.0,
            t_end=0.0,
            h=1.0e-3,
            max_iter=25,
        )
    )
    full_times: np.ndarray
    full_values: np.ndarray
    full_well_initialized: bool
    full_converged: bool
    (
        full_times,
        full_values,
        full_well_initialized,
        full_converged,
    ) = full_solver.simulate()

    assert full_times.tolist() == pytest.approx((0.0,))
    assert full_values.shape == (1, full_problem.get_all_vars_number())
    assert np.all(np.isfinite(full_values))
    assert full_well_initialized
    assert not full_converged


def test_full_vectorized_capacitive_dc_nodal_layout_matches_jacobian() -> None:
    """Evaluate the exact ``P_bus - P_network`` row and its full Jacobian.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    grid, power_flow_results = build_legacy_vsc_dae_case(capacitive_dc_bus=True)
    problem: RmsProblemDaeFullVec = RmsProblemDaeFullVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    problem.set_events_group(rms_events_group=RmsEventsGroup())

    converter: VSC = grid.get_vsc()[0]
    from_active_power: Var = converter.rms_model.E(VarPowerFlowReferenceType.Pf)
    to_active_power: Var = converter.rms_model.E(VarPowerFlowReferenceType.Pt)
    to_reactive_power: Var = converter.rms_model.E(VarPowerFlowReferenceType.Qt)
    local_dc_power: Var = grid.buses[0].rms_model.E(VarPowerFlowReferenceType.P)
    variables: np.ndarray = problem.get_x0()
    variables[problem._uid2idx_vars[from_active_power.uid]] = 0.20
    variables[problem._uid2idx_vars[to_active_power.uid]] = -0.19
    variables[problem._uid2idx_vars[to_reactive_power.uid]] = 0.03
    variables[problem._uid2idx_vars[local_dc_power.uid]] = 0.05
    differentials: np.ndarray = np.zeros(problem.get_diff_var_number())
    problem.update_input_matrices_by_model(x=variables, dx=differentials)
    residual: np.ndarray = problem.rhs_algebraic_vec(
        x=variables,
        dx=differentials,
    )
    analytic_jacobian: np.ndarray = np.hstack((
        problem.get_j21_vec(x=variables, dx=differentials, h=1.0e-3).toarray(),
        problem.get_j22_vec(x=variables, dx=differentials, h=1.0e-3).toarray(),
    ))

    finite_difference_jacobian: np.ndarray = np.zeros_like(analytic_jacobian)
    perturbation: float = 1.0e-7
    column_index: int = 0
    while column_index < len(variables):
        variables_plus: np.ndarray = variables.copy()
        variables_minus: np.ndarray = variables.copy()
        variables_plus[column_index] += perturbation
        variables_minus[column_index] -= perturbation
        problem.update_input_matrices_by_model(
            x=variables_plus,
            dx=differentials,
        )
        residual_plus: np.ndarray = problem.rhs_algebraic_vec(
            x=variables_plus,
            dx=differentials,
        )
        problem.update_input_matrices_by_model(
            x=variables_minus,
            dx=differentials,
        )
        residual_minus: np.ndarray = problem.rhs_algebraic_vec(
            x=variables_minus,
            dx=differentials,
        )
        finite_difference_jacobian[:, column_index] = (
            residual_plus - residual_minus
        ) / (2.0 * perturbation)
        column_index += 1

    # A capacitive DC bus contributes its local P balance, while the physical
    # AC terminal independently retains both reactive and active nodal rows.
    assert residual[-3:].tolist() == pytest.approx((0.25, -0.03, 0.19))
    assert np.allclose(
        analytic_jacobian,
        finite_difference_jacobian,
        rtol=1.0e-7,
        atol=1.0e-8,
    )


def test_full_vectorized_rejects_isolated_bus_before_runtime_layout() -> None:
    """Fail closed instead of inventing runtime rows for an isolated bus.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Isolated AC bus", is_dc=False)
    grid.add_bus(obj=bus)
    initialize_bus_rms(bus=bus, vf=grid.var_factory)
    power_flow_results: PowerFlowResults = PowerFlowResults(
        n=1,
        m=0,
        n_hvdc=0,
        n_vsc=0,
        n_gen=0,
        n_batt=0,
        n_sh=0,
        bus_names=np.array((bus.name,)),
        branch_names=np.array(tuple()),
        hvdc_names=np.array(tuple()),
        vsc_names=np.array(tuple()),
        gen_names=np.array(tuple()),
        batt_names=np.array(tuple()),
        sh_names=np.array(tuple()),
        bus_types=np.zeros(1, dtype=int),
    )
    power_flow_results.voltage = np.array((1.0 + 0.0j,))

    with pytest.raises(ValueError, match="Isolated RMS bus"):
        RmsProblemDaeFullVec(
            grid=grid,
            options=RmsOptions(),
            pf_results=power_flow_results,
        )


def _build_two_generator_dc_initialization_case() -> tuple[MultiCircuit, PowerFlowResults, Var, Var]:
    """Build a DC bus whose aggregate power differs from each device dispatch.

    The two generator results add up to the bus result, but neither generator
    owns the complete bus injection. This distinguishes correct per-device RMS
    initialization from the former duplicated ``Sbus`` initialization.

    :return: Grid, power-flow results and the two mapped generator power variables.
    """
    grid: MultiCircuit = MultiCircuit(Sbase=100.0)
    dc_bus: Bus = Bus(name="Shared generator DC bus", is_dc=True, is_slack=True)
    grid.add_bus(obj=dc_bus)
    initialize_bus_rms(bus=dc_bus, vf=grid.var_factory)

    # Give each generator a distinct mapped P variable so the test can inspect
    # both initial guesses independently after RMS problem construction.
    first_active_power: Var = grid.var_factory.add_var(
        name="P_dc_generator_1",
        reference=VarPowerFlowReferenceType.P,
    )
    first_model: Block = Block(
        algebraic_vars=list((first_active_power,)),
        algebraic_eqs=list((first_active_power,)),
        external_mapping=dict(((VarPowerFlowReferenceType.P, first_active_power),)),
    )
    first_generator: Generator = Generator(name="DC generator 1")
    first_generator.rms_model = first_model
    grid.add_generator(bus=dc_bus, api_obj=first_generator)

    second_active_power: Var = grid.var_factory.add_var(
        name="P_dc_generator_2",
        reference=VarPowerFlowReferenceType.P,
    )
    second_model: Block = Block(
        algebraic_vars=list((second_active_power,)),
        algebraic_eqs=list((second_active_power,)),
        external_mapping=dict(((VarPowerFlowReferenceType.P, second_active_power),)),
    )
    second_generator: Generator = Generator(name="DC generator 2")
    second_generator.rms_model = second_model
    grid.add_generator(bus=dc_bus, api_obj=second_generator)

    power_flow_results: PowerFlowResults = PowerFlowResults(
        n=1,
        m=0,
        n_hvdc=0,
        n_vsc=0,
        n_gen=2,
        n_batt=0,
        n_sh=0,
        bus_names=np.array((dc_bus.name,)),
        branch_names=np.array(tuple()),
        hvdc_names=np.array(tuple()),
        vsc_names=np.array(tuple()),
        gen_names=np.array((first_generator.name, second_generator.name)),
        batt_names=np.array(tuple()),
        sh_names=np.array(tuple()),
        bus_types=np.zeros(1, dtype=int),
    )
    power_flow_results.voltage[0] = 1.0 + 0.0j
    power_flow_results.Sbus[0] = 90.0 + 0.0j
    power_flow_results.gen_p[:] = np.array((30.0, 60.0), dtype=float)
    power_flow_results.gen_q[:] = np.zeros(2, dtype=float)

    return grid, power_flow_results, first_active_power, second_active_power


def test_scalar_rms_dc_injections_use_individual_pf_dispatch() -> None:
    """Verify scalar RMS initializes parallel DC generators from ``gen_p``.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    first_active_power: Var
    second_active_power: Var
    grid, power_flow_results, first_active_power, second_active_power = (
        _build_two_generator_dc_initialization_case()
    )
    problem: RmsProblemDae = RmsProblemDae(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )

    assert np.isclose(problem.init_guess[first_active_power.uid], 0.3)
    assert np.isclose(problem.init_guess[second_active_power.uid], 0.6)


def test_vectorized_rms_dc_injections_use_individual_pf_dispatch() -> None:
    """Verify vectorized RMS initializes parallel DC generators from ``gen_p``.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    first_active_power: Var
    second_active_power: Var
    grid, power_flow_results, first_active_power, second_active_power = (
        _build_two_generator_dc_initialization_case()
    )
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )

    assert np.isclose(problem.init_guess[first_active_power.uid], 0.3)
    assert np.isclose(problem.init_guess[second_active_power.uid], 0.6)


def test_full_vectorized_rms_dc_injections_use_individual_pf_dispatch() -> None:
    """Verify full-vectorized RMS initializes parallel DC generators from ``gen_p``.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    first_active_power: Var
    second_active_power: Var
    grid, power_flow_results, first_active_power, second_active_power = (
        _build_two_generator_dc_initialization_case()
    )
    problem: RmsProblemDaeFullVec = RmsProblemDaeFullVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )

    assert np.isclose(problem.init_guess[first_active_power.uid], 0.3)
    assert np.isclose(problem.init_guess[second_active_power.uid], 0.6)


def test_phasor_rms_dc_injections_use_individual_pf_dispatch() -> None:
    """Verify phasor RMS initializes parallel DC generators from ``gen_p``.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    first_active_power: Var
    second_active_power: Var
    grid, power_flow_results, first_active_power, second_active_power = (
        _build_two_generator_dc_initialization_case()
    )
    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )

    assert np.isclose(problem.init_guess[first_active_power.uid], 0.3)
    assert np.isclose(problem.init_guess[second_active_power.uid], 0.6)


def test_phasor_constructor_preserves_legacy_vsc_power_coupling() -> None:
    """Keep a v1/custom VSC coupled through its historical power references.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    dc_bus: Bus = Bus(name="Legacy phasor DC bus", is_dc=True)
    ac_bus: Bus = Bus(name="Legacy phasor AC bus", is_dc=False)
    grid.add_bus(obj=dc_bus)
    grid.add_bus(obj=ac_bus)

    dc_voltage: Var = grid.var_factory.add_var(
        name="Vdc_legacy",
        reference=VarPowerFlowReferenceType.Vdc,
    )
    dc_bus.rms_model = Block(
        algebraic_vars=list((dc_voltage,)),
        external_mapping=dict(((VarPowerFlowReferenceType.Vdc, dc_voltage),)),
    )
    voltage_real: Var = grid.var_factory.add_var(
        name="Vr_legacy",
        reference=VarPowerFlowReferenceType.Vr,
    )
    voltage_imaginary: Var = grid.var_factory.add_var(
        name="Vi_legacy",
        reference=VarPowerFlowReferenceType.Vi,
    )
    ac_bus.rms_model = Block(
        algebraic_vars=list((voltage_real, voltage_imaginary)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Vr, voltage_real),
            (VarPowerFlowReferenceType.Vi, voltage_imaginary),
        )),
    )

    from_active_power: Var = grid.var_factory.add_var(name="Pf_legacy")
    to_active_power: Var = grid.var_factory.add_var(name="Pt_legacy")
    to_reactive_power: Var = grid.var_factory.add_var(name="Qt_legacy")
    legacy_model: Block = Block(
        algebraic_vars=list((from_active_power, to_active_power, to_reactive_power)),
        algebraic_eqs=list((from_active_power, to_active_power, to_reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Pf, from_active_power),
            (VarPowerFlowReferenceType.Pt, to_active_power),
            (VarPowerFlowReferenceType.Qt, to_reactive_power),
        )),
    )
    converter: VSC = VSC(
        name="Legacy phasor VSC",
        bus_from=dc_bus,
        bus_to=ac_bus,
    )
    converter.rms_model = legacy_model
    grid.add_vsc(obj=converter)

    power_flow_results: PowerFlowResults = PowerFlowResults(
        n=2,
        m=0,
        n_hvdc=0,
        n_vsc=1,
        n_gen=0,
        n_batt=0,
        n_sh=0,
        bus_names=np.array((dc_bus.name, ac_bus.name)),
        branch_names=np.array(tuple()),
        hvdc_names=np.array(tuple()),
        vsc_names=np.array((converter.name,)),
        gen_names=np.array(tuple()),
        batt_names=np.array(tuple()),
        sh_names=np.array(tuple()),
        bus_types=np.zeros(2, dtype=int),
    )
    power_flow_results.voltage = np.array((1.0 + 0.0j, 0.8 + 0.6j))
    power_flow_results.Pfp_vsc[0] = 0.20
    power_flow_results.St_vsc[0] = complex(-0.19, 0.03)

    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    assert sum(child is converter.rms_model for child in problem.sys_block.children) == 1
    nodal_equations: list[Expr] = problem._algebraic_eqs[-3:]
    dc_names: set[str] = set(
        variable.name for variable in get_expression_vars(nodal_equations[0])
    )
    ac_real_names: set[str] = set(
        variable.name for variable in get_expression_vars(nodal_equations[1])
    )
    ac_imaginary_names: set[str] = set(
        variable.name for variable in get_expression_vars(nodal_equations[2])
    )

    assert dc_names == set(("Pf_legacy",))
    assert ac_real_names == set(("Pt_legacy", "Qt_legacy", "Vr_legacy", "Vi_legacy"))
    assert ac_imaginary_names == set(("Pt_legacy", "Qt_legacy", "Vr_legacy", "Vi_legacy"))


def test_full_vectorized_runtime_keeps_device_and_terminal_rows_separate() -> None:
    """Evaluate selected one-terminal powers through the compiled RMS runtime.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Vectorized AC bus", is_dc=False)
    grid.add_bus(obj=bus)
    initialize_bus_rms(bus=bus, vf=grid.var_factory)

    first_active_power: Var = grid.var_factory.add_var(name="P_selected")
    first_reactive_power: Var = grid.var_factory.add_var(name="Q_selected")
    first_model: Block = Block(
        algebraic_vars=list((first_active_power, first_reactive_power)),
        algebraic_eqs=list((first_active_power, first_reactive_power)),
        out_vars=list(),
        external_mapping=dict((
            (VarPowerFlowReferenceType.P, first_active_power),
            (VarPowerFlowReferenceType.Q, first_reactive_power),
        )),
    )
    first_load: Load = Load(name="First selected power")
    first_load.rms_model = first_model
    grid.add_load(bus=bus, api_obj=first_load)

    second_active_power: Var = grid.var_factory.add_var(name="P_selected")
    second_reactive_power: Var = grid.var_factory.add_var(name="Q_selected")
    second_model: Block = Block(
        algebraic_vars=list((second_active_power, second_reactive_power)),
        algebraic_eqs=list((second_active_power, second_reactive_power)),
        out_vars=list(),
        external_mapping=dict((
            (VarPowerFlowReferenceType.P, second_active_power),
            (VarPowerFlowReferenceType.Q, second_reactive_power),
        )),
    )
    second_load: Load = Load(name="Second selected power")
    second_load.rms_model = second_model
    grid.add_load(bus=bus, api_obj=second_load)

    power_flow_results: PowerFlowResults = PowerFlowResults(
        n=1,
        m=0,
        n_hvdc=0,
        n_vsc=0,
        n_gen=0,
        n_batt=0,
        n_sh=0,
        bus_names=np.array((bus.name,)),
        branch_names=np.array(tuple()),
        hvdc_names=np.array(tuple()),
        vsc_names=np.array(tuple()),
        gen_names=np.array(tuple()),
        batt_names=np.array(tuple()),
        sh_names=np.array(tuple()),
        bus_types=np.zeros(1, dtype=int),
    )
    power_flow_results.voltage = np.array((1.0 + 0.0j,))
    problem: RmsProblemDaeFullVec = RmsProblemDaeFullVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    problem.set_events_group(rms_events_group=RmsEventsGroup())
    variables: np.ndarray = problem.get_x0()
    variables[problem._uid2idx_vars[first_active_power.uid]] = 0.10
    variables[problem._uid2idx_vars[first_reactive_power.uid]] = 0.20
    variables[problem._uid2idx_vars[second_active_power.uid]] = -0.03
    variables[problem._uid2idx_vars[second_reactive_power.uid]] = 0.04
    differentials: np.ndarray = np.zeros(problem.get_diff_var_number())
    problem.update_input_matrices_by_model(x=variables, dx=differentials)
    residual: np.ndarray = problem.rhs_algebraic_vec(
        x=variables,
        dx=differentials,
    )

    first_start: int = problem._model_algebraic_eq_start_idx[first_model.uid]
    second_start: int = problem._model_algebraic_eq_start_idx[second_model.uid]
    assert len(problem._mapped_power_layout_by_model_type) == 1
    assert residual[first_start] == pytest.approx(0.10)
    assert residual[first_start + 1] == pytest.approx(0.20)
    assert residual[second_start] == pytest.approx(-0.03)
    assert residual[second_start + 1] == pytest.approx(0.04)
    assert residual[-2] == pytest.approx(0.24)
    assert residual[-1] == pytest.approx(0.07)

    analytic_jacobian: np.ndarray = problem.get_j22_vec(
        x=variables,
        dx=differentials,
        h=1.0e-3,
    ).toarray()
    finite_difference_jacobian: np.ndarray = np.zeros_like(analytic_jacobian)
    perturbation: float = 1.0e-7
    column_index: int = 0
    while column_index < problem.get_algebraic_var_number():
        variables_plus: np.ndarray = variables.copy()
        variables_minus: np.ndarray = variables.copy()
        variables_plus[column_index] += perturbation
        variables_minus[column_index] -= perturbation
        problem.update_input_matrices_by_model(
            x=variables_plus,
            dx=differentials,
        )
        residual_plus: np.ndarray = problem.rhs_algebraic_vec(
            x=variables_plus,
            dx=differentials,
        )
        problem.update_input_matrices_by_model(
            x=variables_minus,
            dx=differentials,
        )
        residual_minus: np.ndarray = problem.rhs_algebraic_vec(
            x=variables_minus,
            dx=differentials,
        )
        finite_difference_jacobian[:, column_index] = (
            residual_plus - residual_minus
        ) / (2.0 * perturbation)
        column_index += 1

    assert np.allclose(
        analytic_jacobian,
        finite_difference_jacobian,
        rtol=1.0e-7,
        atol=1.0e-8,
    )


def build_mixed_terminal_contract_grid(
        contract_first: bool,
) -> tuple[MultiCircuit, PowerFlowResults]:
    """Build two equivalent loads with inconsistent network-interface modes.

    :param contract_first: Whether the typed-contract instance is added first.
    :return: Grid and power-flow seed data for the full-vectorized constructor.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Mixed-contract AC bus", is_dc=False)
    grid.add_bus(obj=bus)
    initialize_bus_rms(bus=bus, vf=grid.var_factory)

    typed_active_power: Var = grid.var_factory.add_var(name="P_mixed")
    typed_reactive_power: Var = grid.var_factory.add_var(name="Q_mixed")
    typed_model: Block = Block(
        algebraic_vars=list((typed_active_power, typed_reactive_power)),
        algebraic_eqs=list((typed_active_power, typed_reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.P, typed_active_power),
            (VarPowerFlowReferenceType.Q, typed_reactive_power),
        )),
    )
    typed_load: Load = Load(name="Typed equivalent load")
    typed_load.rms_model = typed_model

    legacy_active_power: Var = grid.var_factory.add_var(name="P_mixed")
    legacy_reactive_power: Var = grid.var_factory.add_var(name="Q_mixed")
    legacy_model: Block = Block(
        algebraic_vars=list((legacy_active_power, legacy_reactive_power)),
        algebraic_eqs=list((legacy_active_power, legacy_reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.P, legacy_active_power),
            (VarPowerFlowReferenceType.Q, legacy_reactive_power),
        )),
    )
    legacy_load: Load = Load(name="Legacy equivalent load")
    legacy_load.rms_model = legacy_model

    if contract_first:
        grid.add_load(bus=bus, api_obj=typed_load)
        grid.add_load(bus=bus, api_obj=legacy_load)
    else:
        grid.add_load(bus=bus, api_obj=legacy_load)
        grid.add_load(bus=bus, api_obj=typed_load)

    power_flow_results: PowerFlowResults = PowerFlowResults(
        n=1,
        m=0,
        n_hvdc=0,
        n_vsc=0,
        n_gen=0,
        n_batt=0,
        n_sh=0,
        bus_names=np.array((bus.name,)),
        branch_names=np.array(tuple()),
        hvdc_names=np.array(tuple()),
        vsc_names=np.array(tuple()),
        gen_names=np.array(tuple()),
        batt_names=np.array(tuple()),
        sh_names=np.array(tuple()),
        bus_types=np.zeros(1, dtype=int),
    )
    power_flow_results.voltage = np.array((1.0 + 0.0j,))
    return grid, power_flow_results


def test_full_vectorized_ignores_persisted_contract_on_representative() -> None:
    """Compile equivalent mappings independently of persisted old metadata.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    grid, power_flow_results = build_mixed_terminal_contract_grid(contract_first=True)

    problem = RmsProblemDaeFullVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    assert len(problem._mapped_power_layout_by_model_type) == 1


def test_full_vectorized_ignores_persisted_contract_on_member() -> None:
    """Compile equivalent mappings when only a member has old metadata.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    grid, power_flow_results = build_mixed_terminal_contract_grid(contract_first=False)

    problem = RmsProblemDaeFullVec(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )
    assert len(problem._mapped_power_layout_by_model_type) == 1


def test_phasor_balance_consumes_vsc_mapped_power_references() -> None:
    """Convert mapped VSC terminal powers into the phasor AC KCL residual.

    :return: None.
    """
    dc_power: Var = Var(name="Pdc")
    ac_active_power: Var = Var(name="Pac")
    ac_reactive_power: Var = Var(name="Qac")
    voltage_real: Var = Var(name="Vr")
    voltage_imaginary: Var = Var(name="Vi")
    model: Block = Block(
        algebraic_vars=list((dc_power, ac_active_power, ac_reactive_power)),
        algebraic_eqs=list((dc_power, ac_active_power, ac_reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Pf, dc_power),
            (VarPowerFlowReferenceType.Pt, ac_active_power),
            (VarPowerFlowReferenceType.Qt, ac_reactive_power),
        )),
    )
    active_balance: ObjVec = np.zeros(2, dtype=object)
    reactive_balance: ObjVec = np.zeros(2, dtype=object)
    real_current_balance: ObjVec = np.zeros(2, dtype=object)
    imaginary_current_balance: ObjVec = np.zeros(2, dtype=object)
    active_used: BoolVec = np.zeros(2, dtype=bool)
    reactive_used: BoolVec = np.zeros(2, dtype=bool)
    real_current_used: BoolVec = np.zeros(2, dtype=bool)
    imaginary_current_used: BoolVec = np.zeros(2, dtype=bool)

    # Assemble by physical VSC topology first, as each RMS problem does.
    assemble_rms_mapped_power_references(
        model=model,
        bus_from_index=0,
        bus_to_index=1,
        bus_from_is_dc=True,
        bus_to_is_dc=False,
        active_power_balance=active_balance,
        active_power_balance_used=active_used,
        reactive_power_balance=reactive_balance,
        reactive_power_balance_used=reactive_used,
    )
    # The phasor formulation must then consume the AC power entry in its KCL
    # arrays while retaining the DC active-power equation at the other bus.
    convert_rms_ac_power_balance_to_current_balance(
        bus_index=1,
        voltage_real=voltage_real,
        voltage_imaginary=voltage_imaginary,
        active_power_balance=active_balance,
        active_power_balance_used=active_used,
        reactive_power_balance=reactive_balance,
        reactive_power_balance_used=reactive_used,
        real_current_balance=real_current_balance,
        real_current_balance_used=real_current_used,
        imaginary_current_balance=imaginary_current_balance,
        imaginary_current_balance_used=imaginary_current_used,
    )

    assert active_balance[0].eval(Pdc=0.25) == pytest.approx(-0.25)
    assert real_current_used.tolist() == [False, True]
    assert imaginary_current_used.tolist() == [False, True]
    assert real_current_balance[1].eval(
        Pac=-0.24,
        Qac=0.10,
        Vr=0.8,
        Vi=0.6,
    ) == pytest.approx(0.132)
    assert imaginary_current_balance[1].eval(
        Pac=-0.24,
        Qac=0.10,
        Vr=0.8,
        Vi=0.6,
    ) == pytest.approx(0.224)


def test_phasor_problem_emits_vsc_dc_and_ac_nodal_residuals() -> None:
    """Build the phasor problem and inspect its topology-owned VSC residuals.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    dc_bus: Bus = Bus(name="DC bus", is_dc=True)
    ac_bus: Bus = Bus(name="AC bus", is_dc=False)
    grid.add_bus(obj=dc_bus)
    grid.add_bus(obj=ac_bus)

    # Give each physical bus only its canonical phasor voltage coordinates so
    # the problem constructor must provide the network balance equations.
    dc_voltage: Var = grid.var_factory.add_var(
        name="Vdc",
        reference=VarPowerFlowReferenceType.Vdc,
    )
    dc_bus.rms_model = Block(
        algebraic_vars=list((dc_voltage,)),
        out_vars=list((dc_voltage,)),
        external_mapping=dict(((VarPowerFlowReferenceType.Vdc, dc_voltage),)),
    )
    voltage_real: Var = grid.var_factory.add_var(
        name="Vr",
        reference=VarPowerFlowReferenceType.Vr,
    )
    voltage_imaginary: Var = grid.var_factory.add_var(
        name="Vi",
        reference=VarPowerFlowReferenceType.Vi,
    )
    ac_bus.rms_model = Block(
        algebraic_vars=list((voltage_real, voltage_imaginary)),
        out_vars=list((voltage_real, voltage_imaginary)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Vr, voltage_real),
            (VarPowerFlowReferenceType.Vi, voltage_imaginary),
        )),
    )

    # The VSC owns only its device equations and typed terminal contract. Its
    # physical bus_from/bus_to topology determines where the network terms go.
    dc_power: Var = grid.var_factory.add_var(name="Pf")
    ac_active_power: Var = grid.var_factory.add_var(name="Pt")
    ac_reactive_power: Var = grid.var_factory.add_var(name="Qt")
    vsc_model: Block = Block(
        algebraic_vars=list((dc_power, ac_active_power, ac_reactive_power)),
        algebraic_eqs=list((dc_power, ac_active_power, ac_reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Pf, dc_power),
            (VarPowerFlowReferenceType.Pt, ac_active_power),
            (VarPowerFlowReferenceType.Qt, ac_reactive_power),
        )),
    )
    converter: VSC = VSC(
        name="DC-AC VSC",
        bus_from=dc_bus,
        bus_to=ac_bus,
    )
    converter.rms_model = vsc_model
    grid.add_vsc(obj=converter)

    # Add a pre-existing AC current injection to prove that terminal-power
    # conversion augments the KCL arrays instead of replacing their contents.
    existing_real_current: Var = grid.var_factory.add_var(name="Ir_existing")
    existing_imaginary_current: Var = grid.var_factory.add_var(name="Ii_existing")
    current_model: Block = Block(
        algebraic_vars=list((existing_real_current, existing_imaginary_current)),
        algebraic_eqs=list((existing_real_current, existing_imaginary_current)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.Ir, existing_real_current),
            (VarPowerFlowReferenceType.Ii, existing_imaginary_current),
        )),
    )
    current_injection: Load = Load(name="Existing current")
    current_injection.rms_model = current_model
    grid.add_load(bus=ac_bus, api_obj=current_injection)

    # A second one-terminal physical device selects P/Q as its hidden network
    # interface. It has no graphical root ports, yet the assembler must include
    # it automatically through the same physical AC bus topology.
    selected_active_power: Var = grid.var_factory.add_var(name="P_selected")
    selected_reactive_power: Var = grid.var_factory.add_var(name="Q_selected")
    selected_power_model: Block = Block(
        algebraic_vars=list((selected_active_power, selected_reactive_power)),
        algebraic_eqs=list((selected_active_power, selected_reactive_power)),
        external_mapping=dict((
            (VarPowerFlowReferenceType.P, selected_active_power),
            (VarPowerFlowReferenceType.Q, selected_reactive_power),
        )),
    )
    selected_power_injection: Load = Load(name="Selected power")
    selected_power_injection.rms_model = selected_power_model
    grid.add_load(bus=ac_bus, api_obj=selected_power_injection)

    power_flow_results: PowerFlowResults = PowerFlowResults(
        n=2,
        m=0,
        n_hvdc=0,
        n_vsc=1,
        n_gen=0,
        n_batt=0,
        n_sh=0,
        bus_names=np.array((dc_bus.name, ac_bus.name)),
        branch_names=np.array(tuple()),
        hvdc_names=np.array(tuple()),
        vsc_names=np.array((converter.name,)),
        gen_names=np.array(tuple()),
        batt_names=np.array(tuple()),
        sh_names=np.array(tuple()),
        bus_types=np.zeros(2, dtype=int),
    )
    power_flow_results.voltage = np.array((1.0 + 0.0j, 0.8 + 0.6j))
    power_flow_results.Pfp_vsc[0] = 0.25
    power_flow_results.Pfn_vsc[0] = 0.0
    power_flow_results.St_vsc[0] = complex(-0.24, 0.10)

    problem: RmsProblemPhasor = RmsProblemPhasor(
        grid=grid,
        options=RmsOptions(),
        pf_results=power_flow_results,
    )

    # Seven device equations precede the final topology-owned residuals. The
    # two-bus network must end in one DC and two AC current equations.
    nodal_equations: list[Expr] = problem._algebraic_eqs[-3:]
    dc_variable_names: set[str] = set(
        variable.name for variable in get_expression_vars(nodal_equations[0])
    )
    ac_real_variable_names: set[str] = set(
        variable.name for variable in get_expression_vars(nodal_equations[1])
    )
    ac_imaginary_variable_names: set[str] = set(
        variable.name for variable in get_expression_vars(nodal_equations[2])
    )

    assert len(problem._algebraic_eqs) == 10
    assert dc_variable_names == set(("Pf",))
    assert ac_real_variable_names == set((
        "Pt", "Qt", "Vr", "Vi", "Ir_existing", "P_selected", "Q_selected",
    ))
    assert ac_imaginary_variable_names == set((
        "Pt", "Qt", "Vr", "Vi", "Ii_existing", "P_selected", "Q_selected",
    ))
    assert nodal_equations[0].eval(Pf=0.25) == pytest.approx(-0.25)
    assert nodal_equations[1].eval(
        Pt=-0.24,
        Qt=0.10,
        Vr=0.8,
        Vi=0.6,
        Ir_existing=0.05,
        P_selected=0.04,
        Q_selected=-0.02,
    ) == pytest.approx(0.202)
    assert nodal_equations[2].eval(
        Pt=-0.24,
        Qt=0.10,
        Vr=0.8,
        Vi=0.6,
        Ii_existing=-0.03,
        P_selected=0.04,
        Q_selected=-0.02,
    ) == pytest.approx(0.234)


def test_rms_line_physical_shunt_power() -> None:
    """Compare mapped polar line powers with an independent pi primitive.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit(Sbase=100.0)
    source: Bus = grid.add_bus(Bus(name="source", Vnom=132.0))
    target: Bus = grid.add_bus(Bus(name="target", Vnom=132.0))
    line: Line = Line(bus_from=source, bus_to=target, r=0.01, x=0.1, b=0.002, g=0.003)
    grid.add_line(line)
    model: Block = get_line_rms_template(grid.var_factory).block
    physical_block: Block = model.children[0]
    mapped_values: dict[Var, Const] = dict()
    assign_static_api_object_mapping_for_device(
        grid=grid, device=line, mdl=model, problem_mapping=mapped_values, logger=None,
    )
    from_voltage: complex = 1.03 * np.exp(0.13j)
    to_voltage: complex = 0.96 * np.exp(-0.08j)
    series_admittance: complex = 1.0 / complex(line.R, line.X)
    half_shunt: complex = complex(line.G, line.B) / 2.0
    from_current: complex = series_admittance * (from_voltage - to_voltage) + half_shunt * from_voltage
    to_current: complex = series_admittance * (to_voltage - from_voltage) + half_shunt * to_voltage
    from_power: complex = from_voltage * np.conj(from_current)
    to_power: complex = to_voltage * np.conj(to_current)
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Const
    for parameter, value in physical_block.parameters.items():
        assert value.value is not None
        bindings[parameter.uid] = float(value.value)
    for parameter, value in mapped_values.items():
        assert value.value is not None
        bindings[parameter.uid] = float(value.value)
    variable: Var
    for variable in physical_block.algebraic_vars:
        bindings[variable.uid] = 0.0
    bindings[model.external_mapping[VarPowerFlowReferenceType.Vmf].uid] = abs(from_voltage)
    bindings[model.external_mapping[VarPowerFlowReferenceType.Vaf].uid] = float(np.angle(from_voltage))
    bindings[model.external_mapping[VarPowerFlowReferenceType.Vmt].uid] = abs(to_voltage)
    bindings[model.external_mapping[VarPowerFlowReferenceType.Vat].uid] = float(np.angle(to_voltage))
    status: float
    for status in (0.0, 1.0):
        # Both physical half-shunts follow the existing retained conduction status.
        for parameter in physical_block.event_dict:
            bindings[parameter.uid] = status
        expected: np.ndarray = status * np.array(
            (from_power.real, from_power.imag, to_power.real, to_power.imag), dtype=float,
        )
        actual: np.ndarray = np.zeros(4, dtype=float)
        equation_index: int
        for equation_index in range(4):
            actual[equation_index] = -float(physical_block.algebraic_eqs[equation_index].eval_uid(bindings))
        np.testing.assert_allclose(actual, expected, rtol=1.0e-10, atol=1.0e-12)


    # Exercise the actual DAE assembly and projection with the same nonzero G.
    pf_results: PowerFlowResults
    grid, pf_results = build_supported_vectorized_ac_load_case(physical_conductance=0.003)
    assert pf_results.converged
    problem: RmsProblemDaeVec = RmsProblemDaeVec(
        grid=grid, options=RmsOptions(), pf_results=pf_results,
    )
    problem.set_events_group(rms_events_group=RmsEventsGroup())
    solver: BackEulerImplicitIntegration = BackEulerImplicitIntegration(
        problem=problem, t0=0.0, t_end=0.0, h=1.0e-3, max_iter=25,
    )
    times: np.ndarray
    values: np.ndarray
    initialized: bool
    converged: bool
    times, values, initialized, converged = solver.simulate()
    assert initialized
    problem.update_input_matrices_by_model(x=values[0], dx=problem.get_dx0())
    assert np.linalg.norm(problem.rhs_algebraic_vec(x=values[0], dx=problem.get_dx0()), ord=np.inf) < 1.0e-6
    line = grid.lines[0]
    from_voltage = pf_results.voltage[0]
    to_voltage = pf_results.voltage[1]
    from_current = (from_voltage - to_voltage) / complex(line.R, line.X) + complex(line.G, line.B) * from_voltage / 2.0
    to_current = (to_voltage - from_voltage) / complex(line.R, line.X) + complex(line.G, line.B) * to_voltage / 2.0
    expected_power: np.ndarray = np.array((
        (from_voltage * np.conj(from_current)).real, (from_voltage * np.conj(from_current)).imag,
        (to_voltage * np.conj(to_current)).real, (to_voltage * np.conj(to_current)).imag,
    ))
    power_refs: tuple[VarPowerFlowReferenceType, ...] = (
        VarPowerFlowReferenceType.Pf, VarPowerFlowReferenceType.Qf,
        VarPowerFlowReferenceType.Pt, VarPowerFlowReferenceType.Qt,
    )
    actual_power: np.ndarray = np.array(tuple(
        values[0, problem._uid2idx_vars[line.rms_model.E(reference).uid]] for reference in power_refs
    ))
    np.testing.assert_allclose(actual_power, expected_power, rtol=1.0e-6, atol=1.0e-6)


def test_rms_phasor_line_physical_shunt_current() -> None:
    """Preserve physical shunt currents and virtual-tap scaling in the phasor model.

    :return: None.
    """
    grid: MultiCircuit = MultiCircuit(Sbase=2.0)
    source: Bus = grid.add_bus(Bus(Vnom=20.0))
    target: Bus = grid.add_bus(Bus(Vnom=20.0))
    line: Line = Line(bus_from=source, bus_to=target, r=0.02, x=0.2, b=0.006, g=0.004)
    grid.add_line(line)
    model: Block = get_line_phasor_rms_template(grid.var_factory).block
    mapped_values: dict[Var, Const] = dict()
    assign_static_api_object_mapping_for_device(
        grid=grid, device=line, mdl=model, problem_mapping=mapped_values, logger=None,
    )
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Const
    for parameter, value in model.parameters.items():
        if value.value is None:
            pass
        else:
            bindings[parameter.uid] = float(value.value)
    for parameter, value in mapped_values.items():
        assert value.value is not None
        bindings[parameter.uid] = float(value.value)
    from_voltage: complex = 1.02 * np.exp(0.14j)
    to_voltage: complex = 0.97 * np.exp(-0.06j)
    bindings[model.in_vars[0].uid] = float(from_voltage.real)
    bindings[model.in_vars[1].uid] = float(from_voltage.imag)
    bindings[model.in_vars[2].uid] = float(to_voltage.real)
    bindings[model.in_vars[3].uid] = float(to_voltage.imag)
    variable: Var
    for variable in model.algebraic_vars:
        bindings[variable.uid] = 0.0
    from_tap: float
    to_tap: float
    for from_tap, to_tap in ((1.0, 1.0), (1.03, 0.98)):
        tap_parameter: Var | None
        tap_parameter = model.api_obj_mapping.get(ParamPowerFlowReferenceType.vtap_f, None)
        assert tap_parameter is not None
        bindings[tap_parameter.uid] = from_tap
        tap_parameter = model.api_obj_mapping.get(ParamPowerFlowReferenceType.vtap_t, None)
        assert tap_parameter is not None
        bindings[tap_parameter.uid] = to_tap
        series: complex = 1.0 / complex(line.R, line.X)
        half_shunt: complex = complex(line.G, line.B) / 2.0
        from_current: complex = (
            (series + half_shunt) * from_voltage / (from_tap * from_tap)
            - series * to_voltage / (from_tap * to_tap)
        )
        to_current: complex = (
            (series + half_shunt) * to_voltage / (to_tap * to_tap)
            - series * from_voltage / (from_tap * to_tap)
        )
        expected: np.ndarray = np.array((from_current.real, from_current.imag, to_current.real, to_current.imag))
        actual: np.ndarray = np.zeros(4)
        equation_index: int
        for equation_index in range(4):
            actual[equation_index] = -float(model.algebraic_eqs[equation_index].eval_uid(bindings))
        np.testing.assert_allclose(actual, expected, rtol=1.0e-10, atol=1.0e-12)


@pytest.mark.parametrize("problem_type", (RmsProblemTypes.CurrentBalance, RmsProblemTypes.Multilinear))
@pytest.mark.parametrize("use_factory", (False, True))
@pytest.mark.parametrize("logger_present,prepopulate", ((False, False), (True, False), (True, True)))
def test_current_balance_logger_contract(
        problem_type: RmsProblemTypes, use_factory: bool,
        logger_present: bool, prepopulate: bool) -> None:
    """Preserve caller diagnostics through ordinary and inherited RMS entry.

    :param problem_type: Direct phasor or inherited Multilinear constructor.
    :param use_factory: Enter through the production factory or direct constructor.
    :param logger_present: Supply a caller-owned Logger or request a local fallback.
    :param prepopulate: Include a prior entry so preservation is observable.
    :return: None.
    """
    grid: MultiCircuit = MultiCircuit()
    bus: Bus = grid.add_bus(Bus(name="phasor bus"))
    voltage_real: Var = grid.var_factory.add_var("Vr", reference=VarPowerFlowReferenceType.Vr)
    voltage_imaginary: Var = grid.var_factory.add_var("Vi", reference=VarPowerFlowReferenceType.Vi)
    bus.rms_model = Block(algebraic_vars=list((voltage_real, voltage_imaginary)),
                          out_vars=list((voltage_real, voltage_imaginary)),
                          external_mapping=dict(((VarPowerFlowReferenceType.Vr, voltage_real),
                                                 (VarPowerFlowReferenceType.Vi, voltage_imaginary))))
    # A missing optional device model generates existing constructor diagnostics.
    # This fixture qualifies the entry interface, not a numerical trajectory.
    grid.add_load(bus=bus, api_obj=Load(name="missing RMS model"))
    pf: PowerFlowResults = PowerFlowResults(
        n=1, m=0, n_hvdc=0, n_vsc=0, n_gen=0, n_batt=0, n_sh=0,
        bus_names=np.array((bus.name,)), branch_names=np.array(tuple()),
        hvdc_names=np.array(tuple()), vsc_names=np.array(tuple()),
        gen_names=np.array(tuple()), batt_names=np.array(tuple()),
        sh_names=np.array(tuple()), bus_types=np.zeros(1, dtype=int))
    pf.voltage[:] = 1.0 + 0.0j
    logger: Logger | None = Logger() if logger_present else None
    if prepopulate:
        assert logger is not None
        logger.add_info("Existing caller diagnostic")
    else:
        pass
    prior_count: int = len(logger.entries) if logger is not None else 0
    options: RmsOptions = RmsOptions(problem_type=problem_type)
    problem: RmsProblemPhasor
    if use_factory:
        factory_problem: RmsProblemTemplate = build_rms_problem(grid=grid, options=options, pf_results=pf, logger=logger)
        assert isinstance(factory_problem, RmsProblemPhasor)
        problem = factory_problem
    elif problem_type == RmsProblemTypes.CurrentBalance:
        problem = RmsProblemPhasor(grid, options, pf, None, logger)
    else:
        problem = RmsProblemMultilinear(grid, options, pf, None, logger)
    if logger is not None:
        assert problem.logger is logger
    else:
        assert isinstance(problem.logger, Logger)
        second: RmsProblemPhasor = RmsProblemPhasor(grid.copy(), options, pf)
        assert second.logger is not problem.logger
        problem.logger.add_info("First instance only")
        assert not any(entry.msg == "First instance only" for entry in second.logger.entries)
    assert len(problem.logger.entries) > prior_count
    assert any(entry.msg == "No RMS model" for entry in problem.logger.entries[prior_count:])
    if prepopulate:
        assert problem.logger.entries[0].msg == "Existing caller diagnostic"
    else:
        pass


@pytest.mark.parametrize("nominal_ratio", (1.0, 0.97, 1.0 / 0.97))
@pytest.mark.parametrize("physical_conductance", (0.0, 0.003))
@pytest.mark.parametrize("active", (False, True))
@pytest.mark.parametrize("mapped_shunt", (False, True))
@pytest.mark.parametrize("tolerance", (1.0e-7, 1.0e-9))
def test_current_balance_line_shunt_supply(
        nominal_ratio: float, physical_conductance: float, active: bool,
        mapped_shunt: bool, tolerance: float) -> None:
    """Check terminal physics and native projection through the real RMS factory.

    :param nominal_ratio: Receiving-to-sending nominal voltage ratio.
    :param physical_conductance: Total physical Line shunt in system per unit.
    :param active: Whether assembly should retain this branch's admittances.
    :param mapped_shunt: Expose physical G or retain an authored unmapped value.
    :param tolerance: Residual gate for the existing algebraic projection.
    :return: None.
    """
    grid: MultiCircuit = MultiCircuit(Sbase=2.0)
    source: Bus = grid.add_bus(Bus(Vnom=10.0, is_slack=True))
    target: Bus = grid.add_bus(Bus(Vnom=10.0 * nominal_ratio))
    line: Line = grid.add_line(Line(bus_from=source, bus_to=target, r=0.02, x=0.15,
                                   b=0.006, g=physical_conductance))
    generator: Generator = grid.add_generator(bus=source, api_obj=Generator(vset=1.0))
    load: Load = grid.add_load(bus=target, api_obj=Load(P=0.5, Q=0.1))
    pf: PowerFlowResults = power_flow(grid)
    assert pf.converged
    initialize_bus_phasor_rms(source, grid.var_factory)
    initialize_bus_phasor_rms(target, grid.var_factory)
    line_model: Block = get_line_phasor_rms_template(grid.var_factory).block
    # A stale authored value makes overwrite, inactive gating and legacy retention
    # observable. A Block without this mapping keeps its authored parameter.
    shunt_parameter: Var = line_model.api_obj_mapping[ParamPowerFlowReferenceType.shunt_g_pu]
    authored_shunt: float = 0.0007
    line_model.parameters[shunt_parameter] = Const(authored_shunt)
    if mapped_shunt:
        pass
    else:
        del line_model.api_obj_mapping[ParamPowerFlowReferenceType.shunt_g_pu]
    set_rms_model(line, line_model, grid.var_factory)
    load_model: Block = get_load_phasor_current_rms_template(grid.var_factory).block
    # Explicit physical fixture data isolates Line supply from the separate
    # legacy optional-load parameter mapping problem.
    load_model.set_parameter_in_model(var_name="Pl0", new_value=-load.P / grid.Sbase)
    load_model.set_parameter_in_model(var_name="Ql0", new_value=-load.Q / grid.Sbase)
    set_rms_model(load, load_model, grid.var_factory)
    current_real: Var = grid.var_factory.add_var("source Ir")
    current_imaginary: Var = grid.var_factory.add_var("source Ii")
    voltage_real: Var = source.rms_model.E(VarPowerFlowReferenceType.Vr)
    voltage_imaginary: Var = source.rms_model.E(VarPowerFlowReferenceType.Vi)
    # An authored ideal voltage boundary closes this static fixture; it does
    # not qualify machine dynamics or the normal driver's time integrator.
    generator.rms_model = Block(
        algebraic_vars=list((current_real, current_imaginary)),
        algebraic_eqs=list((voltage_real - Const(float(pf.voltage[0].real)),
                           voltage_imaginary - Const(float(pf.voltage[0].imag)))),
        out_vars=list((current_real, current_imaginary)),
        external_mapping=dict(((VarPowerFlowReferenceType.Ir, current_real),
                               (VarPowerFlowReferenceType.Ii, current_imaginary))))
    # Inactive cases use the earlier connected PF only as terminal voltage data.
    # Projection of an islanded network is outside this test's contract.
    line.active = active
    options: RmsOptions = RmsOptions(problem_type=RmsProblemTypes.CurrentBalance)
    problem: RmsProblemTemplate = build_rms_problem(grid=grid, options=options, pf_results=pf)
    assert isinstance(problem, RmsProblemPhasor)
    assert not any(entry.msg == "No RMS model" for entry in problem.logger.entries)
    model: Block = line.rms_model
    bindings: dict[int, float] = dict()
    parameter: Var
    constant: Const
    for parameter, constant in model.parameters.items():
        assert constant.value is not None
        bindings[parameter.uid] = float(constant.value)
    bindings[model.E(VarPowerFlowReferenceType.Vrf).uid] = float(pf.voltage[0].real)
    bindings[model.E(VarPowerFlowReferenceType.Vif).uid] = float(pf.voltage[0].imag)
    bindings[model.E(VarPowerFlowReferenceType.Vrt).uid] = float(pf.voltage[1].real)
    bindings[model.E(VarPowerFlowReferenceType.Vit).uid] = float(pf.voltage[1].imag)
    variable: Var
    for variable in model.algebraic_vars:
        bindings[variable.uid] = 0.0
    active_factor: float = 1.0 if active else 0.0
    expected_shunt: float = active_factor * line.G if mapped_shunt else authored_shunt
    assembled_shunt: Var = next(parameter for parameter in model.parameters if parameter.name == "gsh")
    assert float(model.parameters[assembled_shunt].value) == pytest.approx(expected_shunt)
    from_tap: float = 1.0
    to_tap: float = float(source.Vnom / target.Vnom)
    series: complex = active_factor / complex(line.R, line.X)
    half_shunt: complex = complex(expected_shunt, active_factor * line.B) / 2.0
    from_voltage: complex = complex(pf.voltage[0])
    to_voltage: complex = complex(pf.voltage[1])
    from_current: complex = ((series + half_shunt) * from_voltage / (from_tap * from_tap)
                             - series * to_voltage / (from_tap * to_tap))
    to_current: complex = ((series + half_shunt) * to_voltage / (to_tap * to_tap)
                           - series * from_voltage / (from_tap * to_tap))
    expected: np.ndarray = np.array((from_current.real, from_current.imag,
                                    to_current.real, to_current.imag))
    actual: np.ndarray = np.zeros(4)
    equation_index: int
    for equation_index in range(4):
        actual[equation_index] = -float(model.algebraic_eqs[equation_index].eval_uid(bindings))
    np.testing.assert_allclose(actual, expected, rtol=1.0e-10, atol=1.0e-12)
    if active and mapped_shunt:
        # The full square KCL network must retain the solved PF voltage; a small
        # Newton residual alone would conceal the old omitted-G physical error.
        assert len(problem.get_algebraic_eqs) == problem.get_all_vars_number()
        problem.set_events_group(RmsEventsGroup())
        seed: np.ndarray = problem.get_x0()
        derivatives: np.ndarray = np.zeros(problem.get_diff_var_number())
        assert np.max(np.abs(problem.rhs_algebraic(seed, derivatives))) < 1.0e-9
        projected: np.ndarray
        initialized: bool
        residual: float
        projected, initialized, residual = project_initial_algebraic_state(
            problem=problem, initial_values=seed, differential_values=derivatives,
            tolerance=tolerance, max_iter=25)
        assert initialized and residual <= tolerance
        receiving_voltage: complex = complex(
            projected[problem.get_var_idx(target.rms_model.E(VarPowerFlowReferenceType.Vr))],
            projected[problem.get_var_idx(target.rms_model.E(VarPowerFlowReferenceType.Vi))])
        assert abs(receiving_voltage - to_voltage) < 1.0e-9
    else:
        pass
    problem.close_fmu_cs_devices()
    problem.close_fmu_me_devices()
