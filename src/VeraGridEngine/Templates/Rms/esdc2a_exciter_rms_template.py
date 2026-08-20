# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Standard IEEE ESDC2A direct-current excitation-system RMS model."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Esdc2aRmsParameters:
    """Numerical parameters for one ESDC2A excitation system."""

    __slots__ = (
        "tr", "ka", "ta", "tb", "tc", "vrmax", "vrmin", "ke", "te",
        "kf", "tf1", "e1", "se1", "e2", "se2",
    )

    def __init__(self: "Esdc2aRmsParameters", values: tuple[float, ...]) -> None:
        """Store the fifteen ESDC2A parameters.

        :param values: ``TR,KA,TA,TB,TC,VRMAX,VRMIN,KE,TE,KF,TF1,E1,SE1,E2,SE2``.
        :return: None.
        """
        if len(values) == 15:
            pass
        else:
            raise ValueError(f"ESDC2A requires 15 values; received {len(values)}.")
        (
            self.tr, self.ka, self.ta, self.tb, self.tc, self.vrmax,
            self.vrmin, self.ke, self.te, self.kf, self.tf1,
            self.e1, self.se1, self.e2, self.se2,
        ) = values


def _parameter(block: Block, vfactory: VarFactory, name: str, value: float | None) -> Var:
    """Add one event parameter.

    :param block: Owning block.
    :param vfactory: Shared variable factory.
    :param name: Parameter name.
    :param value: Default value.
    :return: Parameter variable.
    """
    variable: Var = vfactory.add_var(name)
    block.event_dict[variable] = vfactory.add_const(value=value, name=name)
    return variable


def _saturation_coefficients(
    e1_var: Var,
    se1_var: Var,
    e2_var: Var,
    se2_var: Var,
) -> tuple[Expr, Expr]:
    """Return threshold and quadratic coefficient through two saturation points.

    :param e1_var: First voltage point.
    :param se1_var: First saturation factor.
    :param e2_var: Second voltage point.
    :param se2_var: Second saturation factor.
    :return: Saturation threshold and coefficient.
    """
    ratio: Expr = sym.sqrt(se1_var * e1_var / (se2_var * e2_var))
    threshold: Expr = (e1_var - ratio * e2_var) / (sym.Const(1.0) - ratio)
    coefficient: Expr = se1_var * e1_var / (e1_var - threshold) ** 2
    return threshold, coefficient


