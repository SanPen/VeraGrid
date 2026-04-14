# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

import numpy as np

from VeraGridEngine.IO.fmu.importer.experimental_cs import FmuCsDeviceAdapter
from VeraGridEngine.IO.fmu.importer.experimental_me import EmtFmuMeDeviceAdapter


class CompositeEmtBoundaryUpdater:
    """Compose VeraGrid EMT boundary updates with imported FMU CS and ME devices.

    :param problem: Owning EMT problem.
    :param cs_adapters: Imported FMU CS device adapters.
    :param me_adapters: Imported FMU ME device adapters.
    """

    __slots__ = ("problem", "cs_adapters", "me_adapters", "initialized")

    def __init__(self, problem: Any, cs_adapters: list[FmuCsDeviceAdapter], me_adapters: list[EmtFmuMeDeviceAdapter]) -> None:
        """Store the EMT boundary updater wrapper.

        :return: None.
        """

        self.problem: Any = problem
        self.cs_adapters: list[FmuCsDeviceAdapter] = cs_adapters
        self.me_adapters: list[EmtFmuMeDeviceAdapter] = me_adapters
        self.initialized: bool = False

    def _initialize_cs_adapters(self, time_value: float, x_snapshot: np.ndarray, full_params: np.ndarray) -> None:
        """Initialize all FMU CS adapters on the first EMT boundary update.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :param full_params: Runtime-parameter vector.
        :return: None.
        """

        adapter: FmuCsDeviceAdapter
        for adapter in self.cs_adapters:
            outputs = adapter.initialize_outputs(time_value, x_snapshot)
            adapter.apply_outputs(full_params, outputs)

    def _advance_cs_adapters(self, time_value: float, x_snapshot: np.ndarray, full_params: np.ndarray) -> None:
        """Advance all FMU CS adapters for one EMT communication step.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :param full_params: Runtime-parameter vector.
        :return: None.
        """

        adapter: FmuCsDeviceAdapter
        for adapter in self.cs_adapters:
            step_size: float = max(float(time_value - adapter.last_time), 0.0)
            if step_size > 0.0:
                outputs = adapter.advance(current_time=adapter.last_time, step_size=step_size, x_snapshot=x_snapshot)
            else:
                outputs = adapter._read_outputs()
            adapter.apply_outputs(full_params, outputs)

    def _initialize_me_adapters(self, time_value: float, x_snapshot: np.ndarray, full_params: np.ndarray) -> None:
        """Initialize all FMU ME adapters on the first EMT boundary update.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :param full_params: Runtime-parameter vector.
        :return: None.
        """

        adapter: EmtFmuMeDeviceAdapter
        for adapter in self.me_adapters:
            outputs = adapter.initialize_outputs(time_value, x_snapshot)
            adapter.apply_outputs(full_params, outputs)

    def _advance_me_adapters(self, time_value: float, x_snapshot: np.ndarray, full_params: np.ndarray) -> None:
        """Advance all FMU ME adapters for one EMT communication step.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :param full_params: Runtime-parameter vector.
        :return: None.
        """

        adapter: EmtFmuMeDeviceAdapter
        for adapter in self.me_adapters:
            step_size: float = max(float(time_value - adapter.last_time), 0.0)
            if step_size > 0.0:
                outputs = adapter.advance(current_time=adapter.last_time, step_size=step_size, x_snapshot=x_snapshot)
            else:
                outputs = adapter.initialize_outputs(time_value, x_snapshot)
            adapter.apply_outputs(full_params, outputs)

    def update(self, time_value: float, x_snapshot: np.ndarray, full_params: np.ndarray) -> None:
        """Execute the native EMT boundary update and then advance imported FMUs.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :param full_params: Runtime-parameter vector.
        :return: None.
        """

        self.problem.emt_boundary_update(time_value, x_snapshot, full_params)
        if self.initialized:
            self._advance_cs_adapters(time_value, x_snapshot, full_params)
            self._advance_me_adapters(time_value, x_snapshot, full_params)
        else:
            self._initialize_cs_adapters(time_value, x_snapshot, full_params)
            self._initialize_me_adapters(time_value, x_snapshot, full_params)
            self.initialized = True

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> float | None:
        """Forward the next forced event query to the native EMT problem.

        :param t_prev: Previous accepted time.
        :param t_target: Candidate target time.
        :return: Next forced event time if any.
        """

        return self.problem.get_next_forced_event_time(t_prev=t_prev, t_target=t_target)

    def close(self) -> None:
        """Release all FMU runtimes owned by the boundary updater.

        :return: None.
        """

        cs_adapter: FmuCsDeviceAdapter
        for cs_adapter in self.cs_adapters:
            cs_adapter.close()
        me_adapter: EmtFmuMeDeviceAdapter
        for me_adapter in self.me_adapters:
            me_adapter.close()


def build_emt_boundary_updater(problem: Any) -> Any:
    """Build the effective EMT boundary updater for the active problem.

    :param problem: EMT problem instance.
    :return: Native EMT problem or FMU-aware boundary wrapper.
    """

    if len(problem._fmu_cs_adapters) > 0 or len(problem._fmu_me_adapters) > 0:
        return CompositeEmtBoundaryUpdater(problem, list(problem._fmu_cs_adapters), list(problem._fmu_me_adapters))
    else:
        return problem
