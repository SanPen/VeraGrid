# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Check native TGOV2 state and absolute fast-valving boundaries."""

import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Rms.governors.tgov2 import (
    TGOV2Parameters,
    build_tgov2_template,
)
from VeraGridEngine.Utils.procedural_logic import (
    BlockProceduralLogicUpdater,
    ProceduralLogicCodec,
    StartupHandoverLogic,
    build_boundary_updater_from_block,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block


def test_tgov2_builds_four_states_and_configurable_ti() -> None:
    """Keep the documented state, input, and timing contract visible.

    :return: None.
    """
    template = build_tgov2_template(VarFactory())

    assert len(template.block.state_vars) == 4
    assert len(template.block.state_eqs) == 4
    assert tuple(variable.name for variable in template.block.state_vars) == (
        'TGOV2ThrottlePu_TGOV2',
        'TGOV2ReheatPressurePu_TGOV2',
        'TGOV2ReheatPowerPu_TGOV2',
        'TGOV2InterceptValvePu_TGOV2',
    )
    assert tuple(variable.name for variable in template.block.in_vars) == (
        'SpeedReferencePu_TGOV2', 'SpeedDeviationPu_TGOV2',
    )
    assert template.block.event_dict[next(
        variable for variable in template.block.event_dict
        if variable.name == 'FastValvingStartTimeSec_TGOV2'
    )].value == 0.0
    assert len(template.block.procedural_logic) == 4
    assert all(isinstance(logic, StartupHandoverLogic) for logic in template.block.procedural_logic)
    assert tuple(variable.name for variable in template.block.out_vars) == ('gov.PmPu_TGOV2',)


def test_tgov2_valve_schedule_switches_at_ti_relative_boundaries() -> None:
    """Apply each retained fast-valving boundary at its exact PSS/E time.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    template = build_tgov2_template(vf, parameters=TGOV2Parameters(ta=0.1, tb=0.2, tc=0.4))
    runtime_block: Block = roundtrip_block(template.block, ProceduralLogicCodec())
    problem: Tgov2Problem = Tgov2Problem(
        sys_block=runtime_block,
        glob_time=vf.add_var('Tgov2GlobalTime'),
        static_parameter_values_mapping=dict(),
    )
    updater: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(problem)
    assert updater is not None
    state: np.ndarray = problem.get_x0().copy()
    params: np.ndarray = problem.event_params_values.copy()
    modes: tuple[int, ...] = tuple(
        problem.uid2idx_event_params[variable.uid] for variable in runtime_block.mode_dict
    )

    updater.update(0.0, state, params)
    assert tuple(params[index] for index in modes) == (1.0, 0.0, 0.0, 0.0)
    assert updater.get_next_forced_event_time(0.0, 0.5) == 0.1
    updater.update(0.1, state, params)
    assert tuple(params[index] for index in modes) == (1.0, 1.0, 0.0, 0.0)
    assert updater.get_next_forced_event_time(0.1, 0.5) == 0.2
    updater.update(0.2, state, params)
    assert tuple(params[index] for index in modes) == (1.0, 1.0, 1.0, 0.0)
    assert updater.get_next_forced_event_time(0.2, 0.5) == 0.4
    updater.update(0.4, state, params)
    assert tuple(params[index] for index in modes) == (1.0, 1.0, 1.0, 1.0)


class Tgov2Problem(EmtProblemTemplate):
    """Use the standard DAE variable maps for TGOV2 procedural boundaries."""

    __slots__ = ()


def test_tgov2_rejects_invalid_fast_valving_order() -> None:
    """Reject a schedule whose reopen interval is not ordered.

    :return: None.
    """
    parameters: TGOV2Parameters = TGOV2Parameters(ta=0.6, tb=0.5, tc=1.0)

    try:
        build_tgov2_template(VarFactory(), parameters=parameters)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid TGOV2 fast-valving times were accepted')
