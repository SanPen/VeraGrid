# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from enum import Enum
from typing import Tuple


class SchematicAttachmentSlot(Enum):
    """
    Named attachment slots for schematic node graphics.
    """

    DEFAULT = "default"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


def normalize_attachment_slot(slot_key: SchematicAttachmentSlot | str) -> SchematicAttachmentSlot:
    """
    Normalize one runtime or persisted slot key to the enum form.

    :param slot_key: Runtime enum or persisted string.
    :return: Parsed attachment slot enum.
    """
    if isinstance(slot_key, SchematicAttachmentSlot):
        return slot_key
    else:
        return parse_attachment_slot(slot_key=str(slot_key))


def requires_explicit_attachment_anchor(slot_key: SchematicAttachmentSlot | str) -> bool:
    """
    Determine whether a slot key refers to a future explicit slot id instead of a compatibility alias.

    :param slot_key: Persisted slot key.
    :return: ``True`` when the slot should use an explicit anchor, ``False`` for compatibility aliases.
    """
    slot: SchematicAttachmentSlot = normalize_attachment_slot(slot_key)

    if slot == SchematicAttachmentSlot.DEFAULT:
        return False
    else:
        return True


def parse_attachment_slot(slot_key: str) -> SchematicAttachmentSlot:
    """
    Parse an attachment slot key into the corresponding enum value.

    :param slot_key: Persisted slot key.
    :return: Parsed slot enum. Unknown keys are treated as ``DEFAULT`` for compatibility.
    """
    if slot_key == SchematicAttachmentSlot.LEFT.value:
        return SchematicAttachmentSlot.LEFT
    elif slot_key == SchematicAttachmentSlot.RIGHT.value:
        return SchematicAttachmentSlot.RIGHT
    elif slot_key == SchematicAttachmentSlot.TOP.value:
        return SchematicAttachmentSlot.TOP
    elif slot_key == SchematicAttachmentSlot.BOTTOM.value:
        return SchematicAttachmentSlot.BOTTOM
    else:
        return SchematicAttachmentSlot.DEFAULT


def clamp_attachment_alignment(alignment: float | None) -> float:
    """
    Clamp an attachment alignment factor to the supported ``[0, 1]`` range.

    :param alignment: Optional alignment factor.
    :return: Clamped alignment factor.
    """
    if alignment is None:
        return 0.5
    else:
        pass

    alignment_value: float = float(alignment)

    if alignment_value < 0.0:
        return 0.0
    elif alignment_value > 1.0:
        return 1.0
    else:
        return alignment_value


def clamp_coordinate(value: float,
                     minimum: float,
                     maximum: float) -> float:
    """
    Clamp one scalar coordinate to a closed interval.

    :param value: Input coordinate.
    :param minimum: Lower bound.
    :param maximum: Upper bound.
    :return: Clamped coordinate.
    """
    if value < minimum:
        return minimum
    elif value > maximum:
        return maximum
    else:
        return value


def get_bar_terminal_horizontal_inset(width: float) -> float:
    """
    Compute the interior horizontal inset used by bar-style attachment anchors.

    End-of-bar branch connections should not snap exactly to the visual bar
    borders because that makes the schematic look mechanically clipped. This
    helper keeps a small interior margin while still scaling down safely for
    narrow bars.

    :param width: Bar width.
    :return: Horizontal inset from each bar end.
    """
    width_value: float = float(width)

    if width_value <= 0.0:
        return 0.0
    else:
        pass

    preferred_inset: float = min(12.0, width_value * 0.15)
    maximum_supported_inset: float = max(0.0, width_value * 0.5 - 1.0)
    return min(preferred_inset, maximum_supported_inset)


def clamp_bar_terminal_x(width: float,
                         point_x: float) -> float:
    """
    Clamp one bar attachment X coordinate to the interior connection locus.

    :param width: Bar width.
    :param point_x: Requested local X coordinate.
    :return: Clamped local X coordinate.
    """
    width_value: float = float(width)
    inset: float = get_bar_terminal_horizontal_inset(width=width_value)

    if width_value <= inset * 2.0:
        return width_value * 0.5
    else:
        return clamp_coordinate(value=float(point_x),
                                minimum=inset,
                                maximum=width_value - inset)


