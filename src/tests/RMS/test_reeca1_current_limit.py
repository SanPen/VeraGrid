# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Voltage-dependent current-limit checks for the REECA1 controller component."""


import math

import numpy as np
import pytest

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Rms.renewable_controls.reeca1_current_limit import (
    Reeca1CurrentLimitSettings,
    Reeca1CurrentPriority,
    build_reeca1_current_limit_template,
    reeca1_curve_from_source_pairs,
)
from VeraGridEngine.Templates.Rms.renewable_controls.renewable_partial_chain import build_renewable_partial_chain
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var, get_expression_vars
from VeraGridEngine.Utils.procedural_logic import (
    BlockProceduralLogicUpdater, ProceduralLogicCodec,
    build_boundary_updater_from_block,
)

from tests.symbolic_block_roundtrip import roundtrip_block


def _limited_currents(block: Block, voltage: float, ip_order: float, iq_order: float,
                      fault: float = 0., held_cap: float = 0., hold: float = 0.) -> tuple[float, float]:
    """Evaluate both explicit current-limit residuals at one operating point.

    :param block: Stand-alone current-limit controller.
    :param voltage: Live terminal voltage in per unit.
    :param ip_order: Active current order in per unit.
    :param iq_order: Reactive current order in per unit.
    :param fault: Live voltage-fault flag when Thld2 is enabled.
    :param held_cap: Stored faulted active-current ceiling.
    :param hold: Timed active-current hold state.
    :return: Limited active and reactive current commands.
    """
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = voltage
    bindings[block.in_vars[1].uid] = ip_order
    bindings[block.in_vars[2].uid] = iq_order
    if len(block.in_vars) > 3:
        bindings[block.in_vars[3].uid] = fault
    else:
        pass
    mode: Var
    for mode in block.mode_dict:
        if mode.name.startswith('HeldFaultIpmaxPu_'):
            bindings[mode.uid] = held_cap
        else:
            bindings[mode.uid] = hold
    bindings[block.out_vars[0].uid] = 0.
    bindings[block.out_vars[1].uid] = 0.
    ip_limited: float = -float(block.algebraic_eqs[0].eval_uid(bindings))
    iq_limited: float = -float(block.algebraic_eqs[1].eval_uid(bindings))
    return ip_limited, iq_limited


class ActiveLimitProblem(EmtProblemTemplate):
    """Bind the actual Thld2 procedures to minimal current-limit inputs."""

    __slots__ = ()


def test_reeca1_thld2_retains_faulted_ipmax_until_timer_expiry() -> None:
    """Hold the sampled current ceiling through clearance, then release it.

    :return: None.
    """
    vf: VarFactory = VarFactory()
    block: Block = build_reeca1_current_limit_template(
        vf=vf, settings=Reeca1CurrentLimitSettings(
            imax=1., thld2=.2,
            reactive_curve=((.2, 1.), (1.2, 1.)),
            active_curve=((.2, .2), (1.2, 1.)),
        ),
    ).block
    assert len(block.procedural_logic) == 2
    assert _limited_currents(block, 1., 1., 0., held_cap=.36, hold=1.)[0] == pytest.approx(.36)
    assert _limited_currents(block, 1., 1., 0., held_cap=.36, hold=1., fault=1.)[0] == pytest.approx(.84)
    assert _limited_currents(block, 1., 1., 0., held_cap=.36, hold=0.)[0] == pytest.approx(.84)
    inputs: list[Var] = list((block.in_vars[0], block.in_vars[2], block.in_vars[3]))
    runtime_block: Block = Block(
        name='REECA1 active-current recovery runtime',
        state_vars=inputs,
        diff_vars=list((vf.add_diff_var('d_LimitVoltage', base_var=inputs[0]),
                        vf.add_diff_var('d_LimitReactiveCommand', base_var=inputs[1]),
                        vf.add_diff_var('d_LimitFault', base_var=inputs[2]))),
        state_eqs=list((Const(0.), Const(0.), Const(0.))),
        init_eqs=dict(((inputs[0], Const(1.)), (inputs[1], Const(0.)),
                       (inputs[2], Const(0.)))),
        event_dict=block.event_dict, mode_dict=block.mode_dict,
        procedural_logic=block.procedural_logic,
    )
    restored: Block = roundtrip_block(runtime_block, procedural_logic_codec=ProceduralLogicCodec())
    problem: ActiveLimitProblem = ActiveLimitProblem(
        sys_block=restored, glob_time=vf.add_var('LimitTime'),
        static_parameter_values_mapping=dict(),
    )
    updater: BlockProceduralLogicUpdater | None = build_boundary_updater_from_block(problem)
    assert updater is not None
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    voltage_index: int = problem.get_var_idx(inputs[0])
    fault_index: int = problem.get_var_idx(inputs[2])
    stored_mode: Var = next(mode for mode in block.mode_dict
                            if mode.name.startswith('HeldFaultIpmaxPu_'))
    hold_mode: Var = next(mode for mode in block.mode_dict
                          if mode.name.startswith('ActiveLimitRecoveryHold_'))
    stored_index: int = problem.uid2idx_event_params[stored_mode.uid]
    hold_index: int = problem.uid2idx_event_params[hold_mode.uid]
    updater.update(0., state, parameters)
    state[voltage_index] = .4
    state[fault_index] = 1.
    updater.update(.1, state, parameters)
    assert parameters[stored_index] == pytest.approx(.36)
    assert parameters[hold_index] == pytest.approx(1.)
    state[voltage_index] = 1.
    state[fault_index] = 0.
    updater.update(.15, state, parameters)
    assert parameters[stored_index] == pytest.approx(.36)
    assert updater.get_next_forced_event_time(.15, .5) == pytest.approx(.35)
    updater.update(.35, state, parameters)
    assert parameters[hold_index] == pytest.approx(0.)
    with pytest.raises(ValueError, match='voltage-fault settings'):
        build_renewable_partial_chain(
            vf=VarFactory(),
            current_limit_settings=Reeca1CurrentLimitSettings(thld2=.2),
        )
    with pytest.raises(ValueError, match='hold time'):
        build_reeca1_current_limit_template(
            vf=VarFactory(), settings=Reeca1CurrentLimitSettings(thld2=-.1),
        )


