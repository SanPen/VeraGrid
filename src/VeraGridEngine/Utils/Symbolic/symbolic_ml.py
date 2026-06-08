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
