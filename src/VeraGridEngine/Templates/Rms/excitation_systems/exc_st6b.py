# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the CGMES ExcST6B exciter."""

import math
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import ExcST6BOELselectorKind
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_exc_s_t6_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        ilr: float = 4.164,
        k1: bool = True,
        kcl: float = 1.0577,
        kff: float = 1.0,
        kg: float = 1.0,
        kia: float = 45.094,
        klr: float = 17.33,
        km: float = 1.0,
        kpa: float = 18.038,
        kvd: float = 0.0,
        oelin: ExcST6BOELselectorKind = ExcST6BOELselectorKind.noOELinput,
        tg: float = 0.02,
        ts: float = 0.0,
        tvd: float = 0.0,
        vamax: float = 4.81,
        vamin: float = -3.85,
        vilim: bool = True,
        vimax: float = 10.0,
        vimin: float = -10.0,
        vmult: bool = True,
        vrmax: float = 4.81,
        vrmin: float = -3.85,
        xc: float = 0.05,
) -> RmsModelTemplate:
    """Build the ST6B PID, feedback, current limiter, gate, and output lag.

    :param vfactory: Symbol factory for this instance.
    :param name: Optional unique instance name.
    :param ilr: Field-current limiter reference.
    :param k1: Select field-current feedback when true; otherwise use LaddIfd.
    :param kcl: Field-current limiter conversion gain.
    :param kff: Regulator feed-forward gain.
    :param kg: Exciter-output feedback gain.
    :param kia: PID integral gain.
    :param klr: Field-current limiter gain.
    :param km: Main regulator gain.
    :param kpa: PID proportional gain.
    :param kvd: Derivative-path numerator time coefficient.
    :param oelin: OEL insertion point relative to the UEL gate.
    :param tg: Feedback-lag time constant.
    :param ts: Rectifier firing time constant.
    :param tvd: Derivative-path lag time constant.
    :param vamax: PID upper limit.
    :param vamin: PID lower limit.
    :param vilim: Enable the field-current limiter.
    :param vimax: Current-limiter upper capability.
    :param vimin: Current-limiter lower capability.
    :param vmult: Multiply the gated regulator output by terminal voltage.
    :param vrmax: Regulator upper limit.
    :param vrmin: Regulator lower limit.
    :param xc: Load-compensation coefficient applied to LaddIfd.
    :return: ST6B equation graph with canonical RDF event names.
    """
    settings: tuple[float, ...] = (
        ilr, kcl, kff, kg, kia, klr, km, kpa, kvd, tg, ts, tvd, vamax,
        vamin, vimax, vimin, vrmax, vrmin, xc,
    )
    if not all((
            math.isfinite(ilr), math.isfinite(kcl), math.isfinite(kff), math.isfinite(kg),
            math.isfinite(kia), math.isfinite(klr), math.isfinite(km), math.isfinite(kpa),
            math.isfinite(kvd), math.isfinite(tg), math.isfinite(ts), math.isfinite(tvd),
            math.isfinite(vamax), math.isfinite(vamin), math.isfinite(vimax),
            math.isfinite(vimin), math.isfinite(vrmax), math.isfinite(vrmin), math.isfinite(xc),
    )):
        raise ValueError('ExcST6B parameters must be finite')
    elif min(ilr, kcl, kg, kia, klr, km, kpa, kvd, tg, ts, tvd, xc) < 0.0:
        raise ValueError('ExcST6B gains and time constants must be nonnegative')
    elif vamax <= vamin or vimax <= vimin or vrmax <= vrmin:
        raise ValueError('ExcST6B limiter bounds must be ordered')
    else:
        pass
    template_name: str = 'ExcST6B' if name is None else name
    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ilr_event: Var = builder.parameter('ExcST6B.ilr', ilr)
    kcl_event: Var = builder.parameter('ExcST6B.kcl', kcl)
    kff_event: Var = builder.parameter('ExcST6B.kff', kff)
    kg_event: Var = builder.parameter('ExcST6B.kg', kg)
    kia_event: Var = builder.parameter('ExcST6B.kia', kia)
    klr_event: Var = builder.parameter('ExcST6B.klr', klr)
    km_event: Var = builder.parameter('ExcST6B.km', km)
    kpa_event: Var = builder.parameter('ExcST6B.kpa', kpa)
    kvd_event: Var = builder.parameter('ExcST6B.kvd', kvd)
    tg_event: Var = builder.parameter('ExcST6B.tg', tg)
    ts_event: Var = builder.parameter('ExcST6B.ts', ts)
    tvd_event: Var = builder.parameter('ExcST6B.tvd', tvd)
    vamax_event: Var = builder.parameter('ExcST6B.vamax', vamax)
    vamin_event: Var = builder.parameter('ExcST6B.vamin', vamin)
    vimax_event: Var = builder.parameter('ExcST6B.vimax', vimax)
    vimin_event: Var = builder.parameter('ExcST6B.vimin', vimin)
    vrmax_event: Var = builder.parameter('ExcST6B.vrmax', vrmax)
    vrmin_event: Var = builder.parameter('ExcST6B.vrmin', vrmin)
    xc_event: Var = builder.parameter('ExcST6B.xc', xc)
    if oelin == ExcST6BOELselectorKind.noOELinput:
        oelin_code: float = 0.0
    elif oelin == ExcST6BOELselectorKind.beforeUEL:
        oelin_code = 1.0
    else:
        oelin_code = 2.0
    oelin_event: Var = builder.parameter('ExcST6B.oelin', oelin_code)
    k1_event: Var = builder.parameter('ExcST6B.k1', 1.0 if k1 is True else 0.0)
    vilim_event: Var = builder.parameter('ExcST6B.vilim', 1.0 if vilim is True else 0.0)
    vmult_event: Var = builder.parameter('ExcST6B.vmult', 1.0 if vmult is True else 0.0)
    # The host supplies machine and limiter signals; machine ports are composed while external limiter sources remain open.
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('VsPu', Const(0.0))
    oel: Var = builder.input('OelPu', Const(0.0))
    uel: Var = builder.input('UelPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(1.0))
    load_compensating_current: Var = builder.input('LaddIfdPu', Const(0.0))
    # OEL is an upper gate and UEL is a lower gate; oelin selects their order before the PID.
    raw_error: Expr = reference + stabilizer - terminal_voltage
    if oelin == ExcST6BOELselectorKind.beforeUEL:
        oel_limited_error: Expr = sym.min(raw_error, oel)
        voltage_error: Expr = sym.max(oel_limited_error, uel)
    elif oelin == ExcST6BOELselectorKind.afterUEL:
        uel_limited_error: Expr = sym.max(raw_error, uel)
        voltage_error = sym.min(uel_limited_error, oel)
    else:
        voltage_error = sym.max(raw_error, uel)
    integral_state: Var = vfactory.add_var(f'VoltageIntegralPu_{template_name}')
    derivative_output: Expr = Const(0.0)
    if tvd > 0.0:
        derivative_memory: Var = builder.lag(
            'DerivativeMemoryPu', voltage_error, tvd_event, tvd, voltage_error
        )
        derivative_output = kvd_event / tvd_event * (voltage_error - derivative_memory)
    else:
        pass
    raw_pid: Expr = kpa_event * voltage_error + integral_state + derivative_output
    integrator: Var = builder.differential(
        integral_state,
        kia_event * voltage_error,
        Const(0.0),
        vamin_event - kpa_event * voltage_error - derivative_output,
        vamax_event - kpa_event * voltage_error - derivative_output,
    )
    pid_output: Var = builder.algebraic(
        'PIDOutputPu', sym.hard_sat(raw_pid, vamin_event, vamax_event), Const(0.0)
    )
    # The published ST6B realization combines feed-forward, main gain, and lagged field feedback.
    feedback_output: Var = vfactory.add_var(f'FieldFeedbackPu_{template_name}')
    field_output: Var = vfactory.add_var(f'EfdPu_{template_name}')
    feedback_state: Var = builder.lag(
        'FeedbackPu', kg_event * field_output, tg_event, tg, Const(0.0), output=feedback_output
    )
    regulator_demand: Expr = (pid_output - feedback_state) * km_event + pid_output * kff_event
    regulator: Var = builder.algebraic(
        'RegulatorPu', sym.hard_sat(regulator_demand, vrmin_event, vrmax_event), Const(0.0)
    )
    if k1 is True:
        current_feedback: Expr = field_current
    else:
        current_feedback = load_compensating_current
    current_limit: Expr = (ilr_event * kcl_event - current_feedback) * klr_event
    if vilim is True:
        gated_regulator: Expr = sym.min(regulator, sym.hard_sat(current_limit, vimin_event, vimax_event))
    else:
        gated_regulator = regulator
    if vmult is True:
        multiplier: Expr = terminal_voltage
    else:
        multiplier = Const(1.0)
    field_demand: Expr = gated_regulator * multiplier + xc_event * load_compensating_current
    field_state: Var = builder.lag(
        'EfdPu', field_demand, ts_event, ts, Const(1.0), output=field_output
    )
    template: RmsModelTemplate = builder.finish(
        (field_state, regulator),
        'CGMES ExcST6B PID static exciter with field-current limiting and feedback',
    )
    # Keep the canonical RDF properties as runtime events for inspection and parameter updates.
    template.block = builder.block
    return template
