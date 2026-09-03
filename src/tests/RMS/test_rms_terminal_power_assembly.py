# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pytest

from VeraGridEngine.basic_structures import BoolVec, ObjVec
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import PowerFlowResults
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_vectorized import RmsProblemDaeVec
from VeraGridEngine.Simulations.Rms.problems.rms_problem_phasor import RmsProblemPhasor
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae_full_vectorized import (
    RmsProblemDaeFullVec,
)
from VeraGridEngine.Simulations.Rms.problems.rms_terminal_power_assembly import (
    assemble_rms_terminal_power_contributions,
    convert_rms_ac_power_balance_to_current_balance,
)
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Templates.Rms.vsc_gfl_dclinked import build_vsc_rms
from VeraGridEngine.Utils.Symbolic.block import (
    Block,
    RmsTerminalPowerContribution,
    RmsTerminalSide,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var, get_expression_vars
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def test_terminal_power_assembly_uses_physical_topology() -> None:
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
    model.dynamic_model_contract.rms_terminal_power_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.FROM,
            active_power_reference=VarPowerFlowReferenceType.Pf,
            reactive_power_reference=None,
        ),
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.TO,
            active_power_reference=VarPowerFlowReferenceType.Pt,
            reactive_power_reference=VarPowerFlowReferenceType.Qt,
        ),
    ))
    active_balance: ObjVec = np.zeros(2, dtype=object)
    reactive_balance: ObjVec = np.zeros(2, dtype=object)
    active_used: BoolVec = np.zeros(2, dtype=bool)
    reactive_used: BoolVec = np.zeros(2, dtype=bool)

    assemble_rms_terminal_power_contributions(
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


def test_terminal_power_assembly_rejects_missing_contract() -> None:
    """Fail closed instead of inferring network coupling from variable names.

    :return: None.
    """
    active_balance: ObjVec = np.zeros(2, dtype=object)
    reactive_balance: ObjVec = np.zeros(2, dtype=object)
    active_used: BoolVec = np.zeros(2, dtype=bool)
    reactive_used: BoolVec = np.zeros(2, dtype=bool)

    with pytest.raises(ValueError, match="no declared terminal"):
        assemble_rms_terminal_power_contributions(
            model=Block(),
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


def test_terminal_power_assembly_rejects_reactive_power_on_dc_bus_atomically() -> None:
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
    model.dynamic_model_contract.rms_terminal_power_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.FROM,
            active_power_reference=VarPowerFlowReferenceType.Pf,
            reactive_power_reference=VarPowerFlowReferenceType.Qf,
        ),
    ))
    active_balance: ObjVec = np.zeros(2, dtype=object)
    reactive_balance: ObjVec = np.zeros(2, dtype=object)
    active_used: BoolVec = np.zeros(2, dtype=bool)
    reactive_used: BoolVec = np.zeros(2, dtype=bool)

    with pytest.raises(ValueError, match="reactive power on a DC bus"):
        assemble_rms_terminal_power_contributions(
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
    model.dynamic_model_contract.rms_terminal_power_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.BUS,
            active_power_reference=VarPowerFlowReferenceType.P,
            reactive_power_reference=VarPowerFlowReferenceType.Q,
        ),
    ))
    active_balance: ObjVec = np.zeros(2, dtype=object)
    reactive_balance: ObjVec = np.zeros(2, dtype=object)
    active_used: BoolVec = np.zeros(2, dtype=bool)
    reactive_used: BoolVec = np.zeros(2, dtype=bool)

    assemble_rms_terminal_power_contributions(
        model=model,
        bus_from_index=None,
        bus_to_index=None,
        bus_from_is_dc=None,
        bus_to_is_dc=None,
        active_power_balance=active_balance,
        active_power_balance_used=active_used,
        reactive_power_balance=reactive_balance,
        reactive_power_balance_used=reactive_used,
        bus_index=1,
        bus_is_dc=False,
    )
    restored_model: Block = Block.parse(data=model.to_dict())
    restored_contribution: RmsTerminalPowerContribution = (
        restored_model.dynamic_model_contract.rms_terminal_power_contributions[0]
    )

    assert active_used.tolist() == [False, True]
    assert reactive_used.tolist() == [False, True]
    assert active_balance[1].eval(P=0.2) == pytest.approx(0.2)
    assert reactive_balance[1].eval(Q=-0.1) == pytest.approx(-0.1)
    assert restored_contribution.get_terminal_side() is RmsTerminalSide.BUS


