# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text

from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.enumerations import DeviceType, ResultTablePlotType


def test_complex_point_plot_uses_only_selected_mode_rows() -> None:
    """
    Verify row selection controls the points shown in an S-domain plot.

    :return: None.
    """
    table: ResultsTable = ResultsTable(
        data=np.array(
            (
                (-1.0, 2.0, 2.0 / (2.0 * np.pi)),
                (-2.0, -3.0, -3.0 / (2.0 * np.pi)),
                (0.5, 1.0, 1.0 / (2.0 * np.pi)),
            ),
            dtype=float,
        ),
        columns=np.array(("Real", "Imaginary [rad/s]", "Imaginary [Hz]"), dtype=str),
        index=np.array(("Mode 0", "Mode 1", "Mode 2"), dtype=str),
        title="S-Domain Stability plot",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
        plot_type=ResultTablePlotType.COMPLEX_POINTS,
        damping_ratio_boundary=0.05,
        complex_plot_x_column="Real",
        complex_plot_y_columns=np.array(("Imaginary [rad/s]", "Imaginary [Hz]"), dtype=str),
        complex_plot_y_scales=np.array((1.0, 1.0 / (2.0 * np.pi)), dtype=float),
    )
    figure: Figure = Figure(figsize=(8, 6))
    axes: Axes = figure.add_subplot(111)

    table.plot(
        ax=axes,
        selected_col_idx=None,
        selected_rows=np.array((1,), dtype=np.int64),
        stacked=False,
    )

    offsets: np.ndarray = np.asarray(axes.collections[0].get_offsets(), dtype=float)
    assert offsets.shape == (1, 2)
    assert np.array_equal(offsets[0], np.array((-2.0, -3.0), dtype=float))
    assert axes.get_xlabel() == "Real"
    assert axes.get_ylabel() == "Imaginary [rad/s]"
    assert axes.collections[0].cmap.name == "winter"

    hertz_figure: Figure = Figure(figsize=(8, 6))
    hertz_axes: Axes = hertz_figure.add_subplot(111)
    table.plot(
        ax=hertz_axes,
        selected_col_idx=np.array((0, 2), dtype=np.int64),
        selected_rows=np.array((1,), dtype=np.int64),
        stacked=False,
    )
    hertz_offsets: np.ndarray = np.asarray(hertz_axes.collections[0].get_offsets(), dtype=float)
    assert np.isclose(hertz_offsets[0, 1], -3.0 / (2.0 * np.pi))
    assert hertz_axes.get_ylabel() == "Imaginary [Hz]"


def test_complex_vector_plot_uses_selected_modes_and_states() -> None:
    """
    Verify mode-shape plotting builds one subplot from the selected components.

    :return: None.
    """
    table: ResultsTable = ResultsTable(
        data=np.array(
            (
                (1.0 + 0.0j, 0.0 + 2.0j),
                (0.5 + 0.5j, 1.0 + 0.0j),
                (0.0 + 1.0j, -1.0 + 1.0j),
            ),
            dtype=complex,
        ),
        columns=np.array(("Mode 0", "Mode 1\nf=1.250 Hz"), dtype=str),
        index=np.array(("delta1", "omega1", "delta2"), dtype=str),
        title="Mode shapes",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
        plot_type=ResultTablePlotType.COMPLEX_VECTORS,
    )
    figure: Figure = Figure(figsize=(8, 6))
    initial_axes: Axes = figure.add_subplot(111)

    table.plot(
        ax=initial_axes,
        selected_col_idx=np.array((1,), dtype=np.int64),
        selected_rows=np.array((0, 2), dtype=np.int64),
        stacked=False,
    )

    assert len(figure.axes) == 1
    mode_axes: Axes = figure.axes[0]
    component_labels: set[str] = set()
    text_artist: Text
    for text_artist in mode_axes.texts:
        component_labels.add(text_artist.get_text())
    assert len(mode_axes.patches) == 2
    assert component_labels == {"delta1", "delta2"}
    assert mode_axes.get_title() == "Mode 1\nf=1.250 Hz"
    assert mode_axes.get_xlabel() == "Real"
    assert mode_axes.get_ylabel() == "Imaginary"


def test_complex_plot_contract_survives_slicing_but_not_destructive_transforms() -> None:
    """
    Verify safe slices retain plot semantics and absolute conversion drops them.

    :return: None.
    """
    table: ResultsTable = ResultsTable(
        data=np.array(((1.0 + 1.0j, 2.0 + 0.0j),), dtype=complex),
        columns=np.array(("Mode 0", "Mode 1"), dtype=str),
        index=np.array(("delta1",), dtype=str),
        title="Mode shapes",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
        plot_type=ResultTablePlotType.COMPLEX_VECTORS,
    )

    sliced_table: ResultsTable = table.slice_cols(col_idx=np.array((1,), dtype=np.int64))
    assert sliced_table.plot_type == ResultTablePlotType.COMPLEX_VECTORS

    sliced_table.convert_to_abs()
    assert sliced_table.plot_type == ResultTablePlotType.SERIES
