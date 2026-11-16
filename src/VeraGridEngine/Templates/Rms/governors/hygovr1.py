# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Fourth-order lead-lag hydro governor with a rigid water column."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.procedural_logic import flipflop


class Hygovr1Parameters:
    """PSS/E HYGOVR1 settings on the turbine base."""

    __slots__ = (
        'db1_hz', 'err_pu', 'td', 'lead_lag_times', 'kp', 'droop', 'tt', 'kg',
        'tp', 'velocity_open', 'velocity_close', 'gate_max', 'gate_min',
        'db2_mw', 'tw', 'at', 'damping', 'no_load_flow', 'turbine_base_mw',
        'nominal_frequency', 'initial_power',
    )

    def __init__(
            self,
            db1_hz: float = 0.0,
            err_pu: float = 0.0,
            td: float = 0.05,
            lead_lag_times: tuple[float, float, float, float, float, float, float, float] = (
                0.0, 0.1, 0.0, 0.1, 0.0, 0.1, 0.0, 0.1,
            ),
            kp: float = 1.0,
            droop: float = 0.05,
            tt: float = 0.0,
            kg: float = 1.0,
            tp: float = 0.05,
            velocity_open: float = 0.2,
            velocity_close: float = -0.2,
            gate_max: float = 1.0,
            gate_min: float = 0.01,
            db2_mw: float = 0.0,
            tw: float = 1.0,
            at: float = 1.0,
            damping: float = 0.0,
            no_load_flow: float = 0.08,
            turbine_base_mw: float = 100.0,
            nominal_frequency: float = 50.0,
            initial_power: float = 0.5,
    ) -> None:
        """Store source values and conversion bases.

        :param db1_hz: Intentional speed deadband in Hz.
        :param err_pu: Deadband hysteresis in per-unit speed.
        :param td: Speed input filter time in seconds.
        :param lead_lag_times: Ordered lead/lag times for four compensation stages.
        :param kp: Governor integrator gain.
        :param droop: Permanent droop on the turbine base.
        :param tt: Electrical-power feedback filter time in seconds.
        :param kg: Gate servo gain.
        :param tp: Gate servo time in seconds.
        :param velocity_open: Maximum gate opening rate in pu/s.
        :param velocity_close: Maximum gate closing rate in pu/s.
        :param gate_max: Maximum integrator gate position.
        :param gate_min: Minimum integrator gate position.
        :param db2_mw: Unintentional gate deadband width in MW.
        :param tw: Water-column time in seconds.
        :param at: Turbine gain.
        :param damping: Turbine damping coefficient.
        :param no_load_flow: No-load turbine flow.
        :param turbine_base_mw: Positive turbine base from TRATE or machine MBASE.
        :param nominal_frequency: System nominal frequency in Hz.
        :param initial_power: Initial turbine power in pu.
        """
        self.db1_hz: float = db1_hz
        self.err_pu: float = err_pu
        self.td: float = td
        self.lead_lag_times: tuple[float, float, float, float, float, float, float, float] = lead_lag_times
        self.kp: float = kp
        self.droop: float = droop
        self.tt: float = tt
        self.kg: float = kg
        self.tp: float = tp
        self.velocity_open: float = velocity_open
        self.velocity_close: float = velocity_close
        self.gate_max: float = gate_max
        self.gate_min: float = gate_min
        self.db2_mw: float = db2_mw
        self.tw: float = tw
        self.at: float = at
        self.damping: float = damping
        self.no_load_flow: float = no_load_flow
        self.turbine_base_mw: float = turbine_base_mw
        self.nominal_frequency: float = nominal_frequency
        self.initial_power: float = initial_power


