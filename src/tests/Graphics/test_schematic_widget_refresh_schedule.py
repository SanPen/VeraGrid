from typing import Callable

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QGraphicsItem, QGraphicsView

import VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget as schematic_widget_module
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import CustomGraphicsView, SchematicWidget
from VeraGridEngine.Devices.Branches.winding import Winding
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import DeviceType, SchematicAutoRouteStyle


class _UpdateDiagramStub:
    __slots__ = ("diagram", "graphics_manager", "_loading")

    def __init__(self, loading: bool) -> None:
        """
        Initialize the update-diagram stub.

        :param loading: Diagram loading flag.
        :return: ``None``.
        """
        self.diagram = _UpdateDiagramDiagramStub()
        self.graphics_manager = _UpdateDiagramGraphicsManagerStub()
        self._loading = loading

    def is_loading_diagram(self) -> bool:
        """
        Return the configured loading flag.

        :return: Loading flag.
        """
        return self._loading


class _UpdateDiagramDiagramStub:
    __slots__ = ("update_calls", "sync_calls")

    def __init__(self) -> None:
        """
        Initialize recorded diagram calls.

        :return: ``None``.
        """
        self.update_calls: list[tuple] = list()
        self.sync_calls: list[object] = list()

    def update_graphic_location(self, api_object, x, y, h, w, r, draw_labels) -> None:
        """
        Record one graphic-location update.

        :return: ``None``.
        """
        self.update_calls.append((api_object, x, y, h, w, r, draw_labels))

    def sync_branch_attachments(self, api_object) -> None:
        """
        Record one branch-attachment sync request.

        :return: ``None``.
        """
        self.sync_calls.append(api_object)


class _UpdateDiagramGraphicsManagerStub:
    __slots__ = ("registrations",)

    def __init__(self) -> None:
        """
        Initialize recorded graphics registrations.

        :return: ``None``.
        """
        self.registrations: list[tuple] = list()

    def add_device(self, elm, graphic) -> None:
        """
        Record one graphics-manager registration.

        :return: ``None``.
        """
        self.registrations.append((elm, graphic))


class _BranchStyleGraphicStub:
    __slots__ = ("styles",)

    def __init__(self) -> None:
        """
        Initialize the recorded style list.

        :return: ``None``.
        """
        self.styles: list[SchematicAutoRouteStyle] = list()

    def set_branch_auto_route_style(self, route_style: SchematicAutoRouteStyle) -> None:
        """
        Record one widget-level branch style change.

        :param route_style: Requested route style.
        :return: ``None``.
        """
        self.styles.append(route_style)


class _BranchStyleLineGraphicStub(_BranchStyleGraphicStub):
    __slots__ = tuple()


class _BranchStyleGraphicsManagerStub:
    __slots__ = ("device_type_lists",)

    def __init__(self) -> None:
        """
        Initialize branch graphics grouped by device type.

        :return: ``None``.
        """
        self.device_type_lists: dict[DeviceType, list[object]] = dict()

    def get_device_type_list(self, device_type: DeviceType) -> list[object]:
        """
        Return the configured graphic list for one device type.

        :param device_type: Device type key.
        :return: Registered graphics.
        """
        return self.device_type_lists.get(device_type, list())


class _RefreshScheduleStub:
    __slots__ = ("_branch_refresh_scheduled", "_needs_post_show_branch_refresh", "_visible")

    def __init__(self, visible: bool) -> None:
        """
        Initialize the scheduler stub.

        :param visible: Initial visibility flag.
        :return: ``None``.
        """
        self._branch_refresh_scheduled: bool = False
        self._needs_post_show_branch_refresh: bool = False
        self._visible: bool = visible

    def isVisible(self) -> bool:
        """
        Return the configured visibility state.

        :return: Visibility flag.
        """
        return self._visible

    def refresh_branch_callbacks_after_draw(self) -> None:
        """
        Placeholder queued callback target used by the scheduler tests.

        :return: ``None``.
        """
        return None


class _WindingTerminalGraphicStub:
    __slots__ = tuple()

    @staticmethod
    def get_terminal():
        return "terminal"


class _WindingWidgetStub:
    __slots__ = ("queried_buses", "add_api_branch_call")

    def __init__(self) -> None:
        self.queried_buses: list[Bus | None] = list()
        self.add_api_branch_call: tuple | None = None

    def _query_bus_graphic(self, bus: Bus | None):
        self.queried_buses.append(bus)
        return _WindingTerminalGraphicStub()

    def add_api_branch(self, **kwargs):
        self.add_api_branch_call = kwargs
        return "created-winding"


