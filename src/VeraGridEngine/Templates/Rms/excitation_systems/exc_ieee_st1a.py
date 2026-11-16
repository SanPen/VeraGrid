# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE ST1A terminal-fed excitation template."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import ExcIEEEST1AUELselectorKind
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEST1AParameters:
    """Parameter values declared by the canonical ExcIEEEST1A RDF class."""

    __slots__ = (
        'ilr', 'ka', 'kc', 'kf', 'klr', 'pssin', 'ta', 'tb', 'tb1', 'tc',
        'tc1', 'tf', 'uelin', 'vamax', 'vamin', 'vimax', 'vimin', 'vrmax',
        'vrmin',
    )

    def __init__(
            self,
            ilr: float = 0.0,
            ka: float = 190.0,
            kc: float = 0.08,
            kf: float = 0.0,
            klr: float = 0.0,
            pssin: bool = True,
            ta: float = 0.0,
            tb: float = 10.0,
            tb1: float = 0.0,
            tc: float = 1.0,
            tc1: float = 0.0,
            tf: float = 1.0,
            uelin: ExcIEEEST1AUELselectorKind = ExcIEEEST1AUELselectorKind.ignoreUELsignal,
            vamax: float = 14.5,
            vamin: float = -14.5,
            vimax: float = 999.0,
            vimin: float = -999.0,
            vrmax: float = 7.8,
            vrmin: float = -6.7,
    ) -> None:
        """Store exact RDF values with local EA typical-value fallbacks.

        :param ilr: Exciter output current-limit reference.
        :param ka: Voltage-regulator gain.
        :param kc: Rectifier commutation/loading factor.
        :param kf: Excitation-system stabilizer gain.
        :param klr: Exciter output current-limit gain.
        :param pssin: Add PSS voltage before the regulator when true.
        :param ta: Regulator time constant in seconds.
        :param tb: First regulator lag time in seconds.
        :param tb1: Second regulator lag time in seconds.
        :param tc: First regulator lead time in seconds.
        :param tc1: Second regulator lead time in seconds.
        :param tf: Stabilizer washout time in seconds.
        :param uelin: Canonical four-way UEL connection selector.
        :param vamax: Regulator output upper limit.
        :param vamin: Regulator output lower limit.
        :param vimax: Regulator input upper limit.
        :param vimin: Regulator input lower limit.
        :param vrmax: Rectifier output upper limit.
        :param vrmin: Rectifier output lower limit.
        """
        self.ilr: float = ilr
        self.ka: float = ka
        self.kc: float = kc
        self.kf: float = kf
        self.klr: float = klr
        self.pssin: bool = pssin
        self.ta: float = ta
        self.tb: float = tb
        self.tb1: float = tb1
        self.tc: float = tc
        self.tc1: float = tc1
        self.tf: float = tf
        self.uelin: ExcIEEEST1AUELselectorKind = uelin
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.vimax: float = vimax
        self.vimin: float = vimin
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin


