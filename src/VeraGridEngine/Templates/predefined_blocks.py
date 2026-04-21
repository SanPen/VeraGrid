# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Tuple,  Sequence
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.Symbolic.block import Block



# ----------------------------------------------------------------------------------------------------------------------
# Pre defined blocks
# ----------------------------------------------------------------------------------------------------------------------

def constant(var_factory: VarFactory, item_name: str = "") -> Block:
    """

    :param var_factory:
    :param item_name:
    :return:
    """
    name: str = "const_"
    y = var_factory.add_var(name + item_name)
    param = var_factory.add_var("param_" + item_name)

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - param],
        out_vars=[y],
        event_dict={param: var_factory.add_const(0.0)},
        name="const"
    )

    return blk


def gain(var_factory: VarFactory, item_name: str = "") -> Block:
    """

    :param var_factory:
    :param item_name:
    :return:
    """
    inputs = [var_factory.add_var("inp_num_" + item_name)]
    name: str = "gain"
    y = var_factory.add_var(name + item_name)
    gain_param = var_factory.add_var("gain_param_" + item_name)

    expr: sym.Expr = gain_param * inputs[0]
    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        out_vars=[y],
        in_vars=inputs,
        event_dict={gain_param: var_factory.add_const(0.0)},
        name="gain"
    )
    return blk


def variable(var_factory: VarFactory, name: str = "variable_", vartype: str = "vartype_") -> Tuple[sym.Var, Block]:
    """

    :param var_factory:
    :param name:
    :param vartype:
    :return:
    """
    y = var_factory.add_var(name)
    if vartype == 'state':
        blk = Block(state_vars=[y])
    else:
        blk = Block(algebraic_vars=[y])
    return y, blk


def adder(var_factory: VarFactory, item_name: str = "") -> Block:
    """

    :param var_factory:
    :param item_name:
    :return:
    """
    inputs = [var_factory.add_var("sum_in_1_" + item_name),
              var_factory.add_var("sum_in_2_" + item_name)]  # will not be specified if inputs can be more than 2
    y = var_factory.add_var("sum_out_" + item_name)

    expr: sym.Expr = inputs[0]
    for i, inpt in enumerate(inputs):
        if i > 0:
            expr += inpt

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="sum"
    )

    return blk


def substract(var_factory: VarFactory, item_name: str = "") -> Block:
    """

    :param var_factory:
    :param item_name:
    :return:
    """
    inputs = [var_factory.add_var("minuend_" + item_name), var_factory.add_var("subtrahend_" + item_name)]
    y = var_factory.add_var("difference_" + item_name)

    expr: sym.Expr = inputs[0] - inputs[1]

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="substraction"
    )

    return blk


def product(var_factory: VarFactory, item_name: str = "") -> Block:
    """

    :param var_factory:
    :param item_name:
    :return:
    """
    inputs = [var_factory.add_var("factor1_" + item_name),
              var_factory.add_var("factor2_" + item_name)]  # will not be specified if inputs can be more than 2
    y = var_factory.add_var("product_out_" + item_name)

    expr: sym.Expr = inputs[0] * inputs[1]

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="product"
    )

    return blk


def divide(var_factory: VarFactory, item_name: str = "") -> Block:
    """

    :param var_factory:
    :param item_name:
    :return:
    """
    inputs = [var_factory.add_var("divident_" + item_name),
              var_factory.add_var("divisor_" + item_name)]  # will not be specified if inputs can be more than 2
    y = var_factory.add_var("quotient_" + item_name)

    expr: sym.Expr = inputs[0] / inputs[1]

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="divide"
    )

    return blk


def absolut(var_factory: VarFactory, item_name: str = "") -> Block:
    """

    :param var_factory:
    :param item_name:
    :return:
    """
    inputs = [var_factory.add_var("inp_num_" + item_name)]  # will not be specified if inputs can be more than 2
    y = var_factory.add_var("absolut_" + item_name)

    expr: sym.Expr = sym.abs(inputs[0])

    blk = Block(
        algebraic_vars=[y],
        algebraic_eqs=[y - expr],
        in_vars=inputs,
        out_vars=[y],
        name="abs"
    )

    return blk


def integrator(var_factory: VarFactory, u: sym.Var | sym.Const, name: str = "x") -> Tuple[sym.Var, Block]:
    """

    :param var_factory:
    :param u:
    :param name:
    :return:
    """
    x = var_factory.add_var(name)
    blk = Block(state_vars=[x], state_eqs=[u])
    return x, blk


def pi_controller(var_factory: VarFactory, err: sym.Var, kp: float, ki: float, name: str = "pi") -> Block:
    """

    :param var_factory:
    :param err:
    :param kp:
    :param ki:
    :param name:
    :return:
    """
    up, blk_kp = gain(var_factory=var_factory)
    ie, blk_int = integrator(var_factory=var_factory, u=err)
    ui, blk_ki = gain(var_factory=var_factory)
    u, blk_sum = adder(var_factory=var_factory)
    return Block(name="",
                 children=[blk_kp, blk_int, blk_ki, blk_sum],
                 in_vars=[err],
                 out_vars=[u])


def generic(var_factory: VarFactory, 
            inputs: int,
            outputs: int,
            ) -> Block:
    """

    :param var_factory:
    :param inputs:
    :param outputs:
    :return:
    """
    blk = Block(
        name="generic",
        in_vars=[var_factory.add_var(f"input{i}") for i in range(inputs)],
        out_vars = [var_factory.add_var(f"output{i}") for i in range(outputs)]
        )


    return blk