class _CenterNodesSceneStub:
    __slots__ = ("_rect", "set_rect_calls")

    def __init__(self, rect: QRectF) -> None:
        self._rect = rect
        self.set_rect_calls: list[QRectF] = list()

    def itemsBoundingRect(self) -> QRectF:
        return QRectF(self._rect)

    def setSceneRect(self, rect: QRectF) -> None:
        self.set_rect_calls.append(QRectF(rect))


class _CenterNodesViewStub:
    __slots__ = ("fit_calls", "scale_calls")

    def __init__(self) -> None:
        self.fit_calls: list[QRectF] = list()
        self.scale_calls: list[tuple[float, float]] = list()

    def fitInView(self, rect: QRectF, _mode) -> None:
        self.fit_calls.append(QRectF(rect))

    def scale(self, sx: float, sy: float) -> None:
        self.scale_calls.append((sx, sy))


class _CenterNodesWidgetStub:
    __slots__ = ("diagram_scene", "editor_graphics_view")

    def __init__(self, rect: QRectF) -> None:
        self.diagram_scene = _CenterNodesSceneStub(rect=rect)
        self.editor_graphics_view = _CenterNodesViewStub()


class _PersistSelectedGraphicStub:
    __slots__ = ("_api_object", "_pos", "_scene_pos", "_rotation", "w", "h", "_draw_labels", "_movable")

    def __init__(self,
                 api_object,
                 x: float,
                 y: float,
                 movable: bool = True,
                 scene_x: float | None = None,
                 scene_y: float | None = None) -> None:
        self._api_object = api_object
        self._pos = type("PointStub", (), {"x": lambda self: x, "y": lambda self: y})()
        if scene_x is None:
            scene_x = x
        else:
            pass

        if scene_y is None:
            scene_y = y
        else:
            pass

        self._scene_pos = type("PointStub", (), {"x": lambda self: scene_x, "y": lambda self: scene_y})()
        self._rotation = 7.0
        self.w = 30.0
        self.h = 40.0
        self._draw_labels = False
        self._movable = movable

    @property
    def api_object(self):
        return self._api_object

    @property
    def draw_labels(self):
        return self._draw_labels

    def pos(self):
        return self._pos

    def scenePos(self):
        return self._scene_pos

    def rotation(self) -> float:
        return self._rotation

    def flags(self):
        if self._movable:
            return QGraphicsItem.GraphicsItemFlag.ItemIsMovable
        return QGraphicsItem.GraphicsItemFlag(0)


class _PersistSelectedSceneStub:
    __slots__ = ("_selected_items",)

    def __init__(self, selected_items: list[object]) -> None:
        self._selected_items = selected_items

    def selectedItems(self) -> list[object]:
        return list(self._selected_items)


class _PersistSelectedWidgetStub:
    __slots__ = ("diagram_scene", "calls")

    def __init__(self, selected_items: list[object]) -> None:
        self.diagram_scene = _PersistSelectedSceneStub(selected_items=selected_items)
        self.calls: list[dict[str, object]] = list()

    def update_diagram_element(self, **kwargs) -> None:
        self.calls.append(kwargs)


class _RepairInjectionApiStub:
    __slots__ = ("device_type",)

    def __init__(self, device_type: DeviceType) -> None:
        self.device_type = device_type


class _RepairLocationStub:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y


class _RepairOwnerGraphicStub:
    __slots__ = ("w", "h", "scene_x", "scene_y", "arrange_calls")

    def __init__(self, scene_x: float, scene_y: float, w: float = 180.0, h: float = 40.0) -> None:
        self.w = w
        self.h = h
        self.scene_x = scene_x
        self.scene_y = scene_y
        self.arrange_calls = 0

    def mapFromScene(self, point: QPointF) -> QPointF:
        return QPointF(float(point.x()) - self.scene_x, float(point.y()) - self.scene_y)

    def get_bottom_dock_baseline(self) -> float:
        return 40.0

    def arrange_children(self) -> None:
        self.arrange_calls += 1


class _RepairInjectionGraphicStub:
    __slots__ = ("api_object", "parent", "w", "h", "_x", "_y", "_rotation", "draw_labels", "nexus_updates")

    def __init__(self,
                 api_object: _RepairInjectionApiStub,
                 parent: _RepairOwnerGraphicStub,
                 x: float = 0.0,
                 y: float = 0.0) -> None:
        self.api_object = api_object
        self.parent = parent
        self.w = 20.0
        self.h = 20.0
        self._x = x
        self._y = y
        self._rotation = 0.0
        self.draw_labels = True
        self.nexus_updates = 0

    def setPos(self, x: float, y: float) -> None:
        self._x = float(x)
        self._y = float(y)

    def scenePos(self) -> QPointF:
        return QPointF(self.parent.scene_x + self._x, self.parent.scene_y + self._y)

    def rotation(self) -> float:
        return self._rotation

    def update_nexus(self, _pos: QPointF) -> None:
        self.nexus_updates += 1


