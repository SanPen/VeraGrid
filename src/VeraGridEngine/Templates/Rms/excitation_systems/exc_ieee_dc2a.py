# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEDC2A direct-current exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEDC2AParameters:
    """Settings declared by the canonical ExcIEEEDC2A RDF class."""

    __slots__ = (
        'efd1', 'efd2', 'exclim', 'ka', 'ke', 'kf', 'seefd1', 'seefd2',
        'ta', 'tb', 'tc', 'te', 'tf', 'uelin', 'vrmax', 'vrmin',
    )

    def __init__(
            self,
            efd1: float = 3.05,
            efd2: float = 2.29,
            exclim: float = -999.0,
            ka: float = 300.0,
            ke: float = 1.0,
            kf: float = 0.1,
            seefd1: float = 0.279,
            seefd2: float = 0.117,
            ta: float = 0.01,
            tb: float = 0.0,
            tc: float = 0.0,
            te: float = 1.33,
            tf: float = 0.675,
            uelin: bool = True,
            vrmax: float = 4.95,
            vrmin: float = -4.9,
    ) -> None:
        """Store canonical values, defaulting absent values to local EA typicals.

        :param efd1: First exciter saturation voltage point.
        :param efd2: Second exciter saturation voltage point.
        :param exclim: Exciter state lower limit; ``-999`` disables the limit.
        :param ka: Voltage regulator gain.
        :param ke: Exciter field constant.
        :param kf: Stabilizing feedback gain.
        :param seefd1: Saturation at ``efd1``.
        :param seefd2: Saturation at ``efd2``.
        :param ta: Regulator time constant.
        :param tb: Voltage-compensator lag time constant.
        :param tc: Voltage-compensator lead time constant.
        :param te: Exciter integration time constant.
        :param tf: Stabilizing-feedback time constant.
        :param uelin: Put the UEL input at the high gate when true.
        :param vrmax: Terminal-voltage-scaled regulator upper limit.
        :param vrmin: Terminal-voltage-scaled regulator lower limit.
        """
        self.efd1: float = efd1
        self.efd2: float = efd2
        self.exclim: float = exclim
        self.ka: float = ka
        self.ke: float = ke
        self.kf: float = kf
        self.seefd1: float = seefd1
        self.seefd2: float = seefd2
        self.ta: float = ta
        self.tb: float = tb
        self.tc: float = tc
        self.te: float = te
        self.tf: float = tf
        self.uelin: bool = uelin
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin


