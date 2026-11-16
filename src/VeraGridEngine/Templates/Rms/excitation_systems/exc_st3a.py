# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcST3A compound-source excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcST3AParameters:
    """The exact scalar parameters declared by the CGMES ExcST3A RDF class."""

    __slots__ = (
        'vimax', 'vimin', 'kj', 'tb', 'tc', 'efdmax', 'km', 'tm', 'vrmax',
        'vrmin', 'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax', 'vgmax',
        'ks', 'ks1',
    )

    def __init__(
            self,
            vimax: float = 0.2,
            vimin: float = -0.2,
            kj: float = 200.0,
            tb: float = 6.67,
            tc: float = 1.0,
            efdmax: float = 6.9,
            km: float = 7.04,
            tm: float = 1.0,
            vrmax: float = 1.0,
            vrmin: float = 0.0,
            kg: float = 1.0,
            kp: float = 4.37,
            thetap: float = 20.0,
            ki: float = 4.83,
            kc: float = 1.1,
            xl: float = 0.09,
            vbmax: float = 8.63,
            vgmax: float = 6.53,
            ks: float = 0.0,
            ks1: float = 0.0,
    ) -> None:
        """Store CGMES fields using the typical values in the EA class notes.

        :param vimax: Regulator input upper limit.
        :param vimin: Regulator input lower limit.
        :param kj: Voltage regulator gain.
        :param tb: Regulator lead-lag denominator time in seconds.
        :param tc: Regulator lead-lag numerator time in seconds.
        :param efdmax: Maximum exciter output.
        :param km: Inner field-regulator gain.
        :param tm: Inner field-regulator lag time in seconds.
        :param vrmax: Outer regulator upper output limit.
        :param vrmin: Outer regulator lower output limit.
        :param kg: Inner field-voltage feedback gain.
        :param kp: Potential-source gain.
        :param thetap: Potential-source phase shift in degrees.
        :param ki: Current-source gain.
        :param kc: Rectifier commutation loading gain.
        :param xl: Potential-source leakage reactance.
        :param vbmax: Rectifier output upper limit.
        :param vgmax: Inner feedback upper limit.
        :param ks: Output generator-speed multiplier coefficient.
        :param ks1: Rectifier-source generator-speed multiplier coefficient.
        """
        self.vimax: float = vimax
        self.vimin: float = vimin
        self.kj: float = kj
        self.tb: float = tb
        self.tc: float = tc
        self.efdmax: float = efdmax
        self.km: float = km
        self.tm: float = tm
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.kg: float = kg
        self.kp: float = kp
        self.thetap: float = thetap
        self.ki: float = ki
        self.kc: float = kc
        self.xl: float = xl
        self.vbmax: float = vbmax
        self.vgmax: float = vgmax
        self.ks: float = ks
        self.ks1: float = ks1


def exc_st3a_commutation_factor(normalized_loading: Expr) -> Expr:
    """Evaluate the piecewise commutation characteristic shown in EA1157.

    :param normalized_loading: Rectifier current loading ``Kc*Ifd/Ve``.
    :return: Continuous five-region rectifier commutation factor.
    """
    lower_boundary: Expr = Const(0.433)
    middle_boundary: Expr = Const(0.75)
    zero_region: Expr = sym.Const(1.0) - sym.heaviside(normalized_loading)
    first_region: Expr = (
        sym.heaviside(normalized_loading)
        - sym.heaviside(normalized_loading - lower_boundary)
    ) * (Const(1.0) - Const(0.577) * normalized_loading)
    middle_region_gate: Expr = (
        sym.heaviside(normalized_loading - lower_boundary)
        - sym.heaviside(middle_boundary - normalized_loading)
    )
    safe_radicand: Expr = Const(1.0) + middle_region_gate * (
        middle_boundary - normalized_loading ** 2 - Const(1.0)
    )
    middle_region: Expr = middle_region_gate * sym.sqrt(safe_radicand)
    upper_region: Expr = (
        sym.heaviside(normalized_loading - middle_boundary)
        - sym.heaviside(normalized_loading - Const(1.0))
    ) * Const(1.732) * (Const(1.0) - normalized_loading)
    return zero_region + first_region + middle_region + upper_region


