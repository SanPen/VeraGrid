# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
import numpy as np
from typing import List
from VeraGridEngine.Utils.Symbolic.block import (Block)
from VeraGridEngine.Utils.Symbolic.symbolic import (Var, Const, Expr, Func, BinOp)
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory


def ml_positive_part(
    vf: VarFactory,
    u: Expr,
    name: str = '',
    scale_balance: Expr | None = None,
    scale_complementarity: Expr | None = None,
    scale_equalities: Expr | None = None,
):
    u_plus1 = vf.add_var('u_plus1_'+name)
    u_plus2 = vf.add_var('u_plus2_'+name)
    u_minus1 = vf.add_var('u_minus1_' +name)
    u_minus2 = vf.add_var('u_minus2_' +name)
    s_bal = Const(1.0) if scale_balance is None else scale_balance
    s_comp = Const(1.0) if scale_complementarity is None else scale_complementarity
    s_eq = Const(1.0) if scale_equalities is None else scale_equalities
    positive_part_block = Block(
        algebraic_eqs=[
            (u - (u_plus1*u_plus2 - u_minus1*u_minus2)) / s_bal,
            (u_plus1*u_minus1) / s_comp,
            (u_plus1 - u_plus2) / s_eq,
            (u_minus1 - u_minus2) / s_eq,
        ],
        algebraic_vars=[u_plus1, u_plus2, u_minus1, u_minus2],
        init_eqs={
            u_plus1 : sym.sqrt(sym.max(u, Const(0))),
            u_plus2 : u_plus1,
            u_minus1: sym.sqrt(sym.max(-u, Const(0))),
            u_minus2: u_minus1,
        }
    )
    return positive_part_block, u_plus1*u_plus2, u_minus1*u_minus2

def ml_positive_part_alt(vf: VarFactory, A:Expr, name:str=''):
    u_plus1 = vf.add_var('u_plus1_'+name)
    u_plus2 = vf.add_var('u_plus2_'+name)
    u_plus3 = vf.add_var('abs_'+name)
    positive_part_block = Block(
        algebraic_eqs=[
            u_plus1-u_plus2,
            u_plus1*u_plus2-u_plus3,
            u_plus1*u_plus2*u_plus3 - u_plus3*A,
        ],
        algebraic_vars=[u_plus1, u_plus2, u_plus3]
    )
    return positive_part_block, (u_plus3), (A-u_plus3) 

def ml_max(vf: VarFactory, u:Expr, v:Expr, alternative:bool = True, name:str=''):
    if not alternative:
        hv_var, block_hv = ml_heaviside(vf, u-v)
        max_expr = hv_var*u + (Const(1)-hv_var)*v
    else:
        pos_part_uv, neg_part_uv, block_hv = ml_positive_part_alt(vf, u-v)
        max_expr = u + neg_part_uv
    return max_expr, block_hv

def ml_hard_sat(
    vf: VarFactory,
    u: Expr,
    u_min: Expr,
    u_max: Expr,
    name: str = "",
    alternative_positive_part: bool = False,
    scale_balance: Expr | None = None,
    scale_complementarity: Expr | None = None,
    scale_equalities: Expr | None = None,
):
    if alternative_positive_part:
        block1, expr1_plus, expr1_minus = ml_positive_part_alt(vf, u - u_max, name + "_max")
        block2, expr2_plus, expr2_minus = ml_positive_part_alt(vf, u - u_min, name + "_min")
    else:
        block1, expr1_plus, expr1_minus = ml_positive_part(
            vf,
            u - u_max,
            name + "_max",
            scale_balance=scale_balance,
            scale_complementarity=scale_complementarity,
            scale_equalities=scale_equalities,
        )
        block2, expr2_plus, expr2_minus = ml_positive_part(
            vf,
            u - u_min,
            name + "_min",
            scale_balance=scale_balance,
            scale_complementarity=scale_complementarity,
            scale_equalities=scale_equalities,
        )
    final_expr = u_min + expr2_plus - expr1_plus 
    final_block = Block(
        algebraic_eqs=list(block1.algebraic_eqs) + list(block2.algebraic_eqs),
        algebraic_vars=list(block1.algebraic_vars) + list(block2.algebraic_vars),
        init_eqs={**dict(block1.init_eqs), **dict(block2.init_eqs)},
        children=list(block1.children) + list(block2.children),
    )
    return final_block, final_expr 


