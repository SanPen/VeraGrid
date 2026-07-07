import sys
from typing import Any

from PySide6 import QtWidgets
from PySide6.QtCore import QPointF

import VeraGrid.Gui.Diagrams.SchematicWidget.Branches.vsc_graphics_3term as vsc_graphics_3term_module
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics_template import LineGraphicTemplateItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.vsc_graphics_3term import VscGraphicItem3Term
from VeraGrid.Gui.Diagrams.SchematicWidget.Substation.bus_graphics import BusGraphicItem
from VeraGridEngine.Devices.Branches.vsc import VSC
from VeraGridEngine.Devices.Diagrams.schematic_diagram import SchematicDiagram
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import SchematicAutoRouteStyle


class _EditorStub:
    __slots__ = ("diagram_updates", "diagram", "_is_loading_diagram", "_is_batch_refreshing_branches")

    def __init__(self) -> None:
        """
        Initialize the lightweight editor stub used by VSC graphics tests.

        :return: ``None``.
        """
        self.diagram_updates: list[dict[str, Any]] = list()
        self.diagram: SchematicDiagram = SchematicDiagram(name="vsc-3term-test")
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
        Record diagram persistence updates requested by the graphics item.

        :param device: Updated API object.
        :param x: Scene x coordinate.
        :param y: Scene y coordinate.
        :param w: Graphic width.
        :param h: Graphic height.
        :param r: Rotation angle.
        :param draw_labels: Label flag.
        :param graphic_object: Graphic object.
        :return: ``None``.
        """
        self.diagram_updates.append({
            "device": device,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "r": r,
            "draw_labels": draw_labels,
            "graphic_object": graphic_object,
        })
        self.diagram.update_graphic_location(api_object=device,
                                             x=x,
                                             y=y,
                                             h=h,
                                             w=w,
                                             r=r,
                                             draw_labels=draw_labels)

    def set_editor_model(self, api_object: Any) -> None:
        """
        No-op compatibility stub for selection updates.

        :param api_object: Unused API object.
        :return: ``None``.
        """
        return None

    def update_label_drwaing_status(self, device: Any, draw_labels: bool) -> None:
        """
        No-op compatibility stub for GenericDiagramWidget label updates.

        :param device: Unused API object.
        :param draw_labels: Unused label flag.
        :return: ``None``.
        """
        return None

    def set_rate_to_profile(self, api_object: Any) -> None:
        """
        No-op compatibility stub for profile actions.

        :param api_object: Unused API object.
        :return: ``None``.
        """
        return None

    def set_active_status_to_profile(self, api_object: Any) -> None:
        """
        No-op compatibility stub for profile actions.

        :param api_object: Unused API object.
        :return: ``None``.
        """
        return None

    def start_connection(self, terminal: Any) -> None:
        """
        No-op compatibility stub for terminal interactions.

        :param terminal: Unused terminal.
        :return: ``None``.
        """
        return None

    def get_persisted_attachment(self, api_object: Any, endpoint: str) -> dict[str, Any]:
        """
        Return persisted attachment metadata for branch-graphics compatibility.

        :param api_object: Branch API object.
        :param endpoint: Endpoint key.
        :return: Attachment metadata.
        """
        return self.diagram.get_attachment(api_object=api_object, endpoint=endpoint)

    def is_loading_diagram(self) -> bool:
        """
        Return the loading flag expected by graphics code.

        :return: Loading flag.
        """
        return self._is_loading_diagram

    def is_batch_refreshing_branches(self) -> bool:
        """
        Return the batched-branch-refresh flag expected by graphics code.

        :return: Batch-refresh flag.
        """
        return self._is_batch_refreshing_branches


class _ContextMenuEventStub:
    __slots__ = tuple()

    def screenPos(self) -> QPointF:
        """
        Return one fixed screen position for context-menu tests.

        :return: Fixed screen position.
        """
        return QPointF(0.0, 0.0)


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


def test_vsc_3term_rotation_persists_and_refreshes_connections(override_attrs) -> None:
    """
    Rotating the three-terminal VSC should update its angle and persist it.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus_ac: Bus = Bus(name="AC")
    bus_dc_p: Bus = Bus(name="DC+", is_dc=True)
    bus_dc_n: Bus = Bus(name="DC-", is_dc=True)
    vsc: VSC = VSC(name="VSC-3T", bus_from=bus_dc_p, bus_to=bus_ac)
    vsc.bus_dc_n = bus_dc_n
    graphic: VscGraphicItem3Term = VscGraphicItem3Term(editor=editor, api_object=vsc)
    update_conn_calls: list[int] = list()

    def _fake_update_conn() -> None:
        """
        Record connection-refresh requests.

        :return: ``None``.
        """
        update_conn_calls.append(1)

    override_attrs.setattr(graphic, "update_conn", _fake_update_conn)

    graphic.set_rotation_angle(angle_degrees=90.0, persist=True)

    assert graphic.rotation() == 90.0
    assert graphic.r == 90.0
    assert update_conn_calls == [1]
    assert editor.diagram_updates[-1]["r"] == 90.0


