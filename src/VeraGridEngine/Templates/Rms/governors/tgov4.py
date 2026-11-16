# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""PSS/E TGOV4 source-defined valve servo and flow characteristic."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.procedural_logic import (
    FlipFlopLogic,
    PickupDropoffLogic,
    TimeDelayLogic,
    bool_and,
    bool_not,
    bool_or,
)
from VeraGridEngine.enumerations import DeviceType


class Tgov4ValveSettings:
    """Store one TGOV4 valve's servo, characteristic, and initial position."""

    __slots__ = ('time_constant', 'opening_rate', 'closing_rate', 'initial_position',
                 'position_at_80_percent_flow',
                 'demand_position_at_80_percent_signal', 'demand_offset')

    def __init__(self, time_constant: float = 0.1, opening_rate: float = 1.0,
                 closing_rate: float = -10.0, initial_position: float = 0.8,
                 position_at_80_percent_flow: float = 0.8,
                 demand_position_at_80_percent_signal: float = 0.8,
                 demand_offset: float = 0.0) -> None:
        """Store source valve parameters and the 80-percent flow point.

        :param time_constant: Positive T3 for a control valve or TIV for an intercept valve.
        :param opening_rate: Positive UO or UOIV maximum opening rate.
        :param closing_rate: Negative UC or UCIV maximum closing rate.
        :param initial_position: Solved valve position in [0, 1].
        :param position_at_80_percent_flow: Position that gives 0.8 flow area.
        :param demand_position_at_80_percent_signal: Position demand at a 0.8 control signal.
        :param demand_offset: Signal offset before the demand curve is applied.
        """
        self.time_constant: float = time_constant
        self.opening_rate: float = opening_rate
        self.closing_rate: float = closing_rate
        self.initial_position: float = initial_position
        self.position_at_80_percent_flow: float = position_at_80_percent_flow
        self.demand_position_at_80_percent_signal: float = demand_position_at_80_percent_signal
        self.demand_offset: float = demand_offset


class Tgov4SteamSettings:
    """Store TGOV4 steam-train constants and the solved starting condition."""

    __slots__ = ('kcal', 't4', 'k1', 't5', 'k2', 't6', 'prmax',
                 'initial_control_flow', 'initial_intercept_flow',
                 'initial_boiler_pressure')

    def __init__(self, kcal: float = 1.0, t4: float = 0.3, k1: float = 0.2,
                 t5: float = 5.0, k2: float = 0.3, t6: float = 0.5,
                 prmax: float = 1.2, initial_control_flow: float = 0.8,
                 initial_intercept_flow: float = 1.0,
                 initial_boiler_pressure: float = 1.0) -> None:
        """Store the source steam constants and initial valve/boiler signals.

        :param kcal: Maximum control-valve flow calibration.
        :param t4: Steam-bowl lag time in seconds.
        :param k1: High-pressure turbine mechanical-power fraction.
        :param t5: Reheat-pressure lag time in seconds.
        :param k2: Intermediate-pressure turbine mechanical-power fraction.
        :param t6: Low-pressure crossover lag time in seconds.
        :param prmax: Maximum reheat pressure.
        :param initial_control_flow: Solved normalized control-valve area.
        :param initial_intercept_flow: Solved normalized intercept-valve area.
        :param initial_boiler_pressure: Solved boiler pressure in per unit.
        """
        self.kcal: float = kcal
        self.t4: float = t4
        self.k1: float = k1
        self.t5: float = t5
        self.k2: float = k2
        self.t6: float = t6
        self.prmax: float = prmax
        self.initial_control_flow: float = initial_control_flow
        self.initial_intercept_flow: float = initial_intercept_flow
        self.initial_boiler_pressure: float = initial_boiler_pressure


class Tgov4BoilerSettings:
    """Store TGOV4 boiler-control parameters and its solved pressure point."""

    __slots__ = ('kp', 'ki', 'tfuel', 'tfd1', 'tfd2', 'kb', 'cb',
                 'initial_steam_flow', 'initial_boiler_pressure')

    def __init__(self, kp: float = 1.0, ki: float = 0.2, tfuel: float = 1.0,
                 tfd1: float = 0.5, tfd2: float = 0.5, kb: float = 0.01,
                 cb: float = 10.0, initial_steam_flow: float = 0.8,
                 initial_boiler_pressure: float = 1.0) -> None:
        """Store pressure-controller, fuel-delay, and drum parameters.

        :param kp: Boiler pressure controller proportional gain.
        :param ki: Boiler pressure controller integral gain.
        :param tfuel: Fuel-system lag time in seconds.
        :param tfd1: First fuel-delay approximation time in seconds.
        :param tfd2: Second fuel-delay approximation time in seconds.
        :param kb: Flow-dependent boiler friction-drop coefficient.
        :param cb: Positive boiler storage constant in seconds.
        :param initial_steam_flow: Solved main-steam flow in per unit.
        :param initial_boiler_pressure: Solved boiler pressure in per unit.
        """
        self.kp: float = kp
        self.ki: float = ki
        self.tfuel: float = tfuel
        self.tfd1: float = tfd1
        self.tfd2: float = tfd2
        self.kb: float = kb
        self.cb: float = cb
        self.initial_steam_flow: float = initial_steam_flow
        self.initial_boiler_pressure: float = initial_boiler_pressure


class Tgov4GovernorSettings:
    """Store TGOV4 speed-path constants and intercept-valve droop settings."""

    __slots__ = ('k', 't1', 't2', 'r', 'offset')

    def __init__(self, k: float = 25.0, t1: float = 0.02, t2: float = 0.0,
                 r: float = 0.05, offset: float = 0.6) -> None:
        """Store governor compensation, CV gain, IV droop, and offset.

        :param k: Inverse governor speed droop.
        :param t1: Speed-path lag time in seconds.
        :param t2: Speed-path lead time in seconds.
        :param r: Intercept-valve speed droop.
        :param offset: Source IV control offset.
        """
        self.k: float = k
        self.t1: float = t1
        self.t2: float = t2
        self.r: float = r
        self.offset: float = offset


