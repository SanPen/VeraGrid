from pathlib import Path

from PySide6 import QtCore
from PySide6 import QtWidgets

from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.line_graphics import LineGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Fluid.fluid_node_graphics import FluidNodeGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.Substation.bus_graphics import BusGraphicItem
from VeraGrid.Gui.Diagrams.SchematicWidget.schematic_widget import SchematicWidget
from VeraGrid.Gui.Diagrams.graphics_manager import ALL_GRAPHICS
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Fluid.fluid_node import FluidNode
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.IO.file_open import FileOpen


class _DiagramGuiStub:
    """
    Minimal GUI object required by ``SchematicWidget``.
    """

    __slots__ = ("circuit",)

    def __init__(self, circuit: MultiCircuit) -> None:
        """
        Store the active circuit.

        :param circuit: Active circuit for the diagram widget.
        :return: None.
        """
        self.circuit: MultiCircuit = circuit

    def show_warning_toast(self, message: str, duration: int = 2000) -> None:
        """
        Accept warning messages emitted by the diagram.

        :param message: Warning text.
        :param duration: Toast duration.
        :return: None.
        """
        del message
        del duration

    def show_error_toast(self, message: str, duration: int = 2000) -> None:
        """
        Accept error messages emitted by the diagram.

        :param message: Error text.
        :param duration: Toast duration.
        :return: None.
        """
        del message
        del duration


class _ScenePositionEvent:
    """
    Minimal event wrapper for the schematic branch release handler.
    """

    __slots__ = ("_scene_pos",)

    def __init__(self, scene_pos: QtCore.QPointF) -> None:
        """
        Store the release scene position.

        :param scene_pos: Release point in scene coordinates.
        :return: None.
        """
        self._scene_pos: QtCore.QPointF = scene_pos

    def scenePos(self) -> QtCore.QPointF:
        """
        Return the stored scene position.

        :return: Release point in scene coordinates.
        """
        return self._scene_pos


def get_grid_file(name: str) -> Path:
    """
    Return a test grid path.

    :param name: Test grid file name.
    :return: Absolute test grid path.
    """
    return Path(__file__).resolve().parents[1] / "data" / "grids" / name


def load_grid(name: str) -> MultiCircuit:
    """
    Load one test grid.

    :param name: Test grid file name.
    :return: Loaded grid.
    """
    return FileOpen(str(get_grid_file(name=name))).open()


def find_bus_by_name_prefix(grid: MultiCircuit, name_prefix: str) -> Bus:
    """
    Find a bus by name prefix.

    :param grid: Circuit to search.
    :param name_prefix: Prefix to match.
    :return: Matching bus.
    """
    selected_bus: Bus | None = None
    bus: Bus

    for bus in grid.buses:
        if bus.name.startswith(name_prefix):
            selected_bus = bus
        else:
            pass

    assert selected_bus is not None
    return selected_bus


def find_fluid_node_by_name(grid: MultiCircuit, name: str) -> FluidNode:
    """
    Find one fluid node by exact name.

    :param grid: Circuit to search.
    :param name: Fluid node name.
    :return: Matching fluid node.
    """
    selected_node: FluidNode | None = None
    node: FluidNode

    for node in grid.fluid_nodes:
        if node.name == name:
            selected_node = node
        else:
            pass

    assert selected_node is not None
    return selected_node


def get_fluid_node_electrical_lines(grid: MultiCircuit) -> list[Line]:
    """
    Collect electrical lines connected to a fluid node's associated bus.

    :param grid: Circuit to inspect.
    :return: Matching electrical lines.
    """
    fluid_buses: set[Bus] = set()
    fluid_lines: list[Line] = list()
    node: FluidNode
    line: Line

    for node in grid.fluid_nodes:
        if node.bus is not None:
            fluid_buses.add(node.bus)
        else:
            pass

    for line in grid.lines:
        if line.bus_from in fluid_buses or line.bus_to in fluid_buses:
            fluid_lines.append(line)
        else:
            pass

    return fluid_lines


def test_schematic_fluid_node_bus_line_survives_non_terminal_scene_item(
        qt_app: QtWidgets.QApplication) -> None:
    """
    Creating a schematic line from ``CJN230 FN`` to ``CJN230`` must survive non-terminal scene hits.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    app: QtWidgets.QApplication = qt_app
    grid: MultiCircuit = load_grid(name="cnd_enee_15_bus_hydro.veragrid")
    widget: SchematicWidget = SchematicWidget(gui=_DiagramGuiStub(circuit=grid),
                                              diagram=grid.diagrams[0],
                                              default_bus_voltage=10.0)
    fluid_node: FluidNode = find_fluid_node_by_name(grid=grid, name="CJN230 FN")
    target_bus: Bus = find_bus_by_name_prefix(grid=grid, name_prefix="CJN230")
    fluid_node_graphic: ALL_GRAPHICS | None = widget.graphics_manager.query(elm=fluid_node)
    target_bus_graphic: ALL_GRAPHICS | None = widget.graphics_manager.query(elm=target_bus)

    assert isinstance(fluid_node_graphic, FluidNodeGraphicItem)
    assert isinstance(target_bus_graphic, BusGraphicItem)
    assert fluid_node.bus is not None

    before_lines: int = len(grid.lines)
    release_pos: QtCore.QPointF = target_bus_graphic.get_terminal().sceneBoundingRect().center()
    overlay_rect: QtWidgets.QGraphicsRectItem = QtWidgets.QGraphicsRectItem(-5.0, -5.0, 10.0, 10.0)
    overlay_rect.setPos(release_pos)
    overlay_rect.setZValue(1000000.0)
    widget.add_to_scene(graphic_object=overlay_rect)

    widget.start_connection(port=fluid_node_graphic.get_terminal())
    widget.create_branch_on_mouse_release_event(_ScenePositionEvent(scene_pos=release_pos))
    app.processEvents()

    created_line: Line = grid.lines[-1]
    assert len(grid.lines) == before_lines + 1
    assert created_line.bus_from is fluid_node.bus
    assert created_line.bus_to is target_bus


def test_schematic_draws_existing_fluid_node_to_bus_lines(qt_app: QtWidgets.QApplication) -> None:
    """
    Existing electrical lines from fluid-node buses must draw against the fluid node graphics.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    app: QtWidgets.QApplication = qt_app
    grid: MultiCircuit = load_grid(name="cnd_enee_15_bus_hydro_b.veragrid")
    widget: SchematicWidget = SchematicWidget(gui=_DiagramGuiStub(circuit=grid),
                                              diagram=grid.diagrams[0],
                                              default_bus_voltage=10.0)
    fluid_lines: list[Line] = get_fluid_node_electrical_lines(grid=grid)
    line: Line

    app.processEvents()

    assert len(fluid_lines) == 2
    for line in fluid_lines:
        line_graphic: ALL_GRAPHICS | None = widget.graphics_manager.query(elm=line)
        assert isinstance(line_graphic, LineGraphicItem)