def test_reeca1_priority_reserves_the_selected_current_channel() -> None:
    """Reserve Q or P first, then give the other the remaining current circle.

    :return: None.
    """
    flat: tuple[tuple[float, float], ...] = ((.2, 1.), (1.2, 1.))
    q_block: Block = build_reeca1_current_limit_template(
        vf=VarFactory(),
        settings=Reeca1CurrentLimitSettings(
            imax=1., reactive_curve=flat, active_curve=flat,
            priority=Reeca1CurrentPriority.REACTIVE,
        ),
    ).block
    p_block: Block = build_reeca1_current_limit_template(
        vf=VarFactory(),
        settings=Reeca1CurrentLimitSettings(
            imax=1., reactive_curve=flat, active_curve=flat,
            priority=Reeca1CurrentPriority.ACTIVE,
        ),
    ).block
    q_ip: float
    q_iq: float
    p_ip: float
    p_iq: float
    q_ip, q_iq = _limited_currents(q_block, 1., .8, .9)
    p_ip, p_iq = _limited_currents(p_block, 1., .8, .9)
    assert q_iq == pytest.approx(.9)
    assert q_ip == pytest.approx(math.sqrt(1. - .9 * .9))
    assert p_ip == pytest.approx(.8)
    assert p_iq == pytest.approx(.6)
    assert q_ip * q_ip + q_iq * q_iq <= 1. + 1e-12
    assert p_ip * p_ip + p_iq * p_iq <= 1. + 1e-12


def test_reeca1_priority_uses_source_command_for_other_channel_capability() -> None:
    """Keep Appendix B's raw-command dependence when VDL clips priority current.

    :return: None.
    """
    flat: tuple[tuple[float, float], ...] = ((.2, 1.), (1.2, 1.))
    narrow: tuple[tuple[float, float], ...] = ((.2, .5), (1.2, .5))
    q_block: Block = build_reeca1_current_limit_template(
        vf=VarFactory(), settings=Reeca1CurrentLimitSettings(
            imax=1., reactive_curve=narrow, active_curve=flat,
            priority=Reeca1CurrentPriority.REACTIVE,
        ),
    ).block
    p_block: Block = build_reeca1_current_limit_template(
        vf=VarFactory(), settings=Reeca1CurrentLimitSettings(
            imax=1., reactive_curve=flat, active_curve=narrow,
            priority=Reeca1CurrentPriority.ACTIVE,
        ),
    ).block
    q_ip: float
    q_iq: float
    p_ip: float
    p_iq: float
    q_ip, q_iq = _limited_currents(q_block, 1., 1., .9)
    p_ip, p_iq = _limited_currents(p_block, 1., .9, 1.)
    assert q_iq == pytest.approx(.5)
    assert q_ip == pytest.approx(math.sqrt(1. - .9 * .9))
    assert p_ip == pytest.approx(.5)
    assert p_iq == pytest.approx(math.sqrt(1. - .9 * .9))
    assert q_block.out_vars[2].name.startswith('ReactiveCapabilityPu_')


