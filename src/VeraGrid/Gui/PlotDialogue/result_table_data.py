# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Extract isolated numeric result-table series for native Qt plotting."""

import numpy as np

from VeraGrid.Gui.PlotDialogue.qt_chart_widget import GraphsWidget
from VeraGridEngine.Simulations.results_table import ResultsTable


def get_result_table_series(table: ResultsTable,
                            selected_col_idx: np.ndarray | None = None,
                            selected_rows: np.ndarray | None = None,
                            hide_zero_values: bool = False) -> tuple[np.ndarray, list[str], list[np.ndarray]] | None:
    """Copy selected real-valued result columns into native chart buffers.

    :param table: Results table providing the visible values and labels.
    :param selected_col_idx: Optional visible column indices in display order.
    :param selected_rows: Optional visible row indices in display order.
    :param hide_zero_values: Whether exact zero values become gaps in the chart.
    :return: X coordinates, series labels, and independent Y buffers, or ``None`` when invalid.
    """
    index_values: np.ndarray
    column_names: np.ndarray
    data_values: np.ndarray
    index_values, column_names, data_values = table.get_data()
    data_matrix: np.ndarray = np.asarray(data_values)
    if data_matrix.ndim == 2:
        row_count: int = data_matrix.shape[0]
        column_count: int = data_matrix.shape[1]
        if selected_col_idx is None:
            column_indices: np.ndarray = np.arange(column_count, dtype=np.int64)
        else:
            column_indices = np.unique(np.asarray(selected_col_idx, dtype=np.int64))
        if selected_rows is None:
            row_indices: np.ndarray = np.arange(row_count, dtype=np.int64)
        else:
            row_indices = np.unique(np.asarray(selected_rows, dtype=np.int64))

        column_indices_valid: bool = (
            len(column_indices) > 0
            and int(np.min(column_indices)) >= 0
            and int(np.max(column_indices)) < column_count
        )
        row_indices_valid: bool = (
            len(row_indices) > 0
            and int(np.min(row_indices)) >= 0
            and int(np.max(row_indices)) < row_count
        )
        if column_indices_valid and row_indices_valid:
            raw_x_values: np.ndarray = np.asarray(index_values)[row_indices]
            if np.issubdtype(raw_x_values.dtype, np.datetime64):
                x_values: np.ndarray = np.ascontiguousarray(raw_x_values.astype('datetime64[ms]'))
            elif np.issubdtype(raw_x_values.dtype, np.number):
                x_values = np.ascontiguousarray(raw_x_values, dtype=float)
            else:
                x_values = np.arange(len(row_indices), dtype=float)

            selected_data: np.ndarray = np.asarray(
                data_matrix[np.ix_(row_indices, column_indices)],
                dtype=float,
            )
            if hide_zero_values:
                selected_data = selected_data.copy()
                selected_data[selected_data == 0.0] = np.nan
            else:
                pass

            series_names: list[str] = list()
            series_values: list[np.ndarray] = list()
            selected_position: int
            for selected_position in range(len(column_indices)):
                column_index: int = int(column_indices[selected_position])
                series_names.append(str(column_names[column_index]))
                series_values.append(np.ascontiguousarray(selected_data[:, selected_position], dtype=float))
            return x_values, series_names, series_values
        else:
            return None
    else:
        return None


def get_result_table_xy(table: ResultsTable,
                        selected_rows: np.ndarray | None = None,
                        selected_y_columns: np.ndarray | None = None) -> tuple[
                            np.ndarray, list[str], list[np.ndarray]] | None:
    """Extract the first table column as X and selected later columns as Y.

    :param table: Results table whose first column stores horizontal coordinates.
    :param selected_rows: Optional row positions to retain.
    :param selected_y_columns: Optional Y-column positions.
    :return: X coordinates, Y labels, and Y buffers, or ``None`` when invalid.
    """
    data_matrix: np.ndarray = np.asarray(table.data_c, dtype=float)
    if data_matrix.ndim == 2 and data_matrix.shape[1] > 1:
        row_count: int = data_matrix.shape[0]
        if selected_rows is None:
            row_indices: np.ndarray = np.arange(row_count, dtype=np.int64)
        else:
            row_indices = np.unique(np.asarray(selected_rows, dtype=np.int64))
        if selected_y_columns is None:
            y_indices: np.ndarray = np.arange(1, data_matrix.shape[1], dtype=np.int64)
        else:
            y_indices = np.unique(np.asarray(selected_y_columns, dtype=np.int64))
            y_indices = y_indices[y_indices > 0]
        valid_rows: bool = len(row_indices) > 0 and int(np.min(row_indices)) >= 0 and int(np.max(row_indices)) < row_count
        valid_columns: bool = len(y_indices) > 0 and int(np.min(y_indices)) > 0 and int(np.max(y_indices)) < data_matrix.shape[1]
        if valid_rows and valid_columns:
            x_values: np.ndarray = np.ascontiguousarray(data_matrix[row_indices, 0], dtype=float)
            y_names: list[str] = list()
            y_values: list[np.ndarray] = list()
            y_index: int
            for y_index in y_indices:
                y_names.append(str(table.cols_c[int(y_index)]))
                y_values.append(np.ascontiguousarray(data_matrix[row_indices, int(y_index)], dtype=float))
            return x_values, y_names, y_values
        else:
            return None
    else:
        return None


def append_result_table_column(chart: GraphsWidget,
                               table: ResultsTable,
                               column_index: int,
                               series_name: str) -> bool:
    """Append one finite result-table column to an active native chart.

    :param chart: GUI-thread chart receiving copied values.
    :param table: Results table providing the source column.
    :param column_index: Visible table column corresponding to the device.
    :param series_name: Legend label for the source simulation.
    :return: Whether the chart received at least one finite point.
    """
    plot_data: tuple[np.ndarray, list[str], list[np.ndarray]] | None = get_result_table_series(
        table=table,
        selected_col_idx=np.array((column_index,), dtype=np.int64),
    )
    if plot_data is not None:
        x_values: np.ndarray = plot_data[0]
        y_values: np.ndarray = plot_data[2][0]
        if bool(np.any(np.isfinite(y_values))):
            chart.add_line_series(name=series_name, x_values=x_values, y_values=y_values)
            chart.set_axis_titles(table.x_label, table.y_label)
            return True
        else:
            return False
    else:
        return False
