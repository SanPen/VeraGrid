# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the License was not distributed with this
# file, You can obtain one at https://www.mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcDC3A motor-operated rheostat exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcDC3AParameters:
    """Settings declared by the canonical CGMES ExcDC3A class."""

    __slots__ = (
        'trh', 'ks', 'kr', 'kv', 'vrmax', 'vrmin', 'te', 'ke', 'efd1', 'seefd1',
        'efd2', 'seefd2', 'exclim', 'efdmax', 'efdmin', 'efdlim',
    )

    def __init__(
            self,
            trh: float = 20.0,
            ks: float = 0.0,
            kr: float = 0.0,
            kv: float = 0.05,
            vrmax: float = 5.0,
            vrmin: float = 0.0,
            te: float = 1.83,
            ke: float = 1.0,
            efd1: float = 2.6,
            seefd1: float = 0.1,
            efd2: float = 3.45,
            seefd2: float = 0.35,
            exclim: bool = True,
            efdmax: float = 99.0,
            efdmin: float = -99.0,
            efdlim: bool = True,
    ) -> None:
        """Store model parameters with local EA typical values.

        :param trh: Rheostat travel time in seconds.
        :param ks: Speed-deviation multiplier coefficient.
        :param kr: Deadband that selects constant-rate rheostat motion.
        :param kv: Fast raise/lower contact threshold and normalized path scale.
        :param vrmax: Upper rheostat voltage setting.
        :param vrmin: Lower rheostat voltage setting.
        :param te: Exciter integration time constant in seconds.
        :param ke: Exciter field constant.
        :param efd1: First saturation voltage point.
        :param seefd1: Saturation at ``efd1``.
        :param efd2: Second saturation voltage point.
        :param seefd2: Saturation at ``efd2``.
        :param exclim: Apply a zero lower stop to the exciter integrator.
        :param efdmax: Upper delivered field-voltage limit.
        :param efdmin: Lower delivered field-voltage limit.
        :param efdlim: Enable the delivered field-voltage limits.
        """
        self.trh: float = trh
        self.ks: float = ks
        self.kr: float = kr
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
        self.efdmax: float = efdmax
        self.efdmin: float = efdmin
        self.efdlim: bool = efdlim


