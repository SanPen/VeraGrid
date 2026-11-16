# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcSK Slovakian excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcSKParameters:
    """Canonical ExcSK parameter values used by its sourced block diagram."""

    __slots__ = (
        'efdmax', 'efdmin', 'emax', 'emin', 'k', 'k1', 'k2', 'kc', 'kce',
        'kd', 'kgob', 'kp', 'kqi', 'kqob', 'kqp', 'nq', 'qconoff', 'qz',
        'remote', 'sbase', 'tc', 'te', 'ti', 'tp', 'tr', 'uimax', 'uimin',
        'urmax', 'urmin', 'vtmax', 'vtmin', 'yp',
    )

    def __init__(
            self,
            efdmax: float = 5.0,
            efdmin: float = 0.0,
            emax: float = 5.0,
            emin: float = 0.0,
            k: float = 1.0,
            k1: float = 0.0,
            k2: float = 0.0,
            kc: float = 1.0,
            kce: float = 0.0,
            kd: float = 0.0,
            kgob: float = 0.0,
            kp: float = 0.0,
            kqi: float = 0.0,
            kqob: float = 0.0,
            kqp: float = 0.0,
            nq: float = 0.0,
            qconoff: bool = False,
            qz: float = 0.0,
            remote: bool = False,
            sbase: float = 100.0,
            tc: float = 0.0,
            te: float = 0.1,
            ti: float = 0.0,
            tp: float = 0.0,
            tr: float = 0.0,
            uimax: float = 10.0,
            uimin: float = -10.0,
            urmax: float = 10.0,
            urmin: float = -10.0,
            vtmax: float = 2.0,
            vtmin: float = 0.0,
            yp: float = 5.0,
    ) -> None:
        """Store model settings in their declared CGMES units.

        :param efdmax: Maximum final field-voltage output.
        :param efdmin: Minimum final field-voltage output.
        :param emax: Exciter output upper limit.
        :param emin: Exciter output lower limit.
        :param k: Exciter gain.
        :param k1: Underexcitation capability slope against mechanical power.
        :param k2: Underexcitation capability intercept.
        :param kc: PI voltage-regulator gain.
        :param kce: Rectifier regulation factor.
        :param kd: Exciter internal-reactance field-current feedback gain.
        :param kgob: Gain of the terminal-voltage bound path.
        :param kp: Underexcitation PI gain.
        :param kqi: Reactive-power controller integral gain.
        :param kqob: Reactive-power controller output gain.
        :param kqp: Reactive-power controller proportional gain.
        :param nq: Reactive-power controller deadband width.
        :param qconoff: Enable the secondary voltage controller.
        :param qz: Manual reactive-power setpoint.
        :param remote: Select the secondary controller's remote reference.
        :param sbase: Apparent-power base in MVA used to scale reactive power.
        :param tc: Voltage-regulator integral time constant.
        :param te: Exciter time constant.
        :param ti: Underexcitation integral time constant.
        :param tp: Underexcitation output lag time constant.
        :param tr: Terminal-voltage measurement filter time constant.
        :param uimax: Regulator error upper limit.
        :param uimin: Regulator error lower limit.
        :param urmax: Regulator output upper limit.
        :param urmin: Regulator output lower limit.
        :param vtmax: Terminal-voltage upper threshold.
        :param vtmin: Terminal-voltage lower threshold.
        :param yp: Underexcitation output upper limit.
        """
        self.efdmax: float = efdmax
        self.efdmin: float = efdmin
        self.emax: float = emax
        self.emin: float = emin
        self.k: float = k
        self.k1: float = k1
        self.k2: float = k2
        self.kc: float = kc
        self.kce: float = kce
        self.kd: float = kd
        self.kgob: float = kgob
        self.kp: float = kp
        self.kqi: float = kqi
        self.kqob: float = kqob
        self.kqp: float = kqp
        self.nq: float = nq
        self.qconoff: bool = qconoff
        self.qz: float = qz
        self.remote: bool = remote
        self.sbase: float = sbase
        self.tc: float = tc
        self.te: float = te
        self.ti: float = ti
        self.tp: float = tp
        self.tr: float = tr
        self.uimax: float = uimax
        self.uimin: float = uimin
        self.urmax: float = urmax
        self.urmin: float = urmin
        self.vtmax: float = vtmax
        self.vtmin: float = vtmin
        self.yp: float = yp


