# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Exercise DERA1 trip timers, Vmin capture, recovery, and codec persistence."""

import numpy as np
import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Rms.renewable_controls.dera1_protection import (
    Dera1ProtectionSettings,
    build_dera1_protection_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import (
    BlockProceduralLogicUpdater,
    DelayedThresholdLatchLogic,
    ProceduralLogicCodec,
    ResetOnRisingEdgeLogic,
    build_boundary_updater_from_block,
)


class Dera1ProtectionProblem(EmtProblemTemplate):
    """Bind DERA1 protection logic to a compact accepted-state runtime."""

    __slots__ = ()


def _build_runtime(
        settings: Dera1ProtectionSettings,
) -> tuple[Block, Dera1ProtectionProblem, BlockProceduralLogicUpdater]:
    """Build and bind one serializable DERA1 protection block.

    :param settings: Protection parameters under test.
    :return: Model block, runtime problem, and procedural updater.
    """
    factory: VarFactory = VarFactory()
    block: Block = build_dera1_protection_template(
        factory, settings=settings,
    ).block
    voltage: Var = block.in_vars[0]
    frequency: Var = block.in_vars[1]
    runtime_block: Block = Block(
        name='DERA1 protection runtime',
        state_vars=list((voltage, frequency)),
        diff_vars=list((factory.add_diff_var('d_Dera1Voltage', base_var=voltage),
                        factory.add_diff_var('d_Dera1Frequency', base_var=frequency))),
        state_eqs=list((Const(0.0), Const(0.0))),
        init_eqs=dict(((voltage, Const(settings.initial_voltage)),
                       (frequency, Const(settings.initial_frequency_hz)))),
        algebraic_vars=block.algebraic_vars,
        algebraic_eqs=block.algebraic_eqs,
        event_dict=block.event_dict,
        mode_dict=block.mode_dict,
        procedural_logic=block.procedural_logic,
    )
    restored: Block = roundtrip_block(runtime_block, ProceduralLogicCodec())
    problem: Dera1ProtectionProblem = Dera1ProtectionProblem(
        sys_block=restored,
        glob_time=factory.add_var('Dera1ProtectionTime'),
        static_parameter_values_mapping=dict(),
    )
    updater: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(problem)
    assert updater is not None
    return restored, problem, updater


def _refresh_algebraics(
        block: Block,
        problem: Dera1ProtectionProblem,
        state: np.ndarray,
        parameters: np.ndarray,
) -> None:
    """Evaluate this explicit block's algebraic equations before relay updates.

    :param block: DERA1 protection system block.
    :param problem: Runtime variable-index owner.
    :param state: Mutable state/algebraic vector.
    :param parameters: Mutable event-parameter vector.
    :return: None.
    """
    bindings: dict[int, float] = dict()
    variable: Var
    for variable in block.state_vars:
        bindings[variable.uid] = float(state[problem.get_var_idx(variable)])
    for variable in block.algebraic_vars:
        bindings[variable.uid] = float(state[problem.get_var_idx(variable)])
    for variable, _expression in block.event_dict.items():
        bindings[variable.uid] = float(parameters[problem.uid2idx_event_params[variable.uid]])
    equation: Expr
    for variable, equation in zip(block.algebraic_vars, block.algebraic_eqs):
        state_index: int = problem.get_var_idx(variable)
        state[state_index] = 0.0
        bindings[variable.uid] = 0.0
        value: float = -equation.eval_uid(bindings)
        state[state_index] = value
        bindings[variable.uid] = value


def test_dera1_undervoltage_partial_trip_captures_vmin_and_recovers() -> None:
    """Expire tvl1 at its exact event, capture Vmin, then follow Vrfrac recovery."""
    settings: Dera1ProtectionSettings = Dera1ProtectionSettings(
        voltage_trip_enabled=True, vl0=0.5, vl1=0.9, tvl0=1.0, tvl1=0.2,
        vh1=1.2, vh0=1.5, vrfrac=0.5,
    )
    block, problem, updater = _build_runtime(settings)
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    voltage: Var = block.state_vars[0]
    voltage_index: int = problem.get_var_idx(voltage)
    state[voltage_index] = settings.initial_voltage
    updater.update(0.0, state, parameters)

    state[voltage_index] = 0.8
    _refresh_algebraics(block, problem, state, parameters)
    assert updater.get_next_forced_event_time(0.0, 0.1) is None
    updater.update(0.1, state, parameters)
    assert updater.get_next_forced_event_time(0.1, 0.3) == pytest.approx(0.2)

    updater.update(0.2, state, parameters)
    _refresh_algebraics(block, problem, state, parameters)
    extreme: Var = next(
        variable for variable in block.event_dict
        if variable.name.startswith('UnderVoltageExtreme_')
    )
    multiplier: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name.startswith('UnderVoltageMultiplier_')
    )
    assert parameters[problem.uid2idx_event_params[extreme.uid]] == pytest.approx(0.8)
    assert state[problem.get_var_idx(multiplier)] == pytest.approx(0.75)

    state[voltage_index] = 1.0
    _refresh_algebraics(block, problem, state, parameters)
    assert state[problem.get_var_idx(multiplier)] == pytest.approx(0.875)