class Tgov4RelaySettings:
    """Store PLU/EVA thresholds, timer, mode, and solved input values."""

    __slots__ = ('tr_plu', 'tr_eva', 'initial_generator_current',
                 'initial_generator_power', 'initial_reheat_pressure',
                 'plu_rate_level', 'plu_timer', 'plu_unbalance_level',
                 'eva_rate_level', 'eva_unbalance_level', 'cv_close_start',
                 'cv_close_rate', 'cv_closed_times', 'iv_close_start',
                 'iv_close_rate', 'iv_closed_times', 'mode')

    def __init__(self, tr_plu: float = 1.0, tr_eva: float = 1.0,
                 initial_generator_current: float = 0.0,
                 initial_generator_power: float = 0.0,
                 initial_reheat_pressure: float = 0.0,
                 plu_rate_level: float = 0.1,
                 plu_timer: float = 0.1,
                 plu_unbalance_level: float = 0.1,
                 eva_rate_level: float = 0.1,
                 eva_unbalance_level: float = 0.1,
                 cv_close_start: float = 0.0,
                 cv_close_rate: float = 10.0,
                 cv_closed_times: tuple[float, ...] = (0.0, 0.0, 0.0, 0.0),
                 iv_close_start: float = 0.0,
                 iv_close_rate: float = 10.0,
                 iv_closed_times: tuple[float, ...] = (0.0, 0.0),
                 mode: int = 3) -> None:
        """Store source thresholds, filter times, mode, and measurements.

        :param tr_plu: PLU first-order rate-filter time in seconds.
        :param tr_eva: EVA first-order rate-filter time in seconds.
        :param initial_generator_current: Solved generator current on machine base.
        :param initial_generator_power: Solved electrical generator power on machine base.
        :param initial_reheat_pressure: Solved reheat pressure in per unit.
        :param plu_rate_level: PLU rate pickup threshold.
        :param plu_timer: Time rate pickup must remain active before PLU can trip.
        :param plu_unbalance_level: PLU unbalance pickup threshold.
        :param eva_rate_level: EVA rate pickup threshold.
        :param eva_unbalance_level: EVA unbalance pickup threshold.
        :param cv_close_start: Delay between relay trigger and CV closing in seconds.
        :param cv_close_rate: Positive fast-closing speed for CVs in pu/s.
        :param cv_closed_times: Closed hold time in seconds for each of four CVs.
        :param iv_close_start: Delay between relay trigger and IV closing in seconds.
        :param iv_close_rate: Positive fast-closing speed for IVs in pu/s.
        :param iv_closed_times: Closed hold time in seconds for each of two IVs.
        :param mode: Source mode 0, 2 or 3; mode 1 needs external user logic.
        """
        self.tr_plu: float = tr_plu
        self.tr_eva: float = tr_eva
        self.initial_generator_current: float = initial_generator_current
        self.initial_generator_power: float = initial_generator_power
        self.initial_reheat_pressure: float = initial_reheat_pressure
        self.plu_rate_level: float = plu_rate_level
        self.plu_timer: float = plu_timer
        self.plu_unbalance_level: float = plu_unbalance_level
        self.eva_rate_level: float = eva_rate_level
        self.eva_unbalance_level: float = eva_unbalance_level
        self.cv_close_start: float = cv_close_start
        self.cv_close_rate: float = cv_close_rate
        self.cv_closed_times: tuple[float, ...] = cv_closed_times
        self.iv_close_start: float = iv_close_start
        self.iv_close_rate: float = iv_close_rate
        self.iv_closed_times: tuple[float, ...] = iv_closed_times
        self.mode: int = mode


def valve_characteristic_a(position_at_80_percent_flow: float) -> float:
    """Solve the source exponential valve curve's A coefficient.

    The normalized source curve is constrained to unit output at full input and
    0.8 output at the source-defined input. Bisection is monotone for the
    documented concave characteristics in [0.2, 0.8].

    :param position_at_80_percent_flow: Source position at 0.8 flow area.
    :return: Nonnegative exponential coefficient A.
    """
    if position_at_80_percent_flow == 0.8:
        return 0.0
    else:
        lower: float = 0.0
        upper: float = 100.0
        for _ in range(80):
            middle: float = (lower + upper) / 2.0
            denominator: float = 1.0 - math.exp(-middle)
            ratio: float = (1.0 - math.exp(-middle * position_at_80_percent_flow)) / denominator
            if ratio < 0.8:
                lower = middle
            else:
                upper = middle
        return (lower + upper) / 2.0


def valve_position_demand(signal: float, position_at_80: float) -> float:
    """Evaluate the source nonlinear valve demand characteristic.

    :param signal: Normalized control signal after applying any valve offset.
    :param position_at_80: Demand position at a normalized signal of 0.8.
    :return: Valve position demand in [0, 1].
    """
    bounded_signal: float = min(max(signal, 0.0), 1.0)
    characteristic_a: float = valve_characteristic_a(position_at_80)
    if characteristic_a == 0.0:
        return bounded_signal
    else:
        characteristic_k: float = 1.0 / (1.0 - math.exp(-characteristic_a))
        return -math.log(1.0 - bounded_signal / characteristic_k) / characteristic_a


def valve_control_signal(position: float, position_at_80: float, offset: float) -> float:
    """Invert the source demand curve for an initial valve position.

    :param position: Initial mechanical valve position.
    :param position_at_80: Position demand at a normalized signal of 0.8.
    :param offset: Source control-signal offset for this valve.
    :return: Shared control signal that initializes the valve at position.
    """
    characteristic_a: float = valve_characteristic_a(position_at_80)
    if characteristic_a == 0.0:
        return position + offset
    else:
        characteristic_k: float = 1.0 / (1.0 - math.exp(-characteristic_a))
        return (characteristic_k * (1.0 - math.exp(-characteristic_a * position))
                + offset)


def valve_flow_area(position: float, position_at_80: float) -> float:
    """Evaluate the source exponential valve-flow characteristic.

    :param position: Normalized mechanical valve position.
    :param position_at_80: Valve position at a normalized flow of 0.8.
    :return: Normalized valve flow area.
    """
    bounded_position: float = min(max(position, 0.0), 1.0)
    characteristic_a: float = valve_characteristic_a(position_at_80)
    if characteristic_a == 0.0:
        return bounded_position
    else:
        return ((1.0 - math.exp(-characteristic_a * bounded_position))
                / (1.0 - math.exp(-characteristic_a)))


