# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime
from typing import List, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import requests
from matplotlib import pyplot as plt
from PySide6 import QtCore, QtWidgets

from VeraGrid.Gui.DeviceEditors.GeneratorEditor.WindPowerWizard.wind_power_wizard_gui import Ui_MainWindow
from VeraGrid.Gui.messages import error_msg
from VeraGrid.Gui.pandas_model import PandasModel


class WindTurbineParameterModel(QtCore.QAbstractTableModel):
    """
    Editable parameter/value table model for the selected wind turbine.
    """

    def __init__(self, data: pd.DataFrame, parent: QtCore.QObject = None) -> None:
        """
        :param data: Wind turbine parameter table.
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
        :param role: Qt data role.
        :return: Cell text or None.
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
        :param value: Edited value.
        :param role: Qt data role.
        :return: True if the value was accepted.
        """
        if index.isValid() and role == QtCore.Qt.ItemDataRole.EditRole:
            if index.column() == 1:
                parameter_name: str = str(self.data_frame.iat[index.row(), 0])
                old_value: object = self.data_frame.iat[index.row(), index.column()]
                new_value: object

                if isinstance(old_value, bool):
                    text_value: str = str(value).strip().lower()
                    new_value = text_value in ["1", "true", "yes", "y"]
                else:
                    if parameter_name in ["hub_height", "plant_power_mw"]:
                        new_value = float(value)
                    else:
                        new_value = str(value)

                self.data_frame.iat[index.row(), index.column()] = new_value
                self.dataChanged.emit(index, index, [role])
                return True
            else:
                return False
        else:
            return False

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        """
        :param index: Cell index.
        :return: Qt item flags.
        """
        if index.isValid():
            if index.column() == 1:
                return (QtCore.Qt.ItemFlag.ItemIsEditable |
                        QtCore.Qt.ItemFlag.ItemIsEnabled |
                        QtCore.Qt.ItemFlag.ItemIsSelectable)
            else:
                return (QtCore.Qt.ItemFlag.ItemIsEnabled |
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
        :param role: Qt data role.
        :return: Header text or None.
        """
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return str(self.data_frame.columns[section])
            else:
                return str(self.data_frame.index[section])
        else:
            return None


def parse_wind_time_array(time_array: Sequence[Union[str, datetime, pd.Timestamp]]) -> Tuple[bool, pd.DatetimeIndex, str]:
    """
    Convert the circuit time profile to a validated pandas datetime index.

    :param time_array: Sequence with string or datetime-like time values.
    :return: Validity flag, parsed time index and validation message.
    """
    time_index: pd.DatetimeIndex = pd.DatetimeIndex(pd.to_datetime(time_array, errors="coerce"))
    message: str = ""

    if len(time_index) > 0:
        invalid_mask: np.ndarray = pd.isna(time_index)

        if bool(np.any(invalid_mask)):
            message = "The time profile contains values that cannot be converted to dates"
            return False, pd.DatetimeIndex(list()), message
        else:
            if time_index.is_monotonic_increasing:
                return True, time_index, message
            else:
                message = "The time profile must be sorted from oldest to newest"
                return False, pd.DatetimeIndex(list()), message
    else:
        message = "The time profile is empty"
        return False, pd.DatetimeIndex(list()), message


def get_wind_reference_base_year(ts1: pd.Timestamp, ts2: pd.Timestamp) -> Tuple[bool, int, str]:
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
        message = f"The time span of your profile is {year_span} year(s), Open-Meteo span is 10 years maximum"
        return False, reference_year, message


def build_mapped_wind_time_index(time_index: pd.DatetimeIndex, base_year: int) -> pd.DatetimeIndex:
    """
    Map circuit timestamps to a historical weather year while preserving month, day and time.

    :param time_index: Circuit time index.
    :param base_year: Historical base year used for the mapped timestamps.
    :return: Historical weather time index.
    """
    ts1: pd.Timestamp = time_index[0]
    mapped_timestamps: List[datetime] = list()

    for ts in time_index:
        target_year: int = base_year + int(ts.year - ts1.year)
        mapped_timestamp: datetime = datetime(year=target_year,
                                              month=int(ts.month),
                                              day=int(ts.day),
                                              hour=int(ts.hour),
                                              minute=int(ts.minute),
                                              second=int(ts.second),
                                              microsecond=int(ts.microsecond))
        mapped_timestamps.append(mapped_timestamp)

    return pd.DatetimeIndex(pd.to_datetime(mapped_timestamps))


def get_open_meteo_wind_weather_df(time_index: pd.DatetimeIndex,
                                   latitude: float,
                                   longitude: float) -> Tuple[bool, pd.DataFrame]:
    """
    Download hourly wind weather data from the free Open-Meteo historical weather API.

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
                        hourly="wind_speed_100m,temperature_2m,surface_pressure",
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
            weather_df["wind_speed_100m"] = np.asarray(hourly["wind_speed_100m"], dtype=float)
            weather_df["temperature_2m"] = np.asarray(hourly["temperature_2m"], dtype=float)
            weather_df["surface_pressure"] = np.asarray(hourly["surface_pressure"], dtype=float)
            return True, weather_df
        else:
            error_msg(QtCore.QCoreApplication.translate(
                "MainWindow",
                "Open-Meteo did not return hourly weather data",
            ))
            return False, pd.DataFrame()

    except (requests.RequestException, KeyError, ValueError, TypeError) as err:
        error_msg(QtCore.QCoreApplication.translate(
            "MainWindow",
            "Open-Meteo weather request failed :(\n{error_text}",
        ).format(error_text=str(err)))
        return False, pd.DataFrame()


def build_windpowerlib_weather_df(weather_df: pd.DataFrame, roughness_length: float) -> pd.DataFrame:
    """
    Convert Open-Meteo weather columns to the MultiIndex format expected by windpowerlib.

    :param weather_df: Open-Meteo weather data frame.
    :param roughness_length: Surface roughness length in m.
    :return: windpowerlib weather data frame.
    """
    columns: pd.MultiIndex = pd.MultiIndex.from_tuples([("wind_speed", 100),
                                                        ("temperature", 2),
                                                        ("pressure", 0),
                                                        ("roughness_length", 0)],
                                                       names=["variable_name", "height"])
    windpowerlib_weather_df: pd.DataFrame = pd.DataFrame(index=weather_df.index, columns=columns, dtype=float)
    windpowerlib_weather_df[("wind_speed", 100)] = weather_df["wind_speed_100m"].to_numpy(dtype=float)
    windpowerlib_weather_df[("temperature", 2)] = weather_df["temperature_2m"].to_numpy(dtype=float) + 273.15
    windpowerlib_weather_df[("pressure", 0)] = weather_df["surface_pressure"].to_numpy(dtype=float) * 100.0
    windpowerlib_weather_df[("roughness_length", 0)] = np.full(len(weather_df), roughness_length)
    return windpowerlib_weather_df


def build_generic_wind_power_curve(nominal_power_w: float) -> pd.DataFrame:
    """
    Build a generic onshore wind turbine power curve.

    :param nominal_power_w: Rated turbine power in W.
    :return: Power curve with wind speed in m/s and power in W.
    """
    wind_speed: np.ndarray = np.array([0.0, 2.99, 3.0, 5.0, 8.0, 11.0, 12.0, 25.0, 25.01, 40.0], dtype=float)
    power_pu: np.ndarray = np.array([0.0, 0.0, 0.01, 0.08, 0.35, 0.82, 1.0, 1.0, 0.0, 0.0], dtype=float)
    power_w: np.ndarray = nominal_power_w * power_pu
    return pd.DataFrame(data=dict(wind_speed=wind_speed, value=power_w))


def load_windpowerlib_turbine_templates() -> Tuple[bool, pd.DataFrame]:
    """
    Load the windpowerlib turbine template table.

    :return: Success flag and turbine template table.
    """
    try:
        from windpowerlib import data as wt
    except ImportError as err:
        error_msg(QtCore.QCoreApplication.translate(
            "MainWindow",
            "windpowerlib is required to load turbine templates:\n{error_text}",
        ).format(error_text=str(err)))
        return False, pd.DataFrame()

    try:
        templates_df: pd.DataFrame = wt.get_turbine_types(print_out=False)
        return True, templates_df
    except (KeyError, ValueError, TypeError) as err:
        error_msg(QtCore.QCoreApplication.translate(
            "MainWindow",
            "windpowerlib turbine template loading failed :(\n{error_text}",
        ).format(error_text=str(err)))
        return False, pd.DataFrame()


def enrich_turbine_template_table(templates_df: pd.DataFrame,
                                  hub_height: float,
                                  plant_power: float) -> pd.DataFrame:
    """
    Add editable operating parameters to the windpowerlib turbine template list.

    :param templates_df: Raw windpowerlib turbine template table.
    :param hub_height: Default hub height in m.
    :param plant_power: Default plant power in MW.
    :return: Enriched turbine template table.
    """
    enriched_df: pd.DataFrame = templates_df.copy()

    if "hub_height" in enriched_df.columns:
        pass
    else:
        enriched_df["hub_height"] = np.full(len(enriched_df), hub_height)

    if "plant_power_mw" in enriched_df.columns:
        pass
    else:
        enriched_df["plant_power_mw"] = np.full(len(enriched_df), plant_power)

    return enriched_df


def build_turbine_parameter_table(template_label: str,
                                  turbine_type: Union[str, None],
                                  manufacturer: str,
                                  has_power_curve: bool,
                                  has_cp_curve: bool,
                                  hub_height: float,
                                  plant_power: float) -> pd.DataFrame:
    """
    Build the editable parameter table shown for the selected turbine.

    :param template_label: Human-readable template label.
    :param turbine_type: windpowerlib turbine type or None.
    :param manufacturer: Turbine manufacturer.
    :param has_power_curve: True if a power curve exists.
    :param has_cp_curve: True if a Cp curve exists.
    :param hub_height: Hub height in m.
    :param plant_power: Plant power in MW.
    :return: Parameter/value table.
    """
    turbine_type_text: str

    if turbine_type is None:
        turbine_type_text = "Generic onshore turbine"
    else:
        turbine_type_text = turbine_type

    return pd.DataFrame(data=dict(parameter=["template",
                                             "manufacturer",
                                             "turbine_type",
                                             "hub_height",
                                             "plant_power_mw",
                                             "has_power_curve",
                                             "has_cp_curve"],
                                  value=[template_label,
                                         manufacturer,
                                         turbine_type_text,
                                         hub_height,
                                         plant_power,
                                         has_power_curve,
                                         has_cp_curve]))


def get_parameter_value(parameter_df: pd.DataFrame, parameter_name: str, fallback_value: object) -> object:
    """
    Get a value from a parameter/value turbine table.

    :param parameter_df: Parameter/value table.
    :param parameter_name: Parameter name.
    :param fallback_value: Fallback value.
    :return: Parameter value or fallback value.
    """
    matches: pd.DataFrame = parameter_df[parameter_df["parameter"] == parameter_name]

    if len(matches) > 0:
        return matches.iloc[0]["value"]
    else:
        return fallback_value


def make_turbine_template_label(template_row: pd.Series) -> str:
    """
    Build a readable label for a windpowerlib turbine template.

    :param template_row: Wind turbine template row.
    :return: Combo box label.
    """
    manufacturer: str = str(template_row["manufacturer"])
    turbine_type: str = str(template_row["turbine_type"])
    return manufacturer + " - " + turbine_type


def get_selected_turbine_type(template_label: str) -> Union[str, None]:
    """
    Extract the windpowerlib turbine type from a combo box label.

    :param template_label: Combo box label.
    :return: windpowerlib turbine type or None for generic turbine.
    """
    generic_label: str = "Generic onshore turbine"

    if template_label == generic_label:
        return None
    else:
        parts: List[str] = template_label.split(" - ", 1)

        if len(parts) == 2:
            return parts[1]
        else:
            return template_label


def create_windpowerlib_turbine(peak_power: float,
                                hub_height: float,
                                turbine_type: Union[str, None]):
    """
    Create a windpowerlib turbine object from either a template or the generic curve.

    :param peak_power: Generator peak power in MW.
    :param hub_height: Turbine hub height in m.
    :param turbine_type: windpowerlib turbine type or None for the generic turbine.
    :return: windpowerlib WindTurbine object.
    """
    from windpowerlib import WindTurbine

    nominal_power_w: float = peak_power * 1e6

    if turbine_type is None:
        power_curve: pd.DataFrame = build_generic_wind_power_curve(nominal_power_w=nominal_power_w)
        turbine: WindTurbine = WindTurbine(nominal_power=nominal_power_w,
                                           hub_height=hub_height,
                                           power_curve=power_curve)
    else:
        turbine = WindTurbine(turbine_type=turbine_type,
                              hub_height=hub_height)

    return turbine


def calculate_wind_power_with_windpowerlib(weather_df: pd.DataFrame,
                                           peak_power: float,
                                           hub_height: float,
                                           roughness_length: float,
                                           turbine_type: Union[str, None]) -> Tuple[bool, pd.Series]:
    """
    Calculate wind active power with windpowerlib.

    :param weather_df: Open-Meteo weather data frame.
    :param peak_power: Generator peak power in MW.
    :param hub_height: Turbine hub height in m.
    :param roughness_length: Surface roughness length in m.
    :param turbine_type: windpowerlib turbine type or None for the generic turbine.
    :return: Success flag and active power in W.
    """
    try:
        from windpowerlib import ModelChain
    except ImportError as err:
        error_msg(QtCore.QCoreApplication.translate(
            "MainWindow",
            "windpowerlib is required to generate wind power profiles:\n{error_text}",
        ).format(error_text=str(err)))
        return False, pd.Series(dtype=float)

    nominal_power_w: float = peak_power * 1e6
    windpowerlib_weather_df: pd.DataFrame = build_windpowerlib_weather_df(weather_df=weather_df,
                                                                          roughness_length=roughness_length)

    turbine = create_windpowerlib_turbine(peak_power=peak_power,
                                          hub_height=hub_height,
                                          turbine_type=turbine_type)

    try:
        model_chain: ModelChain = ModelChain(power_plant=turbine,
                                             wind_speed_model="interpolation_extrapolation",
                                             density_model="barometric",
                                             temperature_model="linear_gradient",
                                             power_output_model="power_curve",
                                             density_correction=False)
        model_chain.run_model(windpowerlib_weather_df)
        turbine_nominal_power_w: float = float(turbine.nominal_power)

        if turbine_nominal_power_w > 0.0:
            scale_factor: float = nominal_power_w / turbine_nominal_power_w
        else:
            scale_factor = 1.0

        power_output: pd.Series = (pd.Series(model_chain.power_output) * scale_factor).clip(lower=0.0,
                                                                                           upper=nominal_power_w)
        return True, power_output
    except (KeyError, ValueError, TypeError) as err:
        error_msg(QtCore.QCoreApplication.translate(
            "MainWindow",
            "windpowerlib wind calculation failed :(\n{error_text}",
        ).format(error_text=str(err)))
        return False, pd.Series(dtype=float)


def get_wind_power_df(time_array: Sequence[Union[str, datetime, pd.Timestamp]],
                      latitude: float,
                      longitude: float,
                      peak_power: float,
                      hub_height: float,
                      roughness_length: float,
                      turbine_type: Union[str, None]) -> Tuple[bool, pd.DataFrame]:
    """
    Download Open-Meteo wind weather data and calculate wind generator active power.

    :param time_array: Sequence with the circuit time values.
    :param latitude: Site latitude in degrees.
    :param longitude: Site longitude in degrees.
    :param peak_power: Generator peak power in MW.
    :param hub_height: Turbine hub height in m.
    :param roughness_length: Surface roughness length in m.
    :param turbine_type: windpowerlib turbine type or None for the generic turbine.
    :return: Success flag and wind active power data aligned to the requested time profile.
    """
    ok: bool
    time_index: pd.DatetimeIndex
    message: str
    ok, time_index, message = parse_wind_time_array(time_array=time_array)

    if ok:
        if -90.0 <= latitude <= 90.0:
            valid_latitude: bool = True
        else:
            valid_latitude = False

        if -180.0 <= longitude <= 180.0:
            valid_longitude: bool = True
        else:
            valid_longitude = False

        if peak_power > 0.0:
            valid_peak_power: bool = True
        else:
            valid_peak_power = False

        if hub_height > 0.0:
            valid_hub_height: bool = True
        else:
            valid_hub_height = False

        if roughness_length >= 0.0:
            valid_roughness_length: bool = True
        else:
            valid_roughness_length = False

        if valid_latitude and valid_longitude and valid_peak_power and valid_hub_height and valid_roughness_length:
            ts1: pd.Timestamp = time_index[0]
            ts2: pd.Timestamp = time_index[-1]
            valid_base_year: bool
            base_year: int
            valid_base_year, base_year, message = get_wind_reference_base_year(ts1=ts1, ts2=ts2)

            if valid_base_year:
                mapped_time_index: pd.DatetimeIndex = build_mapped_wind_time_index(time_index=time_index,
                                                                                   base_year=base_year)
                weather_ok: bool
                weather_df: pd.DataFrame
                weather_ok, weather_df = get_open_meteo_wind_weather_df(time_index=mapped_time_index,
                                                                        latitude=latitude,
                                                                        longitude=longitude)

                if weather_ok:
                    power_ok: bool
                    power_w: pd.Series
                    power_ok, power_w = calculate_wind_power_with_windpowerlib(weather_df=weather_df,
                                                                               peak_power=peak_power,
                                                                               hub_height=hub_height,
                                                                               roughness_length=roughness_length,
                                                                               turbine_type=turbine_type)

                    if power_ok:
                        source_df: pd.DataFrame = pd.DataFrame(data=dict(P=power_w.to_numpy(dtype=float)),
                                                               index=weather_df.index.asi8)
                        source_df.sort_index(inplace=True)
                        requested_index: np.ndarray = mapped_time_index.asi8
                        interpolation_index: np.ndarray = np.union1d(source_df.index.values, requested_index)
                        interpolated_df: pd.DataFrame = source_df.reindex(interpolation_index).interpolate(method="index")
                        result_df: pd.DataFrame = interpolated_df.ffill().bfill().reindex(requested_index)

                        if bool(result_df["P"].isna().any()):
                            error_msg("Wind data was returned, but it could not be interpolated to the circuit profile")
                            return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))
                        else:
                            result_df["P"] = np.clip(result_df["P"].to_numpy(dtype=float), 0.0, peak_power * 1e6)
                            weather_source_df: pd.DataFrame = weather_df.copy()
                            weather_source_df.index = weather_source_df.index.asi8
                            weather_source_df.sort_index(inplace=True)
                            weather_interpolated_df: pd.DataFrame = (
                                weather_source_df.reindex(interpolation_index).interpolate(method="index")
                            )
                            weather_result_df: pd.DataFrame = weather_interpolated_df.ffill().bfill().reindex(
                                requested_index)
                            result_df["temperature"] = weather_result_df["temperature_2m"].to_numpy(dtype=float)
                            result_df["wind_speed"] = weather_result_df["wind_speed_100m"].to_numpy(dtype=float)
                            return True, result_df
                    else:
                        return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))
                else:
                    return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))
            else:
                error_msg(message)
                return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))
        else:
            if valid_latitude:
                if valid_longitude:
                    if valid_peak_power:
                        if valid_hub_height:
                            error_msg(QtCore.QCoreApplication.translate(
                                "MainWindow",
                                "The roughness length must be zero or greater",
                            ))
                        else:
                            error_msg(QtCore.QCoreApplication.translate("MainWindow", "The hub height must be greater than zero"))
                    else:
                        error_msg(QtCore.QCoreApplication.translate(
                            "MainWindow",
                            "The wind generator peak power must be greater than zero",
                        ))
                else:
                    error_msg(QtCore.QCoreApplication.translate(
                        "MainWindow",
                        "The longitude must be between -180 and 180 degrees",
                    ))
            else:
                error_msg(QtCore.QCoreApplication.translate("MainWindow", "The latitude must be between -90 and 90 degrees"))

            return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))
    else:
        error_msg(message)
        return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))