def exc_sk_rectifier_output(field_voltage: Expr, field_current: Expr, kce: Expr) -> Expr:
    """Apply the three-region controlled-rectifier characteristic.

    :param field_voltage: Internal exciter voltage ``VE``.
    :param field_current: Generator field current ``IFD``.
    :param kce: Canonical ExcSK rectifier regulation factor.
    :return: Rectified field voltage before EFD output clipping.
    """
    current_ratio: Expr = kce * field_current / sym.max(field_voltage, Const(1e-9))
    nonnegative_ratio: Expr = sym.max(current_ratio, Const(0.0))
    first_region: Expr = Const(1.0) - Const(0.577) * nonnegative_ratio
    second_region: Expr = sym.sqrt(
        sym.max(Const(0.75) - nonnegative_ratio * nonnegative_ratio, Const(0.0)),
    )
    third_region: Expr = Const(1.732) * (Const(1.0) - nonnegative_ratio)
    # Offset only the selectors so strict-positive Heaviside follows inclusive source bounds.
    rectifier_factor: Expr = (
        first_region * sym.heaviside(
            Const(0.433) - nonnegative_ratio + Const(1e-12),
        )
        + second_region * (
            sym.heaviside(Const(0.75) - nonnegative_ratio + Const(1e-12))
            - sym.heaviside(
                Const(0.433) - nonnegative_ratio + Const(1e-12),
            )
        )
        + third_region * (
            Const(1.0)
            - sym.heaviside(Const(0.75) - nonnegative_ratio + Const(1e-12))
        )
    )
    return field_voltage * sym.max(rectifier_factor, Const(0.0))


