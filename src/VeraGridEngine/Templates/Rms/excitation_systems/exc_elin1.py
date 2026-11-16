# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://www.mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcELIN1 static excitation controller."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcELIN1Parameters:
    """Parameters declared by the canonical CGMES ExcELIN1 class."""

    __slots__ = (
        'tfi', 'tnu', 'vpu', 'vpi', 'vpnf', 'dpnf', 'tsw', 'efmin', 'efmax',
        'xe', 'ks1', 'ks2', 'ts1', 'ts2', 'smax',
    )

    def __init__(
            self,
            tfi: float = 0.0,
            tnu: float = 2.0,
            vpu: float = 34.5,
            vpi: float = 12.45,
            vpnf: float = 2.0,
            dpnf: float = 0.0,
            tsw: float = 3.0,
            efmin: float = -5.0,
            efmax: float = 5.0,
            xe: float = 0.06,
            ks1: float = 0.0,
            ks2: float = 0.0,
            ts1: float = 1.0,
            ts2: float = 1.0,
            smax: float = 0.1,
    ) -> None:
        """Store EA typical values for the static controller and stabilizer.

        :param tfi: Field-current transducer time constant in seconds.
        :param tnu: Controller reset time constant in seconds.
        :param vpu: Voltage-controller proportional gain.
        :param vpi: Current-controller gain.
        :param vpnf: Controller follow-up gain.
        :param dpnf: Controller follow-up deadband.
        :param tsw: Power stabilizer washout time constant in seconds.
        :param efmin: Lower open-circuit excitation voltage limit.
        :param efmax: Upper open-circuit excitation voltage limit.
        :param xe: Excitation transformer effective reactance.
        :param ks1: Direct stabilizer gain.
        :param ks2: Lagged stabilizer gain.
        :param ts1: Stabilizer lag time constant in seconds.
        :param ts2: Stabilizer phase-lag time constant in seconds.
        :param smax: Symmetric stabilizer output limit.
        """
        self.tfi: float = tfi
        self.tnu: float = tnu
        self.vpu: float = vpu
        self.vpi: float = vpi
        self.vpnf: float = vpnf
        self.dpnf: float = dpnf
        self.tsw: float = tsw
        self.efmin: float = efmin
        self.efmax: float = efmax
        self.xe: float = xe
        self.ks1: float = ks1
        self.ks2: float = ks2
        self.ts1: float = ts1
        self.ts2: float = ts2
        self.smax: float = smax