class _RepairGraphicsManagerStub:
    __slots__ = ("graphics_by_type",)

    def __init__(self, graphics_by_type: dict[DeviceType, list[object]]) -> None:
        self.graphics_by_type = graphics_by_type

    def get_device_type_list(self, device_type: DeviceType) -> list[object]:
        return list(self.graphics_by_type.get(device_type, list()))


class _RepairDiagramStub:
    __slots__ = ("locations", "docks")

    def __init__(self,
                 locations: dict[object, _RepairLocationStub],
                 docks: dict[object, dict[str, object]]) -> None:
        self.locations = locations
        self.docks = docks

    def query_point(self, api_object) -> _RepairLocationStub | None:
        return self.locations.get(api_object)

    def get_dock(self, api_object) -> dict[str, object]:
        return dict(self.docks.get(api_object, dict()))


class _RepairWidgetStub:
    __slots__ = ("diagram", "graphics_manager", "calls")

    def __init__(self,
                 diagram: _RepairDiagramStub,
                 graphics_manager: _RepairGraphicsManagerStub) -> None:
        self.diagram = diagram
        self.graphics_manager = graphics_manager
        self.calls: list[dict[str, object]] = list()

    def _get_device_type_graphics(self, device_type: DeviceType, graphic_type: type) -> list[object]:
        return list(self.graphics_manager.get_device_type_list(device_type))

    def update_diagram_element(self, **kwargs) -> None:
        self.calls.append(kwargs)
        location = self.diagram.query_point(kwargs["device"])

        if location is not None:
            location.x = float(kwargs["x"])
            location.y = float(kwargs["y"])
        else:
            pass


def test_schedule_branch_callbacks_after_draw_coalesces_visible_refresh(override_attrs) -> None:
    """
    Visible widgets should queue at most one branch-refresh callback.
    """
    queued_calls: list[tuple[int, Callable]] = list()
    stub = _RefreshScheduleStub(visible=True)

    def _fake_single_shot(timeout: int, callback: Callable) -> None:
        """
        Record queued callbacks.

        :param timeout: Timer delay.
        :param callback: Queued callback.
        :return: ``None``.
        """
        queued_calls.append((timeout, callback))

    override_attrs.setattr(schematic_widget_module.QTimer, "singleShot", _fake_single_shot)

    SchematicWidget.schedule_branch_callbacks_after_draw(stub)
    SchematicWidget.schedule_branch_callbacks_after_draw(stub)

    assert stub._branch_refresh_scheduled is True
    assert stub._needs_post_show_branch_refresh is False
    assert len(queued_calls) == 1


def test_schedule_branch_callbacks_after_draw_defers_until_visible(override_attrs) -> None:
    """
    Hidden widgets should postpone the heavy refresh until show time.
    """
    queued_calls: list[tuple[int, Callable]] = list()
    stub = _RefreshScheduleStub(visible=False)

    def _fake_single_shot(timeout: int, callback: Callable) -> None:
        """
        Record queued callbacks.

        :param timeout: Timer delay.
        :param callback: Queued callback.
        :return: ``None``.
        """
        queued_calls.append((timeout, callback))

    override_attrs.setattr(schematic_widget_module.QTimer, "singleShot", _fake_single_shot)

    SchematicWidget.schedule_branch_callbacks_after_draw(stub)

    assert stub._branch_refresh_scheduled is False
    assert stub._needs_post_show_branch_refresh is True
    assert queued_calls == list()


def test_custom_graphics_view_drag_mode_defaults_to_pan_and_ctrl_selects() -> None:
    """
    Schematic view dragging should pan by default and use rubber-band selection with Ctrl.
    """
    default_mode = CustomGraphicsView.get_drag_mode_for_modifiers(Qt.KeyboardModifier.NoModifier)
    ctrl_mode = CustomGraphicsView.get_drag_mode_for_modifiers(Qt.KeyboardModifier.ControlModifier)

    assert default_mode == QGraphicsView.DragMode.ScrollHandDrag
    assert ctrl_mode == QGraphicsView.DragMode.RubberBandDrag


