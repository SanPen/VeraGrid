# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from typing import List, Union, Tuple, Sequence
from datetime import datetime, timedelta
import pandas as pd
import requests
import pvlib
from matplotlib import pyplot as plt
from PySide6 import QtCore, QtWidgets
from VeraGrid.Gui.messages import error_msg
from VeraGrid.Gui.DeviceEditors.GeneratorEditor.SolarPowerWizard.solar_power_wizard_gui import Ui_MainWindow
from VeraGrid.Gui.pandas_model import PandasModel


def get_weather_column(data: pd.DataFrame, candidates: List[str]) -> Union[np.ndarray, None]:
    """
    Get the first available weather column from a data frame.

    :param data: Data frame to inspect.
    :param candidates: Candidate column names.
    :return: Column values or None.
    """
    for candidate in candidates:
        if candidate in data.columns:
            return data[candidate].to_numpy(dtype=float)
        else:
            pass

    return None


def parse_pv_time_array(time_array: Sequence[Union[str, datetime, pd.Timestamp]]) -> Tuple[bool, pd.DatetimeIndex, str]:
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


def get_pv_lib_weather_df(time_array: Sequence[Union[str, datetime, pd.Timestamp]],
                          latitude: float,
                          longitude: float,
                          peak_power: float) -> Tuple[bool, pd.DataFrame]:
    """
    Download and align PVGIS solar photovoltaic production for the requested time profile.

    :param time_array: Sequence with the circuit time values.
    :param latitude: Site latitude in degrees.
    :param longitude: Site longitude in degrees.
    :param peak_power: Generator peak power in MW.
    :return: Success flag and PVGIS data aligned to the requested time profile.
    """
    max_year_span: int = 10
    max_days: int = 366 * max_year_span
    ok: bool
    time_index: pd.DatetimeIndex
    message: str
    ok, time_index, message = parse_pv_time_array(time_array=time_array)

    if ok:
        ts1: pd.Timestamp = time_index[0]
        ts2: pd.Timestamp = time_index[-1]
        year_span: int = int(ts2.year - ts1.year)
    else:
        error_msg(message)
        return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))

    time_span_days: int = int((ts2 - ts1).days)

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

    if time_span_days <= max_days:
        valid_time_span: bool = True
    else:
        valid_time_span = False

    if valid_latitude and valid_longitude and valid_peak_power and valid_time_span:

        base_year: int = 2010 + ((int(ts1.year) - 2010) % 4)
        s: datetime = datetime(year=base_year,
                               month=int(ts1.month),
                               day=int(ts1.day),
                               hour=int(ts1.hour),
                               minute=int(ts1.minute),
                               second=int(ts1.second),
                               microsecond=int(ts1.microsecond))
        e: datetime = datetime(year=base_year + year_span,
                               month=int(ts2.month),
                               day=int(ts2.day),
                               hour=int(ts2.hour),
                               minute=int(ts2.minute),
                               second=int(ts2.second),
                               microsecond=int(ts2.microsecond))

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

        new_ts: np.ndarray = pd.to_datetime(mapped_timestamps).asi8

        try:

            pvgis_result: tuple = pvlib.iotools.get_pvgis_hourly(latitude=latitude,
                                                                 longitude=longitude,
                                                                 start=s,
                                                                 end=e,
                                                                 pvcalculation=True,
                                                                 peakpower=peak_power * 1e3,  # MW to kW
                                                                 )

            if len(pvgis_result) == 3:
                data: pd.DataFrame
                meta: dict
                inputs: dict
                data, meta, inputs = pvgis_result
            else:
                data, meta = pvgis_result

            if 'P' in data.columns:
                data_index: pd.DatetimeIndex = pd.DatetimeIndex(data.index)

                if data_index.tz is None:
                    normalized_data_index: pd.DatetimeIndex = data_index
                else:
                    normalized_data_index = data_index.tz_convert(None)

                data.index = normalized_data_index.asi8
                data.sort_index(inplace=True)

                interpolation_index: np.ndarray = np.union1d(data.index.values, new_ts)
                interpolated_data: pd.DataFrame = data.reindex(interpolation_index).interpolate(method='index')
                data2: pd.DataFrame = interpolated_data.ffill().bfill().reindex(new_ts)

                if bool(data2['P'].isna().any()):
                    error_msg(QtCore.QCoreApplication.translate(
                        "MainWindow",
                        "PVGIS returned data, but it could not be interpolated to the circuit time profile",
                    ))
                    return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))
                else:
                    pass

                return True, data2
            else:
                error_msg(QtCore.QCoreApplication.translate("MainWindow", "PVGIS did not return photovoltaic power data"))
                return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))

        except (requests.RequestException, KeyError, ValueError, TypeError) as err:
            error_msg(QtCore.QCoreApplication.translate(
                "MainWindow",
                "pvlib's http request failed :(\n{error_text}",
            ).format(error_text=str(err)))
            return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))

    else:
        if valid_latitude:
            if valid_longitude:
                if valid_peak_power:
                    error_msg(QtCore.QCoreApplication.translate(
                        "MainWindow",
                        "The time span of your profile is {year_span} year(s), Pvlib's span is 10 years maximum",
                    ).format(year_span=year_span))
                else:
                    error_msg(QtCore.QCoreApplication.translate(
                        "MainWindow",
                        "The photovoltaic peak power must be greater than zero",
                    ))
            else:
                error_msg(QtCore.QCoreApplication.translate(
                    "MainWindow",
                    "The longitude must be between -180 and 180 degrees",
                ))
        else:
            error_msg(QtCore.QCoreApplication.translate("MainWindow", "The latitude must be between -90 and 90 degrees"))

        return False, pd.DataFrame(data=dict(P=np.zeros(len(time_array))))


