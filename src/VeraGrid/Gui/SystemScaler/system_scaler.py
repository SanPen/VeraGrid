# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
import sys
from typing import Sequence, Union
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QApplication
from PySide6 import QtCore, QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

from VeraGrid.Gui.SystemScaler.system_scaler_ui import Ui_Dialog
from VeraGrid.Gui.gui_functions import ComboDelegate, FloatDelegate
from VeraGrid.Gui.messages import yes_no_question
from VeraGridEngine.enumerations import DeviceType
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Profiles.profile_float import ProfileFloat


class SystemScalingModel(QtCore.QAbstractTableModel):
    """
    Class to populate a Qt table view with a pandas data frame
    """

    def __init__(self,
                 device_tpe: DeviceType,
                 grid: MultiCircuit,
                 parent: QtWidgets.QTableView,
                 set_delegates: bool = True):
        """

        :param device_tpe:
        :param grid:
        :param parent:
        :param set_delegates: Set the float delegates on the parent table.
        """
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.parent = parent
        self.device_tpe = device_tpe
        self.grid = grid
        self.objects = self.grid.get_elements_by_type(device_type=device_tpe)
        self.injections_per_type = self.grid.get_injection_devices_grouped_by_group_type(group_type=device_tpe)

        self._cols = ['Load factor', 'Generation factor']
        self._editable = [True, True]
        self._index = [elm.name for elm in self.objects]
        self.r = len(self._index)
        self.c = len(self._cols)
        self._data = np.ones((self.r, self.c + 2))
        self.isDate = False

        if len(self._index) > 0:
            if isinstance(self._index[0], np.datetime64):
                self._index = pd.to_datetime(self._index)
                self.isDate = True

        if set_delegates:
            self.set_delegates()
        else:
            pass

        self.original_powers = np.zeros((self.r, 2))

        # compute totals per type
        for i in range(self.r):
            gens = self.injections_per_type[i].get(DeviceType.GeneratorDevice, list())
            loads = self.injections_per_type[i].get(DeviceType.LoadDevice, list())

            # get the original area, zone, etc. power
            self.original_powers[i, 0] = sum([elm.P for elm in loads])
            self.original_powers[i, 1] = sum([elm.P for elm in gens])

            # compute the total scaling power of the area, zone, etc...
            self._data[i, 2] = self.original_powers[i, 0] * self._data[i, 0]
            self._data[i, 3] = self.original_powers[i, 1] * self._data[i, 1]

    def flags(self, index: QtCore.QModelIndex):
        """
        Get the display mode
        :param index:
        :return:
        """

        if self._editable[index.column()]:
            return (QtCore.Qt.ItemFlag.ItemIsEditable |
                    QtCore.Qt.ItemFlag.ItemIsEnabled |
                    QtCore.Qt.ItemFlag.ItemIsSelectable)
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled

    def update(self):
        """
        update table
        """
        # row = self.rowCount()
        # self.beginInsertRows(QtCore.QModelIndex(), row, row)
        # # whatever code
        # self.endInsertRows()
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()

    def set_delegates(self) -> None:
        """
        Set the cell editor types depending on the attribute_types array
        """

        for i in range(self.c):
            delegate = FloatDelegate(self.parent)
            self.parent.setItemDelegateForColumn(i, delegate)

    def rowCount(self, parent: Union[QtCore.QModelIndex, None] = None):
        """

        :param parent:
        :return:
        """
        return self.r

    def columnCount(self, parent: Union[QtCore.QModelIndex, None] = None):
        """

        :param parent:
        :return:
        """
        return self.c

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """

        :param index:
        :param role:
        :return:
        """
        if index.isValid():
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return "%.2f" % self._data[index.row(), index.column()]
                # return str(self._data[index.row(), index.column()])
        return None

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role=QtCore.Qt.ItemDataRole.DisplayRole):
        """

        :param section:
        :param orientation:
        :param role:
        :return:
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self._cols[section]
            elif orientation == QtCore.Qt.Orientation.Vertical:
                if self._index is None:
                    return section
                else:
                    if self.isDate:
                        return self._index[section].strftime('%Y/%m/%d  %H:%M.%S')
                    else:
                        return str(self._index[section])
        return None

    def setData(self, index, value, role=QtCore.Qt.ItemDataRole.DisplayRole):
        """

        :param index:
        :param value:
        :param role:
        :return:
        """
        if self._editable[index.column()]:
            if value != "":
                i = index.row()
                self._data[i, index.column()] = value

                # update the total scaling power of the area, zone, etc...
                self._data[i, 2] = self.original_powers[i, 0] * self._data[i, 0]
                self._data[i, 3] = self.original_powers[i, 1] * self._data[i, 1]
                self.dataChanged.emit(index, self.index(i, 1), [role])
            else:
                pass
        else:
            pass

        return True

    def apply_scaling(self, with_time_series: bool = False):
        """
        Aply the scaling to the objects
        :param with_time_series: scale time profiles too?
        """
        for i in range(self.r):
            gens = self.injections_per_type[i].get(DeviceType.GeneratorDevice, list())
            loads = self.injections_per_type[i].get(DeviceType.LoadDevice, list())
            load_scale = self._data[i, 0]
            gen_scale = self._data[i, 1]

            for elm in loads:
                elm.P *= load_scale
                elm.Q *= load_scale
                elm.G *= load_scale
                elm.B *= load_scale
                elm.Ii *= load_scale
                elm.Ir *= load_scale

                if with_time_series:
                    elm.P_prof *= load_scale
                    elm.Q_prof *= load_scale
                    elm.G_prof *= load_scale
                    elm.B_prof *= load_scale
                    elm.Ii_prof *= load_scale
                    elm.Ir_prof *= load_scale

            for elm in gens:
                elm.P *= gen_scale

                if with_time_series:
                    elm.P_prof *= gen_scale

    def set_load_generation_scaling_factors(self, factors: np.ndarray) -> None:
        """
        Set the editable load/generation scaling factors.

        :param factors: array with shape (number of groups, 2)
        """
        if factors.shape != (self.r, 2):
            raise ValueError(f"Expected scaling factors with shape {(self.r, 2)}, got {factors.shape}")
        else:
            pass

        self._data[:, 0:2] = factors
        self._data[:, 2] = self.original_powers[:, 0] * self._data[:, 0]
        self._data[:, 3] = self.original_powers[:, 1] * self._data[:, 1]
        self.update()


class SystemScalingCheckpoint:
    """
    Typed container for a temporal scaling checkpoint.
    """

    __slots__ = ("time_key", "model")

    def __init__(self, time_key: object, model: "SystemScalingModel") -> None:
        """
        Constructor.

        :param time_key: Integer time index or timestamp-like value from the grid time profile.
        :param model: Scaling model with the factors to enforce at the checkpoint time.
        """
        self.time_key: object = time_key
        self.model: "SystemScalingModel" = model


class SystemScalingCheckpointsModel(QtCore.QAbstractTableModel):
    """
    Table model showing the configured scaling checkpoints.
    """

    def __init__(self,
                 checkpoints: list[SystemScalingCheckpoint],
                 groups: list[DeviceType],
                 grid: MultiCircuit,
                 parent: QtWidgets.QTableView,
                 data_parent: QtWidgets.QTableView) -> None:
        """
        Constructor.

        :param checkpoints: Checkpoint list owned by the dialog.
        :param groups: Available grouping device types.
        :param grid: Grid to scale.
        :param parent: Parent table view.
        :param data_parent: Parent table view for checkpoint group data models.
        """
        QtCore.QAbstractTableModel.__init__(self, parent)

        self.parent: QtWidgets.QTableView = parent
        self.data_parent: QtWidgets.QTableView = data_parent
        self.checkpoints: list[SystemScalingCheckpoint] = checkpoints
        self.groups: list[DeviceType] = groups
        self.grid: MultiCircuit = grid
        self._cols: list[str] = [
            "Time",
            "Grouping",
            "Total load (MW)",
            "Total generation (MW)",
        ]
        self._editable: list[bool] = [True, True, False, False]

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        Get the display mode.

        :param index: Model index.
        :return: Qt item flags.
        """
        flags: QtCore.Qt.ItemFlag

        if index.isValid():
            flags = (QtCore.Qt.ItemFlag.ItemIsEnabled |
                     QtCore.Qt.ItemFlag.ItemIsSelectable)

            if self._editable[index.column()]:
                flags = flags | QtCore.Qt.ItemFlag.ItemIsEditable
            else:
                pass

            return flags
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled

    def rowCount(self, parent: Union[QtCore.QModelIndex, None] = None) -> int:
        """
        Get the number of rows.

        :param parent: Parent model index.
        :return: Number of checkpoints.
        """
        return len(self.checkpoints)

    def columnCount(self, parent: Union[QtCore.QModelIndex, None] = None) -> int:
        """
        Get the number of columns.

        :param parent: Parent model index.
        :return: Number of columns.
        """
        return len(self._cols)

    def get_checkpoint_and_group_indices(self, row: int) -> tuple[int, int]:
        """
        Convert a table row into checkpoint and group row indices.

        :param row: Flat table row.
        :return: Checkpoint index and group index.
        """
        if 0 <= row < len(self.checkpoints):
            return row, 0
        else:
            return 0, 0

    def get_first_row_of_checkpoint(self, checkpoint_idx: int) -> int:
        """
        Get the first flat table row for a checkpoint.

        :param checkpoint_idx: Checkpoint index.
        :return: First table row.
        """
        return checkpoint_idx

    def get_previous_time_index(self, checkpoint_idx: int) -> Union[int, None]:
        """
        Get the previous temporal checkpoint index.

        :param checkpoint_idx: Checkpoint row index.
        :return: Previous temporal index or ``None``.
        """
        previous_time_idx: Union[int, None] = None

        if self.grid.time_profile is not None and len(self.grid.time_profile) > 0:
            for row_idx in range(checkpoint_idx):
                checkpoint: SystemScalingCheckpoint = self.checkpoints[row_idx]

                if checkpoint.time_key is None:
                    pass
                else:
                    previous_time_idx = get_checkpoint_time_index(time_profile=self.grid.time_profile,
                                                                  time_key=checkpoint.time_key)
        else:
            pass

        return previous_time_idx

    def get_next_time_index(self, checkpoint_idx: int) -> Union[int, None]:
        """
        Get the next temporal checkpoint index.

        :param checkpoint_idx: Checkpoint row index.
        :return: Next temporal index or ``None``.
        """
        next_time_idx: Union[int, None] = None
        found: bool = False

        if self.grid.time_profile is not None and len(self.grid.time_profile) > 0:
            row_idx: int = checkpoint_idx + 1

            while row_idx < len(self.checkpoints) and not found:
                checkpoint: SystemScalingCheckpoint = self.checkpoints[row_idx]

                if checkpoint.time_key is None:
                    pass
                else:
                    next_time_idx = get_checkpoint_time_index(time_profile=self.grid.time_profile,
                                                              time_key=checkpoint.time_key)
                    found = True

                row_idx += 1
        else:
            pass

        return next_time_idx

    def is_valid_time_index_for_row(self, checkpoint_idx: int, time_idx: Union[int, None]) -> bool:
        """
        Check whether a checkpoint time keeps the table strictly increasing.

        :param checkpoint_idx: Checkpoint row index.
        :param time_idx: Candidate time index.
        :return: ``True`` if the candidate keeps checkpoint times ordered.
        """
        valid: bool = True

        if time_idx is None:
            if checkpoint_idx == 0:
                valid = True
            else:
                valid = False
        else:
            previous_time_idx: Union[int, None] = self.get_previous_time_index(checkpoint_idx=checkpoint_idx)
            next_time_idx: Union[int, None] = self.get_next_time_index(checkpoint_idx=checkpoint_idx)

            if previous_time_idx is not None and time_idx <= previous_time_idx:
                valid = False
            else:
                pass

            if next_time_idx is not None and time_idx >= next_time_idx:
                valid = False
            else:
                pass

        return valid

    def get_cumulative_factors_for_checkpoint(self, checkpoint_idx: int) -> np.ndarray:
        """
        Get effective cumulative factors for a checkpoint row.

        :param checkpoint_idx: Checkpoint row index.
        :return: Effective load/generation factor matrix.
        """
        checkpoint: SystemScalingCheckpoint = self.checkpoints[checkpoint_idx]
        cumulative_factors: np.ndarray = np.ones((checkpoint.model.r, 2), dtype=float)

        for row_idx in range(checkpoint_idx + 1):
            previous_checkpoint: SystemScalingCheckpoint = self.checkpoints[row_idx]

            # Cumulative factors only compose within the same grouping table.
            if previous_checkpoint.model.device_tpe == checkpoint.model.device_tpe:
                if previous_checkpoint.model._data[:, 0:2].shape == cumulative_factors.shape:
                    cumulative_factors *= previous_checkpoint.model._data[:, 0:2]
                else:
                    pass
            else:
                pass

        return cumulative_factors

    def get_effective_total_load_for_checkpoint(self, checkpoint_idx: int) -> float:
        """
        Get the effective cumulative total load for a checkpoint.

        :param checkpoint_idx: Checkpoint row index.
        :return: Effective total load.
        """
        checkpoint: SystemScalingCheckpoint = self.checkpoints[checkpoint_idx]
        cumulative_factors: np.ndarray = self.get_cumulative_factors_for_checkpoint(checkpoint_idx=checkpoint_idx)
        total_load: float = float(np.sum(checkpoint.model.original_powers[:, 0] * cumulative_factors[:, 0]))

        return total_load

    def get_effective_total_generation_for_checkpoint(self, checkpoint_idx: int) -> float:
        """
        Get the effective cumulative total generation for a checkpoint.

        :param checkpoint_idx: Checkpoint row index.
        :return: Effective total generation.
        """
        checkpoint: SystemScalingCheckpoint = self.checkpoints[checkpoint_idx]
        cumulative_factors: np.ndarray = self.get_cumulative_factors_for_checkpoint(checkpoint_idx=checkpoint_idx)
        total_generation: float = float(np.sum(checkpoint.model.original_powers[:, 1] * cumulative_factors[:, 1]))

        return total_generation

    def data(self,
             index: QtCore.QModelIndex,
             role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole) -> Union[str, None]:
        """
        Get the displayed checkpoint value.

        :param index: Model index.
        :param role: Qt data role.
        :return: Display value or ``None``.
        """
        value: Union[str, None]

        if index.isValid():
            if role == QtCore.Qt.ItemDataRole.DisplayRole or role == QtCore.Qt.ItemDataRole.EditRole:
                checkpoint_idx: int = index.row()
                checkpoint: SystemScalingCheckpoint = self.checkpoints[checkpoint_idx]

                if index.column() == 0:
                    if checkpoint.time_key is None:
                        value = "None"
                    elif isinstance(checkpoint.time_key, (int, np.integer)):
                        time_idx: int = int(checkpoint.time_key)

                        if self.grid.time_profile is not None and 0 <= time_idx < len(self.grid.time_profile):
                            value = str(self.grid.time_profile[time_idx])
                        else:
                            value = str(checkpoint.time_key)
                    else:
                        value = str(checkpoint.time_key)
                elif index.column() == 1:
                    value = checkpoint.model.device_tpe.value
                elif index.column() == 2:
                    value = "%.2f" % self.get_effective_total_load_for_checkpoint(checkpoint_idx=checkpoint_idx)
                elif index.column() == 3:
                    value = "%.2f" % self.get_effective_total_generation_for_checkpoint(checkpoint_idx=checkpoint_idx)
                else:
                    value = str(checkpoint.time_key)

                return value
            else:
                return None
        else:
            return None

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole) -> Union[str, int, None]:
        """
        Get the table headers.

        :param section: Header section.
        :param orientation: Header orientation.
        :param role: Qt data role.
        :return: Header value or ``None``.
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self._cols[section]
            else:
                return section
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.EditRole) -> bool:
        """
        Set the editable checkpoint value.

        :param index: Model index.
        :param value: New value.
        :param role: Qt data role.
        :return: True if the value was accepted.
        """
        accepted: bool = False

        if index.isValid() and role == QtCore.Qt.ItemDataRole.EditRole and self._editable[index.column()]:
            checkpoint_idx: int = index.row()
            checkpoint: SystemScalingCheckpoint = self.checkpoints[checkpoint_idx]

            if index.column() == 0:
                text_value: str = str(value).strip()

                if text_value == "" or text_value.lower() == "none":
                    if self.is_valid_time_index_for_row(checkpoint_idx=checkpoint_idx, time_idx=None):
                        checkpoint.time_key = None
                        self.dataChanged.emit(index, self.index(len(self.checkpoints) - 1, 3), [role])
                        accepted = True
                    else:
                        accepted = False
                else:
                    time_idx: int = get_checkpoint_time_index(time_profile=self.grid.time_profile,
                                                              time_key=value)

                    if self.is_valid_time_index_for_row(checkpoint_idx=checkpoint_idx, time_idx=time_idx):
                        checkpoint.time_key = time_idx
                        self.dataChanged.emit(index, self.index(len(self.checkpoints) - 1, 3), [role])
                        accepted = True
                    else:
                        accepted = False
            elif index.column() == 1:
                if isinstance(value, DeviceType):
                    if checkpoint.model.device_tpe == value:
                        accepted = True
                    else:
                        model: SystemScalingModel = SystemScalingModel(device_tpe=value,
                                                                       grid=self.grid,
                                                                       parent=self.data_parent,
                                                                       set_delegates=False)
                        checkpoint.model = model
                        self.dataChanged.emit(self.index(index.row(), 0),
                                              self.index(len(self.checkpoints) - 1, 3),
                                              [role])
                        self.update()
                        accepted = True
                else:
                    accepted = False
            else:
                accepted = False
        else:
            accepted = False

        return accepted

    def update(self) -> None:
        """
        Notify the view that the checkpoint table changed.

        :return: Nothing.
        """
        self.layoutAboutToBeChanged.emit()
        self.layoutChanged.emit()


def get_system_scaling_model_group_signature(model: "SystemScalingModel") -> tuple[tuple[DeviceType, str], ...]:
    """
    Build a stable group signature to validate checkpoint compatibility.

    :param model: System scaling model.
    :return: Tuple of group device type and idtag pairs.
    """
    signature: list[tuple[DeviceType, str]] = list()

    # Checkpoints can only be interpolated if every row refers to the same group object.
    for elm in model.objects:
        signature.append((elm.device_type, elm.idtag))

    return tuple(signature)


def get_checkpoint_time_index(time_profile: pd.DatetimeIndex, time_key: object) -> int:
    """
    Convert a checkpoint key into a position in the master time profile.

    :param time_profile: Grid time profile.
    :param time_key: Integer position or timestamp-like value.
    :return: Integer time index.
    """
    idx: int

    # Integer keys are already positions in the time series vector.
    if isinstance(time_key, (int, np.integer)):
        idx = int(time_key)

        if 0 <= idx < len(time_profile):
            return idx
        else:
            raise IndexError(f"Checkpoint index {idx} is outside the time profile")
    else:
        text_value: str = str(time_key).strip()

        if text_value.isdigit():
            idx = int(text_value)

            if 0 <= idx < len(time_profile):
                return idx
            else:
                raise IndexError(f"Checkpoint index {idx} is outside the time profile")
        else:
            timestamp: pd.Timestamp = pd.Timestamp(time_key)
            positions: np.ndarray = time_profile.get_indexer([timestamp])
            idx = int(positions[0])

            if idx >= 0:
                return idx
            else:
                raise KeyError(f"Checkpoint timestamp {timestamp} is not present in the time profile")


def get_cumulative_checkpoint_values(checkpoint_indices: np.ndarray,
                                     checkpoint_values: np.ndarray,
                                     values_are_incremental: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert incremental checkpoint factors into cumulative factors ordered by time.

    :param checkpoint_indices: Integer checkpoint time indices.
    :param checkpoint_values: Incremental checkpoint factors with shape ``(checkpoint, group, factor)``.
    :param values_are_incremental: Whether the checkpoint values must be multiplied cumulatively.
    :return: Unique checkpoint indices and cumulative factors.
    """
    n_checkpoints: int = len(checkpoint_indices)
    n_groups: int = checkpoint_values.shape[1]
    n_factors: int = checkpoint_values.shape[2]
    order: np.ndarray = np.argsort(checkpoint_indices, kind="stable")
    sorted_indices: np.ndarray = checkpoint_indices[order].astype(float)
    sorted_values: np.ndarray = checkpoint_values[order, :, :]
    unique_count: int = len(np.unique(sorted_indices))
    unique_indices: np.ndarray = np.zeros(unique_count, dtype=float)
    unique_values: np.ndarray = np.ones((unique_count, n_groups, n_factors), dtype=float)
    cumulative_values: np.ndarray = np.ones((n_groups, n_factors), dtype=float)
    unique_idx: int = -1

    # Each declared checkpoint is an increment over the previously declared effective factor.
    # Duplicate times are still applied in declaration order and represented by the last effective value at that time.
    for sorted_idx in range(n_checkpoints):
        if values_are_incremental:
            cumulative_values *= sorted_values[sorted_idx, :, :]
        else:
            cumulative_values = sorted_values[sorted_idx, :, :].copy()

        if unique_idx >= 0 and sorted_indices[sorted_idx] == unique_indices[unique_idx]:
            unique_values[unique_idx, :, :] = cumulative_values
        else:
            unique_idx += 1
            unique_indices[unique_idx] = sorted_indices[sorted_idx]
            unique_values[unique_idx, :, :] = cumulative_values

    return unique_indices, unique_values


