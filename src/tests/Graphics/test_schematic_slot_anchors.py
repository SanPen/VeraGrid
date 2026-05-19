import sys
from typing import Any

from PySide6 import QtWidgets
from PySide6.QtCore import QPointF

from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.slot_geometry import SchematicAttachmentSlot
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics_template import LineGraphicTemplateItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Fluid.fluid_node_graphics import FluidNodeGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Injections.load_graphics import LoadGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Substation.bus_graphics import BusGraphicItem
from VeraGridEngine.Devices.Diagrams.graphic_location import GraphicLocation
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Diagrams.schematic_diagram import SchematicDiagram
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Fluid.fluid_node import FluidNode
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import BusGraphicType, SchematicAutoRouteStyle, SchematicRouteKind


class _EditorStub:
    __slots__ = ("attachments", "diagram", "diagram_updates", "graphics_manager", "_is_loading_diagram",
                 "_is_batch_refreshing_branches")

    def __init__(self) -> None:
        """
        Initialize the editor stub attachment store.

        :return: ``None``.
        """
        self.attachments: dict[tuple[int, str], dict[str, Any]] = dict()
        self.diagram: _DiagramStub = _DiagramStub()
        self.diagram_updates: dict[int, dict[str, Any]] = dict()
        self.graphics_manager: _GraphicsManagerStub = _GraphicsManagerStub()
        self._is_loading_diagram: bool = False
        self._is_batch_refreshing_branches: bool = False

    def update_diagram_element(self,
                               device: Any,
                               x: float,
                               y: float,
                               w: float,
                               h: float,
                               r: float,
                               draw_labels: bool,
                               graphic_object: Any) -> None:
        """
        No-op compatibility stub for graphics tests.

        :param device: Unused.
        :param x: Unused.
        :param y: Unused.
        :param w: Unused.
        :param h: Unused.
        :param r: Unused.
        :param draw_labels: Unused.
        :param graphic_object: Unused.
        :return: ``None``.
        """
        self.diagram_updates[id(device)] = {
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "r": r,
            "draw_labels": draw_labels,
            "graphic_object": graphic_object,
        }
        self.diagram.update_graphic_location(api_object=device,
                                             x=x,
                                             y=y,
                                             h=h,
                                             w=w,
                                             r=r,
                                             draw_labels=draw_labels)
        return None

    def start_connection(self, terminal: Any) -> None:
        """
        No-op compatibility stub for terminal interactions.

        :param terminal: Unused.
        :return: ``None``.
        """
        return None

    def is_loading_diagram(self) -> bool:
        """
        Return the fake loading flag used by child placement helpers.

        :return: Loading flag.
        """
        return self._is_loading_diagram

    def is_batch_refreshing_branches(self) -> bool:
        """
        Return the fake batched-branch-refresh flag.

        :return: Batch-refresh flag.
        """
        return self._is_batch_refreshing_branches

    def add_to_scene(self, graphic_object: Any) -> None:
        """
        No-op compatibility stub for scene insertion.

        :param graphic_object: Unused.
        :return: ``None``.
        """
        return None

    def get_persisted_attachment(self, api_object: Any, endpoint: str) -> dict[str, Any]:
        """
        Return persisted attachment data for a fake branch endpoint.

        :param api_object: Branch API object.
        :param endpoint: Endpoint key.
        :return: Attachment dictionary.
        """
        return self.diagram.get_attachment(api_object=api_object, endpoint=endpoint)

    def set_persisted_attachment(self, api_object: Any, endpoint: str, attachment: dict[str, Any]) -> None:
        """
        Store persisted attachment data for a fake branch endpoint.

        :param api_object: Branch API object.
        :param endpoint: Endpoint key.
        :param attachment: Attachment dictionary.
        :return: ``None``.
        """
        self.attachments[(id(api_object), endpoint)] = dict(attachment)
        self.diagram.set_attachment(api_object=api_object, endpoint=endpoint, attachment=attachment)


class _BranchGraphicStub:
    __slots__ = ("api_object", "_from_parent", "_to_parent", "pos1", "pos2")

    def __init__(self,
                 api_object: Any,
                 from_parent: Any,
                 to_parent: Any,
                 pos1: QPointF | None = None,
                 pos2: QPointF | None = None) -> None:
        """
        Initialize the fake branch graphic endpoints.

        :param api_object: Branch API object.
        :param from_parent: From-end parent graphic.
        :param to_parent: To-end parent graphic.
        :return: ``None``.
        """
        self.api_object = api_object
        self._from_parent = from_parent
        self._to_parent = to_parent
        self.pos1 = QPointF(0.0, 0.0) if pos1 is None else pos1
        self.pos2 = QPointF(0.0, 0.0) if pos2 is None else pos2

    def get_terminal_from_parent(self) -> Any:
        """
        Return the stored from-end parent graphic.

        :return: Parent graphic.
        """
        return self._from_parent

    def get_terminal_to_parent(self) -> Any:
        """
        Return the stored to-end parent graphic.

        :return: Parent graphic.
        """
        return self._to_parent


class _GraphicsManagerStub:
    __slots__ = tuple()

    def add_device(self, elm: Any, graphic: Any) -> None:
        """
        Accept graphics-manager registrations during lightweight graphics tests.

        :param elm: Unused API object.
        :param graphic: Unused graphic object.
        :return: ``None``.
        """
        return None