def test_reeca1_vdl_interpolates_and_holds_endpoint_currents() -> None:
    """Preserve four-point source interpolation and low/high endpoint behavior.

    :return: None.
    """
    reactive: tuple[tuple[float, float], ...] = (
        (.2, .1), (.4, .3), (.8, .7), (1.2, 1.1),
    )
    active: tuple[tuple[float, float], ...] = ((.2, 1.2), (1.2, 1.2))
    block: Block = build_reeca1_current_limit_template(
        vf=VarFactory(),
        settings=Reeca1CurrentLimitSettings(
            imax=1., reactive_curve=reactive, active_curve=active,
        ),
    ).block
    assert _limited_currents(block, .1, 0., .9)[1] == pytest.approx(.1)
    assert _limited_currents(block, .6, 0., .9)[1] == pytest.approx(.5)
    assert _limited_currents(block, 1.3, 0., .9)[1] == pytest.approx(.9)
    assert _limited_currents(block, .6, .8, -.9)[1] == pytest.approx(-.5)


def test_reeca1_vdl_allows_descending_current_segments() -> None:
    """Interpolate a source VDL whose current decreases as voltage rises.

    :return: None.
    """
    reactive: tuple[tuple[float, float], ...] = ((.2, 1.), (.6, .4), (1.2, .2))
    flat: tuple[tuple[float, float], ...] = ((.2, 1.2), (1.2, 1.2))
    block: Block = build_reeca1_current_limit_template(
        vf=VarFactory(), settings=Reeca1CurrentLimitSettings(
            imax=1.2, reactive_curve=reactive, active_curve=flat,
        ),
    ).block
    assert _limited_currents(block, .4, 0., 1.)[1] == pytest.approx(.7)
    assert _limited_currents(block, .9, 0., 1.)[1] == pytest.approx(.3)


def test_reeca1_vdl_reads_filtered_voltage_when_trv_is_positive() -> None:
    """Keep a voltage dip out of the VDL tables until the sensor responds.

    :return: None.
    """
    reactive: tuple[tuple[float, float], ...] = ((.2, .1), (1., 1.))
    block: Block = build_reeca1_current_limit_template(
        vf=VarFactory(),
        settings=Reeca1CurrentLimitSettings(trv=.05, reactive_curve=reactive),
    ).block
    filtered: Var = block.state_vars[0]
    bindings: dict[int, float] = dict()
    parameter: Var
    value: Expr
    for parameter, value in block.event_dict.items():
        if isinstance(value, Const):
            bindings[parameter.uid] = float(value.value)
        else:
            pass
    bindings[block.in_vars[0].uid] = .2
    bindings[block.in_vars[1].uid] = 0.
    bindings[block.in_vars[2].uid] = .9
    bindings[filtered.uid] = 1.
    bindings[block.out_vars[1].uid] = 0.
    assert block.state_eqs[0].eval_uid(bindings) == pytest.approx(-16.)
    assert -block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(.9)
    bindings[filtered.uid] = .2
    assert -block.algebraic_eqs[1].eval_uid(bindings) == pytest.approx(.1)
    assert filtered in get_expression_vars(block.algebraic_eqs[1])
    assert block.in_vars[0] not in get_expression_vars(block.algebraic_eqs[1])
    with pytest.raises(ValueError, match='voltage measurement time'):
        build_reeca1_current_limit_template(
            vf=VarFactory(), settings=Reeca1CurrentLimitSettings(trv=-.01),
        )


def test_reeca1_current_limits_reject_invalid_source_curves() -> None:
    """Reject missing mandatory pairs and ambiguous curve termination/order.

    :return: None.
    """
    bad_curves: tuple[tuple[tuple[float, float], ...], ...] = (
        ((.2, .1),),
        ((.2, .1), (.2, .3)),
        ((.4, .3), (.2, .1)),
        ((.2, -.1), (.4, .3)),
        ((.2, .1), (.4, .3), (0., 0.)),
    )
    bad: tuple[tuple[float, float], ...]
    for bad in bad_curves:
        with pytest.raises(ValueError, match='curve'):
            build_reeca1_current_limit_template(
                vf=VarFactory(),
                settings=Reeca1CurrentLimitSettings(reactive_curve=bad),
            )


def test_reeca1_source_curve_uses_zero_voltage_terminator() -> None:
    """Accept two mandatory points and reject data after a zero pair.

    :return: None.
    """
    supplied: tuple[tuple[float, float], ...] = (
        (.2, 0.), (.8, 1.), (0., 0.), (0., 0.),
    )
    assert reeca1_curve_from_source_pairs(supplied) == supplied[:2]
    with pytest.raises(ValueError, match='after its zero terminator'):
        reeca1_curve_from_source_pairs((
            (.2, 0.), (.8, 1.), (0., 0.), (1.2, 1.1),
        ))