def build_hygovr1_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: Hygovr1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the PSS/E HYGOVR1 speed, gate and hydro-turbine paths.

    The source diagram has four lead-lag stages, a bounded KP/s governor,
    filtered Pelec or gate feedback, a rate-limited servo, DB2 gate deadband,
    and the rigid-water-column equations. PSS/E provides no N_GV curve data;
    its source layout therefore uses the identity gate curve Pgv=Gv. A positive
    DB2 narrows the usable positive gate by half its turbine-base width.

    :param vf: Shared symbolic factory.
    :param name: Optional unique instance name.
    :param parameters: PSS/E coefficients and machine/turbine conversion bases.
    :return: Native governor with three inputs and mechanical-power/gate/flow outputs.
    :raises ValueError: Nonfinite or physically singular coefficients.
    """
    p: Hygovr1Parameters = Hygovr1Parameters() if parameters is None else parameters
    times: tuple[float, ...] = (p.td, p.tt, p.tp, p.tw, *p.lead_lag_times)
    scalars: tuple[float, ...] = (
        p.db1_hz, p.err_pu, p.kp, p.droop, p.kg, p.velocity_open,
        p.velocity_close, p.gate_max, p.gate_min, p.db2_mw, p.at,
        p.damping, p.no_load_flow, p.turbine_base_mw, p.nominal_frequency,
        p.initial_power,
    )
    db2_pu: float = p.db2_mw / p.turbine_base_mw
    if not all(math.isfinite(value) for value in (*times, *scalars)):
        raise ValueError('HYGOVR1 coefficients must be finite')
    elif min(times) < 0.0 or p.droop <= 0.0 or p.kp < 0.0 or p.kg < 0.0:
        raise ValueError('HYGOVR1 times must be nonnegative; gains and droop are invalid')
    elif p.tw <= 0.0 or p.at <= 0.0 or p.turbine_base_mw <= 0.0 or p.nominal_frequency <= 0.0:
        raise ValueError('HYGOVR1 water time, turbine gain and bases must be positive')
    elif p.gate_min <= db2_pu / 2.0 or p.gate_min >= p.gate_max or p.velocity_open < 0.0 or p.velocity_close > 0.0:
        raise ValueError('HYGOVR1 gate limits or velocity directions are invalid')
    elif p.db1_hz < 0.0 or p.err_pu < 0.0 or p.db2_mw < 0.0 or p.damping < 0.0:
        raise ValueError('HYGOVR1 deadbands and damping must be nonnegative')
    elif p.initial_power < 0.0 or p.no_load_flow < 0.0:
        raise ValueError('HYGOVR1 initial power and no-load flow must be nonnegative')
    else:
        pass
    if p.gate_max <= db2_pu / 2.0:
        raise ValueError('HYGOVR1 maximum gate must exceed half the DB2 deadband')
    else:
        pass
    for stage_index in range(4):
        lead_time: float = p.lead_lag_times[2 * stage_index]
        lag_time: float = p.lead_lag_times[2 * stage_index + 1]
        if lag_time == 0.0 and lead_time != 0.0:
            raise ValueError('HYGOVR1 zero lag requires zero lead in each stage')
        else:
            pass

    model_name: str = 'HYGOVR1' if name is None else name
    c: ControlRealization = ControlRealization(vf, model_name)
    pm0: Var = c.parameter('Pm0Pu', p.initial_power)
    initial_flow_value: float = p.initial_power / p.at + p.no_load_flow
    initial_gate_value: float = initial_flow_value + db2_pu / 2.0
    if initial_flow_value <= 0.0 or initial_gate_value < p.gate_min or initial_gate_value > p.gate_max:
        raise ValueError('HYGOVR1 initial flow/gate is outside its positive operating domain')
    else:
        pass
    initial_flow: Expr = pm0 / p.at + Const(p.no_load_flow)
    initial_gate: Expr = initial_flow + Const(db2_pu / 2.0)
    initial_feedback: Expr = pm0 if p.tt > 0.0 else initial_flow
    speed: Var = c.input('OmegaPu', Const(1.0))
    reference: Var = c.input('GovernorReferencePu', Const(p.droop) * initial_feedback)
    pelec: Var = c.input('ElectricalPowerPu', pm0)

    speed_error: Expr = Const(1.0) - speed
    if p.db1_hz > 0.0 or p.err_pu > 0.0:
        threshold: Const = Const(p.db1_hz / p.nominal_frequency)
        hysteresis: Const = Const(p.err_pu)
        positive_mode: Var = vf.add_var('PositiveSpeedDeadbandMode_' + model_name)
        negative_mode: Var = vf.add_var('NegativeSpeedDeadbandMode_' + model_name)
        c.block.mode_dict[positive_mode] = Const(0.0)
        c.block.mode_dict[negative_mode] = Const(0.0)
        c.block.procedural_logic.append(flipflop(
            boolset=sym.heaviside(speed_error - threshold - hysteresis),
            boolreset=Const(1.0) - sym.heaviside(speed_error - threshold),
            output=positive_mode, name='PositiveSpeedDeadband_' + model_name,
        ))
        c.block.procedural_logic.append(flipflop(
            boolset=sym.heaviside(-threshold - hysteresis - speed_error),
            boolreset=Const(1.0) - sym.heaviside(-threshold - speed_error),
            output=negative_mode, name='NegativeSpeedDeadband_' + model_name,
        ))
        conditioned_speed: Expr = (
            positive_mode * (speed_error - threshold)
            + negative_mode * (speed_error + threshold)
        )
    else:
        conditioned_speed = speed_error
    filtered_speed: Var = c.lag(
        'InputSpeedPu', conditioned_speed, c.parameter('TD', p.td), p.td, Const(0.0),
    )
    lead_lag_output: Expr = filtered_speed
    for stage_index in range(4):
        lead_value: float = p.lead_lag_times[2 * stage_index]
        lag_value: float = p.lead_lag_times[2 * stage_index + 1]
        lead_lag_output = c.lead_lag(
            'LeadLag' + str(stage_index + 1) + 'Pu', lead_lag_output,
            c.parameter('T' + str(stage_index * 2 + 1), lead_value),
            c.parameter('T' + str(stage_index * 2 + 2), lag_value),
            lead_value, lag_value, Const(0.0),
        )

    gate: Var = vf.add_var('GateStatePu_' + model_name)
    if db2_pu > 0.0:
        gate_after_deadband: Expr = sym.max(gate - db2_pu / 2.0, Const(0.0))
    else:
        gate_after_deadband = gate
    effective_gate: Var = c.algebraic(
        'EffectiveGatePu', gate_after_deadband, initial_flow,
    )
    if p.tt > 0.0:
        power_feedback: Expr = c.lag(
            'GeneratorPowerPu', pelec, c.parameter('TT', p.tt), p.tt, pm0,
        )
    else:
        power_feedback = effective_gate
        c.differential(
            vf.add_var('GeneratorPowerPu_' + model_name), Const(0.0), pm0,
        )
    governor_error: Expr = reference + lead_lag_output - p.droop * power_feedback
    cv: Var = c.differential(
        vf.add_var('GovernorOutputPu_' + model_name), p.kp * governor_error,
        initial_gate, c.parameter('GMIN', p.gate_min), c.parameter('GMAX', p.gate_max),
    )
    valve_speed: Var = c.lag(
        'ValveSpeedPuPerSecond', p.kg * (cv - gate), c.parameter('TP', p.tp), p.tp,
        Const(0.0), output=vf.add_var('ValveSpeedPuPerSecond_' + model_name),
    )
    bounded_speed: Var = c.algebraic(
        'BoundedValveSpeedPuPerSecond',
        sym.hard_sat(valve_speed, p.velocity_close, p.velocity_open), Const(0.0),
    )
    c.differential(
        gate, bounded_speed, initial_gate,
        c.parameter('PMIN', p.gate_min), c.parameter('PMAX', p.gate_max),
    )
    flow: Var = vf.add_var('TurbineFlowPu_' + model_name)
    head: Var = c.algebraic(
        'TurbineHeadPu', (flow / effective_gate) ** Const(2.0), Const(1.0),
    )
    c.differential(
        flow, (Const(1.0) - head) / c.parameter('TW', p.tw), initial_flow,
    )
    mechanical_power: Var = c.algebraic(
        'PmPu', p.at * (flow - p.no_load_flow) * head
        + p.damping * effective_gate * speed_error, pm0,
    )
    return c.finish(
        (mechanical_power, effective_gate, flow),
        'PSS/E HYGOVR1 fourth-order lead-lag hydro turbine governor',
    )