def mti_hard_sat(
    vf: VarFactory,
    u: Expr,
    ul: Expr,
    uu: Expr,
    yl: Expr,
    yu: Expr,
    name: str = "",
):
    """MTI hard saturation following toolbox-style mixed constraints.


    """
    b1 = vf.add_var("b1_" + name)
    b2 = vf.add_var("b2_" + name)
    b3 = vf.add_var("b3_" + name)
    b4 = vf.add_var("b4_" + name)
    y = vf.add_var("y_sat_" + name)


    y_expr = b2 * yl + b1 * b4 * u + b3 * yu

    block = Block(
        algebraic_vars=[y],
        algebraic_eqs=[
            y - y_expr,
            b1 + b2 - 1,
            b3 + b4 - 1,
        ],
        inequalities=[
            -(b1 - b2) * (u - ul),
            -(b3 - b4) * (u - uu),
        ],
        init_eqs={
            y: sym.hard_sat(u, yl, yu),
        },
        boolean_guards= {
            b1: sym.heaviside(u - ul),
            b2: 1 - sym.heaviside(u - ul),
            b3: sym.heaviside(u - uu),
            b4: 1 - sym.heaviside(u - uu),
        }
    )

    return block, y


def mti_three_phase_carrier_pwm_direct(
    vf: VarFactory,
    ref_a: Expr,
    ref_b: Expr,
    ref_c: Expr,
    carrier: Expr,
    eps: Expr | float | int | None = None,
    name: str = "",
):
    """
    Direct three-phase MTI carrier PWM comparator.

    The generated gates follow the memoryless comparator rule
    ``gate = 1`` when ``ref - carrier >= 0`` and ``gate = 0`` when
    ``ref - carrier <= 0``. Inequalities use VeraGrid's MTI convention
    ``G <= 0``.
    """
    b_a = vf.add_var("b_pwm_a_" + name)
    b_b = vf.add_var("b_pwm_b_" + name)
    b_c = vf.add_var("b_pwm_c_" + name)
    gate_a = vf.add_var("gate_pwm_a_" + name)
    gate_b = vf.add_var("gate_pwm_b_" + name)
    gate_c = vf.add_var("gate_pwm_c_" + name)

    s_a = ref_a - carrier
    s_b = ref_b - carrier
    s_c = ref_c - carrier

    if eps is None:
        inequalities = [
            -(2 * b_a - 1) * s_a,
            -(2 * b_b - 1) * s_b,
            -(2 * b_c - 1) * s_c,
        ]
    else:
        eps_expr = Const(float(eps)) if isinstance(eps, (float, int)) else eps
        inequalities = [
            b_a * (-(s_a + eps_expr)) + (1 - b_a) * (s_a - eps_expr),
            b_b * (-(s_b + eps_expr)) + (1 - b_b) * (s_b - eps_expr),
            b_c * (-(s_c + eps_expr)) + (1 - b_c) * (s_c - eps_expr),
        ]

    block = Block(
        algebraic_vars=[gate_a, gate_b, gate_c],
        algebraic_eqs=[
            gate_a - b_a,
            gate_b - b_b,
            gate_c - b_c,
        ],
        inequalities=inequalities,
        init_eqs={
            gate_a: sym.heaviside(s_a),
            gate_b: sym.heaviside(s_b),
            gate_c: sym.heaviside(s_c),
        },
        boolean_guards={
            b_a: sym.heaviside(s_a),
            b_b: sym.heaviside(s_b),
            b_c: sym.heaviside(s_c),
        },
    )

    return block, gate_a, gate_b, gate_c


