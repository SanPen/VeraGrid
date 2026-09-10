# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingPoint


class RoutingBounds:
    """
    Store one normalized axis-aligned rectangle in routing coordinates.

    This core representation deliberately contains no Qt types. Presentation
    adapters can therefore capture live scene bounds once and pass plain
    geometry to the routing engine without reversing the Core/Qt dependency.

    :param left: Left rectangle coordinate.
    :param top: Top rectangle coordinate.
    :param right: Right rectangle coordinate.
    :param bottom: Bottom rectangle coordinate.
    :return: None.
    """

    __slots__ = ("_left", "_top", "_right", "_bottom")

    def __init__(self, left: float, top: float, right: float, bottom: float) -> None:
        """
        Build one rectangle while normalizing both coordinate axes.

        :param left: First horizontal rectangle coordinate.
        :param top: First vertical rectangle coordinate.
        :param right: Second horizontal rectangle coordinate.
        :param bottom: Second vertical rectangle coordinate.
        :return: None.
        """
        first_x: float = float(left)
        first_y: float = float(top)
        second_x: float = float(right)
        second_y: float = float(bottom)

        # Bounds are normalized at the Qt boundary so every later geometric
        # predicate can operate without caring about scene transform direction.
        self._left: float = min(first_x, second_x)
        self._top: float = min(first_y, second_y)
        self._right: float = max(first_x, second_x)
        self._bottom: float = max(first_y, second_y)

    def get_left(self) -> float:
        """
        Return the left rectangle coordinate.

        :return: Left coordinate.
        """
        return self._left

    def get_top(self) -> float:
        """
        Return the top rectangle coordinate.

        :return: Top coordinate.
        """
        return self._top

    def get_right(self) -> float:
        """
        Return the right rectangle coordinate.

        :return: Right coordinate.
        """
        return self._right

    def get_bottom(self) -> float:
        """
        Return the bottom rectangle coordinate.

        :return: Bottom coordinate.
        """
        return self._bottom


class RoutingBlockGeometry:
    """
    Associate one stable scene-block identifier with its routing bounds.

    The identifier is metadata for exclusions and ownership decisions. The
    routing constraint engine only consumes the accompanying non-Qt bounds.

    :param block_uid: Stable identifier of the represented block item.
    :param bounds: Axis-aligned block bounds in routing coordinates.
    :return: None.
    """

    __slots__ = ("_block_uid", "_bounds")

    def __init__(self, block_uid: int, bounds: RoutingBounds) -> None:
        """
        Build one identified block geometry value.

        :param block_uid: Stable identifier of the represented block item.
        :param bounds: Axis-aligned block bounds in routing coordinates.
        :return: None.
        """
        self._block_uid: int = int(block_uid)
        self._bounds: RoutingBounds = bounds

    def get_block_uid(self) -> int:
        """
        Return the stable block identifier.

        :return: Stable block identifier.
        """
        return self._block_uid

    def get_bounds(self) -> RoutingBounds:
        """
        Return the captured block bounds.

        :return: Axis-aligned block bounds.
        """
        return self._bounds


class RoutingSegmentObstacle:
    """
    Store one segment belonging to another routed connection.

    The obstacle contains only routing-core values. Connection and segment
    identifiers preserve provenance for diagnostics and future filtering while
    endpoint copies freeze the geometry at snapshot time.

    :param connection_uid: Stable identifier of the owning connection.
    :param segment_id: Stable segment identifier within that connection graph.
    :param start_position: First segment endpoint.
    :param end_position: Second segment endpoint.
    :return: None.
    """

    __slots__ = ("_connection_uid", "_segment_id", "_start_position", "_end_position")

    def __init__(
            self,
            connection_uid: int,
            segment_id: int,
            start_position: RoutingPoint,
            end_position: RoutingPoint,
    ) -> None:
        """
        Build one immutable point-in-time segment obstacle.

        :param connection_uid: Stable identifier of the owning connection.
        :param segment_id: Stable segment identifier within that connection graph.
        :param start_position: First segment endpoint.
        :param end_position: Second segment endpoint.
        :return: None.
        """
        self._connection_uid: int = int(connection_uid)
        self._segment_id: int = int(segment_id)
        self._start_position: RoutingPoint = start_position.copy()
        self._end_position: RoutingPoint = end_position.copy()

    def get_connection_uid(self) -> int:
        """
        Return the obstacle's owning connection identifier.

        :return: Stable connection identifier.
        """
        return self._connection_uid

    def get_segment_id(self) -> int:
        """
        Return the segment identifier within its owning graph.

        :return: Stable segment identifier.
        """
        return self._segment_id

    def get_start_position(self) -> RoutingPoint:
        """
        Return a detached copy of the first endpoint.

        :return: First endpoint copy.
        """
        return self._start_position.copy()

    def get_end_position(self) -> RoutingPoint:
        """
        Return a detached copy of the second endpoint.

        :return: Second endpoint copy.
        """
        return self._end_position.copy()