class _DiagramStub:
    __slots__ = ("docks", "attachments", "locations")

    def __init__(self) -> None:
        """
        Initialize the diagram stub storage.

        :return: ``None``.
        """
        self.docks: dict[int, dict[str, Any]] = dict()
        self.attachments: dict[tuple[int, str], dict[str, Any]] = dict()
        self.locations: dict[int, GraphicLocation] = dict()

    def get_dock(self, api_object: Any) -> dict[str, Any]:
        """
        Return persisted dock metadata.

        :param api_object: Child API object.
        :return: Dock metadata.
        """
        return dict(self.docks.get(id(api_object), dict()))

    def set_dock(self, api_object: Any, dock: dict[str, Any]) -> None:
        """
        Store dock metadata.

        :param api_object: Child API object.
        :param dock: Dock metadata.
        :return: ``None``.
        """
        self.docks[id(api_object)] = dict(dock)

    def get_attachment(self, api_object: Any, endpoint: str) -> dict[str, Any]:
        """
        Return persisted attachment metadata.

        :param api_object: Branch API object.
        :param endpoint: Endpoint key.
        :return: Attachment metadata.
        """
        return dict(self.attachments.get((id(api_object), endpoint), dict()))

    def set_attachment(self, api_object: Any, endpoint: str, attachment: dict[str, Any]) -> None:
        """
        Store persisted attachment metadata.

        :param api_object: Branch API object.
        :param endpoint: Endpoint key.
        :param attachment: Attachment metadata.
        :return: ``None``.
        """
        self.attachments[(id(api_object), endpoint)] = dict(attachment)

    def sync_injection_dock(self, api_object: Any, owner_device: Any, side: str = "bottom") -> dict[str, Any]:
        """
        Emulate the schematic dock sync contract for graphics tests.

        :param api_object: Child API object.
        :param owner_device: Unused owner device.
        :param side: Default dock side.
        :return: Dock metadata.
        """
        dock = self.get_dock(api_object)
        bus_pos = api_object.get_bus_pos(owner_device)

        if "side" not in dock:
            dock["side"] = side
        else:
            pass

        if "offset" not in dock:
            dock["offset"] = 0.0
        else:
            pass

        if "order" not in dock:
            dock["order"] = bus_pos
        else:
            pass

        self.set_dock(api_object, dock)
        return dock

    def query_point(self, api_object: Any) -> GraphicLocation | None:
        """
        Return one stored graphic location.

        :param api_object: API object.
        :return: Graphic location or ``None``.
        """
        return self.locations.get(id(api_object), None)

    def update_graphic_location(self,
                                api_object: Any,
                                x: float,
                                y: float,
                                h: float,
                                w: float,
                                r: float,
                                draw_labels: bool = True) -> None:
        """
        Store one graphic location update.

        :param api_object: API object.
        :param x: Scene X coordinate.
        :param y: Scene Y coordinate.
        :param h: Height.
        :param w: Width.
        :param r: Rotation.
        :param draw_labels: Label flag.
        :return: ``None``.
        """
        self.locations[id(api_object)] = GraphicLocation(x=x,
                                                         y=y,
                                                         h=h,
                                                         w=w,
                                                         r=r,
                                                         draw_labels=draw_labels,
                                                         api_object=api_object)

    def set_branch_route_points(self,
                                api_object: Any,
                                points: list[tuple[float, float]],
                                kind: SchematicRouteKind | str,
                                locked: bool,
                                route_style: SchematicAutoRouteStyle | None = None) -> None:
        """
        Store branch route metadata for lightweight graphics tests.

        :param api_object: Branch API object.
        :param points: Route points.
        :param kind: Route kind.
        :param locked: Lock flag.
        :param route_style: Automatic route-style enum.
        :return: ``None``.
        """
        location = self.query_point(api_object)

        if location is None:
            location = GraphicLocation(api_object=api_object)
            self.locations[id(api_object)] = location
        else:
            pass

        location.poly_line = list(points)
        route_metadata: dict[str, Any] = {
            "points": list(points),
            "kind": kind,
            "locked": locked,
        }

        if route_style is None:
            existing_route: Any = None if location.layout_metadata is None else location.layout_metadata.get("route", None)

            if isinstance(existing_route, dict) and "route_style" in existing_route:
                route_metadata["route_style"] = existing_route["route_style"]
            else:
                pass
        else:
            route_metadata["route_style"] = route_style.value

        location.layout_metadata = {"route": route_metadata}

    def get_branch_auto_route_style(self, api_object: Any) -> SchematicAutoRouteStyle:
        """
        Return the stored automatic route style for one branch.

        :param api_object: Branch API object.
        :return: Branch-specific automatic route-style enum.
        """
        location: GraphicLocation | None = self.query_point(api_object)
        route_metadata: Any
        route_style_text: Any

        if location is None or location.layout_metadata is None:
            return SchematicAutoRouteStyle.STRAIGHT
        else:
            route_metadata = location.layout_metadata.get("route", None)

        if not isinstance(route_metadata, dict):
            return SchematicAutoRouteStyle.STRAIGHT
        else:
            route_style_text = route_metadata.get("route_style", None)

        if route_style_text == SchematicAutoRouteStyle.STRAIGHT.value:
            return SchematicAutoRouteStyle.STRAIGHT
        elif route_style_text == SchematicAutoRouteStyle.RETICULAR.value:
            return SchematicAutoRouteStyle.RETICULAR
        else:
            return SchematicAutoRouteStyle.STRAIGHT

    def set_branch_auto_route_style(self,
                                    api_object: Any,
                                    route_style: SchematicAutoRouteStyle) -> None:
        """
        Store one branch-specific automatic route style.

        :param api_object: Branch API object.
        :param route_style: Requested route-style enum.
        :return: ``None``.
        """
        location: GraphicLocation | None = self.query_point(api_object)
        route_metadata: dict[str, Any]

        if location is None:
            location = GraphicLocation(api_object=api_object)
            self.locations[id(api_object)] = location
        else:
            pass

        if location.layout_metadata is None:
            route_metadata = dict()
            location.layout_metadata = {"route": route_metadata}
        else:
            route_section: Any = location.layout_metadata.get("route", None)

            if isinstance(route_section, dict):
                route_metadata = dict(route_section)
            else:
                route_metadata = dict()

            location.layout_metadata["route"] = route_metadata

        route_metadata["route_style"] = route_style.value

    def should_preserve_branch_route_shape(self, api_object: Any) -> bool:
        """
        Return whether one stored branch route should preserve its saved shape.

        :param api_object: Branch API object.
        :return: Preservation flag.
        """
        location = self.query_point(api_object)

        if location is None:
            return False
        else:
            pass

        route = location.layout_metadata.get("route", None)

        if not isinstance(route, dict):
            return False
        else:
            pass

        if bool(route.get("locked", False)):
            return True
        elif str(route.get("kind", "")) == "manual-polyline":
            return True
        else:
            return False


class _ChildApiStub:
    __slots__ = ("_bus_pos",)

    def __init__(self, bus_pos: int) -> None:
        """
        Initialize the fake child API object.

        :param bus_pos: Bus order index.
        :return: ``None``.
        """
        self._bus_pos = bus_pos

    def get_bus_pos(self, bus: Any) -> int:
        """
        Return the configured bus order index.

        :param bus: Unused parent bus.
        :return: Bus order index.
        """
        return self._bus_pos


class _ChildGraphicStub:
    __slots__ = ("api_object", "w", "h", "_pos", "nexus_updates")

    def __init__(self, api_object: Any, w: float = 40.0, h: float = 40.0) -> None:
        """
        Initialize the fake docked child graphic.

        :param api_object: Child API object.
        :param w: Width.
        :param h: Height.
        :return: ``None``.
        """
        self.api_object = api_object
        self.w = w
        self.h = h
        self._pos = QPointF(0.0, 0.0)
        self.nexus_updates: list[tuple[float, float]] = list()

    def setPos(self, x: float, y: float) -> None:
        """
        Store the latest arranged position.

        :param x: X coordinate.
        :param y: Y coordinate.
        :return: ``None``.
        """
        self._pos = QPointF(float(x), float(y))

    def pos(self) -> Any:
        """
        Return the stored position.

        :return: Position object.
        """
        return self._pos

    def x(self) -> float:
        """
        Return the stored X coordinate.

        :return: X coordinate.
        """
        return float(self._pos.x())

    def y(self) -> float:
        """
        Return the stored Y coordinate.

        :return: Y coordinate.
        """
        return float(self._pos.y())

    def update_nexus(self, pos: Any) -> None:
        """
        Record nexus updates during arrangement.

        :param pos: Position.
        :return: ``None``.
        """
        self.nexus_updates.append((float(pos.x()), float(pos.y())))


class _BranchEditorStub:
    __slots__ = ("diagram", "_is_loading_diagram", "_is_batch_refreshing_branches")

    def __init__(self) -> None:
        """
        Initialize the branch editor stub with a real schematic diagram.

        :return: ``None``.
        """
        self.diagram: SchematicDiagram = SchematicDiagram(name="branch-test")
        self._is_loading_diagram: bool = False
        self._is_batch_refreshing_branches: bool = False

    def update_diagram_element(self,
                               device: Any,
                               x: float,
                               y: float,
                               w: float,
                               h: float,
                               r: float,
                               draw_labels: bool,
                               graphic_object: Any) -> None:
        """
        No-op compatibility stub for graphics tests.

        :param device: Unused.
        :param x: Unused.
        :param y: Unused.
        :param w: Unused.
        :param h: Unused.
        :param r: Unused.
        :param draw_labels: Unused.
        :param graphic_object: Unused.
        :return: ``None``.
        """
        return None

    def start_connection(self, terminal: Any) -> None:
        """
        No-op compatibility stub for terminal interactions.

        :param terminal: Unused.
        :return: ``None``.
        """
        return None

    def get_persisted_attachment(self, api_object: Any, endpoint: str) -> dict[str, Any]:
        """
        Return persisted attachment metadata for a branch endpoint.

        :param api_object: Branch API object.
        :param endpoint: Endpoint key.
        :return: Attachment dictionary.
        """
        return self.diagram.get_attachment(api_object=api_object, endpoint=endpoint)

    def set_editor_model(self, api_object: Any) -> None:
        """
        No-op compatibility stub for selection updates.

        :param api_object: Unused.
        :return: ``None``.
        """
        return None

    def is_loading_diagram(self) -> bool:
        """
        Return the simulated diagram loading flag.

        :return: Loading flag.
        """
        return self._is_loading_diagram

    def is_batch_refreshing_branches(self) -> bool:
        """
        Return the simulated batched-branch-refresh flag.

        :return: Batch-refresh flag.
        """
        return self._is_batch_refreshing_branches


