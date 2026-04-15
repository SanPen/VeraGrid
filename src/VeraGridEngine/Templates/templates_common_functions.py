# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import numpy as np
from typing import Tuple, Optional, List, Any
from typing import Tuple, Optional, List, Callable, Dict

from VeraGridEngine import VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.Utils.Symbolic.symbolic import (Var, Const, Expr, CmpOp, Comparison, heaviside, hard_sat, expression2numba, get_expression_vars)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DeviceType, ParamPowerFlowRefferenceType



def tf_to_block(var_factory: VarFactory,
                num: List[Var | float],
                den: List[Var | float],
                x: Var | Expr,
                y: Var = None,
                create_state: bool = False,
                name: Optional[str] = '') -> Tuple[Block, Var]:
    """
    "transform definition" to block
    num: list of numerator coefficients [b0, b1, ..., bm]
    den: list of denominator coefficients [a0, a1, ..., an]
    x:   sympy symbol for input
    y:   sympy function of t for output
    """
    if len(num) > len(den):
        raise ValueError("Transfer function is improper: numerator degree > denominator degree.")

    if y is None:
        y = var_factory.add_var('y_' + name)

    aux_eqs: List[Expr] = list()
    aux_vars: List[Expr] = list()
    init_eqs = dict()
    diff_init_eqs = dict()  # ADDED
    x_save = x  # Initialize x_save to avoid unbound variable error
    # check if is an expression
    if not isinstance(x, Var):
        u = var_factory.add_var('u_' + name)
        aux_eqs.append((u - x).simplify())
        aux_vars.append(u)
        init_eqs[u] = x
        x = u

    diff_vars_x = [x]
    diff_vars_y = [y]
    diff_vars = list()
    state_eqs = list()
    state_vars = list()
    base_var = x
    for i in range(1, len(num)):
        if i == 1 and create_state:
            x_new = var_factory.add_var(f"x_{i}_" + x.name)
            state_vars.append(x_new)
            state_eqs.append(x_save)  # x is already a Var
            diff_vars_x.append(x_new)
            base_var = x_new
            init_eqs[x_new] = Const(0.0)
        else:
            if base_var.diff_var is None:
                new_diff = var_factory.add_diff_var(name=f'dt_{i}_' + x.name, base_var=base_var)
                diff_vars.append(new_diff)
                diff_init_eqs[new_diff] = Const(0.0)  # ADDED
            diff_vars_x.append(base_var.diff_var)
            base_var = base_var.diff_var
    base_var = y
    for i in range(1, len(den)):
        if base_var.diff_var is None:
            new_diff = var_factory.add_diff_var(name=f'dt_{i}_' + y.name, base_var=base_var)
            diff_vars.append(new_diff)
            diff_init_eqs[new_diff] = Const(0.0)  # ADDED
        diff_vars_y.append(base_var.diff_var)
        base_var = base_var.diff_var

    # Create the diff equation
    rhs = np.array(diff_vars_x) @ np.array(num)
    lhs = np.array(diff_vars_y) @ np.array(den)

    # Pure integrator-style blocks (den[0] == 0) need a derivative init that
    # matches the input, otherwise the first consistency check leaves a residual.
    if len(den) > 1 and den[0] == 0 and y.base_var is not None:
        diff_init_eqs[y.diff_var] = x / den[1]

    block = Block()
    block.algebraic_vars = [y] + aux_vars
    block.algebraic_eqs = [lhs - rhs] + aux_eqs
    block.state_eqs     = state_eqs
    block.state_vars    = state_vars
    block.diff_vars     = diff_vars
    block.in_vars       = [x]  # Input is x
    block.out_vars      = [y]  # Output is y
    block.init_eqs      = init_eqs
    block.diff_init_eqs = diff_init_eqs  # ADDED
    return block, y



