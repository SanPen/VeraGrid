# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import sys
from calendar import isleap
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import requests
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QApplication

from VeraGrid.Gui.DeviceEditors.LoadDesigner.load_designer_ui import Ui_Dialog


class LoadArchetype(Enum):
    """
    Load profile archetypes available in the load designer.
    """
    RESIDENTIAL_EVENING = "Residential evening"
    RESIDENTIAL_SUMMER = "Residential summer"
    COMMERCIAL_OFFICE = "Commercial office"
    RETAIL = "Retail"
    INDUSTRIAL_FLAT = "Industrial flat"
    INDUSTRIAL_TWO_SHIFT = "Industrial two-shift"
    INDUSTRIAL_THREE_SHIFT = "Industrial three-shift"
    EV_HOME = "EV home charging"
    EV_FAST = "EV fast charging"
    HEAT_PUMP = "Heat pump winter"
    STREET_LIGHTING = "Street lighting"
    DATA_CENTER = "Data center"


class ScalingMode(Enum):
    """
    Scaling modes used by load profile components.
    """
    PEAK_MW = "Peak MW"
    AVERAGE_MW = "Average MW"


def get_default_component_table(base_power: float) -> pd.DataFrame:
    """
    Build the default load component table.

    :param base_power: Initial load active power in MW.
    :return: Component table.
    """
    component_power: float = base_power if base_power > 0.0 else 10.0
    data: dict[str, list[object]] = dict(enabled=[True, True, False, False, False, False,
                                                  False, False, False, False, False, False],
                                         archetype=[LoadArchetype.RESIDENTIAL_EVENING.value,
                                                    LoadArchetype.RESIDENTIAL_SUMMER.value,
                                                    LoadArchetype.COMMERCIAL_OFFICE.value,
                                                    LoadArchetype.RETAIL.value,
                                                    LoadArchetype.INDUSTRIAL_FLAT.value,
                                                    LoadArchetype.INDUSTRIAL_TWO_SHIFT.value,
                                                    LoadArchetype.INDUSTRIAL_THREE_SHIFT.value,
                                                    LoadArchetype.EV_HOME.value,
                                                    LoadArchetype.EV_FAST.value,
                                                    LoadArchetype.HEAT_PUMP.value,
                                                    LoadArchetype.STREET_LIGHTING.value,
                                                    LoadArchetype.DATA_CENTER.value],
                                         scale=[0.45 * component_power,
                                                0.20 * component_power,
                                                0.35 * component_power,
                                                0.15 * component_power,
                                                0.20 * component_power,
                                                0.20 * component_power,
                                                0.20 * component_power,
                                                0.05 * component_power,
                                                0.08 * component_power,
                                                0.10 * component_power,
                                                0.04 * component_power,
                                                0.25 * component_power],
                                         scaling_mode=[ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value,
                                                      ScalingMode.PEAK_MW.value],
                                         power_factor=[0.95, 0.95, 0.98, 0.97, 0.96, 0.96,
                                                       0.96, 0.97, 0.98, 0.95, 0.99, 0.99],
                                         annual_growth=[1.0, 1.2, 0.5, 0.6, 0.5, 0.5,
                                                        0.5, 8.0, 10.0, 2.0, 0.2, 1.0])
    return pd.DataFrame(data=data)