def interpolate_time_series_scaling(
        time_profile: pd.DatetimeIndex,
        checkpoints: Sequence[SystemScalingCheckpoint],
) -> np.ndarray:
    """
    Interpolate cumulative load/generation scaling factors over a time profile.

    The returned array has shape ``(time, group, 2)``, where the last dimension is
    load factor and generation factor. Declared checkpoint values are incremental
    over the previous declared factor. Values outside the checkpoint span use the
    closest cumulative checkpoint value.

    :param time_profile: Grid time profile.
    :param checkpoints: Scaling checkpoints to interpolate.
    :return: Interpolated scaling factors.
    """
    if time_profile is None or time_profile is pd.NaT or len(time_profile) == 0:
        raise ValueError("Cannot interpolate temporal scaling without a time profile")
    else:
        pass

    if len(checkpoints) == 0:
        raise ValueError("At least one scaling checkpoint is required")
    else:
        pass

    reference_model: SystemScalingModel = checkpoints[0].model
    reference_signature: tuple[tuple[DeviceType, str], ...] = get_system_scaling_model_group_signature(
        model=reference_model
    )
    n_groups: int = reference_model.r
    n_checkpoints: int = len(checkpoints)
    time_index: pd.DatetimeIndex = pd.DatetimeIndex(pd.to_datetime(time_profile))

    checkpoint_indices: np.ndarray = np.zeros(n_checkpoints, dtype=int)
    checkpoint_values: np.ndarray = np.zeros((n_checkpoints, n_groups, 2), dtype=float)

    # Load every checkpoint into fixed-size arrays before interpolation.
    for checkpoint_idx in range(n_checkpoints):
        checkpoint: SystemScalingCheckpoint = checkpoints[checkpoint_idx]
        model: SystemScalingModel = checkpoint.model

        if model.device_tpe != reference_model.device_tpe:
            raise ValueError("All temporal scaling checkpoints must use the same grouping type")
        else:
            pass

        if get_system_scaling_model_group_signature(model=model) != reference_signature:
            raise ValueError("All temporal scaling checkpoints must contain the same groups in the same order")
        else:
            pass

        checkpoint_indices[checkpoint_idx] = get_checkpoint_time_index(
            time_profile=time_index,
            time_key=checkpoint.time_key,
        )
        checkpoint_values[checkpoint_idx, :, :] = model._data[:, 0:2]

    unique_indices: np.ndarray
    unique_values: np.ndarray
    unique_indices, unique_values = get_cumulative_checkpoint_values(checkpoint_indices=checkpoint_indices,
                                                                     checkpoint_values=checkpoint_values)

    x: np.ndarray = np.arange(len(time_index), dtype=float)
    result: np.ndarray = np.ones((len(time_index), n_groups, 2), dtype=float)

    # Each group and factor is interpolated independently because regions can evolve differently.
    for group_idx in range(n_groups):
        for scale_idx in range(2):
            result[:, group_idx, scale_idx] = np.interp(
                x=x,
                xp=unique_indices,
                fp=unique_values[:, group_idx, scale_idx],
            )

    return result


