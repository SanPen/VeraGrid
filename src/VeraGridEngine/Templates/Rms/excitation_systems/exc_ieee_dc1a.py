# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEDC1A direct-current exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEDC1AParameters:
    """Settings declared by the canonical ExcIEEEDC1A RDF class."""

    __slots__ = (
        'ka', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf',
        'efd1', 'seefd1', 'efd2', 'seefd2', 'uelin', 'exclim',
    )

    def __init__(
            self,
            ka: float = 46.0,
            ta: float = 0.06,
            tb: float = 0.0,
            tc: float = 0.0,
            vrmax: float = 1.0,
            vrmin: float = -0.9,
            ke: float = 0.0,
            te: float = 0.46,
            kf: float = 0.1,
            tf: float = 1.0,
            efd1: float = 3.1,
            seefd1: float = 0.33,
            efd2: float = 2.3,
            seefd2: float = 0.1,
            uelin: bool = True,
            exclim: bool = True,
    ) -> None:
        """Store settings with local EA typical values for absent RDF values.

        :param ka: Voltage-regulator gain.
        :param ta: Voltage-regulator time constant.
        :param tb: Voltage-compensator lag time constant.
        :param tc: Voltage-compensator lead time constant.
        :param vrmax: Regulator output upper limit.
        :param vrmin: Regulator output lower limit.
        :param ke: Exciter field constant.
        :param te: Exciter integration time constant.
        :param kf: Stabilizing feedback gain.
        :param tf: Stabilizing feedback time constant.
        :param efd1: First exciter saturation voltage point.
        :param seefd1: Saturation at ``efd1``.
        :param efd2: Second exciter saturation voltage point.
        :param seefd2: Saturation at ``efd2``.
        :param uelin: Select UEL input at the regulator high gate when true.
        :param exclim: Apply the exciter integrator's zero lower stop.
        """
        self.ka: float = ka
        self.ta: float = ta
        self.tb: float = tb
        self.tc: float = tc
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.ke: float = ke
        self.te: float = te
        self.kf: float = kf
        self.tf: float = tf
        self.efd1: float = efd1
        self.seefd1: float = seefd1
        self.efd2: float = efd2
        self.seefd2: float = seefd2
        self.uelin: bool = uelin
        self.exclim: bool = exclim


def build_exc_i_e_e_e_d_c1_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEDC1AParameters | None = None,
) -> RmsModelTemplate:
    """Build the DC1A regulator, feedback, field integrator, and shaft-speed path.

    :param vfactory: Factory owning the symbolic block variables.
    :param name: Optional runtime model name.
    :param parameters: Parsed CGMES values or EA typical defaults.
    :return: Equation-backed DC1A model with machine-facing signal ports.
    :raises ValueError: If times, limits, or saturation points are invalid.
    """
    settings: ExcIEEEDC1AParameters = (
        ExcIEEEDC1AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEDC1A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.ta, settings.tb, settings.tc, settings.vrmax,
        settings.vrmin, settings.ke, settings.te, settings.kf, settings.tf,
        settings.efd1, settings.seefd1, settings.efd2, settings.seefd2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcIEEEDC1A parameters must be finite')
    elif min(settings.ta, settings.tb, settings.tc, settings.tf) < 0.0:
        raise ValueError('ExcIEEEDC1A times must be nonnegative')
    elif settings.te <= 0.0 or settings.ke < 0.0 or settings.ka <= 0.0:
        raise ValueError('ExcIEEEDC1A TE must be positive and KA/KE valid')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcIEEEDC1A zero TB requires zero TC')
    elif settings.vrmin >= settings.vrmax:
        raise ValueError('ExcIEEEDC1A regulator limits must be ordered')
    elif settings.efd1 <= 0.0 or settings.efd2 <= 0.0 or settings.efd1 == settings.efd2:
        raise ValueError('ExcIEEEDC1A saturation points must be distinct and positive')
    elif settings.seefd1 < 0.0 or settings.seefd2 < 0.0:
        raise ValueError('ExcIEEEDC1A saturation values must be nonnegative')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcIEEEDC1A nonzero KF requires positive TF')
    elif (settings.seefd1 == 0.0) != (settings.seefd2 == 0.0):
        raise ValueError('ExcIEEEDC1A saturation samples must both be zero or positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    tb: Var = builder.parameter('TB', settings.tb)
    tc: Var = builder.parameter('TC', settings.tc)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    ke: Var = builder.parameter('KE', settings.ke)
    te: Var = builder.parameter('TE', settings.te)
    kf: Var = builder.parameter('KF', settings.kf)
    tf: Var = builder.parameter('TF', settings.tf)
    efd1: Var = builder.parameter('EFD1', settings.efd1)
    seefd1: Var = builder.parameter('SEefd1', settings.seefd1)
    efd2: Var = builder.parameter('EFD2', settings.efd2)
    seefd2: Var = builder.parameter('SEefd2', settings.seefd2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    underexcitation: Var = builder.input('VuelPu', Const(0.0))
    machine_speed: Var = builder.input('OmegaPu', Const(1.0))

    exciter_state: Var = vfactory.add_var(f'ExciterVoltagePu_{template_name}')
    voltage_error: Expr = reference - terminal_voltage + supplementary
    if settings.uelin:
        voltage_error_with_uel: Expr = voltage_error
    else:
        voltage_error_with_uel = voltage_error + underexcitation
    if settings.tb == 0.0:
        compensated_error: Expr = voltage_error_with_uel
    else:
        compensated_error = builder.lead_lag(
            'VoltageCompensatorPu', voltage_error_with_uel, tc, tb,
            settings.tc, settings.tb, voltage_error_with_uel,
        )

    if settings.tf == 0.0 or settings.kf == 0.0:
        stabilizing_feedback: Expr = Const(0.0)
    else:
        feedback_state: Var = builder.lag(
            'FeedbackFilterPu', exciter_state, tf, settings.tf, Const(1.0),
        )
        stabilizing_feedback = kf / tf * (exciter_state - feedback_state)
    regulator_input: Expr = compensated_error - stabilizing_feedback
    regulator_output: Var = builder.lag(
        'RegulatorOutputPu', ka * regulator_input, ta, settings.ta,
        Const(0.0), vrmin, vrmax,
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
    if settings.exclim:
        at_lower_stop: Expr = Const(1.0) - sym.heaviside(exciter_state)
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
        (field_voltage,), 'CGMES ExcIEEEDC1A direct-current commutator exciter',
    )
    for parameter_name in (
            'enabled', 'ka', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'ke', 'te',
            'kf', 'tf', 'efd1', 'seefd1', 'efd2', 'seefd2', 'uelin', 'exclim',
    ):
        variable_name: str = f'ExcIEEEDC1A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=variable_name,
        )
    return template
