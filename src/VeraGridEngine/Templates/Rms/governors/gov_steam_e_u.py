# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovSteamEU boiler and steam governor."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.governors.govsteameu import (
    build_govsteameu_template,
)
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Expr, Var


def build_gov_steam_e_u_template(
        vfactory: VarFactory,
        name: str | None = None,
        tf_value: float = 1e-9,
        tw_value: float = 0.02,
        tdp_value: float = 1e-9,
        tfp_value: float = 1e-9,
) -> RmsModelTemplate:
    """Build GovSteamEU equations and retain the canonical RDF parameter fields.

    :param vfactory: Factory owning the equation and RDF symbols.
    :param name: Optional model instance name.
    :param tf_value: Imported frequency-filter time constant.
    :param tw_value: Imported speed-filter time constant.
    :param tdp_value: Imported derivative gain.
    :param tfp_value: Imported derivative-filter time constant.
    :return: Equation-backed model with its exact CGMES parameter surface.
    """
    template_name: str = "GovSteamEU" if name is None else name
    template: RmsModelTemplate = build_govsteameu_template(
        vf=vfactory,
        name=template_name,
    )
    # Replace zero-time first-order states by their exact algebraic limits.
    zero_time_lags: tuple[tuple[str, str, float], ...] = (
        ("gov.firstOrdertfT.y_", "gov.fPu_", tf_value),
        ("gov.firstOrdertOmega.y_", "gov.omegaPu_", tw_value),
    )
    for state_stem, input_stem, time_constant in zero_time_lags:
        if time_constant == 0.0:
            state_index: int | None = None
            state_variable: Var | None = None
            input_variable: Var | None = None
            gain_variable: Var | None = None
            for variable_index, variable in enumerate(template.block.state_vars):
                if variable.name.startswith(state_stem):
                    state_index = variable_index
                    state_variable = variable
                else:
                    pass
            for variable in template.block.in_vars:
                if variable.name.startswith(input_stem):
                    input_variable = variable
                else:
                    pass
            for event_variable in template.block.event_dict:
                if event_variable.name.startswith(state_stem.replace(".y_", ".k_")):
                    gain_variable = event_variable
                else:
                    pass
            if state_index is not None and state_variable is not None and input_variable is not None and gain_variable is not None:
                differential_variable: Var = template.block.diff_vars[state_index]
                template.block.init_eqs.pop(state_variable, None)
                template.block.diff_init_eqs.pop(differential_variable, None)
                template.block.update_equations(
                    state_variable,
                    gain_variable * input_variable,
                )
                template.block.state_vars.pop(state_index)
                template.block.diff_vars.pop(state_index)
                template.block.state_eqs.pop(state_index)
            else:
                pass
        else:
            pass

    # A zero derivative gain makes its filter state and output identically unused.
    if tdp_value == 0.0:
        derivative_state_index: int | None = None
        derivative_state: Var | None = None
        derivative_input: Var | None = None
        derivative_output: Var | None = None
        for variable_index, variable in enumerate(template.block.state_vars):
            if variable.name.startswith("gov.derivativetDPctPc.x_"):
                derivative_state_index = variable_index
                derivative_state = variable
            else:
                pass
        for variable in template.block.algebraic_vars:
            if variable.name.startswith("gov.addPe.y_"):
                derivative_input = variable
            elif variable.name.startswith("gov.derivativetDPctPc.y_"):
                derivative_output = variable
            else:
                pass
        if derivative_state_index is not None and derivative_state is not None and derivative_input is not None and derivative_output is not None:
            derivative_variable: Var = template.block.diff_vars[derivative_state_index]
            template.block.init_eqs.pop(derivative_state, None)
            template.block.diff_init_eqs.pop(derivative_variable, None)
            template.block.update_equations(derivative_state, derivative_input)
            template.block.state_vars.pop(derivative_state_index)
            template.block.diff_vars.pop(derivative_state_index)
            template.block.state_eqs.pop(derivative_state_index)
            for equation_index, equation in enumerate(template.block.algebraic_eqs):
                if isinstance(equation, BinOp) and equation.left is derivative_output:
                    template.block.algebraic_eqs[equation_index] = derivative_output
                else:
                    pass
            template.block.init_eqs[derivative_output] = vfactory.add_const(value=0.0)
        else:
            pass
    elif tfp_value == 0.0:
        derivative_state_index: int | None = None
        derivative_state: Var | None = None
        derivative_input: Var | None = None
        derivative_output: Var | None = None
        derivative_gain: Var | None = None
        for variable_index, variable in enumerate(template.block.state_vars):
            if variable.name.startswith("gov.derivativetDPctPc.x_"):
                derivative_state_index = variable_index
                derivative_state = variable
            else:
                pass
        for variable in template.block.algebraic_vars:
            if variable.name.startswith("gov.addPe.y_"):
                derivative_input = variable
            elif variable.name.startswith("gov.derivativetDPctPc.y_"):
                derivative_output = variable
            else:
                pass
        for event_variable in template.block.event_dict:
            if event_variable.name.startswith("gov.derivativetDPctPc.k_"):
                derivative_gain = event_variable
            else:
                pass
        if (
                derivative_state_index is not None
                and derivative_state is not None
                and derivative_input is not None
                and derivative_output is not None
                and derivative_gain is not None
        ):
            # The DAE compiler finite-differences algebraic variables that own a diff variable.
            state_derivative: Var = template.block.diff_vars[derivative_state_index]
            template.block.init_eqs.pop(derivative_state, None)
            template.block.diff_init_eqs.pop(state_derivative, None)
            template.block.state_vars.pop(derivative_state_index)
            template.block.diff_vars.pop(derivative_state_index)
            template.block.state_eqs.pop(derivative_state_index)
            input_derivative: Var = vfactory.add_diff_var(
                name=f'd_{derivative_input.name}',
                base_var=derivative_input,
            )
            template.block.diff_vars.append(input_derivative)
            template.block.diff_init_eqs[input_derivative] = vfactory.add_const(value=0.0)
            for equation_index, equation in enumerate(template.block.algebraic_eqs):
                if isinstance(equation, BinOp) and equation.left is derivative_output:
                    template.block.algebraic_eqs[equation_index] = (
                        derivative_output - derivative_gain * input_derivative
                    )
                else:
                    pass
        else:
            pass
    else:
        pass
    reference_input: Var | None = None
    reference_sum: Var | None = None
    reference_sum_k1: Var | None = None
    reference_sum_k2: Var | None = None
    frequency_correction: Var | None = None
    for input_variable in template.block.in_vars:
        if input_variable.name.startswith("gov.PRefPu_"):
            reference_input = input_variable
        else:
            pass
    for algebraic_variable in template.block.algebraic_vars:
        if algebraic_variable.name.startswith("gov.addPRef.y_"):
            reference_sum = algebraic_variable
        elif algebraic_variable.name.startswith("gov.addPRef.k1_"):
            reference_sum_k1 = algebraic_variable
        elif algebraic_variable.name.startswith("gov.addPRef.k2_"):
            reference_sum_k2 = algebraic_variable
        elif algebraic_variable.name.startswith("gov.limiterDeltaF.y_"):
            frequency_correction = algebraic_variable
        else:
            pass

    # Restore the RDF reference term which the generated RMS graph replaced with a constant.
    if (
            reference_input is not None
            and reference_sum is not None
            and reference_sum_k1 is not None
            and reference_sum_k2 is not None
            and frequency_correction is not None
    ):
        for equation_index, equation in enumerate(template.block.algebraic_eqs):
            if isinstance(equation, BinOp) and equation.left is reference_sum:
                template.block.algebraic_eqs[equation_index] = reference_sum - (
                    reference_sum_k1 * frequency_correction
                    + reference_sum_k2 * reference_input
                )
            else:
                pass
    else:
        pass

    # Give every explicit algebraic assignment the same expression as its initial seed.
    for equation in template.block.algebraic_eqs:
        if (
                isinstance(equation, BinOp)
                and equation.op == "-"
                and isinstance(equation.left, Var)
                and equation.left in template.block.algebraic_vars
        ):
            target_variable: Var = equation.left
            initialization_expression: Expr = equation.right
            template.block.init_eqs[target_variable] = initialization_expression
        else:
            pass

    parameter_names: tuple[str, ...] = (
        "enabled", "mwbase", "tp", "ke", "tip", "tdp", "tfp", "tf", "kfcor",
        "db1", "wfmax", "wfmin", "pmax", "ten", "tw", "komegacor", "db2",
        "wwmax", "wwmin", "wmax1", "wmax2", "tvhp", "cho", "chc", "hhpmax",
        "tvip", "cio", "cic", "simx", "thp", "trh", "tlp", "prhmax", "khp",
        "klp", "tb",
    )
    for parameter_name in parameter_names:
        variable_name: str = f"GovSteamEU.{parameter_name}_{template_name}"
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    template.comment = "CGMES GovSteamEU using the equation-backed boiler and steam turbine graph."
    return template
