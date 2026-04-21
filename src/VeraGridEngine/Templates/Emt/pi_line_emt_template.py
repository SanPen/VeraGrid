# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Any, Dict
import numpy as np

from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType, ParamPowerFlowRefferenceType, EmtLineTypes
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Utils.Symbolic.block import Var, Expr

def get_pi_line_emt_template(vf: VarFactory,
                             phN: bool = False,
                             phA: bool = True,
                             phB: bool = True,
                             phC: bool = True,
                             name: str = "Pi") -> EmtModelTemplate:
    """
    Build the EMT pi-line template with explicit API-mapped parameters.

    The line connection defines which phases are physically present, while the
    EMT initializer later injects the electrical ``R``, ``Linv`` and ``C``
    values through the block ``api_obj_mapping`` using the full 4x4 NABC enum
    contract.

    :param vf: EMT variable factory.
    :param phN: Bool. True if the line has neutral, else False.
    :param phA: Bool. True if the line has phase A, else False.
    :param phB: Bool. True if the line has phase B, else False.
    :param phC: Bool. True if the line has phase C, else False.
    :param name: Symbolic model name.
    :return: EMT pi-line model template.
    :raises ValueError: If the line has no active phases.
    """
    templ = EmtModelTemplate()
    templ.tpe = DeviceType.LineDevice
    templ.name = name

    templ.block.name = EmtLineTypes.PI.value

    c0 = vf.add_const(0.0)

    # -----------------------------
    # Phase mask from the line itself [N,A,B,C]
    # -----------------------------
    # The template phase layout must be driven exclusively by the explicit
    # phase flags of the current API. The optional ``line`` argument remains
    # only for backward compatibility with older callers.
    ph_mask = np.array([
        phN,
        phA,
        phB,
        phC,
    ], dtype=bool)

    ph_labels = list(["N", "A", "B", "C"])
    idx_global = np.where(ph_mask)[0]  # indices in global NABC convention
    active_ph = list(ph_labels[i] for i in idx_global)
    m = len(active_ph)

    if m == 0:
        raise ValueError(f"PI line '{name}' has no enabled phases in line.ys")

    # -----------------------------
    # Define the fixed NABC API mapping contract.
    # The initializer writes parameter values into these exact enum slots,
    # which is why the template must read them back with the same layout.
    # -----------------------------
    r_enums = list([
        list([
            ParamPowerFlowRefferenceType.Rnn, ParamPowerFlowRefferenceType.Rna,
            ParamPowerFlowRefferenceType.Rnb, ParamPowerFlowRefferenceType.Rnc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Ran, ParamPowerFlowRefferenceType.Raa,
            ParamPowerFlowRefferenceType.Rab, ParamPowerFlowRefferenceType.Rac,
        ]),
        list([
            ParamPowerFlowRefferenceType.Rbn, ParamPowerFlowRefferenceType.Rba,
            ParamPowerFlowRefferenceType.Rbb, ParamPowerFlowRefferenceType.Rbc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Rcn, ParamPowerFlowRefferenceType.Rca,
            ParamPowerFlowRefferenceType.Rcb, ParamPowerFlowRefferenceType.Rcc,
        ]),
    ])
    linv_enums = list([
        list([
            ParamPowerFlowRefferenceType.Linv_nn, ParamPowerFlowRefferenceType.Linv_na,
            ParamPowerFlowRefferenceType.Linv_nb, ParamPowerFlowRefferenceType.Linv_nc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Linv_an, ParamPowerFlowRefferenceType.Linv_aa,
            ParamPowerFlowRefferenceType.Linv_ab, ParamPowerFlowRefferenceType.Linv_ac,
        ]),
        list([
            ParamPowerFlowRefferenceType.Linv_bn, ParamPowerFlowRefferenceType.Linv_ba,
            ParamPowerFlowRefferenceType.Linv_bb, ParamPowerFlowRefferenceType.Linv_bc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Linv_cn, ParamPowerFlowRefferenceType.Linv_ca,
            ParamPowerFlowRefferenceType.Linv_cb, ParamPowerFlowRefferenceType.Linv_cc,
        ]),
    ])
    c_enums = list([
        list([
            ParamPowerFlowRefferenceType.Cnn, ParamPowerFlowRefferenceType.Cna,
            ParamPowerFlowRefferenceType.Cnb, ParamPowerFlowRefferenceType.Cnc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Can, ParamPowerFlowRefferenceType.Caa,
            ParamPowerFlowRefferenceType.Cab, ParamPowerFlowRefferenceType.Cac,
        ]),
        list([
            ParamPowerFlowRefferenceType.Cbn, ParamPowerFlowRefferenceType.Cba,
            ParamPowerFlowRefferenceType.Cbb, ParamPowerFlowRefferenceType.Cbc,
        ]),
        list([
            ParamPowerFlowRefferenceType.Ccn, ParamPowerFlowRefferenceType.Cca,
            ParamPowerFlowRefferenceType.Ccb, ParamPowerFlowRefferenceType.Ccc,
        ]),
    ])

    # -----------------------------
    # Create the symbolic parameter variables and publish them in the API map.
    # The EMT problem writes numerical values into these variables later, so the
    # template equations must depend on the mapped variables instead of line data.
    # -----------------------------
    phases = list(["n", "a", "b", "c"])
    for i in range(4):
        for j in range(4):
            var_r = vf.add_var(f"R{phases[i]}{phases[j]}_{name}")
            templ.block.api_obj_mapping[r_enums[i][j]] = var_r

            var_l = vf.add_var(f"Linv_{phases[i]}{phases[j]}_{name}")
            templ.block.api_obj_mapping[linv_enums[i][j]] = var_l

            var_c = vf.add_var(f"C{phases[i]}{phases[j]}_{name}")
            templ.block.api_obj_mapping[c_enums[i][j]] = var_c

    # -----------------------------
    # Reduce the full mapped matrices using the physical line phase mask.
    # This cleanly separates topology from parameters: line.ys chooses the
    # active equations, while api_obj_mapping supplies the electrical values.
    # -----------------------------
    api_mapping: Dict[ParamPowerFlowRefferenceType, Var] = templ.block.api_obj_mapping
    r_full: list[list[Var]] = list()
    linv_full: list[list[Var]] = list()
    c_full: list[list[Var]] = list()

    for i in range(4):
        r_row: list[Var] = list()
        linv_row: list[Var] = list()
        c_row: list[Var] = list()

        for j in range(4):
            r_row.append(api_mapping[r_enums[i][j]])
            linv_row.append(api_mapping[linv_enums[i][j]])
            c_row.append(api_mapping[c_enums[i][j]])

        r_full.append(r_row)
        linv_full.append(linv_row)
        c_full.append(c_row)

    R_red = list(list(r_full[i][j] for j in idx_global) for i in idx_global)
    Linv_red = list(list(linv_full[i][j] for j in idx_global) for i in idx_global)
    C_red = list(list(c_full[i][j] for j in idx_global) for i in idx_global)

    # -----------------------------
    # Create ONLY active terminal voltage input vars
    # -----------------------------
    vf_keys = dict({
        "N": VarPowerFlowRefferenceType.vf_N,
        "A": VarPowerFlowRefferenceType.vf_A,
        "B": VarPowerFlowRefferenceType.vf_B,
        "C": VarPowerFlowRefferenceType.vf_C,
    })
    vt_keys = dict({
        "N": VarPowerFlowRefferenceType.vt_N,
        "A": VarPowerFlowRefferenceType.vt_A,
        "B": VarPowerFlowRefferenceType.vt_B,
        "C": VarPowerFlowRefferenceType.vt_C,
    })

    vf_vars = [vf.add_var(name=f"vf_{ph_label}_{name}", reference=vf_keys[ph_label]) for ph_label in active_ph]
    vt_vars = [vf.add_var(name=f"vt_{ph_label}_{name}", reference=vt_keys[ph_label]) for ph_label in active_ph]

    d_vf_vars = [vf.add_diff_var(name=f"d_vf_{ph_label}_{name}", base_var=v_base) for ph_label, v_base in zip(active_ph, vf_vars)]
    d_vt_vars = [vf.add_diff_var(name=f"d_vt_{ph_label}_{name}", base_var=v_base) for ph_label, v_base in zip(active_ph, vt_vars)]


    # -----------------------------
    # Create model vars
    # -----------------------------
    i_ser = [vf.add_var(name=f"i_ser_{name}_{ph_label}") for ph_label in active_ph]
    q_f = [vf.add_var(name=f"q_f_{name}_{ph_label}") for ph_label in active_ph]
    q_t = [vf.add_var(name=f"q_t_{name}_{ph_label}") for ph_label in active_ph]

    di_ser = [vf.add_diff_var(name=f"di_ser_{name}_{ph_label}", base_var=i_ser[k]) for k, ph_label  in enumerate(active_ph)]
    dq_f = [vf.add_diff_var(name=f"dq_f_{name}_{ph_label}", base_var=q_f[k]) for k, ph_label  in enumerate(active_ph)]
    dq_t = [vf.add_diff_var(name=f"dq_t_{name}_{ph_label}", base_var=q_t[k]) for k, ph_label  in enumerate(active_ph)]

    i_cap_f = [vf.add_var(name=f"i_cap_f_{name}_{ph_label}") for ph_label in active_ph]
    i_cap_t = [vf.add_var(name=f"i_cap_t_{name}_{ph_label}") for ph_label in active_ph]
    if_act = [vf.add_var(name=f"if_{name}_{ph_label}") for ph_label in active_ph]
    it_act = [vf.add_var(name=f"it_{name}_{ph_label}") for ph_label in active_ph]

    # -----------------------------
    # Build block
    # -----------------------------
    templ.block.in_vars = vf_vars + vt_vars
    templ.block.state_vars = i_ser + q_f + q_t
    templ.block.diff_vars = di_ser + dq_f + dq_t
    templ.block.algebraic_vars = i_cap_f + i_cap_t + if_act + it_act

    # -----------------------------
    # State equations
    # -----------------------------
    state_eqs = []

    for a in range(m):
        expr_rhs = c0
        for b in range(m):
            L_inv_ab = Linv_red[a][b]
            term_b = (vf_vars[b] - vt_vars[b])
            for k in range(m):
                R_bk = R_red[b][k]
                term_b = term_b - R_bk * i_ser[k]
            expr_rhs = expr_rhs + L_inv_ab * term_b
        state_eqs.append(expr_rhs)

    for a in range(m):
        state_eqs.append(i_cap_f[a])
    for a in range(m):
        state_eqs.append(i_cap_t[a])

    templ.block.state_eqs = state_eqs

    # -----------------------------
    # Algebraic equations
    # -----------------------------
    alg_eqs = []

    for a in range(m):
        rhs_q = c0
        for b in range(m):
            C_ab = C_red[a][b]
            rhs_q = rhs_q + C_ab * vf_vars[b]
        alg_eqs.append(q_f[a] - rhs_q)

    for a in range(m):
        rhs_q = c0
        for b in range(m):
            C_ab = C_red[a][b]
            rhs_q = rhs_q + C_ab * vt_vars[b]
        alg_eqs.append(q_t[a] - rhs_q)

    G_damp = 1e-5
    for a in range(m):
        alg_eqs.append(if_act[a] - (i_ser[a] + i_cap_f[a] + G_damp * vf_vars[a]))
        alg_eqs.append(it_act[a] - (-i_ser[a] + i_cap_t[a] + G_damp * vt_vars[a]))

    templ.block.algebraic_eqs = alg_eqs
    templ.block.out_vars = if_act + it_act

    # -----------------------------
    # External mapping
    # -----------------------------
    if_keys = dict({"N": VarPowerFlowRefferenceType.if_N, "A": VarPowerFlowRefferenceType.if_A, "B": VarPowerFlowRefferenceType.if_B, "C": VarPowerFlowRefferenceType.if_C})
    it_keys = dict({"N": VarPowerFlowRefferenceType.it_N, "A": VarPowerFlowRefferenceType.it_A, "B": VarPowerFlowRefferenceType.it_B, "C": VarPowerFlowRefferenceType.it_C})
    Sf_keys = dict({"A": VarPowerFlowRefferenceType.Sf_A, "B": VarPowerFlowRefferenceType.Sf_B, "C": VarPowerFlowRefferenceType.Sf_C})
    St_keys = dict({"A": VarPowerFlowRefferenceType.St_A, "B": VarPowerFlowRefferenceType.St_B, "C": VarPowerFlowRefferenceType.St_C})
    d_vf_keys = dict({"N": VarPowerFlowRefferenceType.d_v_N_f, "A": VarPowerFlowRefferenceType.d_v_A_f, "B": VarPowerFlowRefferenceType.d_v_B_f, "C": VarPowerFlowRefferenceType.d_v_C_f})
    d_vt_keys = dict({"N": VarPowerFlowRefferenceType.d_v_N_t, "A": VarPowerFlowRefferenceType.d_v_A_t, "B": VarPowerFlowRefferenceType.d_v_B_t, "C": VarPowerFlowRefferenceType.d_v_C_t})

    mapping: Dict[VarPowerFlowRefferenceType, Var | None] = dict({
        if_keys["N"]: None, if_keys["A"]: None, if_keys["B"]: None, if_keys["C"]: None,
        it_keys["N"]: None, it_keys["A"]: None, it_keys["B"]: None, it_keys["C"]: None,
        vf_keys["N"]: None, vf_keys["A"]: None, vf_keys["B"]: None, vf_keys["C"]: None,
        vt_keys["N"]: None, vt_keys["A"]: None, vt_keys["B"]: None, vt_keys["C"]: None,
        Sf_keys["A"]: None, Sf_keys["B"]: None, Sf_keys["C"]: None,
        St_keys["A"]: None, St_keys["B"]: None, St_keys["C"]: None,
        d_vf_keys["N"]: None, d_vf_keys["A"]: None, d_vf_keys["B"]: None, d_vf_keys["C"]: None,
        d_vt_keys["N"]: None, d_vt_keys["A"]: None, d_vt_keys["B"]: None, d_vt_keys["C"]: None,
    })

    for k, phase_label in enumerate(active_ph):
        mapping[vf_keys[phase_label]] = vf_vars[k]
        mapping[vt_keys[phase_label]] = vt_vars[k]
        mapping[if_keys[phase_label]] = if_act[k]
        mapping[it_keys[phase_label]] = it_act[k]
        mapping[d_vf_keys[phase_label]] = d_vf_vars[k]
        mapping[d_vt_keys[phase_label]] = d_vt_vars[k]

    templ.block.external_mapping = mapping

    # -----------------------------
    # Init equations
    # -----------------------------
    init_eqs: Dict[Var, Expr] = {}

    for a in range(m):
        rhs_f = c0
        rhs_t = c0
        for b in range(m):
            C_ab = C_red[a][b]
            rhs_f += C_ab * vf_vars[b]
            rhs_t += C_ab * vt_vars[b]
        init_eqs[q_f[a]] = rhs_f
        init_eqs[q_t[a]] = rhs_t

    for a in range(m):
        init_eqs[i_ser[a]] = if_act[a] - i_cap_f[a]

    templ.block.init_eqs = init_eqs

    # -----------------------------
    # Derivative initialization
    # -----------------------------
    diff_init_eqs: Dict[Var, Expr] = {}

    for a in range(m):
        di_expression = c0
        for b in range(m):
            term_b = (vf_vars[b] - vt_vars[b])
            for k in range(m):
                R_bk = R_red[b][k]
                term_b = term_b - R_bk * i_ser[k]
            coeff = Linv_red[a][b]
            di_expression = di_expression + coeff * term_b
        diff_init_eqs[di_ser[a]] = di_expression

    for a in range(m):
        diff_init_eqs[dq_f[a]] = i_cap_f[a]
        diff_init_eqs[dq_t[a]] = i_cap_t[a]

    for a in range(m):
        # -----------------------------
        # Initialize capacitor currents without terminal voltage derivatives.
        # The helper d_vf/d_vt symbols are not bound by the EMT assembler during
        # explicit initialization, so referencing them here leaves the explicit
        # initializer without values for those UIDs.
        #
        # Using zero capacitor current preserves the previous startup state used
        # by the fallback initialization path and keeps the template self-contained
        # for explicit initialization.
        # -----------------------------
        init_eqs[i_cap_f[a]] = c0
        init_eqs[i_cap_t[a]] = c0

    templ.block.diff_init_eqs = diff_init_eqs

    return templ
