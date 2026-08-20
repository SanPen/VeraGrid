# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Standard ST2CUT dual-input power-system stabilizer RMS model."""

from __future__ import annotations

from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class St2cutInputMode(Enum):
    """WECC ST2CUT input modes supported by this standard realization."""

    ROTOR_SPEED = 1
    ELECTRICAL_POWER = 3


class St2cutRmsParameters:
    """Numerical parameters for one ST2CUT stabilizer."""

    __slots__ = (
        "mode", "k1", "t1", "t3", "t4", "t5", "t6", "t7", "t8",
        "t9", "t10", "lsmax", "lsmin", "power_scale",
    )

    def __init__(
        self: "St2cutRmsParameters",
        mode: St2cutInputMode,
        values: tuple[float, ...],
        power_scale: float,
    ) -> None:
        """Store one ST2CUT parameter record.

        :param mode: Primary input-signal selection.
        :param values: ``K1,T1,T3,T4,T5,T6,T7,T8,T9,T10,LSMAX,LSMIN``.
        :param power_scale: Machine-to-system rating ratio ``Sn/Sbase``.
        :return: None.
        """
        if len(values) == 12:
            pass
        else:
            raise ValueError(f"ST2CUT requires 12 values; received {len(values)}.")
        self.mode: St2cutInputMode = mode
        (
            self.k1, self.t1, self.t3, self.t4, self.t5, self.t6,
            self.t7, self.t8, self.t9, self.t10, self.lsmax, self.lsmin,
        ) = values
        self.power_scale: float = power_scale


def _parameter(block: Block, vfactory: VarFactory, name: str, value: float) -> Var:
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


def get_st2cut_stabilizer_rms_template(
    vfactory: VarFactory,
    input_mode: St2cutInputMode,
    include_input_lag: bool,
    include_second_lead_lag: bool,
    include_third_lead_lag: bool,
    name: str = "ST2CUT stabilizer RMS template",
) -> RmsModelTemplate:
    """Build the WECC structural variants of ST2CUT.

    :param vfactory: Shared symbolic variable factory.
    :param input_mode: Rotor-speed or electrical-power input.
    :param include_input_lag: Retain ``L1_y`` when ``T1`` is nonzero.
    :param include_second_lead_lag: Retain ``LL2_x`` when ``T8`` is nonzero.
    :param include_third_lead_lag: Retain ``LL3_x`` when ``T10`` is nonzero.
    :param name: Template name.
    :return: ST2CUT stabilizer template.
    """
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.GeneratorDevice
    omega_var: Var = vfactory.add_var("omega_", shared_reference="omega_reference")
    te_var: Var = vfactory.add_var("Te_", shared_reference="te_reference")
    l1_state: Var | None
    if include_input_lag:
        l1_state = vfactory.add_var("L1_y")
    else:
        l1_state = None
    wo_state: Var = vfactory.add_var("WO_x")
    ll1_state: Var = vfactory.add_var("LL1_x")
    ll2_state: Var | None
    if include_second_lead_lag:
        ll2_state = vfactory.add_var("LL2_x")
    else:
        ll2_state = None
    ll3_state: Var | None
    if include_third_lead_lag:
        ll3_state = vfactory.add_var("LL3_x")
    else:
        ll3_state = None
    output_var: Var = vfactory.add_var("vsout")
    block: Block = Block(name=name)
    names: tuple[str, ...] = (
        "K1", "T1", "T3", "T4", "T5", "T6", "T7", "T8",
        "T9", "T10", "LSMAX", "LSMIN", "power_scale",
    )
    defaults: tuple[float, ...] = (
        5.5, 0.03, 10.0, 10.0, 0.4, 0.04, 0.0, 0.0,
        0.0, 0.0, 0.05, -0.05, 1.0,
    )
    parameters: list[Var] = list()
    parameter_name: str
    default_value: float
    for parameter_name, default_value in zip(names, defaults):
        parameters.append(_parameter(block, vfactory, parameter_name, default_value))
    (
        k1_var, t1_var, t3_var, t4_var, t5_var, t6_var, t7_var,
        t8_var, t9_var, t10_var, lsmax_var, lsmin_var, power_scale_var,
    ) = parameters
    if input_mode is St2cutInputMode.ROTOR_SPEED:
        signal: Expr = omega_var - sym.Const(1.0)
    else:
        signal = te_var / power_scale_var
    if l1_state is None:
        input_output: Expr = k1_var * signal
    else:
        input_output = l1_state
    wo_output: Expr = t3_var / t4_var * (input_output - wo_state)
    ll1_output: Expr = t5_var / t6_var * (wo_output - ll1_state) + ll1_state
    if ll2_state is None:
        ll2_output: Expr = ll1_output
    else:
        ll2_output = t7_var / t8_var * (ll1_output - ll2_state) + ll2_state
    if ll3_state is None:
        ll3_output: Expr = ll2_output
    else:
        ll3_output = t9_var / t10_var * (ll2_output - ll3_state) + ll3_state
    block.state_vars = list()
    block.state_eqs = list()
    if l1_state is None:
        pass
    else:
        block.state_vars.append(l1_state)
        block.state_eqs.append((k1_var * signal - l1_state) / t1_var)
    block.state_vars.append(wo_state)
    block.state_eqs.append((input_output - wo_state) / t4_var)
    block.state_vars.append(ll1_state)
    block.state_eqs.append((wo_output - ll1_state) / t6_var)
    if ll2_state is None:
        pass
    else:
        block.state_vars.append(ll2_state)
        block.state_eqs.append((ll1_output - ll2_state) / t8_var)
    if ll3_state is None:
        pass
    else:
        block.state_vars.append(ll3_state)
        block.state_eqs.append((ll2_output - ll3_state) / t10_var)
    block.algebraic_vars = list((output_var,))
    block.algebraic_eqs = list((
        sym.min(sym.max(ll3_output, lsmin_var), lsmax_var) - output_var,
    ))
    block.init_eqs = dict()
    if l1_state is None:
        pass
    else:
        block.init_eqs[l1_state] = k1_var * signal
    block.init_eqs[wo_state] = input_output
    block.init_eqs[ll1_state] = sym.Const(0.0)
    if ll2_state is None:
        pass
    else:
        block.init_eqs[ll2_state] = sym.Const(0.0)
    if ll3_state is None:
        pass
    else:
        block.init_eqs[ll3_state] = sym.Const(0.0)
    block.init_eqs[output_var] = sym.Const(0.0)
    block.in_vars = list((omega_var, te_var))
    block.out_vars = list((output_var,))
    template.block.children.append(block)
    template.block.in_vars = list(block.in_vars)
    template.block.out_vars = list(block.out_vars)
    return template


def configure_st2cut_block(
    block: Block,
    parameters: St2cutRmsParameters,
    vfactory: VarFactory,
) -> None:
    """Configure one ST2CUT block.

    :param block: ST2CUT symbolic block.
    :param parameters: Numerical record.
    :param vfactory: Shared variable factory.
    :return: None.
    """
    names: tuple[str, ...] = (
        "K1", "T1", "T3", "T4", "T5", "T6", "T7", "T8",
        "T9", "T10", "LSMAX", "LSMIN", "power_scale",
    )
    values: tuple[float, ...] = (
        parameters.k1, parameters.t1, parameters.t3, parameters.t4,
        parameters.t5, parameters.t6, parameters.t7, parameters.t8,
        parameters.t9, parameters.t10, parameters.lsmax, parameters.lsmin,
        parameters.power_scale,
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
                f"Expected one ST2CUT parameter {parameter_name!r}; found {len(matches)}."
            )
