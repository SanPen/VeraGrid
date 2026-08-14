# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Routing.routing_elements import RoutingPoint
from VeraGridEngine.enumerations import RoutingPortSide
from VeraGridEngine.enumerations import RoutingAxis


class RoutingGeometry:
    """
    Provide the shared geometric criteria used by the routing engine.

    The routing engine distinguishes between numerical equality and visual
    alignment. Numerical equality exists only to keep floating-point operations
    stable. Visual alignment drives every visible routing decision so that the
    builder, editor and renderer all react to the same geometry in the same
    way.

    :returns: None.
    """

    __slots__ = ("_numerical_epsilon", "_visual_alignment_threshold", "_port_stub_length")

    def __init__(self) -> None:
        """
        Build the shared routing geometry helper.

        The visual threshold is tied to the current editor port radius, which is
        6 px in ``dynamic_editor_graphics.PortItem``. Using half that radius
        gives one 3 px tolerance: differences smaller than half the visible port
        body are not visually distinguishable as misalignment to the user.

        :returns: None.
        """
        self._numerical_epsilon: float = 1.0e-9
        self._visual_alignment_threshold: float = 3.0
        self._port_stub_length: float = 20.0

    def get_numerical_epsilon(self) -> float:
        """
        Return the numerical epsilon used for internal floating-point checks.

        :returns: Numerical epsilon.
        """
        return self._numerical_epsilon

    def get_visual_alignment_threshold(self) -> float:
        """
        Return the shared visual alignment threshold.

        :returns: Visual alignment threshold in pixels.
        """
        return self._visual_alignment_threshold

    def get_port_stub_length(self) -> float:
        """
        Return the shared fixed length used for port stubs.

        :returns: Port stub length in pixels.
        """
        return self._port_stub_length

    def build_port_stub_point(
            self,
            port_position: RoutingPoint,
            port_side: RoutingPortSide,
    ) -> RoutingPoint:
        """
        Build the endpoint of one fixed-length port stub.

        The builder and the editor must use exactly the same stub geometry so
        route creation and later local port updates keep the same topology and
        the same fixed stub length.

        :param port_position: Port position.
        :param port_side: Physical side of the port.
        :returns: Stub endpoint.
        """
        if port_side == RoutingPortSide.LEFT:
            return RoutingPoint(
                port_position.get_x() - self._port_stub_length,
                port_position.get_y(),
            )
        elif port_side == RoutingPortSide.RIGHT:
            return RoutingPoint(
                port_position.get_x() + self._port_stub_length,
                port_position.get_y(),
            )
        elif port_side == RoutingPortSide.TOP:
            return RoutingPoint(
                port_position.get_x(),
                port_position.get_y() - self._port_stub_length,
            )
        else:
            return RoutingPoint(
                port_position.get_x(),
                port_position.get_y() + self._port_stub_length,
            )

    def are_x_aligned_values(self, first_x: float, second_x: float) -> bool:
        """
        Return whether two x coordinates are visually aligned.

        :param first_x: First x coordinate.
        :param second_x: Second x coordinate.
        :returns: ``True`` when both x coordinates are visually aligned.
        """
        difference: float = abs(float(first_x) - float(second_x))
        if difference <= self._visual_alignment_threshold:
            return True
        else:
            return False

    def are_y_aligned_values(self, first_y: float, second_y: float) -> bool:
        """
        Return whether two y coordinates are visually aligned.

        :param first_y: First y coordinate.
        :param second_y: Second y coordinate.
        :returns: ``True`` when both y coordinates are visually aligned.
        """
        difference: float = abs(float(first_y) - float(second_y))
        if difference <= self._visual_alignment_threshold:
            return True
        else:
            return False

    def are_x_aligned(self, first_point: RoutingPoint, second_point: RoutingPoint) -> bool:
        """
        Return whether two points are visually aligned on x.

        :param first_point: First point.
        :param second_point: Second point.
        :returns: ``True`` when both points are visually aligned on x.
        """
        return self.are_x_aligned_values(first_point.get_x(), second_point.get_x())

    def are_y_aligned(self, first_point: RoutingPoint, second_point: RoutingPoint) -> bool:
        """
        Return whether two points are visually aligned on y.

        :param first_point: First point.
        :param second_point: Second point.
        :returns: ``True`` when both points are visually aligned on y.
        """
        return self.are_y_aligned_values(first_point.get_y(), second_point.get_y())

    def are_orthogonally_aligned(self, first_point: RoutingPoint, second_point: RoutingPoint) -> bool:
        """
        Return whether two points can be joined by one orthogonal segment.

        :param first_point: First point.
        :param second_point: Second point.
        :returns: ``True`` when one horizontal or vertical segment is sufficient.
        """
        if self.are_x_aligned(first_point, second_point):
            return True
        elif self.are_y_aligned(first_point, second_point):
            return True
        else:
            return False

    def derive_axis(
            self,
            start_x: float,
            start_y: float,
            end_x: float,
            end_y: float,
    ) -> RoutingAxis | None:
        """
        Derive the visually dominant axis of one segment.

        :param start_x: Start x coordinate.
        :param start_y: Start y coordinate.
        :param end_x: End x coordinate.
        :param end_y: End y coordinate.
        :returns: Derived axis or ``None`` when the segment is not aligned.
        """
        same_x: bool = self.are_x_aligned_values(start_x, end_x)
        same_y: bool = self.are_y_aligned_values(start_y, end_y)

        if same_y and not same_x:
            return RoutingAxis.HORIZONTAL
        elif same_x and not same_y:
            return RoutingAxis.VERTICAL
        elif same_x and same_y:
            delta_x: float = abs(float(start_x) - float(end_x))
            delta_y: float = abs(float(start_y) - float(end_y))
            if delta_x <= self._numerical_epsilon and delta_y <= self._numerical_epsilon:
                return None
            elif delta_x >= delta_y:
                return RoutingAxis.HORIZONTAL
            else:
                return RoutingAxis.VERTICAL
        else:
            return None

    def are_points_numerically_equal(self, first_point: RoutingPoint, second_point: RoutingPoint) -> bool:
        """
        Return whether two points are numerically equal.

        :param first_point: First point.
        :param second_point: Second point.
        :returns: ``True`` when both coordinates match numerically.
        """
        same_x: bool = abs(first_point.get_x() - second_point.get_x()) <= self._numerical_epsilon
        same_y: bool = abs(first_point.get_y() - second_point.get_y()) <= self._numerical_epsilon
        if same_x and same_y:
            return True
        else:
            return False
