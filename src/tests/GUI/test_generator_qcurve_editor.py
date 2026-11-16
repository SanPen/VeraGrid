# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import numpy as np
from PySide6 import QtCore, QtGui, QtTest, QtWidgets

from VeraGrid.Gui.DeviceEditors.GeneratorEditor.generator_editor import GeneratorEditor, GeneratorQCurveEditor
from VeraGrid.Gui.SigmaAnalysis.sigma_analysis_dialogue import SigmaAnalysisGUI
from VeraGrid.Gui.PlotDialogue.qt_chart_widget import ChartSeries, ChartSeriesType, GraphsWidget
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.generator_q_curve import GeneratorQCurve
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.SigmaAnalysis.sigma_analysis_driver import SigmaAnalysisResults


def build_sigma_results(offset: float, converged: bool) -> SigmaAnalysisResults:
    """Build deterministic data for one Sigma result repaint.

    :param offset: Displacement applied to the Sigma points.
    :param converged: Display convergence state.
    :return: Complete small Sigma result.
    """
    results: SigmaAnalysisResults = SigmaAnalysisResults(n=3)
    results.sigma_re = np.asarray((0.05 + offset, 0.10 + offset, 0.15 + offset), dtype=float)
    results.sigma_im = np.asarray((-0.04, 0.0, 0.04), dtype=float)
    results.distances = np.asarray((0.25, 0.30, 0.35), dtype=float)
    results.bus_names = np.asarray(("Bus 1", "Bus 2", "Bus 3"), dtype=object)
    results.converged = converged
    return results


def flush_deferred_deletes(app: QtWidgets.QApplication) -> None:
    """Deliver Qt deferred destruction while test wrappers are still valid.

    :param app: Shared Qt application fixture.
    :return: None.
    """
    app.processEvents()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)
    app.processEvents()


def send_chart_pan(chart: GraphsWidget, start: QtCore.QPoint, end: QtCore.QPoint) -> None:
    """Deliver one Ctrl+left drag directly to the chart's QWidget handlers.

    :param chart: Native chart receiving the pan gesture.
    :param start: Local drag origin.
    :param end: Local drag destination.
    :return: None.
    """
    modifier: QtCore.Qt.KeyboardModifier = QtCore.Qt.KeyboardModifier.ControlModifier
    start_position: QtCore.QPointF = QtCore.QPointF(start)
    end_position: QtCore.QPointF = QtCore.QPointF(end)
    start_global: QtCore.QPointF = QtCore.QPointF(chart.mapToGlobal(start))
    end_global: QtCore.QPointF = QtCore.QPointF(chart.mapToGlobal(end))
    press_event: QtGui.QMouseEvent = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseButtonPress,
        start_position,
        start_global,
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.MouseButton.LeftButton,
        modifier,
    )
    chart.mousePressEvent(press_event)
    move_event: QtGui.QMouseEvent = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseMove,
        end_position,
        end_global,
        QtCore.Qt.MouseButton.NoButton,
        QtCore.Qt.MouseButton.LeftButton,
        modifier,
    )
    chart.mouseMoveEvent(move_event)
    release_event: QtGui.QMouseEvent = QtGui.QMouseEvent(
        QtCore.QEvent.Type.MouseButtonRelease,
        end_position,
        end_global,
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.MouseButton.NoButton,
        modifier,
    )
    chart.mouseReleaseEvent(release_event)


def build_generator_editor() -> GeneratorEditor:
    """Build the in-place generator editor with an assigned generator bus.

    :return: Generator editor under test.
    """
    circuit: MultiCircuit = MultiCircuit()
    bus: Bus = Bus(name="Generator bus", Vnom=110.0, is_slack=True)
    generator: Generator = Generator(name="Generator", P=1.0, Snom=1.0)
    circuit.add_bus(obj=bus)
    circuit.add_generator(bus=bus, api_obj=generator)
    dialog: GeneratorEditor = GeneratorEditor(api_object=generator, circuit=circuit)
    return dialog