def mti_three_phase_carrier_pwm_direct_params(
    vf: VarFactory,
    name: str = "",
    eps: Expr | float | int | None = None,
    ref_a0: float = 0.0,
    ref_b0: float = 0.0,
    ref_c0: float = 0.0,
    carrier0: float = 0.0,
):
    """
    Direct three-phase MTI carrier PWM comparator with input signals modeled as runtime parameters.

    This mirrors toolbox-style ``u`` inputs in VeraGrid's current block model by
    declaring ``u_ref_a``, ``u_ref_b``, ``u_ref_c`` and ``u_carrier`` in
    ``event_dict``. The MTI inequalities then switch boolean gate modes from the
    parameter residuals ``u_ref_phase - u_carrier``.
    """
    ref_a = vf.add_var("u_ref_a_pwm_" + name)
    ref_b = vf.add_var("u_ref_b_pwm_" + name)
    ref_c = vf.add_var("u_ref_c_pwm_" + name)
    carrier = vf.add_var("u_carrier_pwm_" + name)

    block, gate_a, gate_b, gate_c = mti_three_phase_carrier_pwm_direct(
        vf=vf,
        ref_a=ref_a,
        ref_b=ref_b,
        ref_c=ref_c,
        carrier=carrier,
        eps=eps,
        name=name,
    )
    block.event_dict.update({
        ref_a: Const(float(ref_a0)),
        ref_b: Const(float(ref_b0)),
        ref_c: Const(float(ref_c0)),
        carrier: Const(float(carrier0)),
    })

    return block, gate_a, gate_b, gate_c, ref_a, ref_b, ref_c, carrier


def mti_three_phase_carrier_pwm_internal_carrier_params(
    vf: VarFactory,
    name: str = "",
    omega_sw0: float = 2.0 * np.pi * 1000.0,
    direction_eps: Expr | float | int = 1.0e-9,
    ref_a0: float = 0.0,
    ref_b0: float = 0.0,
    ref_c0: float = 0.0,
    carrier0: float = -1.0,
    carrier_rising0: float = 1.0,
):
    """
    Three-phase MTI PWM with runtime-parameter references and internal triangular carrier.

    The reference signals are modeled as runtime parameters because the current
    VeraGrid MTI path has no first-class ``u`` input category. The triangular
    carrier direction is not external: it is represented by the internal boolean
    ``b_carrier_rise`` and the carrier is a continuous state with slope selected
    by that boolean.
    """
    ref_a = vf.add_var("u_ref_a_pwm_" + name)
    ref_b = vf.add_var("u_ref_b_pwm_" + name)
    ref_c = vf.add_var("u_ref_c_pwm_" + name)
    omega_sw = vf.add_var("u_omega_sw_pwm_" + name)

    carrier = vf.add_var("carrier_pwm_" + name)
    dcarrier = vf.add_diff_var("dt_carrier_pwm_" + name, base_var=carrier)
    b_carrier_rise = vf.add_var("b_carrier_rise_pwm_" + name)

    b_a = vf.add_var("b_pwm_a_" + name)
    b_b = vf.add_var("b_pwm_b_" + name)
    b_c = vf.add_var("b_pwm_c_" + name)
    gate_a = vf.add_var("gate_pwm_a_" + name)
    gate_b = vf.add_var("gate_pwm_b_" + name)
    gate_c = vf.add_var("gate_pwm_c_" + name)

    c_one = Const(1.0)
    c_two = Const(2.0)
    slope_abs = Const(2.0 / np.pi) * omega_sw
    carrier_slope = (c_two * b_carrier_rise - c_one) * slope_abs
    direction_for_switching_surface = c_one - c_two * b_carrier_rise
    direction_eps_expr = Const(float(direction_eps)) if isinstance(direction_eps, (float, int)) else direction_eps

    s_a = ref_a - carrier + direction_eps_expr * direction_for_switching_surface
    s_b = ref_b - carrier + direction_eps_expr * direction_for_switching_surface
    s_c = ref_c - carrier + direction_eps_expr * direction_for_switching_surface

    block = Block(
        state_vars=[carrier],
        state_eqs=[carrier_slope],
        diff_vars=[dcarrier],
        algebraic_vars=[gate_a, gate_b, gate_c],
        algebraic_eqs=[
            gate_a - b_a,
            gate_b - b_b,
            gate_c - b_c,
        ],
        inequalities=[
            -(c_two * b_a - c_one) * s_a,
            -(c_two * b_b - c_one) * s_b,
            -(c_two * b_c - c_one) * s_c,
            b_carrier_rise * (carrier - c_one) + (c_one - b_carrier_rise) * (-carrier - c_one),
        ],
        event_dict={
            ref_a: Const(float(ref_a0)),
            ref_b: Const(float(ref_b0)),
            ref_c: Const(float(ref_c0)),
            omega_sw: Const(float(omega_sw0)),
        },
        init_eqs={
            carrier: Const(float(carrier0)),
            gate_a: sym.heaviside(s_a),
            gate_b: sym.heaviside(s_b),
            gate_c: sym.heaviside(s_c),
        },
        boolean_guards={
            b_a: sym.heaviside(s_a),
            b_b: sym.heaviside(s_b),
            b_c: sym.heaviside(s_c),
            b_carrier_rise: sym.heaviside(Const(float(carrier_rising0)) - Const(0.5)),
        },
    )

    return block, gate_a, gate_b, gate_c, ref_a, ref_b, ref_c, omega_sw, carrier, b_carrier_rise


