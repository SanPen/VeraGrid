# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, Set, TYPE_CHECKING

import networkx as nx
from VeraGrid.ThirdParty.adjustText import adjust_text
from PySide6 import QtWidgets

from VeraGrid.Gui.ProceduralGrid.procedural_grid_preview_ui import Ui_Dialog
from VeraGridEngine.enumerations import ProceduralGridMethods
import VeraGridEngine.Devices as dev

if TYPE_CHECKING:
    from VeraGridEngine.Topology.Procedural.procedural_grid_engine import ProceduralGridComputationEngine


class ProceduralGridPreviewDialog(QtWidgets.QDialog):
    """
    Dialog that displays a preview of the procedural grid expansion result.
    Existing buses are shown in blue; newly created buses (Steiner and intermediate
    points) are shown in green. The user can confirm the result by clicking
    "Create Grid" or discard it by clicking "Cancel".
    """

    def __init__(self,
                 engine: ProceduralGridComputationEngine,
                 method: ProceduralGridMethods,
                 parent: QtWidgets.QWidget = None) -> None:
        """
        :param engine: The engine that has already run the expansion algorithm.
        :param method: The method that was used (shown in the window title).
        :param parent: Parent widget.
        """
        QtWidgets.QDialog.__init__(self, parent)
        self.ui: Ui_Dialog = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(f'Procedural grid preview — {method.value}')

        # Populate the summary label
        n_new_buses: int = len(engine.get_new_buses())
        n_new_lines: int = len(engine.get_new_lines())
        n_new_transformers: int = len(engine.get_new_transformers())
        self.ui.summaryLabel.setText(
            f'{n_new_buses} new bus(es), {n_new_lines} new line(s) and '
            f'{n_new_transformers} new transformer(s) will be added to the grid.'
        )

        self._draw_graph(engine=engine)

        self.ui.createGridButton.clicked.connect(self.accept)
        self.ui.cancelButton.clicked.connect(self.reject)

    def _draw_graph(self, engine: ProceduralGridComputationEngine) -> None:
        """
        Build a NetworkX graph from the engine result and render it on the
        embedded MatplotlibWidget. Existing buses (targets and candidates) are
        drawn in light blue; newly created buses are drawn in light green.

        :param engine: The engine whose buses and lines are used to build the graph.
        """
        all_buses: List[dev.Bus] = engine.get_buses()
        new_buses: List[dev.Bus] = engine.get_new_buses()
        new_lines: List[dev.Line] = engine.get_new_lines()
        new_transformers: List[dev.Transformer2W] = engine.get_new_transformers()

        # Build a set of new-bus names for O(1) membership checks
        new_bus_names: Set[str] = set()
        for bus in new_buses:
            new_bus_names.add(bus.name)

        G: nx.Graph = nx.Graph()
        pos: dict = dict()
        existing_node_names: List[str] = list()
        new_node_names: List[str] = list()

        # Add all buses as nodes, recording which colour group they belong to
        for bus in all_buses:
            G.add_node(bus.name)
            pos[bus.name] = (bus.longitude, bus.latitude)
            if bus.name in new_bus_names:
                new_node_names.append(bus.name)
            else:
                existing_node_names.append(bus.name)

        # Add new lines as edges
        for line in new_lines:
            G.add_edge(line.bus_from.name, line.bus_to.name)

        # Add new transformers as edges
        for transformer in new_transformers:
            G.add_edge(transformer.bus_from.name, transformer.bus_to.name)

        ax = self.ui.plotWidget.get_axis()

        # Draw existing buses in blue and new buses in green so the user can
        # clearly distinguish what is being added to the grid
        nx.draw_networkx_nodes(G, pos=pos, nodelist=existing_node_names,
                               ax=ax, node_color='lightblue', node_size=300)
        nx.draw_networkx_nodes(G, pos=pos, nodelist=new_node_names,
                               ax=ax, node_color='lightgreen', node_size=300)
        nx.draw_networkx_edges(G, pos=pos, ax=ax)

        # Place labels as Text objects first, then let adjustText reposition
        # them so that overlapping labels (including co-located nodes) are
        # spread apart automatically
        texts: List = list()
        for node, (x, y) in pos.items():
            texts.append(ax.text(x, y, node, fontsize=7))

        adjust_text(texts, ax=ax)

        self.ui.plotWidget.redraw()