def scale_float_profile_values(profile: ProfileFloat, scaling_vector: np.ndarray) -> None:
    """
    Scale a float profile by a temporal vector.

    :param profile: Profile to scale.
    :param scaling_vector: Vector with one scaling factor per time step.
    :return: Nothing.
    """
    values: np.ndarray = profile.toarray()

    if len(values) != len(scaling_vector):
        raise ValueError(
            f"Profile length {len(values)} does not match temporal scaling length {len(scaling_vector)}"
        )
    else:
        # The original profile shape is preserved; only its numeric values are scaled.
        profile.set(values * scaling_vector)


def scale_load_time_series_profiles(load: Load, scaling_vector: np.ndarray) -> None:
    """
    Scale all load power time series profiles by a temporal vector.

    :param load: Load device to scale.
    :param scaling_vector: Vector with one scaling factor per time step.
    :return: Nothing.
    """
    # ZIP load components represent one demand object, so all power components use the same temporal factor.
    scale_float_profile_values(profile=load.P_prof, scaling_vector=scaling_vector)
    scale_float_profile_values(profile=load.Q_prof, scaling_vector=scaling_vector)
    scale_float_profile_values(profile=load.G_prof, scaling_vector=scaling_vector)
    scale_float_profile_values(profile=load.B_prof, scaling_vector=scaling_vector)
    scale_float_profile_values(profile=load.Ii_prof, scaling_vector=scaling_vector)
    scale_float_profile_values(profile=load.Ir_prof, scaling_vector=scaling_vector)


