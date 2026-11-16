# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES ExcOEX3T IEEE Type ST1 modified exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcOEX3TParameters:
    """Scalar values that select ExcOEX3T's zero-time topology."""

    __slots__ = (
        't1', 't2', 't3', 't4', 'ka', 't5', 't6', 'vrmax', 'vrmin', 'te',
        'kf', 'tf', 'kc', 'kd', 'ke', 'e1', 'see1', 'e2', 'see2',
    )

    def __init__(
            self,
            t1: float = 0.0,
            t2: float = 0.0,
            t3: float = 0.0,
            t4: float = 0.0,
            ka: float = 0.0,
            t5: float = 0.0,
            t6: float = 0.0,
            vrmax: float = 0.0,
            vrmin: float = 0.0,
            te: float = 0.0,
            kf: float = 0.0,
            tf: float = 0.0,
            kc: float = 0.0,
            kd: float = 0.0,
            ke: float = 0.0,
            e1: float = 0.0,
            see1: float = 0.0,
            e2: float = 0.0,
            see2: float = 0.0,
    ) -> None:
        """Store the nineteen canonical RDF scalar parameters.

        :param t1: First regulator lag time.
        :param t2: First regulator lead time.
        :param t3: Final regulator lag time.
        :param t4: Final regulator lead time.
        :param ka: Regulator gain.
        :param t5: Middle regulator lag time.
        :param t6: Middle regulator lead time.
        :param vrmax: Regulator upper limiter.
        :param vrmin: Regulator lower limiter.
        :param te: Exciter field time constant.
        :param kf: Rate feedback gain.
        :param tf: Rate feedback time constant.
        :param kc: Rectifier commutation coefficient.
        :param kd: Field current demagnetization coefficient.
        :param ke: Exciter field-loss coefficient.
        :param e1: First saturation voltage point.
        :param see1: Saturation at the first point.
        :param e2: Second saturation voltage point.
        :param see2: Saturation at the second point.
        """
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.ka: float = ka
        self.t5: float = t5
        self.t6: float = t6
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.te: float = te
        self.kf: float = kf
        self.tf: float = tf
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.e1: float = e1
        self.see1: float = see1
        self.e2: float = e2
        self.see2: float = see2