class WindFarmWizard(QtWidgets.QDialog):
    """
    Wind farm wizard window.
    """

    def __init__(self,
                 time_array: Sequence[Union[str, datetime, pd.Timestamp]],
                 peak_power: float,
                 latitude: float,
                 longitude: float,
                 gen_name: str = "",
                 bus_name: str = "",
                 title: str = "Wind farm wizard") -> None:
        """
        :param time_array: Array of time values.
        :param peak_power: Generator peak power in MW.
        :param latitude: Latitude in degrees.
        :param longitude: Longitude in degrees.
        :param gen_name: Generator name.
        :param bus_name: Bus name.
        :param title: Window title.
        """
        QtWidgets.QDialog.__init__(self)
        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setObjectName("self")
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)

        self.is_accepted: bool = False
        self.time_array: Sequence[Union[str, datetime, pd.Timestamp]] = time_array
        self.P: np.ndarray = np.zeros(len(time_array))
        self.temperature: Union[np.ndarray, None] = None
        self.wind_speed: Union[np.ndarray, None] = None
        self.df: Union[pd.DataFrame, None] = None
        self.ok: bool = False
        self.template_df: pd.DataFrame = pd.DataFrame()
        self.parameter_model: Union[WindTurbineParameterModel, None] = None

        self.ui.powerSpinBox.setValue(peak_power)
        self.ui.latitudeSpinBox.setValue(latitude)
        self.ui.longitudeSpinBox.setValue(longitude)
        self.ui.label_3.setText(f"Wind turbine data - Generator {gen_name} / Bus {bus_name}")

        self.ui.acceptButton.clicked.connect(self.accept_click)
        self.ui.loadButton.clicked.connect(self.generate_click)
        self.ui.plotButton.clicked.connect(self.plot)
        self.ui.plotDesignCurvesButton.clicked.connect(self.plot_design_curves)
        self.ui.templeteComboBox.currentIndexChanged.connect(self.update_turbine_parameter_table)

        self.setWindowTitle(title)
        self.load_turbine_templates()
        self.update_results()

    def load_turbine_templates(self) -> None:
        """
        Load windpowerlib turbine templates into the combo box and library table.

        :return: Nothing.
        """
        self.ui.templeteComboBox.clear()
        self.ui.templeteComboBox.addItem("Generic onshore turbine")

        ok: bool
        templates_df: pd.DataFrame
        ok, templates_df = load_windpowerlib_turbine_templates()

        if ok:
            self.template_df = enrich_turbine_template_table(templates_df=templates_df,
                                                             hub_height=self.ui.hubHeightSpinBox.value(),
                                                             plant_power=self.ui.powerSpinBox.value())

            for _, template_row in self.template_df.iterrows():
                template_label: str = make_turbine_template_label(template_row=template_row)
                self.ui.templeteComboBox.addItem(template_label)

        else:
            self.template_df = pd.DataFrame(data=dict(turbine_type=["Generic onshore turbine"],
                                                      manufacturer=["VeraGrid"],
                                                      hub_height=[100.0],
                                                      has_power_curve=[True],
                                                      has_cp_curve=[False]))

        self.update_turbine_parameter_table()
        self.ui.windTurbineTableView.resizeColumnsToContents()

    def get_selected_turbine_row_index_from_combo(self) -> int:
        """
        Get the selected turbine row index from the combo box.

        :return: Selected row index.
        """
        combo_index: int = int(self.ui.templeteComboBox.currentIndex()) - 1

        if combo_index >= 0:
            return combo_index
        else:
            return -1

    def update_turbine_parameter_table(self) -> None:
        """
        Show editable parameters for the currently selected turbine.

        :return: Nothing.
        """
        selected_row_index: int = self.get_selected_turbine_row_index_from_combo()

        if selected_row_index >= 0 and selected_row_index < len(self.template_df):
            template_row: pd.Series = self.template_df.iloc[selected_row_index]
            template_label: str = make_turbine_template_label(template_row=template_row)
            turbine_type: Union[str, None] = str(template_row["turbine_type"])
            manufacturer: str = str(template_row["manufacturer"])
            has_power_curve: bool = bool(template_row["has_power_curve"])
            has_cp_curve: bool = bool(template_row["has_cp_curve"])
            hub_height: float = float(template_row["hub_height"])
            plant_power: float = float(template_row["plant_power_mw"])
        else:
            template_label = "Generic onshore turbine"
            turbine_type = None
            manufacturer = "VeraGrid"
            has_power_curve = True
            has_cp_curve = False
            hub_height = self.ui.hubHeightSpinBox.value()
            plant_power = self.ui.powerSpinBox.value()

        parameter_df: pd.DataFrame = build_turbine_parameter_table(template_label=template_label,
                                                                   turbine_type=turbine_type,
                                                                   manufacturer=manufacturer,
                                                                   has_power_curve=has_power_curve,
                                                                   has_cp_curve=has_cp_curve,
                                                                   hub_height=hub_height,
                                                                   plant_power=plant_power)
        self.parameter_model = WindTurbineParameterModel(data=parameter_df)
        self.ui.windTurbineTableView.setModel(self.parameter_model)
        self.ui.windTurbineTableView.resizeColumnsToContents()

    def get_parameter_df(self) -> pd.DataFrame:
        """
        Get the current selected turbine parameter table.

        :return: Parameter/value table.
        """
        if self.parameter_model is None:
            self.update_turbine_parameter_table()
        else:
            pass

        if self.parameter_model is None:
            return pd.DataFrame()
        else:
            return self.parameter_model.data_frame

    def get_selected_turbine_type(self) -> Union[str, None]:
        """
        Get the selected turbine type using the editable table as source of truth.

        :return: windpowerlib turbine type or None for the generic turbine.
        """
        parameter_df: pd.DataFrame = self.get_parameter_df()
        turbine_type_value: object = get_parameter_value(parameter_df=parameter_df,
                                                        parameter_name="turbine_type",
                                                        fallback_value="Generic onshore turbine")
        turbine_type_text: str = str(turbine_type_value)

        if turbine_type_text == "Generic onshore turbine":
            return None
        else:
            return turbine_type_text

    def get_selected_hub_height(self) -> float:
        """
        Get the selected hub height from the editable table or the site page.

        :return: Hub height in m.
        """
        parameter_df: pd.DataFrame = self.get_parameter_df()
        raw_value: object = get_parameter_value(parameter_df=parameter_df,
                                               parameter_name="hub_height",
                                               fallback_value=self.ui.hubHeightSpinBox.value())

        try:
            hub_height: float = float(raw_value)
        except (TypeError, ValueError):
            hub_height = self.ui.hubHeightSpinBox.value()

        if hub_height > 0.0:
            return hub_height
        else:
            return self.ui.hubHeightSpinBox.value()

    def get_selected_plant_power(self) -> float:
        """
        Get the selected plant power from the editable table or the site page.

        :return: Plant power in MW.
        """
        parameter_df: pd.DataFrame = self.get_parameter_df()
        raw_value: object = get_parameter_value(parameter_df=parameter_df,
                                               parameter_name="plant_power_mw",
                                               fallback_value=self.ui.powerSpinBox.value())

        try:
            plant_power: float = float(raw_value)
        except (TypeError, ValueError):
            plant_power = self.ui.powerSpinBox.value()

        if plant_power > 0.0:
            return plant_power
        else:
            return self.ui.powerSpinBox.value()

    def get_selected_windpowerlib_turbine(self):
        """
        Create the currently selected windpowerlib turbine.

        :return: windpowerlib WindTurbine object or None.
        """
        try:
            turbine = create_windpowerlib_turbine(peak_power=self.get_selected_plant_power(),
                                                  hub_height=self.get_selected_hub_height(),
                                                  turbine_type=self.get_selected_turbine_type())
            return turbine
        except (ImportError, KeyError, ValueError, TypeError) as err:
            error_msg(self.tr("The selected wind turbine could not be created:\n{error_text}").format(
                error_text=str(err),
            ))
            return None

    def plot_design_curves(self) -> None:
        """
        Plot Cp on the left axis and power on the right axis for the selected turbine.

        :return: Nothing.
        """
        turbine = self.get_selected_windpowerlib_turbine()

        if turbine is not None:
            figure, cp_axis = plt.subplots()
            power_axis = cp_axis.twinx()
            plotted_cp: bool = False
            plotted_power: bool = False

            if turbine.power_coefficient_curve is not None:
                turbine.power_coefficient_curve.plot(x="wind_speed",
                                                     y="value",
                                                     ax=cp_axis,
                                                     color="tab:blue",
                                                     label="Cp")
                plotted_cp = True
            else:
                pass

            if turbine.power_curve is not None:
                turbine.power_curve.plot(x="wind_speed",
                                         y="value",
                                         ax=power_axis,
                                         color="tab:red",
                                         label="Power")
                plotted_power = True
            else:
                pass

            if plotted_cp or plotted_power:
                cp_axis.set_xlabel("Wind speed (m/s)")
                cp_axis.set_ylabel("Cp", color="tab:blue")
                power_axis.set_ylabel("Power (W)", color="tab:red")
                cp_axis.tick_params(axis="y", labelcolor="tab:blue")
                power_axis.tick_params(axis="y", labelcolor="tab:red")
                figure.suptitle("Wind turbine design curves")
                figure.tight_layout()
                plt.show()
            else:
                error_msg(self.tr("The selected turbine has no design curves"))
        else:
            pass

    def update_results(self) -> None:
        """
        Update the results table with the active power profile.

        :return: Nothing.
        """
        df: pd.DataFrame = pd.DataFrame(data=self.P, index=self.time_array, columns=["P (MW)"])
        model: PandasModel = PandasModel(data=df)
        self.ui.tableView_2.setModel(model)

    def generate_click(self) -> None:
        """
        Generate wind power from Open-Meteo weather and windpowerlib.

        :return: Nothing.
        """
        self.ok, self.df = get_wind_power_df(time_array=self.time_array,
                                             latitude=self.ui.latitudeSpinBox.value(),
                                             longitude=self.ui.longitudeSpinBox.value(),
                                             peak_power=self.get_selected_plant_power(),
                                             hub_height=self.get_selected_hub_height(),
                                             roughness_length=self.ui.roughnessLengthSpinBox.value(),
                                             turbine_type=self.get_selected_turbine_type())
        if self.ok:
            self.P = self.df["P"].to_numpy(dtype=float) / 1e6
            self.temperature = self.df["temperature"].to_numpy(dtype=float)
            self.wind_speed = self.df["wind_speed"].to_numpy(dtype=float)
            self.update_results()
        else:
            self.temperature = None
            self.wind_speed = None
            self.ui.tableView_2.setModel(None)

    def plot(self) -> None:
        """
        Plot the wind power profile.

        :return: Nothing.
        """
        df: pd.DataFrame = pd.DataFrame(data=self.P, index=self.time_array, columns=["P (MW)"])
        df.plot()
        plt.show()

    def accept_click(self) -> None:
        """
        Accept and close the wizard.

        :return: Nothing.
        """
        self.is_accepted = self.ok
        self.accept()


if __name__ == "__main__":
    import sys

    app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)
    start_time: datetime = datetime(year=2026, month=1, day=1)
    longitude: float = -110.9
    direction: float = 1.0 if longitude > 0.0 else -1.0
    offset: float = direction * longitude * 24.0 / 360.0
    time_array: pd.DatetimeIndex = pd.to_datetime([start_time + pd.Timedelta(hours=i + offset) for i in range(200)])

    window: WindFarmWizard = WindFarmWizard(time_array=time_array,
                                            peak_power=20.0,
                                            latitude=32.2,
                                            longitude=longitude,
                                            gen_name="wind_test",
                                            bus_name="bus_test")
    window.resize(int(1.61 * 700.0), 600)
    window.show()
    sys.exit(app.exec())
