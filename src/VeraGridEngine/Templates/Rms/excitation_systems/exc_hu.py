# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://www.mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcHU two-loop PI excitation controller."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcHUParameters:
    """Settings declared by the canonical CGMES ExcHU class."""

    __slots__ = (
        'tr', 'te', 'imin', 'imax', 'ae', 'emin', 'emax', 'ki', 'ai', 'ti', 'atr', 'ke',
    )

    def __init__(
            self,
            tr: float = 0.01,
            te: float = 0.154,
            imin: float = 0.1,
            imax: float = 2.19,
            ae: float = 3.0,
            emin: float = -0.866,
            emax: float = 0.996,
            ki: float = 0.21428,
            ai: float = 22.0,
            ti: float = 0.01333,
            atr: float = 2.19,
            ke: float = 4.666,
    ) -> None:
        """Store the typical values stated on the local EA parameter page.

        :param tr: Terminal-voltage filter time constant in seconds.
        :param te: Major-loop current-reference integrator time constant.
        :param imin: Major-loop lower output limit.
        :param imax: Major-loop upper output limit.
        :param ae: Major-loop proportional gain.
        :param emin: Minor-loop field-voltage command lower limit.
        :param emax: Minor-loop field-voltage command upper limit.
        :param ki: Field-current measurement gain.
        :param ai: Minor-loop proportional gain.
        :param ti: Minor-loop integrator time constant in seconds.
        :param atr: AVR-base gain between minor-loop output and Efd prime.
        :param ke: Voltage-base conversion gain to system Efd.
        """
        self.tr: float = tr
        self.te: float = te
        self.imin: float = imin
        self.imax: float = imax
        self.ae: float = ae
        self.emin: float = emin
        self.emax: float = emax
        self.ki: float = ki
        self.ai: float = ai
        self.ti: float = ti
        self.atr: float = atr
        self.ke: float = ke


def build_exc_h_u_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcHUParameters | None = None,
) -> RmsModelTemplate:
    """Build the bounded major/minor PI loops and ExcHU Efd conversion.

    :param vfactory: Factory owning the symbolic graph.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Model with terminal voltage, reference, supplementary, Ifd, and Efd ports.
    :raises ValueError: Invalid finite values, time constants, or output limits.
    """
    settings: ExcHUParameters = ExcHUParameters() if parameters is None else parameters
    template_name: str = 'ExcHU' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.tr, settings.te, settings.imin, settings.imax, settings.ae,
        settings.emin, settings.emax, settings.ki, settings.ai, settings.ti,
        settings.atr, settings.ke,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcHU parameters must be finite')
    elif min(settings.tr, settings.te, settings.ti) < 0.0:
        raise ValueError('ExcHU time constants must be nonnegative')
    elif settings.imin > settings.imax or settings.emin > settings.emax:
        raise ValueError('ExcHU PI output limits must be ordered')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    tr: Var = builder.parameter('TR', settings.tr)
    te: Var = builder.parameter('TE', settings.te)
    imin: Var = builder.parameter('IMIN', settings.imin)
    imax: Var = builder.parameter('IMAX', settings.imax)
    ae: Var = builder.parameter('AE', settings.ae)
    emin: Var = builder.parameter('EMIN', settings.emin)
    emax: Var = builder.parameter('EMAX', settings.emax)
    ki: Var = builder.parameter('KI', settings.ki)
    ai: Var = builder.parameter('AI', settings.ai)
    ti: Var = builder.parameter('TI', settings.ti)
    atr: Var = builder.parameter('ATR', settings.atr)
    ke: Var = builder.parameter('KE', settings.ke)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(1.0))

    if settings.tr == 0.0:
        filtered_voltage: Expr = terminal_voltage
    else:
        filtered_voltage = builder.lag(
            'VoltageFilterPu', terminal_voltage, tr, settings.tr, terminal_voltage,
        )
    builder.block.init_eqs[reference] = filtered_voltage - supplementary
    voltage_error: Expr = reference - filtered_voltage + supplementary
    if settings.te == 0.0:
        major_integrator: Expr = Const(0.0)
    else:
        major_integrator_state: Var = vfactory.add_var(f'MajorIntegratorPu_{template_name}')
        major_integrator = builder.differential(
            major_integrator_state,
            voltage_error / te,
            sym.hard_sat(ki * field_current, imin, imax),
            imin,
            imax,
        )
    major_current_reference: Var = builder.algebraic(
        'MajorCurrentReferencePu',
        sym.hard_sat(major_integrator + ae * voltage_error, imin, imax),
        sym.hard_sat(ki * field_current, imin, imax),
    )
    minor_current_error: Var = builder.algebraic(
        'MinorCurrentErrorPu', major_current_reference - ki * field_current,
        sym.hard_sat(ki * field_current, imin, imax) - ki * field_current,
    )
    if settings.ti == 0.0:
        minor_integrator: Expr = Const(0.0)
    else:
        minor_integrator_state: Var = vfactory.add_var(f'MinorIntegratorPu_{template_name}')
        minor_initial: Expr = sym.hard_sat(
            Const(1.0) / (ke * atr) - ai * minor_current_error,
            emin,
            emax,
        ) if settings.ke * settings.atr != 0.0 else Const(0.0)
        minor_integrator = builder.differential(
            minor_integrator_state,
            minor_current_error / ti,
            minor_initial,
            emin,
            emax,
        )
    minor_voltage_command: Var = builder.algebraic(
        'MinorVoltageCommandPu',
        sym.hard_sat(minor_integrator + ai * minor_current_error, emin, emax),
        sym.hard_sat(Const(1.0) / (ke * atr), emin, emax)
        if settings.ke * settings.atr != 0.0 else Const(0.0),
    )
    field_voltage: Var = builder.algebraic(
        'EfdPu', ke * atr * minor_voltage_command, Const(1.0),
    )
    return builder.finish((field_voltage,), 'CGMES ExcHU two-loop PI exciter')