def _get_app() -> QtWidgets.QApplication:
    """
    Get or create the Qt application used by graphics tests.

    :return: Qt application instance.
    """
    app: QtWidgets.QApplication | None = QtWidgets.QApplication.instance()

    if app is None:
        return QtWidgets.QApplication(sys.argv)
    else:
        return app


def _noop_callback(value: Any) -> None:
    """
    Ignore terminal callback updates in graphics tests.

    :param value: Unused scene point.
    :return: ``None``.
    """
    return None


def test_bus_graphic_slot_anchors_follow_named_edges() -> None:
    """
    Bus graphics should expose distinct scene anchors for named compatibility slots.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)

    left_anchor = graphic.get_terminal_anchor_by_key("left")
    right_anchor = graphic.get_terminal_anchor_by_key("right")
    top_anchor = graphic.get_terminal_anchor_by_key("top")

    assert left_anchor.x() == 12.0
    assert left_anchor.y() == 45.0
    assert right_anchor.x() == 168.0
    assert right_anchor.y() == 45.0
    assert top_anchor.x() == 90.0
    assert top_anchor.y() == 45.0


def test_connectivity_bus_anchors_collapse_to_center() -> None:
    """
    Connectivity-bus anchors should stay fixed at the dot center.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1", graphic_type=BusGraphicType.Connectivity)
    other_bus: Bus = Bus(name="B2")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=40.0, h=40.0, x=0.0, y=0.0)
    other_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=other_bus, w=180.0, h=40.0, x=220.0, y=0.0)
    line: Line = Line(name="L1", bus_from=bus, bus_to=other_bus)
    branch_graphic = LineGraphicTemplateItem(from_port=graphic.get_terminal(),
                                             to_port=other_graphic.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    left_anchor = graphic.get_terminal_anchor_by_key("left")
    right_anchor = graphic.get_terminal_anchor_by_key("right")
    top_anchor = graphic.get_terminal_anchor_by_key("top")
    center_anchor = graphic.mapToScene(graphic.rect().center())

    assert left_anchor == center_anchor
    assert right_anchor == center_anchor
    assert top_anchor == center_anchor

    branch_graphic.move_endpoint_alignment(endpoint="from", scene_pos=QPointF(-100.0, -100.0))

    moved_anchor = branch_graphic.get_endpoint_anchor(endpoint="from")

    assert moved_anchor == center_anchor


def test_manual_branch_route_is_not_rewritten_during_graphic_redraw() -> None:
    """
    Loading a manual branch polyline must not overwrite the saved route with live endpoint callbacks.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    editor.diagram.set_attachment(line, "from", {"side": "bottom", "slot": "bottom", "terminal_key": "bottom"})
    editor.diagram.set_attachment(line, "to", {"side": "bottom", "slot": "bottom", "terminal_key": "bottom"})
    editor.diagram.set_branch_route_points(api_object=line,
                                           points=[(10.0, 20.0), (40.0, 85.0), (95.0, 65.0)],
                                           kind="manual-polyline",
                                           locked=False)

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    location = editor.diagram.query_point(line)

    assert branch_graphic is not None
    assert location is not None
    assert location.poly_line == [(10.0, 20.0), (40.0, 85.0), (95.0, 65.0)]
    assert location.layout_metadata["route"]["points"] == [(10.0, 20.0), (40.0, 85.0), (95.0, 65.0)]
    assert location.layout_metadata["route"]["kind"] == "manual-polyline"


def test_saved_auto_branch_route_is_rendered_during_load() -> None:
    """
    Loading should render saved branch route points even when the route kind is automatic.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    editor._is_loading_diagram = True
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    editor.diagram.set_attachment(line, "from", {"side": "bottom", "slot": "bottom", "terminal_key": "bottom"})
    editor.diagram.set_attachment(line, "to", {"side": "bottom", "slot": "bottom", "terminal_key": "bottom"})
    editor.diagram.set_branch_route_points(api_object=line,
                                           points=[(90.0, 45.0), (90.0, 110.0), (330.0, 110.0), (330.0, 45.0)],
                                           kind="auto-polyline",
                                           locked=False)

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    assert branch_graphic.get_render_points() == [(90.0, 45.0), (90.0, 110.0), (390.0, 110.0), (390.0, 45.0)]


def test_auto_branch_route_uses_straight_branch_style() -> None:
    """
    Automatic branch routes should collapse to one segment when the branch style is straight.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    editor.diagram.set_branch_auto_route_style(api_object=line, route_style=SchematicAutoRouteStyle.STRAIGHT)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)
    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)
    render_points = branch_graphic.get_render_points()

    assert render_points == [(90.0, 45.0), (390.0, 45.0)]


def test_auto_branch_route_defaults_to_straight_style() -> None:
    """
    Automatic branch routes should be straight when no explicit branch style has been stored.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)
    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    assert branch_graphic.get_render_points() == [(90.0, 45.0), (390.0, 45.0)]


def test_loading_reattaches_saved_branch_route_to_live_endpoint_anchors() -> None:
    """
    Loading should replace saved route endpoints with the live anchor coordinates.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    editor._is_loading_diagram = True
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    editor.diagram.set_attachment(line,
                                  "from",
                                  {
                                      "anchor_x": 30.0,
                                      "anchor_y": 45.0,
                                      "anchor_auto": False,
                                  })
    editor.diagram.set_attachment(line,
                                  "to",
                                  {
                                      "anchor_x": 150.0,
                                      "anchor_y": 45.0,
                                      "anchor_auto": False,
                                  })
    editor.diagram.set_branch_route_points(api_object=line,
                                           points=[(90.0, 45.0), (90.0, 110.0), (330.0, 110.0), (330.0, 45.0)],
                                           kind="auto-polyline",
                                           locked=False)

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)
    render_points = branch_graphic.get_render_points()
    from_anchor = branch_graphic.get_endpoint_anchor(endpoint="from")
    to_anchor = branch_graphic.get_endpoint_anchor(endpoint="to")

    assert render_points[0] == (from_anchor.x(), from_anchor.y())
    assert render_points[-1] == (to_anchor.x(), to_anchor.y())
    assert render_points[0] == (30.0, 45.0)
    assert render_points[-1] == (450.0, 45.0)


def test_sync_attachment_coordinates_keeps_manual_bus_anchor_coordinates() -> None:
    """
    Route synchronization should preserve coordinate-based branch anchors on buses.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    editor.diagram.set_attachment(line,
                                  "from",
                                  {"side": "bottom", "slot": "bottom", "terminal_key": "bottom", "auto_slot": False})
    editor.diagram.set_attachment(line,
                                  "to",
                                  {"side": "bottom", "slot": "bottom", "terminal_key": "bottom"})

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    branch_graphic.sync_attachment_slots_to_diagram(render_points=[(90.0, 50.0), (20.0, 45.0), (360.0, 50.0)])

    from_attachment = editor.diagram.get_attachment(api_object=line, endpoint="from")

    assert from_attachment["anchor_x"] == 90.0
    assert from_attachment["anchor_y"] == 45.0