def test_vsc_3term_context_menu_adds_rotate_entry_with_rotate_icon(override_attrs) -> None:
    """
    The three-terminal VSC context menu should expose a rotate action with the rotate icon.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus_ac: Bus = Bus(name="AC")
    bus_dc_p: Bus = Bus(name="DC+", is_dc=True)
    vsc: VSC = VSC(name="VSC-3T", bus_from=bus_dc_p, bus_to=bus_ac)
    graphic: VscGraphicItem3Term = VscGraphicItem3Term(editor=editor, api_object=vsc)
    menu_entries: list[tuple[str, str]] = list()

    def _fake_add_menu_entry(menu: QtWidgets.QMenu,
                             text: str,
                             icon_path: str = "",
                             icon_pixmap: Any = None,
                             function_ptr: Any = None,
                             checkeable: bool = False,
                             checked_value: bool = False,
                             font_size: int = 0) -> Any:
        """
        Record context-menu entries created through the shared helper.

        :param menu: Unused menu.
        :param text: Entry text.
        :param icon_path: Entry icon path.
        :param icon_pixmap: Unused pixmap.
        :param function_ptr: Unused function pointer.
        :param checkeable: Unused check flag.
        :param checked_value: Unused check value.
        :param font_size: Unused font size.
        :return: ``None``.
        """
        menu_entries.append((text, icon_path))
        return None

    def _fake_exec(menu: QtWidgets.QMenu, position: QPointF) -> None:
        """
        Skip native menu execution during the test.

        :param menu: Unused menu.
        :param position: Unused position.
        :return: ``None``.
        """
        return None

    override_attrs.setattr(vsc_graphics_3term_module, "add_menu_entry", _fake_add_menu_entry)
    override_attrs.setattr(QtWidgets.QMenu, "exec_", _fake_exec)

    graphic.contextMenuEvent(_ContextMenuEventStub())

    assert ("Rotate 90", ":/Icons/icons/rotate.svg") in menu_entries


def test_vsc_3term_redraw_preserves_saved_rotation() -> None:
    """
    Automatic redraw must not wipe a previously restored user rotation.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus_ac: Bus = Bus(name="AC")
    bus_dc_p: Bus = Bus(name="DC+", is_dc=True)
    vsc: VSC = VSC(name="VSC-3T", bus_from=bus_dc_p, bus_to=bus_ac)
    graphic: VscGraphicItem3Term = VscGraphicItem3Term(editor=editor, api_object=vsc)

    graphic.setPos(QPointF(0.0, 0.0))
    graphic.set_rotation_angle(angle_degrees=180.0, persist=False)
    graphic.redraw()

    assert graphic.rotation() == 180.0
    assert graphic.r == 180.0