def mti_three_phase_carrier_pwm_scheduled_params(
    vf: VarFactory,
    time: Expr,
    name: str = "",
    transition_eps: Expr | float | int = 1.0e-9,
    ref_a0: float = 0.0,
    ref_b0: float = 0.0,
    ref_c0: float = 0.0,
    interval_start0: float = 0.0,
    half_period0: float = 5.0e-4,
    carrier_rising0: float = 1.0,
):
    """
    Scheduled-event MTI approximation of regular-sampled carrier PWM.

    The block models the procedural PWM schedule explicitly: sampled references
    and interval timing are runtime parameters, while the phase transition modes
    are MTI booleans driven by ``time - t_cross`` inequalities.
    """
    ref_a = vf.add_var("u_ref_a_sched_pwm_" + name)
    ref_b = vf.add_var("u_ref_b_sched_pwm_" + name)
    ref_c = vf.add_var("u_ref_c_sched_pwm_" + name)
    interval_start = vf.add_var("u_interval_start_sched_pwm_" + name)
    half_period = vf.add_var("u_half_period_sched_pwm_" + name)

    b_carrier_rise = vf.add_var("b_carrier_rise_sched_pwm_" + name)
    q_a = vf.add_var("q_after_a_sched_pwm_" + name)
    q_b = vf.add_var("q_after_b_sched_pwm_" + name)
    q_c = vf.add_var("q_after_c_sched_pwm_" + name)

    t_cross_a = vf.add_var("t_cross_a_sched_pwm_" + name)
    t_cross_b = vf.add_var("t_cross_b_sched_pwm_" + name)
    t_cross_c = vf.add_var("t_cross_c_sched_pwm_" + name)
    gate_a = vf.add_var("gate_pwm_a_" + name)
    gate_b = vf.add_var("gate_pwm_b_" + name)
    gate_c = vf.add_var("gate_pwm_c_" + name)

    c_one = Const(1.0)
    c_half = Const(0.5)
    eps_expr = Const(float(transition_eps)) if isinstance(transition_eps, (float, int)) else transition_eps

    def cross_time(ref: Expr) -> Expr:
        rising_cross = interval_start + c_half * (ref + c_one) * half_period
        falling_cross = interval_start + c_half * (c_one - ref) * half_period
        return b_carrier_rise * rising_cross + (c_one - b_carrier_rise) * falling_cross

    def gate_expr(q_after: Expr) -> Expr:
        return (c_one - q_after) * b_carrier_rise + q_after * (c_one - b_carrier_rise)

    tau_a = time - t_cross_a + eps_expr
    tau_b = time - t_cross_b + eps_expr
    tau_c = time - t_cross_c + eps_expr

    block = Block(
        algebraic_vars=[t_cross_a, t_cross_b, t_cross_c, gate_a, gate_b, gate_c],
        algebraic_eqs=[
            t_cross_a - cross_time(ref_a),
            t_cross_b - cross_time(ref_b),
            t_cross_c - cross_time(ref_c),
            gate_a - gate_expr(q_a),
            gate_b - gate_expr(q_b),
            gate_c - gate_expr(q_c),
        ],
        inequalities=[
            -(Const(2.0) * q_a - c_one) * tau_a,
            -(Const(2.0) * q_b - c_one) * tau_b,
            -(Const(2.0) * q_c - c_one) * tau_c,
        ],
        event_dict={
            ref_a: Const(float(ref_a0)),
            ref_b: Const(float(ref_b0)),
            ref_c: Const(float(ref_c0)),
            interval_start: Const(float(interval_start0)),
            half_period: Const(float(half_period0)),
        },
        init_eqs={
            t_cross_a: cross_time(ref_a),
            t_cross_b: cross_time(ref_b),
            t_cross_c: cross_time(ref_c),
            gate_a: gate_expr(q_a),
            gate_b: gate_expr(q_b),
            gate_c: gate_expr(q_c),
        },
        boolean_guards={
            q_a: sym.heaviside(tau_a),
            q_b: sym.heaviside(tau_b),
            q_c: sym.heaviside(tau_c),
            b_carrier_rise: sym.heaviside(Const(float(carrier_rising0)) - Const(0.5)),
        },
    )

    return (
        block,
        gate_a,
        gate_b,
        gate_c,
        t_cross_a,
        t_cross_b,
        t_cross_c,
        ref_a,
        ref_b,
        ref_c,
        interval_start,
        half_period,
        q_a,
        q_b,
        q_c,
        b_carrier_rise,
    )