def test_standard_vsc_template_declares_both_terminal_contributions() -> None:
    """Keep the native VSC template compatible with fail-closed assembly.

    :return: None.
    """
    model: Block = build_vsc_rms(vfactory=VarFactory()).block
    contributions: list[RmsTerminalPowerContribution] = (
        model.dynamic_model_contract.rms_terminal_power_contributions
    )

    assert model.out_vars == list()
    assert len(contributions) == 2
    assert contributions[0].get_terminal_side() is RmsTerminalSide.FROM
    assert contributions[1].get_terminal_side() is RmsTerminalSide.TO


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
    assert len(full_vectorized_problem._legacy_balance_layout_by_model_type) == 1
    full_vectorized_problem.set_events_group(rms_events_group=RmsEventsGroup())
    assert set(full_vectorized_problem._legacy_balance_layout_by_model_type.keys()).issubset(
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
        iter(full_vectorized_problem._legacy_balance_layout_by_model_type.keys())
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

    assert residual[:3].tolist() == pytest.approx((0.20, -0.19, 0.03))
    assert full_vectorized_problem.Q_vec[1] == pytest.approx(-0.03)
    # The physical AC converter bus retains both Q and P nodal rows; converter
    # control equations do not replace either network balance.
    assert residual[-3:].tolist() == pytest.approx((-0.20, -0.03, 0.19))
    assert jacobian[-3, from_active_index] == pytest.approx(-1.0)
    assert jacobian[-2, to_reactive_index] == pytest.approx(-1.0)
    assert jacobian[-1, to_active_index] == pytest.approx(-1.0)


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
    first_model.dynamic_model_contract.rms_terminal_power_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.BUS,
            active_power_reference=VarPowerFlowReferenceType.P,
            reactive_power_reference=VarPowerFlowReferenceType.Q,
        ),
    ))
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
    second_model.dynamic_model_contract.rms_terminal_power_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.BUS,
            active_power_reference=VarPowerFlowReferenceType.P,
            reactive_power_reference=VarPowerFlowReferenceType.Q,
        ),
    ))
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
    assert len(problem._terminal_balance_layout_by_model_type) == 1
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
    typed_model.dynamic_model_contract.rms_terminal_power_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.BUS,
            active_power_reference=VarPowerFlowReferenceType.P,
            reactive_power_reference=VarPowerFlowReferenceType.Q,
        ),
    ))
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


def test_full_vectorized_rejects_typed_then_legacy_equivalent_models() -> None:
    """Fail closed when a legacy instance follows a typed representative.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    grid, power_flow_results = build_mixed_terminal_contract_grid(contract_first=True)

    with pytest.raises(ValueError, match="same terminal-power contract mode"):
        RmsProblemDaeFullVec(
            grid=grid,
            options=RmsOptions(),
            pf_results=power_flow_results,
        )


def test_full_vectorized_rejects_legacy_then_typed_equivalent_models() -> None:
    """Fail closed when a typed instance follows a legacy representative.

    :return: None.
    """
    grid: MultiCircuit
    power_flow_results: PowerFlowResults
    grid, power_flow_results = build_mixed_terminal_contract_grid(contract_first=False)

    with pytest.raises(ValueError):
        RmsProblemDaeFullVec(
            grid=grid,
            options=RmsOptions(),
            pf_results=power_flow_results,
        )


def test_phasor_balance_consumes_vsc_terminal_power_contributions() -> None:
    """Convert assembled VSC terminal powers into the phasor AC KCL residual.

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
    model.dynamic_model_contract.rms_terminal_power_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.FROM,
            active_power_reference=VarPowerFlowReferenceType.Pf,
            reactive_power_reference=None,
        ),
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.TO,
            active_power_reference=VarPowerFlowReferenceType.Pt,
            reactive_power_reference=VarPowerFlowReferenceType.Qt,
        ),
    ))
    active_balance: ObjVec = np.zeros(2, dtype=object)
    reactive_balance: ObjVec = np.zeros(2, dtype=object)
    real_current_balance: ObjVec = np.zeros(2, dtype=object)
    imaginary_current_balance: ObjVec = np.zeros(2, dtype=object)
    active_used: BoolVec = np.zeros(2, dtype=bool)
    reactive_used: BoolVec = np.zeros(2, dtype=bool)
    real_current_used: BoolVec = np.zeros(2, dtype=bool)
    imaginary_current_used: BoolVec = np.zeros(2, dtype=bool)

    # Assemble by physical VSC topology first, as each RMS problem does.
    assemble_rms_terminal_power_contributions(
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
    vsc_model.dynamic_model_contract.rms_terminal_power_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.FROM,
            active_power_reference=VarPowerFlowReferenceType.Pf,
            reactive_power_reference=None,
        ),
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.TO,
            active_power_reference=VarPowerFlowReferenceType.Pt,
            reactive_power_reference=VarPowerFlowReferenceType.Qt,
        ),
    ))
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
    selected_power_model.dynamic_model_contract.rms_terminal_power_contributions = list((
        RmsTerminalPowerContribution(
            terminal_side=RmsTerminalSide.BUS,
            active_power_reference=VarPowerFlowReferenceType.P,
            reactive_power_reference=VarPowerFlowReferenceType.Q,
        ),
    ))
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