def build_tgov4_valve_bank(
        vf: VarFactory,
        name: str,
        settings: tuple[Tgov4ValveSettings, ...] | None = None,
        initial_control_signal: float | None = None,
        maximum_valves: int = 4,
        fast_close_trigger: Expr | sym.Comparison | None = None,
        fast_close_start: float = 0.0,
        fast_close_rate: float = 10.0,
        closed_times: tuple[float, ...] | None = None,
) -> RmsModelTemplate:
    """Build a TGOV4 multivalve servo bank and normalized aggregate flow.

    Each valve has its source-defined demand and flow characteristics, offset,
    servo time, and rate limits. Their area is normalized so that the aggregate
    flow reaches one at a unit input. A common input is required for equilibrium
    initialization, matching PSS/E's shared CV or IV control signal.

    :param vf: Variable factory owning the component equations.
    :param name: Unique valve instance name.
    :param settings: Ordered settings for one to four CVs or one to two IVs.
    :param initial_control_signal: Shared source signal at the operating point.
    :param maximum_valves: Source bank limit, 4 for CVs or 2 for IVs.
    :param fast_close_trigger: Relay condition that starts the bank's close events.
    :param fast_close_start: Delay from relay trigger to bank closing, in seconds.
    :param fast_close_rate: Positive close-rate magnitude, in pu/s.
    :param closed_times: Per-valve closed hold time in seconds.
    :return: Valve bank with one state per valve and one aggregate flow output.
    :raises ValueError: Settings violate the source parameter domain.
    """
    selected_valves: tuple[Tgov4ValveSettings, ...] = (
        (Tgov4ValveSettings(),) if settings is None else settings
    )
    selected_closed_times: tuple[float, ...] = (
        (0.0,) * len(selected_valves) if closed_times is None else closed_times
    )
    if not 1 <= maximum_valves <= 4:
        raise ValueError('TGOV4 valve-bank limit must be between one and four')
    elif len(selected_valves) < 1 or len(selected_valves) > maximum_valves:
        raise ValueError('TGOV4 valve count is outside the selected bank limit')
    elif initial_control_signal is not None and not math.isfinite(initial_control_signal):
        raise ValueError('TGOV4 initial control signal must be finite')
    elif fast_close_trigger is not None and (
            not math.isfinite(fast_close_start) or fast_close_start < 0.0
            or not math.isfinite(fast_close_rate) or fast_close_rate <= 0.0):
        raise ValueError('TGOV4 fast-close start must be nonnegative and rate positive')
    elif fast_close_trigger is not None and len(selected_closed_times) != len(selected_valves):
        raise ValueError('TGOV4 closed-time count must match its valve bank')
    elif fast_close_trigger is not None and not all(
            math.isfinite(value) and value >= 0.0 for value in selected_closed_times):
        raise ValueError('TGOV4 valve closed times must be finite and nonnegative')
    else:
        pass

    if initial_control_signal is None:
        first_valve: Tgov4ValveSettings = selected_valves[0]
        initial_control_signal = valve_control_signal(
            first_valve.initial_position,
            first_valve.demand_position_at_80_percent_signal,
            first_valve.demand_offset,
        )
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    signal: Var = control.input('ValveControlSignalPu', Const(initial_control_signal))
    flow_terms: list[Expr] = list()
    initial_flow: float = 0.0
    unit_signal_flow: float = 0.0
    previous_offset: float = -1.0
    for index, selected in enumerate(selected_valves):
        values: tuple[float, ...] = (
            selected.time_constant, selected.opening_rate, selected.closing_rate,
            selected.initial_position, selected.position_at_80_percent_flow,
            selected.demand_position_at_80_percent_signal, selected.demand_offset,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError('TGOV4 valve parameters must be finite')
        elif selected.time_constant <= 0.0 or selected.opening_rate <= 0.0 or selected.closing_rate >= 0.0:
            raise ValueError('TGOV4 valve requires positive time/opening rate and negative closing rate')
        elif not 0.0 <= selected.initial_position <= 1.0:
            raise ValueError('TGOV4 initial valve position must lie in [0, 1]')
        elif not 0.2 <= selected.position_at_80_percent_flow <= 0.8:
            raise ValueError('TGOV4 valve 80-percent position must lie in [0.2, 0.8]')
        elif not 0.2 <= selected.demand_position_at_80_percent_signal <= 0.8:
            raise ValueError('TGOV4 demand 80-percent position must lie in [0.2, 0.8]')
        elif selected.demand_offset < 0.0 or selected.demand_offset < previous_offset:
            raise ValueError('TGOV4 valve offsets must be nonnegative and ascending')
        elif index == 0 and selected.demand_offset != 0.0:
            raise ValueError('TGOV4 first valve must have zero demand offset')
        elif not math.isclose(
                valve_position_demand(
                    initial_control_signal - selected.demand_offset,
                    selected.demand_position_at_80_percent_signal,
                ), selected.initial_position, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError('TGOV4 valve initial position must match the shared signal')
        else:
            pass

        valve_index: int = index + 1
        time_constant: Var = control.parameter(
            f'ServoTimeSec{valve_index}', selected.time_constant,
        )
        opening_rate: Var = control.parameter(
            f'OpeningRatePuPerSec{valve_index}', selected.opening_rate,
        )
        closing_rate: Var = control.parameter(
            f'ClosingRatePuPerSec{valve_index}', selected.closing_rate,
        )
        position: Var = vf.add_var(f'TGOV4ValvePositionPu_{name}_{valve_index}')
        valve_signal: Expr = signal
        fast_close_mode: Var | None = None
        if fast_close_trigger is None:
            pass
        else:
            delayed_close: Var = control.parameter(
                f'DelayedFastCloseSignal{valve_index}', 0.0,
            )
            fast_close_mode = control.parameter(f'FastCloseMode{valve_index}', 0.0)
            closed_hold_complete: Var = control.parameter(
                f'ClosedHoldComplete{valve_index}', 0.0,
            )
            fast_close_armed: Var = control.parameter(
                f'FastCloseArmed{valve_index}', 1.0,
            )
            control.block.procedural_logic.append(TimeDelayLogic(
                delayed_close.name, fast_close_trigger, Const(fast_close_start),
                name=name + f'_FastCloseDelay{valve_index}',
            ))
            control.block.procedural_logic.append(PickupDropoffLogic(
                closed_hold_complete.name,
                bool_and(fast_close_mode > Const(0.5), position <= Const(1e-8)),
                Const(selected_closed_times[index]), Const(0.0),
                name=name + f'_ClosedHold{valve_index}',
            ))
            control.block.procedural_logic.append(FlipFlopLogic(
                fast_close_mode.name,
                bool_and(
                    delayed_close > Const(0.5),
                    fast_close_armed > Const(0.5),
                ),
                closed_hold_complete > Const(0.5),
                name=name + f'_FastCloseMode{valve_index}',
            ))
            control.block.procedural_logic.append(FlipFlopLogic(
                fast_close_armed.name,
                bool_not(fast_close_trigger > Const(0.5)),
                delayed_close > Const(0.5),
                name=name + f'_FastCloseArmed{valve_index}',
            ))
            valve_signal = signal * (Const(1.0) - fast_close_mode)
        demand_a: float = valve_characteristic_a(
            selected.demand_position_at_80_percent_signal,
        )
        normalized_signal: Expr = sym.hard_sat(
            valve_signal - Const(selected.demand_offset), Const(0.0), Const(1.0),
        )
        if demand_a == 0.0:
            demand_expression: Expr = normalized_signal
        else:
            demand_k: float = 1.0 / (1.0 - math.exp(-demand_a))
            demand_expression = -sym.log(
                Const(1.0) - normalized_signal / Const(demand_k)
            ) / Const(demand_a)
        normal_rate: Expr = sym.hard_sat(
            (demand_expression - position) / time_constant,
            closing_rate, opening_rate,
        )
        if fast_close_mode is None:
            rate: Expr = normal_rate
        else:
            fast_rate: Expr = sym.hard_sat(
                (Const(0.0) - position) / time_constant,
                Const(-fast_close_rate), opening_rate,
            )
            rate = fast_close_mode * fast_rate + (Const(1.0) - fast_close_mode) * normal_rate
        control.differential(
            position, rate, Const(selected.initial_position), Const(0.0), Const(1.0),
        )
        flow_a: float = valve_characteristic_a(selected.position_at_80_percent_flow)
        if flow_a == 0.0:
            flow_expression: Expr = position
        else:
            flow_k: float = 1.0 / (1.0 - math.exp(-flow_a))
            flow_expression = Const(flow_k) * (
                Const(1.0) - sym.exp(Const(-flow_a) * position)
            )
        flow_terms.append(flow_expression)
        initial_flow += valve_flow_area(
            selected.initial_position, selected.position_at_80_percent_flow,
        )
        unit_position: float = valve_position_demand(
            1.0 - selected.demand_offset,
            selected.demand_position_at_80_percent_signal,
        )
        unit_signal_flow += valve_flow_area(unit_position, selected.position_at_80_percent_flow)
        previous_offset = selected.demand_offset

    if unit_signal_flow <= 0.0:
        raise ValueError('TGOV4 valve bank has no flow at unit control signal')
    else:
        pass
    flow_normalization: float = 1.0 / unit_signal_flow
    flow_expression = Const(flow_normalization) * sum(flow_terms, Const(0.0))
    flow_initial = Const(flow_normalization * initial_flow)
    flow_area: Var = control.algebraic('FlowAreaPu', flow_expression, flow_initial)
    return control.finish(
        (flow_area,),
        'PSS/E TGOV4 rate-limited multivalve bank with source flow normalization.',
    )


def build_tgov4_steam_train(
        vf: VarFactory,
        name: str,
        settings: Tgov4SteamSettings | None = None,
) -> RmsModelTemplate:
    """Build the TGOV4 HP, reheat/IP, LP steam, and power paths.

    The steam bowl follows calibrated control-valve flow times boiler pressure.
    Reheat pressure tracks HP flow and is bounded by PRMAX. Intercept-valve
    area gates IP flow into the crossover lag; turbine fractions form Pmech.

    :param vf: Variable factory owning the DAE graph.
    :param name: Unique steam-train instance name.
    :param settings: Source constants and initial external flow/pressure values.
    :return: Three-stage steam train with mechanical-power and HP-flow outputs.
    :raises ValueError: Parameters violate source limits or produce infeasible fractions.
    """
    selected: Tgov4SteamSettings = Tgov4SteamSettings() if settings is None else settings
    values: tuple[float, ...] = (
        selected.kcal, selected.t4, selected.k1, selected.t5, selected.k2,
        selected.t6, selected.prmax, selected.initial_control_flow,
        selected.initial_intercept_flow, selected.initial_boiler_pressure,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('TGOV4 steam-train parameters must be finite')
    elif not 0.05 <= selected.kcal <= 1.5:
        raise ValueError('TGOV4 KCAL must lie in the source range [0.05, 1.5]')
    elif selected.t4 < 0.0 or selected.t5 <= 0.0 or selected.t6 < 0.0:
        raise ValueError('TGOV4 steam times require T4/T6 nonnegative and T5 positive')
    elif selected.k1 < 0.0 or selected.k2 < 0.0 or selected.k1 + selected.k2 > 1.0:
        raise ValueError('TGOV4 turbine power fractions must lie in [0, 1]')
    elif selected.prmax <= 0.0:
        raise ValueError('TGOV4 PRMAX must be positive')
    elif not 0.0 <= selected.initial_control_flow <= 1.0:
        raise ValueError('TGOV4 initial control flow must lie in [0, 1]')
    elif not 0.0 <= selected.initial_intercept_flow <= 1.0:
        raise ValueError('TGOV4 initial intercept flow must lie in [0, 1]')
    elif selected.initial_boiler_pressure <= 0.0:
        raise ValueError('TGOV4 initial boiler pressure must be positive')
    else:
        pass

    hp_initial: float = (
        selected.kcal * selected.initial_control_flow * selected.initial_boiler_pressure
    )
    reheat_initial: float = min(hp_initial, selected.prmax)
    lp_initial: float = selected.initial_intercept_flow * reheat_initial
    mechanical_initial: float = (
        selected.k1 * hp_initial + selected.k2 * reheat_initial
        + (1.0 - selected.k1 - selected.k2) * lp_initial
    )

    control: ControlRealization = ControlRealization(vf, name)
    kcal: Var = control.parameter('KCAL', selected.kcal)
    t4: Var = control.parameter('T4Sec', selected.t4)
    k1: Var = control.parameter('K1', selected.k1)
    t5: Var = control.parameter('T5Sec', selected.t5)
    k2: Var = control.parameter('K2', selected.k2)
    t6: Var = control.parameter('T6Sec', selected.t6)
    prmax: Var = control.parameter('PRMAX', selected.prmax)
    control_flow: Var = control.input('ControlValveFlowAreaPu', Const(selected.initial_control_flow))
    intercept_flow: Var = control.input('InterceptValveFlowAreaPu', Const(selected.initial_intercept_flow))
    boiler_pressure: Var = control.input('BoilerPressurePu', Const(selected.initial_boiler_pressure))
    hp_flow: Var = control.lag(
        'HPSteamFlowPu', kcal * control_flow * boiler_pressure,
        t4, selected.t4, Const(hp_initial),
    )
    reheat_pressure: Var = control.lag(
        'ReheatPressurePu', hp_flow, t5, selected.t5,
        Const(reheat_initial), Const(0.0), prmax,
    )
    lp_flow: Var = control.lag(
        'LPSteamFlowPu', intercept_flow * reheat_pressure,
        t6, selected.t6, Const(lp_initial),
    )
    mechanical_power: Var = control.algebraic(
        'MechanicalPowerPu',
        k1 * hp_flow + k2 * reheat_pressure + (Const(1.0) - k1 - k2) * lp_flow,
        Const(mechanical_initial),
    )
    return control.finish(
        (mechanical_power, hp_flow),
        'PSS/E TGOV4 HP, reheat/IP, and LP steam path with boiler-pressure input.',
    )


def build_tgov4_boiler(
        vf: VarFactory,
        name: str,
        settings: Tgov4BoilerSettings | None = None,
) -> RmsModelTemplate:
    """Build TGOV4 pressure feedback, PI fuel control, delays, and drum storage.

    Boiler pressure is drum pressure less the Kb flow-dependent pressure drop.
    Its initial value sets the internal pressure reference; the PI and all fuel
    memories start at the solved steam flow so the complete loop is at balance.

    :param vf: Variable factory owning the DAE graph.
    :param name: Unique boiler instance name.
    :param settings: Source constants and solved pressure/flow operating point.
    :return: Five-state boiler controller with boiler-pressure output.
    :raises ValueError: Constants violate source parameter or equilibrium limits.
    """
    selected: Tgov4BoilerSettings = Tgov4BoilerSettings() if settings is None else settings
    values: tuple[float, ...] = (
        selected.kp, selected.ki, selected.tfuel, selected.tfd1, selected.tfd2,
        selected.kb, selected.cb, selected.initial_steam_flow,
        selected.initial_boiler_pressure,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('TGOV4 boiler parameters must be finite')
    elif selected.kp < 0.0 or selected.ki < 0.0:
        raise ValueError('TGOV4 boiler PI gains cannot be negative')
    elif min(selected.tfuel, selected.tfd1, selected.tfd2) < 0.0:
        raise ValueError('TGOV4 fuel delay times cannot be negative')
    elif selected.kb < 0.0 or selected.cb <= 0.0:
        raise ValueError('TGOV4 Kb must be nonnegative and Cb positive')
    elif selected.initial_steam_flow < 0.0 or selected.initial_boiler_pressure <= 0.0:
        raise ValueError('TGOV4 solved steam flow and boiler pressure are invalid')
    else:
        pass

    initial_drum_pressure: float = (
        selected.initial_boiler_pressure + selected.kb * selected.initial_steam_flow
    )
    control: ControlRealization = ControlRealization(vf, name)
    kp: Var = control.parameter('KP', selected.kp)
    ki: Var = control.parameter('KI', selected.ki)
    tfuel: Var = control.parameter('TFUELSec', selected.tfuel)
    tfd1: Var = control.parameter('TFD1Sec', selected.tfd1)
    tfd2: Var = control.parameter('TFD2Sec', selected.tfd2)
    kb: Var = control.parameter('KB', selected.kb)
    cb: Var = control.parameter('CB', selected.cb)
    main_steam_flow: Var = control.input(
        'HPSteamFlowPu', Const(selected.initial_steam_flow),
    )
    drum_pressure: Var = vf.add_var(f'TGOV4DrumPressurePu_{name}')
    boiler_pressure: Var = control.algebraic(
        'BoilerPressurePu', drum_pressure - kb * main_steam_flow,
        Const(selected.initial_boiler_pressure),
    )
    pressure_error: Expr = Const(selected.initial_boiler_pressure) - boiler_pressure
    fuel_integrator: Var = vf.add_var(f'TGOV4BoilerPIIntegralPu_{name}')
    control.differential(
        fuel_integrator, ki * pressure_error, Const(selected.initial_steam_flow),
    )
    fuel_command: Expr = kp * pressure_error + fuel_integrator
    fuel: Var = control.lag(
        'FuelFlowPu', fuel_command, tfuel, selected.tfuel,
        Const(selected.initial_steam_flow),
    )
    fuel_delay_1: Var = control.lag(
        'FuelDelay1Pu', fuel, tfd1, selected.tfd1,
        Const(selected.initial_steam_flow),
    )
    fuel_delay_2: Var = control.lag(
        'FuelDelay2Pu', fuel_delay_1, tfd2, selected.tfd2,
        Const(selected.initial_steam_flow),
    )
    drum_rate: Expr = (fuel_delay_2 - main_steam_flow) / cb
    control.differential(
        drum_pressure, drum_rate, Const(initial_drum_pressure),
    )
    return control.finish(
        (boiler_pressure,),
        'PSS/E TGOV4 boiler pressure PI control, staged fuel delays, and drum storage.',
    )


def build_tgov4_speed_control(
        vf: VarFactory,
        name: str,
        settings: Tgov4GovernorSettings,
        initial_control_signal: float,
        initial_intercept_signal: float,
) -> RmsModelTemplate:
    """Build TGOV4 compensated CV command and independent IV droop command.

    The CV command is its solved load reference less K times the compensated
    speed deviation. The IV command is its solved reference plus Offset less
    speed deviation over R, matching the separate source diagram path.

    :param vf: Variable factory owning the DAE graph.
    :param name: Unique speed-control instance name.
    :param settings: Source K, T1, T2, R and Offset values.
    :param initial_control_signal: Solved CV demand signal.
    :param initial_intercept_signal: Solved IV demand signal.
    :return: Speed input and ordered CV/IV command outputs.
    :raises ValueError: Speed compensation or droop values are invalid.
    """
    values: tuple[float, ...] = (
        settings.k, settings.t1, settings.t2, settings.r, settings.offset,
        initial_control_signal, initial_intercept_signal,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('TGOV4 governor parameters must be finite')
    elif settings.k <= 0.0 or settings.r <= 0.0:
        raise ValueError('TGOV4 CV gain and IV droop must be positive')
    elif settings.t1 < 0.0 or settings.t2 < 0.0:
        raise ValueError('TGOV4 speed compensation times cannot be negative')
    elif settings.t1 == 0.0 and settings.t2 != 0.0:
        raise ValueError('TGOV4 zero speed-path lag requires zero lead')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    speed_deviation: Var = control.input('SpeedDeviationPu', Const(0.0))
    t1: Var = control.parameter('T1Sec', settings.t1)
    t2: Var = control.parameter('T2Sec', settings.t2)
    gain: Var = control.parameter('K', settings.k)
    droop: Var = control.parameter('R', settings.r)
    offset: Var = control.parameter('Offset', settings.offset)
    compensated_speed: Var = control.lead_lag(
        'CompensatedSpeedDeviationPu', speed_deviation, t2, t1,
        settings.t2, settings.t1, Const(0.0),
    )
    cv_reference: Var = control.parameter('CVLoadReferencePu', initial_control_signal)
    cv_signal: Var = control.algebraic(
        'CVControlSignalPu', cv_reference - gain * compensated_speed,
        Const(initial_control_signal),
    )
    iv_reference: Var = control.parameter(
        'IVLoadReferencePu', initial_intercept_signal - settings.offset,
    )
    iv_signal: Var = control.algebraic(
        'IVControlSignalPu', iv_reference + offset - speed_deviation / droop,
        Const(initial_intercept_signal),
    )
    return control.finish(
        (cv_signal, iv_signal),
        'PSS/E TGOV4 compensated CV and droop-controlled IV signal paths.',
    )


def build_tgov4_relay_monitors(
        vf: VarFactory,
        name: str,
        settings: Tgov4RelaySettings | None = None,
) -> RmsModelTemplate:
    """Build source rate measurements, PLU timer/latch, and EVA action.

    The two washout memories are the PLU/EVA rate states listed in the PSS/E
    state table. PLU rate pickup must persist through TIMER before its rate and
    unbalance conjunction sets the retained latch; the latch resets below the
    unbalance level. EVA uses its rate/unbalance conjunction. Relay outputs do
    not yet schedule valve actions because per-valve closing/reopening timing
    is not realized. Mode 1 is rejected because user-controlled inputs are
    unrepresented.

    :param vf: Variable factory owning the relay measurement equations.
    :param name: Unique relay component label.
    :param settings: Source filter times and solved measurement values.
    :return: Two-filter-state block with rate, unbalance, and relay outputs.
    :raises ValueError: Filter times or initial measurements are invalid.
    """
    selected: Tgov4RelaySettings = Tgov4RelaySettings() if settings is None else settings
    values: tuple[float, ...] = (
        selected.tr_plu, selected.tr_eva, selected.initial_generator_current,
        selected.initial_generator_power, selected.initial_reheat_pressure,
        selected.plu_rate_level, selected.plu_timer, selected.plu_unbalance_level,
        selected.eva_rate_level, selected.eva_unbalance_level,
        selected.cv_close_start, selected.cv_close_rate,
        selected.iv_close_start, selected.iv_close_rate,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('TGOV4 PLU/EVA relay settings must be finite')
    elif selected.tr_plu <= 0.0 or selected.tr_eva <= 0.0:
        raise ValueError('TGOV4 PLU/EVA rate-filter times must be positive')
    elif selected.plu_timer < 0.0:
        raise ValueError('TGOV4 PLU rate timer cannot be negative')
    elif selected.cv_close_start < 0.0 or selected.iv_close_start < 0.0:
        raise ValueError('TGOV4 valve close-start delays cannot be negative')
    elif selected.cv_close_rate <= 0.0 or selected.iv_close_rate <= 0.0:
        raise ValueError('TGOV4 fast valve close rates must be positive')
    elif len(selected.cv_closed_times) != 4 or len(selected.iv_closed_times) != 2:
        raise ValueError('TGOV4 requires four CV and two IV closed-time values')
    elif not all(
            math.isfinite(value) and value >= 0.0
            for value in selected.cv_closed_times + selected.iv_closed_times):
        raise ValueError('TGOV4 valve closed times must be finite and nonnegative')
    elif selected.mode not in (0, 1, 2, 3):
        raise ValueError('TGOV4 relay mode must be 0, 1, 2, or 3')
    elif selected.mode == 1:
        raise ValueError('TGOV4 mode 1 user-controlled relay switching is unsupported')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    tr_plu: Var = control.parameter('TRPLUSec', selected.tr_plu)
    tr_eva: Var = control.parameter('TREVASec', selected.tr_eva)
    generator_current: Var = control.input(
        'GeneratorCurrentPu', Const(selected.initial_generator_current),
    )
    generator_power: Var = control.input(
        'GeneratorPowerPu', Const(selected.initial_generator_power),
    )
    reheat_pressure: Var = control.input(
        'ReheatPressurePu', Const(selected.initial_reheat_pressure),
    )
    plu_filtered_current: Var = control.lag(
        'PLUFilteredCurrentPu', generator_current, tr_plu, selected.tr_plu,
        Const(selected.initial_generator_current),
    )
    eva_filtered_power: Var = control.lag(
        'EVAFilteredPowerPu', generator_power, tr_eva, selected.tr_eva,
        Const(selected.initial_generator_power),
    )
    plu_rate: Var = control.algebraic(
        'PLURateSignalPu', generator_current - plu_filtered_current, Const(0.0),
    )
    eva_rate: Var = control.algebraic(
        'EVARateSignalPu', generator_power - eva_filtered_power, Const(0.0),
    )
    plu_unbalance: Var = control.algebraic(
        'PLUUnbalancePu', reheat_pressure - generator_current,
        Const(selected.initial_reheat_pressure - selected.initial_generator_current),
    )
    eva_unbalance: Var = control.algebraic(
        'EVAUnbalancePu', reheat_pressure - generator_power,
        Const(selected.initial_reheat_pressure - selected.initial_generator_power),
    )
    plu_rate_level: Var = control.parameter('PLURateLevelPu', selected.plu_rate_level)
    plu_timer: Var = control.parameter('PLUTimerSec', selected.plu_timer)
    plu_unbalance_level: Var = control.parameter(
        'PLUUnbalanceLevelPu', selected.plu_unbalance_level,
    )
    eva_rate_level: Var = control.parameter('EVARateLevelPu', selected.eva_rate_level)
    eva_unbalance_level: Var = control.parameter(
        'EVAUnbalanceLevelPu', selected.eva_unbalance_level,
    )
    plu_rate_trigger: sym.Comparison = plu_rate > plu_rate_level
    plu_unbalance_trigger: sym.Comparison = plu_unbalance > plu_unbalance_level
    eva_rate_trigger: sym.Comparison = eva_rate > eva_rate_level
    eva_unbalance_trigger: sym.Comparison = eva_unbalance > eva_unbalance_level
    plu_action_expression: Expr = Const(0.0)
    if selected.mode in (2, 3):
        delayed_plu_rate: Var = control.parameter('PLURateTimerReady', 0.0)
        plu_latch: Var = control.parameter('PLUValveCloseLatch', 0.0)
        control.block.procedural_logic.append(TimeDelayLogic(
            delayed_plu_rate.name, plu_rate_trigger, plu_timer,
            name=name + '_PLURateTimer', continuous=True,
        ))
        control.block.procedural_logic.append(FlipFlopLogic(
            plu_latch.name,
            bool_and(
                delayed_plu_rate > Const(0.5), plu_rate_trigger,
                plu_unbalance_trigger,
            ),
            plu_unbalance < plu_unbalance_level,
            name=name + '_PLULatch',
        ))
        plu_action_expression = plu_latch
    else:
        pass
    eva_action_expression: Expr = bool_and(
        eva_rate_trigger, eva_unbalance_trigger,
    ) if selected.mode == 3 else Const(0.0)
    plu_action: Var = control.algebraic(
        'PLURelayTriggered', plu_action_expression, Const(0.0),
    )
    eva_action: Var = control.algebraic(
        'EVARelayTriggered', eva_action_expression, Const(0.0),
    )
    close_action: Var = control.algebraic(
        'FastValvingRelayTriggered',
        bool_or(plu_action > Const(0.5), eva_action > Const(0.5)),
        Const(0.0),
    )
    return control.finish(
        (plu_rate, eva_rate, plu_unbalance, eva_unbalance,
         plu_action, eva_action, close_action),
        'PSS/E TGOV4 PLU timer/latch and EVA comparator action paths.',
    )


def append_tgov4_component(
        target: Block,
        source: Block,
        substitutions: dict[Var, Expr],
) -> None:
    """Append one component's DAE equations after replacing connected ports.

    :param target: Composite DAE block that receives the component equations.
    :param source: Component block whose states and equations are appended.
    :param substitutions: Open component ports and their connected signals.
    :return: None.
    """
    target.state_vars.extend(source.state_vars)
    target.diff_vars.extend(source.diff_vars)
    target.algebraic_vars.extend(source.algebraic_vars)
    for equation in source.state_eqs:
        target.state_eqs.append(equation.subs(substitutions))
    for equation in source.algebraic_eqs:
        target.algebraic_eqs.append(equation.subs(substitutions))
    target.event_dict.update(source.event_dict)
    target.procedural_logic.extend(source.procedural_logic)
    for variable, expression in source.init_eqs.items():
        if variable in substitutions:
            pass
        else:
            target.init_eqs[variable] = expression.subs(substitutions)


def initial_component_value(block: Block, variable: Var) -> float:
    """Read a construction-time constant required to connect TGOV4 stages.

    :param block: Component block containing the initialization equation.
    :param variable: Initialized algebraic signal to read.
    :return: Constant initial value.
    :raises ValueError: The component signal has a nonconstant initialization.
    """
    expression: Expr = block.init_eqs[variable]
    if isinstance(expression, Const) and isinstance(expression.value, (int, float)):
        return float(expression.value)
    else:
        raise ValueError('TGOV4 thermal composition requires constant stage initial values')


def build_tgov4_thermal_train(
        vf: VarFactory,
        name: str,
        control_valves: tuple[Tgov4ValveSettings, ...] | None = None,
        intercept_valves: tuple[Tgov4ValveSettings, ...] | None = None,
        steam_settings: Tgov4SteamSettings | None = None,
        boiler_settings: Tgov4BoilerSettings | None = None,
        governor_settings: Tgov4GovernorSettings | None = None,
        relay_settings: Tgov4RelaySettings | None = None,
        control_signal: float | None = None,
        intercept_signal: float | None = None,
) -> RmsModelTemplate:
    """Connect TGOV4 valve banks, steam train, and boiler pressure dynamics.

    The compensated speed path creates separate CV and IV control signals;
    this host connects them to the valve banks and closes the steam/boiler
    feedback paths while exposing mechanical power to its generator host.

    :param vf: Variable factory owning the connected DAE graph.
    :param name: Unique TGOV4 instance name.
    :param control_valves: Ordered settings for up to four control valves.
    :param intercept_valves: Ordered settings for up to two intercept valves.
    :param steam_settings: Turbine steam constants and initial pressure.
    :param boiler_settings: Boiler controller, storage and fuel-delay constants.
    :param relay_settings: Optional PLU/EVA filters and solved machine measurements.
    :param control_signal: Optional solved common control-valve signal.
    :param intercept_signal: Optional solved common intercept-valve signal.
    :return: Generator-compatible thermal chain with a speed-deviation input.
    :raises ValueError: Stage initialization values cannot be consistently connected.
    """
    selected_steam: Tgov4SteamSettings = (
        Tgov4SteamSettings() if steam_settings is None else steam_settings
    )
    selected_boiler: Tgov4BoilerSettings = (
        Tgov4BoilerSettings(
            initial_steam_flow=(selected_steam.kcal * selected_steam.initial_control_flow
                                * selected_steam.initial_boiler_pressure),
            initial_boiler_pressure=selected_steam.initial_boiler_pressure,
        ) if boiler_settings is None else boiler_settings
    )
    selected_governor: Tgov4GovernorSettings = (
        Tgov4GovernorSettings() if governor_settings is None else governor_settings
    )
    selected_control_valves: tuple[Tgov4ValveSettings, ...] = (
        (Tgov4ValveSettings(initial_position=0.8),)
        if control_valves is None else control_valves
    )
    selected_intercept_valves: tuple[Tgov4ValveSettings, ...] = (
        (Tgov4ValveSettings(initial_position=1.0),)
        if intercept_valves is None else intercept_valves
    )
    relay_block: Block | None = None
    if relay_settings is None:
        pass
    else:
        relay_block = build_tgov4_relay_monitors(
            vf, name + '_Relays', relay_settings,
        ).block
    cv_template: RmsModelTemplate = build_tgov4_valve_bank(
        vf, name + '_CV', selected_control_valves, control_signal, 4,
        None if relay_block is None else relay_block.out_vars[4],
        0.0 if relay_settings is None else relay_settings.cv_close_start,
        10.0 if relay_settings is None else relay_settings.cv_close_rate,
        None if relay_settings is None else relay_settings.cv_closed_times[
            :len(selected_control_valves)
        ],
    )
    iv_template: RmsModelTemplate = build_tgov4_valve_bank(
        vf, name + '_IV', selected_intercept_valves, intercept_signal, 2,
        None if relay_block is None else relay_block.out_vars[6],
        0.0 if relay_settings is None else relay_settings.iv_close_start,
        10.0 if relay_settings is None else relay_settings.iv_close_rate,
        None if relay_settings is None else relay_settings.iv_closed_times[
            :len(selected_intercept_valves)
        ],
    )
    cv_block: Block = cv_template.block
    iv_block: Block = iv_template.block
    cv_initial: float = initial_component_value(cv_block, cv_block.out_vars[0])
    iv_initial: float = initial_component_value(iv_block, iv_block.out_vars[0])
    if not math.isclose(
            cv_initial, selected_steam.initial_control_flow, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError('TGOV4 CV-bank and steam initial flow values must match')
    elif not math.isclose(
            iv_initial, selected_steam.initial_intercept_flow, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError('TGOV4 IV-bank and steam initial flow values must match')
    elif not math.isclose(
            selected_steam.initial_boiler_pressure,
            selected_boiler.initial_boiler_pressure, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError('TGOV4 steam and boiler initial pressures must match')
    else:
        pass
    initial_hp_flow: float = (
        selected_steam.kcal * cv_initial * selected_steam.initial_boiler_pressure
    )
    if boiler_settings is not None and not math.isclose(
            initial_hp_flow, selected_boiler.initial_steam_flow,
            rel_tol=0.0, abs_tol=1e-9):
        raise ValueError('TGOV4 boiler and steam initial flow values must match')
    else:
        pass
    resolved_steam: Tgov4SteamSettings = Tgov4SteamSettings(
        selected_steam.kcal, selected_steam.t4, selected_steam.k1,
        selected_steam.t5, selected_steam.k2, selected_steam.t6,
        selected_steam.prmax, cv_initial, iv_initial,
        selected_steam.initial_boiler_pressure,
    )
    resolved_boiler: Tgov4BoilerSettings = Tgov4BoilerSettings(
        selected_boiler.kp, selected_boiler.ki, selected_boiler.tfuel,
        selected_boiler.tfd1, selected_boiler.tfd2, selected_boiler.kb,
        selected_boiler.cb, initial_hp_flow,
        selected_steam.initial_boiler_pressure,
    )
    steam_template: RmsModelTemplate = build_tgov4_steam_train(
        vf, name + '_Steam', resolved_steam,
    )
    boiler_template: RmsModelTemplate = build_tgov4_boiler(
        vf, name + '_Boiler', resolved_boiler,
    )
    steam_block: Block = steam_template.block
    boiler_block: Block = boiler_template.block
    governor_template: RmsModelTemplate = build_tgov4_speed_control(
        vf, name + '_Governor', selected_governor,
        initial_component_value(cv_block, cv_block.in_vars[0]),
        initial_component_value(iv_block, iv_block.in_vars[0]),
    )
    governor_block: Block = governor_template.block
    steam_connections: dict[Var, Expr] = dict((
        (steam_block.in_vars[0], cv_block.out_vars[0]),
        (steam_block.in_vars[1], iv_block.out_vars[0]),
        (steam_block.in_vars[2], boiler_block.out_vars[0]),
    ))
    boiler_connections: dict[Var, Expr] = dict((
        (boiler_block.in_vars[0], steam_block.out_vars[1]),
    ))
    relay_connections: dict[Var, Expr] = dict()
    if relay_settings is not None:
        mechanical_initial: float = initial_component_value(steam_block, steam_block.out_vars[0])
        reheat_initial: float = initial_component_value(steam_block, steam_block.state_vars[1])
        if not math.isclose(
                mechanical_initial, relay_settings.initial_generator_power,
                rel_tol=0.0, abs_tol=1e-9):
            raise ValueError('TGOV4 relay power must match the steam-train initial power')
        elif not math.isclose(
                reheat_initial, relay_settings.initial_reheat_pressure,
                rel_tol=0.0, abs_tol=1e-9):
            raise ValueError('TGOV4 relay reheat pressure must match the steam initial state')
        else:
            pass
        relay_connections = dict((
            (relay_block.in_vars[1], steam_block.out_vars[0]),
            (relay_block.in_vars[2], steam_block.state_vars[1]),
        ))
    else:
        pass
    cv_command: Expr = governor_block.out_vars[0]
    iv_command: Expr = governor_block.out_vars[1]
    cv_connections: dict[Var, Expr] = dict((
        (cv_block.in_vars[0], cv_command),
    ))
    iv_connections: dict[Var, Expr] = dict((
        (iv_block.in_vars[0], iv_command),
    ))
    root: Block = Block(name=name)
    append_tgov4_component(root, governor_block, dict())
    if relay_block is None:
        pass
    else:
        append_tgov4_component(root, relay_block, relay_connections)
    append_tgov4_component(root, cv_block, cv_connections)
    append_tgov4_component(root, iv_block, iv_connections)
    append_tgov4_component(root, steam_block, steam_connections)
    append_tgov4_component(root, boiler_block, boiler_connections)
    if relay_block is None:
        root.in_vars = [governor_block.in_vars[0]]
        root.out_vars = [steam_block.out_vars[0]]
    else:
        root.in_vars = [governor_block.in_vars[0], relay_block.in_vars[0]]
        root.out_vars = [steam_block.out_vars[0]] + list(relay_block.out_vars)
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.block = root
    template.tpe = DeviceType.GeneratorDevice
    template.comment = 'PSS/E TGOV4 valve, steam, and boiler thermal chain'
    return template