def build_sigma_circuit() -> MultiCircuit:
    """Build the smallest solvable circuit for the real Sigma rerun action.

    :return: Two-bus circuit with one source, one load, and one line.
    """
    circuit: MultiCircuit = MultiCircuit()
    source_bus: Bus = Bus(name="Source", Vnom=110.0, is_slack=True)
    load_bus: Bus = Bus(name="Load", Vnom=110.0)
    generator: Generator = Generator(name="Source generator", P=1.0, Snom=1.0)
    load: Load = Load(name="Demand", P=0.5, Q=0.1)
    circuit.add_bus(obj=source_bus)
    circuit.add_bus(obj=load_bus)
    circuit.add_generator(bus=source_bus, api_obj=generator)
    circuit.add_load(bus=load_bus, api_obj=load)
    line: Line = Line(
        name="Source line",
        bus_from=source_bus,
        bus_to=load_bus,
        r=0.01,
        x=0.05,
        rate=100.0,
    )
    circuit.add_line(obj=line)
    return circuit


def test_qcurve_add_button_reuses_the_existing_chart_series(qt_app: QtWidgets.QApplication) -> None:
    """Verify adding capability points leaves the renderer-owned series intact.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    q_curve: GeneratorQCurve = GeneratorQCurve()
    q_curve.set(np.array([[0.0, -1.0, 1.0]], dtype=float))
    dialog: GeneratorQCurveEditor = GeneratorQCurveEditor(
        q_curve=q_curve,
        Qmin=-1.0,
        Qmax=1.0,
        Pmin=0.0,
        Pmax=1.0,
        Snom=1.0,
    )
    dialog.show()
    qt_app.processEvents()

    plotter: GraphsWidget = dialog.q_curve_widget.ui.plotter
    original_series: tuple[ChartSeries, ...] = tuple(plotter._series)

    # Each click must replace the five existing Python buffers without recreating chart series.
    for _ in range(8):
        QtTest.QTest.mouseClick(dialog.q_curve_widget.ui.addRowButton, QtCore.Qt.MouseButton.LeftButton)
        qt_app.processEvents()

    assert dialog.q_curve_widget.table_model.rowCount() == 9
    assert len(plotter._series) == 5
    assert all(plotter._series[index] is original_series[index] for index in range(len(original_series)))

    dialog.close()
    flush_deferred_deletes(app=qt_app)
    assert plotter._disposed


def test_embedded_generator_editor_reuses_the_existing_chart_series(qt_app: QtWidgets.QApplication) -> None:
    """Verify the GeneratorEditor Add button repaints its fixed chart series.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    dialog: GeneratorEditor = build_generator_editor()
    dialog.show()
    qt_app.processEvents()

    plotter: GraphsWidget = dialog.qcurve_editor_widget.ui.plotter
    original_series: tuple[ChartSeries, ...] = tuple(plotter._series)
    original_row_count: int = dialog.qcurve_editor_widget.table_model.rowCount()
    assert len(original_series) == 5

    click_index: int
    for click_index in range(12):
        QtTest.QTest.mouseClick(dialog.qcurve_editor_widget.ui.addRowButton, QtCore.Qt.MouseButton.LeftButton)
        qt_app.processEvents()
        assert tuple(plotter._series) == original_series

    assert dialog.qcurve_editor_widget.table_model.rowCount() == original_row_count + 12
    dialog.close()
    flush_deferred_deletes(app=qt_app)
    assert plotter._disposed