def build_exc_o_e_x3_t_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcOEX3TParameters | None = None,
) -> RmsModelTemplate:
    """Build the ExcOEX3T cascaded regulator, feedback, field, and rectifier graph.

    :param vfactory: Factory allocating symbolic variables.
    :param name: Optional runtime instance name.
    :return: Equation-backed CGMES ExcOEX3T template.
    """
    template_name: str = 'ExcOEX3T' if name is None else name
    settings: ExcOEX3TParameters = ExcOEX3TParameters() if parameters is None else parameters
    parameter_names: tuple[str, ...] = (
        't1', 't2', 't3', 't4', 'ka', 't5', 't6', 'vrmax', 'vrmin',
        'te', 'kf', 'tf', 'kc', 'kd', 'ke', 'e1', 'see1', 'e2', 'see2',
    )
    default_values: tuple[float, ...] = (
        settings.t1, settings.t2, settings.t3, settings.t4, settings.ka,
        settings.t5, settings.t6, settings.vrmax, settings.vrmin, settings.te,
        settings.kf, settings.tf, settings.kc, settings.kd, settings.ke,
        settings.e1, settings.see1, settings.e2, settings.see2,
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    block: Block = Block(name=template_name)
    parameter_variables: list[Var] = list()
    for parameter_index in range(len(parameter_names)):
        parameter_name: str = parameter_names[parameter_index]
        parameter_variable: Var = vfactory.add_var(f'ExcOEX3T.{parameter_name}_{template_name}')
        block.event_dict[parameter_variable] = vfactory.add_const(
            value=default_values[parameter_index],
            name=parameter_variable.name,
        )
        parameter_variables.append(parameter_variable)
    parameter_by_name: dict[str, Var] = dict()
    for parameter_index in range(len(parameter_names)):
        parameter_by_name[parameter_names[parameter_index]] = parameter_variables[parameter_index]

    if not all(math.isfinite(value) for value in default_values):
        raise ValueError('ExcOEX3T parameters must be finite')
    elif min(settings.t1, settings.t2, settings.t3, settings.t4, settings.t5, settings.t6,
              settings.te, settings.tf) < 0.0:
        raise ValueError('ExcOEX3T time constants must be nonnegative')
    elif (
            (settings.t1 == 0.0 and settings.t2 > 0.0)
            or (settings.t3 == 0.0 and settings.t4 > 0.0)
            or (settings.t5 == 0.0 and settings.t6 > 0.0)
    ):
        raise ValueError('ExcOEX3T lead terms require their corresponding positive lag time')
    elif settings.vrmin > settings.vrmax:
        raise ValueError('ExcOEX3T regulator lower limit must be below its upper limit')
    else:
        pass

    # Named input ports preserve the CGMES signal contract for later association wiring.
    reference: Var = vfactory.add_var(f'VRefPu_ExcOEX3T_{template_name}')
    voltage_compensation: Var = vfactory.add_var(f'VcPu_ExcOEX3T_{template_name}')
    var_controller: Var = vfactory.add_var(f'UvarPu_ExcOEX3T_{template_name}')
    stabilizer: Var = vfactory.add_var(f'VsPu_ExcOEX3T_{template_name}')
    overexcitation_limiter: Var = vfactory.add_var(f'VoelPu_ExcOEX3T_{template_name}')
    underexcitation_limiter: Var = vfactory.add_var(f'VuelPu_ExcOEX3T_{template_name}')
    field_current: Var = vfactory.add_var(f'IfdPu_ExcOEX3T_{template_name}')
    field_output: Var = vfactory.add_var(f'EfdPu_ExcOEX3T_{template_name}')
    block.in_vars = [reference, voltage_compensation, var_controller, stabilizer, overexcitation_limiter,
                     underexcitation_limiter, field_current]
    block.init_eqs[reference] = Const(0.0)
    block.init_eqs[voltage_compensation] = Const(1.0)
    block.init_eqs[var_controller] = Const(0.0)
    block.init_eqs[stabilizer] = Const(0.0)
    block.init_eqs[overexcitation_limiter] = Const(0.0)
    block.init_eqs[underexcitation_limiter] = Const(0.0)
    block.init_eqs[field_current] = Const(1.0)

    t1: Var = parameter_by_name['t1']
    t2: Var = parameter_by_name['t2']
    t3: Var = parameter_by_name['t3']
    t4: Var = parameter_by_name['t4']
    ka: Var = parameter_by_name['ka']
    t5: Var = parameter_by_name['t5']
    t6: Var = parameter_by_name['t6']
    vrmax: Var = parameter_by_name['vrmax']
    vrmin: Var = parameter_by_name['vrmin']
    te: Var = parameter_by_name['te']
    kf: Var = parameter_by_name['kf']
    tf: Var = parameter_by_name['tf']
    kc: Var = parameter_by_name['kc']
    kd: Var = parameter_by_name['kd']
    ke: Var = parameter_by_name['ke']
    # Exciter rate feedback closes around Efd through the documented Kf/Tf filter.
    feedback_state: Var = vfactory.add_var(f'RateFeedbackState_ExcOEX3T_{template_name}')
    feedback: Var = vfactory.add_var(f'RateFeedbackPu_ExcOEX3T_{template_name}')
    block.algebraic_vars.append(feedback)
    if settings.tf > 0.0 and settings.kf != 0.0:
        block.state_vars.append(feedback_state)
        block.state_eqs.append((field_output - feedback_state) / tf)
        block.diff_vars.append(vfactory.add_diff_var(f'd_RateFeedbackState_ExcOEX3T_{template_name}', base_var=feedback_state))
        block.algebraic_eqs.append(feedback - kf * feedback_state)
        block.init_eqs[feedback_state] = Const(0.0)
    else:
        block.algebraic_eqs.append(feedback - kf * field_output)
    block.init_eqs[feedback] = Const(0.0)

    # Apply the external reference and limiter summation in the order shown in EA1141.
    error: Expr = reference + var_controller - voltage_compensation + stabilizer + overexcitation_limiter - underexcitation_limiter - feedback
    stage_one: Expr = error
    stage_one_state: Var | None = None
    if settings.t1 > 0.0:
        stage_one_state = vfactory.add_var(f'RegulatorStageOne_ExcOEX3T_{template_name}')
        block.state_vars.append(stage_one_state)
        block.state_eqs.append((error - stage_one_state) / t1)
        block.diff_vars.append(vfactory.add_diff_var(f'd_RegulatorStageOne_ExcOEX3T_{template_name}', base_var=stage_one_state))
        block.init_eqs[stage_one_state] = Const(0.0)
        stage_one = stage_one_state + (t2 / t1) * (error - stage_one_state)
    else:
        pass
    # The middle lead-lag precedes KA and its explicit VRMAX/VRMIN limiter.
    stage_two: Expr = stage_one
    stage_two_state: Var | None = None
    if settings.t5 > 0.0:
        stage_two_state = vfactory.add_var(f'RegulatorStageTwo_ExcOEX3T_{template_name}')
        block.state_vars.append(stage_two_state)
        block.state_eqs.append((stage_one - stage_two_state) / t5)
        block.diff_vars.append(vfactory.add_diff_var(f'd_RegulatorStageTwo_ExcOEX3T_{template_name}', base_var=stage_two_state))
        block.init_eqs[stage_two_state] = Const(0.0)
        stage_two = stage_two_state + (t6 / t5) * (stage_one - stage_two_state)
    else:
        pass
    limited_gain_output: Expr = sym.hard_sat(ka * stage_two, vrmin, vrmax)
    stage_three_state: Var | None = None
    if settings.t3 > 0.0:
        stage_three_state = vfactory.add_var(f'RegulatorStageThree_ExcOEX3T_{template_name}')
        block.state_vars.append(stage_three_state)
        block.state_eqs.append((limited_gain_output - stage_three_state) / t3)
        block.diff_vars.append(vfactory.add_diff_var(f'd_RegulatorStageThree_ExcOEX3T_{template_name}', base_var=stage_three_state))
        block.init_eqs[stage_three_state] = Const(0.0)
        regulator_output: Expr = stage_three_state + (t4 / t3) * (limited_gain_output - stage_three_state)
    else:
        regulator_output = limited_gain_output

    # Fit the two-point exponential saturation curve from the canonical field points.
    field_voltage: Var = vfactory.add_var(f'FieldVoltage_ExcOEX3T_{template_name}')
    if settings.te > 0.0:
        block.state_eqs.append(
            (regulator_output - (ke + saturation_expression(field_voltage, settings)) * field_voltage
             - kd * field_current) / te,
        )
        block.state_vars.append(field_voltage)
        block.diff_vars.append(vfactory.add_diff_var(f'd_FieldVoltage_ExcOEX3T_{template_name}', base_var=field_voltage))
    else:
        block.algebraic_vars.append(field_voltage)
        block.algebraic_eqs.append(
            regulator_output - (ke + saturation_expression(field_voltage, settings)) * field_voltage
            - kd * field_current,
        )
    block.init_eqs[field_voltage] = Const(0.0)
    block.algebraic_vars.append(field_output)
    rectifier_ratio: Expr = kc * field_current / sym.max(field_voltage, Const(1e-9))
    rectifier_factor: Expr = (
        (Const(1.0) - Const(0.58) * rectifier_ratio) * sym.heaviside(Const(0.433) - rectifier_ratio)
        + sym.sqrt(sym.max(Const(0.75) - rectifier_ratio ** Const(2.0), Const(0.0)))
        * (sym.heaviside(Const(0.75) - rectifier_ratio) - sym.heaviside(Const(0.433) - rectifier_ratio))
        + Const(1.732) * (Const(1.0) - rectifier_ratio)
        * (Const(1.0) - sym.heaviside(Const(0.75) - rectifier_ratio))
    )
    block.algebraic_eqs.append(field_output - field_voltage * rectifier_factor)
    block.init_eqs[field_output] = Const(0.0)
    block.out_vars.append(field_output)
    template.block = block
    template.comment = 'CGMES ExcOEX3T cascade, field saturation, rate feedback, and rectifier equations.'
    return template


def saturation_expression(field_voltage: Expr, parameters: ExcOEX3TParameters) -> Expr:
    """Return the exponential saturation curve through its two RDF points.

    :param field_voltage: Exciter internal field-voltage state.
    :param parameters: Two canonical RDF voltage/saturation points.
    :return: Saturation value, or zero when points cannot define a curve.
    """
    first_product: float = parameters.e1 * parameters.see1
    second_product: float = parameters.e2 * parameters.see2
    if first_product > 0.0 and second_product > 0.0 and parameters.e2 != parameters.e1:
        exponent: float = math.log(second_product / first_product) / (parameters.e2 - parameters.e1)
        coefficient: float = first_product * math.exp(-exponent * parameters.e1)
        return coefficient * sym.exp(exponent * field_voltage) / sym.max(field_voltage, Const(1e-9))
    else:
        return Const(0.0)


def rectifier_field_voltage(
        field_output: Expr,
        field_current: Expr,
        commutation_gain: float,
) -> Expr:
    """Invert the three sourced rectifier regions for operating-point initialization.

    :param field_output: Machine field voltage at the solved operating point.
    :param field_current: Machine field current at the solved operating point.
    :param commutation_gain: Canonical ExcOEX3T ``kc`` setting.
    :return: Internal field voltage consistent with the rectifier characteristic.
    """
    commutated_current: Expr = commutation_gain * field_current
    first_candidate: Expr = field_output + Const(0.58) * commutated_current
    middle_candidate: Expr = sym.sqrt(
        (field_output ** Const(2.0) + commutated_current ** Const(2.0)) / Const(0.75),
    )
    final_candidate: Expr = field_output / Const(1.732) + commutated_current
    first_ratio: Expr = commutated_current / sym.max(first_candidate, Const(1e-9))
    middle_ratio: Expr = commutated_current / sym.max(middle_candidate, Const(1e-9))
    final_ratio: Expr = commutated_current / sym.max(final_candidate, Const(1e-9))
    return (
        first_candidate * sym.heaviside(Const(0.433) - first_ratio)
        + middle_candidate * (
            sym.heaviside(Const(0.75) - middle_ratio)
            - sym.heaviside(Const(0.433) - middle_ratio)
        )
        + final_candidate * (Const(1.0) - sym.heaviside(Const(0.75) - final_ratio))
    )
