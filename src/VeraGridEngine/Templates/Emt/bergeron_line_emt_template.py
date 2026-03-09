# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
import scipy.linalg as spla

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Branches.line import Line

class BergeronLineEmtTemplate(EmtModelTemplate):
    """
    EMT Bergeron line template:
      - ONLY builds the Block stored in line.emt_model.model
      - provides event_dict with Ih history parameters
      - NO runtime state, NO update_history here
    """

    def __init__(self,
                 line: Line,
                 vf: VarFactory,
                 name: str = ""):


        super().__init__(name=name or f"emt_bergeron_{line.name}")
        self.tpe = DeviceType.LineDevice

        # History params as EVENT PARAMS (Var keys in event_dict)
        self.Ih_f = [vf.add_var(f"Ih_f_{line.name}_{i}") for i in range(4)]  # [N,A,B,C]
        self.Ih_t = [vf.add_var(f"Ih_t_{line.name}_{i}") for i in range(4)]

        event_dict = {p: vf.add_const(0.0) for p in (self.Ih_f + self.Ih_t)}

        self._block = Block(
            name=f"Bergeron_{line.name}",
            event_dict=event_dict,
        )

class BergeronHistoryRuntime:
    """
    Runtime companion for Bergeron line:
      - owns Gc, H, n_delay, buffers
      - extracts Ih Vars from the EXISTING line Block event_dict
      - binds bus terminal voltage Vars
      - produces nodal current injection expressions for KCL
      - updates Ih parameters in-place via full_params in boundary callback
    """

    def __init__(self, line,
                 line_block: Block,
                 h: float,
                 sbase: float,
                 fbase: float):

        self.line = line
        self.block = line_block
        self.h = float(h)
        self.num_phases = 4  # [N,A,B,C]

        # -------- 0) Phase mask from the LINE itself --------
        self.ph_mask = np.array([
            bool(line.ys.phN),
            bool(line.ys.phA),
            bool(line.ys.phB),
            bool(line.ys.phC),
        ], dtype=bool)
        self.phase_idx = np.where(self.ph_mask)[0]
        if self.phase_idx.size == 0:
            raise ValueError(f"Bergeron line '{line.name}' has no enabled phases in line.ys")

        # -------- 1) Extract Ih vars from block.event_dict --------
        if self.block.event_dict is None:
            raise ValueError(f"Bergeron line '{line.name}': block.event_dict is None (Ih params missing)")

        self.Ih_f = self._extract_hist_vars(prefix=f"Ih_f_{line.name}_")
        self.Ih_t = self._extract_hist_vars(prefix=f"Ih_t_{line.name}_")

        # -------- 2) Compute Gc/H in active subspace, embed into 4x4 --------
        w = 2 * np.pi * fbase

        Vbase = line.bus_from.Vnom * 1e3
        S = sbase * 1e6
        Zbase = (Vbase * Vbase) / S
        Ybase = 1.0 / Zbase

        Z_phys_m = line.template.z_nabc / 1e3
        Y_phys_m = line.template.y_nabc / 1e3
        Z_pu_m = Z_phys_m / Zbase
        Y_pu_m = Y_phys_m / Ybase

        R_full = np.real(Z_pu_m) * line.length
        L_full = np.imag(Z_pu_m) * line.length
        C_full = np.imag(Y_pu_m) * line.length

        idx = self.phase_idx
        R = R_full[np.ix_(idx, idx)]
        L = L_full[np.ix_(idx, idx)]
        C = C_full[np.ix_(idx, idx)]

        try:
            Zc = spla.sqrtm(L @ np.linalg.inv(C))
        except Exception:
            n = len(idx)
            Zc = np.eye(n) * np.sqrt(L[0, 0] / (C[0, 0] + 1e-20))

        Z_eq = np.real(Zc) + R / 4.0
        Gc_red = np.linalg.inv(Z_eq)
        H_red = (np.real(Zc) - R / 4.0) @ Gc_red

        self.Gc = np.zeros((4, 4), dtype=float)
        self.H = np.zeros((4, 4), dtype=float)
        self.Gc[np.ix_(idx, idx)] = Gc_red
        self.H[np.ix_(idx, idx)] = H_red

        tau = line.get_tau(w=w)
        self.n_delay = max(1, int(round(tau / self.h)))

        # -------- 3) Circular buffers --------
        self.buf_vf = np.zeros((self.n_delay + 1, 4), dtype=float)
        self.buf_vt = np.zeros((self.n_delay + 1, 4), dtype=float)
        self.buf_if = np.zeros((self.n_delay + 1, 4), dtype=float)
        self.buf_it = np.zeros((self.n_delay + 1, 4), dtype=float)

        # -------- 4) Will be bound by assembler --------
        self.v_f_vars = None
        self.v_t_vars = None

        # Indices for callback
        self.idx_vf = None
        self.idx_vt = None
        self.idx_p_hf = None
        self.idx_p_ht = None

    def _extract_hist_vars(self, prefix: str):
        vars_found = [
            v for v in self.block.event_dict.keys()
            if getattr(v, "name", "").startswith(prefix)
        ]
        if len(vars_found) != 4:
            raise ValueError(
                f"Expected 4 history vars with prefix '{prefix}', got {len(vars_found)}. "
                f"Check BergeronLineEmtTemplate naming."
            )
        vars_found.sort(key=lambda v: int(v.name.rsplit("_", 1)[1]))  # ..._0.._3
        return vars_found

    def bind_terminals(self, v_f_vars, v_t_vars):
        """
        v_f_vars/v_t_vars: [vN,vA,vB,vC], each element is Var or Const(0.0)
        """
        self.v_f_vars = v_f_vars
        self.v_t_vars = v_t_vars

    def get_nodal_injections(self):
        """
        Returns symbolic expressions (i_f_exprs, i_t_exprs) length=4 to be added to bus KCL.
        i_f = Gc*v_f + Ih_f ; i_t = Gc*v_t + Ih_t
        """
        if self.v_f_vars is None or self.v_t_vars is None:
            raise RuntimeError("bind_terminals(...) must be called before get_nodal_injections().")

        i_f_exprs, i_t_exprs = [], []
        for i in range(4):
            i_f = sum(self.Gc[i, j] * self.v_f_vars[j] for j in range(4)) + self.Ih_f[i]
            i_t = sum(self.Gc[i, j] * self.v_t_vars[j] for j in range(4)) + self.Ih_t[i]
            i_f_exprs.append(i_f)
            i_t_exprs.append(i_t)
        return i_f_exprs, i_t_exprs

    def setup_indices(self, uid2idx_vars: dict, uid2idx_event_params: dict, params_offset: int = 0):
        """
        Must be called AFTER BaseProblem builds uid->index maps.
        """
        self.idx_vf = [uid2idx_vars.get(v.uid, -1) if hasattr(v, "uid") else -1 for v in self.v_f_vars]
        self.idx_vt = [uid2idx_vars.get(v.uid, -1) if hasattr(v, "uid") else -1 for v in self.v_t_vars]
        self.idx_p_hf = [uid2idx_event_params[p.uid] + params_offset for p in self.Ih_f]
        self.idx_p_ht = [uid2idx_event_params[p.uid] + params_offset for p in self.Ih_t]

    def update_history(self, step_counter: int, x_prev: np.ndarray, full_params: np.ndarray):
        """
        Updates Ih_* in-place in full_params.
        Forces Ih=0 for inactive phases to avoid ghost injections.
        """
        k_curr = step_counter % (self.n_delay + 1)
        k_tau = (step_counter - self.n_delay) % (self.n_delay + 1)

        v_f_now = np.array([x_prev[i] if i >= 0 else 0.0 for i in self.idx_vf], dtype=float)
        v_t_now = np.array([x_prev[i] if i >= 0 else 0.0 for i in self.idx_vt], dtype=float)

        self.buf_vf[k_curr, :] = v_f_now
        self.buf_vt[k_curr, :] = v_t_now

        Ih_f_now = np.array([full_params[i] for i in self.idx_p_hf], dtype=float)
        Ih_t_now = np.array([full_params[i] for i in self.idx_p_ht], dtype=float)

        inactive = ~self.ph_mask
        Ih_f_now[inactive] = 0.0
        Ih_t_now[inactive] = 0.0

        self.buf_if[k_curr, :] = self.Gc @ v_f_now + Ih_f_now
        self.buf_it[k_curr, :] = self.Gc @ v_t_now + Ih_t_now

        v_f_tau = self.buf_vf[k_tau, :]
        v_t_tau = self.buf_vt[k_tau, :]
        i_f_tau = self.buf_if[k_tau, :]
        i_t_tau = self.buf_it[k_tau, :]

        X_f = -self.Gc @ v_t_tau - i_t_tau
        Y_f = -self.Gc @ v_f_tau - i_f_tau
        X_t = -self.Gc @ v_f_tau - i_f_tau
        Y_t = -self.Gc @ v_t_tau - i_t_tau

        I = np.eye(4)
        I_hist_f = 0.5 * ((I + self.H) @ X_f + (I - self.H) @ Y_f)
        I_hist_t = 0.5 * ((I + self.H) @ X_t + (I - self.H) @ Y_t)

        I_hist_f[inactive] = 0.0
        I_hist_t[inactive] = 0.0

        for i in range(4):
            full_params[self.idx_p_hf[i]] = I_hist_f[i]
            full_params[self.idx_p_ht[i]] = I_hist_t[i]