def get_load_time_series_values(load: Load, time_profile: pd.DatetimeIndex) -> np.ndarray:
    """
    Get the active load values used by the scaler preview.

    :param load: Load device.
    :param time_profile: Grid time profile.
    :return: Active load vector in MW.
    """
    values: np.ndarray

    load.ensure_profiles_exist(time_profile)
    values = load.P_prof.toarray() + load.G_prof.toarray() + load.Ir_prof.toarray()

    return values


def get_generator_time_series_values(generator: Generator, time_profile: pd.DatetimeIndex) -> np.ndarray:
    """
    Get the active generation values used by the scaler preview.

    :param generator: Generator device.
    :param time_profile: Grid time profile.
    :return: Active generation vector in MW.
    """
    values: np.ndarray

    generator.ensure_profiles_exist(time_profile)
    values = generator.P_prof.toarray()

    return values


def apply_time_series_scaling_from_checkpoints(
        model: "SystemScalingModel",
        checkpoints: Sequence[SystemScalingCheckpoint],
) -> np.ndarray:
    """
    Apply temporally interpolated checkpoint scaling to load and generator profiles.

    :param model: System scaling model that defines the target grouping.
    :param checkpoints: Scaling checkpoints to interpolate.
    :return: Interpolated scaling factors with shape ``(time, group, 2)``.
    """
    time_profile: pd.DatetimeIndex = model.grid.time_profile
    temporal_scaling: np.ndarray = interpolate_time_series_scaling(
        time_profile=time_profile,
        checkpoints=checkpoints,
    )

    # Each group row receives its own load and generator scaling vectors.
    for i in range(model.r):
        gens: list[Generator] = model.injections_per_type[i].get(DeviceType.GeneratorDevice, list())
        loads: list[Load] = model.injections_per_type[i].get(DeviceType.LoadDevice, list())
        load_scale: np.ndarray = temporal_scaling[:, i, 0]
        gen_scale: np.ndarray = temporal_scaling[:, i, 1]

        for load in loads:
            load.ensure_profiles_exist(time_profile)
            scale_load_time_series_profiles(load=load, scaling_vector=load_scale)

        for generator in gens:
            generator.ensure_profiles_exist(time_profile)
            # The existing snapshot scaler only changes generator P, so temporal scaling follows that same behavior.
            scale_float_profile_values(profile=generator.P_prof, scaling_vector=gen_scale)

    return temporal_scaling


