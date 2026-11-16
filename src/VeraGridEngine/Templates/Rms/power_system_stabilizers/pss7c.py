# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""IEEE 421.5 PSS7C dual-input stabilizer realization."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ramp_tracking_stabilizer import RampStabilizerParameters
from VeraGridEngine.Utils.Symbolic.symbolic import Comparison, CmpOp, Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import PickupDropoffLogic
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_pss7c_template(vf: VarFactory, name: str, parameters: RampStabilizerParameters,
                          canonical_gains: tuple[float, float, float, float, float],
                          canonical_times: tuple[float, float, float, float],
                          canonical_stage_gains: tuple[float, float], pss_on: float,
                          pss_off: float, xcomp: float, tcomp: float) -> RmsModelTemplate:
    """Build the PSS7C dual-input ramp tracker and canonical phase compensator.

    The input paths follow PSS/E 35.2 section 3.14 through KS1. Their summed
    signal passes through the source ramp-tracking order, then the four-state
    canonical realization shared with IEEE PSS6C. The PSS/E output hysteresis
    gates the clipped stabilizing signal using generator active power.

    :param vf: Shared symbolic variable factory.
    :param name: Unique runtime model name.
    :param parameters: Washout, transducer, ramp-order and output-limit values.
    :param canonical_gains: Ordered K0 through K4 gains.
    :param canonical_times: Ordered TI1 through TI4 time constants.
    :param canonical_stage_gains: Ordered KI3 and KI4 state-path gains.
    :param pss_on: Positive power threshold enabling output hysteresis, or negative to disable it.
    :param pss_off: Power threshold disabling output hysteresis.
    :param xcomp: Reactance used by the optional compensated-frequency path.
    :param tcomp: Positive compensated-frequency washout time.
    :return: Native PSS7C template with two selected inputs and machine power.
    :raises ValueError: Invalid filter orders, gains, time constants or limits.
    """
    coefficient_groups: tuple[tuple[float, ...], ...] = (
        parameters.washout_times, parameters.transducer_times,
        (parameters.ks1, parameters.ks2, parameters.ks3, parameters.t8, parameters.t9,
         parameters.upper, parameters.lower, pss_on, pss_off, xcomp, tcomp),
        parameters.input_limits[0], parameters.input_limits[1],
        canonical_gains, canonical_times, canonical_stage_gains,
    )
    if not all(math.isfinite(value) for group in coefficient_groups for value in group):
        raise ValueError('PSS7C coefficients must be finite')
    elif min(parameters.ramp_m, parameters.ramp_n) < 0 or parameters.ramp_m * parameters.ramp_n > 8:
        raise ValueError('PSS7C ramp filter orders must be nonnegative and M*N <= 8')
    elif min(parameters.washout_times[0], parameters.washout_times[2]) <= 0 or min(parameters.washout_times[1], parameters.washout_times[3]) < 0 or min(parameters.transducer_times) < 0:
        raise ValueError('PSS7C first washouts must be positive; optional washouts and transducers must be nonnegative')
    elif parameters.t9 <= 0 or parameters.t8 < 0 or min(canonical_times) <= 0 or tcomp <= 0:
        raise ValueError('PSS7C ramp, canonical and compensated-frequency times must be positive')
    elif parameters.lower >= parameters.upper or any(low >= high for low, high in parameters.input_limits):
        raise ValueError('PSS7C input and output limits must be ordered')
    elif pss_on == 0 or (pss_on > 0 and pss_off >= pss_on):
        raise ValueError('PSS7C output logic requires PSSON < 0 or PSSON > PSSOFF')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    input1: Var = control.input('Signal1Pu', Const(0.0))
    input2: Var = control.input('Signal2Pu', Const(0.0))
    machine_power: Var = control.input('MachinePowerPu', Const(0.0))

    # Clip each measured channel before its independent washout and transducer chain.
    path1_signal: Expr = sym.hard_sat(input1,
        control.parameter('VSL1MIN', parameters.input_limits[0][0]),
        control.parameter('VSL1MAX', parameters.input_limits[0][1]))
    path2_signal: Expr = sym.hard_sat(input2,
        control.parameter('VSL2MIN', parameters.input_limits[1][0]),
        control.parameter('VSL2MAX', parameters.input_limits[1][1]))
    tw1: Var = control.parameter('TW1', parameters.washout_times[0])
    kw2: Var = control.parameter('KW2', parameters.washout_times[1])
    tw3: Var = control.parameter('TW3', parameters.washout_times[2])
    tw4: Var = control.parameter('TW4', parameters.washout_times[3])
    first1: Var = control.washout('Signal1Washout1Pu', path1_signal, tw1,
        parameters.washout_times[0], Const(1.0), path1_signal)
    if parameters.washout_times[1] > 0.0:
        second1: Var = control.washout('Signal1Washout2Pu', first1, kw2,
            parameters.washout_times[1], Const(1.0), Const(0.0))
    else:
        second1 = first1
    first2: Var = control.washout('Signal2Washout1Pu', path2_signal, tw3,
        parameters.washout_times[2], Const(1.0), path2_signal)
    if parameters.washout_times[3] > 0.0:
        second2: Var = control.washout('Signal2Washout2Pu', first2, tw4,
            parameters.washout_times[3], Const(1.0), Const(0.0))
    else:
        second2 = first2
    t6: Var = control.parameter('T6', parameters.transducer_times[0])
    t7: Var = control.parameter('T7', parameters.transducer_times[1])
    path1: Var = control.lag('Signal1TransducerPu', second1, t6,
        parameters.transducer_times[0], Const(0.0))
    ks2: Var = control.parameter('KS2', parameters.ks2)
    path2: Var = control.lag('Signal2TransducerPu', ks2 * second2, t7,
        parameters.transducer_times[1], Const(0.0))

    # Cascade N copies of a lead and M-1 denominator lags, as specified by M/N.
    ks3: Var = control.parameter('KS3', parameters.ks3)
    t8: Var = control.parameter('T8', parameters.t8)
    t9: Var = control.parameter('T9', parameters.t9)
    tracked: Var = control.algebraic('RampInputPu', path1 + ks3 * path2, Const(0.0))
    active_ramp_states: int = 0
    repeat_index: int
    stage_index: int
    for repeat_index in range(parameters.ramp_n):
        if parameters.ramp_m > 0:
            tracked = control.lead_lag('RampLead' + str(repeat_index + 1) + 'Pu',
                tracked, t8, t9, parameters.t8, parameters.t9, Const(0.0))
            active_ramp_states += 1
            for stage_index in range(1, parameters.ramp_m):
                tracked = control.lag('RampLag' + str(repeat_index + 1) + '_' + str(stage_index) + 'Pu',
                    tracked, t9, parameters.t9, Const(0.0))
                active_ramp_states += 1
        else:
            pass

    # Preserve PSS/E's fixed eight ramp-state allocation; unused slots remain zero states.
    padding_index: int
    for padding_index in range(active_ramp_states, 8):
        padding_state: Var = vf.add_var('RampStatePadding' + str(padding_index + 1) + '_' + name)
        control.differential(padding_state, Const(0.0), Const(0.0))

    # The dual-input ramp tracker subtracts the conditioned second channel before KS1.
    damping_input: Var = control.algebraic('DampingInputPu', tracked - path2, Const(0.0))
    ks1: Var = control.parameter('KS1', parameters.ks1)
    canonical_input: Expr = ks1 * damping_input
    canonical_states: list[Var] = list()
    canonical_index: int
    for canonical_index in range(4):
        canonical_states.append(vf.add_var('CanonicalState' + str(canonical_index + 1) + '_' + name))
    k0: Var = control.parameter('K0', canonical_gains[0])
    k1: Var = control.parameter('K1', canonical_gains[1])
    k2: Var = control.parameter('K2', canonical_gains[2])
    k3: Var = control.parameter('K3', canonical_gains[3])
    k4: Var = control.parameter('K4', canonical_gains[4])
    ti1: Var = control.parameter('TI1', canonical_times[0])
    ti2: Var = control.parameter('TI2', canonical_times[1])
    ti3: Var = control.parameter('TI3', canonical_times[2])
    ti4: Var = control.parameter('TI4', canonical_times[3])
    ki3: Var = control.parameter('KI3', canonical_stage_gains[0])
    ki4: Var = control.parameter('KI4', canonical_stage_gains[1])
    canonical_feedback: Expr = canonical_states[0] + canonical_states[1] + canonical_states[2] + canonical_states[3]
    control.differential(canonical_states[0], (canonical_input - canonical_feedback) / ti1, Const(0.0))
    control.differential(canonical_states[1], canonical_states[0] / ti2, Const(0.0))
    control.differential(canonical_states[2], ki3 * canonical_states[1] / ti3, Const(0.0))
    control.differential(canonical_states[3], ki4 * canonical_states[2] / ti4, Const(0.0))
    canonical_output: Expr = (k0 * (canonical_input - canonical_feedback) + k1 * canonical_states[0] +
        k2 * canonical_states[1] + k3 * canonical_states[2] + k4 * canonical_states[3])
    pss_max: Var = control.parameter('VSTMAX', parameters.upper)
    pss_min: Var = control.parameter('VSTMIN', parameters.lower)
    limited_output: Var = control.algebraic('LimitedOutputPu',
        sym.hard_sat(canonical_output, pss_min, pss_max), Const(0.0))
    pss_on_parameter: Var = control.parameter('PSSON', pss_on)
    pss_off_parameter: Var = control.parameter('PSSOFF', pss_off)

    # PSSON<0 bypasses the output gate; otherwise the generator power controls its hysteresis.
    if pss_on > 0.0:
        enabled: Var = vf.add_var('PssOutputEnabled_' + name)
        turn_on: Expr = Comparison(machine_power, CmpOp.GE, pss_on_parameter).to_expression()
        remain_on: Expr = Comparison(machine_power, CmpOp.GT, pss_off_parameter).to_expression()
        initially_enabled: Expr = turn_on
        control.block.mode_dict[enabled] = turn_on
        control.block.init_eqs[enabled] = initially_enabled
        control.block.procedural_logic.append(PickupDropoffLogic(
            output_var_name=enabled.name,
            bool_expr=(Const(1.0) - enabled) * turn_on + enabled * remain_on,
            pickup_delay_expr=Const(0.0), drop_delay_expr=Const(0.0),
            name='PSS7C electrical-power output hysteresis ' + name))
        output: Var = control.algebraic('VsPu', limited_output * enabled, Const(0.0))
    else:
        output = limited_output

    # Selector 7 is rejected at import; retain its allocated washout state without inventing bus signals.
    xcomp_parameter: Var = control.parameter('XCOMP', xcomp)
    comp_time: Var = control.parameter('TCOMP', tcomp)
    control.washout('CompensatedFrequencyWashoutPu', xcomp_parameter * Const(0.0), comp_time,
        tcomp, Const(1.0), Const(0.0))
    # Preserve the documented fixed nineteen-state allocation when zero-time stages bypass memories.
    state_padding_index: int
    for state_padding_index in range(len(control.block.state_vars), 19):
        state_padding: Var = vf.add_var('StatePadding' + str(state_padding_index + 1) + '_' + name)
        control.differential(state_padding, Const(0.0), Const(0.0))
    return control.finish((output,), 'IEEE PSS7C dual-input stabilizer with canonical phase compensation')