def test_update_diagram_element_skips_branch_attachment_sync_while_loading() -> None:
    """
    Loading the schematic should not normalize saved branch attachments again.
    """
    stub = _UpdateDiagramStub(loading=True)
    device = object()
    graphic = object()

    SchematicWidget.update_diagram_element(stub,
                                           device=device,
                                           x=1.0,
                                           y=2.0,
                                           w=3.0,
                                           h=4.0,
                                           r=5.0,
                                           draw_labels=True,
                                           graphic_object=graphic)

    assert stub.diagram.sync_calls == list()
    assert stub.graphics_manager.registrations == [(device, graphic)]


def test_update_diagram_element_syncs_branch_attachments_outside_loading() -> None:
    """
    Normal runtime updates should still sync branch attachments.
    """
    stub = _UpdateDiagramStub(loading=False)
    device = object()

    SchematicWidget.update_diagram_element(stub,
                                           device=device,
                                           x=1.0,
                                           y=2.0,
                                           w=3.0,
                                           h=4.0,
                                           r=5.0,
                                           draw_labels=True,
                                           graphic_object=None)

    assert stub.diagram.sync_calls == [device]


def test_set_all_branch_drawing_styles_updates_all_registered_branch_widgets(override_attrs) -> None:
    """
    Applying one branch drawing style at widget level should fan out to every registered branch graphic.
    """
    graphics_manager = _BranchStyleGraphicsManagerStub()
    line_graphic = _BranchStyleLineGraphicStub()
    fluid_path_graphic = _BranchStyleLineGraphicStub()
    non_branch_graphic = _BranchStyleGraphicStub()
    stub = type("BranchStyleWidgetStub", (), {"graphics_manager": graphics_manager})()
    override_attrs.setattr(
        schematic_widget_module,
        "LineGraphicTemplateItem",
        _BranchStyleLineGraphicStub
    )
    graphics_manager.device_type_lists[DeviceType.LineDevice] = [line_graphic, non_branch_graphic]
    graphics_manager.device_type_lists[DeviceType.FluidPathDevice] = [fluid_path_graphic]

    SchematicWidget.set_all_branch_drawing_styles(stub, route_style=SchematicAutoRouteStyle.RETICULAR)

    assert line_graphic.styles == [SchematicAutoRouteStyle.RETICULAR]
    assert fluid_path_graphic.styles == [SchematicAutoRouteStyle.RETICULAR]
    assert non_branch_graphic.styles == list()


def test_add_api_winding_uses_visible_winding_terminal_bus() -> None:
    """
    Winding graphics should query the visible transformer terminal bus after the winding orientation flip.
    """
    visible_bus = Bus(name="Visible", Vnom=110.0)
    internal_bus = Bus(name="Internal", Vnom=1.0, is_internal=True)
    winding = Winding(bus_from=visible_bus, bus_to=internal_bus)
    stub = _WindingWidgetStub()

    result = SchematicWidget.add_api_winding(stub,
                                             branch=winding,
                                             from_port="from-port",
                                             draw_labels=True)

    assert result == "created-winding"
    assert stub.queried_buses == [visible_bus]
    assert stub.add_api_branch_call is not None
    assert stub.add_api_branch_call["to_port"] == "terminal"


def test_center_nodes_uses_full_scene_bounds() -> None:
    """
    Centering the view should use the full scene bounds, not just bus-like widgets.
    """
    stub = _CenterNodesWidgetStub(QRectF(10.0, 20.0, 200.0, 100.0))

    SchematicWidget.center_nodes(stub, margin_factor=0.1)

    assert len(stub.diagram_scene.set_rect_calls) == 1
    assert len(stub.editor_graphics_view.fit_calls) == 1
    assert stub.editor_graphics_view.scale_calls == [(1.0, 1.0)]

    rect = stub.diagram_scene.set_rect_calls[0]
    assert rect.x() == -10.0
    assert rect.y() == 10.0
    assert rect.width() == 240.0
    assert rect.height() == 120.0


def test_persist_selected_item_positions_updates_all_selected_movable_items() -> None:
    """
    Releasing a multi-selection drag should persist every moved item position.
    """
    first = _PersistSelectedGraphicStub(api_object="first",
                                        x=10.0,
                                        y=20.0,
                                        movable=True,
                                        scene_x=110.0,
                                        scene_y=120.0)
    second = _PersistSelectedGraphicStub(api_object="second",
                                         x=30.0,
                                         y=40.0,
                                         movable=True,
                                         scene_x=130.0,
                                         scene_y=140.0)
    ignored = _PersistSelectedGraphicStub(api_object="ignored", x=50.0, y=60.0, movable=False)
    stub = _PersistSelectedWidgetStub(selected_items=[first, second, ignored])

    SchematicWidget.persist_selected_item_positions(stub)

    assert len(stub.calls) == 2
    assert [call["device"] for call in stub.calls] == ["first", "second"]
    assert [(call["x"], call["y"]) for call in stub.calls] == [(110.0, 120.0), (130.0, 140.0)]


