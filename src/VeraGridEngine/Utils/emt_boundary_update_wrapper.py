from __future__ import annotations

from typing import Optional, Tuple

from VeraGridEngine.basic_structures import Vec


class BoundaryUpdateWrapper:
    """
    Lightweight interface for EMT boundary updates and forced events.

    The class lives in ``VeraGridEngine.Utils`` so EMT templates, procedural logic
    and solver modules can import it statically without pulling one heavy solver or
    simulation package ``__init__`` into the import graph.
    """

    __slots__ = list()

    def update(self, t: float, x: Vec, params: Vec) -> None:
        """
        Update the runtime parameter vector in place.

        :param t: Current solver time.
        :param x: Accepted state vector.
        :param params: Runtime parameter vector.
        :return: None.
        """
        _unused: Tuple[BoundaryUpdateWrapper, float, Vec, Vec] = (self, t, x, params)
        return None

    def get_next_forced_event_time(self, t_prev: float, t_target: float) -> Optional[float]:
        """
        Return the earliest forced event time in ``(t_prev, t_target]``.

        :param t_prev: Previous solver time.
        :param t_target: Nominal target time.
        :return: Forced event time or ``None``.
        """
        _unused: Tuple[BoundaryUpdateWrapper, float, float] = (self, t_prev, t_target)
        return None
