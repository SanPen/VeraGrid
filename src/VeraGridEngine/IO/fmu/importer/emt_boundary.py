# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

import numpy as np

from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.IO.fmu.importer.co_simulation import FmuCsDeviceAdapter
from VeraGridEngine.IO.fmu.importer.model_exchange import EmtFmuMeDeviceAdapter
from VeraGridEngine.IO.fmu.importer.errors import FmuModeError
from VeraGridEngine.IO.fmu.importer.runtime_profile import FmuMeEvaluationBudget


class CompositeEmtBoundaryUpdater:
    """Compose VeraGrid EMT boundary updates with imported FMU CS and ME devices.

    :param problem: Owning EMT problem.
    :param cs_adapters: Imported FMU CS device adapters.
    :param me_adapters: Imported FMU ME device adapters.
    """

    __slots__ = (
        "problem",
        "cs_adapters",
        "me_adapters",
        "initialized",
        "me_evaluation_budget",
    )

    def __init__(self, problem: Any, cs_adapters: list[FmuCsDeviceAdapter], me_adapters: list[EmtFmuMeDeviceAdapter]) -> None:
        """Store the EMT boundary updater wrapper.

        :return: None.
        """

        self.problem: Any = problem
        self.cs_adapters: list[FmuCsDeviceAdapter] = cs_adapters
        self.me_adapters: list[EmtFmuMeDeviceAdapter] = me_adapters
        self.initialized: bool = False
        self.me_evaluation_budget: FmuMeEvaluationBudget | None = None

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

    def _initialize_me_adapters(
        self,
        time_value: float,
        x_snapshot: np.ndarray,
        full_params: np.ndarray,
        evaluation_budget: FmuMeEvaluationBudget,
    ) -> None:
        """Initialize all FMU ME adapters on the first EMT boundary update.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :param full_params: Runtime-parameter vector.
        :return: None.
        """

        adapter: EmtFmuMeDeviceAdapter
        for adapter in self.me_adapters:
            outputs = adapter.initialize_outputs(
                time_value,
                x_snapshot,
                evaluation_budget=evaluation_budget,
            )
            adapter.apply_outputs(full_params, outputs)

    def _advance_me_adapters(
        self,
        time_value: float,
        x_snapshot: np.ndarray,
        full_params: np.ndarray,
        evaluation_budget: FmuMeEvaluationBudget,
    ) -> None:
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
                outputs = adapter.advance(
                    current_time=adapter.last_time,
                    step_size=step_size,
                    x_snapshot=x_snapshot,
                    evaluation_budget=evaluation_budget,
                )
            else:
                outputs = dict(adapter.last_outputs)
            adapter.apply_outputs(full_params, outputs)

    def update(
        self,
        time_value: float,
        x_snapshot: np.ndarray,
        full_params: np.ndarray,
    ) -> float | None:
        """Execute the native EMT boundary update and then advance imported FMUs.

        :param time_value: Current simulation time.
        :param x_snapshot: Current accepted state snapshot.
        :param full_params: Runtime-parameter vector.
        :return: Localized ME retry time before CS advances, or ``None``.
        """

        self.problem.emt_boundary_update(time_value, x_snapshot, full_params)
        if self.initialized:
            evaluation_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(
                self.problem.options.fmi_me_max_runtime_evaluations_per_step
            )
            self.me_evaluation_budget = evaluation_budget
            self._advance_me_adapters(
                time_value,
                x_snapshot,
                full_params,
                evaluation_budget=evaluation_budget,
            )
            retry_time: float | None = self._prepare_me_state_event_retry(
                full_params
            )
            if retry_time is None:
                self._advance_cs_adapters(time_value, x_snapshot, full_params)
            else:
                pass
        else:
            initialization_budget: FmuMeEvaluationBudget = FmuMeEvaluationBudget(
                self.problem.options.fmi_me_max_runtime_evaluations_per_step
            )
            self._initialize_cs_adapters(time_value, x_snapshot, full_params)
            self._initialize_me_adapters(
                time_value,
                x_snapshot,
                full_params,
                evaluation_budget=initialization_budget,
            )
            self.initialized = True
            retry_time = None
        return retry_time

    def _prepare_me_state_event_retry(
        self,
        params: np.ndarray,
    ) -> float | None:
        """Localize the global first ME event before any CS device advances.

        :param params: Runtime-parameter vector receiving restored ME outputs.
        :return: Global shortened target time, or ``None``.
        """

        adapter_count: int = len(self.me_adapters)
        evaluation_budget: FmuMeEvaluationBudget | None = (
            self.me_evaluation_budget
        )
        if evaluation_budget is not None:
            pass
        else:
            raise FmuModeError("EMT FMI ME localization lost its evaluation budget")
        localized_times: list[float | None] = [None] * adapter_count
        earliest_event_time: float | None = None
        adapter_index: int
        for adapter_index in range(adapter_count):
            adapter: EmtFmuMeDeviceAdapter = self.me_adapters[adapter_index]
            localized_time: float | None = (
                adapter.runtime_adapter.get_pending_state_event_time(
                    time_tolerance=(
                        self.problem.options.fmi_state_event_time_tolerance
                    ),
                    maximum_iterations=(
                        self.problem.options.fmi_state_event_max_iterations
                    ),
                    evaluation_budget=evaluation_budget,
                )
            )
            localized_times[adapter_index] = localized_time
            if (
                localized_time is not None
                and (
                    earliest_event_time is None
                    or localized_time < earliest_event_time
                )
            ):
                earliest_event_time = localized_time
            else:
                pass

        if earliest_event_time is not None:
            # Roll every ME device back to the common accepted system point.
            for adapter_index in range(adapter_count):
                adapter = self.me_adapters[adapter_index]
                adapter_event_time: float | None = localized_times[adapter_index]
                source_is_simultaneous: bool = (
                    adapter_event_time is not None
                    and (adapter_event_time - earliest_event_time)
                    <= self.problem.options.fmi_state_event_time_tolerance
                )
                if source_is_simultaneous:
                    retry_event_time: float | None = earliest_event_time
                else:
                    retry_event_time = None
                restored_values: tuple[float, ...] = (
                    adapter.runtime_adapter.prepare_state_event_retry(
                        event_time=retry_event_time,
                        evaluation_budget=evaluation_budget,
                    )
                )
                restored_outputs: dict[VarPowerFlowReferenceType, float] = (
                    adapter.runtime_adapter._map_bound_output_values(
                        restored_values
                    )
                )
                if adapter.pending_previous_time is not None:
                    adapter.last_time = adapter.pending_previous_time
                else:
                    pass
                adapter.pending_previous_time = None
                adapter.last_outputs = dict(restored_outputs)
                adapter.apply_outputs(params, restored_outputs)
        else:
            pass
        return earliest_event_time

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> float | None:
        """Forward the next forced event query to the native EMT problem.

        :param t_prev: Previous accepted time.
        :param t_target: Candidate target time.
        :return: Next forced event time if any.
        """

        next_event_time: float | None = self.problem.get_next_forced_event_time(
            t_prev=t_prev,
            t_target=t_target,
        )
        adapter: EmtFmuMeDeviceAdapter
        for adapter in self.me_adapters:
            adapter_event_time: float | None = (
                adapter.runtime_adapter.get_next_event_time()
            )
            if (
                adapter_event_time is not None
                and t_prev < adapter_event_time <= t_target
            ):
                if (
                    next_event_time is None
                    or adapter_event_time < next_event_time
                ):
                    next_event_time = adapter_event_time
                else:
                    pass
            else:
                pass
        return next_event_time

    def resolve_step(
        self,
        accepted: bool,
        params: np.ndarray,
    ) -> float | None:
        """Accept or reject every prepared ME candidate after EMT Newton.

        :param accepted: Whether the EMT numerical step converged.
        :param params: Runtime-parameter vector receiving resolved outputs.
        :return: Always ``None`` because localization precedes Co-Simulation.
        """

        evaluation_budget: FmuMeEvaluationBudget | None = (
            self.me_evaluation_budget
        )
        pending_me_step_exists: bool = False
        pending_adapter: EmtFmuMeDeviceAdapter
        for pending_adapter in self.me_adapters:
            if pending_adapter.pending_previous_time is not None:
                pending_me_step_exists = True
            else:
                pass
        if pending_me_step_exists:
            pass
        else:
            # Some EMT backends resolve their initial t0 boundary callback even
            # though initialization did not prepare an ME candidate. A same-time
            # update can likewise allocate an unused budget. Both are no-ops.
            self.me_evaluation_budget = None
            return None
        if evaluation_budget is not None:
            pass
        else:
            raise FmuModeError("EMT FMI ME step lost its evaluation budget")
        adapter: EmtFmuMeDeviceAdapter
        for adapter in self.me_adapters:
            outputs: dict[VarPowerFlowReferenceType, float] = (
                adapter.resolve_step(
                    accepted=accepted,
                    evaluation_budget=evaluation_budget,
                )
            )
            adapter.apply_outputs(params, outputs)
        self.me_evaluation_budget = None
        return None

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