def build_exc_i_e_e_e_s_t1_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEST1AParameters | None = None,
) -> RmsModelTemplate:
    """Build IEEE ST1A lead-lag, limited regulator, and terminal-fed bridge.

    :param vfactory: Factory that allocates the equation symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed RDF settings or the local EA typicals.
    :return: Equation-backed ST1A with terminal, current, PSS, and UEL ports.
    :raises ValueError: Invalid limits, time constants, or selector value.
    """
    settings: ExcIEEEST1AParameters = (
        ExcIEEEST1AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEST1A' if name is None else name
    values: tuple[float, ...] = (
        settings.ilr, settings.ka, settings.kc, settings.kf, settings.klr,
        settings.ta, settings.tb, settings.tb1, settings.tc, settings.tc1,
        settings.tf, settings.vamax, settings.vamin, settings.vimax,
        settings.vimin, settings.vrmax, settings.vrmin,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('ExcIEEEST1A parameters must be finite')
    elif min(settings.ta, settings.tb, settings.tb1, settings.tc, settings.tc1, settings.tf) < 0.0:
        raise ValueError('ExcIEEEST1A time constants must be nonnegative')
    elif settings.vamin >= settings.vamax or settings.vimin >= settings.vimax:
        raise ValueError('ExcIEEEST1A regulator bounds must be ordered')
    elif settings.vrmin >= settings.vrmax:
        raise ValueError('ExcIEEEST1A rectifier bounds must be ordered')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcIEEEST1A first lead-lag requires zero lead with zero lag')
    elif settings.tb1 == 0.0 and settings.tc1 != 0.0:
        raise ValueError('ExcIEEEST1A second lead-lag requires zero lead with zero lag')
    elif settings.kf != 0.0 and settings.tf == 0.0:
        raise ValueError('ExcIEEEST1A nonzero KF requires positive TF')
    elif not isinstance(settings.uelin, ExcIEEEST1AUELselectorKind):
        raise ValueError('ExcIEEEST1A UEL selector must use its canonical RDF enumeration')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    tc: Var = builder.parameter('TC', settings.tc)
    tb: Var = builder.parameter('TB', settings.tb)
    tc1: Var = builder.parameter('TC1', settings.tc1)
    tb1: Var = builder.parameter('TB1', settings.tb1)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    vimax: Var = builder.parameter('VIMAX', settings.vimax)
    vimin: Var = builder.parameter('VIMIN', settings.vimin)
    vamax: Var = builder.parameter('VAMAX', settings.vamax)
    vamin: Var = builder.parameter('VAMIN', settings.vamin)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    kc: Var = builder.parameter('KC', settings.kc)
    kf: Var = builder.parameter('KF', settings.kf)
    tf: Var = builder.parameter('TF', settings.tf)
    ilr: Var = builder.parameter('ILR', settings.ilr)
    klr: Var = builder.parameter('KLR', settings.klr)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))
    terminal_current: Var = builder.input('ItPu', Const(0.0))
    uel_signal: Var = builder.input('UelPu', Const(0.0))
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')

    feedback: Expr = Const(0.0)
    if settings.kf != 0.0:
        feedback = builder.washout(
            'FeedbackPu', field_voltage, tf, settings.tf,
            Const(settings.kf / settings.tf), Const(0.0),
        )
    else:
        pass
    pss_at_input: Expr = stabilizer if settings.pssin else Const(0.0)
    error: Expr = reference - terminal_voltage + pss_at_input - feedback
    if settings.uelin == ExcIEEEST1AUELselectorKind.inputAddedToErrorSignal:
        error = error + uel_signal
    elif settings.uelin == ExcIEEEST1AUELselectorKind.inputHVgateErrorSignal:
        error = sym.max(error, uel_signal)
    else:
        pass
    regulator_input: Var = builder.algebraic(
        'RegulatorInputPu', sym.hard_sat(error, vimin, vimax), Const(0.0),
    )
    compensated_1: Var = builder.lead_lag(
        'LeadLag1Pu', regulator_input, tc, tb,
        settings.tc, settings.tb, Const(0.0),
    )
    compensated_2: Var = builder.lead_lag(
        'LeadLag2Pu', compensated_1, tc1, tb1,
        settings.tc1, settings.tb1, Const(0.0),
    )
    regulator_stage: Var = builder.lag(
        'RegulatorStagePu', ka * compensated_2,
        ta, settings.ta, Const(0.0), vamin, vamax,
    )
    regulator_output_expression: Expr = regulator_stage
    if settings.pssin is False:
        regulator_output_expression = sym.hard_sat(
            regulator_stage + stabilizer,
            vamin,
            vamax,
        )
    else:
        pass
    regulator_output: Var = builder.algebraic(
        'RegulatorOutputPu', regulator_output_expression, Const(0.0),
    )
    if settings.uelin == ExcIEEEST1AUELselectorKind.inputHVgateVoltageOutput:
        gated_regulator: Expr = sym.max(regulator_output, uel_signal)
    else:
        gated_regulator = regulator_output
    current_limited: Expr = gated_regulator - klr * sym.max(
        field_current - ilr, Const(0.0),
    )
    rectifier_output: Expr = sym.hard_sat(
        current_limited,
        terminal_voltage * vrmin,
        terminal_voltage * vrmax - kc * field_current,
    )
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(field_voltage - rectifier_output)
    builder.block.init_eqs[field_voltage] = Const(1.0)
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcIEEEST1A terminal-fed controlled rectifier',
    )
    for parameter_name in (
            'enabled', 'ilr', 'ka', 'kc', 'kf', 'klr', 'pssin', 'ta', 'tb',
            'tb1', 'tc', 'tc1', 'tf', 'uelin', 'vamax', 'vamin', 'vimax',
            'vimin', 'vrmax', 'vrmin',
    ):
        variable_name: str = f'ExcIEEEST1A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    return template