def build_exc_d_c3_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcDC3AParameters | None = None,
) -> RmsModelTemplate:
    """Build the rheostat, fast-contact, and saturated field equations.

    :param vfactory: Factory owning the symbolic graph.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Equation-backed model with voltage, reference, Vs, optional speed, and Efd ports.
    :raises ValueError: Invalid travel time, contact thresholds, bounds, or saturation data.
    """
    settings: ExcDC3AParameters = ExcDC3AParameters() if parameters is None else parameters
    template_name: str = 'ExcDC3A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.trh, settings.ks, settings.kr, settings.kv, settings.vrmax,
        settings.vrmin, settings.te, settings.ke, settings.efd1, settings.seefd1,
        settings.efd2, settings.seefd2, settings.efdmax, settings.efdmin,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcDC3A parameters must be finite')
    elif settings.trh <= 0.0 or settings.te <= 0.0 or settings.kv <= 0.0 or settings.kr < 0.0:
        raise ValueError('ExcDC3A requires positive TRH, TE, KV and nonnegative KR')
    elif settings.vrmin >= settings.vrmax or settings.efdmin >= settings.efdmax:
        raise ValueError('ExcDC3A rheostat and field limits must be ordered')
    elif settings.efd1 <= 0.0 or settings.efd2 <= 0.0 or settings.efd1 == settings.efd2:
        raise ValueError('ExcDC3A saturation voltage points must be distinct and positive')
    elif settings.seefd1 <= 0.0 or settings.seefd2 <= 0.0:
        raise ValueError('ExcDC3A saturation values must be positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    trh: Var = builder.parameter('TRH', settings.trh)
    ks: Var = builder.parameter('KS', settings.ks)
    kr: Var = builder.parameter('KR', settings.kr)
    kv: Var = builder.parameter('KV', settings.kv)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    te: Var = builder.parameter('TE', settings.te)
    ke: Var = builder.parameter('KE', settings.ke)
    efd1: Var = builder.parameter('EFD1', settings.efd1)
    seefd1: Var = builder.parameter('SEefd1', settings.seefd1)
    efd2: Var = builder.parameter('EFD2', settings.efd2)
    seefd2: Var = builder.parameter('SEefd2', settings.seefd2)
    builder.parameter('EXCLIM', 1.0 if settings.exclim else 0.0)
    efdmax: Var = builder.parameter('EFDMAX', settings.efdmax)
    efdmin: Var = builder.parameter('EFDMIN', settings.efdmin)
    builder.parameter('EFDLIM', 1.0 if settings.efdlim else 0.0)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    voltage_error: Expr = reference - terminal_voltage + supplementary

    exciter_state: Var = vfactory.add_var(f'ExciterVoltagePu_{template_name}')
    saturation_b: float = math.log(settings.seefd2 / settings.seefd1) / (settings.efd2 - settings.efd1)
    saturation_a: float = settings.seefd1 * math.exp(-saturation_b * settings.efd1)
    initial_saturation: float = saturation_a * math.exp(saturation_b)
    initial_regulator: Expr = Const((settings.ke + initial_saturation) * 1.0)
    rheostat_memory: Var = vfactory.add_var(f'RheostatPu_{template_name}')
    if settings.kr > 0.0:
        rheostat_direction: Expr = (
            sym.heaviside(voltage_error - kr) - sym.heaviside(-voltage_error - kr)
        )
        rheostat_derivative: Expr = rheostat_direction / trh
    else:
        rheostat_derivative = (
            (vrmax - vrmin) * sym.hard_sat(voltage_error, -kv, kv) / (kv * trh)
        )
    builder.differential(
        rheostat_memory,
        rheostat_derivative,
        sym.hard_sat(initial_regulator, vrmin, vrmax),
        vrmin,
        vrmax,
    )
    fast_raise: Expr = Const(1.0) - sym.heaviside(kv - voltage_error)
    fast_lower: Expr = Const(1.0) - sym.heaviside(kv + voltage_error)
    rheostat_setting: Expr = sym.hard_sat(rheostat_memory, vrmin, vrmax)
    regulator_output: Expr = (
        rheostat_setting
        + fast_raise * (vrmax - rheostat_setting)
        + fast_lower * (vrmin - rheostat_setting)
    )

    saturation: Expr = Const(saturation_a) * sym.exp(Const(saturation_b) * exciter_state)
    exciter_derivative: Expr = (regulator_output - (ke + saturation) * exciter_state) / te
    builder.block.state_vars.append(exciter_state)
    builder.block.diff_vars.append(vfactory.add_diff_var(name=f'd_{exciter_state.name}', base_var=exciter_state))
    if settings.exclim:
        lower_stop: Expr = Const(1.0) - sym.heaviside(exciter_state)
        outward_motion: Expr = sym.heaviside(-exciter_derivative)
        exciter_derivative = exciter_derivative * (Const(1.0) - lower_stop * outward_motion)
    else:
        pass
    builder.block.state_eqs.append(exciter_derivative)
    builder.block.init_eqs[exciter_state] = Const(1.0)

    if settings.ks == 0.0:
        speed_multiplier: Expr = Const(1.0)
    else:
        machine_speed: Var = builder.input('OmegaPu', Const(1.0))
        speed_multiplier = Const(1.0) + ks * (machine_speed - Const(1.0))
    delivered_expression: Expr = speed_multiplier * exciter_state
    if settings.efdlim:
        delivered_expression = sym.hard_sat(delivered_expression, efdmin, efdmax)
    else:
        pass
    field_voltage: Var = builder.algebraic('EfdPu', delivered_expression, exciter_state)
    return builder.finish((field_voltage,), 'CGMES ExcDC3A motor-operated rheostat exciter')
