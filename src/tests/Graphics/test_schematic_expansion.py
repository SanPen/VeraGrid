# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict

from PySide6.QtCore import QPointF

from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget
from VeraGridEngine.Devices.Fluid.fluid_node import FluidNode
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import DeviceType


class _ExpansionGraphicStub:
    """
    Minimal movable graphic object for schematic expansion tests.
    """

    __slots__ = ("_api_object", "api_object", "_position", "_selected")

    def __init__(self, api_object: object, x: float, y: float, selected: bool = False) -> None:
        """
        Store the fake API object and initial position.

        :param api_object: API object represented by the graphic.
        :param x: Initial X coordinate.
        :param y: Initial Y coordinate.
        :param selected: Selection flag.
        :return: None.
        """
        self._api_object: object = api_object
        self.api_object: object = api_object
        self._position: QPointF = QPointF(x, y)
        self._selected: bool = selected

    def pos(self) -> QPointF:
        """
        Return the current position.

        :return: Current position.
        """
        return QPointF(self._position)

    def setPos(self, position: QPointF) -> None:
        """
        Store the new position.

        :param position: New position.
        :return: None.
        """
        self._position = QPointF(position)

    def isSelected(self) -> bool:
        """
        Return whether the item is selected.

        :return: Selection flag.
        """
        return self._selected


class _ExpansionGraphicsManagerStub:
    """
    Minimal graphics registry for schematic expansion tests.
    """

    __slots__ = ("graphic_dict",)

    def __init__(self) -> None:
        """
        Initialize the fake graphics dictionary.

        :return: None.
        """
        self.graphic_dict: Dict[DeviceType, Dict[str, _ExpansionGraphicStub]] = dict()


class _ExpansionDiagramSceneStub:
    """
    Minimal scene selection adapter for schematic expansion tests.
    """

    __slots__ = ("_selected_items",)

    def __init__(self) -> None:
        """
        Initialize the fake selected-items list.

        :return: None.
        """
        self._selected_items: list[object] = list()

    def selectedItems(self) -> list[object]:
        """
        Return selected items.

        :return: Selected graphics list.
        """
        return list(self._selected_items)


class _ExpansionDiagramStub:
    """
    Minimal diagram persistence adapter for schematic expansion tests.
    """

    __slots__ = ("positions",)

    def __init__(self) -> None:
        """
        Initialize persisted position storage.

        :return: None.
        """
        self.positions: dict[int, QPointF] = dict()

    def update_xy(self, api_object: object, x: float, y: float) -> None:
        """
        Persist one graphic position update.

        :param api_object: API object represented by the graphic.
        :param x: New X coordinate.
        :param y: New Y coordinate.
        :return: None.
        """
        self.positions[id(api_object)] = QPointF(x, y)


class _ExpansionWidgetStub:
    """
    Minimal object with the attributes used by ``SchematicWidget.apply_expansion_factor``.
    """

    __slots__ = ("diagram", "diagram_scene", "graphics_manager", "limits")

    def __init__(self) -> None:
        """
        Initialize fake schematic-widget collaborators.

        :return: None.
        """
        self.diagram: _ExpansionDiagramStub = _ExpansionDiagramStub()
        self.diagram_scene: _ExpansionDiagramSceneStub = _ExpansionDiagramSceneStub()
        self.graphics_manager: _ExpansionGraphicsManagerStub = _ExpansionGraphicsManagerStub()
        self.limits: tuple[float, float, float, float] | None = None

    def set_limits(self, min_x: float, max_x: float, min_y: float, max_y: float) -> None:
        """
        Store the requested scene limits.

        :param min_x: Minimum X coordinate.
        :param max_x: Maximum X coordinate.
        :param min_y: Minimum Y coordinate.
        :param max_y: Maximum Y coordinate.
        :return: None.
        """
        self.limits = (min_x, max_x, min_y, max_y)


def test_expansion_keeps_fluid_node_offset_from_visible_bus() -> None:
    """
    Check that schematic expansion preserves fluid-node offset from its visible bus.

    :return: None.
    """
    widget: _ExpansionWidgetStub = _ExpansionWidgetStub()
    bus: Bus = Bus(name="Electrical bus")
    anchored_fluid_node: FluidNode = FluidNode(name="Reservoir", bus=bus)
    free_fluid_node: FluidNode = FluidNode(name="Free reservoir")
    internal_bus: Bus = Bus(name="Internal electrical bus")
    internally_registered_fluid_node: FluidNode = FluidNode(name="Internal reservoir", bus=internal_bus)

    bus_graphic: _ExpansionGraphicStub = _ExpansionGraphicStub(api_object=bus, x=100.0, y=40.0)
    anchored_graphic: _ExpansionGraphicStub = _ExpansionGraphicStub(api_object=anchored_fluid_node,
                                                                    x=130.0,
                                                                    y=70.0)
    free_graphic: _ExpansionGraphicStub = _ExpansionGraphicStub(api_object=free_fluid_node, x=10.0, y=15.0)
    internally_registered_graphic: _ExpansionGraphicStub = _ExpansionGraphicStub(
        api_object=internally_registered_fluid_node,
        x=50.0,
        y=25.0,
    )

    widget.graphics_manager.graphic_dict[DeviceType.BusDevice] = dict([
        (bus.idtag, bus_graphic),
        (internal_bus.idtag, internally_registered_graphic),
    ])
    widget.graphics_manager.graphic_dict[DeviceType.FluidNodeDevice] = dict([
        (anchored_fluid_node.idtag, anchored_graphic),
        (free_fluid_node.idtag, free_graphic),
        (internally_registered_fluid_node.idtag, internally_registered_graphic),
    ])

    SchematicWidget.apply_expansion_factor(widget, factor=2.0)

    assert bus_graphic.pos() == QPointF(200.0, 80.0)
    assert anchored_graphic.pos() == QPointF(230.0, 110.0)
    assert free_graphic.pos() == QPointF(20.0, 30.0)
    assert internally_registered_graphic.pos() == QPointF(100.0, 50.0)
    assert widget.diagram.positions[id(anchored_fluid_node)] == QPointF(230.0, 110.0)

    SchematicWidget.apply_expansion_factor(widget, factor=0.5)

    assert bus_graphic.pos() == QPointF(100.0, 40.0)
    assert anchored_graphic.pos() == QPointF(130.0, 70.0)
    assert free_graphic.pos() == QPointF(10.0, 15.0)
    assert internally_registered_graphic.pos() == QPointF(50.0, 25.0)
