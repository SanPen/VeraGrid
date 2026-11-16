# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""OSTB2T equations and switching declarations follow the PSS/E data sheet."""

import pytest
import numpy as np

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.raw.dyr_parser import parse_dyr
from VeraGridEngine.IO.raw.dyr_to_veragrid import (
    PsseDynamicBinding,
    build_controller,
    dynamic_binding,
)
from VeraGridEngine.IO.raw.versioned.base.dyr import DyrRecord
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ostb2t import (
    Ostb2tParameters,
    build_ostb2t_template,
)
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Utils.procedural_logic import (
    BlockProceduralLogicUpdater,
    build_boundary_updater_from_block,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.procedural_logic import (
    FlipFlopLogic,
    ProceduralLogicCodec,
    TimedPulseLogic,
)
from VeraGridEngine.enumerations import InternationalStandardModel


def _ostb2t_event_runtime(
        name: str,
) -> tuple[EmtProblemTemplate, BlockProceduralLogicUpdater, np.ndarray, np.ndarray,
           dict[str, int]]:
    """Build an isolated procedural runtime with three mutable source inputs.

    :param name: Unique model name preventing symbolic UID collisions.
    :return: Bound problem, procedural updater, state/parameter vectors and input indexes.
    """
    factory: VarFactory = VarFactory()
    template: RmsModelTemplate = build_ostb2t_template(
        factory, name,
        Ostb2tParameters(switch_on_time=0.2, switch_off_time=0.8, seal_time=0.3),
    )
    input_indices: dict[str, int] = dict()
    for port, initial_value in zip(tuple(template.block.in_vars), (0.0, 1.0, 1.0), strict=True):
        template.block.in_vars.remove(port)
        template.block.init_eqs.pop(port, None)
        template.block.event_dict[port] = factory.add_const(initial_value)
        if port.name.startswith('SpeedDeviationPu_'):
            input_indices['SpeedDeviationPu'] = port.uid
        elif port.name.startswith('ETerminalPu_'):
            input_indices['ETerminalPu'] = port.uid
        else:
            input_indices['EfdPu'] = port.uid
    parsed: Block = roundtrip_block(template.block, ProceduralLogicCodec())
    problem: EmtProblemTemplate = EmtProblemTemplate(
        sys_block=parsed,
        glob_time=factory.add_var('glob_time_' + name),
        static_parameter_values_mapping=dict(),
    )
    updater: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(problem)
    assert updater is not None
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    indexes: dict[str, int] = dict(
        (name_key, int(problem.uid2idx_event_params[uid]))
        for name_key, uid in input_indices.items()
    )
    s1: Var = next(variable for variable in parsed.event_dict if variable.name == 'S1_' + name)
    indexes['S1'] = int(problem.uid2idx_event_params[s1.uid])
    return problem, updater, state, parameters, indexes


def test_ostb2t_switch_observes_minimum_and_maximum_closed_times() -> None:
    """S1 holds through T-ON and releases at T-OFF when no earlier reset applies."""
    problem: EmtProblemTemplate
    updater: BlockProceduralLogicUpdater
    state: np.ndarray
    parameters: np.ndarray
    indexes: dict[str, int]
    problem, updater, state, parameters, indexes = _ostb2t_event_runtime('OSTB2T_TIMERS')
    updater.update(0.0, state, parameters)
    parameters[indexes['ETerminalPu']] = 0.8
    parameters[indexes['SpeedDeviationPu']] = 0.2
    updater.update(0.1, state, parameters)
    assert parameters[indexes['S1']] == pytest.approx(1.0)
    assert updater.get_next_forced_event_time(0.1, 1.0) == pytest.approx(0.3)
    parameters[indexes['SpeedDeviationPu']] = -0.1
    parameters[indexes['EfdPu']] = 0.0
    updater.update(0.2, state, parameters)
    assert parameters[indexes['S1']] == pytest.approx(1.0)
    updater.update(0.3, state, parameters)
    assert parameters[indexes['S1']] == pytest.approx(0.0)

    problem, updater, state, parameters, indexes = _ostb2t_event_runtime('OSTB2T_TIMEOUT')
    updater.update(0.0, state, parameters)
    parameters[indexes['ETerminalPu']] = 0.8
    parameters[indexes['SpeedDeviationPu']] = 0.2
    updater.update(0.1, state, parameters)
    assert parameters[indexes['S1']] == pytest.approx(1.0)
    assert updater.get_next_forced_event_time(0.1, 1.0) == pytest.approx(0.3)
    updater.update(0.3, state, parameters)
    assert parameters[indexes['S1']] == pytest.approx(1.0)
    updater.update(0.9, state, parameters)
    assert parameters[indexes['S1']] == pytest.approx(0.0)


def test_ostb2t_voltage_seal_reopens_only_for_tseal_seconds() -> None:
    """A recent low-voltage event permits speed pickup through the seal window."""
    problem: EmtProblemTemplate
    updater: BlockProceduralLogicUpdater
    state: np.ndarray
    parameters: np.ndarray
    indexes: dict[str, int]
    problem, updater, state, parameters, indexes = _ostb2t_event_runtime('OSTB2T_SEAL')
    updater.update(0.0, state, parameters)
    parameters[indexes['ETerminalPu']] = 0.8
    updater.update(0.05, state, parameters)
    parameters[indexes['ETerminalPu']] = 1.0
    updater.update(0.1, state, parameters)
    parameters[indexes['SpeedDeviationPu']] = 0.2
    updater.update(0.2, state, parameters)
    assert parameters[indexes['S1']] == pytest.approx(1.0)

    problem, updater, state, parameters, indexes = _ostb2t_event_runtime('OSTB2T_SEAL_EXPIRED')
    updater.update(0.0, state, parameters)
    parameters[indexes['ETerminalPu']] = 0.8
    updater.update(0.05, state, parameters)
    parameters[indexes['ETerminalPu']] = 1.0
    updater.update(0.1, state, parameters)
    updater.update(0.4, state, parameters)
    parameters[indexes['SpeedDeviationPu']] = 0.2
    updater.update(0.41, state, parameters)
    assert parameters[indexes['S1']] == pytest.approx(0.0)


def test_ostb2t_has_the_documented_filters_ports_and_switch_logic() -> None:
    """The template retains its four memories and three physical inputs."""
    template = build_ostb2t_template(VarFactory())
    assert template.name == 'OSTB2T'
    assert len(template.block.in_vars) == 3
    assert len(template.block.out_vars) == 1
    assert len(template.block.state_vars) == 4
    assert len(template.block.procedural_logic) == 4
    assert isinstance(template.block.procedural_logic[0], TimedPulseLogic)
    assert isinstance(template.block.procedural_logic[1], TimedPulseLogic)
    assert isinstance(template.block.procedural_logic[2], TimedPulseLogic)
    assert isinstance(template.block.procedural_logic[3], FlipFlopLogic)
    assert template.block.out_vars[0].name.startswith('VOTHSG_')


def test_ostb2t_catalogue_registration_builds_the_native_template() -> None:
    """The standard-model factory exposes OSTB2T to native RMS callers."""
    template = build_international_standard_template(
        InternationalStandardModel.OSTB2T,
        VarFactory(),
    )
    assert template.name == 'OSTB2T'
    assert len(template.block.state_vars) == 4


def test_ostb2t_runtime_logic_round_trips_through_block_codec() -> None:
    """Timed sealing and S1 switching survive template persistence."""
    template = build_ostb2t_template(VarFactory(), 'OSTB2T_PERSIST')
    restored: Block = roundtrip_block(template.block, ProceduralLogicCodec())
    assert len(restored.procedural_logic) == 4
    assert isinstance(restored.procedural_logic[0], TimedPulseLogic)
    assert isinstance(restored.procedural_logic[1], TimedPulseLogic)
    assert isinstance(restored.procedural_logic[2], TimedPulseLogic)
    assert isinstance(restored.procedural_logic[3], FlipFlopLogic)
    assert all(isinstance(value, Const) for value in restored.event_dict.values())


def test_ostb2t_source_record_binds_all_twenty_constants() -> None:
    """The direct DYR binding preserves and applies each ordered source constant."""
    values: str = '1 10 1 .1 1 .1 .1 -.1 1 .1 0 0 .1 1 .1 -.1 0 .9 0 .1'
    record: DyrRecord = parse_dyr("1 'OSTB2T' '01' " + values + ' /', version=35).records[0]
    binding: PsseDynamicBinding | None = dynamic_binding('OSTB2T')
    assert binding is not None
    template: RmsModelTemplate = build_controller(
        record, binding, VarFactory(), 'OSTB2T_SOURCE', 1.0,
    )
    named_values: dict[str, float] = dict(
        (variable.name, value.value)
        for variable, value in template.block.event_dict.items()
        if isinstance(value, Const)
    )
    assert len(binding.parameters) == 20
    assert named_values['K_OSTB2T_SOURCE'] == 1.0
    assert named_values['TS_OSTB2T_SOURCE'] == 10.0
    assert named_values['T1_T3_OSTB2T_SOURCE'] == 1.0
    assert named_values['T3_OSTB2T_SOURCE'] == 0.1
    assert named_values['T2_T4_OSTB2T_SOURCE'] == 1.0
    assert named_values['T4_OSTB2T_SOURCE'] == 0.1
    assert named_values['VNGMX_OSTB2T_SOURCE'] == 0.0
    assert named_values['VMGMX_OSTB2T_SOURCE'] == 0.0
    assert named_values['TSEAL_OSTB2T_SOURCE'] == 0.1


def test_ostb5t_source_times_translate_to_shared_lead_lag_kernel() -> None:
    """OSTB5T converts T1/T2 and T3/T4 to the kernel's numerator/denominator pairs."""
    values: str = '1 10 .4 .05 2 .1 .1 -.1 1 .1 0 0 .1 1 .1 -.1 0 .9 0 .1'
    record: DyrRecord = parse_dyr("1 'OSTB5T' '01' " + values + ' /', version=35).records[0]
    binding: PsseDynamicBinding | None = dynamic_binding('OSTB5T')
    assert binding is not None
    template: RmsModelTemplate = build_controller(
        record, binding, VarFactory(), 'OSTB5T_SOURCE', 1.0,
    )
    named_values: dict[str, float] = dict(
        (variable.name, value.value)
        for variable, value in template.block.event_dict.items()
        if isinstance(value, Const)
    )
    assert binding.standard == InternationalStandardModel.OSTB5T
    assert named_values['T1_T3_OSTB5T_SOURCE'] == pytest.approx(2.0)
    assert named_values['T3_OSTB5T_SOURCE'] == pytest.approx(0.2)
    assert named_values['T2_T4_OSTB5T_SOURCE'] == pytest.approx(0.5)
    assert named_values['T4_OSTB5T_SOURCE'] == pytest.approx(0.1)


def test_ostb2t_zero_tang_removes_only_the_voltage_filter_state() -> None:
    """A zero TANG uses its documented exact static transfer reduction."""
    parameters: Ostb2tParameters = Ostb2tParameters(angle_time=0.0)
    template = build_ostb2t_template(VarFactory(), parameters=parameters)
    assert len(template.block.state_vars) == 3


@pytest.mark.parametrize(
    'parameters',
    (
        Ostb2tParameters(washout_time=0.0),
        Ostb2tParameters(lag1_time=0.0),
        Ostb2tParameters(lag2_time=0.0),
        Ostb2tParameters(angle_gain=0.0),
        Ostb2tParameters(switch_on_time=2.0, switch_off_time=1.0),
        Ostb2tParameters(lower_speed=0.2, upper_speed=0.1),
        Ostb2tParameters(output_min=0.1, output_max=-0.1),
    ),
)
def test_ostb2t_rejects_invalid_physical_and_switch_settings(
        parameters: Ostb2tParameters,
) -> None:
    """Invalid filter, output and timer contracts fail before graph assembly."""
    with pytest.raises(ValueError):
        build_ostb2t_template(VarFactory(), parameters=parameters)