def build_exc_s_k_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcSKParameters | None = None,
) -> RmsModelTemplate:
    """Build the ExcSK voltage, reactive-power and field-voltage graph.

    The equations follow the NEPLAN ExcSK block diagram (printed page 88).
    The remote secondary-controller voltage reference remains an explicit input
    because CGMES ExcSK has no RDF association to that separate controller.

    :param vfactory: Factory allocating the graph symbols.
    :param name: Optional unique runtime name.
    :param parameters: Canonical CGMES parameter values.
    :return: ExcSK graph with field-voltage output and explicit external inputs.
    :raises ValueError: Nonfinite or structurally invalid parameter values.
    """
    settings: ExcSKParameters = ExcSKParameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.efdmax, settings.efdmin, settings.emax, settings.emin, settings.k,
        settings.k1, settings.k2, settings.kc, settings.kce, settings.kd,
        settings.kgob, settings.kp, settings.kqi, settings.kqob, settings.kqp,
        settings.nq, settings.qz, settings.sbase, settings.tc, settings.te,
        settings.ti, settings.tp, settings.tr, settings.uimax, settings.uimin,
        settings.urmax, settings.urmin, settings.vtmax, settings.vtmin, settings.yp,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcSK parameters must be finite')
    elif min(settings.tc, settings.te, settings.ti, settings.tp, settings.tr) < 0.0:
        raise ValueError('ExcSK time constants must be nonnegative')
    elif settings.te == 0.0 or settings.sbase <= 0.0:
        raise ValueError('ExcSK requires positive TE and SBASE')
    elif settings.uimin >= settings.uimax or settings.urmin >= settings.urmax:
        raise ValueError('ExcSK regulator lower limits must be below upper limits')
    elif settings.efdmin >= settings.efdmax or settings.emin >= settings.emax:
        raise ValueError('ExcSK field and exciter lower limits must be below upper limits')
    elif settings.vtmin > settings.vtmax or settings.nq < 0.0:
        raise ValueError('ExcSK voltage bounds and reactive-power deadband are invalid')
    else:
        pass

    template_name: str = 'ExcSK' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    k: Var = model.parameter('ExcSK.k', settings.k)
    kc: Var = model.parameter('ExcSK.kc', settings.kc)
    kce: Var = model.parameter('ExcSK.kce', settings.kce)
    kd: Var = model.parameter('ExcSK.kd', settings.kd)
    kgob: Var = model.parameter('ExcSK.kgob', settings.kgob)
    kqi: Var = model.parameter('ExcSK.kqi', settings.kqi)
    kqp: Var = model.parameter('ExcSK.kqp', settings.kqp)
    nq: Var = model.parameter('ExcSK.nq', settings.nq)
    qz: Var = model.parameter('ExcSK.qz', settings.qz)
    sbase: Var = model.parameter('ExcSK.sbase', settings.sbase)
    tc: Var = model.parameter('ExcSK.tc', settings.tc)
    te: Var = model.parameter('ExcSK.te', settings.te)
    tr: Var = model.parameter('ExcSK.tr', settings.tr)
    uimax: Var = model.parameter('ExcSK.uimax', settings.uimax)
    uimin: Var = model.parameter('ExcSK.uimin', settings.uimin)
    urmax: Var = model.parameter('ExcSK.urmax', settings.urmax)
    urmin: Var = model.parameter('ExcSK.urmin', settings.urmin)
    vtmax: Var = model.parameter('ExcSK.vtmax', settings.vtmax)
    vtmin: Var = model.parameter('ExcSK.vtmin', settings.vtmin)
    efdmax: Var = model.parameter('ExcSK.efdmax', settings.efdmax)
    efdmin: Var = model.parameter('ExcSK.efdmin', settings.efdmin)
    emax: Var = model.parameter('ExcSK.emax', settings.emax)
    emin: Var = model.parameter('ExcSK.emin', settings.emin)
    qconoff_parameter: Var = model.parameter(
        'ExcSK.qconoff', 1.0 if settings.qconoff else 0.0,
    )
    remote_parameter: Var = model.parameter(
        'ExcSK.remote', 1.0 if settings.remote else 0.0,
    )
    k1: Var = model.parameter('ExcSK.k1', settings.k1)
    k2: Var = model.parameter('ExcSK.k2', settings.k2)
    kp: Var = model.parameter('ExcSK.kp', settings.kp)
    ti: Var = model.parameter('ExcSK.ti', settings.ti)
    tp: Var = model.parameter('ExcSK.tp', settings.tp)
    yp: Var = model.parameter('ExcSK.yp', settings.yp)

    voltage: Var = model.input('UsPu', Const(1.0))
    reference: Var = model.input('UsRefPu', Const(1.0))
    stabilizer: Var = model.input('VsPu', Const(0.0))
    field_current: Var = model.input('IfdPu', Const(0.0))
    reactive_power: Var = model.input('QgMvar', Const(0.0))
    mechanical_power: Var = model.input('PmechPu', Const(0.0))
    remote_reference: Var = model.input('VintPu', Const(0.0))
    reactive_power_pu: Expr = reactive_power / sbase
    measured_voltage: Var = model.lag('VcPu', voltage, tr, settings.tr, Const(1.0))
    voltage_bound: Expr = measured_voltage - sym.hard_sat(
        measured_voltage, vtmin, vtmax,
    )
    kqob: Var = model.parameter('ExcSK.kqob', settings.kqob)
    reactive_power_limited: Var = vfactory.add_var(f'ReactivePowerRateLimitedPu_{template_name}')
    model.differential(
        reactive_power_limited,
        sym.hard_sat(reactive_power_pu - reactive_power_limited, -kqob, kqob),
        reactive_power_pu,
    )
    # The diagram places the KQOB slew limiter after Q/MBASE and before the Q controller.
    reactive_pu: Expr = reactive_power_limited
    reactive_reference: Expr = remote_parameter * remote_reference + (Const(1.0) - remote_parameter) * qz
    reactive_error: Expr = reactive_reference - reactive_pu
    reactive_deadband: Expr = (
        sym.max(reactive_error - nq, Const(0.0))
        + sym.min(reactive_error + nq, Const(0.0))
    )
    q_integrator: Var = vfactory.add_var(f'ReactiveIntegralPu_{template_name}')
    if settings.kqi > 0.0:
        model.differential(q_integrator, kqi * reactive_deadband, Const(0.0))
    else:
        model.block.algebraic_vars.append(q_integrator)
        model.block.algebraic_eqs.append(q_integrator)
        model.block.init_eqs[q_integrator] = Const(0.0)
    q_controller: Expr = qconoff_parameter * (
        kqp * reactive_deadband + q_integrator
    )
    mechanical_power_limited: Expr = sym.hard_sat(
        mechanical_power, Const(0.0), Const(1.0),
    )
    reactive_capability: Expr = k1 * mechanical_power_limited + k2
    underexcitation_error: Var = model.algebraic(
        'UnderexcitationErrorPu',
        sym.hard_sat(reactive_capability - reactive_pu, Const(0.0), Const(5.0)),
        Const(0.0),
    )
    if settings.ti > 0.0:
        underexcitation_integral: Var = vfactory.add_var(
            f'UnderexcitationIntegralPu_{template_name}',
        )
        model.differential(underexcitation_integral, underexcitation_error / ti, Const(0.0))
        underexcitation_pi: Expr = kp * (underexcitation_error + underexcitation_integral)
    else:
        underexcitation_pi = kp * underexcitation_error
    underexcitation_limited: Expr = sym.hard_sat(underexcitation_pi, Const(0.0), yp)
    underexcitation_output: Var = model.lag(
        'UnderexcitationOutputPu', underexcitation_limited, tp, settings.tp,
        Const(0.0), Const(0.0), yp,
    )
    error: Expr = (
        reference - measured_voltage + stabilizer - kgob * voltage_bound
        + q_controller - underexcitation_output
    )
    limited_error: Var = model.algebraic(
        'RegulatorErrorPu', sym.hard_sat(error, uimin, uimax), Const(0.0),
    )
    proportional: Expr = kc * limited_error
    if settings.tc > 0.0:
        regulator_integral: Var = vfactory.add_var(f'RegulatorIntegralPu_{template_name}')
        model.differential(regulator_integral, limited_error / tc, Const(0.0))
        regulator_integral_gain: Expr = kc * regulator_integral
    else:
        regulator_integral_gain = Const(0.0)
    regulator_unbounded: Expr = proportional + regulator_integral_gain
    regulator: Var = model.algebraic(
        'RegulatorPu', sym.hard_sat(regulator_unbounded, urmin, urmax), Const(0.0),
    )
    exciter_feedback: Expr = kd * field_current
    exciter_input: Expr = regulator - exciter_feedback
    exciter_voltage: Var = model.lag(
        'VePu', exciter_input * k, te, settings.te, Const(1.0), emin, emax,
    )
    # KCE sets the normalized commutating-current ratio in the standard rectifier curve.
    field_voltage: Var = model.algebraic(
        'EfdPu', sym.hard_sat(
            exc_sk_rectifier_output(exciter_voltage, field_current, kce), efdmin, efdmax,
        ),
        Const(1.0),
    )
    template: RmsModelTemplate = model.finish((field_voltage,), 'CGMES ExcSK excitation system')
    template.comment = (
        'ExcSK voltage regulator and field-current feedback follow the NEPLAN page 88 diagram. '
        'VintPu is explicit because the remote secondary-controller state has no ExcSK RDF link. '
        'The Qmax/UEL branch and KQOB slew limiter are translated from the diagram. '
        'KCE(IFD/VE) uses the three-region rectifier characteristic in the NEPLAN source.'
    )
    return template