def test_chart_widget_survives_repeated_paint_lifecycles(qt_app: QtWidgets.QApplication) -> None:
    """Stress series replacement, view resize, clearing, and ordered disposal.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    widget_index: int
    for widget_index in range(12):
        dialog: QtWidgets.QDialog = QtWidgets.QDialog()
        layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(dialog)
        plotter: GraphsWidget = GraphsWidget(dialog)
        layout.addWidget(plotter)
        dialog.resize(840 + widget_index, 560 + widget_index)
        dialog.show()
        qt_app.processEvents()
        assert plotter.width() > 400

        # Configure one stable line/scatter pair before replacing only its point buffers.
        initial_x: np.ndarray = np.asarray((0.0, 1.0, 2.0), dtype=float)
        plotter.add_line_series(name="Line", x_values=initial_x, y_values=initial_x, color="#2563eb")
        plotter.add_scatter_series(name="Points", x_values=initial_x, y_values=-initial_x, color="#f97316")
        original_series: tuple[ChartSeries, ...] = tuple(plotter._series)
        assert len(original_series) == 2
        zoom_before: float = plotter.axis_x.get_zoom()
        center: QtCore.QPoint = plotter.rect().center()
        wheel_event: QtGui.QWheelEvent = QtGui.QWheelEvent(
            QtCore.QPointF(center),
            QtCore.QPointF(plotter.mapToGlobal(center)),
            QtCore.QPoint(),
            QtCore.QPoint(0, 120),
            QtCore.Qt.MouseButton.NoButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
            QtCore.Qt.ScrollPhase.ScrollUpdate,
            False,
        )
        QtWidgets.QApplication.sendEvent(plotter, wheel_event)
        qt_app.processEvents()
        assert plotter.axis_x.get_zoom() > zoom_before
        visual_minimum_before: float = plotter.axis_x.get_visual_range()[0]
        send_chart_pan(chart=plotter, start=center, end=center + QtCore.QPoint(80, 0))
        qt_app.processEvents()
        assert plotter.axis_x.get_visual_range()[0] != visual_minimum_before
        first_zoom_pan_distance: float = abs(plotter.axis_x.get_pan())

        # The same physical drag must cover fewer data units after further wheel zoom.
        plotter.axis_x.reset_viewport()
        plotter.axis_y.reset_viewport()
        zoom_index: int
        for zoom_index in range(4):
            high_zoom_wheel_event: QtGui.QWheelEvent = QtGui.QWheelEvent(
                QtCore.QPointF(center),
                QtCore.QPointF(plotter.mapToGlobal(center)),
                QtCore.QPoint(),
                QtCore.QPoint(0, 120),
                QtCore.Qt.MouseButton.NoButton,
                QtCore.Qt.KeyboardModifier.NoModifier,
                QtCore.Qt.ScrollPhase.ScrollUpdate,
                False,
            )
            QtWidgets.QApplication.sendEvent(plotter, high_zoom_wheel_event)
        send_chart_pan(chart=plotter, start=center, end=center + QtCore.QPoint(80, 0))
        qt_app.processEvents()
        assert abs(plotter.axis_x.get_pan()) < first_zoom_pan_distance

        replacement_index: int
        for replacement_index in range(24):
            point_x: np.ndarray = np.linspace(0.0, 2.0 + replacement_index, 7)
            point_y: np.ndarray = point_x * float(replacement_index + 1)
            updated: bool = plotter.replace_xy_series_data(series_data=(
                (point_x, point_y, "#2563eb"),
                (point_x, -point_y, "#f97316"),
            ))
            assert updated
            assert tuple(plotter._series) == original_series
            dialog.resize(420 + replacement_index, 280 + replacement_index)
            plotter.redraw()
            qt_app.processEvents()

        invalid_update: bool = plotter.replace_xy_series_data(series_data=(
            (np.asarray((0.0,), dtype=float), np.asarray((0.0, 1.0), dtype=float), "#000000"),
            (np.asarray((0.0,), dtype=float), np.asarray((0.0,), dtype=float), "#000000"),
        ))
        assert not invalid_update
        assert tuple(plotter._series) == original_series

        # Clearing releases chart-owned buffers before dispose prevents later reuse.
        plotter.clear()
        plotter.add_scatter_series(name="Empty", x_values=np.zeros(0), y_values=np.zeros(0), color="#2563eb")
        assert len(plotter._series) == 1
        plotter.dispose()
        assert plotter._disposed
        dialog.close()
        dialog.deleteLater()
        flush_deferred_deletes(app=qt_app)


def test_chart_widget_owns_data_without_native_chart_children(qt_app: QtWidgets.QApplication) -> None:
    """Verify source arrays, bar rendering, and disposal need no chart QObjects.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    dialog: QtWidgets.QDialog = QtWidgets.QDialog()
    layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(dialog)
    plotter: GraphsWidget = GraphsWidget(dialog)
    layout.addWidget(plotter)
    dialog.resize(760, 480)
    dialog.show()
    qt_app.processEvents()

    source_x: np.ndarray = np.asarray((0.0, 1.0, 2.0), dtype=float)
    source_y: np.ndarray = np.asarray((2.0, 1.0, 0.0), dtype=float)
    plotter.add_line_series(name="Owned", x_values=source_x, y_values=source_y, color="#2563eb")
    plotter.add_scatter_series(
        name="Points",
        x_values=source_x,
        y_values=source_y,
        color="#f97316",
        point_tooltips=("Bus 1", "Bus 2", "Bus 3"),
    )
    qt_app.processEvents()
    chart_image: QtGui.QImage = plotter.grab().toImage()
    plot_rect: QtCore.QRectF = plotter._get_plot_rect()
    line_point: QtCore.QPointF = plotter._map_xy_point(x_value=0.5, y_value=1.5, plot_rect=plot_rect)
    scatter_point: QtCore.QPointF = plotter._map_xy_point(x_value=1.0, y_value=1.0, plot_rect=plot_rect)
    line_pixel: QtGui.QColor = chart_image.pixelColor(line_point.toPoint())
    line_color: QtGui.QColor = QtGui.QColor("#2563eb")
    assert (abs(line_pixel.red() - line_color.red()) + abs(line_pixel.green() - line_color.green())
            + abs(line_pixel.blue() - line_color.blue())) <= 12
    assert chart_image.pixelColor(scatter_point.toPoint()).name() == "#f97316"
    assert plotter.get_point_tooltip_at(position=scatter_point) == "Bus 2"
    assert len(plotter.findChildren(QtWidgets.QLineEdit)) == 1
    assert plotter.set_series_point_tooltips(series_index=1, point_tooltips=("A", "B", "C"))
    assert plotter.get_point_tooltip_at(position=scatter_point) == "B"
    line_series: ChartSeries = plotter._series[0]
    source_x[:] = 99.0
    source_y[:] = 99.0
    assert np.array_equal(line_series.get_x_data(), np.asarray((0.0, 1.0, 2.0), dtype=float))
    assert np.array_equal(line_series.get_y_data(), np.asarray((2.0, 1.0, 0.0), dtype=float))

    plotter.add_horizontal_bar_series(
        labels=("Export", "Import", "Neutral"),
        values=np.asarray((2.0, -1.0, 0.0), dtype=float),
        positive_color="#0f766e",
        negative_color="#dc2626",
    )
    assert len(plotter._series) == 2
    assert all(series.get_series_type() == ChartSeriesType.HORIZONTAL_BAR for series in plotter._series)
    plotter.redraw()
    qt_app.processEvents()

    plotter.dispose()
    assert plotter._disposed
    assert len(plotter._series) == 0
    dialog.close()
    dialog.deleteLater()
    flush_deferred_deletes(app=qt_app)


