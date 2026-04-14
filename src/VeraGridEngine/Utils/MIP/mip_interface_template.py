# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
This module abstracts the synthax of PuLP out
so that in the future it can be exchanged with some
other solver interface easily
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, List, Tuple, Union
from VeraGridEngine.enumerations import MIPSolvers
from VeraGridEngine.basic_structures import Logger


class AbstractLpModel(ABC):
    """
    Abstract base class for LP/MIP models.
    """
    __slots__ = (
        "name",
        "solver_type",
        "logger",
        "relaxed_slacks",
        "originally_infeasible",
    )

    OPTIMAL: Any
    INFINITY: float = 1e20

    def __init__(self, solver_type: MIPSolvers, name: str):
        self.name = name
        self.solver_type = solver_type
        self.logger = Logger()
        self.relaxed_slacks: List[Tuple[int, Any, float]] = []
        self.originally_infeasible: bool = False

    # --- Abstract interface methods -------------------------------------------

    @staticmethod
    @abstractmethod
    def set_var_bounds(var: Any, lb: float, ub: float):
        """Modify variable bounds."""

    @abstractmethod
    def add_int(self, lb: int, ub: int, name: str = "") -> Any:
        """Add an integer variable."""

    @abstractmethod
    def add_var(self, lb: float, ub: float, name: str = "") -> Any:
        """Add a continuous variable."""

    @abstractmethod
    def add_bin(self, name: str = "") -> Any:
        """ add binary variable. """

    @abstractmethod
    def add_cst(self, cst: Any, name: str = "") -> Any:
        """Add a constraint."""

    @staticmethod
    @abstractmethod
    def sum(exprs: Iterable) -> Any:
        """Sum of expressions."""

    @abstractmethod
    def minimize(self, obj_function: Any):
        """Define minimization objective."""

    @abstractmethod
    def solve(self, robust: bool = False, show_logs: bool = False,
              progress_text: Callable[[str], None] | None = None) -> int:
        """Solve the optimization problem."""

    @abstractmethod
    def fobj_value(self) -> float:
        """Get the objective value."""

    @staticmethod
    @abstractmethod
    def get_value(x: Any) -> float:
        """Return the numerical value of a variable/expression."""

    @staticmethod
    @abstractmethod
    def get_dual_value(x: Any) -> float:
        """Return the dual value of a constraint."""

    @abstractmethod
    def status2string(self, stat: Any) -> str:
        """Convert solver status to readable string."""

    # --- Optional helper methods ---------------------------------------------

    @abstractmethod
    def save_model(self, file_name: str):
        """Export the model to LP/MPS for debugging."""

    @abstractmethod
    def is_mip(self) -> bool:
        """Return True if model has integer variables."""

    @abstractmethod
    def model_as_string(self) -> str:
        """Return model string representation (LP)"""