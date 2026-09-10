# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import math

from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingPoint
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBlockGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBounds
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingConnectionGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingSegmentObstacle


class RoutingSpatialIndex:
    """Index immutable routing obstacles in uniform non-Qt spatial cells.

    The index only reduces the candidate set. Constraint predicates remain
    responsible for exact intersection decisions.

    :param connection_geometry: Immutable obstacle snapshot to index.
    :param cell_size: Width and height of every spatial bucket.
    :return: None.
    """

    __slots__ = ("_cell_size", "_blocks_by_cell", "_segments_by_cell")

    def __init__(
            self,
            connection_geometry: RoutingConnectionGeometry,
            cell_size: float = 256.0,
    ) -> None:
        """Build one temporary spatial lookup from routing-core geometry.

        :param connection_geometry: Immutable obstacle snapshot to index.
        :param cell_size: Width and height of every spatial bucket.
        :return: None.
        """
        self._cell_size: float = max(float(cell_size), 1.0)
        self._blocks_by_cell: dict[tuple[int, int], list[RoutingBlockGeometry]] = dict()
        self._segments_by_cell: dict[tuple[int, int], list[RoutingSegmentObstacle]] = dict()

        block_geometry: RoutingBlockGeometry
        for block_geometry in connection_geometry.get_other_blocks():
            self._insert_block(block_geometry=block_geometry)

        # Endpoint owners also participate in central-route searches. They are
        # indexed once here and later excluded by the constraint engine only
        # when the active segment legitimately belongs to their own port.
        source_owner: RoutingBlockGeometry | None = connection_geometry.get_source_owner()
        destination_owner: RoutingBlockGeometry | None = connection_geometry.get_destination_owner()
        if source_owner is not None:
            self._insert_block(block_geometry=source_owner)
        else:
            pass
        if destination_owner is not None and destination_owner is not source_owner:
            self._insert_block(block_geometry=destination_owner)
        else:
            pass

        segment_obstacle: RoutingSegmentObstacle
        for segment_obstacle in connection_geometry.get_other_connection_segments():
            self._insert_segment(segment_obstacle=segment_obstacle)

    def query_blocks(
            self,
            start_position: RoutingPoint,
            end_position: RoutingPoint,
    ) -> tuple[RoutingBlockGeometry, ...]:
        """Return foreign blocks in cells touched by a segment bounding box.

        :param start_position: First candidate-segment endpoint.
        :param end_position: Second candidate-segment endpoint.
        :return: Deduplicated candidate block geometries.
        """
        candidates_by_uid: dict[int, RoutingBlockGeometry] = dict()
        cell_key: tuple[int, int]
        for cell_key in self._build_cell_keys_for_points(
                start_position=start_position,
                end_position=end_position,
        ):
            cell_blocks: list[RoutingBlockGeometry] | None = self._blocks_by_cell.get(cell_key, None)
            if cell_blocks is not None:
                block_geometry: RoutingBlockGeometry
                for block_geometry in cell_blocks:
                    candidates_by_uid[block_geometry.get_block_uid()] = block_geometry
            else:
                pass
        return tuple(candidates_by_uid.values())

    def query_segments(
            self,
            start_position: RoutingPoint,
            end_position: RoutingPoint,
    ) -> tuple[RoutingSegmentObstacle, ...]:
        """Return foreign segments in cells touched by a segment bounding box.

        :param start_position: First candidate-segment endpoint.
        :param end_position: Second candidate-segment endpoint.
        :return: Deduplicated candidate segment obstacles.
        """
        candidates_by_identifier: dict[tuple[int, int], RoutingSegmentObstacle] = dict()
        cell_key: tuple[int, int]
        for cell_key in self._build_cell_keys_for_points(
                start_position=start_position,
                end_position=end_position,
        ):
            cell_segments: list[RoutingSegmentObstacle] | None = self._segments_by_cell.get(cell_key, None)
            if cell_segments is not None:
                segment_obstacle: RoutingSegmentObstacle
                for segment_obstacle in cell_segments:
                    obstacle_identifier: tuple[int, int] = (
                        segment_obstacle.get_connection_uid(),
                        segment_obstacle.get_segment_id(),
                    )
                    candidates_by_identifier[obstacle_identifier] = segment_obstacle
            else:
                pass
        return tuple(candidates_by_identifier.values())

    def _insert_block(self, block_geometry: RoutingBlockGeometry) -> None:
        """Insert one block into every cell touched by its bounds.

        :param block_geometry: Foreign block to index.
        :return: None.
        """
        block_bounds: RoutingBounds = block_geometry.get_bounds()
        cell_key: tuple[int, int]
        for cell_key in self._build_cell_keys(
                minimum_x=block_bounds.get_left(),
                maximum_x=block_bounds.get_right(),
                minimum_y=block_bounds.get_top(),
                maximum_y=block_bounds.get_bottom(),
        ):
            cell_blocks: list[RoutingBlockGeometry] | None = self._blocks_by_cell.get(cell_key, None)
            if cell_blocks is None:
                cell_blocks = list()
                self._blocks_by_cell[cell_key] = cell_blocks
            else:
                pass
            cell_blocks.append(block_geometry)

    def _insert_segment(self, segment_obstacle: RoutingSegmentObstacle) -> None:
        """Insert one foreign segment into every cell touched by its bounds.

        :param segment_obstacle: Foreign segment to index.
        :return: None.
        """
        start_position: RoutingPoint = segment_obstacle.get_start_position()
        end_position: RoutingPoint = segment_obstacle.get_end_position()
        cell_key: tuple[int, int]
        for cell_key in self._build_cell_keys_for_points(
                start_position=start_position,
                end_position=end_position,
        ):
            cell_segments: list[RoutingSegmentObstacle] | None = self._segments_by_cell.get(cell_key, None)
            if cell_segments is None:
                cell_segments = list()
                self._segments_by_cell[cell_key] = cell_segments
            else:
                pass
            cell_segments.append(segment_obstacle)

    def _build_cell_keys_for_points(
            self,
            start_position: RoutingPoint,
            end_position: RoutingPoint,
    ) -> tuple[tuple[int, int], ...]:
        """Return cells touched by the bounding box of two points.

        :param start_position: First bounding-box point.
        :param end_position: Second bounding-box point.
        :return: Immutable spatial-cell keys.
        """
        return self._build_cell_keys(
            minimum_x=min(start_position.get_x(), end_position.get_x()),
            maximum_x=max(start_position.get_x(), end_position.get_x()),
            minimum_y=min(start_position.get_y(), end_position.get_y()),
            maximum_y=max(start_position.get_y(), end_position.get_y()),
        )

    def _build_cell_keys(
            self,
            minimum_x: float,
            maximum_x: float,
            minimum_y: float,
            maximum_y: float,
    ) -> tuple[tuple[int, int], ...]:
        """Return every spatial cell overlapped by normalized bounds.

        :param minimum_x: Left geometry coordinate.
        :param maximum_x: Right geometry coordinate.
        :param minimum_y: Top geometry coordinate.
        :param maximum_y: Bottom geometry coordinate.
        :return: Immutable spatial-cell keys.
        """
        minimum_cell_x: int = math.floor(minimum_x / self._cell_size)
        maximum_cell_x: int = math.floor(maximum_x / self._cell_size)
        minimum_cell_y: int = math.floor(minimum_y / self._cell_size)
        maximum_cell_y: int = math.floor(maximum_y / self._cell_size)
        cell_keys: list[tuple[int, int]] = list()
        cell_x: int
        cell_y: int
        for cell_x in range(minimum_cell_x, maximum_cell_x + 1):
            for cell_y in range(minimum_cell_y, maximum_cell_y + 1):
                cell_keys.append((cell_x, cell_y))
        return tuple(cell_keys)