def exponential_ml(vf: VarFactory, x:Expr, name:str=""):
    algebraic_eqs = list()
    algebraic_vars = list()
    y = vf.add_var('exp_' + name)
    dy = vf.add_diff_var('dt_'+y.name, base_var=y)
    
    if not isinstance(x, Var):
        u = vf.add_var(name + '_aux')
        aux_block = Block(
            algebraic_eqs=[u-x],
            algebraic_vars=[u],
            init_eqs={u:x},
        )
    else:
        aux_block = Block()
        u = x

    du = vf.add_diff_var('dt_'+u.name, base_var=u)
    children = [aux_block]
    block = Block(
        algebraic_eqs= [dy - du*y] + algebraic_eqs,
        algebraic_vars=[y] + algebraic_vars,
        diff_vars=[du, dy] ,
        init_eqs={
            y: sym.exp(u)
        }, 
        children=children
    )
    return block, y

def ml_heaviside(vf: VarFactory, u:Expr, name:str=''):
    u_plus1 = vf.add_var('u_plus1_' + name)
    u_plus2 = vf.add_var('u_plus2_' + name)
    u_minus1 = vf.add_var('u_minus1_' + name)
    u_minus2 = vf.add_var('u_minus2_' + name)
    hv = vf.add_var('hv_' + name)
    positive_part_block = Block(
        algebraic_eqs=[
            u - (u_plus1*u_plus2 - u_minus1*u_minus2),
            u - (hv*u_plus1*u_plus2 - (1-hv)*u_minus1*u_minus2),
            u_plus1*u_minus1,
            u_plus1 - u_plus2,
            u_minus1 - u_minus2,
        ],
        algebraic_vars=[hv, u_plus1, u_plus2, u_minus1, u_minus2],
        init_eqs={
            hv      : sym.heaviside(u), 
            u_plus1 : sym.sqrt(sym.max(u, Const(0))),
            u_plus2 : u_plus1,
            u_minus1: sym.sqrt(sym.max(-u, Const(0))),
            u_minus2: u_minus1,
        }
    )
    return positive_part_block, hv


def ml_heaviside_sigmoid(
    vf: VarFactory,
    u: Expr,
    name: str = '',
    k: Expr = Const(20.0),
    exp_clip: Expr = Const(60.0),
):
    hv = vf.add_var('hv_' + name)
    sig_arg = sym.max(sym.min(k * u, exp_clip), -exp_clip)
    hv_rhs = Const(1.0) / (Const(1.0) + sym.exp(-sig_arg))
    block = Block(
        algebraic_eqs=[hv - hv_rhs],
        algebraic_vars=[hv],
        init_eqs={hv: hv_rhs},
    )
    return block, hv


def ml_hard_sat_sigmoid(
    vf: VarFactory,
    u: Expr,
    u_min: Expr,
    u_max: Expr,
    name: str = '',
    k: Expr = Const(20.0),
    exp_clip: Expr = Const(60.0),
):
    block_min, h_min = ml_heaviside_sigmoid(vf, u - u_min, name=f"{name}_min", k=k, exp_clip=exp_clip)
    block_max, h_max = ml_heaviside_sigmoid(vf, u - u_max, name=f"{name}_max", k=k, exp_clip=exp_clip)
    sat_expr = u_min + (u - u_min) * h_min - (u - u_max) * h_max
    block = Block(children=[block_min, block_max])
    return block, sat_expr