def test_vsc_3term_connector_line_supports_reticular_auto_route() -> None:
    """
    Three-terminal VSC connector lines should support the routed straight/reticular styles.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus_ac: Bus = Bus(name="AC")
    bus_dc_p: Bus = Bus(name="DC+", is_dc=True)
    vsc: VSC = VSC(name="VSC-3T", bus_from=bus_dc_p, bus_to=bus_ac)
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_ac, w=180.0, h=40.0, x=0.0, y=0.0)
    vsc_graphic: VscGraphicItem3Term = VscGraphicItem3Term(editor=editor, api_object=vsc)
    vsc_graphic.setPos(QPointF(260.0, 0.0))
    connector_line: LineGraphicTemplateItem = LineGraphicTemplateItem(from_port=bus_graphic.get_terminal(),
                                                                      to_port=vsc_graphic.terminal_ac,
                                                                      editor=editor)

    reticular_points = connector_line.get_render_points()

    assert connector_line.get_branch_auto_route_style() == SchematicAutoRouteStyle.RETICULAR
    assert len(reticular_points) > 2

    connector_line.set_branch_auto_route_style(route_style=SchematicAutoRouteStyle.STRAIGHT)

    assert connector_line.get_branch_auto_route_style() == SchematicAutoRouteStyle.STRAIGHT
    assert len(connector_line.get_render_points()) == 2


def test_rotated_vsc_3term_connector_uses_rotated_terminal_center() -> None:
    """
    Rotated VSC connector endpoints must follow the rotated round-terminal center.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    bus_ac: Bus = Bus(name="AC")
    bus_dc_p: Bus = Bus(name="DC+", is_dc=True)
    vsc: VSC = VSC(name="VSC-3T", bus_from=bus_dc_p, bus_to=bus_ac)
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_ac, w=180.0, h=40.0, x=0.0, y=0.0)
    vsc_graphic: VscGraphicItem3Term = VscGraphicItem3Term(editor=editor, api_object=vsc)
    vsc_graphic.setPos(QPointF(260.0, 0.0))
    vsc_graphic.set_rotation_angle(angle_degrees=90.0, persist=False)

    connector_line: LineGraphicTemplateItem = LineGraphicTemplateItem(from_port=bus_graphic.get_terminal(),
                                                                      to_port=vsc_graphic.terminal_ac,
                                                                      editor=editor)

    terminal_center: QPointF = vsc_graphic.terminal_ac.mapToScene(vsc_graphic.terminal_ac.rect().center())
    render_end = connector_line.get_render_points()[-1]

    assert render_end == (terminal_center.x(), terminal_center.y())


def test_vsc_3term_connector_shows_bus_side_green_handle_and_persists_alignment() -> None:
    """
    VSC connector editing should expose a green handle on the bus side and persist its movement.
    """
    _get_app()
    editor: _EditorStub = _EditorStub()
    scene: QtWidgets.QGraphicsScene = QtWidgets.QGraphicsScene()
    bus_ac: Bus = Bus(name="AC")
    bus_dc_p: Bus = Bus(name="DC+", is_dc=True)
    vsc: VSC = VSC(name="VSC-3T", bus_from=bus_dc_p, bus_to=bus_ac)
    bus_graphic: BusGraphicItem = BusGraphicItem(editor=editor, bus=bus_ac, w=180.0, h=40.0, x=0.0, y=0.0)
    vsc_graphic: VscGraphicItem3Term = VscGraphicItem3Term(editor=editor, api_object=vsc)
    vsc_graphic.setPos(QPointF(260.0, 0.0))
    connector_line: LineGraphicTemplateItem = LineGraphicTemplateItem(from_port=bus_graphic.get_terminal(),
                                                                      to_port=vsc_graphic.terminal_ac,
                                                                      editor=editor)

    scene.addItem(bus_graphic)
    scene.addItem(vsc_graphic)
    scene.addItem(connector_line)
    connector_line.setSelected(True)
    connector_line.set_route_edit_active(True)

    assert connector_line._endpoint_handles["from"].isVisible()
    assert not connector_line._endpoint_handles["to"].isVisible()

    connector_line.move_endpoint_alignment(endpoint="from", scene_pos=QPointF(140.0, 45.0))

    moved_anchor: QPointF = connector_line.get_endpoint_anchor(endpoint="from")

    assert moved_anchor.x() == 140.0
    assert moved_anchor.y() == 45.0
