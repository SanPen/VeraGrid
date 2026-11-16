# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Explicit reference-frame interfaces for native converter equipment."""
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def add_native_vsc_dq_interface(equipment: Block, system_base_mva: float,
                                equipment_base_mva: float) -> Block:
    """Expose PF Pmd/Pmq and generator-oriented equipment-base id/iq.

    PF2024 PWM section 5.1 defines the rotation through cosref/sinref.
    The physical bridge uses stationary modulation and load-oriented terminal
    powers; its current probes therefore change sign and power base here.
    """
    inputs = {variable.name: variable for variable in equipment.in_vars}
    outputs = {variable.name: variable for variable in equipment.out_vars}
    pmr, pmi = inputs['Pmr'], inputs['Pmi']
    vm, va = inputs['Vm'], inputs['Va']
    pac, qac = outputs['Pac'], outputs['Qac']
    pmd, pmq = Var('Pmd'), Var('Pmq')
    cosine, sine = Var('cosref'), Var('sinref')
    current_d, current_q = Var('id'), Var('iq')
    vr, vi = vm * sym.cos(va), vm * sym.sin(va)
    base = system_base_mva / equipment_base_mva
    ir = -base * (pac * vr + qac * vi) / (vm * vm + 1e-9)
    ii = -base * (pac * vi - qac * vr) / (vm * vm + 1e-9)
    id_expr = ir * cosine + ii * sine
    iq_expr = -ir * sine + ii * cosine
    equipment.in_vars = [variable for variable in equipment.in_vars
                         if variable.uid not in (pmr.uid, pmi.uid)] + [pmd, pmq, cosine, sine]
    equipment.algebraic_vars.extend([pmr, pmi, current_d, current_q])
    equipment.algebraic_eqs.extend([
        pmr - (pmd * cosine - pmq * sine),
        pmi - (pmd * sine + pmq * cosine),
        current_d - id_expr, current_q - iq_expr,
    ])
    equipment.out_vars.extend([current_d, current_q])
    initial = {pmd: pmr * cosine + pmi * sine,
               pmq: -pmr * sine + pmi * cosine,
               current_d: id_expr, current_q: iq_expr}
    equipment.init_eqs.update(initial)
    equipment.post_init_seed_eqs.update(initial)
    return equipment
