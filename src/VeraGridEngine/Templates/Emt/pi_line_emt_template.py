# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Dict
import numpy as np
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Utils.Symbolic.block import Var, Expr

class PiLineEmtTemplate(EmtModelTemplate):
    """
    Continuous-time PI line model in abc (matrix-coupled), no internal discretization.

    Inputs (in_vars) - ONLY active phases:
      vf_{ph}_{line.name}, vt_{ph}_{line.name}  (instantaneous terminal voltages in pu)

    States (active dimension m):
      i_ser[k]   series current
      q_f[k]     shunt charge at from end
      q_t[k]     shunt charge at to end

    Diff vars:
      di_ser[k], dq_f[k], dq_t[k]

    Algebraic vars:
      i_cap_f[k], i_cap_t[k]  capacitor currents
      If[k], It[k]            terminal currents (to stamp KCL)

    DAEs (active subspace):
      (1) L di_ser + R i_ser = vf - vt
      (2) dq_f = i_cap_f
      (3) dq_t = i_cap_t
      (4) q_f = C_end vf
      (5) q_t = C_end vt
      (6) If = i_ser +  i_cap_f
      (7) It = -i_ser +  i_cap_t
    """

    def __init__(self,
                 vf: VarFactory,
                 line: Line,
                 sbase: float,
                 fbase: float,
                 name: str = ""):
        super().__init__(name=name or f"emt_pi_{line.name}")
        self.tpe = DeviceType.LineDevice
        self.name = name

        c0 = vf.add_const(0.0)

        # -----------------------------
        # 0) Phase mask from the line itself [N,A,B,C]
        # -----------------------------
        ph_mask = np.array([
            bool(line.ys.phN),
            bool(line.ys.phA),
            bool(line.ys.phB),
            bool(line.ys.phC),
        ], dtype=bool)


        ph_labels = ["N", "A", "B", "C"]
        idx = np.where(ph_mask)[0]              # indices in [0..3]
        active_ph = [ph_labels[i] for i in idx] # names in canonical order
        m = len(active_ph)

        if m == 0:
            raise ValueError(f"PI line '{line.name}' has no enabled phases in line.ys")

        # -----------------------------
        # 1) Create ONLY active terminal voltage input vars
        #    (Connection to buses is done by the assembler, not here.)
        # -----------------------------
        vf_vars = [vf.add_var(f"vf_{ph}_{line.name}") for ph in active_ph]
        vt_vars = [vf.add_var(f"vt_{ph}_{line.name}") for ph in active_ph]
        d_vf_vars = [vf.add_diff_var(name=f"d_vf_{ph}_{line.name}", base_var=v_base) for ph, v_base in zip(active_ph, vf_vars)]
        d_vt_vars = [vf.add_diff_var(name=f"d_vt_{ph}_{line.name}", base_var=v_base) for ph, v_base in zip(active_ph, vt_vars)]

        # -----------------------------
        # 2) Compute continuous parameters in pu (R, L, G_end, C_end) in ACTIVE subspace
        # -----------------------------
        w0 = 2.0 * np.pi * float(fbase)

        Vbase = line.bus_from.Vnom * 1e3
        S = float(sbase) * 1e6
        Zbase = (Vbase * Vbase) / S
        Ybase = 1.0 / Zbase

        # per-meter matrices to lumped over length
        # Z_phys = (line.template.z_nabc / 1e3) * line.length
        # Y_phys = (line.template.y_nabc / 1e3) * line.length
        Z_phys = line.template.z_nabc * line.length
        Y_phys = line.template.y_nabc * line.length

        # pu conversion
        Z_pu = Z_phys / Zbase
        Y_pu = Y_phys / Ybase

        R_full = np.real(Z_pu)
        X_full = np.imag(Z_pu)
        L_full = X_full / (w0 + 1e-20)

        Gsh_full = np.real(Y_pu)
        Bsh_full = np.imag(Y_pu)
        C_full = Bsh_full / (w0 + 1e-20)

        G_end_full = 0.5 * Gsh_full
        C_end_full = 0.5 * C_full

        # print(f"Rfull = {R_full}")
        # print(f"Xfull = {X_full}")
        # print(f"Lfull = {L_full}")
        # print(f"Cfull = {C_full}")

        idx_global = idx
        n_mat = R_full.shape[0]

        if n_mat == 3:
            # Matrices are ABC only
            if 0 in idx_global:
                raise ValueError(
                    f"Line '{line.name}' has N phase enabled but template matrices are 3x3 (ABC)."
                )
            idx_mat = idx_global - 1  # A->0, B->1, C->2
        elif n_mat == 4:
            # Matrices are NABC
            idx_mat = idx_global
        else:
            raise ValueError(
                f"Unsupported template matrix size {n_mat} for line '{line.name}' (expected 3 or 4)."
            )

        R = R_full[np.ix_(idx_mat, idx_mat)]
        L = L_full[np.ix_(idx_mat, idx_mat)]
        G_end = G_end_full[np.ix_(idx_mat, idx_mat)]
        C_end = C_end_full[np.ix_(idx_mat, idx_mat)]

        # -----------------------------
        # 3) Create model vars
        # -----------------------------
        i_ser = [vf.add_var(f"i_ser_{line.name}_{k}") for k in range(m)]
        q_f   = [vf.add_var(f"q_f_{line.name}_{k}")   for k in range(m)]
        q_t   = [vf.add_var(f"q_t_{line.name}_{k}")   for k in range(m)]

        di_ser = [vf.add_diff_var(name=f"di_ser_{line.name}_{k}", base_var=i_ser[k]) for k in range(m)]
        dq_f   = [vf.add_diff_var(name=f"dq_f_{line.name}_{k}", base_var=q_f[k])   for k in range(m)]
        dq_t   = [vf.add_diff_var(name=f"dq_t_{line.name}_{k}", base_var=q_t[k])   for k in range(m)]

        i_cap_f = [vf.add_var(f"i_cap_f_{line.name}_{k}") for k in range(m)]
        i_cap_t = [vf.add_var(f"i_cap_t_{line.name}_{k}") for k in range(m)]
        if_act  = [vf.add_var(f"if_{line.name}_{k}")      for k in range(m)]
        it_act  = [vf.add_var(f"it_{line.name}_{k}")      for k in range(m)]

        # -----------------------------
        # 4) Build block
        # -----------------------------
        self._block = Block(name=f"PiLine_{line.name}")
        self._block.in_vars = vf_vars + vt_vars + d_vf_vars + d_vt_vars
        # self._block.in_vars = vf_vars + vt_vars
        self._block.state_vars = i_ser + q_f + q_t
        self._block.diff_vars = di_ser + dq_f + dq_t
        self._block.algebraic_vars = i_cap_f + i_cap_t + if_act + it_act

        # -----------------------------
        # 5) State equations
        # -----------------------------
        state_eqs = []
        #  L * di_ser + R * i_ser - (vf - vt) = 0
        # di_ser = L^-1 * [(vf - vt) - R * i_ser]
        L_inv = np.linalg.inv(L)

        # (1) Equations for the series branch currents (i_ser)
        for a in range(m):
            expr_rhs = c0
            for b in range(m):
                Linv_ab = float(L_inv[a, b])
                if Linv_ab != 0.0:
                    # term_b = (vf_b - vt_b) - sum_k R[b,k]*i_ser[k]
                    term_b = (vf_vars[b] - vt_vars[b])
                    for k in range(m):
                        R_bk = float(R[b, k])
                        if R_bk != 0.0:
                            term_b = term_b - R_bk * i_ser[k]
                    expr_rhs = expr_rhs + Linv_ab * term_b
            state_eqs.append(expr_rhs)

        # (2) Equations for the charge of the 'from' side capacitor (q_f)
        # Capacitor charge dynamics:
        #   dq_f = i_cap_f
        #   dq_t = i_cap_t
        for a in range(m):
            state_eqs.append(i_cap_f[a])
        for a in range(m):
            state_eqs.append(i_cap_t[a])

        self._block.state_eqs = state_eqs

        # -----------------------------
        # 6) Algebraic equations
        # -----------------------------
        alg_eqs = []

        # (4) q_f - C_end * vf = 0
        for a in range(m):
            rhs = c0
            for b in range(m):
                Cab = float(C_end[a, b])
                if Cab != 0.0:
                    rhs = rhs + Cab * vf_vars[b]
            alg_eqs.append(q_f[a] - rhs)

        # (5) q_t - C_end * vt = 0
        for a in range(m):
            rhs = c0
            for b in range(m):
                Cab = float(C_end[a, b])
                if Cab != 0.0:
                    rhs = rhs + Cab * vt_vars[b]
            alg_eqs.append(q_t[a] - rhs)

        # (6) i_cap_f - C_end * d_vf = 0
        # NOTE: d_vf_vars must be the bus diff_vars (shared), not duplicated inputs.
        for a in range(m):
            rhs = c0
            for b in range(m):
                Cab = float(C_end[a, b])
                if Cab != 0.0:
                    rhs = rhs + Cab * d_vf_vars[b]
            alg_eqs.append(i_cap_f[a] - rhs)
        # (7) i_cap_t - C_end * d_vt = 0
        for a in range(m):
            rhs = c0
            for b in range(m):
                Cab = float(C_end[a, b])
                if Cab != 0.0:
                    rhs = rhs + Cab * d_vt_vars[b]
            alg_eqs.append(i_cap_t[a] - rhs)

        # (8) Terminal current at from-bus:
        # if = i_ser + i_cap_f
        for a in range(m):
            gv = c0
            alg_eqs.append(if_act[a] - (i_ser[a] + gv + i_cap_f[a]))

        # (9) Terminal current at to-bus:
        # it = -i_ser + i_cap_t
        for a in range(m):
            gv = c0
            alg_eqs.append(it_act[a] - (-i_ser[a] + gv + i_cap_t[a]))

        self._block.algebraic_eqs = alg_eqs

        # outputs
        self._block.out_vars = if_act + it_act

        # -----------------------------
        # 7) external mapping for KCL stamping in EmtProblemDae
        # -----------------------------
        if_keys = {
            "N": VarPowerFlowRefferenceType.if_N,
            "A": VarPowerFlowRefferenceType.if_A,
            "B": VarPowerFlowRefferenceType.if_B,
            "C": VarPowerFlowRefferenceType.if_C,
        }
        it_keys = {
            "N": VarPowerFlowRefferenceType.it_N,
            "A": VarPowerFlowRefferenceType.it_A,
            "B": VarPowerFlowRefferenceType.it_B,
            "C": VarPowerFlowRefferenceType.it_C,
        }
        Sf_keys = {
            "A": VarPowerFlowRefferenceType.Sf_A,
            "B": VarPowerFlowRefferenceType.Sf_B,
            "C": VarPowerFlowRefferenceType.Sf_C,
        }
        St_keys = {
            "A": VarPowerFlowRefferenceType.St_A,
            "B": VarPowerFlowRefferenceType.St_B,
            "C": VarPowerFlowRefferenceType.St_C,
        }

        # Start with all phases present as None
        mapping: Dict[VarPowerFlowRefferenceType, Var|None] = {
            if_keys["N"]: None, if_keys["A"]: None, if_keys["B"]: None, if_keys["C"]: None,
            it_keys["N"]: None, it_keys["A"]: None, it_keys["B"]: None, it_keys["C"]: None,
            Sf_keys["A"]: None, Sf_keys["B"]: None, Sf_keys["C"]: None,
            St_keys["A"]: None, St_keys["B"]: None, St_keys["C"]: None,
        }

        # Fill only active phases
        for k, ph in enumerate(active_ph):
            mapping[if_keys[ph]] = if_act[k]
            mapping[it_keys[ph]] = it_act[k]

        self._block.external_mapping = mapping

        # -----------------------------
        # 8) init equations (ALL internal vars)
        # -----------------------------
        init_eqs: Dict[Var, Expr] = {}

        # q_f = C_end * vf
        for a in range(m):
            rhs = c0
            for b in range(m):
                Cab = float(C_end[a, b])
                if Cab != 0.0:
                    rhs = rhs + Cab * vf_vars[b]
            init_eqs[q_f[a]] = rhs

        # q_t = C_end * vt
        for a in range(m):
            rhs = c0
            for b in range(m):
                Cab = float(C_end[a, b])
                if Cab != 0.0:
                    rhs = rhs + Cab * vt_vars[b]
            init_eqs[q_t[a]] = rhs

        # i_cap seeds
        for a in range(m): # INCORRECT ASSUMPTION FOR EMT IN abc DOMAIN
            init_eqs[i_cap_f[a]] = c0
            init_eqs[i_cap_t[a]] = c0

        # # i_cap_f = C_end * d_vf
        # for a in range(m):
        #     rhs = c0
        #     for b in range(m):
        #         Cab = float(C_end[a, b])
        #         if Cab != 0.0:
        #             rhs = rhs + Cab * d_vf_vars[b]
        #     init_eqs[i_cap_f[a]] = rhs
        #
        # # i_cap_t = C_end * d_vt
        # for a in range(m):
        #     rhs = c0
        #     for b in range(m):
        #         Cab = float(C_end[a, b])
        #         if Cab != 0.0:
        #             rhs = rhs + Cab * d_vt_vars[b]
        #     init_eqs[i_cap_t[a]] = rhs

        # i_ser seed using KLC
        for a in range(m):
            init_eqs[i_ser[a]] = if_act[a] - i_cap_f[a]

        self._block.init_eqs = init_eqs

        # -----------------------------
        # 9) Derivative initialization (diff_init_eqs)
        # -----------------------------
        diff_init_eqs: Dict[Var, Expr] = {}
        Linv_numeric = np.linalg.inv(L)

        for a in range(m):
            di_expression = c0
            for b in range(m):
                term_b = (vf_vars[b] - vt_vars[b])
                for k in range(m):
                    R_bk = float(R[b, k])
                    if R_bk != 0.0:
                        term_b = term_b - R_bk * i_ser[k]
                coeff = float(Linv_numeric[a, b])
                if abs(coeff) > 1e-15:
                    di_expression = di_expression + coeff * term_b

            diff_init_eqs[di_ser[a]] = di_expression

            # (B) dq_f = i_cap_f y dq_t = i_cap_t
            # diff_init_eqs[dq_f[a]] = i_cap_f[a]
            # diff_init_eqs[dq_t[a]] = i_cap_t[a]

        # For trapezoidal start-up stability:
        # - Set dq_f, dq_t to 0 as an initial guess.
        # - They will be reconciled by Newton via state_eqs (dq = i_cap) and algebraic (i_cap = C*d_v).
        for a in range(m):
            diff_init_eqs[dq_f[a]] = c0
            diff_init_eqs[dq_t[a]] = c0

        self._block.diff_init_eqs = diff_init_eqs

def get_pi_line_emt_template(grid: MultiCircuit,
                             line: Line,
                             name: str = "") -> EmtModelTemplate:

    templ = PiLineEmtTemplate(vf = grid.var_factory,
                              line= line,
                              sbase = grid.Sbase,
                              fbase = grid.fBase,
                              name = name)

    return templ