def build_exc_e_l_i_n1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcELIN1Parameters | None = None,
) -> RmsModelTemplate:
    """Build the ELIN1 reset controller, current feedback, and power stabilizer.

    :param vfactory: Factory owning the symbolic graph.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Equation-backed model with Pg, voltage, reference, bias, Ifd, and Efd ports.
    :raises ValueError: Invalid time constants, limits, or nonfinite settings.
    """
    settings: ExcELIN1Parameters = ExcELIN1Parameters() if parameters is None else parameters
    template_name: str = 'ExcELIN1' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.tfi, settings.tnu, settings.vpu, settings.vpi, settings.vpnf,
        settings.dpnf, settings.tsw, settings.efmin, settings.efmax, settings.xe,
        settings.ks1, settings.ks2, settings.ts1, settings.ts2, settings.smax,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcELIN1 parameters must be finite')
    elif min(settings.tfi, settings.tsw, settings.ts1, settings.ts2) < 0.0 or settings.tnu <= 0.0:
        raise ValueError('ExcELIN1 filter times must be nonnegative and Tnu positive')
    elif settings.efmin >= settings.efmax or settings.xe < 0.0 or settings.dpnf < 0.0 or settings.smax < 0.0:
        raise ValueError('ExcELIN1 bounds, reactance, deadband, or stabilizer limit are invalid')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    tfi: Var = builder.parameter('TFI', settings.tfi)
    tnu: Var = builder.parameter('TNU', settings.tnu)
    vpu: Var = builder.parameter('VPU', settings.vpu)
    vpi: Var = builder.parameter('VPI', settings.vpi)
    vpnf: Var = builder.parameter('VPNF', settings.vpnf)
    dpnf: Var = builder.parameter('DPNF', settings.dpnf)
    tsw: Var = builder.parameter('TSW', settings.tsw)
    efmin: Var = builder.parameter('EFMIN', settings.efmin)
    efmax: Var = builder.parameter('EFMAX', settings.efmax)
    xe: Var = builder.parameter('XE', settings.xe)
    ks1: Var = builder.parameter('KS1', settings.ks1)
    ks2: Var = builder.parameter('KS2', settings.ks2)
    ts1: Var = builder.parameter('TS1', settings.ts1)
    ts2: Var = builder.parameter('TS2', settings.ts2)
    smax: Var = builder.parameter('SMAX', settings.smax)
    power: Var = builder.input('PgPu', Const(0.0))
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    bias: Var = builder.input('UsBiasPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(1.0))

    stabilizer_signal: Expr = power
    stage_index: int
    if settings.tsw == 0.0:
        stabilizer_signal = Const(0.0)
    else:
        for stage_index in range(3):
            stabilizer_signal = builder.washout(
                f'PowerWashout{stage_index + 1}Pu',
                stabilizer_signal,
                tsw,
                settings.tsw,
                Const(1.0),
                Const(0.0),
            )
    if settings.ks2 == 0.0:
        lagged_stabilizer_signal: Expr = Const(0.0)
    elif settings.ts1 == 0.0:
        lagged_stabilizer_signal = stabilizer_signal
    else:
        lagged_stabilizer_signal = builder.lag(
            'StabilizerLagPu', stabilizer_signal, ts1, settings.ts1, Const(0.0),
        )
    stabilizer_raw: Expr = ks1 * stabilizer_signal + ks2 * lagged_stabilizer_signal
    if settings.ts2 == 0.0:
        stabilizer_phase_output: Expr = Const(0.0)
    else:
        stabilizer_phase_output = builder.washout(
            'StabilizerPhasePu', stabilizer_raw, ts2, settings.ts2,
            Const(-1.0), Const(0.0),
        )
    stabilizer_output: Expr = sym.hard_sat(stabilizer_phase_output, -smax, smax)

    if settings.tfi == 0.0:
        filtered_field_current: Expr = field_current
    else:
        filtered_field_current = builder.lag(
            'FieldCurrentFilterPu', field_current, tfi, settings.tfi, Const(1.0),
        )
    controller_state: Var = vfactory.add_var(f'ControllerStatePu_{template_name}')
    followup_error: Expr = filtered_field_current - controller_state
    followup_deadband: Expr = (
        sym.max(followup_error - dpnf, Const(0.0))
        + sym.min(followup_error + dpnf, Const(0.0))
    )
    voltage_error: Expr = reference - terminal_voltage + stabilizer_output
    reset_input: Expr = vpu * voltage_error + bias + vpnf * followup_deadband
    controller_derivative: Expr = reset_input / tnu
    if settings.vpi == 0.0:
        controller_initial: Expr = Const(0.0)
    else:
        field_current_drop: Expr = xe * filtered_field_current / terminal_voltage
        required_limited_output: Expr = sym.hard_sat(Const(1.0) - field_current_drop, efmin, efmax)
        controller_initial = required_limited_output / vpi + filtered_field_current - stabilizer_output
    if settings.vpu == 0.0:
        pass
    else:
        builder.block.init_eqs[reference] = (
            terminal_voltage - stabilizer_output
            - (bias + vpnf * followup_deadband) / vpu
        )
    builder.differential(controller_state, controller_derivative, controller_initial)
    current_error: Expr = controller_state + stabilizer_output - filtered_field_current
    limited_voltage: Var = builder.algebraic(
        'LimitedExcitationVoltagePu', sym.hard_sat(vpi * current_error, efmin, efmax),
        required_limited_output,
    )
    field_voltage: Var = builder.algebraic(
        'EfdPu', limited_voltage + xe * filtered_field_current / terminal_voltage, Const(1.0),
    )
    return builder.finish((field_voltage,), 'CGMES ExcELIN1 static excitation controller')