def project_point_to_rectangle_perimeter(width: float,
                                         height: float,
                                         point_x: float,
                                         point_y: float) -> Tuple[float, float]:
    """
    Project one local point to the rectangle perimeter along the center-to-point ray.

    :param width: Rectangle width.
    :param height: Rectangle height.
    :param point_x: Local X coordinate.
    :param point_y: Local Y coordinate.
    :return: Projected perimeter point.
    """
    center_x: float = width * 0.5
    center_y: float = height * 0.5
    delta_x: float = float(point_x) - center_x
    delta_y: float = float(point_y) - center_y

    if width <= 0.0 or height <= 0.0:
        return center_x, center_y
    elif abs(delta_x) <= 1e-9 and abs(delta_y) <= 1e-9:
        return center_x, height
    else:
        pass

    if abs(delta_x) <= 1e-9:
        scale_x: float = float("inf")
    else:
        scale_x = (width * 0.5) / abs(delta_x)

    if abs(delta_y) <= 1e-9:
        scale_y: float = float("inf")
    else:
        scale_y = (height * 0.5) / abs(delta_y)

    scale: float = min(scale_x, scale_y)
    projected_x: float = center_x + delta_x * scale
    projected_y: float = center_y + delta_y * scale
    return projected_x, projected_y


def project_point_to_bar_terminal(width: float,
                                  terminal_y: float,
                                  terminal_h: float,
                                  point_x: float) -> Tuple[float, float]:
    """
    Project one local point to the bus-bar attachment line.

    :param width: Parent width.
    :param terminal_y: Bar top Y coordinate.
    :param terminal_h: Bar height.
    :param point_x: Requested local X coordinate.
    :return: Projected local anchor point.
    """
    center_y: float = terminal_y + terminal_h * 0.5
    clamped_x: float = clamp_bar_terminal_x(width=width,
                                            point_x=point_x)
    return clamped_x, center_y


def get_bar_slot_anchor(width: float,
                        terminal_y: float,
                        terminal_h: float,
                        slot_key: SchematicAttachmentSlot | str,
                        alignment: float | None = None) -> Tuple[float, float]:
    """
    Compute the local anchor point for a bar-style terminal.

    :param width: Parent body width in scene-local coordinates.
    :param terminal_y: Y coordinate of the hosting terminal in parent-local coordinates.
    :param terminal_h: Terminal height in parent-local coordinates.
    :param slot_key: Named attachment slot key.
    :param alignment: Optional normalized alignment along the hosting side.
    :return: Local anchor point ``(x, y)``.
    """
    slot: SchematicAttachmentSlot = normalize_attachment_slot(slot_key)
    alignment_value: float = clamp_attachment_alignment(alignment)
    top_y: float = terminal_y
    center_y: float = terminal_y + terminal_h * 0.5
    bottom_y: float = terminal_y + terminal_h
    inset: float = get_bar_terminal_horizontal_inset(width=width)
    aligned_x: float = clamp_bar_terminal_x(width=width,
                                            point_x=width * alignment_value)

    if slot == SchematicAttachmentSlot.LEFT:
        return inset, center_y
    elif slot == SchematicAttachmentSlot.RIGHT:
        return width - inset, center_y
    elif slot == SchematicAttachmentSlot.TOP:
        return aligned_x, center_y
    elif slot == SchematicAttachmentSlot.BOTTOM:
        return aligned_x, center_y
    else:
        return width * 0.5, center_y


def get_round_slot_anchor(width: float,
                          height: float,
                          slot_key: SchematicAttachmentSlot | str,
                          alignment: float | None = None) -> Tuple[float, float]:
    """
    Compute the local anchor point for a round or connectivity-style node.

    :param width: Parent body width in parent-local coordinates.
    :param height: Parent body height in parent-local coordinates.
    :param slot_key: Named attachment slot key.
    :param alignment: Optional normalized alignment along the hosting side.
    :return: Local anchor point ``(x, y)``.
    """
    slot: SchematicAttachmentSlot = normalize_attachment_slot(slot_key)
    alignment_value: float = clamp_attachment_alignment(alignment)
    center_x: float = width * 0.5
    center_y: float = height * 0.5
    aligned_x: float = width * alignment_value
    aligned_y: float = height * alignment_value

    if slot == SchematicAttachmentSlot.LEFT:
        return 0.0, aligned_y
    elif slot == SchematicAttachmentSlot.RIGHT:
        return width, aligned_y
    elif slot == SchematicAttachmentSlot.TOP:
        return aligned_x, 0.0
    elif slot == SchematicAttachmentSlot.BOTTOM:
        return aligned_x, height
    else:
        return center_x, height