def test_repair_suspicious_injection_positions_repairs_legacy_local_coordinates(monkeypatch) -> None:
    """
    Legacy manual injection positions saved in owner-local space should be rewritten to scene space.
    """
    monkeypatch.setattr(schematic_widget_module, "InjectionTemplateGraphicItem", _RepairInjectionGraphicStub)
    owner = _RepairOwnerGraphicStub(scene_x=1000.0, scene_y=500.0)
    api_object = _RepairInjectionApiStub(device_type=DeviceType.LoadDevice)
    graphic = _RepairInjectionGraphicStub(api_object=api_object, parent=owner)
    location = _RepairLocationStub(x=50.0, y=80.0)
    diagram = _RepairDiagramStub(locations={api_object: location},
                                 docks={api_object: {"auto_layout": False}})
    graphics_manager = _RepairGraphicsManagerStub(graphics_by_type={DeviceType.LoadDevice: [graphic]})
    stub = _RepairWidgetStub(diagram=diagram, graphics_manager=graphics_manager)

    repaired_count = SchematicWidget.repair_suspicious_injection_positions(stub, multiplier=4.0)

    assert repaired_count == 1
    assert len(stub.calls) == 1
    assert (graphic._x, graphic._y) == (50.0, 80.0)
    assert (location.x, location.y) == (1050.0, 580.0)
    assert owner.arrange_calls == 1


def test_repair_suspicious_injection_positions_skips_valid_scene_coordinates(monkeypatch) -> None:
    """
    Already-correct manual scene coordinates should not be touched.
    """
    monkeypatch.setattr(schematic_widget_module, "InjectionTemplateGraphicItem", _RepairInjectionGraphicStub)
    owner = _RepairOwnerGraphicStub(scene_x=1000.0, scene_y=500.0)
    api_object = _RepairInjectionApiStub(device_type=DeviceType.LoadDevice)
    graphic = _RepairInjectionGraphicStub(api_object=api_object, parent=owner)
    location = _RepairLocationStub(x=1050.0, y=580.0)
    diagram = _RepairDiagramStub(locations={api_object: location},
                                 docks={api_object: {"auto_layout": False}})
    graphics_manager = _RepairGraphicsManagerStub(graphics_by_type={DeviceType.LoadDevice: [graphic]})
    stub = _RepairWidgetStub(diagram=diagram, graphics_manager=graphics_manager)

    repaired_count = SchematicWidget.repair_suspicious_injection_positions(stub, multiplier=4.0)

    assert repaired_count == 0
    assert len(stub.calls) == 0
    assert (location.x, location.y) == (1050.0, 580.0)
    assert owner.arrange_calls == 0


def test_repair_suspicious_injection_positions_repairs_when_wrong_scene_is_still_broadly_plausible(monkeypatch) -> None:
    """
    Legacy local coordinates should still be repaired when the scene-space interpretation falls inside the old wide box.
    """
    monkeypatch.setattr(schematic_widget_module, "InjectionTemplateGraphicItem", _RepairInjectionGraphicStub)
    owner = _RepairOwnerGraphicStub(scene_x=300.0, scene_y=100.0)
    api_object = _RepairInjectionApiStub(device_type=DeviceType.GeneratorDevice)
    graphic = _RepairInjectionGraphicStub(api_object=api_object, parent=owner)
    location = _RepairLocationStub(x=50.0, y=80.0)
    diagram = _RepairDiagramStub(locations={api_object: location},
                                 docks={api_object: {"auto_layout": False,
                                                     "side": "bottom",
                                                     "alignment": (50.0 + graphic.w * 0.5) / owner.w,
                                                     "offset": 40.0}})
    graphics_manager = _RepairGraphicsManagerStub(graphics_by_type={DeviceType.GeneratorDevice: [graphic]})
    stub = _RepairWidgetStub(diagram=diagram, graphics_manager=graphics_manager)

    repaired_count = SchematicWidget.repair_suspicious_injection_positions(stub, multiplier=4.0)

    assert repaired_count == 1
    assert len(stub.calls) == 1
    assert (location.x, location.y) == (350.0, 180.0)
    assert owner.arrange_calls == 1