def test_move_endpoint_alignment_persists_local_bus_anchor_coordinates() -> None:
    """
    Moving the from-end alignment should persist coordinate-based anchor metadata.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    original_anchor = branch_graphic.get_endpoint_anchor(endpoint="from")
    branch_graphic.move_endpoint_alignment(endpoint="from", scene_pos=QPointF(30.0, 50.0))

    from_attachment = editor.diagram.get_attachment(api_object=line, endpoint="from")
    moved_anchor = branch_graphic.get_endpoint_anchor(endpoint="from")

    assert from_attachment["anchor_x"] == 30.0
    assert from_attachment["anchor_y"] == 45.0
    assert from_attachment["anchor_auto"] is False
    assert original_anchor.x() != moved_anchor.x()
    assert moved_anchor.x() == 30.0
    assert moved_anchor.y() == 45.0


def test_move_endpoint_alignment_replaces_legacy_slot_identity_with_anchor_coordinates() -> None:
    """
    Dragging a branch endpoint along a bar should persist coordinates even if legacy slot ids exist.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    editor.diagram.set_attachment(api_object=line,
                                  endpoint="from",
                                  attachment={"side": "bottom",
                                              "slot": "bus-bottom-1",
                                              "terminal_key": "bus-bottom-1",
                                              "order": 1})

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    branch_graphic.move_endpoint_alignment(endpoint="from", scene_pos=QPointF(60.0, 50.0))

    from_attachment = editor.diagram.get_attachment(api_object=line, endpoint="from")

    assert from_attachment["anchor_x"] == 60.0
    assert from_attachment["anchor_y"] == 45.0
    assert from_attachment["anchor_auto"] is False
    assert from_attachment["owner_device_id"] == bus_from.idtag
    assert from_attachment["owner_device_type"] == bus_from.device_type.value


def test_endpoint_alignment_handle_has_wide_hit_shape() -> None:
    """
    Endpoint handles should remain easy to drag even when they overlap the bus bar.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    handle = branch_graphic._endpoint_handles["from"]

    assert handle.contains(QPointF(9.0, 0.0))


def test_move_endpoint_alignment_ignores_stale_legacy_side_metadata() -> None:
    """
    Endpoint dragging should use projected coordinates instead of stale side metadata.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    editor.diagram.set_attachment(api_object=line,
                                  endpoint="from",
                                  attachment={"side": "left",
                                              "slot": "bottom",
                                              "terminal_key": "bottom",
                                              "auto_slot": False})

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    branch_graphic.move_endpoint_alignment(endpoint="from", scene_pos=QPointF(30.0, 50.0))

    from_attachment = editor.diagram.get_attachment(api_object=line, endpoint="from")
    moved_anchor = branch_graphic.get_endpoint_anchor(endpoint="from")

    assert from_attachment["anchor_x"] == 30.0
    assert from_attachment["anchor_y"] == 45.0
    assert from_attachment["anchor_auto"] is False
    assert moved_anchor.x() == 30.0
    assert moved_anchor.y() == 45.0


def test_move_route_vertex_keeps_manual_bus_endpoint_anchor_fixed() -> None:
    """
    Moving an interior branch vertex should not move a manually aligned bus endpoint.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    branch_graphic.move_endpoint_alignment(endpoint="from", scene_pos=QPointF(30.0, 50.0))
    anchored_before = branch_graphic.get_endpoint_anchor(endpoint="from")

    editor.diagram.set_branch_route_points(api_object=line,
                                           points=[(30.0, 45.0), (110.0, 95.0), (220.0, 80.0), (390.0, 45.0)],
                                           kind="manual-polyline",
                                           locked=False)
    branch_graphic.load_route_points_from_diagram()
    branch_graphic.move_route_vertex(vertex_index=1, scene_pos=QPointF(140.0, 120.0))

    anchored_after = branch_graphic.get_endpoint_anchor(endpoint="from")
    from_attachment = editor.diagram.get_attachment(api_object=line, endpoint="from")

    assert anchored_before == QPointF(30.0, 45.0)
    assert anchored_after == QPointF(30.0, 45.0)
    assert from_attachment["anchor_x"] == 30.0
    assert from_attachment["anchor_y"] == 45.0
    assert from_attachment["anchor_auto"] is False


def test_fluid_node_slot_anchors_follow_named_edges() -> None:
    """
    Fluid-node graphics should expose distinct scene anchors for named compatibility slots.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    node: FluidNode = FluidNode(name="N1")
    graphic: FluidNodeGraphicItem = FluidNodeGraphicItem(editor=editor, fluid_node=node, w=180.0, h=40.0, x=0.0, y=0.0)

    left_anchor = graphic.get_terminal_anchor_by_key("left")
    right_anchor = graphic.get_terminal_anchor_by_key("right")
    top_anchor = graphic.get_terminal_anchor_by_key("top")

    assert left_anchor.x() == 12.0
    assert left_anchor.y() == 45.0
    assert right_anchor.x() == 168.0
    assert right_anchor.y() == 45.0
    assert top_anchor.x() == 90.0
    assert top_anchor.y() == 45.0


def test_bus_graphic_terminal_slots_include_explicit_attached_slots() -> None:
    """
    Bus graphics should expose attached explicit slot ids in the slot catalog.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    other_bus: Bus = Bus(name="B2")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_api_object: object = object()
    branch_graphic: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object,
                                                            from_parent=graphic,
                                                            to_parent=other_bus)
    graphic.terminal.add_hosting_connection(branch_graphic, _noop_callback)
    editor.set_persisted_attachment(branch_api_object, "from", {"terminal_key": "bus-right-3"})

    slots = graphic.get_terminal_slots()

    assert "bus-right-3" in slots
    assert slots["bus-right-3"] == {"terminal_key": "bus-right-3", "side": "right"}


def test_bus_graphic_duplicate_explicit_orders_do_not_collapse_anchor_positions() -> None:
    """
    Duplicate explicit slot orders should still spread deterministically by branch identity.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    other_bus: Bus = Bus(name="B2")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_api_object_1: object = object()
    branch_api_object_2: object = object()
    branch_graphic_1: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object_1,
                                                              from_parent=graphic,
                                                              to_parent=other_bus)
    branch_graphic_2: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object_2,
                                                              from_parent=graphic,
                                                              to_parent=other_bus)
    graphic.terminal.add_hosting_connection(branch_graphic_1, _noop_callback)
    graphic.terminal.add_hosting_connection(branch_graphic_2, _noop_callback)
    editor.set_persisted_attachment(branch_api_object_1, "from", {"terminal_key": "bus-right-1"})
    editor.set_persisted_attachment(branch_api_object_2, "from", {"terminal_key": "bus-right-1"})

    anchor_1 = graphic.get_terminal_anchor_by_key("bus-right-1", graphic_object=branch_graphic_1)
    anchor_2 = graphic.get_terminal_anchor_by_key("bus-right-1", graphic_object=branch_graphic_2)

    assert anchor_1.x() == 168.0
    assert anchor_2.x() == 168.0
    assert anchor_1.y() != anchor_2.y()


