# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Verify TGOV4 valve flow characteristics, position, and rate limits."""

from __future__ import annotations

import pytest
import numpy as np

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Simulations.EMT.problems.emt_problem_template import EmtProblemTemplate
from VeraGridEngine.Templates.Rms import build_international_standard_template
from VeraGridEngine.enumerations import InternationalStandardModel
from VeraGridEngine.Templates.Rms.governors.tgov4 import (
    Tgov4SteamSettings,
    Tgov4BoilerSettings,
    Tgov4GovernorSettings,
    Tgov4RelaySettings,
    Tgov4ValveSettings,
    build_tgov4_valve_bank,
    build_tgov4_steam_train,
    build_tgov4_boiler,
    build_tgov4_thermal_train,
    build_tgov4_speed_control,
    build_tgov4_relay_monitors,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from tests.symbolic_block_roundtrip import roundtrip_block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import (
    PickupDropoffLogic,
    ProceduralLogicCodec,
    build_boundary_updater_from_block,
)


def parameter_values(block: Block) -> dict[int, float]:
    """Bind declared valve parameters to their explicit construction values.

    :param block: Valve block whose parameters are constant event expressions.
    :return: Symbol UID to numeric parameter mapping.
    """
    values: dict[int, float] = dict()
    for parameter, expression in block.event_dict.items():
        if isinstance(expression, Const):
            values[parameter.uid] = float(expression.value)
        else:
            pass
    for variable, expression in block.init_eqs.items():
        if isinstance(expression, Const):
            values[variable.uid] = float(expression.value)
        else:
            pass
    return values


def test_tgov4_linear_valve_maps_position_to_flow_and_clips_servo_rate() -> None:
    """Keep linear valve flow equal to position and apply UO/UC velocity stops.

    :return: None.
    """
    template = build_tgov4_valve_bank(
        VarFactory(), 'tgov4_cv1',
        (Tgov4ValveSettings(
            time_constant=.1, opening_rate=.2, closing_rate=-.3,
            initial_position=.8,
        ),),
    )
    block: Block = template.block
    position: Var = block.state_vars[0]
    demand: Var = block.in_vars[0]

    assert len(block.state_vars) == 1
    assert block.out_vars[0].name == 'FlowAreaPu_tgov4_cv1'
    assert block.algebraic_eqs[0].right.eval_uid({position.uid: .45}) == pytest.approx(.45)

    opening_values: dict[int, float] = parameter_values(block)
    opening_values[position.uid] = .8
    opening_values[demand.uid] = 1.0
    assert block.state_eqs[0].eval_uid(opening_values) == pytest.approx(.2)

    closing_values: dict[int, float] = parameter_values(block)
    closing_values[position.uid] = .8
    closing_values[demand.uid] = 0.0
    assert block.state_eqs[0].eval_uid(closing_values) == pytest.approx(-.3)

    upper_stop_values: dict[int, float] = parameter_values(block)
    upper_stop_values[position.uid] = 1.0
    upper_stop_values[demand.uid] = 2.0
    assert block.state_eqs[0].eval_uid(upper_stop_values) == pytest.approx(0.0)

    lower_stop_values: dict[int, float] = parameter_values(block)
    lower_stop_values[position.uid] = 0.0
    lower_stop_values[demand.uid] = -1.0
    assert block.state_eqs[0].eval_uid(lower_stop_values) == pytest.approx(0.0)


def test_tgov4_plu_eva_washouts_and_unbalance_polarity() -> None:
    """Match relay washout and summed-unbalance directions from the source figure.

    :return: None.
    """
    block: Block = build_tgov4_relay_monitors(
        VarFactory(), 'tgov4_relay_monitors',
        Tgov4RelaySettings(
            tr_plu=2.0, tr_eva=4.0, initial_generator_current=.5,
            initial_generator_power=.3, initial_reheat_pressure=.3,
        ),
    ).block
    values: dict[int, float] = parameter_values(block)
    values[block.in_vars[0].uid] = .7
    values[block.in_vars[1].uid] = .4
    values[block.in_vars[2].uid] = .6
    current_filter: Var = block.state_vars[0]
    power_filter: Var = block.state_vars[1]
    values[current_filter.uid] = .5
    values[power_filter.uid] = .3

    assert block.state_eqs[0].eval_uid(values) == pytest.approx(.1)
    assert block.state_eqs[1].eval_uid(values) == pytest.approx(.025)
    assert [equation.right.eval_uid(values) for equation in block.algebraic_eqs[:4]] == pytest.approx(
        [.2, .1, -.1, .2],
    )


def test_tgov4_eva_thresholds_generate_intercept_valve_monitor() -> None:
    """Require washout EVA rate and unbalance pickups for the monitor.

    :return: None.
    """
    block: Block = build_tgov4_relay_monitors(
        VarFactory(), 'tgov4_eva_action',
        Tgov4RelaySettings(
            tr_plu=2.0, tr_eva=4.0, initial_generator_current=.1,
            initial_generator_power=.2, initial_reheat_pressure=.2,
            eva_rate_level=.1, eva_unbalance_level=.1,
        ),
    ).block
    values: dict[int, float] = parameter_values(block)
    values[block.in_vars[0].uid] = .3
    values[block.in_vars[1].uid] = .4
    values[block.in_vars[2].uid] = .6
    values[block.state_vars[0].uid] = .1
    values[block.state_vars[1].uid] = .2
    values[block.algebraic_vars[0].uid] = .2
    values[block.algebraic_vars[1].uid] = .2
    values[block.algebraic_vars[2].uid] = .3
    values[block.algebraic_vars[3].uid] = .2

    assert block.algebraic_eqs[5].right.eval_uid(values) == pytest.approx(1.0)
    values[block.algebraic_vars[5].uid] = 1.0
    assert block.algebraic_eqs[6].right.eval_uid(values) == pytest.approx(1.0)


@pytest.mark.parametrize('mode', (0, 2))
def test_tgov4_relay_modes_gate_eva_monitor(mode: int) -> None:
    """Disable the EVA monitor in mode 0 and PLU-only mode 2.

    :param mode: PSS/E relay mode under test.
    :return: None.
    """
    block: Block = build_tgov4_relay_monitors(
        VarFactory(), 'tgov4_mode_' + str(mode),
        Tgov4RelaySettings(
            initial_generator_current=.1, initial_generator_power=.2,
            initial_reheat_pressure=.2, mode=mode,
        ),
    ).block
    values: dict[int, float] = parameter_values(block)
    values[block.in_vars[0].uid] = .3
    values[block.in_vars[1].uid] = .4
    values[block.in_vars[2].uid] = .6
    values[block.state_vars[0].uid] = .1
    values[block.state_vars[1].uid] = .2
    values[block.algebraic_vars[0].uid] = .2
    values[block.algebraic_vars[1].uid] = .2
    values[block.algebraic_vars[2].uid] = .3
    values[block.algebraic_vars[3].uid] = .2

    assert block.algebraic_eqs[6].right.eval_uid(values) == pytest.approx(0.0)


def test_tgov4_mode_one_requires_unimplemented_external_switching() -> None:
    """Reject user-controlled relay mode until its external status inputs exist.

    :return: None.
    """
    with pytest.raises(ValueError):
        build_tgov4_relay_monitors(
            VarFactory(), 'tgov4_mode_one', Tgov4RelaySettings(mode=1),
        )


def test_tgov4_plu_timer_cancels_on_dropout_and_latches_until_unbalance_clears() -> None:
    """Require continuous PLU rate pickup before the unbalance latch can set.

    :return: None.
    """
    factory: VarFactory = VarFactory()
    block: Block = build_tgov4_relay_monitors(
        factory, 'tgov4_continuous_plu_timer',
        Tgov4RelaySettings(
            initial_generator_current=.5, initial_generator_power=.5,
            initial_reheat_pressure=.5, plu_rate_level=.1, plu_timer=.2,
            plu_unbalance_level=.1, mode=2,
        ),
    ).block
    for port in tuple(block.in_vars):
        block.in_vars.remove(port)
        block.init_eqs.pop(port, None)
        block.event_dict[port] = factory.add_const(.5)
    parsed: Block = roundtrip_block(block, ProceduralLogicCodec())
    problem: EmtProblemTemplate = EmtProblemTemplate(
        sys_block=parsed, glob_time=factory.add_var('tgov4_continuous_timer_time'),
        static_parameter_values_mapping=dict(),
    )
    updater = build_boundary_updater_from_block(problem)
    assert updater is not None
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    rate: Var = next(
        variable for variable in parsed.algebraic_vars
        if variable.name.startswith('PLURateSignalPu_')
    )
    unbalance: Var = next(
        variable for variable in parsed.algebraic_vars
        if variable.name.startswith('PLUUnbalancePu_')
    )
    timer_ready: Var = next(
        variable for variable in parsed.event_dict
        if variable.name.startswith('PLURateTimerReady_')
    )
    latch: Var = next(
        variable for variable in parsed.event_dict
        if variable.name.startswith('PLUValveCloseLatch_')
    )
    rate_index: int = problem.get_var_idx(rate)
    unbalance_index: int = problem.get_var_idx(unbalance)
    timer_index: int = int(problem.uid2idx_event_params[timer_ready.uid])
    latch_index: int = int(problem.uid2idx_event_params[latch.uid])

    state[rate_index] = .2
    state[unbalance_index] = .2
    updater.update(0.0, state, parameters)
    state[rate_index] = 0.0
    updater.update(.05, state, parameters)
    assert parameters[timer_index] == pytest.approx(0.0)
    state[rate_index] = .2
    updater.update(.1, state, parameters)
    assert updater.get_next_forced_event_time(.1, .4) == pytest.approx(.3)
    assert parameters[timer_index] == pytest.approx(0.0)
    updater.update(.299, state, parameters)
    assert parameters[latch_index] == pytest.approx(0.0)
    updater.update(.3, state, parameters)
    assert parameters[timer_index] == pytest.approx(1.0)
    assert parameters[latch_index] == pytest.approx(1.0)
    state[unbalance_index] = 0.0
    updater.update(.26, state, parameters)
    assert parameters[latch_index] == pytest.approx(0.0)


@pytest.mark.parametrize(
    'settings',
    (
        Tgov4RelaySettings(tr_plu=0.0),
        Tgov4RelaySettings(tr_eva=-1.0),
        Tgov4RelaySettings(plu_timer=-0.1),
        Tgov4RelaySettings(initial_generator_power=float('nan')),
    ),
)
def test_tgov4_plu_eva_reject_invalid_filter_settings(
        settings: Tgov4RelaySettings,
) -> None:
    """Reject relay filter times and solved measurements outside their domains.

    :param settings: Invalid relay settings for one focused validation case.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_tgov4_relay_monitors(VarFactory(), 'invalid_tgov4_relays', settings)


@pytest.mark.parametrize(
    'settings',
    (
        Tgov4ValveSettings(time_constant=0.0),
        Tgov4ValveSettings(opening_rate=0.0),
        Tgov4ValveSettings(closing_rate=0.0),
        Tgov4ValveSettings(initial_position=1.1),
        Tgov4ValveSettings(position_at_80_percent_flow=0.1),
    ),
)
def test_tgov4_linear_valve_rejects_invalid_source_settings(
        settings: Tgov4LinearValveSettings,
) -> None:
    """Reject invalid source actuator times, rates, and position states.

    :param settings: Deliberately invalid TGOV4 valve settings.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_tgov4_valve_bank(VarFactory(), 'invalid_tgov4_valve', (settings,))


def test_tgov4_nonlinear_valve_matches_source_eighty_percent_point() -> None:
    """Match both published calibration points for a nonlinear valve.

    :return: None.
    """
    template = build_tgov4_valve_bank(
        VarFactory(), 'tgov4_nonlinear',
        (Tgov4ValveSettings(
            initial_position=.3, position_at_80_percent_flow=.3,
            demand_position_at_80_percent_signal=.3,
        ),),
        initial_control_signal=.8,
    )
    block: Block = template.block
    position: Var = block.state_vars[0]
    flow: Expr = block.algebraic_eqs[0].right

    assert flow.eval_uid({position.uid: .3}) == pytest.approx(.8)
    assert flow.eval_uid({position.uid: 1.0}) == pytest.approx(1.0)

    signal: Var = block.in_vars[0]
    values: dict[int, float] = parameter_values(block)
    values[position.uid] = .3
    values[signal.uid] = .8
    assert block.state_eqs[0].eval_uid(values) == pytest.approx(0.0, abs=1e-12)


def test_tgov4_valve_demand_curve_applies_source_offset() -> None:
    """Apply the nonlinear demand calibration after its control offset.

    :return: None.
    """
    template = build_tgov4_valve_bank(
        VarFactory(), 'tgov4_offset',
        (
            Tgov4ValveSettings(initial_position=1.0),
            Tgov4ValveSettings(
                initial_position=.3, demand_position_at_80_percent_signal=.3,
                demand_offset=.5,
            ),
        ),
        initial_control_signal=1.3,
    )
    block: Block = template.block
    position: Var = block.state_vars[1]
    signal: Var = block.in_vars[0]
    values: dict[int, float] = parameter_values(block)
    values[position.uid] = .3
    values[signal.uid] = 1.3

    assert block.state_eqs[1].eval_uid(values) == pytest.approx(0.0, abs=1e-12)


def test_tgov4_valve_bank_normalizes_aggregate_offset_flow() -> None:
    """Normalize staggered linear valves to unit aggregate full-signal flow.

    :return: None.
    """
    template = build_tgov4_valve_bank(
        VarFactory(), 'tgov4_cv_bank',
        (
            Tgov4ValveSettings(initial_position=1.0),
            Tgov4ValveSettings(initial_position=.75, demand_offset=.25),
        ),
        maximum_valves=4,
    )
    block: Block = template.block
    first: Var = block.state_vars[0]
    second: Var = block.state_vars[1]
    aggregate_flow: Expr = block.algebraic_eqs[0].right

    assert len(block.state_vars) == 2
    assert aggregate_flow.eval_uid({first.uid: 1.0, second.uid: .75}) == pytest.approx(1.0)


@pytest.mark.parametrize('settings,maximum_valves', [
    ((Tgov4ValveSettings(initial_position=1.0),) * 3, 2),
    ((Tgov4ValveSettings(demand_offset=.1),), 2),
    ((Tgov4ValveSettings(initial_position=1.0), Tgov4ValveSettings(
        initial_position=.5, demand_offset=.5), Tgov4ValveSettings(
        initial_position=.75, demand_offset=.25)), 4),
])
def test_tgov4_valve_bank_rejects_invalid_counts_offsets_or_initial_state(
        settings: tuple[Tgov4ValveSettings, ...], maximum_valves: int,
) -> None:
    """Reject source banks with invalid counts, offsets, or state alignment.

    :param settings: Deliberately invalid valve-bank settings.
    :param maximum_valves: Source maximum count for the bank kind.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_tgov4_valve_bank(
            VarFactory(), 'invalid_tgov4_bank', settings,
            maximum_valves=maximum_valves,
        )


def test_tgov4_steam_train_initializes_hp_reheat_lp_and_power() -> None:
    """Keep all three steam states at equilibrium for solved inputs.

    :return: None.
    """
    template = build_tgov4_steam_train(VarFactory(), 'tgov4_steam')
    block: Block = template.block
    values: dict[int, float] = parameter_values(block)

    assert len(block.state_vars) == 3
    assert [equation.eval_uid(values) for equation in block.state_eqs] == pytest.approx(
        [0.0, 0.0, 0.0], abs=1e-12,
    )
    assert block.algebraic_eqs[0].right.eval_uid(values) == pytest.approx(.8)


def test_tgov4_steam_train_tracks_valves_and_caps_reheat_pressure() -> None:
    """Apply HP/IP/LP path equations and the PRMAX state stop.

    :return: None.
    """
    template = build_tgov4_steam_train(VarFactory(), 'tgov4_steam_response')
    block: Block = template.block
    values: dict[int, float] = parameter_values(block)
    hp_flow: Var = block.state_vars[0]
    reheat: Var = block.state_vars[1]
    lp_flow: Var = block.state_vars[2]
    values[hp_flow.uid] = .8
    values[reheat.uid] = .8
    values[lp_flow.uid] = .8
    values[block.in_vars[0].uid] = .9
    values[block.in_vars[1].uid] = .5

    assert block.state_eqs[0].eval_uid(values) == pytest.approx(1.0 / 3.0)
    assert block.state_eqs[1].eval_uid(values) == pytest.approx(0.0)
    assert block.state_eqs[2].eval_uid(values) == pytest.approx(-.8)

    values[hp_flow.uid] = 2.0
    values[reheat.uid] = 1.2
    values[block.in_vars[0].uid] = 2.0
    assert block.state_eqs[1].eval_uid(values) == pytest.approx(0.0)


@pytest.mark.parametrize(
    'settings',
    (
        Tgov4SteamSettings(t4=-.1),
        Tgov4SteamSettings(t5=0.0),
        Tgov4SteamSettings(t6=-.1),
        Tgov4SteamSettings(k1=.8, k2=.3),
        Tgov4SteamSettings(prmax=0.0),
    ),
)
def test_tgov4_steam_train_rejects_invalid_source_settings(
        settings: Tgov4SteamSettings,
) -> None:
    """Reject times, stage fractions, and reheat pressure outside source limits.

    :param settings: Invalid steam-train source settings.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_tgov4_steam_train(VarFactory(), 'invalid_tgov4_steam', settings)


def test_tgov4_boiler_initializes_pressure_fuel_and_drum_balance() -> None:
    """Start boiler pressure control, fuel delays, and storage at equilibrium.

    :return: None.
    """
    template = build_tgov4_boiler(VarFactory(), 'tgov4_boiler')
    block: Block = template.block
    values: dict[int, float] = parameter_values(block)

    assert len(block.state_vars) == 5
    assert [equation.eval_uid(values) for equation in block.state_eqs] == pytest.approx(
        [0.0, 0.0, 0.0, 0.0, 0.0], abs=1e-12,
    )
    assert block.algebraic_eqs[0].right.eval_uid(values) == pytest.approx(1.0)


def test_tgov4_boiler_pressure_drop_and_zero_pi_controller() -> None:
    """Retain drum-pressure response when boiler PI gains are disabled.

    :return: None.
    """
    template = build_tgov4_boiler(
        VarFactory(), 'tgov4_boiler_no_pi',
        Tgov4BoilerSettings(kp=0.0, ki=0.0),
    )
    block: Block = template.block
    values: dict[int, float] = parameter_values(block)
    main_steam_flow: Var = block.in_vars[0]
    values[main_steam_flow.uid] = .9

    assert block.algebraic_eqs[0].right.eval_uid(values) == pytest.approx(
        1.0 + .01 * .8 - .01 * .9,
    )
    assert block.state_eqs[-1].eval_uid(values) == pytest.approx(-.01)


def test_tgov4_boiler_controller_increases_fuel_when_pressure_drops() -> None:
    """Drive the PI/fuel chain in the restoring direction after flow rises.

    :return: None.
    """
    block: Block = build_tgov4_boiler(
        VarFactory(), 'tgov4_boiler_control',
    ).block
    values: dict[int, float] = parameter_values(block)
    main_steam_flow: Var = block.in_vars[0]
    boiler_pressure: Var = block.algebraic_vars[0]
    drum_pressure: Var = block.state_vars[-1]
    values[main_steam_flow.uid] = .9
    values[boiler_pressure.uid] = block.algebraic_eqs[0].right.eval_uid(values)

    assert values[boiler_pressure.uid] < 1.0
    assert block.state_eqs[0].eval_uid(values) > 0.0
    assert block.state_eqs[1].eval_uid(values) > 0.0


@pytest.mark.parametrize(
    'settings',
    (
        Tgov4BoilerSettings(cb=0.0),
        Tgov4BoilerSettings(tfuel=-1.0),
        Tgov4BoilerSettings(ki=-.1),
        Tgov4BoilerSettings(kb=-.1),
        Tgov4BoilerSettings(initial_boiler_pressure=0.0),
    ),
)
def test_tgov4_boiler_rejects_invalid_source_settings(
        settings: Tgov4BoilerSettings,
) -> None:
    """Reject invalid storage, controller, delay, and pressure-drop settings.

    :param settings: Invalid boiler source settings.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_tgov4_boiler(VarFactory(), 'invalid_tgov4_boiler', settings)


def test_tgov4_boiler_reduces_zero_fuel_lags_algebraically() -> None:
    """Remove zero-time fuel stages without adding artificial states.

    :return: None.
    """
    block: Block = build_tgov4_boiler(
        VarFactory(), 'tgov4_boiler_static_fuel',
        Tgov4BoilerSettings(tfuel=0.0, tfd1=0.0, tfd2=0.0),
    ).block
    values: dict[int, float] = parameter_values(block)

    assert len(block.state_vars) == 2
    assert block.state_eqs[-1].eval_uid(values) == pytest.approx(0.0)


def test_tgov4_thermal_train_connects_valves_steam_and_boiler() -> None:
    """Close the source thermal chain and retain its initialized DAE balance.

    :return: None.
    """
    block: Block = build_tgov4_thermal_train(
        VarFactory(), 'tgov4_thermal',
    ).block
    values: dict[int, float] = parameter_values(block)

    assert len(block.in_vars) == 1
    assert len(block.out_vars) == 1
    assert len(block.state_vars) == 11
    assert [equation.eval_uid(values) for equation in block.state_eqs] == pytest.approx(
        [0.0] * 11, abs=1e-12,
    )
    assert [equation.eval_uid(values) for equation in block.algebraic_eqs] == pytest.approx(
        [0.0] * len(block.algebraic_eqs), abs=1e-12,
    )
    assert block.init_eqs[block.out_vars[0]] == Const(.8)


def test_tgov4_thermal_train_rejects_inconsistent_component_initialization() -> None:
    """Reject steam/boiler settings that disagree with valve-bank initial flow.

    :return: None.
    """
    with pytest.raises(ValueError):
        build_tgov4_thermal_train(
            VarFactory(), 'invalid_tgov4_thermal',
            steam_settings=Tgov4SteamSettings(initial_control_flow=.7),
        )


def test_tgov4_native_catalog_builds_connected_thermal_chain() -> None:
    """Expose the composed TGOV4 chain through the standard RMS catalogue.

    :return: None.
    """
    template = build_international_standard_template(
        InternationalStandardModel.TGOV4, VarFactory(), 'catalog_tgov4',
    )
    block: Block = template.block
    assert template.tpe.name == 'GeneratorDevice'
    assert len(block.in_vars) == 1
    assert len(block.out_vars) == 1
    assert len(block.state_vars) == 11
    assert len(block.state_eqs) == len(block.state_vars)
    assert all(equation.eval_uid(parameter_values(block)) == pytest.approx(0.0, abs=1e-12)
               for equation in block.state_eqs)


def test_tgov4_maximum_valve_configuration_has_seventeen_balanced_states() -> None:
    """Assemble four CVs, two IVs, boiler, steam, and both rate memories.

    :return: None.
    """
    template = build_tgov4_thermal_train(
        VarFactory(), 'tgov4_full_state_count',
        control_valves=(Tgov4ValveSettings(),) * 4,
        intercept_valves=(Tgov4ValveSettings(initial_position=1.0),) * 2,
        relay_settings=Tgov4RelaySettings(
            initial_generator_current=.6, initial_generator_power=.8,
            initial_reheat_pressure=.8,
        ),
    )
    block: Block = template.block
    values: dict[int, float] = parameter_values(block)

    assert len(block.in_vars) == 2
    assert len(block.out_vars) == 8
    assert len(block.state_vars) == 17
    assert len(block.state_eqs) == 17
    assert len(block.procedural_logic) == 26
    assert [equation.eval_uid(values) for equation in block.state_eqs] == pytest.approx(
        [0.0] * 17, abs=1e-12,
    )
    assert [equation.eval_uid(values) for equation in block.algebraic_eqs] == pytest.approx(
        [0.0] * len(block.algebraic_eqs), abs=1e-12,
    )


def test_tgov4_fast_close_waits_at_zero_then_releases_the_valve() -> None:
    """Close at the fast rate, hold at zero, then restore governor demand.

    :return: None.
    """
    factory: VarFactory = VarFactory()
    template = build_tgov4_valve_bank(
        factory, 'tgov4_fast_close',
        (Tgov4ValveSettings(initial_position=.8),),
        initial_control_signal=.8,
        fast_close_trigger=Const(1.0), fast_close_start=0.0,
        fast_close_rate=4.0, closed_times=(.2,),
    )
    block: Block = template.block
    input_signal: Var = block.in_vars[0]
    block.in_vars.remove(input_signal)
    block.init_eqs.pop(input_signal, None)
    block.event_dict[input_signal] = factory.add_const(1.0)
    parsed: Block = roundtrip_block(block, ProceduralLogicCodec())
    problem: EmtProblemTemplate = EmtProblemTemplate(
        sys_block=parsed, glob_time=factory.add_var('tgov4_fast_close_time'),
        static_parameter_values_mapping=dict(),
    )
    updater = build_boundary_updater_from_block(problem)
    assert updater is not None
    state: np.ndarray = problem.get_x0().copy()
    parameters: np.ndarray = problem.event_params_values.copy()
    position: Var = parsed.state_vars[0]
    close_mode: Var = next(
        variable for variable in parsed.event_dict
        if variable.name.startswith('FastCloseMode1_')
    )
    closed_hold: Var = next(
        variable for variable in parsed.event_dict
        if variable.name.startswith('ClosedHoldComplete1_')
    )
    hold_logic: PickupDropoffLogic = updater.logic_entries[1]
    position_index: int = problem.get_var_idx(position)
    close_mode_index: int = int(problem.uid2idx_event_params[close_mode.uid])
    hold_index: int = int(problem.uid2idx_event_params[closed_hold.uid])
    updater.update(0.0, state, parameters)
    assert parameters[close_mode_index] == pytest.approx(1.0)
    state[position_index] = 0.0
    updater.update(.1, state, parameters)
    assert parameters[close_mode_index] == pytest.approx(1.0)
    assert hold_logic.pending_pickup_time == pytest.approx(.3)
    assert hold_logic.get_next_forced_event_time(.1, .31) == pytest.approx(.3)
    updater.update(.299, state, parameters)
    assert parameters[close_mode_index] == pytest.approx(1.0)
    hold_logic.get_next_forced_event_time(.299, .31)
    updater.update(.31, state, parameters)
    assert parameters[hold_index] == pytest.approx(1.0)
    assert parameters[close_mode_index] == pytest.approx(0.0)
    values: dict[int, float] = parameter_values(parsed)
    values[position.uid] = 0.0
    values[close_mode.uid] = parameters[close_mode_index]
    assert parsed.state_eqs[0].eval_uid(values) > 0.0


def test_tgov4_relay_monitors_do_not_drive_valves_without_verified_timing() -> None:
    """Keep unverified relay status timing outside the CV/IV demand path.

    :return: None.
    """
    block: Block = build_tgov4_thermal_train(
        VarFactory(), 'tgov4_relay_gating',
        relay_settings=Tgov4RelaySettings(
            initial_generator_current=.2, initial_generator_power=.8,
            initial_reheat_pressure=.8,
        ),
    ).block
    values: dict[int, float] = parameter_values(block)
    control_positions: list[Var] = [
        state for state in block.state_vars
        if '_CV_' in state.name and 'ValvePosition' in state.name
    ]
    intercept_positions: list[Var] = [
        state for state in block.state_vars
        if '_IV_' in state.name and 'ValvePosition' in state.name
    ]
    for position in control_positions:
        values[position.uid] = .8
    for position in intercept_positions:
        values[position.uid] = 1.0
    for variable in block.algebraic_vars:
        if variable.name.startswith('CVControlSignalPu_'):
            values[variable.uid] = .8
        elif variable.name.startswith('IVControlSignalPu_'):
            values[variable.uid] = 1.0
    control_derivatives: list[Expr] = [
        block.state_eqs[block.state_vars.index(position)] for position in control_positions
    ]
    intercept_derivatives: list[Expr] = [
        block.state_eqs[block.state_vars.index(position)] for position in intercept_positions
    ]

    assert [equation.eval_uid(values) for equation in control_derivatives] == pytest.approx(
        [0.0] * len(control_derivatives), abs=1e-12,
    )
    assert [equation.eval_uid(values) for equation in intercept_derivatives] == pytest.approx(
        [0.0] * len(intercept_derivatives), abs=1e-12,
    )


def test_tgov4_speed_paths_initialize_and_reduce_power_on_overspeed() -> None:
    """Hold both references at the initial point and close valves on overspeed.

    :return: None.
    """
    block: Block = build_tgov4_speed_control(
        VarFactory(), 'tgov4_speed', Tgov4GovernorSettings(), .8, 1.0,
    ).block
    values: dict[int, float] = parameter_values(block)
    speed: Var = block.in_vars[0]
    speed_filter: Var = block.state_vars[0]
    compensated_speed: Var = block.algebraic_vars[0]
    values[speed.uid] = .01
    values[speed_filter.uid] = .01
    values[compensated_speed.uid] = .01
    cv_signal: Var = block.out_vars[0]
    iv_signal: Var = block.out_vars[1]

    assert block.state_eqs[0].eval_uid(values) == pytest.approx(0.0, abs=1e-12)
    assert block.algebraic_eqs[-2].right.eval_uid(values) == pytest.approx(.55)
    assert block.algebraic_eqs[-1].right.eval_uid(values) == pytest.approx(.8)
    assert cv_signal.name.endswith('CVControlSignalPu_tgov4_speed')
    assert iv_signal.name.endswith('IVControlSignalPu_tgov4_speed')


@pytest.mark.parametrize(
    'settings',
    (
        Tgov4GovernorSettings(k=0.0),
        Tgov4GovernorSettings(t1=-.1),
        Tgov4GovernorSettings(t1=0.0, t2=.1),
        Tgov4GovernorSettings(r=0.0),
    ),
)
def test_tgov4_speed_control_rejects_invalid_constants(
        settings: Tgov4GovernorSettings,
) -> None:
    """Reject invalid speed gain, compensation, and intercept droop values.

    :param settings: Invalid governor source settings.
    :return: None.
    """
    with pytest.raises(ValueError):
        build_tgov4_speed_control(VarFactory(), 'invalid_tgov4_speed', settings, .8, 1.0)