def ml_piecewise_aux(vf: VarFactory, x: Expr, name: str = None):
    x, all_blocks, _ = ml_piecewise(vf, x, name=name, counter=0)
    block = Block(children = all_blocks)
    return block, x

def ml_piecewise(
        vf: VarFactory,
        x: Expr,
        name: str = '',
        counter: int = 0
    ) -> tuple[Expr, List[Block], int]:
    """
    Recursively traverse expression x, replacing Heaviside() nodes with
    ml_heaviside() outputs and collecting Blocks.
    Each Heaviside gets a unique suffix via an integer counter.
    """
    # --- base cases ---
    if isinstance(x, Var) or isinstance(x, Const):
        return x, list(), counter

    # --- Heaviside function case ---
    if isinstance(x, Func) and x.op == "heaviside":
        local_name = f"{name or 'hv'}_{counter}"
        block, y = ml_heaviside(vf, x.arg, local_name)
        return y, [block], counter + 1

    # --- General function (like sin, exp, etc.) ---
    if isinstance(x, Func):
        new_arg, blocks, counter = ml_piecewise(vf, x.arg, name, counter)
        x = Func(new_arg, x.op)
        return x, blocks, counter

    # --- Binary operator case (e.g. +, -, *, /, **) ---
    if isinstance(x, BinOp):
        left_new, blocks_left, counter = ml_piecewise(vf, x.left, name, counter)
        right_new, blocks_right, counter = ml_piecewise(vf, x.right, name, counter)
        x = BinOp(left=left_new, op= x.op, right=right_new)
        all_blocks = blocks_left + blocks_right
        return x, all_blocks, counter

    # --- fallback ---
    raise ValueError(f"Unsupported expression type: {type(x)}")

def park_transform(vf: VarFactory, X:Var, ang:Var, delta:Var, multilinear:bool = False):
    Xd = vf.add_var('Xd')
    Xq = vf.add_var('Xq')
    sqrt_2 = Const(np.sqrt(2))
    if not multilinear:
        block = Block(
            algebraic_eqs= [
            Xd - X*sym.cos(delta - ang)*sqrt_2,
            Xq - X*sym.sin(delta - ang)*sqrt_2,
            ],
            algebraic_vars= [Xd, Xq]
        )
    else:
        u_cos = vf.add_var('u_cos')
        u_sin = vf.add_var('u_sin')
        d_u_cos = vf.add_diff_var('d_u_cos', base_var=u_cos)
        d_u_sin = vf.add_diff_var('d_u_sin', base_var=u_sin)
        d_delta = vf.add_diff_var('d_delta', base_var=delta)
        d_ang = vf.add_diff_var('d_ang', base_var=ang)
        block = Block(
            algebraic_eqs= [
            Xd - X*u_cos*sqrt_2,
            Xq - X*u_sin*sqrt_2,
            ],
            algebraic_vars= [u_cos, u_cos, Xd, Xq],
            differential_eqs=[
                d_u_cos + (d_delta - d_ang)*u_sin,
                d_u_sin - (d_delta - d_ang)*u_cos,
            ],
            diff_vars=[d_u_sin, d_u_cos, d_delta, d_ang]
        )
    
    return Xd, Xq, block