class RoutingSceneGeometrySnapshot:
    """Store one immutable capture of every routing obstacle in a scene.

    :param blocks: Every visible block captured from the Qt scene.
    :param connection_segments: Every segment from registered routing graphs.
    :return: None.
    """

    __slots__ = ("_blocks", "_connection_segments")

    def __init__(
            self,
            blocks: tuple[RoutingBlockGeometry, ...],
            connection_segments: tuple[RoutingSegmentObstacle, ...],
    ) -> None:
        """Build one immutable scene-level routing snapshot.

        :param blocks: Every visible block captured from the Qt scene.
        :param connection_segments: Every registered connection segment.
        :return: None.
        """
        self._blocks: tuple[RoutingBlockGeometry, ...] = tuple(blocks)
        self._connection_segments: tuple[RoutingSegmentObstacle, ...] = tuple(connection_segments)

    def get_blocks(self) -> tuple[RoutingBlockGeometry, ...]:
        """Return all captured block geometries.

        :return: Immutable block sequence.
        """
        return self._blocks

    def get_connection_segments(self) -> tuple[RoutingSegmentObstacle, ...]:
        """Return all captured connection segments.

        :return: Immutable segment-obstacle sequence.
        """
        return self._connection_segments


class RoutingConnectionGeometry:
    """
    Store the immutable block geometry relevant to one routed connection.

    Endpoint owners are deliberately separate from unrelated scene blocks.
    A port segment is allowed to touch its owning block at the port boundary,
    while every unrelated block is a full obstacle for every route segment.
    Keeping those categories separate prevents future collision checks from
    applying the stricter foreign-obstacle policy to an endpoint owner.

    :param source_owner: Geometry of the source port owner when available.
    :param destination_owner: Geometry of the destination port owner when available.
    :param other_blocks: Geometry of every unrelated block obstacle.
    :param other_connection_segments: Segments belonging to other routing graphs.
    :return: None.
    """

    __slots__ = (
        "_source_owner",
        "_destination_owner",
        "_other_blocks",
        "_other_connection_segments",
    )

    def __init__(
            self,
            source_owner: RoutingBlockGeometry | None,
            destination_owner: RoutingBlockGeometry | None,
            other_blocks: tuple[RoutingBlockGeometry, ...],
            other_connection_segments: tuple[RoutingSegmentObstacle, ...] = tuple(),
    ) -> None:
        """
        Build one point-in-time connection geometry snapshot.

        :param source_owner: Geometry of the source port owner when available.
        :param destination_owner: Geometry of the destination port owner when available.
        :param other_blocks: Geometry of every unrelated block obstacle.
        :param other_connection_segments: Segments belonging to other routing graphs.
        :return: None.
        """
        self._source_owner: RoutingBlockGeometry | None = source_owner
        self._destination_owner: RoutingBlockGeometry | None = destination_owner
        self._other_blocks: tuple[RoutingBlockGeometry, ...] = tuple(other_blocks)
        self._other_connection_segments: tuple[RoutingSegmentObstacle, ...] = tuple(
            other_connection_segments,
        )

    def get_source_owner(self) -> RoutingBlockGeometry | None:
        """
        Return the source endpoint owner geometry.

        :return: Source owner geometry or ``None``.
        """
        return self._source_owner

    def get_destination_owner(self) -> RoutingBlockGeometry | None:
        """
        Return the destination endpoint owner geometry.

        :return: Destination owner geometry or ``None``.
        """
        return self._destination_owner

    def get_other_blocks(self) -> tuple[RoutingBlockGeometry, ...]:
        """
        Return the unrelated block obstacles captured for the connection.

        :return: Immutable sequence of unrelated block geometry.
        """
        return self._other_blocks

    def get_other_connection_segments(self) -> tuple[RoutingSegmentObstacle, ...]:
        """
        Return the segments captured from other connection graphs.

        :return: Immutable sequence of foreign connection segments.
        """
        return self._other_connection_segments
