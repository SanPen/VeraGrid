# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union, List, Mapping
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure
from matplotlib.text import Annotation
from VeraGridEngine.enumerations import ResultTypes, DeviceType, ResultTablePlotType
from VeraGridEngine.basic_structures import StrVec, Mat, Vec
from VeraGridEngine.Devices.types import ALL_DEV_TYPES


class ComplexPointHoverHandler:
    """
    Display the identity and coordinates of a complex point under the cursor.

    The callable object is registered directly with Matplotlib so the callback
    registry retains it for the complete lifetime of the figure.
    """

    __slots__ = ("scatter", "annotation", "figure", "axes", "labels")

    def __init__(self,
                 scatter: PathCollection,
                 annotation: Annotation,
                 figure: Figure,
                 axes: Axes,
                 labels: np.ndarray) -> None:
        """
        Initialize the complex-point hover handler.

        :param scatter: Scatter artist containing the complex points.
        :param annotation: Annotation updated when the cursor reaches a point.
        :param figure: Figure containing the scatter artist.
        :param axes: Axes containing the scatter artist.
        :param labels: Display label associated with every scatter point.
        :return: None.
        """
        self.scatter: PathCollection = scatter
        self.annotation: Annotation = annotation
        self.figure: Figure = figure
        self.axes: Axes = axes
        self.labels: np.ndarray = labels

    def __call__(self, event: MouseEvent) -> None:
        """
        Update the visible annotation for one Matplotlib mouse event.

        :param event: Mouse event emitted by the figure canvas.
        :return: None.
        """
        if event.inaxes is self.axes:
            contains_point: bool
            point_details: Mapping[str, object]
            contains_point, point_details = self.scatter.contains(event)

            if contains_point:
                point_indices_object: object | None = point_details.get("ind", None)
                if isinstance(point_indices_object, np.ndarray) and point_indices_object.size > 0:
                    point_index: int = int(point_indices_object[0])
                    point_position: np.ndarray = self.scatter.get_offsets()[point_index]
                    label: str = str(self.labels[point_index])
                    self.annotation.xy = (float(point_position[0]), float(point_position[1]))
                    self.annotation.set_text(
                        f"{label}\nRe={float(point_position[0]):.6g}, "
                        f"Im={float(point_position[1]):.6g}"
                    )
                    self.annotation.set_visible(True)
                    self.figure.canvas.draw_idle()
                else:
                    self.annotation.set_visible(False)
            else:
                if self.annotation.get_visible():
                    self.annotation.set_visible(False)
                    self.figure.canvas.draw_idle()
                else:
                    pass
        else:
            if self.annotation.get_visible():
                self.annotation.set_visible(False)
                self.figure.canvas.draw_idle()
            else:
                pass