class SolarPvWizard(QtWidgets.QDialog):
    """
    New solar photovoltaic wizard window
    """

    def __init__(self, time_array: Sequence[Union[str, datetime, pd.Timestamp]],
                 peak_power: float,
                 latitude: float,
                 longitude: float,
                 gen_name: str = '',
                 bus_name: str = '',
                 title: str = 'solar photovoltaic wizard') -> None:
        """

        :param time_array: array of time values
        :param peak_power: generator peak power in MW
        :param latitude: latitude (float)
        :param longitude: longitude (float)
        :param title: Window title
        """
        QtWidgets.QDialog.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setObjectName("self")
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)

        self.is_accepted: bool = False
        self.selected_indices: List[int] = list()

        self.ui.label_gen.setText("Generator {}".format(gen_name))
        self.ui.label_bus.setText("Bus: {}".format(bus_name))
        self.ui.powerSpinBox.setValue(peak_power)
        self.ui.latitudeSpinBox.setValue(latitude)
        self.ui.longitudeSpinBox.setValue(longitude)

        self.time_array = time_array
        self.P = np.zeros(len(time_array))
        self.temperature: Union[np.ndarray, None] = None
        self.wind_speed: Union[np.ndarray, None] = None
        self.irradiation: Union[np.ndarray, None] = None

        # accept button
        self.ui.acceptButton.clicked.connect(self.accept_click)
        self.ui.generateButton.clicked.connect(self.generate_click)
        self.ui.plotButton.clicked.connect(self.plot)

        self.setWindowTitle(title)

        h = 260
        self.resize(h, int(0.8 * h))

        self.df: Union[pd.DataFrame, None] = None
        self.ok = False

        self.update_results()

    def update_results(self) -> None:
        """

        :return:
        """
        df: pd.DataFrame = pd.DataFrame(data=self.P, index=self.time_array, columns=['P (MW)'])
        mdl: PandasModel = PandasModel(data=df)
        self.ui.resultsTableView.setModel(mdl)

    def generate_click(self) -> None:
        """
        Accept and close
        """
        self.ok, self.df = get_pv_lib_weather_df(time_array=self.time_array,
                                                 latitude=self.ui.latitudeSpinBox.value(),
                                                 longitude=self.ui.longitudeSpinBox.value(),
                                                 peak_power=self.ui.powerSpinBox.value())
        if self.ok:
            self.P = self.df['P'].values / 1e6  # Power in MW
            self.temperature = get_weather_column(data=self.df, candidates=["T2m", "temp_air", "temperature"])
            self.wind_speed = get_weather_column(data=self.df, candidates=["WS10m", "wind_speed", "wind_speed_10m"])
            self.irradiation = get_weather_column(data=self.df, candidates=["G(i)", "poa_global", "GHI", "ghi"])
            self.update_results()

        else:
            self.temperature = None
            self.wind_speed = None
            self.irradiation = None
            self.ui.resultsTableView.setModel(None)

    def plot(self) -> None:

        df: pd.DataFrame = pd.DataFrame(data=self.P, index=self.time_array, columns=['P (MW)'])
        df.plot()
        plt.show()

    def accept_click(self) -> None:
        """
        Accept and close
        """

        self.is_accepted = self.ok
        self.accept()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    longitude = -110.9

    st = datetime(year=2018, month=1, day=1)
    direction = 1.0 if longitude > 0 else -1.0
    offset = direction * longitude * 24.0 / 360.0
    time_arr = pd.to_datetime([st + timedelta(hours=i + offset) for i in range(200)])

    window = SolarPvWizard(time_array=time_arr, peak_power=20, latitude=32.2, longitude=-110.9)
    window.resize(1.61 * 700.0, 600.0)  # golden ratio
    window.show()
    sys.exit(app.exec())
