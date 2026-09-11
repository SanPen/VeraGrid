from __future__ import annotations

import math

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import PortItem


def test_port_hit_shape_is_the_triangle_circumcircle() -> None:
    """Input and output ports must expose their exact circumcircles for hits.

    :return: None.
    """
    parent_item: QtWidgets.QGraphicsRectItem = QtWidgets.QGraphicsRectItem()
    editor_stub: object = object()
    port_size: int = 10
    expected_radius: float = float(port_size) / math.sqrt(3.0)
    triangle_height: float = math.sqrt(3.0) * float(port_size) / 2.0
    input_port: PortItem = PortItem(
        subsystem=parent_item,  # type: ignore[arg-type]
        editor=editor_stub,  # type: ignore[arg-type]
        is_input=True,
        index=0,
        total=1,
        size=port_size,
    )
    output_port: PortItem = PortItem(
        subsystem=parent_item,  # type: ignore[arg-type]
        editor=editor_stub,  # type: ignore[arg-type]
        is_input=False,
        index=0,
        total=1,
        size=port_size,
    )

    input_center: QtCore.QPointF = QtCore.QPointF(-2.0 * triangle_height / 3.0, 0.0)
    output_center: QtCore.QPointF = QtCore.QPointF(triangle_height / 3.0, 0.0)
    port: PortItem
    center: QtCore.QPointF
    for port, center in ((input_port, input_center), (output_port, output_center)):
        hit_bounds: QtCore.QRectF = port.boundingRect()
        point_inside_circle_outside_triangle: QtCore.QPointF = QtCore.QPointF(
            center.x(),
            expected_radius - 0.1,
        )
        point_outside_circle: QtCore.QPointF = QtCore.QPointF(
            center.x(),
            expected_radius + 0.1,
        )

        assert math.isclose(hit_bounds.width(), 2.0 * expected_radius)
        assert math.isclose(hit_bounds.height(), 2.0 * expected_radius)
        assert port.shape().contains(point_inside_circle_outside_triangle)
        assert not port._path.contains(point_inside_circle_outside_triangle)
        assert not port.shape().contains(point_outside_circle)
