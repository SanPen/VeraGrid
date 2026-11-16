# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES ExcPIC proportional-integral controlled-rectifier exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcPICParameters:
    """Canonical ExcPIC scalar fields and EA typical values."""

    __slots__ = (
        'ka', 'ta1', 'vr1', 'vr2', 'ta2', 'ta3', 'ta4', 'vrmax', 'vrmin',
        'kf', 'tf1', 'tf2', 'efdmax', 'efdmin', 'ke', 'te', 'e1', 'se1',
        'e2', 'se2', 'kp', 'ki', 'kc',
    )

    def __init__(
            self,
            ka: float = 3.15,
            ta1: float = 1.0,
            vr1: float = 1.0,
            vr2: float = -0.87,
            ta2: float = 0.01,
            ta3: float = 0.0,
            ta4: float = 0.0,
            vrmax: float = 1.0,
            vrmin: float = -0.87,
            kf: float = 0.0,
            tf1: float = 0.0,
            tf2: float = 0.0,
            efdmax: float = 8.0,
            efdmin: float = -0.87,
            ke: float = 0.0,
            te: float = 0.0,
            e1: float = 0.0,
            se1: float = 0.0,
            e2: float = 0.0,
            se2: float = 0.0,
            kp: float = 6.5,
            ki: float = 0.0,
            kc: float = 0.08,
    ) -> None:
        """Store the 23 scalar values declared by ExcPIC RDF.

        :param ka: PI regulator gain.
        :param ta1: PI regulator zero time.
        :param vr1: PI regulator upper stop.
        :param vr2: PI regulator lower stop.
        :param ta2: First regulator lag time.
        :param ta3: Lead time in the regulator compensation.
        :param ta4: Second regulator lag time.
        :param vrmax: Output regulator upper stop.
        :param vrmin: Output regulator lower stop.
        :param kf: Field-voltage rate-feedback gain.
        :param tf1: First rate-feedback lag.
        :param tf2: Second rate-feedback lag.
        :param efdmax: Exciter output upper stop.
        :param efdmin: Exciter output lower stop.
        :param ke: Exciter field-loss constant.
        :param te: Exciter field time constant.
        :param e1: First saturation voltage point.
        :param se1: Saturation at ``e1``.
        :param e2: Second saturation voltage point.
        :param se2: Saturation at ``e2``.
        :param kp: Potential-source gain.
        :param ki: Current-source gain.
        :param kc: Rectifier regulation factor.
        """
        self.ka: float = ka
        self.ta1: float = ta1
        self.vr1: float = vr1
        self.vr2: float = vr2
        self.ta2: float = ta2
        self.ta3: float = ta3
        self.ta4: float = ta4
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.kf: float = kf
        self.tf1: float = tf1
        self.tf2: float = tf2
        self.efdmax: float = efdmax
        self.efdmin: float = efdmin
        self.ke: float = ke
        self.te: float = te
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2
        self.kp: float = kp
        self.ki: float = ki
        self.kc: float = kc