def trig_transform(vf: VarFactory, u:Expr, type = 'usual'):
    aux_block = None
    if not isinstance(u, Var):
        x = vf.add_var('x')
        aux_block = Block(
            algebraic_eqs=[x - u],
            algebraic_vars=[x],
            init_eqs={x:u}
        )
    else:
        x = u
    if type == 'usual':
        u_cos = vf.add_var('u_cos')
        u_sin = vf.add_var('u_sin')
        d_u_cos = vf.add_diff_var('d_u_cos', base_var=u_cos)
        d_u_sin = vf.add_diff_var('d_u_sin', base_var=u_sin)
        dx = vf.add_diff_var('d_delta', base_var=x)
        block = Block(
            algebraic_vars= [u_cos, u_sin],
            algebraic_eqs =[
                d_u_cos + (dx)*u_sin,
                d_u_sin - (dx)*u_cos,
            ],
            diff_vars=[d_u_sin, d_u_cos, dx],
            reformulated_vars=[u_sin, u_cos],
            init_eqs={
                #x:u,
                u_cos: sym.cos(x),
                u_sin: sym.sin(x),
            }
        )
    elif type == 'norm':
        u_cos = vf.add_var('u_cos')
        u_sin = vf.add_var('u_sin')
        u_cos_n = vf.add_var('u_cos_n')
        u_sin_n = vf.add_var('u_sin_n')

        norm = vf.add_var('norm')
        u_cos_aux = vf.add_var('u_cos_aux')
        u_sin_aux = vf.add_var('u_sin_aux')
        norm_aux = vf.add_var('norm_aux')

        d_u_cos = vf.add_diff_var('d_u_cos', base_var=u_cos)
        d_u_sin = vf.add_diff_var('d_u_sin', base_var=u_sin)
        dx = vf.add_diff_var('d_delta', base_var=x)
        block = Block(
            algebraic_vars= [u_cos, u_sin],
            differential_eqs=[
                d_u_cos + (dx)*u_sin,
                d_u_sin - (dx)*u_cos,
            ],
            diff_vars=[d_u_sin, d_u_cos, dx],
        )
        norm_block = Block(
            algebraic_eqs=[
                norm - norm_aux,
                u_cos - u_cos_aux,
                u_sin - u_sin_aux,
                norm*norm_aux - (u_cos*u_cos_aux + u_sin*u_sin_aux),
                u_cos_n*norm - u_cos,
                u_sin_n*norm - u_sin,
            ],
            algebraic_vars=[norm, norm_aux, u_cos_n, u_sin_n, u_sin_aux, u_cos_aux],
            init_eqs={
                x:u,
                u_cos: sym.cos(x),
                u_cos_aux: sym.cos(x),
                u_cos_n: sym.cos(x),
                u_sin: sym.sin(x),
                u_sin_aux: sym.sin(x),
                u_sin_n: sym.sin(x),
                norm: Const(1),
                norm_aux: Const(1),
            }
        )
        u_cos = u_cos_n
        u_sin = u_sin_n
        block.add(norm_block)

    elif type =='singular':
        int_xsinx = vf.add_var('int_xsinx')
        int_xcosx = vf.add_var('int_xcosx')
        dt_int_xsinx = vf.add_diff_var('dt_int_xsinx', base_var=int_xsinx)
        dt_int_xcosx = vf.add_diff_var('dt_int_xcosx', base_var=int_xcosx)
        u_cos = vf.add_var('u_cos')
        u_sin = vf.add_var('u_sin')
        d_u_cos = vf.add_diff_var('d_u_cos', base_var=u_cos)
        d_u_sin = vf.add_diff_var('d_u_sin', base_var=u_sin)
        dx = vf.add_diff_var('d_delta', base_var=x)
        block = Block(
            algebraic_vars= [u_cos, u_sin, int_xcosx, int_xsinx],
            algebraic_eqs=[
                #int_xsinx - (u_sin - (x)*u_cos), 
                #int_xcosx - ((x)*u_sin + u_cos),
                (int_xsinx + x*int_xcosx)/(1+x**2) - u_sin,
                (int_xcosx - x*int_xsinx)/(1+x**2) - u_cos,
            ],
            differential_eqs = [
                dt_int_xsinx - dx*(u_sin*(x)),
                dt_int_xcosx - dx*(u_cos*(x)),
            ],
            diff_vars=[ dx, dt_int_xcosx, dt_int_xsinx],
            init_eqs={
                #x:u,
                u_cos: sym.cos(x),
                u_sin: sym.sin(x),
                int_xsinx: sym.sin(x) - x*sym.cos(x),
                int_xcosx: x*sym.sin(x) + sym.cos(x),
                dt_int_xsinx: dx*sym.sin(x)*x,
                dt_int_xcosx: dx*sym.cos(x)*x,
            }
        )
    else:
        u_cos = vf.add_var('u_cos')
        u_sin = vf.add_var('u_sin')
        int_sin2 = vf.add_var('int_sin2')
        int_sin2cos2 = vf.add_var('int_sin2cos2')
        dt_int_sin2 = vf.add_diff_var('dt_int_sin2', base_var=int_sin2)
        dt_int_sin2cos2 = vf.add_diff_var('dt_int_sin2cos2', base_var=int_sin2cos2)
        dx = vf.add_diff_var('d_delta', base_var=x)
        block = Block(
            algebraic_vars= [u_cos, u_sin, int_sin2, int_sin2cos2],
            algebraic_eqs=[
                int_sin2 - 0.5*((x)-u_sin*u_cos), 
                int_sin2cos2 - 1/32*(4*(x) - (4*u_cos**3*u_sin - 4*u_sin**3*u_cos)),
            ],
            differential_eqs = [       
                dt_int_sin2 - (dx)*u_sin**2,
                dt_int_sin2cos2 - (dx)*u_sin**2*u_cos**2
            ],
            init_eqs={
                u_cos: sym.cos(x),
                u_sin: sym.sin(x),
                int_sin2: 0.5*(x - u_sin*u_cos),
                int_sin2cos2: 1/32*(4*x - 4*u_cos**3*u_sin + 4*u_sin**3*u_cos),
                dt_int_sin2: dx*u_sin**2,
                dt_int_sin2cos2: dx*u_sin**2*u_cos**2,
            },
            diff_vars=[dx, dt_int_sin2, dt_int_sin2cos2],
        )

    if aux_block is not None:
        block.add(aux_block)
    return block, u_cos, u_sin