def get_esdc2a_exciter_rms_template(
    vfactory: VarFactory,
    name: str = "ESDC2A exciter RMS template",
) -> RmsModelTemplate:
    """Build the standard five-state ESDC2A realization.

    :param vfactory: Shared symbolic variable factory.
    :param name: Template name.
    :return: ESDC2A exciter template.
    """
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.GeneratorDevice
    vm_var: Var = vfactory.add_var("Vm_", reference=VarPowerFlowReferenceType.Vm)
    vf_var: Var = vfactory.add_var("Vf", shared_reference="vf_reference")
    vpss_var: Var = vfactory.add_var("vpss")
    lg_state: Var = vfactory.add_var("LG_y")
    ll_state: Var = vfactory.add_var("LL_x")
    la_state: Var = vfactory.add_var("LA_y")
    int_state: Var = vfactory.add_var("INT_y")
    wf_state: Var = vfactory.add_var("WF_x")
    block: Block = Block(name=name)
    names: tuple[str, ...] = (
        "TR", "KA", "TA", "TB", "TC", "VRMAX", "VRMIN", "KE", "TE",
        "KF", "TF1", "E1", "SE1", "E2", "SE2",
    )
    defaults: tuple[float, ...] = (
        0.02, 50.0, 0.05, 0.02, 0.0, 0.0, -3.0, 0.0, 0.5,
        0.07, 1.0, 3.0, 0.5, 5.0, 1.0,
    )
    parameters: list[Var] = list()
    parameter_name: str
    default_value: float
    for parameter_name, default_value in zip(names, defaults):
        parameters.append(_parameter(block, vfactory, parameter_name, default_value))
    (
        tr_var, ka_var, ta_var, tb_var, tc_var, vrmax_var, vrmin_var,
        ke_var, te_var, kf_var, tf1_var, e1_var, se1_var, e2_var, se2_var,
    ) = parameters
    vref_hold: Var = _parameter(block, vfactory, "vref0", None)
    vi_var: Var = vfactory.add_var("vi")
    ll_output: Var = vfactory.add_var("LL_y")
    wf_output: Var = vfactory.add_var("WF_y")
    se_var: Var = vfactory.add_var("Se")
    vfe_var: Var = vfactory.add_var("VFE")
    saturation_threshold, saturation_coefficient = _saturation_coefficients(
        e1_var, se1_var, e2_var, se2_var
    )
    saturation: Expr = sym.heaviside(int_state - saturation_threshold) * (
        int_state - saturation_threshold
    ) ** 2 * saturation_coefficient
    block.state_vars = list((lg_state, ll_state, la_state, int_state, wf_state))
    block.state_eqs = list((
        (vm_var - lg_state) / tr_var,
        (vi_var - ll_state) / tb_var,
        (ka_var * ll_output - la_state) / ta_var,
        (la_state - vfe_var) / te_var,
        (int_state - wf_state) / tf1_var,
    ))
    block.algebraic_vars = list((
        vi_var, ll_output, wf_output, se_var, vfe_var, vf_var,
    ))
    block.algebraic_eqs = list((
        vref_hold - vm_var - wf_output + vpss_var - vi_var,
        tc_var / tb_var * (vi_var - ll_state) + ll_state - ll_output,
        kf_var / tf1_var * (int_state - wf_state) - wf_output,
        saturation - se_var,
        ke_var * int_state + se_var - vfe_var,
        int_state - vf_var,
    ))
    initial_saturation: Expr = sym.heaviside(vf_var - saturation_threshold) * (
        vf_var - saturation_threshold
    ) ** 2 * saturation_coefficient
    initial_vfe: Expr = ke_var * vf_var + initial_saturation
    initial_vi: Expr = initial_vfe / ka_var
    block.init_eqs = dict()
    block.init_eqs[lg_state] = vm_var
    block.init_eqs[vi_var] = initial_vi
    block.init_eqs[ll_state] = initial_vi
    block.init_eqs[ll_output] = initial_vi
    block.init_eqs[la_state] = initial_vfe
    block.init_eqs[int_state] = vf_var
    block.init_eqs[wf_state] = vf_var
    block.init_eqs[wf_output] = sym.Const(0.0)
    block.init_eqs[se_var] = initial_saturation
    block.init_eqs[vfe_var] = initial_vfe
    block.init_eqs[vref_hold] = vm_var + initial_vi
    block.in_vars = list((vm_var, vpss_var))
    block.out_vars = list((vf_var,))
    template.block.children.append(block)
    template.block.in_vars = list(block.in_vars)
    template.block.out_vars = list(block.out_vars)
    return template


def configure_esdc2a_block(
    block: Block,
    parameters: Esdc2aRmsParameters,
    vfactory: VarFactory,
) -> None:
    """Configure one ESDC2A block.

    :param block: ESDC2A symbolic block.
    :param parameters: Numerical record.
    :param vfactory: Shared variable factory.
    :return: None.
    """
    names: tuple[str, ...] = (
        "TR", "KA", "TA", "TB", "TC", "VRMAX", "VRMIN", "KE", "TE",
        "KF", "TF1", "E1", "SE1", "E2", "SE2",
    )
    values: tuple[float, ...] = (
        parameters.tr, parameters.ka, parameters.ta, parameters.tb,
        parameters.tc, parameters.vrmax, parameters.vrmin, parameters.ke,
        parameters.te, parameters.kf, parameters.tf1, parameters.e1,
        parameters.se1, parameters.e2, parameters.se2,
    )
    parameter_name: str
    value: float
    for parameter_name, value in zip(names, values):
        matches: list[Var] = list(
            variable for variable in block.event_dict if variable.name == parameter_name
        )
        if len(matches) == 1:
            block.event_dict[matches[0]] = vfactory.add_const(value=value, name=parameter_name)
        else:
            raise ValueError(
                f"Expected one ESDC2A parameter {parameter_name!r}; found {len(matches)}."
            )