def build_exc_s_t3_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcST3AParameters | None = None,
) -> RmsModelTemplate:
    """Build the CGMES ST3A regulator, compound source, rectifier, and field loop.

    :param vfactory: Factory allocating the model symbols.
    :param name: Optional unique runtime name.
    :param parameters: Parsed canonical CGMES fields or EA reference values.
    :return: Equation-backed template with direct-axis machine signal ports.
    :raises ValueError: Invalid regulator, exciter, or rectifier parameter set.
    """
    settings: ExcST3AParameters = ExcST3AParameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.vimax, settings.vimin, settings.kj, settings.tb, settings.tc,
        settings.efdmax, settings.km, settings.tm, settings.vrmax, settings.vrmin,
        settings.kg, settings.kp, settings.thetap, settings.ki, settings.kc,
        settings.xl, settings.vbmax, settings.vgmax, settings.ks, settings.ks1,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcST3A parameters must be finite')
    elif settings.vimin >= settings.vimax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcST3A regulator limits are invalid')
    elif settings.kj <= 0.0 or settings.km <= 0.0 or settings.tb <= 0.0 or settings.tm < 0.0:
        raise ValueError('ExcST3A Kj, Km, Tb, and Tm values are invalid')
    elif settings.tc < 0.0 or min(
            settings.efdmax, settings.kg, settings.kp, settings.ki,
            settings.kc, settings.xl, settings.vbmax, settings.vgmax,
    ) < 0.0:
        raise ValueError('ExcST3A source, field, and time parameters are invalid')
    else:
        pass

    # Keep signal-port names aligned with the direct-axis machine composition interface.
    template_name: str = 'ExcST3A' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    field_current: Var = control.input('XadIfd', Const(0.5))
    terminal_voltage: Var = control.input('Vm', Const(1.0))
    voltage_d: Var = control.input('Vd', Const(1.0))
    voltage_q: Var = control.input('Vq', Const(0.0))
    current_d: Var = control.input('Id', Const(0.0))
    current_q: Var = control.input('Iq', Const(0.0))
    supplementary_voltage: Var = control.input('VsPu', Const(0.0))
    speed: Var = control.input('OmegaPu', Const(1.0))
    voltage_reference: Var = control.input('Vref', Const(1.0))

    # Rotate the terminal-voltage source and add the quadrature current-compounding source.
    phase_angle: Var = control.parameter('thetap', settings.thetap) * Const(math.pi / 180.0)
    potential_real: Expr = control.parameter('kp', settings.kp) * (
        sym.cos(phase_angle) * voltage_d - sym.sin(phase_angle) * voltage_q
    )
    potential_imag: Expr = control.parameter('kp', settings.kp) * (
        sym.sin(phase_angle) * voltage_d + sym.cos(phase_angle) * voltage_q
    )
    current_gain_real: Expr = control.parameter('ki', settings.ki) + (
        control.parameter('xl', settings.xl) * control.parameter('kp', settings.kp)
        * sym.cos(phase_angle)
    )
    current_gain_imag: Expr = (
        control.parameter('xl', settings.xl) * control.parameter('kp', settings.kp)
        * sym.sin(phase_angle)
    )
    current_term_real: Expr = -(
        current_gain_real * current_q + current_gain_imag * current_d
    )
    current_term_imag: Expr = (
        current_gain_real * current_d - current_gain_imag * current_q
    )
    source_voltage: Expr = sym.sqrt(
        (potential_real + current_term_real) ** 2
        + (potential_imag + current_term_imag) ** 2
    )
    rectifier_source: Var = control.algebraic(
        'CompoundSourcePu', source_voltage, source_voltage,
    )
    rectifier_loading: Expr = sym.safe_divide(
        control.parameter('kc', settings.kc) * field_current,
        rectifier_source,
        Const(1.0),
    )
    commutation_factor: Var = control.algebraic(
        'CommutationFactorPu', exc_st3a_commutation_factor(rectifier_loading),
        exc_st3a_commutation_factor(rectifier_loading),
    )
    rectifier_speed: Expr = Const(1.0) + control.parameter('ks1', settings.ks1) * (
        speed - Const(1.0)
    )
    rectifier_voltage: Var = control.algebraic(
        'RectifierVoltagePu',
        sym.min(
            rectifier_source * rectifier_speed * commutation_factor,
            control.parameter('vbmax', settings.vbmax),
        ),
        sym.min(
            rectifier_source * rectifier_speed * commutation_factor,
            control.parameter('vbmax', settings.vbmax),
        ),
    )

    # The voltage regulator limits its error before Kj and the lead-lag stage.
    voltage_error: Expr = voltage_reference + supplementary_voltage - rectifier_source
    limited_error: Var = control.algebraic(
        'RegulatorInputPu',
        sym.hard_sat(
            voltage_error,
            control.parameter('vimin', settings.vimin),
            control.parameter('vimax', settings.vimax),
        ),
        sym.hard_sat(
            voltage_error,
            control.parameter('vimin', settings.vimin),
            control.parameter('vimax', settings.vimax),
        ),
    )
    regulator_command: Expr = control.parameter('kj', settings.kj) * limited_error
    regulator_initial: Expr = regulator_command
    regulator_lead_lag: Var = control.lead_lag(
        'RegulatorLeadLagPu', regulator_command,
        control.parameter('tc', settings.tc), control.parameter('tb', settings.tb),
        settings.tc, settings.tb, regulator_initial,
    )
    regulator_voltage: Var = control.algebraic(
        'RegulatorVoltagePu',
        sym.hard_sat(
            regulator_lead_lag,
            control.parameter('vrmin', settings.vrmin),
            control.parameter('vrmax', settings.vrmax),
        ),
        sym.hard_sat(
            regulator_initial,
            control.parameter('vrmin', settings.vrmin),
            control.parameter('vrmax', settings.vrmax),
        ),
    )

    # Inner feedback limits the field signal before the exciter lag and output ceiling.
    field_voltage_unscaled: Var = vfactory.add_var('FieldVoltageUnscaledPu_')
    control.block.algebraic_vars.append(field_voltage_unscaled)
    control.block.init_eqs[field_voltage_unscaled] = Const(1.0)
    field_feedback: Var = control.algebraic(
        'FieldFeedbackPu',
        sym.min(
            control.parameter('kg', settings.kg) * field_voltage_unscaled,
            control.parameter('vgmax', settings.vgmax),
        ),
        sym.min(
            control.parameter('kg', settings.kg) * field_voltage_unscaled,
            control.parameter('vgmax', settings.vgmax),
        ),
    )
    exciter_voltage: Var = control.lag(
        'ExciterVoltagePu',
        control.parameter('km', settings.km) * (regulator_voltage - field_feedback),
        control.parameter('tm', settings.tm), settings.tm,
        control.parameter('km', settings.km) * (regulator_voltage - field_feedback),
    )
    control.block.algebraic_eqs.append(
        field_voltage_unscaled - sym.hard_sat(
            exciter_voltage * rectifier_voltage,
            Const(0.0),
            control.parameter('efdmax', settings.efdmax),
        )
    )
    control.block.init_eqs[field_voltage_unscaled] = sym.hard_sat(
        exciter_voltage * rectifier_voltage,
        Const(0.0),
        control.parameter('efdmax', settings.efdmax),
    )
    speed_factor: Expr = Const(1.0) + control.parameter('ks', settings.ks) * (
        speed - Const(1.0)
    )
    field_voltage: Var = vfactory.add_var('Vf')
    control.block.algebraic_vars.append(field_voltage)
    control.block.algebraic_eqs.append(field_voltage - field_voltage_unscaled * speed_factor)
    control.block.init_eqs[field_voltage] = field_voltage_unscaled * speed_factor

    runtime: RmsModelTemplate = control.finish(
        (field_voltage,), 'CGMES ExcST3A compound-source static excitation system',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    runtime.block.name = template_name
    template.comment = 'CGMES ExcST3A equations from the canonical EA1157 diagram.'

    # Preserve every exact RDF scalar field as a distinct imported event.
    rdf_parameter_names: tuple[str, ...] = (
        'enabled', 'vimax', 'vimin', 'kj', 'tb', 'tc', 'efdmax', 'km', 'tm',
        'vrmax', 'vrmin', 'kg', 'kp', 'thetap', 'ki', 'kc', 'xl', 'vbmax',
        'vgmax', 'ks', 'ks1',
    )
    for parameter_name in rdf_parameter_names:
        parameter_variable: Var = vfactory.add_var(
            f'ExcST3A.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template
