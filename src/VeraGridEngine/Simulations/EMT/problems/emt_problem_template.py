# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from abc import ABC
import numpy as np
from typing import Dict, List,Optional

from VeraGridEngine.Utils.Symbolic.symbolic import Const
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Any
from VeraGridEngine.basic_structures import Vec


class EmtProblemTemplate(ABC):
    """
    Intermediate layer that manages DAE plumbing including indexing, variable mapping,
    and event updating, regardless of whether the system comes from an electrical
    circuit or a generic mathematical model.
    """

    VARS_NAME = "vars"
    VARIABLE_PARAMS_NAME = "vprms"
    CONSTANT_PARAMS_NAME = "cprms"
    DIFF_NAME = "diff"
    TIME_NAME = "glob_time"

    def __init__(self, sys_block: Block, glob_time: Var):
        """
        Initializes the BaseProblem with a root system block and global time variable.
        """
        super().__init__()
        self.sys_block = sys_block
        self._glob_time = glob_time
        self._newton_trace_collector = None

        self._state_vars = self.sys_block.state_vars
        self._algebraic_vars = self.sys_block.algebraic_vars
        self._state_eqs = self.sys_block.state_eqs
        self._algebraic_eqs = self.sys_block.algebraic_eqs
        self._diff_vars = self.sys_block.diff_vars

        self._constant_parameters = list(self.sys_block.parameters.keys())
        self._parameters_values = list(self.sys_block.parameters.values())

        self._variable_parameters = []
        self._event_parameters_eqs = []
        if self.sys_block.event_dict:
            self._variable_parameters = list(self.sys_block.event_dict.keys())
            self._event_parameters_eqs = list(self.sys_block.event_dict.values())

        self.init_guess: Dict[int, float] = dict()
        self.diff_init_guess: Dict[int, float] = dict()

        self._finalize_order_and_maps()
        self._build_runtime_param_vectors()

    @property
    def glob_time(self) -> Var:
        return self._glob_time

    def _finalize_order_and_maps(self):
        """
        Builds canonical ordering, index maps, and internal counters.
        """

        self._diff_vars = sorted(self._diff_vars, key=lambda dv: dv.diff_order)

        self._n_state = len(self._state_vars)
        self._n_alg = len(self._algebraic_vars)
        self._n_vars = self._n_state + self._n_alg
        self._n_event_params = len(self._variable_parameters)
        self._n_params = len(self._constant_parameters)
        self._n_diff = len(self._diff_vars)
        self._n_algebraic = len(self._algebraic_eqs)

        self._compiler_names_dict = {}
        self._alias_names_dict = {}
        self._uid2idx_vars = {}
        self._uid2idx_event_params = {}
        self._uid2idx_params = {}
        self._uid2idx_diff = {}
        self._uid2idx_t = {}

        i = 0
        for v in self._state_vars:
            self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{i}]"
            self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{i}"
            self._uid2idx_vars[v.uid] = i
            i += 1

        for v in self._algebraic_vars:
            self._compiler_names_dict[v.uid] = f"{self.VARS_NAME}[{i}]"
            self._alias_names_dict[v.uid] = f"{self.VARS_NAME}_{i}"
            self._uid2idx_vars[v.uid] = i
            i += 1

        for j, p in enumerate(self._constant_parameters):
            self._compiler_names_dict[p.uid] = f"{self.CONSTANT_PARAMS_NAME}[{j}]"
            self._alias_names_dict[p.uid] = f"{self.CONSTANT_PARAMS_NAME}_{j}"
            self._uid2idx_params[p.uid] = j

        for k, p in enumerate(self._variable_parameters):
            self._compiler_names_dict[p.uid] = f"{self.VARIABLE_PARAMS_NAME}[{k}]"
            self._alias_names_dict[p.uid] = f"{self.VARIABLE_PARAMS_NAME}_{k}"
            self._uid2idx_event_params[p.uid] = k

        for k, d in enumerate(self._diff_vars):
            self._compiler_names_dict[d.uid] = f"{self.DIFF_NAME}[{k}]"
            self._alias_names_dict[d.uid] = f"{self.DIFF_NAME}_{k}"
            self._uid2idx_diff[d.uid] = k

        self._compiler_names_dict[self._glob_time.uid] = self.TIME_NAME
        self._uid2idx_t[self._glob_time.uid] = 0

    def _build_runtime_param_vectors(self):
        """
        Builds and initializes runtime vectors for event and constant parameters.
        """
        self._event_params_fn = self._build_event_params_fn()

        self._event_params_values = np.ones(self.get_variable_parameter_number(), dtype=np.float64)
        if self.get_variable_parameter_number() > 0:
            self._event_params_values = self._event_params_fn(self._event_params_values, 0.0)
            self._event_params_values = self._event_params_fn(self._event_params_values, 0.0)

        self._constant_params_values = np.array([c.value for c in self._parameters_values], dtype=np.float64)

    def _build_event_params_fn(self):
        """
        Builds the event parameter update function to evaluate expressions at runtime.
        """
        eqs = list(self._event_parameters_eqs)
        n = len(eqs)

        if n == 0:
            def _evt_update(event_params: np.ndarray, t: float) -> np.ndarray:
                return event_params

            return _evt_update

        uid2idx_event = dict(self._uid2idx_event_params)
        uid2idx_const = dict(self._uid2idx_params)
        time_uid = self._glob_time.uid
        const_vals = np.array([c.value for c in self._parameters_values], dtype=np.float64)

        def _eval_expr(expr, ev: np.ndarray, tm: float):
            if isinstance(expr, Const):
                return float(expr.value)

            if isinstance(expr, Var):
                if expr.uid == time_uid:
                    return float(tm)
                if expr.uid in uid2idx_event:
                    return float(ev[uid2idx_event[expr.uid]])
                if expr.uid in uid2idx_const:
                    return float(const_vals[uid2idx_const[expr.uid]])
                raise KeyError(f"Unknown variable uid={expr.uid} in event expression.")

            if hasattr(expr, "eval"):
                local_map = {}
                for uid, idx in uid2idx_event.items():
                    local_map[uid] = float(ev[idx])
                for uid, idx in uid2idx_const.items():
                    local_map[uid] = float(const_vals[idx])
                local_map[time_uid] = float(tm)
                return float(expr.eval(local_map))

            if hasattr(expr, "args"):
                raise TypeError("Expression type is not directly evaluable and has no eval() implementation.")

            return float(expr)

        def _evt_update(event_params: np.ndarray, t: float) -> np.ndarray:
            out = np.empty(n, dtype=np.float64)
            for i, eq in enumerate(eqs):
                out[i] = _eval_expr(eq, event_params, t)
            return out

        return _evt_update

    def get_state_vars(self):
        """
        Returns the list of state variables.
        """
        return self._state_vars

    def get_algebraic_vars(self):
        """
        Returns the list of algebraic variables.
        """
        return self._algebraic_vars

    def get_state_eqs(self):
        """
        Returns the list of state equations.
        """
        return self._state_eqs

    def get_algebraic_eqs(self):
        """
        Returns the list of algebraic equations.
        """
        return self._algebraic_eqs

    def get_variable_parameters(self):
        """
        Returns the list of variable parameters.
        """
        return self._variable_parameters

    def get_constant_parameters(self):
        """
        Returns the list of constant parameters.
        """
        return self._constant_parameters

    def get_diff_vars(self):
        """

        Returns the list of derivatives.

        """
        return self._diff_vars

    def get_parameters_values(self):
        """
        Returns the list of constant parameter values.
        """
        return self._parameters_values

    def get_all_vars_number(self) -> int:
        """
        Returns the total number of variables.
        """
        return self._n_vars

    def get_diff_var_number(self) -> int:
        """
        Returns the number of differential variables.
        """
        return self._n_diff

    def get_algebraic_var_number(self) -> int:
        """
        Returns the number of algebraic variables.
        """
        return self._n_alg

    def get_states_number(self) -> int:
        """
        Returns the number of state variables.
        """
        return self._n_state

    def get_variable_parameter_number(self) -> int:
        """
        Returns the number of variable parameters.
        """
        return self._n_event_params

    def get_x0(self) -> Vec:
        """
        Builds and returns the initial condition vector based on the initialization guess.
        """
        x = np.zeros(self._n_vars, dtype=np.float64)
        for uid, val in self.init_guess.items():
            idx = self._uid2idx_vars.get(uid, None)
            if idx is not None:
                x[idx] = float(val)

        return x

    def get_dx0(self) -> Vec:
        """
        Builds and returns the initial condition vector based on the initialization guess.
        """
        dx = np.zeros(self._n_diff, dtype=np.float64)
        for uid, val in self.diff_init_guess.items():
            idx = self._uid2idx_diff.get(uid, None)
            if idx is not None:
                dx[idx] = float(val)
        return dx

    def def_event_params_fn(self, ev_param: Vec, tm: float) -> Vec:
        """
        Solver-facing event update callback.
        """
        return self._event_params_fn(ev_param, tm)

    def update_variable_params(self, t: float):
        """
        Updates the internal event parameter values at the given time.
        """
        self._event_params_values = self._event_params_fn(self._event_params_values, float(t))

    def get_full_param_index(self, uid: int) -> int:
        n_ev = len(self._variable_parameters)
        if uid in self._uid2idx_event_params:
            return self._uid2idx_event_params[uid]
        if uid in self._uid2idx_params:
            return n_ev + self._uid2idx_params[uid]
        raise KeyError(f"Unknown param uid={uid}")

    def get_newton_trace_collector(self) -> Any:
        """
        Returns the Newton trace collector instance.
        """
        return self._newton_trace_collector

    def set_newton_trace_collector(self, collector: Any):
        """
        Sets the Newton trace collector instance.
        """
        self._newton_trace_collector = collector

    def get_device_vars_dict(self) -> Dict[Any, List[Var]]:
        """
        Returns the device variable mapping dictionary.
        """
        return getattr(self, '_vars_info', {})

    def get_var_idx(self, v: Var) -> int:
        """
        Returns the index of a specific variable.
        """
        return self._uid2idx_vars[v.uid]

    def get_diff_var_idx(self, dv: Var) -> int:
        """
        Returns the index of a specific derivative of a variable.
        """
        return self._uid2idx_diff[dv.uid]

    def set_init_guess(self, mdl: Block, reference_powerflow: Any, val: float):
        if not hasattr(mdl, "external_mapping") or mdl.external_mapping is None:
            return
        if reference_powerflow in mdl.external_mapping:
            var = mdl.external_mapping[reference_powerflow]
            if var is None:
                return
            self.init_guess[var.uid] = float(val)

    def get_floquet_ak_stack(self, trajectory: np.ndarray, h: float, jac_evaluator=None, static_params=None) -> \
            Optional[np.ndarray]:
        """
        Calculates the stack of transition matrices A_k for Floquet analysis...
        """
        return None

    @property
    def uid2idx_vars(self):
        return self._uid2idx_vars

    @property
    def uid2idx_params(self):
        return self._uid2idx_params

    @property
    def uid2idx_event_params(self):
        return self._uid2idx_event_params

    @property
    def uid2idx_diff(self):
        return self._uid2idx_diff

    @property
    def event_params_values(self):
        return self._event_params_values