def test_bus_graphic_detects_duplicate_explicit_slot_orders() -> None:
    """
    Duplicate explicit slot orders should be detectable for compatibility fallback.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    other_bus: Bus = Bus(name="B2")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_api_object_1: object = object()
    branch_api_object_2: object = object()
    branch_graphic_1: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object_1,
                                                              from_parent=graphic,
                                                              to_parent=other_bus)
    branch_graphic_2: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object_2,
                                                              from_parent=graphic,
                                                              to_parent=other_bus)
    graphic.terminal.add_hosting_connection(branch_graphic_1, _noop_callback)
    graphic.terminal.add_hosting_connection(branch_graphic_2, _noop_callback)
    editor.set_persisted_attachment(branch_api_object_1, "from", {"terminal_key": "bus-right-1"})
    editor.set_persisted_attachment(branch_api_object_2, "from", {"terminal_key": "bus-right-1"})

    assert graphic.has_duplicate_explicit_slot_order(side_key=SchematicAttachmentSlot.RIGHT, order=1) is True


def test_fluid_node_terminal_slots_include_explicit_attached_slots() -> None:
    """
    Fluid-node graphics should expose attached explicit slot ids in the slot catalog.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    node: FluidNode = FluidNode(name="N1")
    other_node: object = object()
    graphic: FluidNodeGraphicItem = FluidNodeGraphicItem(editor=editor, fluid_node=node, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_api_object: object = object()
    branch_graphic: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object,
                                                            from_parent=graphic,
                                                            to_parent=other_node)
    graphic._terminal.add_hosting_connection(branch_graphic, _noop_callback)
    editor.set_persisted_attachment(branch_api_object, "from", {"terminal_key": "fluid-right-2"})

    slots = graphic.get_terminal_slots()

    assert "fluid-right-2" in slots
    assert slots["fluid-right-2"] == {"terminal_key": "fluid-right-2", "side": "right"}


def test_bus_graphic_arrange_children_uses_persisted_dock_sides() -> None:
    """
    Bus graphics should place children according to persisted dock metadata.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)

    bottom_api = _ChildApiStub(bus_pos=1)
    top_api = _ChildApiStub(bus_pos=2)
    right_api = _ChildApiStub(bus_pos=3)
    bottom_child = _ChildGraphicStub(api_object=bottom_api)
    top_child = _ChildGraphicStub(api_object=top_api)
    right_child = _ChildGraphicStub(api_object=right_api)

    graphic._child_graphics = [bottom_child, top_child, right_child]
    editor.diagram.set_dock(bottom_api, {"side": "bottom", "order": 1, "offset": 5.0})
    editor.diagram.set_dock(top_api, {"side": "top", "order": 1, "offset": 10.0})
    editor.diagram.set_dock(right_api, {"side": "right", "order": 1, "offset": 15.0})

    graphic.arrange_children()

    assert bottom_child.y() == 85.0
    assert top_child.y() == -90.0
    assert right_child.x() == 235.0
    assert len(bottom_child.nexus_updates) == 1
    assert len(top_child.nexus_updates) == 1
    assert len(right_child.nexus_updates) == 1


def test_bus_graphic_arrange_children_uses_manual_dock_alignment() -> None:
    """
    Bus graphics should keep manually aligned child placement instead of recentering it.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)

    manual_api = _ChildApiStub(bus_pos=1)
    manual_child = _ChildGraphicStub(api_object=manual_api)
    graphic._child_graphics = [manual_child]
    editor.diagram.set_dock(manual_api,
                            {"side": "bottom",
                             "order": 1,
                             "offset": 12.0,
                             "alignment": 0.25,
                             "auto_layout": False})

    graphic.arrange_children()

    assert manual_child.x() == 25.0
    assert manual_child.y() == 92.0


def test_injection_graphic_sync_manual_dock_metadata_from_position() -> None:
    """
    Dragged injection graphics should persist manual dock side, alignment, and offset.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="LD1")
    load.bus = bus
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = LoadGraphicItem(parent=bus_graphic, api_obj=load, editor=editor)

    load_graphic.setPos(20.0, 96.0)
    load_graphic.sync_manual_dock_metadata_from_position()

    dock = editor.diagram.get_dock(load)

    assert dock["side"] == "bottom"
    assert dock["auto_layout"] is False
    assert dock["alignment"] == 1.0 / 6.0
    assert dock["offset"] == 16.0
    assert dock["anchor_x"] == 30.0
    assert dock["anchor_y"] == 45.0
    assert dock["anchor_auto"] is False


def test_injection_nexus_parent_endpoint_move_persists_parent_anchor_coordinates() -> None:
    """
    Moving the parent nexus endpoint should persist explicit parent anchor coordinates.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="LD1")
    load.bus = bus
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = LoadGraphicItem(parent=bus_graphic, api_obj=load, editor=editor)

    load_graphic.move_nexus_endpoint_alignment(endpoint="parent", scene_pos=QPointF(30.0, 80.0))

    dock = editor.diagram.get_dock(load)
    parent_anchor = load_graphic.get_parent_nexus_anchor()

    assert dock["anchor_x"] == 30.0
    assert dock["anchor_y"] == 45.0
    assert dock["anchor_auto"] is False
    assert parent_anchor.x() == 30.0
    assert parent_anchor.y() == 45.0


def test_moving_injection_preserves_manual_child_nexus_anchor() -> None:
    """
    Moving the injection glyph must not overwrite one manually aligned child nexus anchor.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="LD1")
    load.bus = bus
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = LoadGraphicItem(parent=bus_graphic, api_obj=load, editor=editor)

    load_graphic.move_nexus_endpoint_alignment(endpoint="child", scene_pos=QPointF(10.0, 120.0))
    dock_before = editor.diagram.get_dock(load)
    child_anchor_x_before: float = float(dock_before["child_anchor_x"])
    child_anchor_y_before: float = float(dock_before["child_anchor_y"])

    load_graphic.setPos(40.0, 110.0)
    load_graphic.sync_manual_dock_metadata_from_position()

    dock_after = editor.diagram.get_dock(load)
    child_anchor_scene = load_graphic.get_child_nexus_anchor()
    nexus_path = load_graphic.nexus.path()
    nexus_start = nexus_path.elementAt(0)

    assert dock_after["child_anchor_x"] == child_anchor_x_before
    assert dock_after["child_anchor_y"] == child_anchor_y_before
    assert child_anchor_scene == load_graphic.mapToScene(QPointF(child_anchor_x_before, child_anchor_y_before))
    assert float(nexus_start.x) == child_anchor_scene.x()
    assert float(nexus_start.y) == child_anchor_scene.y()


def test_injection_base_context_menu_only_exposes_rotate_not_dock_move() -> None:
    """
    Injection base menus should remove dock/move actions and expose only rotation.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="LD1")
    load.bus = bus
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = LoadGraphicItem(parent=graphic, api_obj=load, editor=editor)

    menu = load_graphic.get_base_context_menu()
    action_texts = [action.text() for action in menu.actions()]

    assert "Rotate 90" in action_texts
    assert "Dock top" not in action_texts
    assert "Dock bottom" not in action_texts
    assert "Dock left" not in action_texts
    assert "Dock right" not in action_texts
    assert "Move earlier" not in action_texts
    assert "Move later" not in action_texts
    assert "Move outward" not in action_texts
    assert "Move inward" not in action_texts


