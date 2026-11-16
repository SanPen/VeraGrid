# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import GraphicsView


def _get_qt_app() -> QtWidgets.QApplication:
    """Return the Qt application used by this graphics-view test.

    :return: Existing or newly created Qt application.
    """
    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    else:
        pass
    return app


def test_left_drag_empty_zoomed_canvas_pans_view() -> None:
    """Move the visible canvas when dragging empty scrollable space.

    :return: None.
    """
    qt_app: QtWidgets.QApplication = _get_qt_app()
    scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene()
    scene.setSceneRect(0.0, 0.0, 2000.0, 2000.0)
    view: GraphicsView = GraphicsView(scene=scene)
    view.resize(240, 180)
    view.show()
    qt_app.processEvents()
    view.centerOn(1000.0, 1000.0)
    qt_app.processEvents()

    initial_horizontal_value: int = view.horizontalScrollBar().value()
    initial_vertical_value: int = view.verticalScrollBar().value()
    start_position: QtCore.QPointF = QtCore.QPointF(90.0, 70.0)
    moved_position: QtCore.QPointF = QtCore.QPointF(130.0, 95.0)
    press_event: QtGui.QMouseEvent = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseButtonPress,
        start_position,
        start_position,
        start_position,
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.KeyboardModifier.NoModifier,
    )
    move_event: QtGui.QMouseEvent = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseMove,
        moved_position,
        moved_position,
        moved_position,
        QtCore.Qt.MouseButton.NoButton,
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.KeyboardModifier.NoModifier,
    )
    release_event: QtGui.QMouseEvent = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseButtonRelease,
        moved_position,
        moved_position,
        moved_position,
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.MouseButton.NoButton,
        QtCore.Qt.KeyboardModifier.NoModifier,
    )

    view.mousePressEvent(press_event)
    view.mouseMoveEvent(move_event)
    view.mouseReleaseEvent(release_event)

    assert view.horizontalScrollBar().value() < initial_horizontal_value
    assert view.verticalScrollBar().value() < initial_vertical_value
    view.close()


def test_center_items_ignores_selection_and_fits_all_block_content() -> None:
    """Fit every block-content item even when one item is selected.

    :return: None.
    """
    qt_app: QtWidgets.QApplication = _get_qt_app()
    scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene()
    view: GraphicsView = GraphicsView(scene=scene)
    original_content_types: tuple[type[QtWidgets.QGraphicsItem], ...] = GraphicsView.BLOCK_CONTENT_TYPES
    first_item: QtWidgets.QGraphicsRectItem = scene.addRect(0.0, 0.0, 20.0, 20.0)
    second_item: QtWidgets.QGraphicsRectItem = scene.addRect(1000.0, 0.0, 20.0, 20.0)
    first_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    second_item.setFlag(QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
    first_item.setSelected(True)
    view.resize(240, 180)
    view.show()
    qt_app.processEvents()

    try:
        GraphicsView.BLOCK_CONTENT_TYPES = tuple((QtWidgets.QGraphicsRectItem,))
        view.center_items()
        qt_app.processEvents()
        viewport_rect: QtCore.QRect = view.viewport().rect().adjusted(-1, -1, 1, 1)
        first_rect: QtCore.QRect = view.mapFromScene(first_item.sceneBoundingRect()).boundingRect()
        second_rect: QtCore.QRect = view.mapFromScene(second_item.sceneBoundingRect()).boundingRect()

        assert viewport_rect.contains(first_rect)
        assert viewport_rect.contains(second_rect)
    finally:
        GraphicsView.BLOCK_CONTENT_TYPES = original_content_types
        view.close()