def test_dera1_full_undervoltage_trip_latches_zero_after_timer() -> None:
    """The vl0 timer latches full trip even after terminal voltage recovers."""
    settings: Dera1ProtectionSettings = Dera1ProtectionSettings(
        voltage_trip_enabled=True, vl0=0.5, vl1=0.9, tvl0=0.1,
        tvl1=0.5, vh1=1.2, vh0=1.5, vrfrac=0.5,
    )
    block, problem, updater = _build_runtime(settings)
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    voltage: Var = block.state_vars[0]
    voltage_index: int = problem.get_var_idx(voltage)
    state[voltage_index] = settings.initial_voltage
    updater.update(0.0, state, parameters)
    state[voltage_index] = 0.4
    _refresh_algebraics(block, problem, state, parameters)
    updater.get_next_forced_event_time(0.0, 0.05)
    updater.update(0.05, state, parameters)
    assert updater.get_next_forced_event_time(0.05, 0.2) == pytest.approx(0.1)
    updater.update(0.1, state, parameters)
    state[voltage_index] = 1.0
    _refresh_algebraics(block, problem, state, parameters)
    multiplier: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name.startswith('VoltageTripMultiplier_')
    )
    assert state[problem.get_var_idx(multiplier)] == pytest.approx(0.0)


def test_dera1_frequency_trip_is_bypassed_below_vpr() -> None:
    """Low terminal voltage clears pending frequency pickup and does not trip."""
    settings: Dera1ProtectionSettings = Dera1ProtectionSettings(
        frequency_trip_enabled=True, fl=57.0, fh=63.0,
        tfl=0.2, tfh=0.2, vpr=0.8, initial_voltage=1.0,
    )
    block, problem, updater = _build_runtime(settings)
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    voltage: Var = block.state_vars[0]
    frequency: Var = block.state_vars[1]
    voltage_index: int = problem.get_var_idx(voltage)
    frequency_index: int = problem.get_var_idx(frequency)
    state[voltage_index] = settings.initial_voltage
    state[frequency_index] = settings.initial_frequency_hz
    updater.update(0.0, state, parameters)

    state[frequency_index] = 56.0
    _refresh_algebraics(block, problem, state, parameters)
    updater.get_next_forced_event_time(0.0, 0.1)
    updater.update(0.1, state, parameters)
    assert updater.get_next_forced_event_time(0.1, 0.3) == pytest.approx(0.2)

    state[voltage_index] = 0.7
    _refresh_algebraics(block, problem, state, parameters)
    updater.get_next_forced_event_time(0.1, 0.3)
    updater.update(0.2, state, parameters)
    _refresh_algebraics(block, problem, state, parameters)
    multiplier: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name.startswith('FrequencyTripMultiplier_')
    )
    assert state[problem.get_var_idx(multiplier)] == pytest.approx(1.0)


def test_dera1_overvoltage_partial_trip_captures_vmax_and_recovers() -> None:
    """The transformed high-side curve captures Vmax at its partial timer."""
    settings: Dera1ProtectionSettings = Dera1ProtectionSettings(
        voltage_trip_enabled=True, vh1=1.1, vh0=1.5,
        tvh1=0.1, tvh0=0.5, vrfrac=0.5,
    )
    block, problem, updater = _build_runtime(settings)
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    voltage: Var = block.state_vars[0]
    voltage_index: int = problem.get_var_idx(voltage)
    state[voltage_index] = settings.initial_voltage
    updater.update(0.0, state, parameters)
    state[voltage_index] = 1.2
    _refresh_algebraics(block, problem, state, parameters)
    updater.get_next_forced_event_time(0.0, 0.05)
    updater.update(0.05, state, parameters)
    assert updater.get_next_forced_event_time(0.05, 0.2) == pytest.approx(0.1)
    updater.update(0.1, state, parameters)
    extreme: Var = next(
        variable for variable in block.event_dict
        if variable.name.startswith('OverVoltageExtreme_')
    )
    assert parameters[problem.uid2idx_event_params[extreme.uid]] == pytest.approx(-1.2)
    state[voltage_index] = 0.9
    _refresh_algebraics(block, problem, state, parameters)
    multiplier: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name.startswith('OverVoltageMultiplier_')
    )
    assert state[problem.get_var_idx(multiplier)] == pytest.approx(0.875)


def test_dera1_low_frequency_trip_latches_after_tfl() -> None:
    """Frequency below fl trips after its timer when voltage is above Vpr."""
    settings: Dera1ProtectionSettings = Dera1ProtectionSettings(
        frequency_trip_enabled=True, fl=57.0, fh=63.0,
        tfl=0.1, tfh=0.2, vpr=0.8,
    )
    block, problem, updater = _build_runtime(settings)
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    voltage: Var = block.state_vars[0]
    frequency: Var = block.state_vars[1]
    voltage_index: int = problem.get_var_idx(voltage)
    frequency_index: int = problem.get_var_idx(frequency)
    state[voltage_index] = settings.initial_voltage
    state[frequency_index] = settings.initial_frequency_hz
    updater.update(0.0, state, parameters)
    state[frequency_index] = 56.0
    _refresh_algebraics(block, problem, state, parameters)
    updater.get_next_forced_event_time(0.0, 0.05)
    updater.update(0.05, state, parameters)
    assert updater.get_next_forced_event_time(0.05, 0.2) == pytest.approx(0.1)
    updater.update(0.1, state, parameters)
    _refresh_algebraics(block, problem, state, parameters)
    multiplier: Var = next(
        variable for variable in block.algebraic_vars
        if variable.name.startswith('FrequencyTripMultiplier_')
    )
    assert state[problem.get_var_idx(multiplier)] == pytest.approx(0.0)


def test_dera1_protection_builds_latches_and_capture_logic() -> None:
    """Use existing serializable timer and rising-edge runtime primitives."""
    block: Block = build_dera1_protection_template(
        VarFactory(),
        settings=Dera1ProtectionSettings(
            voltage_trip_enabled=True, frequency_trip_enabled=True,
            initial_voltage=1.0, initial_frequency_hz=60.0,
        ),
    ).block
    assert sum(isinstance(logic, DelayedThresholdLatchLogic)
               for logic in block.procedural_logic) == 6
    assert sum(isinstance(logic, ResetOnRisingEdgeLogic)
               for logic in block.procedural_logic) == 2
