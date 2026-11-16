# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, Iterable, Protocol

from VeraGridEngine.basic_structures import Vec
ProceduralLogicData = Dict[str, object]

class ManufacturerNativeRuntimeSessionProtocol(Protocol):
    """Dependency-neutral driver-owned native session used by boundary logic."""

    __slots__ = ()

    def preflight(self, problem: object, logic_entries: Iterable[object], model_mode: int) -> None:
        """Resolve providers, mappings, limits and workers before native startup.

        :param problem: Numerical problem exposing compiled variable maps.
        :param logic_entries: Runtime procedural entries owned by the updater.
        :param model_mode: Exact IEEE/CIGRE EMT or RMS mode value.
        :return: None.
        """
        ...

    def initialize(self, t: float, x: Vec, params: Vec) -> None:
        """Seed held native outputs once from the complete t0 guess.

        :param t: Required zero startup time.
        :param x: Complete finite initialization state.
        :param params: Mutable runtime parameter vector.
        :return: None.
        """
        ...

    def get_next_sample_time(self, t_prev: float, t_target: float) -> float | None:
        """Return the earliest fixed native sample boundary in an interval.

        :param t_prev: Previous accepted solver time.
        :param t_target: Proposed target time.
        :return: Earliest boundary or ``None``.
        """
        ...

    def commit_boundary(self, t: float, x: Vec, params: Vec) -> None:
        """Commit due native instances after the solver accepts a boundary.

        :param t: Accepted boundary time.
        :param x: Accepted state vector.
        :param params: Mutable runtime parameters receiving held outputs.
        :return: None.
        """
        ...

    def close(self) -> None:
        """Close every worker owned by the session.

        :return: None.
        """
        ...
