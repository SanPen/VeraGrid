# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Version-specific four-phase and quadratic dual-input stabilizer conversion contracts."""
from __future__ import annotations

import pytest
from VeraGridEngine.IO.raw.dyr_parser import parse_dyr
from VeraGridEngine.IO.raw.dyr_to_veragrid import validate_dynamic_parameters
from VeraGridEngine.IO.raw.raw_to_veragrid import psse_to_veragrid
from VeraGridEngine.IO.raw.versioned.base.auxiliary import RecordStatus
from VeraGridEngine.IO.raw.versioned.base.dyr import DyrRecord
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Utils.procedural_logic import BlockProceduralLogicUpdater, build_boundary_updater_from_block
from VeraGridEngine.api import power_flow
from VeraGridEngine.basic_structures import Logger
from tests.FileFormats.PSSe.test_psse_auxiliary_conversion import (
    make_raw_case, test_adapter_initializes_at_a_real_power_flow_equilibrium as check_equilibrium,
)


def additional_stabilizer_record(model: str, bypass: bool = False) -> str:
    """Build the exact source ICON/CON contract for the added physical structure.

    :param model: Four-phase ramp-tracking or quadratic dual-input identity.
    :param bypass: Bypass all channel dynamics for the quadratic family.
    :return: Complete source assignment.
    """
    if model == 'PSS2C':
        return "1 'PSS2C' '01' 1 0 3 0 2 2 3 0 .02 4 0 .03 .4 .7 .1 .2 5 .2 .05 .1 .03 .04 .02 2 -2 2 -2 .1 -.1 .08 .04 -1 0 0 .1 /"
    else:
        times: str = '0 0' if bypass else '.02 10'
        second_times: str = '0 0 0' if bypass else '.03 12 .5'
        return "1 'PSS3B' '01' 1 0 3 0 1 "+times+' -.5 '+second_times+' .1 .01 .2 .02 .1 .01 .2 .02 .1 -.1 /'


@pytest.mark.parametrize('model',('PSS2C','PSS3B'))
@pytest.mark.parametrize('version',(33,34,35,36))
def test_added_stabilizer_profile_contracts(model: str, version: int) -> None:
    """The new four-phase source layout is release-owned while the quadratic layout matches both supplied snapshots.

    :param model: Exact source identifier.
    :param version: Parser release profile.
    """
    record: DyrRecord = parse_dyr(additional_stabilizer_record(model),version=version).records[0]
    if model == 'PSS2C' and version in (33,34):
        assert record.status == RecordStatus.UNSUPPORTED
    else:
        assert record.status == RecordStatus.VALID
        assert len(record.parameters) == (29 if model == 'PSS2C' else 17)
        assert len(record.icons) == (6 if model == 'PSS2C' else 4)


@pytest.mark.parametrize('model,version,bypass',(('PSS2C',35,False),('PSS2C',36,False),
    ('PSS3B',33,False),('PSS3B',34,False),('PSS3B',35,False),('PSS3B',36,False),('PSS3B',35,True)))
@pytest.mark.parametrize('runtime',(False,True))
def test_added_stabilizer_machine_equilibrium(model: str, version: int, bypass: bool, runtime: bool) -> None:
    """Selected speed/power measurements initialize both stored/runtime paths, including nonzero fully bypassed bias.

    :param model: Exact source stabilizer identifier.
    :param version: Reviewed source profile.
    :param bypass: Remove optional quadratic-family channel memories.
    :param runtime: Inspect runtime duplication or stored graph.
    """
    controller: str = "1 'SEXS' '01' .1 1 20 .05 0 5 /\n"+additional_stabilizer_record(model,bypass)
    check_equilibrium('GENROU','8 .03 .4 .05 4 0 1.8 1.7 .3 .55 .2 .15 .08 .3',controller,runtime,version=version)


@pytest.mark.parametrize('pss_on,pss_off',((-1.,0.),(0.,0.),(.1,.05)))
def test_pss2c_power_logic_threshold_contract(pss_on: float, pss_off: float) -> None:
    """PSS/E's signed PSSON switch distinguishes bypass from active hysteresis.

    :param pss_on: Machine-base power activation threshold or negative bypass.
    :param pss_off: Machine-base power deactivation threshold.
    """
    source: str = additional_stabilizer_record('PSS2C').replace(
        ' -1 0 0 .1 /',f' {pss_on} {pss_off} 0 .1 /')
    record: DyrRecord = parse_dyr(source,version=35).records[0]
    validate_dynamic_parameters(record)


def test_pss2c_power_logic_requires_ordered_thresholds() -> None:
    """An enabled hysteresis must switch on above its switch-off threshold."""
    source: str = additional_stabilizer_record('PSS2C').replace(
        ' -1 0 0 .1 /',' .05 .1 0 .1 /')
    record: DyrRecord = parse_dyr(source,version=35).records[0]
    with pytest.raises(ValueError,match='PSSON'):
        validate_dynamic_parameters(record)


def test_pss2c_active_power_hysteresis_initializes_with_machine_base_power() -> None:
    """The enabled PSS2C path connects the source-machine-base power signal."""
    controller: str = "1 'SEXS' '01' .1 1 20 .05 0 5 /\n"+additional_stabilizer_record('PSS2C').replace(
        ' -1 0 0 .1 /',' .08 .04 0 .1 /')
    check_equilibrium('GENROU','8 .03 .4 .05 4 0 1.8 1.7 .3 .55 .2 .15 .08 .3',
                      controller,False,version=35)


def test_pss2c_connected_power_hysteresis_runtime_transitions() -> None:
    """Compile and execute the PSS2C latch against a connected RMS DAE signal."""
    case = make_raw_case()
    controller: str = "1 'GENROU' '01' 8 .03 .4 .05 4 0 1.8 1.7 .3 .55 .2 .15 .08 .3 /\n"
    controller += "1 'EXST1' '01' .02 .2 -.2 1 5 20 .02 5 -5 .01 .1 1 /\n"
    controller += additional_stabilizer_record('PSS2C').replace(
        ' -1 0 0 .1 /',' .08 .04 0 .1 /')
    assert case.add_auxiliary(parse_dyr(controller,version=35))
    grid = psse_to_veragrid(case,logger=Logger())
    power_flow_results = power_flow(grid=grid)
    assert power_flow_results.converged
    problem: RmsProblemDae = RmsProblemDae(grid=grid,options=RmsOptions(),pf_results=power_flow_results)
    problem.set_events_group(rms_events_group=RmsEventsGroup())
    updater: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(problem)
    assert updater is not None
    power = next(variable for block in problem.sys_block.get_all_blocks()
                 for variable in block.in_vars if variable.name.startswith('GeneratorActivePowerPu_'))
    enabled = next(variable for block in problem.sys_block.get_all_blocks()
                   for variable in block.mode_dict if variable.name.startswith('PssOutputEnabled_'))
    state = problem.get_x0().copy()
    parameters = problem.get_eventparams0().copy()
    power_index: int = problem.get_var_idx(power)
    enabled_index: int = problem.uid2idx_event_params[enabled.uid]
    for time, value, expected in ((0.,.09,1.),(.1,.06,1.),(.2,.03,0.),(.3,.06,0.),(.4,.09,1.)):
        state[power_index] = value
        updater.update(time,state,parameters)
        assert parameters[enabled_index] == expected