def tf_to_diffblock_with_output(
        var_factory: VarFactory,
        num: List[Var | float],
        den: List[Var | float],
        x: Var | Expr,
        y: Var = None,
        create_state: bool = False,
        name: Optional[str] = ''):
    """
    num: list of numerator coefficients [b0, b1, ..., bm]
    den: list of denominator coefficients [a0, a1, ..., an]
    x:   sympy symbol for input
    y:   sympy function of t for output
    """
    if len(num) > len(den):
        raise ValueError("Transfer function is improper: numerator degree > denominator degree.")
    if (isinstance(num[-1], float) and num[-1] == 0) or (isinstance(den[-1], float) and den[-1] == 0):
        raise ValueError("Leading coefficient of numerator or denominator cannot be zero.")

    if y is None:
        y = var_factory.add_var('y_' + name)

    aux_eqs: List[Var | Expr] = []
    aux_vars: List[Var | Expr] = []
    x_save = None  # Initialize x_save to avoid unbound variable error
    # check if is an expression
    if not isinstance(x, Var):
        u = var_factory.add_var('u_' + name)
        aux_eqs.append((u - x).simplify())
        aux_vars.append(u)
        x_save = x
        x = u

    diff_vars_x = [x]
    diff_vars_y = [y]
    diff_vars = list()
    state_eqs = list()
    state_vars = list()
    init_eqs = dict()
    diff_init_eqs = dict()   # ADDED
    base_var = x
    for i in range(1, len(num)):
        if i == 1 and create_state:
            x_new = var_factory.add_var(f"x_{i}_" + x.name)
            state_vars.append(x_new)
            # x_save only exists if x was an expression (not a Var)
            if 'x_save' in locals():
                state_eqs.append(x_save)
            else:
                state_eqs.append(x)  # x is already a Var
            diff_vars_x.append(x_new)
            base_var = x_new
            init_eqs[x_new] = Const(0.0)

        else:
            if base_var.diff_var is None:
                new_diff = var_factory.add_diff_var(name=f'dt_{i}_' + x.name, base_var=base_var)
                diff_vars.append(new_diff)
                diff_init_eqs[new_diff] = Const(0.0)   # ADDED
            diff_vars_x.append(base_var.diff_var)
            base_var = base_var.diff_var
    base_var = y
    for i in range(1, len(den)):
        if base_var.diff_var is None:
            new_diff = var_factory.add_diff_var(name=f'dt_{i}_' + y.name, base_var=base_var)
            diff_vars.append(new_diff)
            diff_init_eqs[new_diff] = Const(0.0)   # ADDED
        diff_vars_y.append(base_var.diff_var)
        base_var = base_var.diff_var

    # Create the diff equation
    rhs: Vec = np.array(diff_vars_x) @ np.array(num)
    lhs: Vec = np.array(diff_vars_y) @ np.array(den)

    block = Block()
    block.state_eqs = state_eqs
    block.state_vars = state_vars
    block.algebraic_vars = [y] + aux_vars
    block.algebraic_eqs = [lhs - rhs] + aux_eqs
    block.diff_vars = diff_vars
    block.init_eqs = init_eqs
    block.diff_init_eqs = diff_init_eqs   # ADDED

    return block, y, x



def tf_to_block_with_states(
        var_factory: VarFactory,
        num: List[Var | float],
        den: List[Var | float],
        x: Var | Expr,
        y: Var = None, name: Optional[str] = ''):
    """
    num: numerator coefficients [b0,...,bm]
    den: denominator coefficients [a0,...,an], with an != 0
    u:   input Var
    y:   output Var
    """
    if len(num) > len(den):
        raise ValueError("Transfer function is improper: numerator degree > denominator degree.")
    if num[-1] == 0 or den[-1] == 0:
        raise ValueError("Leading coefficient of cannot be zero.")

    if y is None:
        y = var_factory.add_var('y_' + name)

    aux_eqs = []
    aux_vars = []
    diff_init_eqs = dict()  # ADDED
    # check if x is a expression
    if not isinstance(x, Var):
        u = var_factory.add_var('u_' + name)
        aux_eqs.append(u - x)
        aux_vars.append(u)
        x = u

    # Normalize
    den = [c / den[-1] for c in den]
    num = [c / den[-1] for c in num]

    # States
    x_states = [x]
    y_states = [y]
    y_states.extend([var_factory.add_var(f"y{i}") for i in range(1, len(den))])  # y1,...,yn
    x_states.extend([var_factory.add_var(f"x{i}") for i in range(1, len(num))])  # x1,...,xm

    # Differential equations (canonical form)
    diff_eqs = list()
    diff_vars = list()
    for i in range(len(y_states) - 1):
        if y_states[i].diff_var is None:
            dy = var_factory.add_diff_var(f"d_{y_states[i].name}", base_var=y_states[i])
            diff_vars.append(dy)
            diff_init_eqs[dy] = Const(0.0)  # ADDED
        diff_eqs.append(y_states[i + 1] - y_states[i].diff_var)

    for i in range(len(num) - 1):
        if x_states[i].diff_var is None:
            dx = var_factory.add_diff_var(f"d^{i}_{x_states[i].name}", base_var=x_states[i])
            diff_vars.append(dx)
            diff_init_eqs[dx] = Const(0.0)  # ADDED
        diff_eqs.append(x_states[i + 1] - x_states[i].diff_var)

        # Last equation: linear combination
    last_eq = (
            sum(den[i] * y_states[i] for i in range(len(y_states)))
            - sum(num[i] * x_states[i] for i in range(len(x_states)))
    )
    diff_eqs.append(last_eq)

    block = Block(
        algebraic_vars=y_states + x_states[1:] + aux_vars,
        algebraic_eqs=diff_eqs + aux_eqs,
    )
    block.diff_vars = diff_vars
    block.diff_init_eqs = diff_init_eqs  # ADDED
    block.name = 'TF'
    return block, y_states[0]



