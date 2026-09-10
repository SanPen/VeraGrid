# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtWidgets import QGraphicsScene

from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBlockGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBounds
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingConnectionGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingSegmentObstacle
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingSceneGeometrySnapshot
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import BlockItem
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import GenericBlockItem
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import MeasurementsItem
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import PairedItem
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import PortItem
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import RectBaseArithmeticOpItem
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import RoundBaseArithmeticOpItem


class QtRoutingSceneGeometryAdapter:
    """
    Capture live Qt block geometry as one immutable routing-core snapshot.

    This adapter is the only layer that understands both graphics items and
    routing geometry. The produced snapshot contains no Qt objects, allowing
    the constraint engine to remain independent from the presentation layer.

    :return: None.
    """

    __slots__ = tuple()

    def capture_scene_geometry(
            self,
            scene: QGraphicsScene | None,
            connection_segments: tuple[RoutingSegmentObstacle, ...],
    ) -> RoutingSceneGeometrySnapshot:
        """Capture every reusable routing obstacle from one Qt scene traversal.

        :param scene: Live graphics scene, if available.
        :param connection_segments: Segments from all registered routing graphs.
        :return: Immutable scene-level geometry snapshot.
        """
        blocks: list[RoutingBlockGeometry] = list()
        if scene is not None:
            scene_item: QGraphicsItem
            for scene_item in scene.items():
                block_geometry: RoutingBlockGeometry | None = self._build_block_geometry(scene_item=scene_item)
                if block_geometry is not None:
                    blocks.append(block_geometry)
                else:
                    pass
        else:
            pass

        return RoutingSceneGeometrySnapshot(
            blocks=tuple(blocks),
            connection_segments=connection_segments,
        )

    def build_connection_geometry_from_snapshot(
            self,
            snapshot: RoutingSceneGeometrySnapshot,
            source_port: PortItem,
            destination_port: PortItem,
            connection_uid: int,
    ) -> RoutingConnectionGeometry:
        """Classify one shared scene snapshot for a specific connection.

        :param snapshot: Reusable scene-level geometry snapshot.
        :param source_port: Source endpoint whose owner is exempt at its boundary.
        :param destination_port: Destination endpoint whose owner is exempt at its boundary.
        :param connection_uid: Active connection whose own segments are excluded.
        :return: Connection-specific immutable geometry.
        """
        source_owner_uid: int | None
        destination_owner_uid: int | None
        if source_port.subsystem.subsys is not None:
            source_owner_uid = source_port.subsystem.subsys.uid
        else:
            source_owner_uid = None
        if destination_port.subsystem.subsys is not None:
            destination_owner_uid = destination_port.subsystem.subsys.uid
        else:
            destination_owner_uid = None
        source_owner: RoutingBlockGeometry | None = None
        destination_owner: RoutingBlockGeometry | None = None
        other_blocks: list[RoutingBlockGeometry] = list()
        block_geometry: RoutingBlockGeometry

        # Classification changes per connection, while the expensive Qt scene
        # traversal and coordinate conversion remain shared by the whole drag.
        for block_geometry in snapshot.get_blocks():
            block_uid: int = block_geometry.get_block_uid()
            if source_owner_uid is not None and block_uid == source_owner_uid:
                source_owner = block_geometry
            else:
                pass
            if destination_owner_uid is not None and block_uid == destination_owner_uid:
                destination_owner = block_geometry
            else:
                pass
            if block_uid != source_owner_uid and block_uid != destination_owner_uid:
                other_blocks.append(block_geometry)
            else:
                pass

        other_connection_segments: list[RoutingSegmentObstacle] = list()
        segment_obstacle: RoutingSegmentObstacle
        for segment_obstacle in snapshot.get_connection_segments():
            if segment_obstacle.get_connection_uid() != int(connection_uid):
                other_connection_segments.append(segment_obstacle)
            else:
                pass

        return RoutingConnectionGeometry(
            source_owner=source_owner,
            destination_owner=destination_owner,
            other_blocks=tuple(other_blocks),
            other_connection_segments=tuple(other_connection_segments),
        )

    def capture_connection_geometry(
            self,
            scene: QGraphicsScene | None,
            source_port: PortItem,
            destination_port: PortItem,
            other_connection_segments: tuple[RoutingSegmentObstacle, ...],
    ) -> RoutingConnectionGeometry:
        """
        Capture owner and foreign-block geometry for one connection.

        The two endpoint owners are captured separately because a port segment
        may touch its own block boundary. Every other supported block item is
        kept in the foreign-obstacle collection for stricter intersection
        checks in a later integration step.

        :param scene: Live graphics scene containing the connection blocks, if available.
        :param source_port: Source endpoint whose parent owns one route end.
        :param destination_port: Destination endpoint whose parent owns the other route end.
        :param other_connection_segments: Segments captured from other routing graphs.
        :return: Immutable non-Qt geometry snapshot for the connection.
        """
        source_owner_item: QGraphicsItem = source_port.subsystem
        destination_owner_item: QGraphicsItem = destination_port.subsystem
        source_owner: RoutingBlockGeometry | None = self._build_block_geometry(
            scene_item=source_owner_item,
        )
        destination_owner: RoutingBlockGeometry | None

        # A loop connection can have both ports on the same block. Reuse the
        # captured value so both endpoint roles retain identical geometry.
        if destination_owner_item is source_owner_item:
            destination_owner = source_owner
        else:
            destination_owner = self._build_block_geometry(
                scene_item=destination_owner_item,
            )

        other_blocks: list[RoutingBlockGeometry] = list()
        scene_item: QGraphicsItem
        block_geometry: RoutingBlockGeometry | None

        # Scene traversal happens only while taking the snapshot. The routing
        # core receives a stable tuple and never queries mutable Qt state.
        if scene is not None:
            for scene_item in scene.items():
                if scene_item is source_owner_item or scene_item is destination_owner_item:
                    pass
                else:
                    block_geometry = self._build_block_geometry(scene_item=scene_item)
                    if block_geometry is not None:
                        other_blocks.append(block_geometry)
                    else:
                        pass
        else:
            # Endpoint geometry remains useful during early item construction,
            # when ports exist but have not yet joined a graphics scene.
            pass

        connection_geometry: RoutingConnectionGeometry = RoutingConnectionGeometry(
            source_owner=source_owner,
            destination_owner=destination_owner,
            other_blocks=tuple(other_blocks),
            other_connection_segments=other_connection_segments,
        )
        return connection_geometry

    def _build_block_geometry(self, scene_item: QGraphicsItem) -> RoutingBlockGeometry | None:
        """
        Convert one supported visible block item to routing-core geometry.

        Child decorations and routing graphics are rejected by their concrete
        types. Invisible blocks are also omitted because they do not occupy the
        currently rendered routing workspace.

        :param scene_item: Candidate graphics-scene item.
        :return: Captured block geometry, or ``None`` for a non-block item.
        """
        supported_block_item: bool = isinstance(
            scene_item,
            (
                BlockItem,
                GenericBlockItem,
                MeasurementsItem,
                PairedItem,
                RectBaseArithmeticOpItem,
                RoundBaseArithmeticOpItem,
            ),
        )
        if not supported_block_item:
            return None
        elif not scene_item.isVisible():
            return None
        elif scene_item.subsys is None:
            return None
        else:
            scene_bounds: QRectF = scene_item.sceneBoundingRect()
            routing_bounds: RoutingBounds = RoutingBounds(
                left=scene_bounds.left(),
                top=scene_bounds.top(),
                right=scene_bounds.right(),
                bottom=scene_bounds.bottom(),
            )
            block_geometry: RoutingBlockGeometry = RoutingBlockGeometry(
                block_uid=scene_item.subsys.uid,
                bounds=routing_bounds,
            )
            return block_geometry