def build_exc_i_e_e_e_d_c2_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEDC2AParameters | None = None,
) -> RmsModelTemplate:
    """Build DC2A with terminal-scaled regulator limits and UEL selection.

    :param vfactory: Factory owning the symbolic equations.
    :param name: Optional runtime model name.
    :param parameters: Parsed CGMES values or EA typical defaults.
    :return: Equation-backed DC2A with machine-facing signal ports.
    :raises ValueError: If the supplied times, limits, or saturation points are invalid.
    """
    settings: ExcIEEEDC2AParameters = (
        ExcIEEEDC2AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEDC2A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.efd1, settings.efd2, settings.exclim, settings.ka, settings.ke,
        settings.kf, settings.seefd1, settings.seefd2, settings.ta, settings.tb,
        settings.tc, settings.te, settings.tf, settings.vrmax, settings.vrmin,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcIEEEDC2A parameters must be finite')
    elif min(settings.ta, settings.tb, settings.tc, settings.tf) < 0.0 or settings.te <= 0.0:
        raise ValueError('ExcIEEEDC2A times must be nonnegative and TE positive')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcIEEEDC2A zero TB requires zero TC')
    elif settings.ka <= 0.0 or settings.ke < 0.0 or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcIEEEDC2A regulator and exciter gains/limits are invalid')
    elif settings.efd1 <= 0.0 or settings.efd2 <= 0.0 or settings.efd1 == settings.efd2:
        raise ValueError('ExcIEEEDC2A saturation points must be distinct and positive')
    elif settings.seefd1 < 0.0 or settings.seefd2 < 0.0:
        raise ValueError('ExcIEEEDC2A saturation samples must be nonnegative')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcIEEEDC2A nonzero KF requires positive TF')
    elif (settings.seefd1 == 0.0) != (settings.seefd2 == 0.0):
        raise ValueError('ExcIEEEDC2A saturation samples must both be zero or positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    efd1: Var = builder.parameter('EFD1', settings.efd1)
    efd2: Var = builder.parameter('EFD2', settings.efd2)
    exclim: Var = builder.parameter('EXCLIM', settings.exclim)
    ka: Var = builder.parameter('KA', settings.ka)
    ke: Var = builder.parameter('KE', settings.ke)
    kf: Var = builder.parameter('KF', settings.kf)
    seefd1: Var = builder.parameter('SEefd1', settings.seefd1)
    seefd2: Var = builder.parameter('SEefd2', settings.seefd2)
    ta: Var = builder.parameter('TA', settings.ta)
    tb: Var = builder.parameter('TB', settings.tb)
    tc: Var = builder.parameter('TC', settings.tc)
    te: Var = builder.parameter('TE', settings.te)
    tf: Var = builder.parameter('TF', settings.tf)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    underexcitation: Var = builder.input('VuelPu', Const(0.0))
    machine_speed: Var = builder.input('OmegaPu', Const(1.0))

    exciter_state: Var = vfactory.add_var(f'ExciterVoltagePu_{template_name}')
    voltage_error: Expr = reference - terminal_voltage + supplementary
    if settings.uelin:
        error_with_uel: Expr = voltage_error
    else:
        error_with_uel = voltage_error + underexcitation
    if settings.tb == 0.0:
        compensated_error: Expr = error_with_uel
    else:
        compensated_error = builder.lead_lag(
            'VoltageCompensatorPu', error_with_uel, tc, tb,
            settings.tc, settings.tb, error_with_uel,
        )

    if settings.tf == 0.0 or settings.kf == 0.0:
        stabilizing_feedback: Expr = Const(0.0)
    else:
        feedback_state: Var = builder.lag(
            'FeedbackFilterPu', exciter_state, tf, settings.tf, Const(1.0),
        )
        stabilizing_feedback = kf / tf * (exciter_state - feedback_state)
    regulator_input: Expr = compensated_error - stabilizing_feedback
    regulator_lower: Expr = terminal_voltage * vrmin
    regulator_upper: Expr = terminal_voltage * vrmax
    regulator_output: Var = builder.lag(
        'RegulatorOutputPu', ka * regulator_input, ta, settings.ta,
        Const(0.0), regulator_lower, regulator_upper,
    )
    if settings.uelin:
        regulator_forcing: Expr = sym.max(regulator_output, underexcitation)
    else:
        regulator_forcing = regulator_output

    saturation: Expr = Const(0.0)
    if settings.seefd1 > 0.0 and settings.seefd2 > 0.0:
        saturation_slope: Expr = sym.log(seefd2 / seefd1) / (efd2 - efd1)
        saturation_base: Expr = seefd1 * sym.exp(-saturation_slope * efd1)
        saturation = saturation_base * sym.exp(saturation_slope * exciter_state)
    else:
        pass
    exciter_derivative: Expr = (
        regulator_forcing - (ke + saturation) * exciter_state
    ) / te
    if settings.exclim > -999.0:
        at_lower_stop: Expr = Const(1.0) - sym.heaviside(exciter_state - exclim)
        moving_below_stop: Expr = sym.heaviside(-exciter_derivative)
        exciter_derivative = exciter_derivative * (
            Const(1.0) - at_lower_stop * moving_below_stop
        )
    else:
        pass
    builder.differential(exciter_state, exciter_derivative, Const(1.0))
    field_voltage: Var = builder.algebraic(
        'EfdPu', exciter_state * machine_speed, Const(1.0),
    )
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcIEEEDC2A direct-current commutator exciter',
    )
    for parameter_name in (
            'enabled', 'efd1', 'efd2', 'exclim', 'ka', 'ke', 'kf', 'seefd1',
            'seefd2', 'ta', 'tb', 'tc', 'te', 'tf', 'uelin', 'vrmax', 'vrmin',
    ):
        variable_name: str = f'ExcIEEEDC2A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=variable_name,
        )
    return template
