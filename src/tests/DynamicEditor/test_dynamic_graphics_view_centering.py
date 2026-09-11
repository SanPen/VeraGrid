from __future__ import annotations

import sys

from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import BlockItem
from VeraGrid.Gui.DynamicModelEditor.Editor.dynamic_editor_graphics import GraphicsView


class CenteringTestBlockItem(BlockItem):
    """Minimal block item used to exercise graphics-view fitting."""

    __slots__ = ()

    def __init__(self, rect: QtCore.QRectF) -> None:
        """Create a centerable item without dynamic-model dependencies.

        :param rect: Local rectangle represented by the test block.
        :return: None.
        """
        QtWidgets.QGraphicsRectItem.__init__(self, rect)


def get_qt_application() -> QtWidgets.QApplication:
    """Return the shared Qt application used by graphics tests.

    :return: Existing or newly created Qt application.
    """
    application: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()
    if application is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return application


def test_center_items_fits_all_blocks_inside_visible_viewport() -> None:
    """Center must make every unselected block fully visible with a margin.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene()
    first_item: CenteringTestBlockItem = CenteringTestBlockItem(
        QtCore.QRectF(0.0, 0.0, 100.0, 60.0)
    )
    second_item: CenteringTestBlockItem = CenteringTestBlockItem(
        QtCore.QRectF(0.0, 0.0, 120.0, 80.0)
    )
    second_item.setPos(1200.0, 700.0)
    scene.addItem(first_item)
    scene.addItem(second_item)
    view: GraphicsView = GraphicsView(scene)
    view.resize(800, 600)
    view.show()
    _unused_application.processEvents()

    view.scale(4.0, 4.0)
    view.center_items()

    visible_scene_rect: QtCore.QRectF = view.mapToScene(view.viewport().rect()).boundingRect()
    assert visible_scene_rect.contains(first_item.sceneBoundingRect())
    assert visible_scene_rect.contains(second_item.sceneBoundingRect())
    assert scene.sceneRect().contains(first_item.sceneBoundingRect())
    assert scene.sceneRect().contains(second_item.sceneBoundingRect())
    assert view.transform().m11() < 4.0
    view.close()


def test_expand_scene_rect_contains_blocks_without_changing_zoom() -> None:
    """Scene expansion must expose distant blocks and preserve current zoom.

    :return: None.
    """
    _unused_application: QtWidgets.QApplication = get_qt_application()
    scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene(
        QtCore.QRectF(0.0, 0.0, 1200.0, 800.0)
    )
    distant_item: CenteringTestBlockItem = CenteringTestBlockItem(
        QtCore.QRectF(0.0, 0.0, 120.0, 80.0)
    )
    distant_item.setPos(1800.0, 950.0)
    scene.addItem(distant_item)
    view: GraphicsView = GraphicsView(scene)
    view.scale(2.0, 2.0)
    original_scale: float = view.transform().m11()

    view.expand_scene_rect_to_blocks()

    assert scene.sceneRect().contains(distant_item.sceneBoundingRect())
    assert view.transform().m11() == original_scale
    view.close()