def test_injection_rotate_90_persists_angle_and_child_load_restores_it() -> None:
    """
    Rotating one injection should persist its angle and restore it when the child graphic is recreated.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="LD1")
    load.bus = bus
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = LoadGraphicItem(parent=bus_graphic, api_obj=load, editor=editor)

    load_graphic.rotate_90()

    update_record = editor.diagram_updates[id(load)]

    assert load_graphic.rotation() == 90.0
    assert load_graphic.transformOriginPoint() == QPointF(float(load_graphic.w) * 0.5,
                                                          float(load_graphic.h) * 0.5)
    assert update_record["r"] == 90.0

    editor.diagram.update_graphic_location(api_object=load,
                                           x=0.0,
                                           y=0.0,
                                           h=float(load_graphic.h),
                                           w=float(load_graphic.w),
                                           r=90.0,
                                           draw_labels=True)

    recreated_bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    recreated_load_graphic = recreated_bus_graphic.add_load(api_obj=load)

    assert recreated_load_graphic.rotation() == 90.0


def test_rotated_injection_child_nexus_anchor_uses_item_transform() -> None:
    """
    Rotated injection child anchors should follow the child transform instead of an axis-aligned box.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="LD1")
    load.bus = bus
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = LoadGraphicItem(parent=bus_graphic, api_obj=load, editor=editor)

    load_graphic.setRotation(90.0)

    child_anchor = load_graphic.get_child_nexus_anchor()
    expected_anchor = load_graphic.mapToScene(load_graphic.get_child_anchor_local_point_from_dock(load_graphic.get_dock_metadata()))

    assert child_anchor == expected_anchor


def test_rotated_injection_nexus_path_survives_recreation() -> None:
    """
    Recreated rotated injections should rebuild the nexus path from the restored rotation.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="LD1")
    load.bus = bus
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = LoadGraphicItem(parent=bus_graphic, api_obj=load, editor=editor)

    load_graphic.rotate_90()

    editor.diagram.update_graphic_location(api_object=load,
                                           x=0.0,
                                           y=0.0,
                                           h=float(load_graphic.h),
                                           w=float(load_graphic.w),
                                           r=90.0,
                                           draw_labels=True)

    recreated_bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    recreated_load_graphic: LoadGraphicItem = recreated_bus_graphic.add_load(api_obj=load)
    child_anchor = recreated_load_graphic.get_child_nexus_anchor()
    nexus_path = recreated_load_graphic.nexus.path()
    nexus_start = nexus_path.elementAt(0)

    assert recreated_load_graphic.rotation() == 90.0
    assert child_anchor == recreated_load_graphic.mapToScene(
        recreated_load_graphic.get_child_anchor_local_point_from_dock(recreated_load_graphic.get_dock_metadata())
    )
    assert float(nexus_start.x) == child_anchor.x()
    assert float(nexus_start.y) == child_anchor.y()


def test_loading_rebuilds_auto_nexus_route_from_rotated_injection_anchors() -> None:
    """
    Loading should rebuild automatic nexus routes from the restored rotated child anchor.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    editor._is_loading_diagram = True
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="LD1")
    load.bus = bus
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    editor.diagram.set_dock(load,
                            {
                                "side": "bottom",
                                "alignment": 0.5,
                                "offset": 0.0,
                                "nexus_parent_alignment": 0.5,
                                "nexus_child_alignment": 0.5,
                                "nexus_route_kind": "auto-polyline",
                                "nexus_route_points": [(80.0, 120.0), (120.0, 120.0), (120.0, 45.0), (90.0, 45.0)],
                            })
    editor.diagram.update_graphic_location(api_object=load,
                                           x=0.0,
                                           y=100.0,
                                           h=40.0,
                                           w=40.0,
                                           r=90.0,
                                           draw_labels=True)

    load_graphic: LoadGraphicItem = bus_graphic.add_load(api_obj=load)
    expected_start = load_graphic.get_child_nexus_anchor()
    render_points = load_graphic.get_nexus_render_points()

    assert render_points != [(80.0, 120.0), (120.0, 120.0), (120.0, 45.0), (90.0, 45.0)]
    assert render_points[0] == (expected_start.x(), expected_start.y())


def test_loading_preserves_manual_nexus_route_shape_for_rotated_injection() -> None:
    """
    Loading should still preserve manual nexus paths for rotated injections.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    editor._is_loading_diagram = True
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="LD1")
    load.bus = bus
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    editor.diagram.set_dock(load,
                            {
                                "side": "bottom",
                                "alignment": 0.5,
                                "offset": 0.0,
                                "nexus_parent_alignment": 0.5,
                                "nexus_child_alignment": 0.5,
                                "nexus_route_kind": "manual-polyline",
                                "nexus_route_points": [(80.0, 120.0), (120.0, 120.0), (120.0, 45.0), (90.0, 45.0)],
                            })
    editor.diagram.update_graphic_location(api_object=load,
                                           x=0.0,
                                           y=100.0,
                                           h=40.0,
                                           w=40.0,
                                           r=90.0,
                                           draw_labels=True)

    load_graphic: LoadGraphicItem = bus_graphic.add_load(api_obj=load)
    render_points = load_graphic.get_nexus_render_points()
    expected_start = load_graphic.get_child_nexus_anchor()
    expected_end = load_graphic.get_parent_nexus_anchor()

    assert render_points[0] == (expected_start.x(), expected_start.y())
    assert render_points[-1] == (expected_end.x(), expected_end.y())
    assert len(render_points) == 4
    assert render_points[1] != (80.0, 120.0)
    assert render_points[2][1] == 45.0
    assert render_points[2][0] != 120.0


def test_bus_graphic_nexus_point_for_child_uses_dock_side() -> None:
    """
    Bus nexus anchors should follow the dock side of each child.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    left_api = _ChildApiStub(bus_pos=1)
    left_child = _ChildGraphicStub(api_object=left_api)
    left_child.setPos(-80.0, 20.0)
    editor.diagram.set_dock(left_api, {"side": "left", "order": 1, "offset": 0.0})

    nexus_point = graphic.get_nexus_point_for_child(left_child)

    assert nexus_point.x() == 12.0
    assert nexus_point.y() == 45.0


def test_bus_graphic_auto_assign_branch_slots_uses_geometry_order() -> None:
    """
    Bus graphics should assign explicit branch slots deterministically from scene geometry.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    other_bus: Bus = Bus(name="B2")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_api_object_1: object = object()
    branch_api_object_2: object = object()
    branch_graphic_1: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object_1,
                                                              from_parent=graphic,
                                                              to_parent=other_bus,
                                                              pos1=QPointF(90.0, 25.0),
                                                              pos2=QPointF(40.0, 220.0))
    branch_graphic_2: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object_2,
                                                              from_parent=graphic,
                                                              to_parent=other_bus,
                                                              pos1=QPointF(90.0, 25.0),
                                                              pos2=QPointF(140.0, 220.0))
    graphic.terminal.add_hosting_connection(branch_graphic_1, _noop_callback)
    graphic.terminal.add_hosting_connection(branch_graphic_2, _noop_callback)

    graphic.auto_assign_branch_slots()

    assert editor.diagram.get_attachment(branch_api_object_1, "from")["slot"] == "bus-bottom-1"
    assert editor.diagram.get_attachment(branch_api_object_2, "from")["slot"] == "bus-bottom-2"
    assert editor.diagram.get_attachment(branch_api_object_1, "from")["auto_slot"] is True
    assert editor.diagram.get_attachment(branch_api_object_2, "from")["auto_slot"] is True
    assert editor.diagram.get_attachment(branch_api_object_1, "from")["anchor_x"] == 40.0
    assert editor.diagram.get_attachment(branch_api_object_2, "from")["anchor_x"] == 140.0
    assert editor.diagram.get_attachment(branch_api_object_1, "from")["anchor_y"] == 45.0
    assert editor.diagram.get_attachment(branch_api_object_2, "from")["anchor_y"] == 45.0


def test_bus_graphic_auto_assign_branch_slots_ignores_connector_without_api_object() -> None:
    """
    Auto slot assignment should skip connector graphics that do not have one diagram API object.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    other_bus: Bus = Bus(name="B2")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_api_object: object = object()
    branch_graphic: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object,
                                                            from_parent=graphic,
                                                            to_parent=other_bus,
                                                            pos1=QPointF(90.0, 25.0),
                                                            pos2=QPointF(40.0, 220.0))
    connector_graphic: _BranchGraphicStub = _BranchGraphicStub(api_object=None,
                                                               from_parent=graphic,
                                                               to_parent=other_bus,
                                                               pos1=QPointF(90.0, 25.0),
                                                               pos2=QPointF(140.0, 220.0))
    graphic.terminal.add_hosting_connection(branch_graphic, _noop_callback)
    graphic.terminal.add_hosting_connection(connector_graphic, _noop_callback)

    graphic.auto_assign_branch_slots()

    assert editor.diagram.get_attachment(branch_api_object, "from")["slot"] == "bus-bottom-1"