def tf_to_block2(
        var_factory: VarFactory,
        num: List[Var | float],
        den: List[Var | float],
        x: Var | float,
        y: Var = None,
        name:str = ''):
    """
    num: numerator coefficients [b0,...,bm]
    den: denominator coefficients [a0,...,an], with an != 0
    u:   input Expr or Var
    y:   output Var
    """
    if len(num) >= len(den):
        raise ValueError("Transfer function is improper: numerator degree > denominator degree.")
    if num[-1] == 0 or den[-1] == 0:
        raise ValueError("Leading coefficient of cannot be zero.")

    aux_eqs: List[Expr] = list()
    aux_vars: List[Var] = list()
    # check if xis a expression
    if not isinstance(x, Var):
        u = var_factory.add_var('u')
        aux_eqs.append(u - x)
        aux_vars.append(u)
        x = u

    # Normalize
    den = [c / den[-1] for c in den]
    num = [c / den[-1] for c in num]

    order = len(den)  # system order
    x_states: List[Var] = [x]  # x0
    x_states.extend([var_factory.add_var(f"x{i}") for i in range(1, order + 1)])  # x1,...,xn

    # Differential equations (canonical form)
    state_eqs = list()
    state_vars = list()
    for i in range(1, order):
        state_eqs.append(x_states[i])
        state_vars.append(x_states[i + 1])

    y_states: List[Var] = [var_factory.add_var(f"y{i}") for i in range(len(num) + 1)]  # x1,...,xn
    for i in range(len(num)):
        state_eqs.append(y_states[i])
        state_vars.append(y_states[i + 1])

    # Last equation: linear combination
    last_eq = (
            sum(den[i] * y_states[i] for i in range(order))
            - sum(num[i] * x_states[i] for i in range(len(num)))
    )

    aux_eqs.append(last_eq)

    block = Block(
        state_eqs=state_eqs,
        state_vars=state_vars,
        algebraic_eqs=aux_eqs,
        # TODO: this is highly suspicious (better add vars to aux_vars)
        algebraic_vars=x_states[0] + y_states[0] + aux_vars,
    )
    return block, y_states[0]

def to_implicit(block: Block, vfactory: VarFactory) -> Block:
    """
    Convert a block with explicit state equations to implicit form.
    
    For each state variable x with equation dx/dt = f(x, y):
    - Create a new algebraic variable dt_x representing the derivative
    - Add dt_x to algebraic_vars
    - Add equation: diff(x) - f(x, y) = 0 to algebraic_eqs
    - Move x from state_vars to algebraic_vars
    - Remove the state equation from state_eqs
    
    This transforms the explicit ODE form into DAE implicit form suitable
    for solvers that expect algebraic equations.
    """
    # Process each state variable and its corresponding state equation
    # We iterate backwards to safely modify lists while iterating
    for i, state_var in enumerate(block.state_vars):
        state_eq = block.state_eqs[i]
        
        # Create a new algebraic variable for the derivative
        if state_var.diff_var == None:
            dt_var = vfactory.add_diff_var(f"dt_{state_var.name}", base_var=state_var)
            block.diff_vars.append(dt_var)
        else:
            dt_var = state_var.diff_var

        implicit_eq = dt_var - state_eq
        block.algebraic_vars.append(state_var)
        block.algebraic_eqs.append(implicit_eq)
        
        #block.init_eqs[dt_var] = block.init_eqs[state_var]

    
    # The state_vars become algebraic_vars since they now appear in algebraic equations
    block.state_vars = list()
    block.state_eqs = list()
    
    
    # Recursively process children
    for b in block.children:
        to_implicit(b, vfactory)
    
    return block