def test_sigma_resimulation_reuses_the_existing_chart_series(qt_app: QtWidgets.QApplication) -> None:
    """Verify Sigma result rerenders preserve the three renderer-owned series.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    bus_names: np.ndarray = np.asarray(("Bus 1", "Bus 2", "Bus 3"), dtype=object)
    dialog: SigmaAnalysisGUI = SigmaAnalysisGUI(
        results=build_sigma_results(offset=0.0, converged=True),
        bus_names=bus_names,
    )
    dialog.show()
    qt_app.processEvents()

    plotter: GraphsWidget = dialog.ui.plotwidget
    original_series: tuple[ChartSeries, ...] = tuple(plotter._series)
    assert len(original_series) == 3
    sigma_point: QtCore.QPointF = plotter._map_xy_point(
        x_value=0.10,
        y_value=0.0,
        plot_rect=plotter._get_plot_rect(),
    )
    assert plotter.get_point_tooltip_at(position=sigma_point) == "Bus 2"

    rerun_index: int
    for rerun_index in range(24):
        dialog.apply_results(
            results=build_sigma_results(offset=float(rerun_index) / 100.0, converged=rerun_index % 2 == 0),
            bus_names=bus_names,
        )
        qt_app.processEvents()
        assert tuple(plotter._series) == original_series

    dialog.close()
    flush_deferred_deletes(app=qt_app)
    assert plotter._disposed


def test_sigma_rerun_action_keeps_its_chart_series(qt_app: QtWidgets.QApplication) -> None:
    """Run the real Sigma action twice and retain its chart objects.

    :param qt_app: Shared Qt application fixture.
    :return: None.
    """
    dialog: SigmaAnalysisGUI = SigmaAnalysisGUI(
        grid=build_sigma_circuit(),
        options=PowerFlowOptions(),
        classical_sigma=True,
    )
    dialog.show()
    qt_app.processEvents()

    dialog.rerun_sigma_analysis()
    qt_app.processEvents()
    assert dialog.results is not None
    plotter: GraphsWidget = dialog.ui.plotwidget
    original_series: tuple[ChartSeries, ...] = tuple(plotter._series)
    assert len(original_series) == 3

    dialog.rerun_sigma_analysis()
    qt_app.processEvents()
    assert tuple(plotter._series) == original_series
    dialog.close()
    flush_deferred_deletes(app=qt_app)
    assert plotter._disposed
