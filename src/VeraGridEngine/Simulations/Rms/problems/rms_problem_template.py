# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from abc import ABC
from typing import List, Dict
import numpy as np
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.Simulations.driver_template import DummySignal


class RmsProblemTemplate(ABC):

    def __init__(self,
                 progress_signal: DummySignal | None = None,
                 progress_text: DummySignal | None = None,):

        self._is_initialized = False
        self.progress_signal =  DummySignal() if progress_signal is None else progress_signal
        self.progress_text = DummySignal(str) if progress_text is None else progress_text

    def set_initialize_flag(self):
        self._is_initialized = True

    def is_initialized(self) -> bool:
        return self._is_initialized

    def get_vars_info(self) -> Dict[ALL_DEV_TYPES, List[Var]]:
        raise NotImplementedError("get_device_vars_dict")

    def get_all_vars_number(self) -> int:
        return 0

    def get_diff_var_number(self) -> int:
        return 0

    def get_algebraic_var_number(self) -> int:
        return 0

    def get_states_number(self) -> int:
        return 0

    def get_variable_parameter_number(self) -> int:
        return 0

    def get_algebraic_vars(self) -> List:
        return list()

    def get_state_vars(self):
        return list()

    # def get_constant_parameters(self) -> Vec:
    #     raise NotImplementedError("get_constant_parameters")

    def get_x0(self) -> Vec:
        raise NotImplementedError("get_x0")

    # def compute_event_params(self, parameters: Vec, time_value: float) -> Vec:
    #     raise NotImplementedError("compute_event_params")

    def update_variable_params(self, t: float):
        raise NotImplementedError("update_variable_params")

    def get_dx(self, x: Vec, xn: Vec, dx: Vec, h: float) -> Vec:
        raise NotImplementedError("derivative")

    def rhs_state(self, x: Vec, dx: Vec) -> Vec:
        raise NotImplementedError("rhs_state")

    def rhs_algebraic(self, values: Vec, diff_values: Vec) -> Vec:
        raise NotImplementedError("rhs_algebraic")

    def get_j11(self, x: Vec, dx: Vec, h: float):
        raise NotImplementedError("get_j11")

    def get_j12(self, x: Vec, dx: Vec, h: float):
        raise NotImplementedError("get_j12")

    def get_j21(self, x: Vec, dx: Vec, h: float):
        raise NotImplementedError("get_j21")

    def get_j22(self, x: Vec, dx: Vec, h: float):
        raise NotImplementedError("get_j22")

    def get_E_matrix(self, x:Vec, dx:Vec):
        raise NotImplementedError("get_E_matrix")

    def get_dt(self):
        return NotImplementedError("get_dt")

    def get_dt_value(self):
        return NotImplementedError("get_dt_value")

    def report_progress(self, val: float):
        """
        Report progress
        :param val: float value
        """
        self.progress_signal.emit(val)

    def report_progress2(self, current: int, total: int):
        """
        Report progress
        :param current: current value (zero based)
        :param total: total value
        """
        if self.progress_signal is not None:
            val = ((current + 1) / total) * 100
            self.progress_signal.emit(val)

    def report_text(self, val: str):
        """
        Report text
        :param val: text value
        """
        self.progress_text.emit(val)
