# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-
from __future__ import annotations

import math
from typing import Dict, List, Tuple

import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import BlockType, VarPowerFlowReferenceType

measurement_vars_dict = {"dc_bus": {BlockType.MEASUREMENTS_VOLTAGE_FROM_DC: [VarPowerFlowReferenceType.UR, VarPowerFlowReferenceType.U],
                                    BlockType.MEASUREMENTS_CURRENT_FROM_DC: [VarPowerFlowReferenceType.I_DC],
                                    BlockType.MEASUREMENTS_VOLTAGE_ANGLE: [VarPowerFlowReferenceType.Vdc],
                                    BlockType.MEASUREMENTS_P_Q: [VarPowerFlowReferenceType.P]

                                    },

                         "a_c_bus": {BlockType.MEASUREMENTS_VOLTAGE_FROM_POLAR: [VarPowerFlowReferenceType.U, VarPowerFlowReferenceType.UR_A, VarPowerFlowReferenceType.UR_B, VarPowerFlowReferenceType.UR_C, VarPowerFlowReferenceType.UI_A,
                                                                             VarPowerFlowReferenceType.UI_B, VarPowerFlowReferenceType.UI_C],
                                      BlockType.MEASUREMENTS_CURRENT_FROM_PQ: [VarPowerFlowReferenceType.UR,
                                                                               VarPowerFlowReferenceType.UI,
                                                                               VarPowerFlowReferenceType.IR,
                                                                               VarPowerFlowReferenceType.II,
                                                                               VarPowerFlowReferenceType.IR_B,
                                                                               VarPowerFlowReferenceType.IR_C,
                                                                               VarPowerFlowReferenceType.II_B,
                                                                               VarPowerFlowReferenceType.II_C],
                                     BlockType.MEASUREMENTS_VOLTAGE_ANGLE: [VarPowerFlowReferenceType.Vm,
                                                                            VarPowerFlowReferenceType.Va],
                                     BlockType.MEASUREMENTS_P_Q: [VarPowerFlowReferenceType.P,
                                                                  VarPowerFlowReferenceType.Q]
                                     }}

def _rotate_complex_components(real_part: Expr, imag_part: Expr, angle_rad: float) -> tuple[Expr, Expr]:
    """
    Rotate one complex quantity by one fixed phase angle.

    :param real_part: Real component.
    :param imag_part: Imaginary component.
    :param angle_rad: Rotation angle in radians.
    :return: Rotated ``(real, imag)`` pair.
    """
    cos_a: Const = Const(math.cos(angle_rad))
    sin_a: Const = Const(math.sin(angle_rad))
    rotated_real: Expr = (real_part * cos_a) - (imag_part * sin_a)
    rotated_imag: Expr = (real_part * sin_a) + (imag_part * cos_a)
    return rotated_real, rotated_imag


def build_rms_voltage_meter_outputs_from_polar(var_factory: VarFactory,
                                               vm: Var,
                                               va: Var,
                                               measured_frequency_hz: Const,
                                               nominal_frequency_hz: Const) -> Tuple[Block, List[Var]]:
    """
    Build the VeraGrid RMS output set of one AC voltage meter.

    :param var_factory: Var factory.
    :param vm: Voltage magnitude.
    :param va: Voltage angle in radians.
    :param measured_frequency_hz: Measured frequency in Hz.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :return: Signal-name to expression mapping.
    """
    # create block
    block = Block()

    #create_variables

    u = var_factory.add_var(name = "u", reference=VarPowerFlowReferenceType.U)
    ur_a = var_factory.add_var(name = "ur_a", reference=VarPowerFlowReferenceType.UR_A)
    ui_a = var_factory.add_var(name="ui_a", reference=VarPowerFlowReferenceType.UI_A)
    ur_b = var_factory.add_var(name="ur_b", reference=VarPowerFlowReferenceType.UR_B)
    ui_b = var_factory.add_var(name="ui_b", reference=VarPowerFlowReferenceType.UI_B)
    ur_c = var_factory.add_var(name="ur_c", reference=VarPowerFlowReferenceType.UR_C)
    ui_c = var_factory.add_var(name="ui_c", reference=VarPowerFlowReferenceType.UI_C)

    variables = [u, ur_a, ui_a, ur_b, ui_b, ur_c, ui_c]


    # create rotation equations
    rotated_real_ur_b, rotated_imag_ui_b = _rotate_complex_components(ur_a, ui_a, -2.0 * math.pi / 3.0)
    rotated_real_ur_c, rotated_imag_ui_c = _rotate_complex_components(ur_a, ui_a, 2.0 * math.pi / 3.0)

    # fill block
    block.algebraic_vars = variables
    block.algebraic_eqs = [ur_a - vm * sym.cos(va), ui_a - vm * sym.sin(va), ur_b - rotated_real_ur_b,
                           ui_b - rotated_imag_ui_b, ur_c - rotated_real_ur_c, ui_c - rotated_imag_ui_c,
                           u - vm]

    return block, variables


