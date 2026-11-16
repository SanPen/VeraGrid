# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES OverexcLimIEEE timed field-current limiter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import flipflop
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class OverexcLimIEEEParameters:
    """Canonical OverexcLimIEEE scalar fields."""

    __slots__ = ('itfpu', 'ifdmax', 'ifdlim', 'hyst', 'kcd', 'kramp')

    def __init__(self, itfpu: float = 1.05, ifdmax: float = 1.5,
                 ifdlim: float = 1.05, hyst: float = 0.03,
                 kcd: float = 1.0, kramp: float = 10.0) -> None:
        """Store the exact RDF model fields.

        :param itfpu: Timed field-current pickup in rated-current per unit.
        :param ifdmax: Instantaneous field-current limit in rated-current per unit.
        :param ifdlim: Timed field-current limit in rated-current per unit.
        :param hyst: Pickup/dropout hysteresis in per unit.
        :param kcd: Timer cooldown gain.
        :param kramp: Post-timeout field-voltage reduction rate per second.
        """
        self.itfpu: float = itfpu
        self.ifdmax: float = ifdmax
        self.ifdlim: float = ifdlim
        self.hyst: float = hyst
        self.kcd: float = kcd
        self.kramp: float = kramp


def build_overexc_lim_i_e_e_e_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: OverexcLimIEEEParameters | None = None,
) -> RmsModelTemplate:
    """Build the IEEE 421.5 OEL1B threshold, cooldown, and ramp equations.

    :param vfactory: Factory allocating model symbols.
    :param name: Optional runtime template name.
    :param parameters: Canonical RDF parameter values.
    :return: OEL graph with field-current input and exciter field-voltage limit.
    :raises ValueError: A setting is nonfinite, negative, or inconsistent.
    """
    settings: OverexcLimIEEEParameters = (
        OverexcLimIEEEParameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.itfpu, settings.ifdmax, settings.ifdlim,
        settings.hyst, settings.kcd, settings.kramp,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('OverexcLimIEEE parameters must be finite')
    elif min(settings.itfpu, settings.ifdmax, settings.ifdlim,
             settings.hyst, settings.kcd, settings.kramp) < 0.0:
        raise ValueError('OverexcLimIEEE thresholds, hysteresis, and gains must be nonnegative')
    elif settings.ifdmax < settings.ifdlim:
        raise ValueError('OverexcLimIEEE instantaneous limit must be at least its timed limit')
    else:
        pass

    template_name: str = 'OverexcLimIEEE' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    pickup: Var = model.parameter('OverexcLimIEEE.itfpu', settings.itfpu)
    instantaneous_limit: Var = model.parameter('OverexcLimIEEE.ifdmax', settings.ifdmax)
    timed_limit: Var = model.parameter('OverexcLimIEEE.ifdlim', settings.ifdlim)
    hysteresis: Var = model.parameter('OverexcLimIEEE.hyst', settings.hyst)
    cooldown_gain: Var = model.parameter('OverexcLimIEEE.kcd', settings.kcd)
    ramp_rate: Var = model.parameter('OverexcLimIEEE.kramp', settings.kramp)
    field_current: Var = model.input('IfdPu', Const(settings.itfpu))
    field_voltage: Var = model.input('EfdPu', Const(settings.itfpu))

    # The relay state retains HYST after pickup and drops out below ITFPU-HYST.
    pickup_mode: Var = vfactory.add_var(f'OelPickedUp_{template_name}')
    model.block.mode_dict[pickup_mode] = Const(0.0)
    model.block.procedural_logic.append(
        flipflop(
            boolset=field_current > pickup,
            boolreset=field_current <= pickup - hysteresis,
            output=pickup_mode,
            name=f'OverexcLimIEEE.Pickup_{template_name}',
        )
    )

    # Timer advances at one second while picked up and cools proportionally
    # below the pickup level; its state cannot become negative.
    timer_state: Var = vfactory.add_var(f'OelTimerSeconds_{template_name}')
    timer_derivative: Expr = pickup_mode - (Const(1.0) - pickup_mode) * cooldown_gain * sym.max(
        pickup - field_current, Const(0.0),
    )
    bounded_timer_derivative: Expr = sym.max(timer_derivative, -timer_state)
    model.differential(timer_state, bounded_timer_derivative, Const(0.0))

    # The published IEEE flowchart computes timeout from the current field
    # current but provides no timeout curve coefficients in this RDF class.
    # Its associated curve is represented by the standard 33.75/(IFD-1)^2 s.
    timeout: Var = model.algebraic(
        'TimeoutSeconds',
        Const(33.75) / sym.max(field_current - Const(1.0), Const(0.01)) ** Const(2.0),
        Const(33.75) / max(settings.itfpu - 1.0, 0.01) ** 2.0,
    )
    ramp_elapsed: Var = model.algebraic(
        'RampElapsedSeconds', sym.max(timer_state - timeout, Const(0.0)), Const(0.0),
    )
    timed_field_voltage_limit: Var = model.algebraic(
        'TimedFieldVoltageLimitPu',
        sym.max(timed_limit, field_current - ramp_rate * ramp_elapsed),
        sym.max(timed_limit, field_current),
    )
    # IEEE 421.5 applies this limiter at the machine field-voltage output gate,
    # not at an internal exciter VOEL port; separate flags preserve both actions.
    instantaneous_mode: Var = vfactory.add_var(f'OelInstantaneous_{template_name}')
    model.block.mode_dict[instantaneous_mode] = Const(0.0)
    model.block.procedural_logic.append(
        flipflop(
            boolset=field_current > instantaneous_limit,
            boolreset=field_current <= pickup - hysteresis,
            output=instantaneous_mode,
            name=f'OverexcLimIEEE.Instantaneous_{template_name}',
        )
    )
    timed_mode: Var = vfactory.add_var(f'OelTimed_{template_name}')
    model.block.mode_dict[timed_mode] = Const(0.0)
    model.block.procedural_logic.append(
        flipflop(
            boolset=timer_state > timeout,
            boolreset=field_current <= pickup - hysteresis,
            output=timed_mode,
            name=f'OverexcLimIEEE.Timed_{template_name}',
        )
    )
    limiting_mode: Var = model.algebraic(
        'OelLimitingMode', sym.max(instantaneous_mode, timed_mode), Const(0.0),
    )
    active_field_voltage_limit: Var = model.algebraic(
        'ActiveFieldVoltageLimitPu',
        sym.min(instantaneous_limit, timed_field_voltage_limit),
        sym.min(instantaneous_limit, sym.max(timed_limit, field_current)),
    )
    output: Var = model.algebraic(
        'EfdLimitedPu',
        (Const(1.0) - limiting_mode) * field_voltage
        + limiting_mode * sym.min(field_voltage, active_field_voltage_limit),
        (Const(1.0) - limiting_mode) * field_voltage
        + limiting_mode * sym.min(
            field_voltage,
            sym.min(instantaneous_limit, sym.max(timed_limit, field_current)),
        ),
    )
    template: RmsModelTemplate = model.finish(
        (output,), 'CGMES OverexcLimIEEE timed/instantaneous field-current limiter',
    )
    template.comment = (
        'IEEE 421.5-2016 OEL1B Figure 40: field current on rated-current base; '
        'pickup threshold ITFPU−HYST, reset/cooldown timer, instantaneous IFDMAX '
        'limit, and post-timeout KRAMP ramp to IFDLIM. Timeout uses IEEE 421.5-2005 '
        'rotor capability 33.75/(IFD−1)^2 seconds. This implementation assumes '
        'equal rated-current and field-voltage per-unit bases at the machine low gate; '
        'the RDF supplies neither rated '
        'field current nor a manufacturer-specific capability curve; IfdPu is assumed '
        'already rated-current based and the IEEE generic curve is used.'
    )
    enabled_name: str = f'OverexcLimIEEE.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_name)
    model.block.event_dict[enabled_variable] = vfactory.add_const(value=None, name=enabled_name)
    return template
