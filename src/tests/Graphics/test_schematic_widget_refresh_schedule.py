from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView

import VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget as schematic_widget_module
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import CustomGraphicsView, SchematicWidget
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
