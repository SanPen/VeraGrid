# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Shared physical balance and detached-voltage row layout for FullVec RMS."""

from typing import Dict, List

import numpy as np

from VeraGridEngine.basic_structures import ObjVec, Vec
from VeraGridEngine.enumerations import RmsVectorizedNodalBalanceKind


class RmsVectorizedNodalBalanceLayout:
    """Keep symbolic row order and runtime residual evaluation synchronized."""

    __slots__ = ("_kinds", "_bus_indices", "_local_power_variable_uids",
                 "_fixed_voltage_variable_uids", "_fixed_voltage_initial_values")

    def __init__(self) -> None:
        """Initialize construction-time row metadata.

        :return: None.
        """
        self._kinds: List[RmsVectorizedNodalBalanceKind] = list()
        self._bus_indices: List[int] = list()
        self._local_power_variable_uids: List[int | None] = list()
        self._fixed_voltage_variable_uids: List[int | None] = list()
        self._fixed_voltage_initial_values: List[float] = list()

    def add_row(self, kind: RmsVectorizedNodalBalanceKind, bus_index: int,
                local_power_variable_uid: int | None,
                fixed_voltage_variable_uid: int | None = None,
                fixed_voltage_initial_value: float = 0.0) -> None:
        """Register metadata at the same time the symbolic equation is appended.

        :param kind: Residual rule for this row.
        :param bus_index: Owning physical bus index.
        :param local_power_variable_uid: Local power coordinate for a capacitive DC bus.
        :param fixed_voltage_variable_uid: Detached voltage coordinate, when applicable.
        :param fixed_voltage_initial_value: Operating-point target for that coordinate.
        :return: None.
        """
        if kind is RmsVectorizedNodalBalanceKind.CAPACITIVE_DC_POWER:
            if local_power_variable_uid is None:
                raise ValueError("Capacitive DC nodal row lacks its local power variable")
            else:
                pass
        else:
            if local_power_variable_uid is not None:
                raise ValueError("Non-capacitive nodal row cannot own a local power variable")
            else:
                pass
        if kind is RmsVectorizedNodalBalanceKind.FIXED_VOLTAGE:
            if fixed_voltage_variable_uid is None or not np.isfinite(fixed_voltage_initial_value):
                raise ValueError("Fixed-voltage nodal row lacks a coordinate or finite target")
            else:
                pass
        else:
            if fixed_voltage_variable_uid is not None:
                raise ValueError("Power-balance row cannot own a fixed voltage coordinate")
            else:
                pass
        self._kinds.append(kind)
        self._bus_indices.append(bus_index)
        self._local_power_variable_uids.append(local_power_variable_uid)
        self._fixed_voltage_variable_uids.append(fixed_voltage_variable_uid)
        self._fixed_voltage_initial_values.append(fixed_voltage_initial_value)

    def evaluate(self, variables: Vec, variable_index_by_uid: Dict[int, int],
                 active_power_balance: ObjVec, reactive_power_balance: ObjVec) -> np.ndarray:
        """Evaluate all rows in their original symbolic order.

        :param variables: Current global coordinates.
        :param variable_index_by_uid: Compiled global coordinate lookup.
        :param active_power_balance: Physical active-power accumulator.
        :param reactive_power_balance: Physical reactive-power accumulator.
        :return: Nodal and fixed-voltage residuals.
        """
        values: np.ndarray = np.empty(len(self._kinds))
        index: int
        kind: RmsVectorizedNodalBalanceKind
        for index, kind in enumerate(self._kinds):
            bus_index: int = self._bus_indices[index]
            if kind is RmsVectorizedNodalBalanceKind.ACTIVE_POWER:
                values[index] = active_power_balance[bus_index]
            elif kind is RmsVectorizedNodalBalanceKind.REACTIVE_POWER:
                values[index] = reactive_power_balance[bus_index]
            else:
                variable_uid: int | None
                offset: float
                if kind is RmsVectorizedNodalBalanceKind.CAPACITIVE_DC_POWER:
                    variable_uid = self._local_power_variable_uids[index]
                    offset = float(active_power_balance[bus_index])
                elif kind is RmsVectorizedNodalBalanceKind.FIXED_VOLTAGE:
                    variable_uid = self._fixed_voltage_variable_uids[index]
                    offset = self._fixed_voltage_initial_values[index]
                else:
                    raise ValueError("Unsupported RMS vectorized nodal balance kind")
                variable_index: int | None = (
                    variable_index_by_uid.get(variable_uid, None) if variable_uid is not None else None
                )
                if variable_index is None:
                    raise ValueError("RMS nodal row coordinate is not compiled")
                else:
                    values[index] = variables[variable_index] - offset
        return values
