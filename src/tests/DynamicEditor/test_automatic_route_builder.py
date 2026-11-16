# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.automatic_route_builder import AutomaticRouteBuilder
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_elements import RoutingPoint
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_graph import RoutingGraph
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBlockGeometry
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingBounds
from VeraGrid.Gui.DynamicModelEditor.Editor.Routing.routing_scene_geometry import RoutingConnectionGeometry


def test_exterior_search_bounds_ignore_far_unrelated_blocks() -> None:
    """Keep automatic routing fallback bounds local to the connected blocks.

    :return: None.
    """
    start_position: RoutingPoint = RoutingPoint(0.0, 0.0)
    end_position: RoutingPoint = RoutingPoint(100.0, 0.0)
    near_block: RoutingBlockGeometry = RoutingBlockGeometry(
        block_uid=10,
        bounds=RoutingBounds(left=40.0, top=-10.0, right=60.0, bottom=10.0),
    )
    far_block: RoutingBlockGeometry = RoutingBlockGeometry(
        block_uid=11,
        bounds=RoutingBounds(left=5000.0, top=5000.0, right=5100.0, bottom=5100.0),
    )
    connection_geometry: RoutingConnectionGeometry = RoutingConnectionGeometry(
        source_owner=None,
        destination_owner=None,
        other_blocks=tuple((near_block, far_block)),
        other_connection_segments=tuple(),
    )
    route_builder: AutomaticRouteBuilder = AutomaticRouteBuilder(
        graph=RoutingGraph(source_node_id=1, destination_node_id=2),
        connection_geometry=connection_geometry,
    )

    search_bounds: RoutingBounds = route_builder._build_exterior_search_bounds(
        start_position=start_position,
        end_position=end_position,
        local_geometry=connection_geometry,
        exterior_margin=12.0,
    )
    exterior_margins: tuple[float, ...] = route_builder._build_exterior_search_margins(
        start_position=start_position,
        end_position=end_position,
        local_geometry=connection_geometry,
    )

    assert search_bounds.get_left() == -12.0
    assert search_bounds.get_right() == 112.0
    assert search_bounds.get_top() == -22.0
    assert search_bounds.get_bottom() == 22.0
    assert exterior_margins == tuple((12.0, 24.0, 62.0, 262.0))