class ResultsTable:
    """
    Class to populate a Qt table view with data from the results
    """
    __slots__ = (
        "data_c",
        "cols_c",
        "index_c",
        "editable",
        "editable_min_idx",
        "palette",
        "title",
        "x_label",
        "y_label",
        "units",
        "r",
        "c",
        "isDate",
        "decimals",
        "format_string",
        "formatter",
        "cols_device_type",
        "idx_device_type",
        "_col_devices",
        "_idx_devices",
        "plot_type",
        "damping_ratio_boundary",
        "plot_title",
        "complex_plot_x_column",
        "complex_plot_y_columns",
        "complex_plot_y_scales",
    )

    def __init__(self,
                 data: Union[Mat, Vec],
                 columns: StrVec,
                 index: StrVec | pd.DatetimeIndex,
                 title: str,
                 cols_device_type: DeviceType,
                 idx_device_type: DeviceType,
                 units: str = "",
                 xlabel: str = "",
                 ylabel: str = "",
                 editable: bool = False,
                 palette: object | None = None,
                 editable_min_idx: int = -1,
                 decimals: int = 6,
                 plot_type: ResultTablePlotType = ResultTablePlotType.SERIES,
                 damping_ratio_boundary: float | None = None,
                 plot_title: str | None = None,
                 complex_plot_x_column: str | None = None,
                 complex_plot_y_columns: StrVec | None = None,
                 complex_plot_y_scales: Vec | None = None) -> None:
        """
        ResultsTable constructor
        :param data:
        :param columns:
        :param index:
        :param palette:
        :param title:
        :param xlabel:
        :param ylabel:
        :param editable:
        :param editable_min_idx:
        :param decimals:
        :param plot_type: Graphical representation used when plotting this table.
        :param damping_ratio_boundary: Optional damping-ratio guide for complex-point plots.
        :param plot_title: Optional title used only by the plot representation.
        :param complex_plot_x_column: Column name used as the real coordinate.
        :param complex_plot_y_columns: Allowed imaginary-coordinate column names.
        :param complex_plot_y_scales: Overlay scales corresponding to the allowed imaginary columns.
        :return: None.
        """
        if data.ndim == 1:
            # assert compatible dimensions
            assert len(data) == len(index)

            self.data_c = data.reshape(-1, 1)

        elif data.ndim == 2:
            # assert compatible dimensions
            assert data.shape[0] == len(index)
            assert data.shape[1] == len(columns)

            self.data_c = data
        else:
            raise Exception("Unsupported number of dimensions {}".format(data.ndim))

        self.cols_c = columns
        self.index_c = index

        self.editable = editable
        self.editable_min_idx = editable_min_idx
        self.palette = palette
        self.title = title
        self.x_label = xlabel
        self.y_label = ylabel
        self.units = units
        self.r, self.c = self.data_c.shape
        self.isDate = False
        if self.r > 0 and self.c > 0:
            if isinstance(self.index_c[0], np.datetime64):
                self.index_c = pd.to_datetime(self.index_c)
                self.isDate = True

        self.decimals: int = decimals
        self.format_string = '.' + str(decimals) + 'f'
        self.formatter = lambda x: self.format_string % x

        self.cols_device_type: DeviceType = cols_device_type
        self.idx_device_type: DeviceType = idx_device_type

        # list of devices that match the columns or rows for filtering
        self._col_devices = list()
        self._idx_devices = list()

        # Plot semantics travel with the data so filtering and slicing retain
        # the same graphical interpretation as the source result.
        self.plot_type: ResultTablePlotType = plot_type
        self.damping_ratio_boundary: float | None = damping_ratio_boundary
        self.plot_title: str | None = plot_title
        self.complex_plot_x_column: str | None = complex_plot_x_column
        if complex_plot_y_columns is None:
            self.complex_plot_y_columns: StrVec = np.empty(0, dtype=np.str_)
        else:
            self.complex_plot_y_columns = np.asarray(complex_plot_y_columns, dtype=np.str_)
        if complex_plot_y_scales is None:
            self.complex_plot_y_scales: Vec = np.empty(0, dtype=float)
        else:
            self.complex_plot_y_scales = np.asarray(complex_plot_y_scales, dtype=float)

        if len(self.complex_plot_y_columns) == len(self.complex_plot_y_scales):
            pass
        else:
            raise ValueError("Complex plot Y columns and scales must have the same length.")

    @property
    def data(self):
        """
        Backward-compatible alias for the table numeric payload.

        :return: Table data array.
        """
        return self.data_c

    @property
    def col_devices(self):
        """

        :return:
        """
        return self._col_devices

    @property
    def idx_devices(self):
        """

        :return:
        """
        return self._idx_devices

    def set_col_devices(self, devices_list: List[ALL_DEV_TYPES]):
        """
        Set the list of devices that matches the results for filtering
        :param devices_list:
        """
        self._col_devices = devices_list

    def set_idx_devices(self, devices_list: List[ALL_DEV_TYPES]):
        """
        Set the list of devices that matches the results for filtering
        :param devices_list:
        """
        self._idx_devices = devices_list

    def transpose(self):
        """
        Transpose the results in-place
        """
        self.data_c = self.data_c.copy().transpose()
        self.r, self.c = self.data_c.shape
        self.x_label, self.y_label = self.y_label, self.x_label
        self.cols_c, self.index_c = self.index_c, self.cols_c
        self._col_devices, self._idx_devices = self._idx_devices, self._col_devices

        # Structured complex plots assign semantic roles to rows and columns.
        # Transposition changes those roles, so the transformed table reverts
        # explicitly to the ordinary series representation.
        self.plot_type = ResultTablePlotType.SERIES
        self.damping_ratio_boundary = None
        self.plot_title = None
        self.complex_plot_x_column = None
        self.complex_plot_y_columns = np.empty(0, dtype=np.str_)
        self.complex_plot_y_scales = np.empty(0, dtype=float)

    def sort_column(self, c: int, max_to_min: bool = True):
        """

        :param c:
        :param max_to_min:
        :return:
        """
        try:
            sorting_arr = self.data_c[:, c].astype(float)
        except ValueError:
            print("Not a float column...")
            sorting_arr = self.data_c[:, c]

        if max_to_min:
            idx = sorting_arr.argsort()[::-1]
        else:
            idx = sorting_arr.argsort()

        self.data_c = self.data_c[idx]
        self.index_c = self.index_c[idx]

    def slice_cols(self, col_idx) -> "ResultsTable":
        """
        Make column slicing
        :param col_idx: indices of the columns
        :return: Nothing
        """
        sliced_model = ResultsTable(data=self.data_c[:, col_idx],
                                    columns=np.array([self.cols_c[i] for i in col_idx]),
                                    index=np.array(self.index_c),
                                    palette=None,
                                    title=self.title,
                                    xlabel=self.x_label,
                                    ylabel=self.y_label,
                                    units=self.units,
                                    editable=self.editable,
                                    editable_min_idx=self.editable_min_idx,
                                    decimals=self.decimals,
                                    cols_device_type=self.cols_device_type,
                                    idx_device_type=self.idx_device_type,
                                    plot_type=self.plot_type,
                                    damping_ratio_boundary=self.damping_ratio_boundary,
                                    plot_title=self.plot_title,
                                    complex_plot_x_column=self.complex_plot_x_column,
                                    complex_plot_y_columns=self.complex_plot_y_columns,
                                    complex_plot_y_scales=self.complex_plot_y_scales)

        return sliced_model

    def slice_rows(self, idx) -> "ResultsTable":
        """
        Make rows slicing
        :param idx: indices of the columns
        :return: Nothing
        """
        sliced_model = ResultsTable(data=self.data_c[idx, :],
                                    columns=self.cols_c,
                                    index=np.array([self.index_c[i] for i in idx]),
                                    palette=None,
                                    title=self.title,
                                    xlabel=self.x_label,
                                    ylabel=self.y_label,
                                    units=self.units,
                                    editable=self.editable,
                                    editable_min_idx=self.editable_min_idx,
                                    decimals=self.decimals,
                                    cols_device_type=self.cols_device_type,
                                    idx_device_type=self.idx_device_type,
                                    plot_type=self.plot_type,
                                    damping_ratio_boundary=self.damping_ratio_boundary,
                                    plot_title=self.plot_title,
                                    complex_plot_x_column=self.complex_plot_x_column,
                                    complex_plot_y_columns=self.complex_plot_y_columns,
                                    complex_plot_y_scales=self.complex_plot_y_scales)

        return sliced_model

    def slice_all(self, row_idx, col_idx) -> "ResultsTable":
        """
        Make rows slicing
        :param row_idx: indices of the rows
        :param col_idx: indices of the columns
        :return: ResultsTable
        """
        sliced_model = ResultsTable(data=self.data_c[row_idx, :][:, col_idx],
                                    columns=np.array([self.cols_c[i] for i in col_idx]),
                                    index=np.array([self.index_c[i] for i in row_idx]),
                                    palette=None,
                                    title=self.title,
                                    xlabel=self.x_label,
                                    ylabel=self.y_label,
                                    units=self.units,
                                    editable=self.editable,
                                    editable_min_idx=self.editable_min_idx,
                                    decimals=self.decimals,
                                    cols_device_type=self.cols_device_type,
                                    idx_device_type=self.idx_device_type,
                                    plot_type=self.plot_type,
                                    damping_ratio_boundary=self.damping_ratio_boundary,
                                    plot_title=self.plot_title,
                                    complex_plot_x_column=self.complex_plot_x_column,
                                    complex_plot_y_columns=self.complex_plot_y_columns,
                                    complex_plot_y_scales=self.complex_plot_y_scales)
        return sliced_model

    def search_in_columns(self, txt):
        """
        Search stuff
        :param txt:
        :return:
        """
        idx = list()
        txt2 = str(txt).lower()
        for i, val in enumerate(self.cols_c):
            if txt2 in val.lower():
                idx.append(i)
        idx = np.array(idx, dtype=int)
        if len(idx) > 0:
            return self.slice_cols(idx)
        else:
            return None

    def search_in_rows(self, txt):
        """
        Search stuff
        :param txt:
        :return:
        """
        idx = list()
        txt2 = str(txt).lower()
        for i, val in enumerate(self.index_c):
            if txt2 in str(val).lower():
                idx.append(i)
        idx = np.array(idx, dtype=int)
        if len(idx) > 0:
            return self.slice_rows(idx)
        else:
            return None

    def copy_to_column(self, row: int, col: int):
        """
        Copies one value to all the column
        @param row: Row of the value
        @param col: Column of the value
        @return: Nothing
        """
        self.data_c[:, col] = self.data_c[row, col]

    def is_complex(self) -> bool:
        """
        Is the data complex?
        :return:
        """
        return self.data_c.dtype == complex

    def get_data(self):
        """
        Returns: index, columns, data
        """
        n = len(self.cols_c)

        if n > 0:
            # gather values
            if isinstance(self.cols_c, pd.Index):
                names = self.cols_c.values

                if len(names) > 0:
                    if isinstance(names[0], ResultTypes):
                        names = [str(val) for val in names]
            else:
                names = [str(val) for val in self.cols_c]

            values = self.data_c

            return self.index_c, names, values
        else:
            # there are no elements
            return self.index_c, list(), self.data_c

    def convert_to_cdf(self):
        """
        Convert the data in-place to CDF based
        :return:
        """

        # calculate the proportional values of samples
        n = self.data_c.shape[0]
        if n > 1:
            self.index_c = np.arange(n, dtype=float) / (n - 1)
        else:
            self.index_c = np.arange(n, dtype=float)

        for i in range(self.data_c.shape[1]):
            self.data_c[:, i] = np.sort(self.data_c[:, i].copy(), axis=0)

        self.x_label = 'Probability of value<=x'

        # Independent column sorting destroys complex coordinate pairs and
        # eigenvector component relationships.
        self.plot_type = ResultTablePlotType.SERIES
        self.damping_ratio_boundary = None
        self.plot_title = None
        self.complex_plot_x_column = None
        self.complex_plot_y_columns = np.empty(0, dtype=np.str_)
        self.complex_plot_y_scales = np.empty(0, dtype=float)

    def convert_to_abs(self):
        """
        Convert the data to abs
        :return:
        """
        try:
            self.data_c = np.abs(self.data_c)

            # Magnitudes no longer contain a real-imaginary plane, so their
            # natural representation is the existing series plot.
            self.plot_type = ResultTablePlotType.SERIES
            self.damping_ratio_boundary = None
            self.plot_title = None
            self.complex_plot_x_column = None
            self.complex_plot_y_columns = np.empty(0, dtype=np.str_)
            self.complex_plot_y_scales = np.empty(0, dtype=float)
        except TypeError:
            print('Could not convert to abs :/')

    def to_df(self) -> pd.DataFrame:
        """
        get DataFrame
        """
        index, columns, data = self.get_data()

        return pd.DataFrame(data=data, index=index, columns=columns)

    def save_to_excel(self, file_name):
        """
        save data to excel
        :param file_name:
        """
        self.to_df().to_excel(file_name)

    def save_to_csv(self, file_name):
        """
        Save data to csv
        :param file_name:
        """
        self.to_df().to_csv(file_name)

    def get_data_frame(self):
        """
        Save data to csv
        """
        index, columns, data = self.get_data()
        return pd.DataFrame(data=data, index=index, columns=columns)

    def _resolve_complex_point_columns(self,
                                       selected_col_idx: np.ndarray | None) -> tuple[int, int, float]:
        """
        Resolve the configured real and imaginary columns for a complex plot.

        With no complete-column selection, the first configured imaginary
        column is the default. Selecting columns explicitly requires exactly
        the configured real column and one allowed imaginary representation.

        :param selected_col_idx: Optional complete-column selection from the table view.
        :return: Real column index, imaginary column index, and damping-guide scale.
        """
        x_column_name: str | None = self.complex_plot_x_column
        y_column_names: np.ndarray = self.complex_plot_y_columns
        if x_column_name is not None and y_column_names.size > 0:
            pass
        else:
            raise ValueError("This table does not define complex-plane coordinate columns.")

        selected_y_column_name: str
        if selected_col_idx is None:
            selected_y_column_name = str(y_column_names[0])
        else:
            selected_columns: np.ndarray = np.unique(
                np.asarray(selected_col_idx, dtype=np.int64)
            )
            if selected_columns.size == 2:
                pass
            else:
                raise ValueError(
                    "Select exactly two complete columns: Real and one Imaginary representation."
                )

            selected_column_names: np.ndarray = np.asarray(self.cols_c, dtype=str)[selected_columns]
            if bool(np.any(selected_column_names == x_column_name)):
                pass
            else:
                raise ValueError(f"The complex-plane X coordinate must be '{x_column_name}'.")

            matching_y_names: list[str] = list()
            configured_y_name: str
            for configured_y_name in y_column_names:
                if bool(np.any(selected_column_names == configured_y_name)):
                    matching_y_names.append(str(configured_y_name))
                else:
                    pass

            if len(matching_y_names) == 1:
                selected_y_column_name = matching_y_names[0]
            else:
                allowed_y_columns: str = ", ".join(str(name) for name in y_column_names)
                raise ValueError(
                    "Select Real together with one of these columns: " + allowed_y_columns
                )

        visible_column_names: np.ndarray = np.asarray(self.cols_c, dtype=str)
        x_matches: np.ndarray = np.where(visible_column_names == x_column_name)[0]
        y_matches: np.ndarray = np.where(visible_column_names == selected_y_column_name)[0]
        scale_matches: np.ndarray = np.where(y_column_names == selected_y_column_name)[0]
        if x_matches.size == 1 and y_matches.size == 1 and scale_matches.size == 1:
            pass
        else:
            raise ValueError("The selected results no longer contain a complete complex coordinate pair.")

        x_column_index: int = int(x_matches[0])
        y_column_index: int = int(y_matches[0])
        imaginary_scale: float = float(self.complex_plot_y_scales[int(scale_matches[0])])
        return x_column_index, y_column_index, imaginary_scale

    def _plot_complex_points(self,
                             ax: Axes | None,
                             selected_col_idx: np.ndarray | None,
                             selected_rows: np.ndarray | None) -> None:
        """
        Plot rows containing paired real and imaginary coordinates.

        Row selection chooses modes. An optional complete-column selection
        chooses one of the explicitly configured imaginary representations.

        :param ax: Matplotlib axes that will contain the complex-plane plot.
        :param selected_col_idx: Optional complete-column coordinate selection.
        :param selected_rows: Optional indices of the result rows to plot.
        :return: None.
        """
        x_column_index: int
        y_column_index: int
        imaginary_scale: float
        x_column_index, y_column_index, imaginary_scale = self._resolve_complex_point_columns(
            selected_col_idx=selected_col_idx
        )

        # Use every visible mode when the user has not selected specific rows.
        row_indices: np.ndarray
        if selected_rows is None:
            row_indices = np.arange(self.r, dtype=np.int64)
        else:
            row_indices = np.asarray(selected_rows, dtype=np.int64)

        if row_indices.size > 0:
            pass
        else:
            raise ValueError("There are no visible modes to plot in the complex plane.")

        # A filtered coordinate pair is valid only when both components remain
        # finite; incomplete points cannot be placed in the complex plane.
        coordinate_data: np.ndarray = np.asarray(
            self.data_c[
                np.ix_(
                    row_indices,
                np.array((x_column_index, y_column_index), dtype=np.int64),
                )
            ],
            dtype=float,
        )
        finite_points: np.ndarray = np.logical_and(
            np.isfinite(coordinate_data[:, 0]),
            np.isfinite(coordinate_data[:, 1]),
        )
        if bool(np.any(finite_points)):
            pass
        else:
            raise ValueError("The selected modes do not contain finite Real and Imaginary coordinates.")

        real_points: np.ndarray = coordinate_data[finite_points, 0]
        imaginary_points: np.ndarray = coordinate_data[finite_points, 1]
        selected_labels: np.ndarray = np.asarray(self.index_c, dtype=str)[row_indices]
        point_labels: np.ndarray = selected_labels[finite_points]

        if ax is None:
            figure: Figure = plt.figure(figsize=(8, 6))
            plot_axes: Axes = figure.add_subplot(111)
        else:
            plot_axes = ax
            figure = plot_axes.figure

        # Restore the original S-domain colour definition: the winter map is
        # driven by the normalized distance of each mode from the imaginary axis.
        real_distances: np.ndarray = np.abs(np.nan_to_num(real_points))
        maximum_distance: float = float(np.max(real_distances))
        if maximum_distance > 0.0:
            point_colours: np.ndarray = -real_distances / maximum_distance
        else:
            point_colours = np.zeros_like(real_distances)
        scatter: PathCollection = plot_axes.scatter(
            real_points,
            imaginary_points,
            c=point_colours,
            cmap="winter",
            s=120,
            alpha=0.8,
        )

        real_span: float = float(np.max(real_points) - np.min(real_points))
        imaginary_span: float = float(np.max(imaginary_points) - np.min(imaginary_points))
        if real_span > 0.0:
            real_margin: float = real_span * 0.1
        else:
            real_margin = max(float(np.max(np.abs(real_points))) * 0.1, 1.0)
        if imaginary_span > 0.0:
            imaginary_margin: float = imaginary_span * 0.1
        else:
            imaginary_margin = max(float(np.max(np.abs(imaginary_points))) * 0.1, 1.0)

        x_min: float = float(np.min(real_points) - real_margin)
        x_max: float = float(np.max(real_points) + real_margin)
        y_min: float = float(np.min(imaginary_points) - imaginary_margin)
        y_max: float = float(np.max(imaginary_points) + imaginary_margin)

        # Draw the optional constant-damping guides in the coordinates already
        # supplied by the table, which also supports the Hz-scaled view.
        damping_ratio: float | None = self.damping_ratio_boundary
        if damping_ratio is not None and 0.0 < damping_ratio < 1.0 and x_min < 0.0:
            negative_x_max: float = min(0.0, x_max)
            if negative_x_max > x_min:
                damping_x: np.ndarray = np.linspace(x_min, negative_x_max, 400)
                damping_slope: float = float(np.sqrt(1.0 - damping_ratio ** 2) / damping_ratio)
                damping_y: np.ndarray = (
                    -damping_x * damping_slope * imaginary_scale
                )
                plot_axes.plot(
                    damping_x,
                    damping_y,
                    "--",
                    color="grey",
                    linewidth=0.8,
                    alpha=0.7,
                    label=f"ζ = {damping_ratio:.0%}",
                )
                plot_axes.plot(
                    damping_x,
                    -damping_y,
                    "--",
                    color="grey",
                    linewidth=0.8,
                    alpha=0.7,
                )
                plot_axes.legend(loc="best", fontsize="small")
            else:
                pass
        else:
            pass

        if self.plot_title is None:
            displayed_plot_title: str = self.title
        else:
            displayed_plot_title = self.plot_title
        plot_axes.set_title(displayed_plot_title, fontsize=14)
        plot_axes.set_xlabel(str(self.cols_c[x_column_index]), fontsize=11)
        plot_axes.set_ylabel(str(self.cols_c[y_column_index]), fontsize=11)
        plot_axes.axhline(0.0, color="black", linewidth=0.8)
        plot_axes.axvline(0.0, color="black", linewidth=0.8)
        plot_axes.set_xlim(x_min, x_max)
        plot_axes.set_ylim(y_min, y_max)
        plot_axes.grid(True, alpha=0.25)

        # Hover text carries the mode identity that was previously missing
        # from the S-domain plot annotation.
        annotation: Annotation = plot_axes.annotate(
            "",
            xy=(0.0, 0.0),
            xytext=(16.0, 16.0),
            textcoords="offset points",
        )
        annotation.set_visible(False)
        hover_handler: ComplexPointHoverHandler = ComplexPointHoverHandler(
            scatter=scatter,
            annotation=annotation,
            figure=figure,
            axes=plot_axes,
            labels=point_labels,
        )
        figure.canvas.mpl_connect("motion_notify_event", hover_handler)
        figure.tight_layout()

    def _plot_complex_vectors(self,
                              ax: Axes | None,
                              selected_col_idx: np.ndarray | None,
                              selected_rows: np.ndarray | None) -> None:
        """
        Plot selected complex table columns as normalized mode-shape vectors.

        Each selected column receives one subplot. Its finite row components
        are phase-aligned to the dominant component and drawn as arrows in the
        real-imaginary plane.

        :param ax: Matplotlib axes whose figure will host the subplot grid.
        :param selected_col_idx: Optional indices of the mode columns to plot.
        :param selected_rows: Optional indices of the state rows to plot.
        :return: None.
        """
        mode_indices: np.ndarray
        if selected_col_idx is None:
            mode_indices = np.arange(self.c, dtype=np.int64)
        else:
            mode_indices = np.asarray(selected_col_idx, dtype=np.int64)

        state_indices: np.ndarray
        if selected_rows is None:
            state_indices = np.arange(self.r, dtype=np.int64)
        else:
            state_indices = np.asarray(selected_rows, dtype=np.int64)

        if mode_indices.size > 0:
            pass
        else:
            raise ValueError("Select at least one right-eigenvector column to plot.")
        if state_indices.size > 0:
            pass
        else:
            raise ValueError("There are no visible state components to plot.")

        number_of_modes: int = int(mode_indices.size)
        number_of_columns: int = min(3, number_of_modes)
        number_of_rows: int = int(np.ceil(number_of_modes / number_of_columns))

        if ax is None:
            figure: Figure = plt.figure(
                figsize=(5.5 * number_of_columns, 5.0 * number_of_rows)
            )
        else:
            figure = ax.figure
            figure.clear()

        axes_matrix: np.ndarray = np.asarray(
            figure.subplots(number_of_rows, number_of_columns, squeeze=False),
            dtype=object,
        )
        flat_axes: np.ndarray = axes_matrix.ravel()
        state_names: np.ndarray = np.asarray(self.index_c, dtype=str)

        plot_position: int
        mode_index: int
        for plot_position, mode_index in enumerate(mode_indices):
            mode_axes: Axes = flat_axes[plot_position]
            mode_values: np.ndarray = np.asarray(
                self.data_c[state_indices, mode_index],
                dtype=complex,
            )
            finite_components: np.ndarray = np.logical_and(
                np.isfinite(mode_values.real),
                np.isfinite(mode_values.imag),
            )
            visible_values: np.ndarray = mode_values[finite_components]
            visible_state_indices: np.ndarray = state_indices[finite_components]

            if visible_values.size > 0:
                magnitudes: np.ndarray = np.abs(visible_values)
                reference_position: int = int(np.argmax(magnitudes))
                reference_magnitude: float = float(magnitudes[reference_position])
                if reference_magnitude > 0.0:
                    reference_phase: float = float(np.angle(visible_values[reference_position]))
                    aligned_values: np.ndarray = (
                        visible_values * np.exp(-1j * reference_phase) / reference_magnitude
                    )
                else:
                    aligned_values = np.zeros_like(visible_values)

                # Every state is an arrow from the common origin, making both
                # relative magnitude and relative phase directly observable.
                component_position: int
                state_index: int
                for component_position, state_index in enumerate(visible_state_indices):
                    component: complex = complex(aligned_values[component_position])
                    component_color: str = f"C{component_position % 10}"
                    mode_axes.arrow(
                        0.0,
                        0.0,
                        component.real,
                        component.imag,
                        width=0.006,
                        length_includes_head=True,
                        color=component_color,
                        alpha=0.85,
                    )
                    mode_axes.text(
                        component.real * 1.04,
                        component.imag * 1.04,
                        str(state_names[state_index]),
                        color=component_color,
                        fontsize=8,
                    )
            else:
                mode_axes.text(
                    0.5,
                    0.5,
                    "No finite components",
                    horizontalalignment="center",
                    verticalalignment="center",
                    transform=mode_axes.transAxes,
                )

            unit_circle_angles: np.ndarray = np.linspace(0.0, 2.0 * np.pi, 361)
            mode_axes.plot(
                np.cos(unit_circle_angles),
                np.sin(unit_circle_angles),
                color="grey",
                linewidth=0.7,
                alpha=0.5,
            )
            mode_axes.axhline(0.0, color="black", linewidth=0.6)
            mode_axes.axvline(0.0, color="black", linewidth=0.6)
            mode_axes.set_xlim(-1.15, 1.15)
            mode_axes.set_ylim(-1.15, 1.15)
            mode_axes.set_aspect("equal", adjustable="box")
            mode_axes.set_xlabel("Real")
            mode_axes.set_ylabel("Imaginary")
            mode_axes.set_title(str(self.cols_c[mode_index]), fontsize=10)
            mode_axes.grid(True, alpha=0.25)

        # Unused grid cells are hidden so selecting two or five modes does not
        # leave distracting empty coordinate systems in the figure.
        for plot_position in range(number_of_modes, int(flat_axes.size)):
            unused_axes: Axes = flat_axes[plot_position]
            unused_axes.set_visible(False)

        figure.suptitle(self.title, fontsize=13, fontweight="bold")
        figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))

    def plot(self,
             ax: Axes | None = None,
             selected_col_idx: np.ndarray | None = None,
             selected_rows: np.ndarray | None = None,
             stacked: bool = False) -> None:
        """
        Plot the data model
        :param ax: Matplotlib axis
        :param selected_col_idx: list of selected column indices
        :param selected_rows: list of rows to plot
        :param stacked: Stack plot?
        :return: None.
        """
        if self.plot_type == ResultTablePlotType.COMPLEX_POINTS:
            self._plot_complex_points(
                ax=ax,
                selected_col_idx=selected_col_idx,
                selected_rows=selected_rows,
            )
            return
        elif self.plot_type == ResultTablePlotType.COMPLEX_VECTORS:
            self._plot_complex_vectors(
                ax=ax,
                selected_col_idx=selected_col_idx,
                selected_rows=selected_rows,
            )
            return
        else:
            pass

        index, columns, data = self.get_data()

        if selected_col_idx is not None:
            columns = [columns[i] for i in selected_col_idx]
            data = data[:, selected_col_idx]

        if selected_rows is not None:
            index = [index[i] for i in selected_rows]
            data = data[selected_rows, :]

        if ax is None:
            fig = plt.figure(figsize=(12, 6))
            ax = fig.add_subplot(111)

        if 'voltage' in self.title.lower():
            data[data == 0] = 'nan'  # to avoid plotting the zeros

        if len(columns) > 15:
            plot_legend = False
        else:
            plot_legend = True

        df = pd.DataFrame(data=data, index=index, columns=columns)

        if stacked and len(columns) > 1:
            # --- 1. Filter Out Columns That Are Entirely Zero ---
            df_filtered = df.loc[:, (df != 0).any()]
            data = df_filtered.values  # Convert the filtered DataFrame to a NumPy array
            n_series = data.shape[1]

            # --- 2. Prepare the Positive and Negative Parts ---
            # For positive plotting: keep positive values and set non-positive ones to 0.
            data_pos = np.where(data > 0, data, 0)
            # For negative plotting: keep negative values and set non-negative ones to 0.
            data_neg = np.where(data < 0, data, 0)

            # --- 3. Compute Cumulative Sums Along the Series Axis ---
            cum_pos = np.cumsum(data_pos, axis=1)
            cum_neg = np.cumsum(data_neg, axis=1)

            # --- 4. Plot Using Matplotlib's fill_between ---
            # Use a colormap to generate distinct colors for each series.
            colors = plt.cm.viridis(np.linspace(0, 1, n_series))

            # x-axis will use the DataFrame's DatetimeIndex.
            x = df_filtered.index

            # Plot the positive areas for each series.
            for i in range(n_series):
                if i == 0:
                    if cum_pos[:, i].sum() != 0:
                        ax.fill_between(x, 0, cum_pos[:, i], color=colors[i],
                            label=f'{df_filtered.columns[i]}')
                else:
                    if cum_pos[:, i].sum() != 0:
                        ax.fill_between(x, cum_pos[:, i - 1], cum_pos[:, i], color=colors[i],
                            label=f'{df_filtered.columns[i]}')

            # Plot the negative areas for each series.
            for i in range(n_series):
                if i == 0:
                    if cum_neg[:, i].sum() != 0:
                        ax.fill_between(x, 0, cum_neg[:, i], color=colors[i], alpha=0.6,
                            label=f'{df_filtered.columns[i]}')
                else:
                    if cum_neg[:, i].sum() != 0:
                        ax.fill_between(x, cum_neg[:, i - 1], cum_neg[:, i], color=colors[i], alpha=0.6,
                            label=f'{df_filtered.columns[i]}')

            # Add legend and labels for clarity
            ax.set_title(self.title, fontsize=14)
            ax.set_ylabel(self.y_label, fontsize=11)
            ax.set_xlabel(self.x_label, fontsize=11)
            ax.legend(loc='upper right', fontsize='small')
        else:
            ax.set_title(self.title, fontsize=14)
            ax.set_ylabel(self.y_label, fontsize=11)
            ax.set_xlabel(self.x_label, fontsize=11)
            try:
                df.plot(ax=ax, legend=plot_legend)
            except TypeError:
                print('No numeric data to plot...')

    def plot_device(self, ax=None, device_idx: int = 0, stacked=False, title: str = ""):
        """
        Plot the data model
        :param ax: Matplotlib axis
        :param device_idx: list of selected column indices
        :param stacked: Stack plot?
        :param title: Title of the plot
        """
        index, columns, data = self.get_data()

        # columns = [columns[device_idx]]
        columns = [self.title] if title == "" else [title]
        data = data[:, device_idx]

        if ax is None:
            fig = plt.figure(figsize=(12, 6))
            ax = fig.add_subplot(111)

        if 'voltage' in self.title.lower():
            data[data == 0] = 'nan'  # to avoid plotting the zeros

        if len(columns) > 15:
            plot_legend = False
        else:
            plot_legend = True

        df = pd.DataFrame(data=data, index=index, columns=columns)
        ax.set_title(self.title, fontsize=14)
        ax.set_ylabel(self.y_label, fontsize=11)
        ax.set_xlabel(self.x_label, fontsize=11)
        try:
            df.plot(ax=ax, legend=plot_legend, stacked=stacked)
        except TypeError:
            print('No numeric data to plot...')