def trig_transform_diff(vf: VarFactory, delta1:Expr, delta2:Expr):
    aux_block = None
    
    if not isinstance(delta1, Var):
        x1 = vf.add_var('x1')
        aux_block1 = Block(
            algebraic_eqs=[x1 - delta1],
            algebraic_vars=[x1],
            init_eqs={x1: delta1}
        )
    else:
        x1 = delta1
        aux_block1 = None
    
    if not isinstance(delta2, Var):
        x2 = vf.add_var('x2')
        aux_block2 = Block(
            algebraic_eqs=[x2 - delta2],
            algebraic_vars=[x2],
            init_eqs={x2: delta2}
        )
    else:
        x2 = delta2
        aux_block2 = None
    
    diff = x1 - x2
    
    u_cos = vf.add_var('u_cos')
    u_sin = vf.add_var('u_sin')
    d_u_cos = vf.add_diff_var('d_u_cos', base_var=u_cos)
    d_u_sin = vf.add_diff_var('d_u_sin', base_var=u_sin)
    d_delta1 = vf.add_diff_var('d_delta1', base_var=x1)
    d_delta2 = vf.add_diff_var('d_delta2', base_var=x2)
    
    block = Block(
        algebraic_vars=[u_cos, u_sin],
        algebraic_eqs=[
            d_u_cos + (d_delta1 - d_delta2) * u_sin,
            d_u_sin - (d_delta1 - d_delta2) * u_cos,
        ],
        diff_vars=[d_u_sin, d_u_cos, d_delta1, d_delta2],
        reformulated_vars=[u_sin, u_cos],
        init_eqs={
            u_cos: sym.cos(diff),
            u_sin: sym.sin(diff),
        }
    )
    
    if aux_block1 is not None:
        block.add(aux_block1)
    if aux_block2 is not None:
        block.add(aux_block2)
    
    return block, u_cos, u_sin

def ml_f_exc(vf: VarFactory, In:Expr):
    ml_block1, hv1 = ml_heaviside(vf, Const(0.433) - In)
    ml_block2, hv2 = ml_heaviside(vf, Const(0.75) - In)
    ml_block3, hv3 = ml_heaviside(vf, Const(1.0) - In)

    In_aux = vf.add_var('In_aux')
    sqrt1 = vf.add_var('sqrt1')
    sqrt2 = vf.add_var('sqrt2')
    exp1 = (Const(1) - Const(0.577) * In)
    exp2 = (Const(0.75)  - In*In_aux)
    exp3 = (Const(1.732) - In * Const(1.732))
    b = (exp1 - sqrt1) * hv1
    c = (sqrt1 - exp3) * hv2
    d =  exp3 * hv3
    res_block = Block(
        algebraic_eqs=[
            In_aux -In,
            sqrt1 -sqrt2,
            hv2*(sqrt1*sqrt2 - exp2),
        ],
        algebraic_vars=[In_aux, sqrt1, sqrt2],
        init_eqs={
            In_aux:In,
            sqrt1: sym.sqrt(sym.max(exp2, Const(1e-6))),
            sqrt2: sqrt1,
        },
        children = [ml_block1, ml_block2, ml_block3]
    )
    return res_block, b + c + d
