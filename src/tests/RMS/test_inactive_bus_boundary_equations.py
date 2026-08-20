from __future__ import annotations

from typing import Dict, List

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import build_inactive_bus_boundary_equations
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.symbolic import Expr, Var


def test_inactive_ac_bus_boundary_fixes_voltage_initial_point() -> None:
    """
    Verify an isolated inactive AC bus contributes two voltage constraints.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    bus: Bus = Bus(name="inactive AC", active=False)
    initialize_bus_rms(bus=bus, vf=var_factory)
    voltage_magnitude: Var = bus.rms_model.algebraic_vars[0]
    voltage_angle: Var = bus.rms_model.algebraic_vars[1]
    init_guess: Dict[int, float | int | complex | None] = dict({
        voltage_magnitude.uid: 1.03,
        voltage_angle.uid: -0.12,
    })

    equations: List[Expr] = build_inactive_bus_boundary_equations(bus=bus, init_guess=init_guess)
    initial_bindings: Dict[int, float] = dict({
        voltage_magnitude.uid: 1.03,
        voltage_angle.uid: -0.12,
    })

    assert len(equations) == 2
    assert equations[0].eval_uid(initial_bindings) == 0.0
    assert equations[1].eval_uid(initial_bindings) == 0.0
    assert equations[0].eval_uid(dict({voltage_magnitude.uid: 1.04})) != 0.0
    assert equations[1].eval_uid(dict({voltage_angle.uid: -0.11})) != 0.0


def test_inactive_dc_bus_boundary_fixes_voltage_initial_point() -> None:
    """
    Verify an isolated inactive DC bus contributes one voltage constraint.

    :return: None.
    """
    var_factory: VarFactory = VarFactory()
    bus: Bus = Bus(name="inactive DC", active=False, is_dc=True)
    initialize_bus_rms(bus=bus, vf=var_factory)
    dc_voltage: Var = bus.rms_model.algebraic_vars[0]
    init_guess: Dict[int, float | int | complex | None] = dict({dc_voltage.uid: 0.98})

    equations: List[Expr] = build_inactive_bus_boundary_equations(bus=bus, init_guess=init_guess)

    assert len(equations) == 1
    assert equations[0].eval_uid(dict({dc_voltage.uid: 0.98})) == 0.0
    assert equations[0].eval_uid(dict({dc_voltage.uid: 1.0})) != 0.0