def build_rms_voltage_meter_outputs_from_dc(var_factory: VarFactory,
                                            vdc: Var,
                                            nominal_frequency_hz: Expr)  -> Tuple[Block, List[Var]]:
    """
    Build the VeraGrid RMS output set of one DC voltage meter.

    :param var_factory: Var factory.
    :param vdc: DC voltage magnitude.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :return: Signal-name to expression mapping.
    """
    # zero: Const = Const(0.0)

    # create block
    block = Block()

    # create_variables

    u = var_factory.add_var(name="u", reference=VarPowerFlowReferenceType.U)
    ur = var_factory.add_var(name="ur", reference=VarPowerFlowReferenceType.UR)

    variables = [u, ur]

    # fill block
    block.algebraic_vars = variables
    block.algebraic_eqs = [ur - vdc,
                           u - vdc]

    return block, variables

def build_rms_current_meter_outputs_from_pq(var_factory: VarFactory,
                                            vm: Var,
                                            va: Var,
                                            p: Var,
                                            q: Var) -> Tuple[Block, List[Var]]:
    """
    Build the VeraGrid RMS current outputs from ``P/Q`` and ``V``.

    :param var_factory: Var factory.
    :param vm: Voltage magnitude.
    :param va: Voltage angle in radians.
    :param p: Active power.
    :param q: Reactive power.
    :return: Signal-name to expression mapping.
    """

    # create block
    block = Block()

    # create_variables

    ur = var_factory.add_var(name="ur", reference=VarPowerFlowReferenceType.UR)
    ui = var_factory.add_var(name="ui", reference=VarPowerFlowReferenceType.UI)
    ir = var_factory.add_var(name="ir", reference=VarPowerFlowReferenceType.UI)
    ii = var_factory.add_var(name="ii", reference=VarPowerFlowReferenceType.UI)
    ir_b = var_factory.add_var(name="ir_b", reference=VarPowerFlowReferenceType.UI)
    ii_b = var_factory.add_var(name="ii_b", reference=VarPowerFlowReferenceType.UI)
    ir_c = var_factory.add_var(name="ir_c", reference=VarPowerFlowReferenceType.UI)
    ii_c = var_factory.add_var(name="ii_c", reference=VarPowerFlowReferenceType.UI)


    variables = [ur, ui, ir, ii, ir_b, ii_b, ir_c, ii_c]

    ir_b_expr, ii_b_expr = _rotate_complex_components(ir, ii, -2.0 * math.pi / 3.0)
    ir_c_expr, ii_c_expr = _rotate_complex_components(ir, ii, 2.0 * math.pi / 3.0)

    # fill block
    block.algebraic_vars = variables
    block.algebraic_eqs = [ur - vm * sym.cos(va),
                           ui -  vm * sym.sin(va),
                           ir - (p * ur + q * ui) /(vm * vm) + Const(1e-9),
                           ii - (p * ui - q * ur) / (vm * vm) + Const(1e-9),
                           ir_b - ir_b_expr,
                           ii_b - ii_b_expr,
                           ir_c - ir_c_expr,
                           ii_c - ii_c_expr]

    return block, variables

def build_rms_current_meter_outputs_from_dc(
        var_factory: VarFactory,
        vdc: Var,
        p: Var,
) -> Tuple[Block, List[Var]]:
    """Build the RMS-editor current channels of one DC terminal.

    DC terminal power follows ``P = Vdc * Idc``.  The regularized quotient
    keeps the generated symbolic model finite while a bus is de-energized and
    uses the real current channel shared by the balanced meter interface.

    :param var_factory: Var factory.
    :param vdc: DC terminal voltage.
    :param p: Signed active power at the same terminal.
    :return: Single signed ``Idc`` current expression.
    """

    # create block
    block = Block()

    # create_variables
    idc = var_factory.add_var(name="ur", reference=VarPowerFlowReferenceType.UR)

    variables = [idc]

    # fill block
    block.algebraic_vars = variables
    block.algebraic_eqs = [idc - (p * vdc) / ((vdc * vdc) + Const(1e-9))]

    return block, variables

def build_rms_power_meter_outputs_from_pq(p: Expr, q: Expr) -> Dict[str, Expr]:
    """
    Build the VeraGrid RMS active/reactive power outputs.

    :param p: Active power.
    :param q: Reactive power.
    :return: Signal-name to expression mapping.
    """
    zero: Const = Const(0.0)
    return {
        "p": p,
        "q": q,
        "p2": zero,
        "q2": zero,
        "p0": zero,
        "q0": zero,
    }