def tf_to_diffblock_with_antiwindup(
        var_factory: VarFactory,
        num: List[Var | float],
        den: List[Var | float],
        x: Var,
        y: Var = None,
        name: Optional[str] = '',
        sat_min: Expr = Const(float(-1e6)),
        sat_max: Expr = Const(float(1e6)),
        multilinear=False,
        PI: bool = False):
    """
    num: numerator coefficients [b0, ..., bm]
    den: denominator coefficients [a0, ..., an]
    x:   input (Var or Expr)
    y:   output Var
    sat_min, sat_max: saturation limits for anti-windup
    """

    if len(num) > len(den):
        raise ValueError("Transfer function is improper: numerator degree > denominator degree.")
    if num[-1] == 0 or den[-1] == 0:
        raise ValueError("Leading coefficient cannot be zero.")

    if y is None:
        y = var_factory.add_var('y_' + name)

    aux_eqs = []
    aux_vars = []
    diff_init_eqs = dict()  # ADDED

    # If x is an expression, wrap it in a Var
    if not isinstance(x, Var):
        u = var_factory.add_var('u_' + name)
        aux_eqs.append((u - x).simplify())
        aux_vars.append(u)
        x = u

    diff_vars_x = [x]
    diff_vars_y = [y]
    diff_vars = []

    # Derivative chain for x
    base_var = x
    for i in range(1, len(num)):
        if base_var.diff_var is None:
            new_diff = var_factory.add_diff_var(name=f'dt_{i}_' + x.name, base_var=base_var)
            diff_vars.append(new_diff)
            diff_init_eqs[new_diff] = Const(0.0)  # ADDED
        diff_vars_x.append(x.diff_var)
        base_var = x.diff_var

    # Derivative chain for y
    base_var = y
    for i in range(1, len(den)):
        if base_var.diff_var is None:
            new_diff = var_factory.add_diff_var(name=f'dt_{i}_' + y.name, base_var=base_var)
            diff_vars.append(new_diff)
            diff_init_eqs[new_diff] = Const(0.0)  # ADDED
        diff_vars_y.append(y.diff_var)
        base_var = y.diff_var

    # Base equations
    rhs = np.array(diff_vars_x) @ np.array(num)
    lhs = np.array(diff_vars_y) @ np.array(den)

    # -----------------------------------------------------------
    # ANTI-WINDUP BY MULTIPLYING ALL COEFFICIENTS BY h
    # -----------------------------------------------------------

    # TODO: review multilinear implementation
    # if not multilinear:
    h1 = heaviside(y - sat_min)
    h2 = heaviside(sat_max - y)

    # TODO: review multilinear implementation
    # else:
    #     h1, ml_block1 = heaviside(y - sat_min, name=f'h1_{name}')
    #     h2, ml_block2 = heaviside(sat_max - y, name=f'h2_{name}')

    # Build LHS term-by-term, skipping multiplication on dy
    rhs = Const(0.0)
    lhs = Const(0.0)
    if not PI:
        for i, term in enumerate(np.array(den) * np.array(diff_vars_y)):
            if i != 1:
                lhs += term
        for i, term in enumerate(np.array(num) * np.array(diff_vars_x)):
            rhs += term
    else:
        for i, term in enumerate(np.array(num) * np.array(diff_vars_x)):
            rhs += term

    f = (rhs - lhs) / Const(den[1])
    hf = heaviside(rhs - lhs)
    ha = h1 * h2
    hb = (1 - h1) * hf
    hc = (1 - h2) * (1 - hf)
    h = heaviside(ha + hb + hc)
    # Differential equation (single equation)
    eq_main = (diff_vars_y[1] - h * f).simplify()

    block = Block(
        name=name,
        algebraic_vars=[y] + aux_vars,
        algebraic_eqs=[eq_main] + aux_eqs,
        diff_vars=diff_vars,
    )
    block.diff_init_eqs = diff_init_eqs  # ADDED

    # TODO: review multilinear implementation
    # if multilinear:
    #     block.add(ml_block1)
    #     block.add(ml_block2)
    return block, y