class LoadComponentModel(QtCore.QAbstractTableModel):
    """
    Editable model for load profile composition components.
    """

    def __init__(self, data: pd.DataFrame, parent: QtCore.QObject = None) -> None:
        """
        :param data: Component data table.
        :param parent: Parent object.
        """
        QtCore.QAbstractTableModel.__init__(self, parent)
        self.data_frame: pd.DataFrame = data.copy()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        :param parent: Parent index.
        :return: Number of rows.
        """
        return int(self.data_frame.shape[0])

    def columnCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        """
        :param parent: Parent index.
        :return: Number of columns.
        """
        return int(self.data_frame.shape[1])

    def data(self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Union[str, None]:
        """
        :param index: Cell index.
        :param role: Qt role.
        :return: Display text or None.
        """
        if index.isValid():
            if role == QtCore.Qt.ItemDataRole.DisplayRole or role == QtCore.Qt.ItemDataRole.EditRole:
                value: object = self.data_frame.iat[index.row(), index.column()]
                return str(value)
            else:
                return None
        else:
            return None

    def setData(self,
                index: QtCore.QModelIndex,
                value: object,
                role: int = QtCore.Qt.ItemDataRole.EditRole) -> bool:
        """
        :param index: Cell index.
        :param value: New value.
        :param role: Qt role.
        :return: True if accepted.
        """
        if index.isValid() and role == QtCore.Qt.ItemDataRole.EditRole:
            column_name: str = str(self.data_frame.columns[index.column()])

            if column_name == "enabled":
                normalized_value: str = str(value).strip().lower()
                new_value: object = normalized_value in ["1", "true", "yes", "y"]
            else:
                if column_name in ["scale", "power_factor", "annual_growth"]:
                    new_value = float(value)
                else:
                    new_value = str(value)

            self.data_frame.at[self.data_frame.index[index.row()], column_name] = new_value
            self.dataChanged.emit(index, index, [role])
            return True
        else:
            return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        :param index: Cell index.
        :return: Qt item flags.
        """
        if index.isValid():
            return (QtCore.Qt.ItemFlag.ItemIsEditable |
                    QtCore.Qt.ItemFlag.ItemIsEnabled |
                    QtCore.Qt.ItemFlag.ItemIsSelectable)
        else:
            return QtCore.Qt.ItemFlag.NoItemFlags

    def headerData(self,
                   section: int,
                   orientation: QtCore.Qt.Orientation,
                   role: int = QtCore.Qt.ItemDataRole.DisplayRole) -> Union[str, None]:
        """
        :param section: Header section.
        :param orientation: Header orientation.
        :param role: Qt role.
        :return: Header text or None.
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self.data_frame.columns[section])
            else:
                return str(self.data_frame.index[section])
        else:
            return None


def parse_load_time_array(time_array: Sequence[Union[str, datetime, pd.Timestamp]]) -> Tuple[bool, pd.DatetimeIndex, str]:
    """
    Convert the MultiCircuit time profile to a validated datetime index.

    :param time_array: MultiCircuit time profile.
    :return: Validity flag, datetime index and message.
    """
    time_index: pd.DatetimeIndex = pd.DatetimeIndex(pd.to_datetime(time_array, errors="coerce"))
    message: str = ""

    if len(time_index) > 0:
        invalid_mask: np.ndarray = pd.isna(time_index)

        if bool(np.any(invalid_mask)):
            message = "The time profile contains values that cannot be converted to dates"
            return False, pd.DatetimeIndex(list()), message
        else:
            return True, time_index, message
    else:
        message = "The time profile is empty"
        return False, pd.DatetimeIndex(list()), message


def circular_hour_distance(hour_values: np.ndarray, center: float) -> np.ndarray:
    """
    Compute circular distance between hours and a center hour.

    :param hour_values: Hour values in [0, 24).
    :param center: Center hour.
    :return: Circular distance in hours.
    """
    raw_distance: np.ndarray = np.abs(hour_values - center)
    return np.minimum(raw_distance, 24.0 - raw_distance)


def circular_month_distance(month_values: np.ndarray, center: float) -> np.ndarray:
    """
    Compute circular distance between months and a center month.

    :param month_values: Month values in [1, 12].
    :param center: Center month.
    :return: Circular distance in months.
    """
    raw_distance: np.ndarray = np.abs(month_values - center)
    return np.minimum(raw_distance, 12.0 - raw_distance)


def gaussian_daily_component(hour_values: np.ndarray, center: float, width: float) -> np.ndarray:
    """
    Build a circular Gaussian daily component.

    :param hour_values: Hour values in [0, 24).
    :param center: Center hour.
    :param width: Width parameter in hours.
    :return: Component array.
    """
    distance: np.ndarray = circular_hour_distance(hour_values=hour_values, center=center)
    return np.exp(-0.5 * np.power(distance / width, 2.0))


def gaussian_monthly_component(month_values: np.ndarray, center: float, width: float) -> np.ndarray:
    """
    Build a circular Gaussian seasonal component.

    :param month_values: Month values in [1, 12].
    :param center: Center month.
    :param width: Width parameter in months.
    :return: Component array.
    """
    distance: np.ndarray = circular_month_distance(month_values=month_values, center=center)
    return np.exp(-0.5 * np.power(distance / width, 2.0))


def normalize_shape(shape: np.ndarray) -> np.ndarray:
    """
    Normalize a profile shape to peak value 1.

    :param shape: Raw shape.
    :return: Normalized shape.
    """
    max_value: float = float(np.max(shape))

    if max_value > 0.0:
        return shape / max_value
    else:
        return np.zeros(len(shape), dtype=float)


def build_archetype_shape(time_index: pd.DatetimeIndex, archetype: LoadArchetype) -> np.ndarray:
    """
    Build a normalized load shape for an archetype on the MultiCircuit time profile.

    :param time_index: MultiCircuit time profile.
    :param archetype: Load archetype.
    :return: Normalized shape.
    """
    hour_values: np.ndarray = (time_index.hour.to_numpy(dtype=float) +
                               time_index.minute.to_numpy(dtype=float) / 60.0)
    month_values: np.ndarray = time_index.month.to_numpy(dtype=float)
    day_of_week: np.ndarray = time_index.dayofweek.to_numpy(dtype=int)
    weekday_factor: np.ndarray = np.where(day_of_week < 5, 1.0, 0.82)
    weekend_factor: np.ndarray = np.where(day_of_week < 5, 0.85, 1.0)
    summer_factor: np.ndarray = 0.75 + 0.35 * gaussian_monthly_component(month_values=month_values,
                                                                         center=7.0,
                                                                         width=2.0)
    winter_factor: np.ndarray = 0.75 + 0.35 * gaussian_monthly_component(month_values=month_values,
                                                                         center=1.0,
                                                                         width=2.0)

    if archetype == LoadArchetype.RESIDENTIAL_EVENING:
        shape: np.ndarray = (0.25 +
                             0.35 * gaussian_daily_component(hour_values=hour_values, center=7.5, width=2.0) +
                             0.75 * gaussian_daily_component(hour_values=hour_values, center=20.0, width=3.0))
        return normalize_shape(shape * weekend_factor)
    elif archetype == LoadArchetype.RESIDENTIAL_SUMMER:
        shape = (0.20 +
                 0.20 * gaussian_daily_component(hour_values=hour_values, center=8.0, width=2.5) +
                 0.95 * gaussian_daily_component(hour_values=hour_values, center=18.0, width=4.0))
        return normalize_shape(shape * summer_factor * weekend_factor)
    elif archetype == LoadArchetype.COMMERCIAL_OFFICE:
        shape = 0.20 + 0.85 * gaussian_daily_component(hour_values=hour_values, center=13.0, width=4.2)
        return normalize_shape(shape * weekday_factor)
    elif archetype == LoadArchetype.RETAIL:
        shape = 0.25 + 0.75 * gaussian_daily_component(hour_values=hour_values, center=16.0, width=5.0)
        return normalize_shape(shape * np.where(day_of_week < 5, 0.95, 1.08))
    elif archetype == LoadArchetype.INDUSTRIAL_FLAT:
        shape = np.ones(len(time_index), dtype=float)
        return normalize_shape(shape)
    elif archetype == LoadArchetype.INDUSTRIAL_TWO_SHIFT:
        shape = np.where((hour_values >= 6.0) & (hour_values < 22.0), 1.0, 0.25)
        return normalize_shape(shape * weekday_factor)
    elif archetype == LoadArchetype.INDUSTRIAL_THREE_SHIFT:
        shape = np.where(day_of_week < 5, 1.0, 0.75)
        return normalize_shape(shape)
    elif archetype == LoadArchetype.EV_HOME:
        shape = 0.05 + 0.95 * gaussian_daily_component(hour_values=hour_values, center=22.0, width=2.4)
        return normalize_shape(shape * weekend_factor)
    elif archetype == LoadArchetype.EV_FAST:
        shape = 0.30 + 0.45 * gaussian_daily_component(hour_values=hour_values, center=12.0, width=3.0)
        return normalize_shape(shape * np.where(day_of_week < 5, 1.0, 1.15))
    elif archetype == LoadArchetype.HEAT_PUMP:
        shape = (0.30 +
                 0.40 * gaussian_daily_component(hour_values=hour_values, center=7.0, width=2.0) +
                 0.55 * gaussian_daily_component(hour_values=hour_values, center=19.5, width=3.0))
        return normalize_shape(shape * winter_factor)
    elif archetype == LoadArchetype.STREET_LIGHTING:
        shape = np.where((hour_values >= 19.0) | (hour_values < 7.0), 1.0, 0.0)
        return normalize_shape(shape * winter_factor)
    elif archetype == LoadArchetype.DATA_CENTER:
        shape = np.ones(len(time_index), dtype=float)
        return normalize_shape(shape)
    else:
        shape = np.ones(len(time_index), dtype=float)
        return normalize_shape(shape)


def get_growth_multiplier(time_index: pd.DatetimeIndex, annual_growth_percent: float) -> np.ndarray:
    """
    Build an annual compounded growth multiplier on the MultiCircuit time profile.

    :param time_index: MultiCircuit time profile.
    :param annual_growth_percent: Annual growth in percent.
    :return: Growth multiplier.
    """
    base_year: int = int(time_index[0].year)
    elapsed_years: np.ndarray = time_index.year.to_numpy(dtype=float) - float(base_year)
    return np.power(1.0 + annual_growth_percent / 100.0, elapsed_years)


def scale_shape(shape: np.ndarray, scale: float, scaling_mode: ScalingMode) -> np.ndarray:
    """
    Scale a normalized shape.

    :param shape: Normalized shape.
    :param scale: Scale value.
    :param scaling_mode: Scaling mode.
    :return: Scaled active power profile in MW.
    """
    if scaling_mode == ScalingMode.PEAK_MW:
        return shape * scale
    elif scaling_mode == ScalingMode.AVERAGE_MW:
        mean_value: float = float(np.mean(shape))

        if mean_value > 0.0:
            return shape * scale / mean_value
        else:
            return np.zeros(len(shape), dtype=float)
    else:
        return shape * scale


def get_reactive_power(active_power: np.ndarray, power_factor: float) -> np.ndarray:
    """
    Compute reactive power from active power and power factor.

    :param active_power: Active power in MW.
    :param power_factor: Power factor.
    :return: Reactive power in MVAr.
    """
    clipped_power_factor: float = float(np.clip(power_factor, 0.01, 1.0))
    angle: float = float(np.arccos(clipped_power_factor))
    return active_power * np.tan(angle)


def get_load_weather_reference_base_year(ts1: pd.Timestamp, ts2: pd.Timestamp) -> Tuple[bool, int, str]:
    """
    Select a historical reference year range that Open-Meteo can serve.

    :param ts1: First requested timestamp.
    :param ts2: Last requested timestamp.
    :return: Validity flag, reference base year and validation message.
    """
    max_year_span: int = 10
    reference_year: int = 2024
    year_span: int = int(ts2.year - ts1.year)
    message: str = ""

    if year_span <= max_year_span:
        if 2017 <= int(ts1.year) and int(ts2.year) <= reference_year:
            base_year: int = int(ts1.year)
        else:
            base_year = reference_year - year_span

        if base_year >= 2017:
            return True, base_year, message
        else:
            message = "The mapped Open-Meteo weather year must be 2017 or newer"
            return False, base_year, message
    else:
        message = "The Open-Meteo weather span is limited to 10 years"
        return False, reference_year, message


def build_mapped_load_weather_time_index(time_index: pd.DatetimeIndex, base_year: int) -> pd.DatetimeIndex:
    """
    Map circuit timestamps to historical weather years while preserving month, day and time.

    :param time_index: Circuit time index.
    :param base_year: Historical base year used for the mapped timestamps.
    :return: Historical weather time index.
    """
    ts1: pd.Timestamp = time_index[0]
    mapped_timestamps: List[datetime] = list()

    for ts in time_index:
        target_year: int = base_year + int(ts.year - ts1.year)
        target_month: int = int(ts.month)
        target_day: int = int(ts.day)

        if target_month == 2 and target_day == 29 and not isleap(target_year):
            target_day = 28
        else:
            pass

        mapped_timestamp: datetime = datetime(year=target_year,
                                              month=target_month,
                                              day=target_day,
                                              hour=int(ts.hour),
                                              minute=int(ts.minute),
                                              second=int(ts.second),
                                              microsecond=int(ts.microsecond))
        mapped_timestamps.append(mapped_timestamp)

    return pd.DatetimeIndex(pd.to_datetime(mapped_timestamps))


def get_open_meteo_load_weather_df(time_index: pd.DatetimeIndex,
                                   latitude: float,
                                   longitude: float) -> Tuple[bool, pd.DataFrame]:
    """
    Download hourly temperature and wind data from the free Open-Meteo historical weather API.

    :param time_index: Mapped historical weather time index.
    :param latitude: Site latitude in degrees.
    :param longitude: Site longitude in degrees.
    :return: Success flag and weather data frame indexed by timestamp.
    """
    url: str = "https://archive-api.open-meteo.com/v1/archive"
    params: dict = dict(latitude=latitude,
                        longitude=longitude,
                        start_date=time_index[0].strftime("%Y-%m-%d"),
                        end_date=time_index[-1].strftime("%Y-%m-%d"),
                        hourly="temperature_2m,wind_speed_10m",
                        wind_speed_unit="ms",
                        timezone="GMT")

    try:
        response: requests.Response = requests.get(url=url, params=params, timeout=30.0)
        response.raise_for_status()
        payload: dict = response.json()
        hourly: Union[dict, None] = payload.get("hourly", None)

        if isinstance(hourly, dict):
            weather_index: pd.DatetimeIndex = pd.DatetimeIndex(pd.to_datetime(hourly["time"], errors="coerce"))
            weather_df: pd.DataFrame = pd.DataFrame(index=weather_index)
            weather_df["temperature"] = np.asarray(hourly["temperature_2m"], dtype=float)
            weather_df["wind_speed"] = np.asarray(hourly["wind_speed_10m"], dtype=float)
            return True, weather_df
        else:
            return False, pd.DataFrame()

    except (requests.RequestException, KeyError, ValueError, TypeError):
        return False, pd.DataFrame()


def interpolate_load_weather_to_requested_time(weather_df: pd.DataFrame,
                                               mapped_time_index: pd.DatetimeIndex) -> Tuple[bool, pd.DataFrame]:
    """
    Interpolate downloaded weather to the exact MultiCircuit time samples.

    :param weather_df: Weather data frame indexed by downloaded timestamps.
    :param mapped_time_index: Requested mapped weather timestamps.
    :return: Success flag and interpolated weather frame.
    """
    source_df: pd.DataFrame = weather_df.copy()
    source_df.index = source_df.index.asi8
    source_df.sort_index(inplace=True)
    requested_index: np.ndarray = mapped_time_index.asi8
    interpolation_index: np.ndarray = np.union1d(source_df.index.values, requested_index)
    interpolated_df: pd.DataFrame = source_df.reindex(interpolation_index).interpolate(method="index")
    result_df: pd.DataFrame = interpolated_df.ffill().bfill().reindex(requested_index)

    if bool(result_df["temperature"].isna().any()) or bool(result_df["wind_speed"].isna().any()):
        return False, pd.DataFrame()
    else:
        return True, result_df


def compose_load_profiles(time_index: pd.DatetimeIndex, component_table: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compose active and reactive load profiles from enabled components.

    :param time_index: MultiCircuit time profile.
    :param component_table: Component definition table.
    :return: Active and reactive power arrays.
    """
    active_power: np.ndarray = np.zeros(len(time_index), dtype=float)
    reactive_power: np.ndarray = np.zeros(len(time_index), dtype=float)

    for _, row in component_table.iterrows():
        enabled: bool = bool(row["enabled"])

        if enabled:
            archetype: LoadArchetype = LoadArchetype(str(row["archetype"]))
            scale: float = float(row["scale"])
            scaling_mode: ScalingMode = ScalingMode(str(row["scaling_mode"]))
            power_factor: float = float(row["power_factor"])
            annual_growth: float = float(row["annual_growth"])
            shape: np.ndarray = build_archetype_shape(time_index=time_index, archetype=archetype)
            scaled_power: np.ndarray = scale_shape(shape=shape, scale=scale, scaling_mode=scaling_mode)
            growth: np.ndarray = get_growth_multiplier(time_index=time_index, annual_growth_percent=annual_growth)
            component_p: np.ndarray = scaled_power * growth
            component_q: np.ndarray = get_reactive_power(active_power=component_p, power_factor=power_factor)
            active_power += component_p
            reactive_power += component_q
        else:
            pass

    return active_power, reactive_power


