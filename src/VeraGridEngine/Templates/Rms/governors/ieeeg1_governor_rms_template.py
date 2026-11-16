# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Standard IEEE Type-1 steam-turbine governor RMS model."""

from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.Utils.Symbolic.symbolic import Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ieeeg1RmsParameters:
    """Numerical parameters and structural time constants for IEEEG1."""

    __slots__ = (
        "k", "t1", "t2", "t3", "uo", "uc", "pmax", "pmin", "t4",
        "k1", "k2", "t5", "k3", "k4", "t6", "k5", "k6", "t7", "k7", "k8",
    )

    def __init__(
        self: "Ieeeg1RmsParameters",
        values: tuple[float, ...],
    ) -> None:
        """Store the twenty standard IEEEG1 parameters.

        :param values: ``K,T1,T2,T3,UO,UC,PMAX,PMIN,T4,K1,K2,T5,K3,K4,T6,K5,K6,T7,K7,K8``.
        :return: None.
        """
        if len(values) == 20:
            pass
        else:
            raise ValueError(f"IEEEG1 requires 20 values; received {len(values)}.")
        (
            self.k, self.t1, self.t2, self.t3, self.uo, self.uc,
            self.pmax, self.pmin, self.t4, self.k1, self.k2, self.t5,
            self.k3, self.k4, self.t6, self.k5, self.k6, self.t7,
            self.k7, self.k8,
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


def get_ieeeg1_governor_rms_template(
    vfactory: VarFactory,
    include_t7_state: bool,
    name: str = "IEEEG1 governor RMS template",
) -> RmsModelTemplate:
    """Build an IEEEG1 block in the normal interior-limiter regime.

    WECC records use zero ``T5`` and ``T6`` and therefore retain only the
    lead-lag, valve, first-process and optional fourth-process states.

    :param vfactory: Shared symbolic variable factory.
    :param include_t7_state: Retain the fourth-process lag when ``T7`` is nonzero.
    :param name: Block name.
    :return: IEEEG1 governor template.
    """
    template: RmsModelTemplate = RmsModelTemplate(name=name)
    template.tpe = DeviceType.GeneratorDevice
    omega_var: Var = vfactory.add_var("omega_", shared_reference="omega_reference")
    te_var: Var = vfactory.add_var("Te_", shared_reference="te_reference")
    tm_var: Var = vfactory.add_var("Tm", shared_reference="tm_reference")
    ll_state: Var = vfactory.add_var("LL_x")
    valve_state: Var = vfactory.add_var("IAW_y")
    l4_state: Var = vfactory.add_var("L4_y")
    l7_state: Var | None
    if include_t7_state:
        l7_state = vfactory.add_var("L7_y")
    else:
        l7_state = None
    block: Block = Block(name=name)
    names: tuple[str, ...] = (
        "K", "T1", "T2", "T3", "UO", "UC", "PMAX", "PMIN", "T4",
        "K1", "K2", "T5", "K3", "K4", "T6", "K5", "K6", "T7", "K7", "K8",
    )
    defaults: tuple[float, ...] = (
        20.0, 0.1, 0.0, 0.2, 1.0, -1.0, 1.0, 0.0, 0.1,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.0, 8.72, 0.7, 0.0,
    )
    parameters: list[Var] = list()
    parameter_name: str
    default_value: float
    for parameter_name, default_value in zip(names, defaults):
        parameters.append(_parameter(block, vfactory, parameter_name, default_value))
    (
        k_var, t1_var, t2_var, t3_var, uo_var, uc_var, pmax_var, pmin_var,
        t4_var, k1_var, k2_var, t5_var, k3_var, k4_var, t6_var, k5_var,
        k6_var, t7_var, k7_var, k8_var,
    ) = parameters
    tm_hold: Var = _parameter(block, vfactory, "Tm_initial", None)
    wd_var: Var = vfactory.add_var("wd")
    ll_output: Var = vfactory.add_var("LL_y")
    valve_speed: Var = vfactory.add_var("vs")
    php_var: Var = vfactory.add_var("PHP")
    sum_k: Expr = k1_var + k2_var + k3_var + k4_var + k5_var + k6_var + k7_var + k8_var
    normalized_k1: Expr = k1_var / sum_k
    normalized_k3: Expr = k3_var / sum_k
    normalized_k5: Expr = k5_var / sum_k
    normalized_k7: Expr = k7_var / sum_k
    l5_output: Expr = l4_state
    l6_output: Expr = l4_state
    if l7_state is None:
        l7_output: Expr = l4_state
    else:
        l7_output = l7_state
    block.state_vars = list((ll_state, valve_state, l4_state))
    block.state_eqs = list((
        (wd_var - ll_state) / t1_var,
        valve_speed,
        (valve_state - l4_state) / t4_var,
    ))
    if l7_state is None:
        pass
    else:
        block.state_vars.append(l7_state)
        block.state_eqs.append((l6_output - l7_state) / t7_var)
    block.algebraic_vars = list((wd_var, ll_output, valve_speed, php_var, tm_var))
    block.algebraic_eqs = list((
        sym.Const(1.0) - omega_var - wd_var,
        k_var * (t2_var / t1_var * (wd_var - ll_state) + ll_state) - ll_output,
        (ll_output + tm_hold - valve_state) / t3_var - valve_speed,
        normalized_k1 * l4_state + normalized_k3 * l5_output
        + normalized_k5 * l6_output + normalized_k7 * l7_output - php_var,
        php_var - tm_var,
    ))
    block.init_eqs = dict()
    block.init_eqs[tm_hold] = te_var
    block.init_eqs[wd_var] = sym.Const(0.0)
    block.init_eqs[ll_state] = sym.Const(0.0)
    block.init_eqs[ll_output] = sym.Const(0.0)
    block.init_eqs[valve_speed] = sym.Const(0.0)
    block.init_eqs[valve_state] = te_var
    block.init_eqs[l4_state] = te_var
    if l7_state is None:
        pass
    else:
        block.init_eqs[l7_state] = te_var
    block.init_eqs[php_var] = te_var
    block.init_eqs[tm_var] = te_var
    block.in_vars = list((omega_var, te_var))
    block.out_vars = list((tm_var,))
    template.block.children.append(block)
    template.block.in_vars = list(block.in_vars)
    template.block.out_vars = list(block.out_vars)
    return template


def configure_ieeeg1_block(
    block: Block,
    parameters: Ieeeg1RmsParameters,
    vfactory: VarFactory,
) -> None:
    """Configure one IEEEG1 block.

    :param block: IEEEG1 symbolic block.
    :param parameters: Numerical record.
    :param vfactory: Shared variable factory.
    :return: None.
    """
    names: tuple[str, ...] = (
        "K", "T1", "T2", "T3", "UO", "UC", "PMAX", "PMIN", "T4",
        "K1", "K2", "T5", "K3", "K4", "T6", "K5", "K6", "T7", "K7", "K8",
    )
    values: tuple[float, ...] = (
        parameters.k, parameters.t1, parameters.t2, parameters.t3,
        parameters.uo, parameters.uc, parameters.pmax, parameters.pmin,
        parameters.t4, parameters.k1, parameters.k2, parameters.t5,
        parameters.k3, parameters.k4, parameters.t6, parameters.k5,
        parameters.k6, parameters.t7, parameters.k7, parameters.k8,
    )
    name: str
    value: float
    for name, value in zip(names, values):
        matches: list[Var] = list(variable for variable in block.event_dict if variable.name == name)
        if len(matches) == 1:
            block.event_dict[matches[0]] = vfactory.add_const(value=value, name=name)
        else:
            raise ValueError(f"Expected one IEEEG1 parameter {name!r}; found {len(matches)}.")