def build_exc_p_i_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcPICParameters | None = None,
) -> RmsModelTemplate:
    """Build the ExcPIC regulator, rectifier, and field equations.

    :param vfactory: Factory allocating symbolic variables.
    :param name: Optional runtime instance name.
    :param parameters: Parsed RDF fields or EA typical values.
    :return: Equation-backed ExcPIC component with complex AC source ports.
    :raises ValueError: Invalid gains, times, or limiter ranges.
    """
    settings: ExcPICParameters = ExcPICParameters() if parameters is None else parameters
    template_name: str = 'ExcPIC' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.ta1, settings.vr1, settings.vr2, settings.ta2,
        settings.ta3, settings.ta4, settings.vrmax, settings.vrmin, settings.kf,
        settings.tf1, settings.tf2, settings.efdmax, settings.efdmin,
        settings.ke, settings.te, settings.e1, settings.se1, settings.e2,
        settings.se2, settings.kp, settings.ki, settings.kc,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcPIC fields must be finite')
    elif min(settings.ta1, settings.ta2, settings.ta3, settings.ta4, settings.tf1, settings.tf2, settings.te) < 0.0:
        raise ValueError('ExcPIC time constants must be nonnegative')
    elif settings.vr2 >= settings.vr1 or settings.vrmin >= settings.vrmax or settings.efdmin >= settings.efdmax:
        raise ValueError('ExcPIC lower limits must be below upper limits')
    elif settings.kf > 0.0 and (settings.tf1 <= 0.0 or settings.tf2 <= 0.0):
        raise ValueError('ExcPIC positive Kf requires positive Tf1 and Tf2')
    elif settings.ta2 == 0.0 and settings.ta3 > 0.0:
        raise ValueError('ExcPIC Ta3 lead requires positive Ta2')
    else:
        pass

    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    block: Block = Block(name=template_name)
    field_names: tuple[str, ...] = (
        'ka', 'ta1', 'vr1', 'vr2', 'ta2', 'ta3', 'ta4', 'vrmax', 'vrmin',
        'kf', 'tf1', 'tf2', 'efdmax', 'efdmin', 'ke', 'te', 'e1', 'se1',
        'e2', 'se2', 'kp', 'ki', 'kc',
    )
    field_values: tuple[float, ...] = numeric_values
    for field_index in range(len(field_names)):
        field_name: str = field_names[field_index]
        parameter_variable: Var = vfactory.add_var(f'ExcPIC.{field_name}_{template_name}')
        block.event_dict[parameter_variable] = vfactory.add_const(
            value=field_values[field_index],
            name=parameter_variable.name,
        )

    # The bridge supply uses the full terminal-voltage/current phasor sum.
    voltage_real: Var = vfactory.add_var(f'VtRePu_ExcPIC_{template_name}')
    voltage_imaginary: Var = vfactory.add_var(f'VtImPu_ExcPIC_{template_name}')
    current_real: Var = vfactory.add_var(f'ItRePu_ExcPIC_{template_name}')
    current_imaginary: Var = vfactory.add_var(f'ItImPu_ExcPIC_{template_name}')
    field_current: Var = vfactory.add_var(f'IfdPu_ExcPIC_{template_name}')
    sensed_voltage: Var = vfactory.add_var(f'UsPu_ExcPIC_{template_name}')
    reference_voltage: Var = vfactory.add_var(f'UsRefPu_ExcPIC_{template_name}')
    supplementary_voltage: Var = vfactory.add_var(f'UpssPu_ExcPIC_{template_name}')
    inputs: list[Var] = [
        voltage_real, voltage_imaginary, current_real, current_imaginary,
        field_current, sensed_voltage, reference_voltage, supplementary_voltage,
    ]
    block.in_vars = inputs
    block.init_eqs[voltage_real] = Const(1.0)
    block.init_eqs[voltage_imaginary] = Const(0.0)
    block.init_eqs[current_real] = Const(0.0)
    block.init_eqs[current_imaginary] = Const(0.0)
    block.init_eqs[field_current] = Const(1.0)
    block.init_eqs[sensed_voltage] = Const(1.0)
    block.init_eqs[reference_voltage] = Const(1.0)
    block.init_eqs[supplementary_voltage] = Const(0.0)

    # Rectifier commutation reduces the AC bridge voltage as field current rises.
    bridge_real: Expr = settings.kp * voltage_real - settings.ki * current_imaginary
    bridge_imaginary: Expr = settings.kp * voltage_imaginary + settings.ki * current_real
    bridge_voltage: Expr = sym.sqrt(bridge_real ** Const(2.0) + bridge_imaginary ** Const(2.0))
    current_ratio: Expr = settings.kc * field_current / sym.max(bridge_voltage, Const(1e-9))
    below_first_break: Expr = sym.heaviside(Const(0.433) - current_ratio)
    below_second_break: Expr = sym.heaviside(Const(0.75) - current_ratio)
    first_region: Expr = Const(1.0) - Const(0.58) * current_ratio
    middle_region: Expr = sym.sqrt(sym.max(Const(0.75) - current_ratio ** Const(2.0), Const(0.0)))
    final_region: Expr = Const(1.732) * (Const(1.0) - current_ratio)
    rectifier_factor: Expr = (
        first_region * below_first_break
        + middle_region * (below_second_break - below_first_break)
        + final_region * (Const(1.0) - below_second_break)
    )
    bridge_output: Expr = bridge_voltage * rectifier_factor

    # The PI output and the two regulator lags retain independent memories.
    feedback_signal: Var = vfactory.add_var(f'RateFeedbackPu_ExcPIC_{template_name}')
    block.algebraic_vars.append(feedback_signal)
    error: Expr = reference_voltage - sensed_voltage + supplementary_voltage - feedback_signal
    pi_state: Var = vfactory.add_var(f'PIState_ExcPIC_{template_name}')
    block.state_vars.append(pi_state)
    block.state_eqs.append(settings.ka * error)
    block.diff_vars.append(vfactory.add_diff_var(f'd_PIState_ExcPIC_{template_name}', base_var=pi_state))
    proportional_integral: Var = vfactory.add_var(f'PIOutput_ExcPIC_{template_name}')
    block.algebraic_vars.append(proportional_integral)
    block.algebraic_eqs.append(
        proportional_integral
        - sym.hard_sat(pi_state + settings.ka * settings.ta1 * error, settings.vr2, settings.vr1),
    )

    regulator_signal: Expr = proportional_integral
    regulator_state: Var | None = None
    phase_state: Var | None = None
    if settings.ta2 > 0.0:
        regulator_state = vfactory.add_var(f'RegulatorLag_ExcPIC_{template_name}')
        block.state_vars.append(regulator_state)
        block.state_eqs.append((regulator_signal - regulator_state) / settings.ta2)
        block.diff_vars.append(
            vfactory.add_diff_var(f'd_RegulatorLag_ExcPIC_{template_name}', base_var=regulator_state),
        )
        regulator_signal = regulator_signal + (settings.ta3 / settings.ta2) * (regulator_signal - regulator_state)
    else:
        pass
    if settings.ta4 > 0.0:
        phase_state = vfactory.add_var(f'PhaseLag_ExcPIC_{template_name}')
        block.state_vars.append(phase_state)
        block.state_eqs.append((regulator_signal - phase_state) / settings.ta4)
        block.diff_vars.append(
            vfactory.add_diff_var(f'd_PhaseLag_ExcPIC_{template_name}', base_var=phase_state),
        )
        regulator_signal = phase_state
    else:
        pass
    regulator_output: Var = vfactory.add_var(f'VrPu_ExcPIC_{template_name}')
    block.algebraic_vars.append(regulator_output)
    block.algebraic_eqs.append(
        regulator_output - sym.hard_sat(regulator_signal, settings.vrmin, settings.vrmax),
    )

    # The rate feedback is a two-pole washout of delivered field voltage.
    field_state: Var | None = None
    if settings.te > 0.0:
        field_state = vfactory.add_var(f'FieldState_ExcPIC_{template_name}')
        block.state_vars.append(field_state)
        block.diff_vars.append(vfactory.add_diff_var(f'd_FieldState_ExcPIC_{template_name}', base_var=field_state))
    else:
        pass
    field_output: Var = vfactory.add_var(f'EfdPu_ExcPIC_{template_name}')
    block.algebraic_vars.append(field_output)
    block.out_vars = list((field_output,))
    # Fit saturation on the internal field voltage, not the measured terminal reference.
    saturation_enabled: bool = (
        settings.e1 > 0.0 and settings.e2 > settings.e1
        and settings.se1 > 0.0 and settings.se2 > 0.0
    )
    if saturation_enabled:
        saturation_slope: float = math.log(
            settings.e2 * settings.se2 / (settings.e1 * settings.se1),
        ) / (settings.e2 - settings.e1)
        saturation_base: float = settings.se1 * math.exp(-saturation_slope * settings.e1)
        saturation_voltage: Expr = field_state if field_state is not None else field_output
        saturation: Expr = Const(saturation_base) * sym.exp(Const(saturation_slope) * saturation_voltage)
    else:
        saturation: Expr = Const(0.0)
    feedback_first: Var | None = None
    feedback_second: Var | None = None
    if settings.kf > 0.0:
        feedback_first = vfactory.add_var(f'RateFeedbackFirst_ExcPIC_{template_name}')
        feedback_second = vfactory.add_var(f'RateFeedbackSecond_ExcPIC_{template_name}')
        block.state_vars.extend((feedback_first, feedback_second))
        block.diff_vars.extend((
            vfactory.add_diff_var(f'd_RateFeedbackFirst_ExcPIC_{template_name}', base_var=feedback_first),
            vfactory.add_diff_var(f'd_RateFeedbackSecond_ExcPIC_{template_name}', base_var=feedback_second),
        ))
        block.state_eqs.extend((
            (field_output - feedback_first) / settings.tf1,
            ((field_output - feedback_first) / settings.tf1 - feedback_second) / settings.tf2,
        ))
        feedback: Expr = settings.kf * feedback_second
    else:
        feedback = Const(0.0)
    block.algebraic_eqs.append(feedback_signal - feedback)

    # Use the EA two-point exponential when present and zero saturation otherwise.
    if field_state is not None:
        block.algebraic_eqs.append(field_output - sym.hard_sat(field_state, settings.efdmin, settings.efdmax))
        field_loss: Expr = (settings.ke + saturation) * field_state
        field_equation: Expr = (regulator_output * bridge_output - field_loss) / settings.te
        field_state_index: int = block.state_vars.index(field_state)
        block.state_eqs.insert(field_state_index, field_equation)
        block.init_eqs[field_state] = Const(1.0)
    else:
        block.init_eqs[field_output] = Const(1.0)
        block.algebraic_eqs.append(
            (settings.ke + saturation) * field_output
            - regulator_output * bridge_output,
        )
        block.algebraic_eqs.append(field_output - sym.hard_sat(field_output, settings.efdmin, settings.efdmax))
    initial_field_voltage: Expr = field_state if field_state is not None else field_output
    initial_regulator_output: Expr = (
        (settings.ke + saturation) * initial_field_voltage
        / sym.max(bridge_output, Const(1e-9))
    )
    block.init_eqs[pi_state] = initial_regulator_output - settings.ka * settings.ta1 * error
    if regulator_state is not None:
        block.init_eqs[regulator_state] = initial_regulator_output
    else:
        pass
    if phase_state is not None:
        block.init_eqs[phase_state] = initial_regulator_output
    else:
        pass
    if feedback_first is not None and feedback_second is not None:
        block.init_eqs[feedback_first] = Const(1.0)
        block.init_eqs[feedback_second] = Const(0.0)
    else:
        pass

    template.block = block
    template.comment = 'CGMES ExcPIC PI regulator, bridge commutation, saturation, and field equations.'
    return template
