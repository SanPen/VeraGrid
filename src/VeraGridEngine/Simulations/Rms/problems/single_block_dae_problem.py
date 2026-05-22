from __future__ import annotations

from typing import Callable

import numpy as np
import scipy.sparse as sp

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.compiled_functions import SymbolicDerivative, SymbolicJacobian, SymbolicVector
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var


def _unique_keep_order(vars_list: list[Var]) -> list[Var]:
    seen: set[int] = set()
    out: list[Var] = []
    for var in vars_list:
        if var.uid in seen:
            continue
        seen.add(var.uid)
        out.append(var)
    return out


class SingleBlockDaeProblem:
    """
    Generic single-block DAE problem adapter.

    This class is shaped like the problem API consumed by implicit RMS solvers,
    but focuses on one symbolic block and optional externally-driven inputs.
    """

    VARS_NAME = "vrs"
    VARIABLE_PARAMS_NAME = "vprms"
    CONSTANT_PARAMS_NAME = "cprms"
    DIFF_NAME = "diff"

    def __init__(self, block: Block):
        self.block = block
        self._promote_differential_eqs_to_algebraic_all_blocks()
        self.block.unify_blocks()

        self._state_vars = list(self.block.state_vars)
        self._algebraic_vars = list(self.block.algebraic_vars)
        self._diff_vars = list(self.block.diff_vars)
        self._state_eqs = list(self.block.state_eqs)
        self._algebraic_eqs = list(self.block.algebraic_eqs)

        self._all_vars = _unique_keep_order(self._state_vars + self._algebraic_vars)
        self.uid2idx_vars = {v.uid: i for i, v in enumerate(self._all_vars)}
        self._uid2idx_diff = {v.uid: i for i, v in enumerate(self._diff_vars)}

        self._compiler_names_dict: dict[int, str] = {}
        self._alias_names_dict: dict[int, str] = {}
        for uid, i in self.uid2idx_vars.items():
            self._compiler_names_dict[uid] = f"{self.VARS_NAME}[{i}]"
            self._alias_names_dict[uid] = f"{self.VARS_NAME}_{i}"
        for uid, i in self._uid2idx_diff.items():
            self._compiler_names_dict[uid] = f"{self.DIFF_NAME}[{i}]"
            self._alias_names_dict[uid] = f"{self.DIFF_NAME}_{i}"

        self._input_var_by_name: dict[str, Var] = {}
        self._input_param_by_name: dict[str, Var] = {}
        self._input_profile_by_name: dict[str, Callable[[float], float] | float] = {}

        self._variable_parameters: list[Var] = []
        self._variable_parameters_eqs: list[Expr | Const] = []
        self._variable_parameters_values = np.zeros(0, dtype=float)
        self._constant_params = np.zeros(0, dtype=float)

        self._collect_block_runtime_parameters()
        self._wire_in_vars_as_runtime_inputs()
        self._compile_rhs_and_jacobian()

        self.init_guess: dict[int, float] = {}
        self._populate_init_guess()
        self._x0 = self._build_x0_from_init_data()

    def _collect_block_runtime_parameters(self) -> None:
        for var, eq in self.block.event_dict.items():
            if not isinstance(var, Var):
                continue
            self._variable_parameters.append(var)
            self._variable_parameters_eqs.append(eq)

    def _promote_differential_eqs_to_algebraic_all_blocks(self) -> None:
        for blk in self.block.get_all_blocks():
            if len(blk.differential_eqs):
                blk.algebraic_eqs.extend(blk.differential_eqs)

    def _wire_in_vars_as_runtime_inputs(self) -> None:
        for in_var in list(self.block.in_vars):
            if in_var.uid not in self.uid2idx_vars:
                self._algebraic_vars.append(in_var)
                self._all_vars.append(in_var)
                self.uid2idx_vars[in_var.uid] = len(self._all_vars) - 1
                self._compiler_names_dict[in_var.uid] = f"{self.VARS_NAME}[{self.uid2idx_vars[in_var.uid]}]"
                self._alias_names_dict[in_var.uid] = f"{self.VARS_NAME}_{self.uid2idx_vars[in_var.uid]}"

            inp_name = in_var.name
            runtime_param = Var(f"input_{inp_name}")
            self._input_var_by_name[inp_name] = in_var
            self._input_param_by_name[inp_name] = runtime_param
            self._input_profile_by_name[inp_name] = 0.0

            self._variable_parameters.append(runtime_param)
            self._variable_parameters_eqs.append(Const(0.0))
            self._algebraic_eqs.append(in_var - runtime_param)

        self._algebraic_vars = _unique_keep_order(self._algebraic_vars)
        self._all_vars = _unique_keep_order(self._state_vars + self._algebraic_vars)
        self.uid2idx_vars = {v.uid: i for i, v in enumerate(self._all_vars)}

        self._variable_parameters_values = np.zeros(len(self._variable_parameters), dtype=float)

    def _compile_rhs_and_jacobian(self) -> None:
        all_eqs = self._state_eqs + self._algebraic_eqs

        self._rhs_fn = SymbolicVector(
            all_eqs,
            self._compiler_names_dict,
            self._alias_names_dict,
            self.VARS_NAME,
            self.DIFF_NAME,
            self.VARIABLE_PARAMS_NAME,
            self.CONSTANT_PARAMS_NAME,
            use_jit=True,
        ) if len(all_eqs) else None

        self._jacobian_fn = SymbolicJacobian(
            eqs=all_eqs,
            variables=self._all_vars,
            compiler_names_dict=self._compiler_names_dict,
            alias_names_dict=self._alias_names_dict,
            VARS_NAME=self.VARS_NAME,
            DIFF_NAME=self.DIFF_NAME,
            EVENT_PARAMS_NAME=self.VARIABLE_PARAMS_NAME,
            PARAMS_NAME=self.CONSTANT_PARAMS_NAME,
            use_jit=True,
        ) if len(all_eqs) else None

        self._derivative_fn = SymbolicDerivative(
            vars=self._all_vars,
            uid2idx_vars=self.uid2idx_vars,
            diff_vars=self._diff_vars,
            compiler_names_dict=self._compiler_names_dict,
            use_jit=True,
        )

    def _populate_init_guess(self) -> None:
        for var, value in self.block.init_values.items():
            if isinstance(var, Var) and var.uid in self.uid2idx_vars:
                self.init_guess[var.uid] = float(value.value if isinstance(value, Const) else value)

        uid_bindings: dict[int, float] = dict(self.init_guess)
        pending = list(self.block.init_eqs.items())
        for _ in range(30):
            changed = False
            next_pending: list[tuple[Var, Expr | Const | float]] = []
            for var, expr in pending:
                if not isinstance(var, Var) or var.uid not in self.uid2idx_vars:
                    continue
                try:
                    if isinstance(expr, Const):
                        val = 0.0 if expr.value is None else float(expr.value)
                    elif isinstance(expr, Expr):
                        val = float(expr.eval_uid(uid_bindings))
                    else:
                        val = float(expr)
                    self.init_guess[var.uid] = val
                    uid_bindings[var.uid] = val
                    changed = True
                except Exception:
                    next_pending.append((var, expr))
            pending = next_pending
            if not changed:
                break

        for var in self._all_vars:
            self.init_guess.setdefault(var.uid, 0.0)

    def _build_x0_from_init_data(self) -> np.ndarray:
        x0 = np.zeros(len(self._all_vars), dtype=float)
        for var in self._all_vars:
            x0[self.uid2idx_vars[var.uid]] = float(self.init_guess.get(var.uid, 0.0))
        return x0

    def bind_input_constant(self, input_name: str, value: float) -> None:
        if input_name not in self._input_profile_by_name:
            raise KeyError(f"Unknown input '{input_name}'. Available: {sorted(self._input_profile_by_name.keys())}")
        self._input_profile_by_name[input_name] = float(value)

    def bind_input_profile(self, input_name: str, profile: Callable[[float], float]) -> None:
        if input_name not in self._input_profile_by_name:
            raise KeyError(f"Unknown input '{input_name}'. Available: {sorted(self._input_profile_by_name.keys())}")
        self._input_profile_by_name[input_name] = profile

    def list_inputs(self) -> list[str]:
        return sorted(self._input_profile_by_name.keys())

    def get_all_vars_number(self) -> int:
        return len(self._all_vars)

    def get_states_number(self) -> int:
        return len(self._state_vars)

    def get_algebraic_var_number(self) -> int:
        return len(self._algebraic_vars)

    def get_diff_var_number(self) -> int:
        return len(self._diff_vars)

    @property
    def algebraic_vars(self):
        return self._algebraic_vars

    @property
    def _algebraic_vars_(self):
        return self._algebraic_vars

    def get_x0(self) -> np.ndarray:
        return self._x0.copy()

    def update_variable_params_ts(self, x_snapshot: np.ndarray, t: float) -> None:
        self.update_variable_params(t=t, x_snapshot=x_snapshot)

    def update_variable_params(self, t: float, x_snapshot: np.ndarray | None = None) -> None:
        _ = x_snapshot
        for i, param in enumerate(self._variable_parameters):
            if i < len(self._variable_parameters_eqs):
                expr = self._variable_parameters_eqs[i]
            else:
                expr = Const(0.0)

            if param.name.startswith("input_"):
                input_name = param.name.replace("input_", "", 1)
                profile = self._input_profile_by_name[input_name]
                self._variable_parameters_values[i] = float(profile(t) if callable(profile) else profile)
            elif isinstance(expr, Const):
                self._variable_parameters_values[i] = float(0.0 if expr.value is None else expr.value)
            elif isinstance(expr, Expr):
                try:
                    self._variable_parameters_values[i] = float(expr.eval_uid(dict()))
                except Exception:
                    self._variable_parameters_values[i] = 0.0
            else:
                self._variable_parameters_values[i] = float(expr)

    def rhs_algebraic(self, x: np.ndarray, dx: np.ndarray) -> np.ndarray:
        if self._rhs_fn is None:
            return np.array([])
        full = self._rhs_fn(x, dx, self._variable_parameters_values, self._constant_params)
        ns = self.get_states_number()
        return full[ns:]

    def rhs_state(self, x: np.ndarray, dx: np.ndarray) -> np.ndarray:
        if self._rhs_fn is None or self.get_states_number() == 0:
            return np.array([])
        full = self._rhs_fn(x, dx, self._variable_parameters_values, self._constant_params)
        ns = self.get_states_number()
        return full[:ns]

    def get_dx(self, x: np.ndarray, xn: np.ndarray, dx: np.ndarray, h: float) -> np.ndarray:
        return self._derivative_fn(x, xn, dx, h)

    def _jac_full(self, x: np.ndarray, dx: np.ndarray, h: float) -> sp.csc_matrix:
        if self._jacobian_fn is None:
            return sp.csc_matrix((0, 0))
        return self._jacobian_fn(x, dx, self._variable_parameters_values, self._constant_params, h).tocsc()

    def get_j11(self, x: np.ndarray, dx: np.ndarray, h: float) -> sp.csc_matrix:
        ns = self.get_states_number()
        if ns == 0:
            return sp.csc_matrix((0, 0))
        J = self._jac_full(x, dx, h)
        return J[:ns, :ns]

    def get_j12(self, x: np.ndarray, dx: np.ndarray, h: float) -> sp.csc_matrix:
        ns = self.get_states_number()
        na = self.get_algebraic_var_number()
        if ns == 0:
            return sp.csc_matrix((0, na))
        J = self._jac_full(x, dx, h)
        return J[:ns, ns:ns + na]

    def get_j21(self, x: np.ndarray, dx: np.ndarray, h: float) -> sp.csc_matrix:
        ns = self.get_states_number()
        na = self.get_algebraic_var_number()
        if na == 0:
            return sp.csc_matrix((0, ns))
        J = self._jac_full(x, dx, h)
        return J[ns:ns + na, :ns]

    def get_j22(self, x: np.ndarray, dx: np.ndarray, h: float) -> sp.csc_matrix:
        ns = self.get_states_number()
        na = self.get_algebraic_var_number()
        if na == 0:
            return sp.csc_matrix((0, 0))
        J = self._jac_full(x, dx, h)
        return J[ns:ns + na, ns:ns + na]

    def get_var_idx(self, v: Var) -> int:
        return self.uid2idx_vars[v.uid]

    def report_progress2(self, step_idx: int, steps: int) -> None:
        _ = (step_idx, steps)

    def update(self, t: float, x_snapshot: np.ndarray, event_values: np.ndarray) -> None:
        _ = (t, x_snapshot, event_values)

    def get_next_forced_event_time(self, t_prev: float, t_target: float):
        _ = (t_prev, t_target)
        return None

    def initialize_fmu_cs_devices(self, x0: np.ndarray, t0: float) -> None:
        _ = (x0, t0)

    def initialize_fmu_me_devices(self, x0: np.ndarray, t0: float) -> None:
        _ = (x0, t0)

    def advance_fmu_cs_devices(self, t: float, x_snapshot: np.ndarray, h: float) -> None:
        _ = (t, x_snapshot, h)

    def advance_fmu_me_devices(self, t: float, x_snapshot: np.ndarray, h: float) -> None:
        _ = (t, x_snapshot, h)

    def close_fmu_cs_devices(self) -> None:
        return None

    def close_fmu_me_devices(self) -> None:
        return None