def test_bus_graphic_applies_persisted_rotation_to_bar_and_nexus_anchors() -> None:
    """
    Bus graphics should apply the stored diagram rotation angle to branch and nexus anchors.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0, r=90.0)

    bar_anchor = graphic.get_terminal_anchor_by_key("bottom", alignment=0.5)
    nexus_anchor = graphic.get_nexus_point()
    recovered_alignment = graphic.get_terminal_alignment_from_scene_point(side_key="bottom",
                                                                          scene_point=bar_anchor)

    assert graphic.rotation() == 90.0
    assert graphic.r == 90.0
    assert graphic.transformOriginPoint() == graphic.get_rotation_origin_local_point()
    assert graphic.transformOriginPoint() == graphic.rect().center()
    assert bar_anchor.x() == 65.0
    assert bar_anchor.y() == 20.0
    assert nexus_anchor == bar_anchor
    assert recovered_alignment == 0.5


def test_bus_graphic_auto_assign_branch_slots_prefers_vertical_feeders_for_bar_buses() -> None:
    """
    Bar-style buses should default to top/bottom feeder slots instead of end-of-bar anchors.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    other_bus: Bus = Bus(name="B2")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_api_object: object = object()
    branch_graphic: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object,
                                                            from_parent=graphic,
                                                            to_parent=other_bus,
                                                            pos1=QPointF(90.0, 25.0),
                                                            pos2=QPointF(260.0, 35.0))
    graphic.terminal.add_hosting_connection(branch_graphic, _noop_callback)

    graphic.auto_assign_branch_slots()

    assert editor.diagram.get_attachment(branch_api_object, "from")["side"] == "top"
    assert editor.diagram.get_attachment(branch_api_object, "from")["slot"] == "bus-top-1"
    assert editor.diagram.get_attachment(branch_api_object, "from")["anchor_x"] == 168.0
    assert editor.diagram.get_attachment(branch_api_object, "from")["anchor_y"] == 45.0


def test_bus_graphic_auto_assign_branch_slots_preserves_manual_canonical_side() -> None:
    """
    Manual canonical endpoint placement should not be converted back to auto explicit slots.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus: Bus = Bus(name="B1")
    other_bus: Bus = Bus(name="B2")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_api_object: object = object()
    branch_graphic: _BranchGraphicStub = _BranchGraphicStub(api_object=branch_api_object,
                                                            from_parent=graphic,
                                                            to_parent=other_bus,
                                                            pos1=QPointF(90.0, 50.0),
                                                            pos2=QPointF(40.0, 200.0))
    graphic.terminal.add_hosting_connection(branch_graphic, _noop_callback)
    editor.set_persisted_attachment(branch_api_object,
                                    "from",
                                    {"side": "bottom", "slot": "bottom", "terminal_key": "bottom", "auto_slot": False})

    graphic.auto_assign_branch_slots()

    assert editor.diagram.get_attachment(branch_api_object, "from") == {
        "side": "bottom",
        "slot": "bottom",
        "terminal_key": "bottom",
        "auto_slot": False,
    }


def test_bus_graphic_auto_assign_branch_slots_preserves_saved_manual_route_endpoints_on_load() -> None:
    """
    Loading a saved manual branch route should not reassign its stored endpoint slot identity.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    editor._is_loading_diagram = True
    bus: Bus = Bus(name="B1")
    other_bus: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus, bus_to=other_bus)
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_graphic: _BranchGraphicStub = _BranchGraphicStub(api_object=line,
                                                            from_parent=graphic,
                                                            to_parent=other_bus,
                                                            pos1=QPointF(90.0, 50.0),
                                                            pos2=QPointF(40.0, 200.0))
    graphic.terminal.add_hosting_connection(branch_graphic, _noop_callback)
    editor.diagram.set_attachment(api_object=line,
                                  endpoint="from",
                                  attachment={"side": "bottom",
                                              "slot": "bus-bottom-3",
                                              "terminal_key": "bus-bottom-3",
                                              "order": 3,
                                              "auto_slot": True})
    editor.diagram.set_branch_route_points(api_object=line,
                                           points=[(90.0, 45.0), (90.0, 120.0), (40.0, 120.0), (40.0, 200.0)],
                                           kind="manual-polyline",
                                           locked=False)

    graphic.auto_assign_branch_slots()

    assert editor.diagram.get_attachment(line, "from") == {
        "side": "bottom",
        "slot": "bus-bottom-3",
        "terminal_key": "bus-bottom-3",
        "order": 3,
        "auto_slot": True,
    }


def test_bus_graphic_auto_assign_branch_slots_preserves_saved_endpoints_on_load_even_for_auto_routes() -> None:
    """
    Loading a saved branch should not recalculate endpoint slots just because its route kind is automatic.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    editor._is_loading_diagram = True
    bus: Bus = Bus(name="B1")
    other_bus: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus, bus_to=other_bus)
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    branch_graphic: _BranchGraphicStub = _BranchGraphicStub(api_object=line,
                                                            from_parent=graphic,
                                                            to_parent=other_bus,
                                                            pos1=QPointF(90.0, 50.0),
                                                            pos2=QPointF(40.0, 200.0))
    graphic.terminal.add_hosting_connection(branch_graphic, _noop_callback)
    editor.diagram.set_attachment(api_object=line,
                                  endpoint="from",
                                  attachment={"side": "bottom",
                                              "slot": "bus-bottom-5",
                                              "terminal_key": "bus-bottom-5",
                                              "order": 5,
                                              "auto_slot": True})

    graphic.auto_assign_branch_slots()

    assert editor.diagram.get_attachment(line, "from") == {
        "side": "bottom",
        "slot": "bus-bottom-5",
        "terminal_key": "bus-bottom-5",
        "order": 5,
        "auto_slot": True,
    }


def test_branch_scene_index_tracks_redraw_bounds_after_route_change() -> None:
    """
    Branch hit testing should follow the latest rendered route after redraw.

    This exercises the scene-index invalidation path for the routed controller
    item. If the item changes its path-based bounds without notifying the
    scene, clicks at the new route location can miss and stale pixels can
    remain after redraw.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=220.0, y=0.0)
    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=None)

    scene.addItem(graphic_from)
    scene.addItem(graphic_to)
    scene.addItem(branch_graphic)

    initial_probe: QPointF = QPointF(120.0, 45.0)
    moved_probe: QPointF = QPointF(480.0, 190.0)

    initial_hit_items = scene.items(initial_probe)
    moved_hit_items_before = scene.items(moved_probe)

    branch_graphic.setBeginPos(QPointF(90.0, 45.0))
    branch_graphic.setEndPos(QPointF(540.0, 210.0))

    moved_hit_items_after = scene.items(moved_probe)

    assert branch_graphic in initial_hit_items
    assert branch_graphic not in moved_hit_items_before
    assert branch_graphic in moved_hit_items_after


