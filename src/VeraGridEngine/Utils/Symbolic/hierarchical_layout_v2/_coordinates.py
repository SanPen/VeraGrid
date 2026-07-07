# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Coordinate assignment — strict vertical grid.

Rules:
  1. x = layer_index * spacing  (fixed)
  2. y = margin_y + row * pitch  (fixed, pitch = node_h + node_spacing_y)
  3. No alignment passes (they break the grid)
  4. No compaction (destroys separation)
  5. No edge-length optimisation (pulls everything to centre)

After crossing minimisation the node order within each layer is good.
Coordinate assignment respects that order and places nodes on a
strict uniform grid.  Nothing more, nothing less.
"""
from __future__ import annotations

from typing import Dict, Tuple

from ._types import LayoutGraph


def assign_coordinates(
    graph: LayoutGraph,
) -> Dict[int, Tuple[float, float]]:
    cfg = graph.config
    pitch_y = cfg.node_h + cfg.node_spacing_y
    node_x: Dict[int, float] = {}
    node_y: Dict[int, float] = {}

    for layer_idx, items in enumerate(graph.layers):
        for v in items:
            node_x[v] = cfg.margin_x + layer_idx * cfg.layer_spacing_x

    for items in graph.layers:
        for i, v in enumerate(items):
            h = cfg.dummy_h if v in graph.is_dummy else cfg.node_h
            centre_offset = (cfg.node_h - h) / 2.0
            node_y[v] = cfg.margin_y + i * pitch_y + centre_offset

    result: Dict[int, Tuple[float, float]] = {}
    for v in graph.original_nodes:
        result[v] = (node_x.get(v, 0.0), node_y.get(v, 0.0))
    return result