class LoadDesigner(QtWidgets.QDialog):
    """
    Load profile composition wizard.
    """

    def __init__(self,
                 time_array: Sequence[Union[str, datetime, pd.Timestamp]] | None = None,
                 active_power: float = 0.0,
                 reactive_power: float = 0.0,
                 latitude: Union[float, None] = None,
                 longitude: Union[float, None] = None,
                 load_name: str = "",
                 bus_name: str = "",
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        :param time_array: MultiCircuit time profile.
        :param active_power: Snapshot active power in MW.
        :param reactive_power: Snapshot reactive power in MVAr.
        :param latitude: Load bus latitude in degrees.
        :param longitude: Load bus longitude in degrees.
        :param load_name: Load name.
        :param bus_name: Bus name.
        :param parent: Parent widget.
        """
        QtWidgets.QDialog.__init__(self, parent)
        self.ui: Ui_Dialog = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('Load designer'))

        if time_array is None:
            start_time: datetime = datetime(year=2026, month=1, day=1)
            self.time_array: pd.DatetimeIndex = pd.to_datetime([start_time + timedelta(hours=i) for i in range(24)])
        else:
            self.time_array = pd.DatetimeIndex(pd.to_datetime(time_array, errors="coerce"))

        self.P: np.ndarray = np.zeros(len(self.time_array), dtype=float)
        self.Q: np.ndarray = np.zeros(len(self.time_array), dtype=float)
        self.latitude: Union[float, None] = latitude
        self.longitude: Union[float, None] = longitude
        self.temperature: Union[np.ndarray, None] = None
        self.wind_speed: Union[np.ndarray, None] = None
        self.is_accepted: bool = False
        self.is_generated: bool = False
        self.component_model: LoadComponentModel = LoadComponentModel(data=get_default_component_table(active_power))
        self.accept_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Accept")
        self.cancel_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Cancel")

        self.ui.tableView.setModel(self.component_model)
        self.ui.draw_by_peak_pushButton.clicked.connect(self.process_by_peak)
        self.ui.draw_by_points_pushButton.clicked.connect(self.generate_from_components)
        self.accept_button.clicked.connect(self.accept_click)
        self.cancel_button.clicked.connect(self.reject)
        self.ui.horizontalLayout_9.addWidget(self.accept_button)
        self.ui.horizontalLayout_9.addWidget(self.cancel_button)

        self.ui.draw_by_peak_pushButton.setText("Generate")
        self.ui.draw_by_points_pushButton.setText("Generate")
        self.ui.toolBox.setItemText(self.ui.toolBox.indexOf(self.ui.page), "Definition by load components")
        self.ui.tableView.resizeColumnsToContents()

        if reactive_power != 0.0 and active_power > 0.0:
            initial_pf: float = active_power / float(np.sqrt(active_power * active_power + reactive_power * reactive_power))
            self.component_model.data_frame.loc[:, "power_factor"] = initial_pf
        else:
            pass

        if load_name != "" or bus_name != "":
            self.setWindowTitle("Load designer - " + load_name + " / " + bus_name)
        else:
            pass

        self.generate_from_components()

    def done(self, result: int) -> None:
        """
        Release plot resources before the modal dialog closes.

        :param result: Qt dialog result code.
        :return: None.
        """
        self.ui.plotwidget.dispose()
        QtWidgets.QDialog.done(self, result)

    def msg(self, text: str, title: str = "Warning") -> None:
        """
        Show a message box.

        :param text: Text to display.
        :param title: Window title.
        :return: Nothing.
        """
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setText(text)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg.exec()

    def process_by_peak(self) -> None:
        """
        Generate a daily shape from peak points and map it to the MultiCircuit time profile.

        :return: Nothing.
        """
        hour_values: np.ndarray = (self.time_array.hour.to_numpy(dtype=float) +
                                   self.time_array.minute.to_numpy(dtype=float) / 60.0)
        points_x: np.ndarray = np.array([0.0,
                                         self.ui.night_valley_timeEdit.time().hour() +
                                         self.ui.night_valley_timeEdit.time().minute() / 60.0,
                                         self.ui.morning_peak_timeEdit.time().hour() +
                                         self.ui.morning_peak_timeEdit.time().minute() / 60.0,
                                         self.ui.afternoon_valley_timeEdit.time().hour() +
                                         self.ui.afternoon_valley_timeEdit.time().minute() / 60.0,
                                         self.ui.evening_peak_timeEdit.time().hour() +
                                         self.ui.evening_peak_timeEdit.time().minute() / 60.0,
                                         24.0], dtype=float)
        points_y: np.ndarray = np.array([self.ui.night_valley_doubleSpinBox.value(),
                                         self.ui.night_valley_doubleSpinBox.value(),
                                         self.ui.morning_peak_doubleSpinBox.value(),
                                         self.ui.afternoon_valley_doubleSpinBox.value(),
                                         self.ui.evening_peak_doubleSpinBox.value(),
                                         self.ui.night_valley_doubleSpinBox.value()], dtype=float)
        self.P = np.interp(hour_values, points_x, points_y)
        self.Q = get_reactive_power(active_power=self.P, power_factor=0.95)
        self.update_weather_profiles(time_index=self.time_array)
        self.update_results()

    def generate_from_components(self) -> None:
        """
        Generate active and reactive profiles from the load component table.

        :return: Nothing.
        """
        ok: bool
        time_index: pd.DatetimeIndex
        message: str
        ok, time_index, message = parse_load_time_array(time_array=self.time_array)

        if ok:
            try:
                self.P, self.Q = compose_load_profiles(time_index=time_index,
                                                       component_table=self.component_model.data_frame)
                self.update_weather_profiles(time_index=time_index)
                self.update_results()
            except (ValueError, TypeError) as err:
                self.msg(text=str(err), title="Load designer")
        else:
            if message == "The time profile is empty":
                # An absent circuit time profile is a valid state for the editor.
                # Keep the designer quiet and leave the result disabled instead of
                # presenting it as an error condition to the user.
                self.P = np.zeros(0, dtype=float)
                self.Q = np.zeros(0, dtype=float)
                self.temperature = None
                self.wind_speed = None
                self.update_results()
            else:
                self.msg(text=message, title="Load designer")

    def update_weather_profiles(self, time_index: pd.DatetimeIndex) -> None:
        """
        Fill optional weather arrays using Open-Meteo when bus coordinates are available.

        :param time_index: MultiCircuit time profile.
        :return: Nothing.
        """
        self.temperature = None
        self.wind_speed = None

        # Weather enrichment requires a non-empty time profile. When the circuit
        # has no time series yet, keep the optional weather arrays unset and exit
        # quietly instead of treating it as an error.
        if len(time_index) == 0:
            return
        elif self.latitude is None or self.longitude is None:
            pass
        else:
            reference_ok: bool
            base_year: int
            reference_message: str
            reference_ok, base_year, reference_message = get_load_weather_reference_base_year(ts1=time_index[0],
                                                                                              ts2=time_index[-1])

            if reference_ok:
                mapped_time_index: pd.DatetimeIndex = build_mapped_load_weather_time_index(time_index=time_index,
                                                                                           base_year=base_year)
                weather_ok: bool
                weather_df: pd.DataFrame
                weather_ok, weather_df = get_open_meteo_load_weather_df(time_index=mapped_time_index,
                                                                        latitude=float(self.latitude),
                                                                        longitude=float(self.longitude))

                if weather_ok:
                    interpolation_ok: bool
                    interpolated_df: pd.DataFrame
                    interpolation_ok, interpolated_df = interpolate_load_weather_to_requested_time(
                        weather_df=weather_df,
                        mapped_time_index=mapped_time_index)

                    if interpolation_ok:
                        self.temperature = interpolated_df["temperature"].to_numpy(dtype=float)
                        self.wind_speed = interpolated_df["wind_speed"].to_numpy(dtype=float)
                    else:
                        pass
                else:
                    pass
            else:
                _ = reference_message

    def update_results(self) -> None:
        """
        Update plot and mark generated profiles as ready for acceptance.

        :return: Nothing.
        """
        result_df: pd.DataFrame = pd.DataFrame(data=dict(P=self.P, Q=self.Q), index=self.time_array)
        self.ui.plotwidget.clear()
        axis = self.ui.plotwidget.get_axis()
        result_df.plot(ax=axis)
        self.ui.plotwidget.redraw()
        # Zero-length arrays mean that the circuit has no usable time profile yet,
        # so the designer must remain disabled even though the lengths match.
        self.is_generated = (len(self.time_array) > 0 and
                             len(self.P) == len(self.time_array) and
                             len(self.Q) == len(self.time_array))
        self.is_accepted = False

    def accept_click(self) -> None:
        """
        Accept the currently generated profile and close the dialog.

        :return: Nothing.
        """
        if self.is_generated:
            self.is_accepted = True
            self.accept()
        else:
            self.msg(text="Generate a load profile before accepting the wizard result.",
                     title="Load designer")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo_start: datetime = datetime(year=2026, month=1, day=1)
    demo_time: pd.DatetimeIndex = pd.to_datetime([demo_start + timedelta(hours=i) for i in range(24 * 14)])
    window = LoadDesigner(time_array=demo_time, active_power=20.0, reactive_power=5.0)
    window.resize(1.61 * 700.0, 600.0)
    window.show()
    sys.exit(app.exec())
