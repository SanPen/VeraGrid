# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEDC3A motor-operated rheostat exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEDC3AParameters:
    """Settings declared by the canonical ExcIEEEDC3A RDF class."""

    __slots__ = (
        'trh', 'kv', 'vrmax', 'vrmin', 'te', 'ke', 'efd1', 'seefd1',
        'efd2', 'seefd2', 'exclim',
    )

    def __init__(
            self,
            trh: float = 20.0,
            kv: float = 0.05,
            vrmax: float = 1.0,
            vrmin: float = 0.0,
            te: float = 0.5,
            ke: float = 0.05,
            efd1: float = 3.375,
            seefd1: float = 0.267,
            efd2: float = 3.15,
            seefd2: float = 0.068,
            exclim: bool = True,
    ) -> None:
        """Store the exact RDF fields with local EA typical fallbacks.

        :param trh: Rheostat travel time constant.
        :param kv: Fast raise/lower contact threshold.
        :param vrmax: Rheostat upper setting.
        :param vrmin: Rheostat lower setting.
        :param te: Exciter integration time constant.
        :param ke: Exciter field constant.
        :param efd1: First saturation voltage point.
        :param seefd1: Saturation at ``efd1``.
        :param efd2: Second saturation voltage point.
        :param seefd2: Saturation at ``efd2``.
        :param exclim: Apply a zero lower stop to the exciter integrator.
        """
        self.trh: float = trh
        self.kv: float = kv
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.te: float = te
        self.ke: float = ke
        self.efd1: float = efd1
        self.seefd1: float = seefd1
        self.efd2: float = efd2
        self.seefd2: float = seefd2
        self.exclim: bool = exclim


def build_exc_i_e_e_e_d_c3_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEDC3AParameters | None = None,
) -> RmsModelTemplate:
    """Build the continuous rheostat, fast contacts, and saturated field.

    :param vfactory: Factory owning the symbolic variables and states.
    :param name: Optional runtime model name.
    :param parameters: Parsed CGMES values or EA typical defaults.
    :return: Equation-backed DC3A model with voltage, speed, and Efd ports.
    :raises ValueError: Invalid travel time, thresholds, bounds, or saturation data.
    """
    settings: ExcIEEEDC3AParameters = (
        ExcIEEEDC3AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEDC3A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.trh, settings.kv, settings.vrmax, settings.vrmin, settings.te,
        settings.ke, settings.efd1, settings.seefd1, settings.efd2, settings.seefd2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcIEEEDC3A parameters must be finite')
    elif settings.trh <= 0.0 or settings.kv <= 0.0 or settings.te <= 0.0:
        raise ValueError('ExcIEEEDC3A TRH, KV, and TE must be positive')
    elif settings.vrmin >= settings.vrmax or settings.ke < 0.0:
        raise ValueError('ExcIEEEDC3A rheostat limits or KE are invalid')
    elif settings.efd1 <= 0.0 or settings.efd2 <= 0.0 or settings.efd1 == settings.efd2:
        raise ValueError('ExcIEEEDC3A saturation points must be distinct and positive')
    elif settings.seefd1 < 0.0 or settings.seefd2 < 0.0:
        raise ValueError('ExcIEEEDC3A saturation values must be nonnegative')
    elif (settings.seefd1 == 0.0) != (settings.seefd2 == 0.0):
        raise ValueError('ExcIEEEDC3A saturation samples must both be zero or positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    trh: Var = builder.parameter('TRH', settings.trh)
    kv: Var = builder.parameter('KV', settings.kv)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    te: Var = builder.parameter('TE', settings.te)
    ke: Var = builder.parameter('KE', settings.ke)
    efd1: Var = builder.parameter('EFD1', settings.efd1)
    seefd1: Var = builder.parameter('SEefd1', settings.seefd1)
    efd2: Var = builder.parameter('EFD2', settings.efd2)
    seefd2: Var = builder.parameter('SEefd2', settings.seefd2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    machine_speed: Var = builder.input('OmegaPu', Const(1.0))
    voltage_error: Expr = reference - terminal_voltage + supplementary

    initial_saturation: float = 0.0
    if settings.seefd1 > 0.0 and settings.seefd2 > 0.0:
        saturation_slope: float = math.log(
            settings.seefd2 / settings.seefd1,
        ) / (settings.efd2 - settings.efd1)
        saturation_base: float = settings.seefd1 * math.exp(-saturation_slope * settings.efd1)
        initial_saturation = saturation_base * math.exp(saturation_slope)
    else:
        pass
    rheostat_memory: Var = vfactory.add_var(f'RheostatPu_{template_name}')
    rheostat_derivative: Expr = (
        (vrmax - vrmin) * sym.hard_sat(voltage_error, -kv, kv) / (kv * trh)
    )
    rheostat_initial: Expr = sym.hard_sat(
        Const((settings.ke + initial_saturation)), vrmin, vrmax,
    )
    builder.differential(
        rheostat_memory, rheostat_derivative, rheostat_initial, vrmin, vrmax,
    )
    fast_raise: Expr = Const(1.0) - sym.heaviside(kv - voltage_error)
    fast_lower: Expr = Const(1.0) - sym.heaviside(kv + voltage_error)
    rheostat_setting: Expr = sym.hard_sat(rheostat_memory, vrmin, vrmax)
    regulator_output: Expr = (
        rheostat_setting
        + fast_raise * (vrmax - rheostat_setting)
        + fast_lower * (vrmin - rheostat_setting)
    )

    exciter_state: Var = vfactory.add_var(f'ExciterVoltagePu_{template_name}')
    saturation: Expr = Const(0.0)
    if settings.seefd1 > 0.0 and settings.seefd2 > 0.0:
        saturation_slope_expression: Expr = sym.log(seefd2 / seefd1) / (efd2 - efd1)
        saturation_base_expression: Expr = seefd1 * sym.exp(
            -saturation_slope_expression * efd1,
        )
        saturation = saturation_base_expression * sym.exp(
            saturation_slope_expression * exciter_state,
        )
    else:
        pass
    exciter_derivative: Expr = (
        regulator_output - (ke + saturation) * exciter_state
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
        (field_voltage,), 'CGMES ExcIEEEDC3A motor-operated rheostat exciter',
    )
    for parameter_name in (
            'enabled', 'trh', 'kv', 'vrmax', 'vrmin', 'te', 'ke', 'efd1',
            'seefd1', 'efd2', 'seefd2', 'exclim',
    ):
        variable_name: str = f'ExcIEEEDC3A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=variable_name,
        )
    return template