def tf_to_diffblock_with_antiwindup_by_feedback(
        var_factory: VarFactory,
        num: List[Var | float],
        den: List[Var | float],
        x: Var,
        y: Var = None,
        name: Optional[str] = '',
        sat_min: Expr = Const(-1e6),
        sat_max: Expr = Const(1e6),
        Kaw: Expr = Const(10.0),  # anti-windup gain (1/Tt)
):
    """
    Implements a back-calculation anti-windup controller using (u_sat - u) as feedback input.
    Works better for implicit solvers
    num: numerator coefficients [b0, ..., bm]
    den: denominator coefficients [a0, ..., an]
    x:   input signal
    y:   output (saturated)
    """

    if len(num) > len(den):
        raise ValueError("Improper TF")

    if y is None:
        y = var_factory.add_var(f'y_{name}')

    aux_eqs = []
    aux_vars = []

    # Wrap input expression
    if not isinstance(x, Var):
        u_in = var_factory.add_var(f'u_in_{name}')
        aux_eqs.append((u_in - x).simplify())
        aux_vars.append(u_in)
        x = u_in

    # --------------------------------------------------
    # Build derivative chains
    # --------------------------------------------------
    diff_vars = []
    diff_x = [x]
    diff_y = [y]

    base = x
    for i in range(1, len(num)):
        dv = var_factory.add_diff_var(f'dt_{i}_{x.name}', base_var=base)
        diff_vars.append(dv)
        diff_x.append(dv)
        base = dv

    base = y
    for i in range(1, len(den)):
        dv = var_factory.add_diff_var(f'dt_{i}_{y.name}', base_var=base)
        diff_vars.append(dv)
        diff_y.append(dv)
        base = dv

    # --------------------------------------------------
    # Unsaturated output (internal)
    # --------------------------------------------------
    u = var_factory.add_var(f'u_{name}')
    aux_vars.append(u)

    tf_rhs = np.dot(num, diff_x)
    tf_lhs = np.dot(den, diff_y)

    aux_eqs.append((u - tf_rhs).simplify())

    # --------------------------------------------------
    # Saturation
    # --------------------------------------------------
    u_sat = var_factory.add_var(f'u_sat_{name}')
    aux_vars.append(u_sat)

    sat_expr = (
            sat_min
            + (u - sat_min) * heaviside(u - sat_min)
            - (u - sat_max) * heaviside(u - sat_max)
    )

    aux_eqs.append((u_sat - sat_expr).simplify())

    # --------------------------------------------------
    # Main differential equation
    # Add anti-windup ONLY to integrator (dy/dt term)
    # --------------------------------------------------
    lhs = Const(0)
    rhs = Const(0)

    for i, term in enumerate(den * np.array(diff_y)):
        lhs += term

    for term in num * np.array(diff_x):
        rhs += term

    # Anti-windup injection
    rhs += Kaw * (u_sat - u)

    eq_main = (lhs - rhs).simplify()

    block = Block(
        name=name,
        algebraic_vars=[y, u, u_sat] + aux_vars,
        algebraic_eqs=[eq_main] + aux_eqs,
        diff_vars=diff_vars,
    )

    return block, y

def discrete_control_block(
    var_factory: VarFactory,
    m: Var,
    delta_m: Var,
    m_max: Var,
    m_min: Var,
    v: Var,
    v_ref: Var,
    delta_v: Var,
    ts: Var,          # seconds
    name: Optional[str] = ''
) -> Tuple[Block, Var]:

    m_last   = var_factory.add_var(f'm_last_{name}')
    t_signal = var_factory.add_var(f't_signal_{name}')

    tick = (t_signal >= ts).to_expression()

    # your switching increment (only evaluated on tick)
    inc = delta_m * (v - v_ref <= delta_v).to_expression() \
        - delta_m * (v - v_ref >= delta_v).to_expression()

    changed = (1 - Comparison(m_last, CmpOp.EQ, m).to_expression())

    dt = var_factory.add_var(f'dt')
    block = Block(
        name=name + '_input_controlled_switch',
        discrete_eqs={
            t_signal: changed*(t_signal + dt),
            m:hard_sat(m + inc * tick, m_min, m_max),
            m_last: m,
        },
        api_obj_mapping={dt: ParamPowerFlowRefferenceType.dt}
    )
    return block, m

