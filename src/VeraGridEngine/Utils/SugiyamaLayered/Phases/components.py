# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Connected components phase for the Sugiyama layered pipeline."""

from __future__ import annotations

from collections import deque

from VeraGridEngine.Utils.SugiyamaLayered.pipeline import LayoutContext, LayoutPhaseBase


def _owner_of_endpoint(
        node_ids: set[str],
        port_to_owner: dict[str, str],
        endpoint_id: str,
) -> str | None:
    """Resolve one endpoint identifier to its owning node.

    :param node_ids: Known node identifiers.
    :type node_ids: set[str]
    :param port_to_owner: Port-to-node ownership map.
    :type port_to_owner: dict[str, str]
    :param endpoint_id: Endpoint identifier to resolve.
    :type endpoint_id: str
    :return: Owning node identifier when it exists.
    :rtype: str | None
    """
    if endpoint_id in node_ids:
        return endpoint_id
    else:
        return port_to_owner.get(endpoint_id, None)


class ConnectedComponentsPhase(LayoutPhaseBase):
    """Detect connected graph components."""

    __slots__ = ()

    name: str = "connected-components"

    def run(self, context: LayoutContext) -> None:
        """Execute the connected components phase.

        The phase first maps every port to its owner node so edge endpoints can
        be reduced to a pure node-level adjacency graph. Then it runs one
        breadth-first search per unvisited node to enumerate the components.

        :param context: Shared pipeline context.
        :type context: LayoutContext
        :return: None.
        :rtype: None
        """
        node_ids: set[str] = set()
        port_to_owner: dict[str, str] = dict()
        adjacency: dict[str, set[str]] = dict()
        components: list[list[str]] = list()
        visited: set[str] = set()
        node_id: str

        for node in context.graph.children:
            node_ids.add(node.identifier)
            adjacency[node.identifier] = set()
            for port in node.ports:
                port_to_owner[port.identifier] = node.identifier

        for edge in context.graph.edges:
            for source in edge.sources:
                for target in edge.targets:
                    source_node: str | None = _owner_of_endpoint(node_ids, port_to_owner, source)
                    target_node: str | None = _owner_of_endpoint(node_ids, port_to_owner, target)
                    if source_node is None or target_node is None:
                        pass
                    else:
                        adjacency[source_node].add(target_node)
                        adjacency[target_node].add(source_node)

        for node_id in adjacency:
            if node_id in visited:
                pass
            else:
                queue: deque[str] = deque([node_id])
                component: list[str] = list()
                visited.add(node_id)

                while len(queue) > 0:
                    current_node_id: str = queue.popleft()
                    component.append(current_node_id)

                    for neighbor_node_id in sorted(adjacency.get(current_node_id, set())):
                        if neighbor_node_id in visited:
                            pass
                        else:
                            visited.add(neighbor_node_id)
                            queue.append(neighbor_node_id)

                components.append(component)

        context.phase_state.components.clear()
        context.phase_state.components.extend(components)
        context.report.add_note(f"Detected {len(components)} connected component(s).")