def test_branch_endpoint_callback_skips_immediate_redraw_during_batched_refresh(override_attrs) -> None:
    """
    Batched branch refresh should collect endpoint updates without redrawing on every callback.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=220.0, y=0.0)
    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)
    redraw_calls: list[int] = list()

    def _fake_redraw() -> None:
        """
        Record redraw invocations.

        :return: ``None``.
        """
        redraw_calls.append(1)

    override_attrs.setattr(branch_graphic, "redraw", _fake_redraw)

    editor._is_batch_refreshing_branches = True
    branch_graphic.setBeginPos(QPointF(100.0, 45.0))
    branch_graphic.setEndPos(QPointF(320.0, 45.0))

    assert branch_graphic.pos1 == QPointF(100.0, 45.0)
    assert branch_graphic.pos2 == QPointF(320.0, 45.0)
    assert redraw_calls == list()

    editor._is_batch_refreshing_branches = False
    branch_graphic.setBeginPos(QPointF(110.0, 45.0))

    assert redraw_calls == [1]


def test_line_graphic_constructor_skips_redraw_while_loading(override_attrs) -> None:
    """
    Branch construction during diagram loading should defer the first redraw.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    editor._is_loading_diagram = True
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=220.0, y=0.0)
    redraw_calls: list[int] = list()

    def _fake_redraw(self: LineGraphicTemplateItem) -> None:
        """
        Record constructor redraw attempts.

        :param self: Branch graphic instance.
        :return: ``None``.
        """
        redraw_calls.append(1)

    override_attrs.setattr(LineGraphicTemplateItem, "redraw", _fake_redraw)

    LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                            to_port=graphic_to.get_terminal(),
                            editor=editor)

    assert redraw_calls == list()


def test_bus_arrange_children_skips_intermediate_callback_churn_while_loading(override_attrs) -> None:
    """
    Bus child arrangement should avoid nexus and terminal callback refreshes during loading.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    editor._is_loading_diagram = True
    bus: Bus = Bus(name="B")
    load: Load = Load(name="L")
    graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = graphic.add_load(api_obj=load)
    nexus_calls: list[int] = list()
    callback_calls: list[int] = list()

    def _fake_update_nexus(position: QPointF) -> None:
        """
        Record nexus refresh attempts.

        :param position: Child position.
        :return: ``None``.
        """
        nexus_calls.append(1)

    def _fake_process_callbacks(position: QPointF) -> None:
        """
        Record terminal callback attempts.

        :param position: Terminal scene position.
        :return: ``None``.
        """
        callback_calls.append(1)

    override_attrs.setattr(load_graphic, "update_nexus", _fake_update_nexus)
    override_attrs.setattr(graphic.get_terminal(), "process_callbacks", _fake_process_callbacks)

    graphic.arrange_children()

    assert nexus_calls == list()
    assert callback_calls == list()

    editor._is_loading_diagram = False
    graphic.arrange_children()

    assert nexus_calls == [1]
    assert callback_calls == [1]


def test_terminal_reassignment_updates_branch_endpoint_port_reference() -> None:
    """
    Reassigning a branch terminal must update the branch endpoint port object.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    bus_new: Bus = Bus(name="B3")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=220.0, y=0.0)
    graphic_new: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_new, w=180.0, h=40.0, x=440.0, y=0.0)
    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)

    graphic_new.get_terminal().reassign_terminal(graphic_obj=branch_graphic,
                                                 another_terminal=graphic_from.get_terminal())

    assert branch_graphic.get_terminal_from() is graphic_new.get_terminal()
    assert branch_graphic in graphic_new.get_terminal().get_hosted_graphics()
    assert branch_graphic not in graphic_from.get_terminal().get_hosted_graphics()


def test_plain_branch_selection_does_not_activate_route_handles() -> None:
    """
    Rubber-band or programmatic selection alone must not surface branch edit handles.
    """
    _get_app()
    editor: _BranchEditorStub = _BranchEditorStub()
    scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene()
    bus_from: Bus = Bus(name="B1")
    bus_to: Bus = Bus(name="B2")
    line: Line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    graphic_from: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_from, w=180.0, h=40.0, x=0.0, y=0.0)
    graphic_to: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_to, w=180.0, h=40.0, x=300.0, y=0.0)

    scene.addItem(graphic_from)
    scene.addItem(graphic_to)

    editor.diagram.set_attachment(line, "from", {"side": "bottom", "slot": "bottom", "terminal_key": "bottom"})
    editor.diagram.set_attachment(line, "to", {"side": "bottom", "slot": "bottom", "terminal_key": "bottom"})
    editor.diagram.set_branch_route_points(api_object=line,
                                           points=[(90.0, 45.0), (90.0, 110.0), (390.0, 110.0), (390.0, 45.0)],
                                           kind="manual-polyline",
                                           locked=False)

    branch_graphic = LineGraphicTemplateItem(from_port=graphic_from.get_terminal(),
                                             to_port=graphic_to.get_terminal(),
                                             editor=editor,
                                             api_object=line)
    scene.addItem(branch_graphic)

    branch_graphic.setSelected(True)
    branch_graphic.refresh_route_handles()

    assert len(branch_graphic._route_handles) > 0
    assert all(not handle.isVisible() for handle in branch_graphic._route_handles)
    assert all(not handle.isVisible() for handle in branch_graphic._vertex_handles)
    assert all(not handle.isVisible() for handle in branch_graphic._endpoint_handles.values())

    branch_graphic.set_route_edit_active(True)

    assert all(handle.isVisible() for handle in branch_graphic._route_handles)
    assert all(handle.isVisible() for handle in branch_graphic._vertex_handles)
    assert all(handle.isVisible() for handle in branch_graphic._endpoint_handles.values())


def test_plain_injection_selection_does_not_activate_nexus_handles() -> None:
    """
    Selecting one injection without clicking into edit mode must keep nexus handles hidden.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene()
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="L1")
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = LoadGraphicItem(parent=bus_graphic, api_obj=load, editor=editor)

    scene.addItem(bus_graphic)
    scene.addItem(load_graphic.nexus)
    load_graphic.update_nexus(load_graphic.scenePos())
    load_graphic.setSelected(True)
    load_graphic.refresh_nexus_handles()

    assert not load_graphic._nexus_endpoint_handles["child"].isVisible()
    assert not load_graphic._nexus_endpoint_handles["parent"].isVisible()

    load_graphic.set_nexus_edit_active(True)

    assert load_graphic._nexus_endpoint_handles["child"].isVisible()
    assert load_graphic._nexus_endpoint_handles["parent"].isVisible()


def test_glyph_interaction_clears_nexus_edit_and_restores_movement() -> None:
    """
    Starting a normal glyph interaction must leave nexus edit mode so the
    injection remains draggable.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene()
    bus: Bus = Bus(name="B1")
    load: Load = Load(name="L1")
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus, w=180.0, h=40.0, x=0.0, y=0.0)
    load_graphic: LoadGraphicItem = LoadGraphicItem(parent=bus_graphic, api_obj=load, editor=editor)

    scene.addItem(bus_graphic)
    scene.addItem(load_graphic.nexus)
    load_graphic.setSelected(True)
    load_graphic.set_nexus_edit_active(True)

    assert load_graphic.is_nexus_edit_active()
    assert not bool(load_graphic.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

    load_graphic.prepare_for_glyph_interaction()

    assert not load_graphic.is_nexus_edit_active()
    assert bool(load_graphic.flags() & QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