def deadband_block(
        var_factory: VarFactory,
        x: Var | Expr,
        y: Var = None,
        name: Optional[str] = '',
        deadband: Expr = Const(0.1)) -> Tuple[Block, Var]:
    """
    Creates a deadband function block.
    
    The deadband function returns:
    - 0 when input is within the deadband [-deadband, +deadband]
    - input - deadband when input > deadband
    - input + deadband when input < -deadband
    
    Parameters:
    -----------
    var_factory: VarFactory instance for creating variables
    x: input signal (Var or Expr)
    y: output variable (optional, created if None)
    name: name prefix for variables
    deadband: deadband threshold (default 0.1)
    
    Returns:
    --------
    Tuple of (Block, output_var)
    """
    if y is None:
        y = var_factory.add_var('y_deadband_' + name)
    
    aux_eqs = []
    aux_vars = []
    
    # Wrap input expression if needed
    if not isinstance(x, Var):
        u = var_factory.add_var('u_deadband_' + name)
        aux_eqs.append((u - x).simplify())
        aux_vars.append(u)
        x = u
    
    # Deadband logic using Heaviside step functions
    # y = (u - deadband) * H(u - deadband) + (u + deadband) * H(-deadband - u)
    #   = (u - deadband) * H(u - deadband) + (u + deadband) * H(-u - deadband)
    
    h_pos = heaviside(x - deadband)
    h_neg = heaviside(-x - deadband)
    
    # Output expression
    output_expr = (x - deadband) * h_pos + (x + deadband) * h_neg
    
    # Algebraic equation: y - output_expr = 0
    eq = (y - output_expr).simplify()
    
    block = Block(
        name=name + '_deadband',
        algebraic_vars=[y] + aux_vars,
        algebraic_eqs=[eq] + aux_eqs,
        diff_vars=[]
    )
    
    return block, y


def connect_line_rms_from(mdl1: Block, mdl2: Block):
    """
    This function substitutes input variables for output variables to connect two rms models
    :param mdl1:
    :param mdl2:
    :return:
    """
    # connect Vm
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowRefferenceType.Vm and inpt.ref == VarPowerFlowRefferenceType.Vmf
    ]
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])

    # connect Va
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowRefferenceType.Va and inpt.ref == VarPowerFlowRefferenceType.Vaf
    ]
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])


def connect_line_rms_to(mdl1: Block, mdl2: Block):
    """
    This function substitutes input variables for output variables to connect two rms models
    :param mdl1:
    :param mdl2:
    :return:
    """
    # connect Vm
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowRefferenceType.Vm and inpt.ref == VarPowerFlowRefferenceType.Vmt
    ]
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])

    # connect Va
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowRefferenceType.Va and inpt.ref == VarPowerFlowRefferenceType.Vat
    ]
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])


def connect_line_phasor_rms_from(mdl1: Block, mdl2: Block):
    """
    Connect phasor RMS models for the 'from' end of a line.
    Connects Vr, Vi from bus to line inputs.
    """
    # connect Vr
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowRefferenceType.Vr and inpt.ref == VarPowerFlowRefferenceType.Vrf
    ]
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])

    # connect Vi
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowRefferenceType.Vi and inpt.ref == VarPowerFlowRefferenceType.Vif
    ]
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])


def connect_line_phasor_rms_to(mdl1: Block, mdl2: Block):
    """
    Connect phasor RMS models for the 'to' end of a line.
    Connects Vr, Vi from bus to line inputs.
    """
    # connect Vr
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowRefferenceType.Vr and inpt.ref == VarPowerFlowRefferenceType.Vrt
    ]
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])

    # connect Vi
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == VarPowerFlowRefferenceType.Vi and inpt.ref == VarPowerFlowRefferenceType.Vit
    ]
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])


def connect_models(mdl1: Block, mdl2: Block):
    """
    This function substitutes input variables for output variables to connect two rms models
    :param mdl1:
    :param mdl2:
    :return:
    """
    # connect inputs mdl2 with outputs mdl1
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref == inpt.ref
    ]

    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])

    # connect inputs mdl2 with outputs mdl1
    pairs = [
        (outp, inpt)
        for outp in mdl2.out_vars
        for inpt in mdl1.in_vars
        if outp.ref == inpt.ref
    ]

    for outp, inpt in pairs:
        mdl1.connect([inpt], [outp])



    #print("")