#
# class BergeronLineEmtTemplate(EmtModelTemplate):
#     """
#     Implicit Bergeron line model (DAE):
#       - Local Norton injection: i = Gc*v + I_hist
#       - I_hist is a changeable parameter (event_dict) actualized in boundary_update
#     """
#
#     def __init__(self,
#                  vf: VarFactory,
#                  line,
#                  h: float,
#                  sbase: float,
#                  fbase: float,
#                  name: str = ""):
#         super().__init__(name=name or "emt_bergeron_line_template")
#
#         self.tpe = DeviceType.LineDevice
#         self.line = line
#         self.h = float(h)
#         self.num_phases = 4  # [N, A, B, C]
#
#         # -----------------------------
#         # 0) Phase mask FROM THE LINE ITSELF
#         # -----------------------------
#         self.ph_mask = np.array([
#             bool(line.ys.phN),
#             bool(line.ys.phA),
#             bool(line.ys.phB),
#             bool(line.ys.phC),
#         ], dtype=bool)  # [N,A,B,C]
#
#         self.phase_idx = np.where(self.ph_mask)[0]
#         if self.phase_idx.size == 0:
#             raise ValueError(f"Bergeron line '{line.name}' has no enabled phases in line.ys")
#
#         # -----------------------------
#         # 1) Gc and H construction (compute in active subspace, then embed into 4x4)
#         # -----------------------------
#         w = 2 * np.pi * fbase
#
#         Vbase = line.bus_from.Vnom * 1e3
#         S = sbase * 1e6
#         Zbase = (Vbase * Vbase) / S
#         Ybase = 1.0 / Zbase
#
#         # per-meter series/shunt matrices -> pu per meter
#         Z_phys_m = line.template.z_nabc / 1e3
#         Y_phys_m = line.template.y_nabc / 1e3
#         Z_pu_m = Z_phys_m / Zbase
#         Y_pu_m = Y_phys_m / Ybase
#
#         # integrated over length (simple approximation like you had)
#         R_full = np.real(Z_pu_m) * line.length
#         L_full = np.imag(Z_pu_m) * line.length
#         C_full = np.imag(Y_pu_m) * line.length
#
#         # ---- reduce to active phases ONLY (critical) ----
#         idx = self.phase_idx
#         R = R_full[np.ix_(idx, idx)]
#         L = L_full[np.ix_(idx, idx)]
#         C = C_full[np.ix_(idx, idx)]
#
#         # Zc ~ sqrt(L * inv(C))
#         # guard against singular C
#         try:
#             Zc = spla.sqrtm(L @ np.linalg.inv(C))
#         except Exception:
#             n = len(idx)
#             # fallback diagonal approx
#             Zc = np.eye(n) * np.sqrt(L[0, 0] / (C[0, 0] + 1e-20))
#
#         Z_eq = np.real(Zc) + R / 4.0
#         Gc_red = np.linalg.inv(Z_eq)
#         H_red = (np.real(Zc) - R / 4.0) @ Gc_red
#
#         # ---- embed back into 4x4 [N,A,B,C] ----
#         self.Gc = np.zeros((4, 4), dtype=float)
#         self.H = np.zeros((4, 4), dtype=float)
#         self.Gc[np.ix_(idx, idx)] = Gc_red
#         self.H[np.ix_(idx, idx)] = H_red
#
#         tau = line.get_tau(w=w)
#         self.n_delay = max(1, int(round(tau / self.h)))
#
#         # -----------------------------
#         # 3) Circular buffers
#         # -----------------------------
#         self.buf_vf = np.zeros((self.n_delay + 1, 4), dtype=float)
#         self.buf_vt = np.zeros((self.n_delay + 1, 4), dtype=float)
#         self.buf_if = np.zeros((self.n_delay + 1, 4), dtype=float)
#         self.buf_it = np.zeros((self.n_delay + 1, 4), dtype=float)
#
#         # -----------------------------
#         # 4) History vars (EVENT PARAMS)
#         # -----------------------------
#         # IMPORTANT: these must be "event params", not DAE unknowns.
#         # If vf.add_var registers variables as unknowns, DO NOT use it here.
#         # Use Var(...) directly for event parameters.
#         self.Ih_f = [Var(f"Ih_f_{line.name}_{i}") for i in range(4)]
#         self.Ih_t = [Var(f"Ih_t_{line.name}_{i}") for i in range(4)]
#
#         event_dict = {p: Const(0.0) for p in (self.Ih_f + self.Ih_t)}
#
#         self._block = Block(
#             name=f"Bergeron_{line.name}",
#             event_dict=event_dict,
#         )
#
#         # set later by assembler
#         self.v_f_vars = None
#         self.v_t_vars = None
#
#         # indices for callback
#         self.idx_vf = None
#         self.idx_vt = None
#         self.idx_p_hf = None
#         self.idx_p_ht = None
#
#     # -------------------------------------------------------
#     # ASSEMBLY: KCL
#     # -------------------------------------------------------
#     def get_nodal_injections(self, v_f_vars, v_t_vars):
#         """
#         v_f_vars / v_t_vars: lista de longitud 4 (Vars o Const(0.0)) orden [N,A,B,C]
#         Devuelve:
#           i_f_exprs, i_t_exprs: listas length 4 con expresiones simbólicas
#         """
#         self.v_f_vars = v_f_vars
#         self.v_t_vars = v_t_vars
#
#         i_f_exprs = []
#         i_t_exprs = []
#         for i in range(4):
#             i_f = sum(self.Gc[i, j] * self.v_f_vars[j] for j in range(4)) + self.Ih_f[i]
#             i_t = sum(self.Gc[i, j] * self.v_t_vars[j] for j in range(4)) + self.Ih_t[i]
#             i_f_exprs.append(i_f)
#             i_t_exprs.append(i_t)
#
#         return i_f_exprs, i_t_exprs
#
#     # -------------------------------------------------------
#     # INDICES PARA EL CALLBACK (una vez uid2idx existe)
#     # -------------------------------------------------------
#     def setup_indices(self, uid2idx_vars: dict, uid2idx_event_params: dict, params_offset: int = 0):
#         # Vars de bus pueden ser Const -> idx = -1
#         self.idx_vf = [uid2idx_vars.get(v.uid, -1) if hasattr(v, "uid") else -1 for v in self.v_f_vars]
#         self.idx_vt = [uid2idx_vars.get(v.uid, -1) if hasattr(v, "uid") else -1 for v in self.v_t_vars]
#
#         # Ih_* están en event_params
#         self.idx_p_hf = [uid2idx_event_params[p.uid] + params_offset for p in self.Ih_f]
#         self.idx_p_ht = [uid2idx_event_params[p.uid] + params_offset for p in self.Ih_t]
#
#     # -------------------------------------------------------
#     # CALLBACK: actualizar historia en full_params
#     # -------------------------------------------------------
#     def update_history(self, step_counter: int, x_prev: np.ndarray, full_params: np.ndarray):
#         k_curr = step_counter % (self.n_delay + 1)
#         k_tau = (step_counter - self.n_delay) % (self.n_delay + 1)
#
#         v_f_now = np.array([x_prev[i] if i >= 0 else 0.0 for i in self.idx_vf], dtype=float)
#         v_t_now = np.array([x_prev[i] if i >= 0 else 0.0 for i in self.idx_vt], dtype=float)
#
#         self.buf_vf[k_curr, :] = v_f_now
#         self.buf_vt[k_curr, :] = v_t_now
#
#         # Read current Ih values from params
#         Ih_f_now = np.array([full_params[i] for i in self.idx_p_hf], dtype=float)
#         Ih_t_now = np.array([full_params[i] for i in self.idx_p_ht], dtype=float)
#
#         # FORCE Ih = 0 in inactive phases (avoid ghost injections)
#         # self.ph_mask is [N,A,B,C] bool
#         inactive = ~self.ph_mask
#         Ih_f_now[inactive] = 0.0
#         Ih_t_now[inactive] = 0.0
#
#         # currents “now” consistent with local Norton using Ih from previous step
#         self.buf_if[k_curr, :] = self.Gc @ v_f_now + Ih_f_now
#         self.buf_it[k_curr, :] = self.Gc @ v_t_now + Ih_t_now
#
#         v_f_tau = self.buf_vf[k_tau, :]
#         v_t_tau = self.buf_vt[k_tau, :]
#         i_f_tau = self.buf_if[k_tau, :]
#         i_t_tau = self.buf_it[k_tau, :]
#
#         # Lossy Bergeron (H-form)
#         X_f = -self.Gc @ v_t_tau - i_t_tau
#         Y_f = -self.Gc @ v_f_tau - i_f_tau
#         X_t = -self.Gc @ v_f_tau - i_f_tau
#         Y_t = -self.Gc @ v_t_tau - i_t_tau
#
#         I = np.eye(4)
#         I_hist_f = 0.5 * ((I + self.H) @ X_f + (I - self.H) @ Y_f)
#         I_hist_t = 0.5 * ((I + self.H) @ X_t + (I - self.H) @ Y_t)
#
#         # FORCE computed history to 0 for inactive phases too
#         I_hist_f[inactive] = 0.0
#         I_hist_t[inactive] = 0.0
#
#         for i in range(4):
#             full_params[self.idx_p_hf[i]] = I_hist_f[i]
#             full_params[self.idx_p_ht[i]] = I_hist_t[i]