def infer_attachment_slot_from_route(points: Tuple[Tuple[float, float], ...] | list[Tuple[float, float]],
                                     endpoint: str) -> SchematicAttachmentSlot:
    """
    Infer the attachment side from the endpoint-adjacent route segment.

    :param points: Routed polyline points in scene order.
    :param endpoint: ``"from"`` or ``"to"``.
    :return: Canonical slot key.
    """
    if len(points) < 2:
        return SchematicAttachmentSlot.DEFAULT

    endpoint_point: Tuple[float, float]
    inner_point: Tuple[float, float]

    if endpoint == "from":
        endpoint_point = points[0]
        inner_point = points[1]
    elif endpoint == "to":
        endpoint_point = points[-1]
        inner_point = points[-2]
    else:
        return SchematicAttachmentSlot.DEFAULT

    dx: float = inner_point[0] - endpoint_point[0]
    dy: float = inner_point[1] - endpoint_point[1]

    if abs(dx) >= abs(dy):
        if dx >= 0.0:
            return SchematicAttachmentSlot.RIGHT
        else:
            return SchematicAttachmentSlot.LEFT
    else:
        if dy >= 0.0:
            return SchematicAttachmentSlot.BOTTOM
        else:
            return SchematicAttachmentSlot.TOP


def infer_attachment_side_from_points(origin: Tuple[float, float],
                                      other: Tuple[float, float],
                                      vertical_bias: float = 1.0) -> SchematicAttachmentSlot:
    """
    Infer the node side that should host a connection based on the other endpoint position.

    :param origin: Node center point.
    :param other: Opposite endpoint point.
    :param vertical_bias: Values below ``1.0`` prefer ``top``/``bottom`` for busbar-like nodes.
    :return: Canonical side key.
    """
    dx: float = float(other[0]) - float(origin[0])
    dy: float = float(other[1]) - float(origin[1])
    bias: float = max(0.1, float(vertical_bias))

    if abs(dy) >= abs(dx) * bias:
        if dy >= 0.0:
            return SchematicAttachmentSlot.BOTTOM
        else:
            return SchematicAttachmentSlot.TOP
    else:
        if dx >= 0.0:
            return SchematicAttachmentSlot.RIGHT
        else:
            return SchematicAttachmentSlot.LEFT


def build_explicit_slot_key(owner_kind: str, side: SchematicAttachmentSlot | str, order: int) -> str:
    """
    Build a stable explicit slot identifier.

    :param owner_kind: Node kind prefix such as ``"bus"`` or ``"fluid"``.
    :param side: Attachment side.
    :param order: One-based slot order on that side.
    :return: Explicit slot key.
    """
    normalized_side: SchematicAttachmentSlot = normalize_attachment_slot(side)
    return f"{owner_kind}-{normalized_side.value}-{int(order)}"


def parse_explicit_slot_key(slot_key: str) -> Tuple[str, SchematicAttachmentSlot, int] | None:
    """
    Parse an explicit slot identifier.

    :param slot_key: Persisted slot key.
    :return: Tuple ``(owner_kind, side, order)`` or ``None`` when the key is not explicit.
    """
    parts: list[str] = slot_key.split("-")

    if len(parts) != 3:
        return None
    else:
        pass

    owner_kind: str = parts[0]
    side: SchematicAttachmentSlot = parse_attachment_slot(parts[1])
    order_text: str = parts[2]

    if not order_text.isdigit():
        return None
    elif side == SchematicAttachmentSlot.DEFAULT:
        return None
    else:
        return owner_kind, side, int(order_text)


def get_distributed_anchor(side: SchematicAttachmentSlot | str,
                           width: float,
                           height: float,
                           terminal_y: float,
                           terminal_h: float,
                           order_index: int,
                           slot_count: int,
                           alignment: float | None = None) -> Tuple[float, float]:
    """
    Compute a distributed anchor along a given side.

    :param side: Attachment side.
    :param width: Body width.
    :param height: Body height.
    :param terminal_y: Terminal Y coordinate for bar-style bodies.
    :param terminal_h: Terminal height for bar-style bodies.
    :param order_index: One-based slot index within the sorted side ordering.
    :param slot_count: Total slot count on that side.
    :param alignment: Optional normalized alignment override along the side.
    :return: Local anchor point.
    """
    normalized_side: SchematicAttachmentSlot = normalize_attachment_slot(side)

    if alignment is None:
        span_fraction: float = float(order_index) / float(slot_count + 1)
    else:
        span_fraction = clamp_attachment_alignment(alignment)

    inset: float = get_bar_terminal_horizontal_inset(width=width)
    bar_top_y: float = terminal_y
    bar_center_y: float = terminal_y + terminal_h * 0.5
    bar_bottom_y: float = terminal_y + terminal_h

    if normalized_side == SchematicAttachmentSlot.LEFT:
        return inset, height * span_fraction
    elif normalized_side == SchematicAttachmentSlot.RIGHT:
        return width - inset, height * span_fraction
    elif normalized_side == SchematicAttachmentSlot.TOP:
        return clamp_bar_terminal_x(width=width,
                                    point_x=width * span_fraction), bar_center_y
    elif normalized_side == SchematicAttachmentSlot.BOTTOM:
        return clamp_bar_terminal_x(width=width,
                                    point_x=width * span_fraction), bar_center_y
    else:
        return width * 0.5, bar_center_y