def set_rms_model(device: Any, model:Block, var_factory: VarFactory):
    """
    Set the RMS model
    :return:
    :rtype:
    """
    # connect bus variables

    if device.device_type in [DeviceType.BranchDevice, DeviceType.LineDevice, DeviceType.Transformer2WDevice, DeviceType.Transformer3WDevice]:
        # Check if using phasor or polar coordinates by looking at bus model outputs
        bus_model = device.bus_from.rms_model
        if not bus_model.empty():
            # Check if bus has Vr/Vi (phasor) or Vm/Va (polar) outputs
            has_phasor = any(v.ref == VarPowerFlowRefferenceType.Vr for v in bus_model.out_vars)
            if has_phasor:
                connect_line_phasor_rms_from(device.bus_from.rms_model, model)
            else:
                connect_line_rms_from(device.bus_from.rms_model, model)
        else:
            raise ValueError(f"Connection Bus RMS model cannot be empty, initialize {device.bus_from.name} RMS model")

        bus_model = device.bus_to.rms_model
        if not bus_model.empty():
            # Check if bus has Vr/Vi (phasor) or Vm/Va (polar) outputs
            has_phasor = any(v.ref == VarPowerFlowRefferenceType.Vr for v in bus_model.out_vars)
            if has_phasor:
                connect_line_phasor_rms_to(device.bus_to.rms_model, model)
            else:
                connect_line_rms_to(device.bus_to.rms_model, model)
        else:
            raise ValueError(f"Connection Bus RMS model cannot be empty, initialize {device.bus_to.name} RMS model")

    else:
        if not device.bus.rms_model.empty():
            connect_models(device.bus.rms_model, model)

        else:
            raise ValueError(f"Connection Bus RMS model cannot be empty, initialize {device.bus.name} RMS model")

    # fill var factoru dict[Dev, List[Var]] with model variables
    model.unify_blocks()
    for vr in model.algebraic_vars:
        var_factory.register_var(device, vr)
    for vr in model.state_vars:
        var_factory.register_var(device, vr)

    # set the model to the device
    device.rms_model = model


def connect_line_emt_from(mdl1: Block, mdl2: Block):
    """
    Connects the bus voltages (mdl1) to the "from" side of the line (mdl2)
    for simulations with explicit phases (e.g., EMT).
    It only connects the phases present in both models (any NABC combination).

    :param mdl1: Bus model (Block)
    :param mdl2: Line model (Block)
    :return: None
    """
    # Create a dictionary to map the bus output variable
    # to the corresponding line input variable ("from" side)
    phase_map = {
        VarPowerFlowRefferenceType.v_N: VarPowerFlowRefferenceType.vf_N,
        VarPowerFlowRefferenceType.v_A: VarPowerFlowRefferenceType.vf_A,
        VarPowerFlowRefferenceType.v_B: VarPowerFlowRefferenceType.vf_B,
        VarPowerFlowRefferenceType.v_C: VarPowerFlowRefferenceType.vf_C
    }

    # Find the variable pairs that match our mapping
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref in phase_map and phase_map[outp.ref] == inpt.ref
    ]

    # Connect all found pairs
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])

def connect_line_emt_to(mdl1: Block, mdl2: Block):
    """
    Connects the bus voltages (mdl1) to the "to" side of the line (mdl2)
    for simulations with explicit phases (e.g., EMT).
    It only connects the phases present in both models (any NABC combination).

    :param mdl1: Bus model (Block)
    :param mdl2: Line model (Block)
    :return: None
    """
    # Create a dictionary to map the bus output variable
    # to the corresponding line input variable ("to" side)
    phase_map = {
        VarPowerFlowRefferenceType.v_N: VarPowerFlowRefferenceType.vt_N,
        VarPowerFlowRefferenceType.v_A: VarPowerFlowRefferenceType.vt_A,
        VarPowerFlowRefferenceType.v_B: VarPowerFlowRefferenceType.vt_B,
        VarPowerFlowRefferenceType.v_C: VarPowerFlowRefferenceType.vt_C
    }

    # Find the variable pairs that match our mapping
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if outp.ref in phase_map and phase_map[outp.ref] == inpt.ref
    ]

    # Connect all found pairs
    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])


def connect_vsc_emt_from(mdl1: Block, mdl2: Block, is_dc_bus: bool = False):
    """
    Connects the bus voltages to the "from" side of the VSC model.
    For DC buses, connects Vdc. For AC buses, connects abc voltages.

    :param mdl1: Bus model (Block)
    :param mdl2: VSC model (Block)
    :param is_dc_bus: True if bus_from is DC
    :return: None
    """
    if is_dc_bus:
        # DC bus: connect Vdc
        dc_map = {
            VarPowerFlowRefferenceType.Vdc: VarPowerFlowRefferenceType.Vdc
        }
        pairs = [
            (outp, inpt)
            for outp in mdl1.out_vars
            for inpt in mdl2.in_vars
            if outp.ref in dc_map and dc_map[outp.ref] == inpt.ref
        ]
    else:
        # AC bus: connect abc voltages
        phase_map = {
            VarPowerFlowRefferenceType.v_A: VarPowerFlowRefferenceType.v_A,
            VarPowerFlowRefferenceType.v_B: VarPowerFlowRefferenceType.v_B,
            VarPowerFlowRefferenceType.v_C: VarPowerFlowRefferenceType.v_C
        }
        pairs = [
            (outp, inpt)
            for outp in mdl1.out_vars
            for inpt in mdl2.in_vars
            if outp.ref in phase_map and phase_map[outp.ref] == inpt.ref
        ]

    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])


