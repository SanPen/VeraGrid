"""
Fase 4: Region packing.

After each connected component has its own layout, arrange the
component bounding boxes in the available scene space.

Strategy: horizontal strip (shelf) packing.
- Sort components by height descending.
- Place left-to-right in rows (shelves).
- Each row height is determined by the tallest component.
- When a component doesn't fit in the current row, start a new row below.

This is deterministic and O(C log C) where C = number of components.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from ._types import LayoutConfig


@dataclass
class ComponentBBox:
    """Bounding box of a laid-out connected component."""
    component_id: int
    nodes: Set[int]
    positions: Dict[int, Tuple[float, float]]
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    def normalize_to_zero(self) -> None:
        """Shift all positions so min_x=0, min_y=0."""
        offset_x = self.min_x
        offset_y = self.min_y
        for node in self.positions:
            x, y = self.positions[node]
            self.positions[node] = (x - offset_x, y - offset_y)
        self.max_x -= offset_x
        self.min_x = 0.0
        self.max_y -= offset_y
        self.min_y = 0.0

    def translate(self, dx: float, dy: float) -> None:
        """Shift all positions by (dx, dy)."""
        for node in self.positions:
            x, y = self.positions[node]
            self.positions[node] = (x + dx, y + dy)
        self.min_x += dx
        self.max_x += dx
        self.min_y += dy
        self.max_y += dy


def compute_component_bboxes(
    component_layouts: List[Tuple[Set[int], Dict[int, Tuple[float, float]]]],
    config: LayoutConfig,
) -> List[ComponentBBox]:
    """
    Compute bounding boxes for each component layout.
    """
    bboxes: List[ComponentBBox] = []
    for cid, (nodes, positions) in enumerate(component_layouts):
        if not positions:
            bboxes.append(ComponentBBox(
                component_id=cid, nodes=nodes,
                positions=positions,
            ))
            continue
        xs = [p[0] for p in positions.values()]
        ys = [p[1] for p in positions.values()]
        bbox = ComponentBBox(
            component_id=cid,
            nodes=nodes,
            positions=positions,
            min_x=min(xs),
            max_x=max(xs) + config.node_w,
            min_y=min(ys),
            max_y=max(ys) + config.node_h,
        )
        bboxes.append(bbox)
    return bboxes


def pack_components(
    bboxes: List[ComponentBBox],
    config: LayoutConfig,
) -> Dict[int, Tuple[float, float]]:
    """
    Pack component bounding boxes into the scene.

    Shelf-packing algorithm:
    1. Sort by height descending.
    2. Place left-to-right; when width exceeds limit, new row.
    3. Return merged positions dict.

    The COMPONENT_GAP controls separation between components.
    """
    if not bboxes:
        return {}

    # Normalise each component to (0,0) origin
    for bbox in bboxes:
        bbox.normalize_to_zero()

    # Sort by height descending for better packing
    sorted_bboxes = sorted(bboxes, key=lambda b: -b.height)

    # Scene width limit: use available width or a large default
    scene_width = config.layer_spacing_x * 8  # 8 layers worth

    # Pack
    packed: List[ComponentBBox] = []
    cursor_x = 0.0
    cursor_y = 0.0
    row_height = 0.0
    gap = config.node_spacing_y * 2  # separation between components

    for bbox in sorted_bboxes:
        if cursor_x + bbox.width > scene_width and cursor_x > 0:
            # New row
            cursor_x = 0.0
            cursor_y += row_height + gap * 3
            row_height = 0.0

        bbox.translate(cursor_x, cursor_y)
        packed.append(bbox)
        cursor_x += bbox.width + gap * 4
        row_height = max(row_height, bbox.height)

    # Merge all positions
    merged: Dict[int, Tuple[float, float]] = {}
    for bbox in packed:
        merged.update(bbox.positions)

    return merged


# ──────────────────────────────────────────────
# Region packing (within a connected component)
# ──────────────────────────────────────────────

@dataclass
class RegionBBox:
    """Bounding box of a laid-out region (cluster within a component)."""
    nodes: Set[int]
    positions: Dict[int, Tuple[float, float]]
    min_x: float = 0.0
    min_y: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    def normalize_to_zero(self) -> None:
        offset_x = self.min_x
        offset_y = self.min_y
        for node in self.positions:
            x, y = self.positions[node]
            self.positions[node] = (x - offset_x, y - offset_y)
        self.max_x -= offset_x
        self.min_x = 0.0
        self.max_y -= offset_y
        self.min_y = 0.0

    def translate(self, dx: float, dy: float) -> None:
        for node in self.positions:
            x, y = self.positions[node]
            self.positions[node] = (x + dx, y + dy)
        self.min_x += dx
        self.max_x += dx
        self.min_y += dy
        self.max_y += dy


def pack_regions(
    region_layouts: List[Tuple[Set[int], Dict[int, Tuple[float, float]]]],
    config: LayoutConfig,
) -> Dict[int, Tuple[float, float]]:
    """
    Pack regions within a single connected component.

    Regions are separated by larger gaps:
        region_gap_x = layer_spacing_x * 2.5
        region_gap_y = node_spacing_y * 3.0

    Shelf-packing: sort by height, place left-to-right, new row below.
    """
    if not region_layouts:
        return {}

    region_gap_x = config.layer_spacing_x * 2.5
    region_gap_y = config.node_spacing_y * 3.0

    # Build bboxes
    bboxes: List[RegionBBox] = []
    for nodes, positions in region_layouts:
        if not positions:
            bboxes.append(RegionBBox(nodes=nodes, positions=positions))
            continue
        xs = [p[0] for p in positions.values()]
        ys = [p[1] for p in positions.values()]
        bboxes.append(RegionBBox(
            nodes=nodes,
            positions=positions,
            min_x=min(xs),
            max_x=max(xs) + config.node_w,
            min_y=min(ys),
            max_y=max(ys) + config.node_h,
        ))

    # Normalise
    for bbox in bboxes:
        bbox.normalize_to_zero()

    # Sort by height descending
    sorted_bboxes = sorted(bboxes, key=lambda b: -b.height)
    scene_width = config.layer_spacing_x * 8

    cursor_x = 0.0
    cursor_y = 0.0
    row_height = 0.0

    for bbox in sorted_bboxes:
        if cursor_x + bbox.width > scene_width and cursor_x > 0:
            cursor_x = 0.0
            cursor_y += row_height + region_gap_y
            row_height = 0.0

        bbox.translate(cursor_x, cursor_y)
        cursor_x += bbox.width + region_gap_x
        row_height = max(row_height, bbox.height)

    merged: Dict[int, Tuple[float, float]] = {}
    for bbox in bboxes:
        merged.update(bbox.positions)

    return merged