class SystemScaler(QtWidgets.QDialog):
    """
    SystemScaler GUI
    """

    def __init__(self, grid: MultiCircuit, parent=None):
        """

        :param parent:
        """
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr("System scaling"))

        self.grid = grid
        self.checkpoints: list[SystemScalingCheckpoint] = list()
        self.checkpoints_model: Union[SystemScalingCheckpointsModel, None] = None
        self.current_checkpoint_data_model: Union[SystemScalingModel, None] = None
        self.connected_checkpoint_data_models: list[SystemScalingModel] = list()
        self.plot_figure: Figure = Figure(figsize=(7.0, 5.0))
        self.plot_canvas: FigureCanvas = FigureCanvas(self.plot_figure)
        self.plot_toolbar: NavigationToolbar = NavigationToolbar(self.plot_canvas, self)

        self.ui.verticalLayout_2.addWidget(self.plot_toolbar)
        self.ui.verticalLayout_2.addWidget(self.plot_canvas)

        plot_axis = self.plot_figure.add_subplot(111)
        plot_axis.text(0.5, 0.5, self.tr("Press plot to preview scaling"), ha="center", va="center")
        plot_axis.set_axis_off()
        self.plot_canvas.draw()

        self.groups = [DeviceType.AreaDevice,
                       DeviceType.ZoneDevice,
                       DeviceType.CountryDevice,
                       DeviceType.RegionDevice,
                       DeviceType.CommunityDevice,
                       DeviceType.MunicipalityDevice,
                       DeviceType.SubstationDevice]

        # The snapshot checkpoint is always available and uses None as its time key.
        snapshot_model: SystemScalingModel = SystemScalingModel(device_tpe=self.groups[0],
                                                                grid=self.grid,
                                                                parent=self.ui.checkpointDataTableView,
                                                                set_delegates=False)
        self.connect_checkpoint_data_model(model=snapshot_model)
        self.checkpoints.append(SystemScalingCheckpoint(time_key=None, model=snapshot_model))
        self.checkpoints_model = SystemScalingCheckpointsModel(checkpoints=self.checkpoints,
                                                               groups=self.groups,
                                                               grid=self.grid,
                                                               parent=self.ui.checkpointsTableView,
                                                               data_parent=self.ui.checkpointDataTableView)
        self.ui.checkpointsTableView.setModel(self.checkpoints_model)
        self.ui.checkpointsTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.ui.checkpointsTableView.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.set_checkpoints_delegates()
        self.set_checkpoint_data_delegates()
        self.set_current_checkpoint_data_model(checkpoint_idx=0)
        self.ui.checkpointsTableView.selectRow(0)
        self.ui.checkpointsTableView.clicked.connect(self.on_checkpoint_table_clicked)
        self.ui.checkpointsTableView.selectionModel().currentChanged.connect(self.on_checkpoint_table_current_changed)
        self.checkpoints_model.dataChanged.connect(self.on_checkpoints_model_data_changed)

        self.ui.doit_button.clicked.connect(self.do_it)
        self.ui.plotButton.clicked.connect(self.plot_scaling)
        self.ui.addButton.clicked.connect(self.add_checkpoint)
        self.ui.removeButton.clicked.connect(self.remove_checkpoint)
        self._plot_disposed: bool = False

    def done(self, result: int) -> None:
        """
        Release Matplotlib resources before the modal dialog closes.

        :param result: Qt dialog result code.
        :return: None.
        """
        if self._plot_disposed:
            pass
        else:
            self._plot_disposed = True
            self.plot_figure.clear()
            plt.close(self.plot_figure)
            self.plot_toolbar.setParent(None)
            self.plot_toolbar.deleteLater()
            self.plot_canvas.setParent(None)
            self.plot_canvas.deleteLater()
        QtWidgets.QDialog.done(self, result)

    def set_checkpoints_delegates(self) -> None:
        """
        Configure the checkpoint table delegates.

        :return: Nothing.
        """
        group_names: list[str] = list()
        time_objects: list[object] = list()
        time_names: list[str] = list()

        for group in self.groups:
            group_names.append(group.value)

        time_objects.append(None)
        time_names.append("None")

        if self.grid.time_profile is not None and len(self.grid.time_profile) > 0:
            for time_value in self.grid.time_profile:
                time_objects.append(time_value)
                time_names.append(str(time_value))
        else:
            pass

        group_delegate: ComboDelegate = ComboDelegate(parent=self.ui.checkpointsTableView,
                                                      objects=self.groups,
                                                      object_names=group_names)
        time_delegate: ComboDelegate = ComboDelegate(parent=self.ui.checkpointsTableView,
                                                     objects=time_objects,
                                                     object_names=time_names)

        self.ui.checkpointsTableView.setItemDelegateForColumn(0, time_delegate)
        self.ui.checkpointsTableView.setItemDelegateForColumn(1, group_delegate)

    def set_checkpoint_data_delegates(self) -> None:
        """
        Configure the selected checkpoint data table delegates.

        :return: Nothing.
        """
        load_factor_delegate: FloatDelegate = FloatDelegate(parent=self.ui.checkpointDataTableView)
        generation_factor_delegate: FloatDelegate = FloatDelegate(parent=self.ui.checkpointDataTableView)

        self.ui.checkpointDataTableView.setItemDelegateForColumn(0, load_factor_delegate)
        self.ui.checkpointDataTableView.setItemDelegateForColumn(1, generation_factor_delegate)

    def connect_checkpoint_data_model(self, model: SystemScalingModel) -> None:
        """
        Connect a checkpoint data model to refresh checkpoint totals after factor edits.

        :param model: Checkpoint data model.
        :return: Nothing.
        """
        connected: bool = False

        for connected_model in self.connected_checkpoint_data_models:
            if connected_model is model:
                connected = True
            else:
                pass

        if connected:
            pass
        else:
            model.dataChanged.connect(self.on_checkpoint_data_model_data_changed)
            self.connected_checkpoint_data_models.append(model)

    def set_current_checkpoint_data_model(self, checkpoint_idx: int) -> None:
        """
        Display the group scaling data model for a checkpoint.

        :param checkpoint_idx: Checkpoint index to display.
        :return: Nothing.
        """
        if 0 <= checkpoint_idx < len(self.checkpoints):
            self.current_checkpoint_data_model = self.checkpoints[checkpoint_idx].model
            self.connect_checkpoint_data_model(model=self.current_checkpoint_data_model)
            self.ui.checkpointDataTableView.setModel(self.current_checkpoint_data_model)
        else:
            self.current_checkpoint_data_model = None
            self.ui.checkpointDataTableView.setModel(None)

    def on_checkpoint_table_clicked(self, index: QtCore.QModelIndex) -> None:
        """
        Display the checkpoint data when the checkpoint row is clicked.

        :param index: Clicked checkpoint table index.
        :return: Nothing.
        """
        if index.isValid():
            self.set_current_checkpoint_data_model(checkpoint_idx=index.row())
        else:
            pass

    def on_checkpoint_table_current_changed(self,
                                            current: QtCore.QModelIndex,
                                            previous: QtCore.QModelIndex) -> None:
        """
        Display the checkpoint data when table selection changes.

        :param current: Current selected model index.
        :param previous: Previous selected model index.
        :return: Nothing.
        """
        del previous

        if current.isValid():
            self.set_current_checkpoint_data_model(checkpoint_idx=current.row())
        else:
            pass

    def on_checkpoints_model_data_changed(self,
                                          top_left: QtCore.QModelIndex,
                                          bottom_right: QtCore.QModelIndex,
                                          roles: list[int]) -> None:
        """
        Refresh the checkpoint data table after checkpoint-level edits.

        :param top_left: First changed checkpoint table index.
        :param bottom_right: Last changed checkpoint table index.
        :param roles: Changed Qt roles.
        :return: Nothing.
        """
        del bottom_right
        del roles

        if top_left.isValid():
            self.set_current_checkpoint_data_model(checkpoint_idx=top_left.row())
        else:
            pass

    def on_checkpoint_data_model_data_changed(self,
                                              top_left: QtCore.QModelIndex,
                                              bottom_right: QtCore.QModelIndex,
                                              roles: list[int]) -> None:
        """
        Refresh checkpoint total columns after editing group scaling factors.

        :param top_left: First changed checkpoint data table index.
        :param bottom_right: Last changed checkpoint data table index.
        :param roles: Changed Qt roles.
        :return: Nothing.
        """
        del top_left
        del bottom_right
        del roles

        current_index: QtCore.QModelIndex = self.ui.checkpointsTableView.currentIndex()

        if current_index.isValid() and self.checkpoints_model is not None:
            row: int = current_index.row()
            self.checkpoints_model.dataChanged.emit(self.checkpoints_model.index(row, 2),
                                                    self.checkpoints_model.index(len(self.checkpoints) - 1, 3),
                                                    [QtCore.Qt.ItemDataRole.DisplayRole])
        else:
            pass

    def get_selected_checkpoint_index(self) -> int:
        """
        Get the selected checkpoint row.

        :return: Selected checkpoint index or zero when there is no valid selection.
        """
        selected_index: QtCore.QModelIndex = self.ui.checkpointsTableView.currentIndex()
        selected_row: int

        if selected_index.isValid():
            selected_row = selected_index.row()
        else:
            selected_row = 0

        return selected_row

    def seed_model_from_previous_checkpoint(self,
                                            model: SystemScalingModel,
                                            previous_checkpoint: SystemScalingCheckpoint) -> None:
        """
        Copy scaling values from a previous checkpoint when both use the same grouping.

        :param model: New model to seed.
        :param previous_checkpoint: Previous checkpoint used as the source.
        :return: Nothing.
        """
        previous_factors: np.ndarray

        if previous_checkpoint.model.device_tpe == model.device_tpe:
            previous_factors = previous_checkpoint.model._data[:, 0:2].copy()

            if previous_factors.shape == (model.r, 2):
                model.set_load_generation_scaling_factors(factors=previous_factors)
            else:
                pass
        else:
            pass

    def add_checkpoint(self) -> None:
        """
        Add a scaling checkpoint after the selected checkpoint.

        :return: Nothing.
        """
        selected_row: int = self.get_selected_checkpoint_index()
        selected_checkpoint_idx: int = selected_row
        insert_checkpoint_idx: int = selected_checkpoint_idx + 1
        selected_group: DeviceType = self.groups[0]
        time_key: Union[int, None] = None
        can_insert: bool = True

        if 0 <= selected_checkpoint_idx < len(self.checkpoints):
            selected_group = self.checkpoints[selected_checkpoint_idx].model.device_tpe
        else:
            pass

        model: SystemScalingModel = SystemScalingModel(device_tpe=selected_group,
                                                       grid=self.grid,
                                                       parent=self.ui.checkpointDataTableView,
                                                       set_delegates=False)
        self.connect_checkpoint_data_model(model=model)

        if 0 <= selected_checkpoint_idx < len(self.checkpoints):
            self.seed_model_from_previous_checkpoint(model=model,
                                                     previous_checkpoint=self.checkpoints[selected_checkpoint_idx])

            if self.grid.time_profile is not None and len(self.grid.time_profile) > 0:
                if self.checkpoints[selected_checkpoint_idx].time_key is None:
                    time_key = 0
                else:
                    time_idx: int = get_checkpoint_time_index(time_profile=self.grid.time_profile,
                                                              time_key=self.checkpoints[
                                                                  selected_checkpoint_idx].time_key)
                    time_key = time_idx + 1

                next_time_idx: Union[int, None] = self.checkpoints_model.get_next_time_index(
                    checkpoint_idx=selected_checkpoint_idx
                )

                if time_key >= len(self.grid.time_profile):
                    can_insert = False
                else:
                    pass

                if next_time_idx is not None and time_key >= next_time_idx:
                    can_insert = False
                else:
                    pass
            else:
                time_key = None
        else:
            if self.grid.time_profile is not None and len(self.grid.time_profile) > 0:
                time_key = 0
            else:
                time_key = None

        if can_insert:
            self.checkpoints.insert(insert_checkpoint_idx, SystemScalingCheckpoint(time_key=time_key, model=model))

            if self.checkpoints_model is not None:
                self.checkpoints_model.update()
            else:
                pass

            insert_row: int = insert_checkpoint_idx
            self.ui.checkpointsTableView.selectRow(insert_row)
            self.set_current_checkpoint_data_model(checkpoint_idx=insert_checkpoint_idx)
        else:
            pass

    def remove_checkpoint(self) -> None:
        """
        Remove the selected checkpoints while keeping at least one default checkpoint.

        :return: Nothing.
        """
        selection_model: QtCore.QItemSelectionModel = self.ui.checkpointsTableView.selectionModel()
        selected_rows_model_indexes: list[QtCore.QModelIndex] = selection_model.selectedRows()
        selected_checkpoint_indices: list[int] = list()
        rows_to_remove: set[int] = set()
        none_count: int = 0

        for checkpoint in self.checkpoints:
            if checkpoint.time_key is None:
                none_count += 1
            else:
                pass

        if len(selected_rows_model_indexes) > 0:
            for row_index in selected_rows_model_indexes:
                selected_checkpoint_indices.append(row_index.row())
        else:
            selected_checkpoint_indices.append(self.get_selected_checkpoint_index())

        for selected_checkpoint_idx in selected_checkpoint_indices:
            if 0 <= selected_checkpoint_idx < len(self.checkpoints):
                if self.checkpoints[selected_checkpoint_idx].time_key is None:
                    if none_count > 1:
                        rows_to_remove.add(selected_checkpoint_idx)
                        none_count -= 1
                    else:
                        pass
                else:
                    rows_to_remove.add(selected_checkpoint_idx)
            else:
                pass

        if len(rows_to_remove) > 0 and len(self.checkpoints) > len(rows_to_remove):
            sorted_rows: list[int] = sorted(rows_to_remove, reverse=True)

            for selected_checkpoint_idx in sorted_rows:
                self.checkpoints.pop(selected_checkpoint_idx)

            if self.checkpoints_model is not None:
                self.checkpoints_model.update()
            else:
                pass

            next_checkpoint_idx: int = min(min(rows_to_remove), len(self.checkpoints) - 1)
            next_row: int = next_checkpoint_idx
            self.ui.checkpointsTableView.selectRow(next_row)
            self.set_current_checkpoint_data_model(checkpoint_idx=next_checkpoint_idx)
        else:
            pass

    def get_temporal_checkpoints_by_group(self) -> dict[DeviceType, list[SystemScalingCheckpoint]]:
        """
        Collect temporal checkpoints by grouping type.

        :return: Dictionary keyed by grouping type.
        """
        temporal_checkpoints_by_group: dict[DeviceType, list[SystemScalingCheckpoint]] = dict()

        for checkpoint in self.checkpoints:
            if checkpoint.time_key is None:
                pass
            else:
                temporal_checkpoints: Union[list[SystemScalingCheckpoint], None]
                temporal_checkpoints = temporal_checkpoints_by_group.get(checkpoint.model.device_tpe, None)

                if temporal_checkpoints is None:
                    temporal_checkpoints = list()
                    temporal_checkpoints_by_group[checkpoint.model.device_tpe] = temporal_checkpoints
                else:
                    pass

                temporal_checkpoints.append(checkpoint)

        return temporal_checkpoints_by_group

    def get_effective_temporal_scaling_by_group(self,
                                                group: DeviceType,
                                                time_profile: pd.DatetimeIndex) -> Union[tuple[SystemScalingModel,
    np.ndarray], None]:
        """
        Build effective cumulative temporal scaling for one grouping type.

        :param group: Grouping type to process.
        :param time_profile: Time profile used for interpolation.
        :return: Reference model and effective temporal scaling, or ``None``.
        """
        temporal_count: int = 0
        first_model: Union[SystemScalingModel, None] = None

        # Count first so the numerical arrays can be allocated with their final size.
        for checkpoint in self.checkpoints:
            if checkpoint.time_key is None:
                pass
            else:
                if checkpoint.model.device_tpe == group:
                    temporal_count += 1

                    if first_model is None:
                        first_model = checkpoint.model
                    else:
                        pass
                else:
                    pass

        if temporal_count > 0 and first_model is not None:
            checkpoint_indices: np.ndarray = np.zeros(temporal_count, dtype=int)
            checkpoint_values: np.ndarray = np.zeros((temporal_count, first_model.r, 2), dtype=float)
            temporal_idx: int = 0

            # Each plotted checkpoint value is the effective cumulative factor shown by the checkpoint table.
            for checkpoint_idx in range(len(self.checkpoints)):
                checkpoint = self.checkpoints[checkpoint_idx]

                if checkpoint.time_key is None:
                    pass
                else:
                    if checkpoint.model.device_tpe == group:
                        checkpoint_indices[temporal_idx] = get_checkpoint_time_index(time_profile=time_profile,
                                                                                     time_key=checkpoint.time_key)
                        checkpoint_values[
                            temporal_idx, :, :] = self.checkpoints_model.get_cumulative_factors_for_checkpoint(
                            checkpoint_idx=checkpoint_idx
                        )
                        temporal_idx += 1
                    else:
                        pass

            unique_indices: np.ndarray
            unique_values: np.ndarray
            unique_indices, unique_values = get_cumulative_checkpoint_values(
                checkpoint_indices=checkpoint_indices,
                checkpoint_values=checkpoint_values,
                values_are_incremental=False,
            )
            x: np.ndarray = np.arange(len(time_profile), dtype=float)
            temporal_scaling: np.ndarray = np.ones((len(time_profile), first_model.r, 2), dtype=float)

            for group_idx in range(first_model.r):
                for scale_idx in range(2):
                    temporal_scaling[:, group_idx, scale_idx] = np.interp(
                        x=x,
                        xp=unique_indices,
                        fp=unique_values[:, group_idx, scale_idx],
                    )

            return first_model, temporal_scaling
        else:
            return None

    def get_scaling_preview_arrays(self) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Aggregate original and scaled load/generation arrays without mutating the grid.

        :return: Time index, original load, scaled load, original generation, scaled generation.
        """
        time_profile: pd.DatetimeIndex = self.grid.time_profile
        nt: int = len(time_profile)
        original_load: np.ndarray = np.zeros(nt, dtype=float)
        scaled_load: np.ndarray = np.zeros(nt, dtype=float)
        original_generation: np.ndarray = np.zeros(nt, dtype=float)
        scaled_generation: np.ndarray = np.zeros(nt, dtype=float)
        load_scales_by_idtag: dict[str, np.ndarray] = dict()
        generation_scales_by_idtag: dict[str, np.ndarray] = dict()

        for load in self.grid.get_loads():
            load_scales_by_idtag[load.idtag] = np.ones(nt, dtype=float)

        for generator in self.grid.get_generators():
            generation_scales_by_idtag[generator.idtag] = np.ones(nt, dtype=float)

        # Snapshot checkpoints are constant multipliers. Temporal checkpoints overwrite them where configured.
        for checkpoint in self.checkpoints:
            if checkpoint.time_key is None:
                for group_idx in range(checkpoint.model.r):
                    loads: list[Load] = checkpoint.model.injections_per_type[group_idx].get(DeviceType.LoadDevice,
                                                                                            list())
                    generators: list[Generator]
                    generators = checkpoint.model.injections_per_type[group_idx].get(DeviceType.GeneratorDevice,
                                                                                     list())
                    load_scale: float = float(checkpoint.model._data[group_idx, 0])
                    generation_scale: float = float(checkpoint.model._data[group_idx, 1])

                    for load in loads:
                        load_scales_by_idtag[load.idtag] *= load_scale

                    for generator in generators:
                        generation_scales_by_idtag[generator.idtag] *= generation_scale
            else:
                pass

        for group in self.groups:
            effective_temporal_scaling: Union[tuple[SystemScalingModel, np.ndarray], None]
            effective_temporal_scaling = self.get_effective_temporal_scaling_by_group(group=group,
                                                                                      time_profile=time_profile)

            if effective_temporal_scaling is not None:
                reference_model: SystemScalingModel
                temporal_scaling: np.ndarray
                reference_model, temporal_scaling = effective_temporal_scaling

                for group_idx in range(reference_model.r):
                    loads = reference_model.injections_per_type[group_idx].get(DeviceType.LoadDevice, list())
                    generators = reference_model.injections_per_type[group_idx].get(DeviceType.GeneratorDevice, list())

                    for load in loads:
                        load_scales_by_idtag[load.idtag] = temporal_scaling[:, group_idx, 0]

                    for generator in generators:
                        generation_scales_by_idtag[generator.idtag] = temporal_scaling[:, group_idx, 1]
            else:
                pass

        for load in self.grid.get_loads():
            load_values: np.ndarray = get_load_time_series_values(load=load, time_profile=time_profile)
            original_load += load_values
            scaled_load += load_values * load_scales_by_idtag[load.idtag]

        for generator in self.grid.get_generators():
            generation_values: np.ndarray = get_generator_time_series_values(generator=generator,
                                                                             time_profile=time_profile)
            original_generation += generation_values
            scaled_generation += generation_values * generation_scales_by_idtag[generator.idtag]

        return time_profile, original_load, scaled_load, original_generation, scaled_generation

    def plot_scaling(self) -> None:
        """
        Plot original and scaled aggregate load/generation without applying changes.

        :return: Nothing.
        """
        if self.grid.time_profile is not None and len(self.grid.time_profile) > 0:
            time_profile: pd.DatetimeIndex
            original_load: np.ndarray
            scaled_load: np.ndarray
            original_generation: np.ndarray
            scaled_generation: np.ndarray
            time_profile, original_load, scaled_load, original_generation, scaled_generation = (
                self.get_scaling_preview_arrays()
            )

            time_delta_hours: np.ndarray = self.grid.get_time_deltas_in_hours()
            original_generation_energy: np.ndarray = original_generation * time_delta_hours
            scaled_generation_energy: np.ndarray = scaled_generation * time_delta_hours
            original_load_energy: np.ndarray = -original_load * time_delta_hours
            scaled_load_energy: np.ndarray = -scaled_load * time_delta_hours

            self.plot_figure.clear()
            power_axis = self.plot_figure.add_subplot(211)
            energy_axis = self.plot_figure.add_subplot(212, sharex=power_axis)

            power_axis.plot(time_profile,
                            original_generation,
                            label=self.tr("Original generation"),
                            linewidth=2.0)
            power_axis.plot(time_profile,
                            scaled_generation,
                            label=self.tr("Scaled generation"),
                            linewidth=2.0)
            power_axis.plot(time_profile, -original_load, label=self.tr("Original load"), linewidth=2.0)
            power_axis.plot(time_profile, -scaled_load, label=self.tr("Scaled load"), linewidth=2.0)
            power_axis.axhline(0.0, color="black", linewidth=0.8)
            power_axis.set_ylabel(self.tr("MW"))
            power_axis.set_title(self.tr("Aggregated power scaling preview"))
            power_axis.grid(True)
            power_axis.legend()

            energy_axis.fill_between(time_profile, 0.0, scaled_generation_energy,
                                     alpha=0.35, label=self.tr("Scaled generation energy"))
            energy_axis.fill_between(time_profile, 0.0, scaled_load_energy,
                                     alpha=0.35, label=self.tr("Scaled load energy"))
            energy_axis.plot(time_profile, original_generation_energy,
                             linestyle="--", linewidth=1.6, label=self.tr("Original generation energy"))
            energy_axis.plot(time_profile, original_load_energy,
                             linestyle="--", linewidth=1.6, label=self.tr("Original load energy"))
            energy_axis.axhline(0.0, color="black", linewidth=0.8)
            energy_axis.set_ylabel(self.tr("MWh"))
            energy_axis.set_title(self.tr("Aggregated energy scaling preview"))
            energy_axis.grid(True)
            energy_axis.legend()

            self.plot_figure.autofmt_xdate()
            self.plot_figure.tight_layout()
            self.plot_canvas.draw()
        else:
            QtWidgets.QMessageBox.warning(self,
                                          self.tr("System scaling"),
                                          self.tr("There is no time series to plot."))

    def do_it(self):
        """

        :return:
        """
        ok = yes_no_question(self.tr("This operation will alter the generation "
                                     "and load composition irreversibly\nAre you sure?"),
                             self.tr("System scaling"))

        if ok:
            if len(self.checkpoints) > 0:
                temporal_checkpoints_by_group: dict[DeviceType, list[SystemScalingCheckpoint]]
                temporal_checkpoints_by_group = self.get_temporal_checkpoints_by_group()

                for checkpoint in self.checkpoints:
                    if checkpoint.time_key is None:
                        checkpoint.model.apply_scaling(with_time_series=False)
                    else:
                        pass

                for group in self.groups:
                    temporal_checkpoints = temporal_checkpoints_by_group.get(group, None)

                    if temporal_checkpoints is not None:
                        apply_time_series_scaling_from_checkpoints(model=temporal_checkpoints[0].model,
                                                                   checkpoints=temporal_checkpoints)
                    else:
                        pass
            else:
                pass

            self.close()


def build_demo_system_scaler_grid() -> MultiCircuit:
    """
    Build a small five-bus grid for manually testing the system scaler.

    :return: Demo grid with aggregation groups, injections and twelve time steps.
    """
    grid: MultiCircuit = MultiCircuit()

    # Define several aggregation levels so every SystemScaler grouping mode has visible rows.
    area_north: dev.Area = dev.Area(name="North area")
    area_south: dev.Area = dev.Area(name="South area")
    zone_urban: dev.Zone = dev.Zone(name="North urban", area=area_north)
    zone_rural: dev.Zone = dev.Zone(name="North rural", area=area_north)
    zone_south: dev.Zone = dev.Zone(name="South zone", area=area_south)
    country_es: dev.Country = dev.Country(name="Spain")
    country_pt: dev.Country = dev.Country(name="Portugal")
    community_canary: dev.Community = dev.Community(name="Canary islands", country=country_es)
    community_mainland: dev.Community = dev.Community(name="Mainland", country=country_es)
    community_algarve: dev.Community = dev.Community(name="Algarve", country=country_pt)
    region_gran_canaria: dev.Region = dev.Region(name="Gran Canaria", community=community_canary)
    region_tenerife: dev.Region = dev.Region(name="Tenerife", community=community_canary)
    region_madrid: dev.Region = dev.Region(name="Madrid", community=community_mainland)
    region_faro: dev.Region = dev.Region(name="Faro", community=community_algarve)
    municipality_las_palmas: dev.Municipality = dev.Municipality(name="Las Palmas", region=region_gran_canaria)
    municipality_santa_cruz: dev.Municipality = dev.Municipality(name="Santa Cruz", region=region_tenerife)
    municipality_madrid: dev.Municipality = dev.Municipality(name="Madrid city", region=region_madrid)
    municipality_faro: dev.Municipality = dev.Municipality(name="Faro city", region=region_faro)

    grid.add_area(obj=area_north)
    grid.add_area(obj=area_south)
    grid.add_zone(obj=zone_urban)
    grid.add_zone(obj=zone_rural)
    grid.add_zone(obj=zone_south)
    grid.add_country(obj=country_es)
    grid.add_country(obj=country_pt)
    grid.add_community(obj=community_canary)
    grid.add_community(obj=community_mainland)
    grid.add_community(obj=community_algarve)
    grid.add_region(obj=region_gran_canaria)
    grid.add_region(obj=region_tenerife)
    grid.add_region(obj=region_madrid)
    grid.add_region(obj=region_faro)
    grid.add_municipality(obj=municipality_las_palmas)
    grid.add_municipality(obj=municipality_santa_cruz)
    grid.add_municipality(obj=municipality_madrid)
    grid.add_municipality(obj=municipality_faro)

    substation_gc: dev.Substation = dev.Substation(name="GC substation",
                                                   area=area_north,
                                                   zone=zone_urban,
                                                   country=country_es,
                                                   community=community_canary,
                                                   region=region_gran_canaria,
                                                   municipality=municipality_las_palmas)
    substation_tfe: dev.Substation = dev.Substation(name="TFE substation",
                                                    area=area_north,
                                                    zone=zone_rural,
                                                    country=country_es,
                                                    community=community_canary,
                                                    region=region_tenerife,
                                                    municipality=municipality_santa_cruz)
    substation_mad: dev.Substation = dev.Substation(name="MAD substation",
                                                    area=area_south,
                                                    zone=zone_south,
                                                    country=country_es,
                                                    community=community_mainland,
                                                    region=region_madrid,
                                                    municipality=municipality_madrid)
    substation_faro: dev.Substation = dev.Substation(name="Faro substation",
                                                     area=area_south,
                                                     zone=zone_south,
                                                     country=country_pt,
                                                     community=community_algarve,
                                                     region=region_faro,
                                                     municipality=municipality_faro)

    grid.add_substation(obj=substation_gc)
    grid.add_substation(obj=substation_tfe)
    grid.add_substation(obj=substation_mad)
    grid.add_substation(obj=substation_faro)

    bus_1: dev.Bus = dev.Bus(name="Bus 1 GC load", area=area_north, zone=zone_urban, substation=substation_gc)
    bus_2: dev.Bus = dev.Bus(name="Bus 2 GC gen", area=area_north, zone=zone_urban, substation=substation_gc)
    bus_3: dev.Bus = dev.Bus(name="Bus 3 TFE mixed", area=area_north, zone=zone_rural, substation=substation_tfe)
    bus_4: dev.Bus = dev.Bus(name="Bus 4 MAD load", area=area_south, zone=zone_south, substation=substation_mad)
    bus_5: dev.Bus = dev.Bus(name="Bus 5 Faro gen", area=area_south, zone=zone_south, substation=substation_faro)

    grid.add_bus(obj=bus_1)
    grid.add_bus(obj=bus_2)
    grid.add_bus(obj=bus_3)
    grid.add_bus(obj=bus_4)
    grid.add_bus(obj=bus_5)

    time_profile: pd.DatetimeIndex = pd.date_range("2026-01-01 00:00:00", periods=12, freq="h")
    grid.format_profiles(index=time_profile)

    load_1: dev.Load = dev.Load(name="L1 residential", P=18.0, Q=4.0)
    load_3: dev.Load = dev.Load(name="L3 rural", P=11.0, Q=2.5)
    load_4: dev.Load = dev.Load(name="L4 industrial", P=28.0, Q=7.0)
    generator_2: dev.Generator = dev.Generator(name="G2 solar", P=22.0)
    generator_3: dev.Generator = dev.Generator(name="G3 diesel", P=15.0)
    generator_5: dev.Generator = dev.Generator(name="G5 wind", P=35.0)

    grid.add_load(bus=bus_1, api_obj=load_1)
    grid.add_load(bus=bus_3, api_obj=load_3)
    grid.add_load(bus=bus_4, api_obj=load_4)
    grid.add_generator(bus=bus_2, api_obj=generator_2)
    grid.add_generator(bus=bus_3, api_obj=generator_3)
    grid.add_generator(bus=bus_5, api_obj=generator_5)

    load_shape: np.ndarray = np.array([0.72, 0.68, 0.66, 0.70, 0.84, 0.98,
                                       1.06, 1.12, 1.18, 1.10, 0.94, 0.82], dtype=float)
    solar_shape: np.ndarray = np.array([0.00, 0.00, 0.00, 0.08, 0.32, 0.64,
                                        0.92, 1.00, 0.82, 0.46, 0.12, 0.00], dtype=float)
    dispatch_shape: np.ndarray = np.array([0.78, 0.76, 0.74, 0.76, 0.82, 0.90,
                                           0.96, 1.00, 1.02, 0.98, 0.90, 0.84], dtype=float)
    wind_shape: np.ndarray = np.array([0.52, 0.58, 0.61, 0.66, 0.70, 0.73,
                                       0.68, 0.60, 0.55, 0.50, 0.48, 0.54], dtype=float)

    load_1.P_prof.set(load_1.P * load_shape)
    load_1.Q_prof.set(load_1.Q * load_shape)
    load_3.P_prof.set(load_3.P * load_shape * 0.86)
    load_3.Q_prof.set(load_3.Q * load_shape * 0.86)
    load_4.P_prof.set(load_4.P * load_shape * 1.08)
    load_4.Q_prof.set(load_4.Q * load_shape * 1.08)
    generator_2.P_prof.set(generator_2.P * solar_shape)
    generator_3.P_prof.set(generator_3.P * dispatch_shape)
    generator_5.P_prof.set(generator_5.P * wind_shape)

    return grid


def configure_demo_system_scaler_checkpoints(window: SystemScaler) -> None:
    """
    Add several sample checkpoints to a SystemScaler window.

    :param window: SystemScaler instance to populate.
    :return: Nothing.
    """
    snapshot_area_factors: np.ndarray = np.array([[1.05, 0.98],
                                                  [0.96, 1.04]], dtype=float)
    area_t0_factors: np.ndarray = np.array([[1.00, 1.00],
                                            [1.00, 1.00]], dtype=float)
    area_t5_factors: np.ndarray = np.array([[1.18, 0.90],
                                            [0.92, 1.16]], dtype=float)
    area_t11_factors: np.ndarray = np.array([[0.88, 1.10],
                                             [1.12, 0.94]], dtype=float)
    zone_t3_factors: np.ndarray = np.array([[1.10, 0.95],
                                            [0.86, 1.06],
                                            [1.04, 1.02]], dtype=float)
    zone_t9_factors: np.ndarray = np.array([[0.94, 1.04],
                                            [1.18, 0.92],
                                            [0.90, 1.12]], dtype=float)

    window.checkpoints[0].model.set_load_generation_scaling_factors(factors=snapshot_area_factors)
    window.checkpoints.append(SystemScalingCheckpoint(
        time_key=0,
        model=SystemScalingModel(device_tpe=DeviceType.AreaDevice,
                                 grid=window.grid,
                                 parent=window.ui.checkpointDataTableView,
                                 set_delegates=False),
    ))
    window.checkpoints.append(SystemScalingCheckpoint(
        time_key=3,
        model=SystemScalingModel(device_tpe=DeviceType.ZoneDevice,
                                 grid=window.grid,
                                 parent=window.ui.checkpointDataTableView,
                                 set_delegates=False),
    ))
    window.checkpoints.append(SystemScalingCheckpoint(
        time_key=5,
        model=SystemScalingModel(device_tpe=DeviceType.AreaDevice,
                                 grid=window.grid,
                                 parent=window.ui.checkpointDataTableView,
                                 set_delegates=False),
    ))
    window.checkpoints.append(SystemScalingCheckpoint(
        time_key=9,
        model=SystemScalingModel(device_tpe=DeviceType.ZoneDevice,
                                 grid=window.grid,
                                 parent=window.ui.checkpointDataTableView,
                                 set_delegates=False),
    ))
    window.checkpoints.append(SystemScalingCheckpoint(
        time_key=11,
        model=SystemScalingModel(device_tpe=DeviceType.AreaDevice,
                                 grid=window.grid,
                                 parent=window.ui.checkpointDataTableView,
                                 set_delegates=False),
    ))

    window.checkpoints[1].model.set_load_generation_scaling_factors(factors=area_t0_factors)
    window.checkpoints[2].model.set_load_generation_scaling_factors(factors=zone_t3_factors)
    window.checkpoints[3].model.set_load_generation_scaling_factors(factors=area_t5_factors)
    window.checkpoints[4].model.set_load_generation_scaling_factors(factors=zone_t9_factors)
    window.checkpoints[5].model.set_load_generation_scaling_factors(factors=area_t11_factors)

    for checkpoint in window.checkpoints:
        window.connect_checkpoint_data_model(model=checkpoint.model)

    if window.checkpoints_model is not None:
        window.checkpoints_model.update()
    else:
        pass

    window.ui.checkpointsTableView.selectRow(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemScaler(grid=build_demo_system_scaler_grid())
    configure_demo_system_scaler_checkpoints(window=window)
    # window.resize(1.61 * 700.0, 600.0)  # golden ratio
    window.show()
    sys.exit(app.exec())