def connect_vsc_emt_to(mdl1: Block, mdl2: Block, is_dc_bus: bool = False):
    """
    Connects the bus voltages to the "to" side of the VSC model.
    For DC buses, connects Vdc. For AC buses, connects abc voltages.

    :param mdl1: Bus model (Block)
    :param mdl2: VSC model (Block)
    :param is_dc_bus: True if bus_to is DC
    :return: None
    """
    if is_dc_bus:
        # DC bus: connect Vdc
        dc_map = {
            VarPowerFlowRefferenceType.Vdc: VarPowerFlowRefferenceType.Vdc
        }
        pairs = [
            (outp, inpt)
            for outp in mdl1.out_vars
            for inpt in mdl2.in_vars
            if outp.ref in dc_map and dc_map[outp.ref] == inpt.ref
        ]
    else:
        # AC bus: connect abc voltages
        phase_map = {
            VarPowerFlowRefferenceType.v_A: VarPowerFlowRefferenceType.v_A,
            VarPowerFlowRefferenceType.v_B: VarPowerFlowRefferenceType.v_B,
            VarPowerFlowRefferenceType.v_C: VarPowerFlowRefferenceType.v_C
        }
        pairs = [
            (outp, inpt)
            for outp in mdl1.out_vars
            for inpt in mdl2.in_vars
            if outp.ref in phase_map and phase_map[outp.ref] == inpt.ref
        ]

    for outp, inpt in pairs:
        mdl2.connect([inpt], [outp])


def set_emt_model(device: Any, model: Block, var_factory: VarFactory):
    """
    Sets the EMT model for a given device, connects it to the bus(es),
    and registers all its variables in the VarFactory.

    :param device: The power system device (Line, Transformer, Generator, etc.)
    :param model: The mathematical block model of the device
    :param var_factory: Factory to register simulation variables
    :return: None
    """
    # 1. Connect bus variables depending on the device type
    if device.device_type in [DeviceType.BranchDevice, DeviceType.LineDevice, DeviceType.Transformer2WDevice,
                              DeviceType.Transformer3WDevice]:

        # Bus FROM connection
        bus_from_model = device.bus_from.emt_model
        if not bus_from_model.empty():
            connect_line_emt_from(bus_from_model, model)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_from.name} EMT model")

        # Bus TO connection
        bus_to_model = device.bus_to.emt_model
        if not bus_to_model.empty():
            connect_line_emt_to(bus_to_model, model)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_to.name} EMT model")

    elif device.device_type == DeviceType.VscDevice:

        # VSC: bus_from is DC, bus_to is AC
        bus_from_model = device.bus_from.emt_model
        if not bus_from_model.empty():
            connect_vsc_emt_from(bus_from_model, model, is_dc_bus=device.bus_from.is_dc)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_from.name} EMT model")

        bus_to_model = device.bus_to.emt_model
        if not bus_to_model.empty():
            connect_vsc_emt_to(bus_to_model, model, is_dc_bus=device.bus_to.is_dc)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus_to.name} EMT model")

    else:
        # Generic device connection (e.g., Loads, Generators connected to a single bus)
        if not device.bus.emt_model.empty():
            connect_models(device.bus.emt_model, model)
        else:
            raise ValueError(f"Connection Bus EMT model cannot be empty, initialize {device.bus.name} EMT model")

    # 2. Unify blocks and register all variables in the VarFactory
    model.unify_blocks()

    for vr in model.algebraic_vars:
        var_factory.register_var(device, vr)

    for vr in model.state_vars:
        var_factory.register_var(device, vr)

    # Added diff_vars for EMT simulations
    for vr in model.diff_vars:
        var_factory.register_var(device, vr)

    # 3. Assign the configured model to the device
    device.emt_model = model
