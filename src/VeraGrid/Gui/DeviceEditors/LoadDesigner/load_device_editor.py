# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import sys

from PySide6 import QtCore, QtGui, QtWidgets

from VeraGrid.Gui.DeviceEditors.LoadDesigner.load_designer import LoadDesigner
from VeraGrid.Gui.DeviceEditors.TemplateDeviceEditor.template_device_editor import TemplateDeviceEditor
from VeraGrid.Gui.messages import info_msg, warning_msg
from VeraGrid.Gui.profile_wizard_utils import fill_substation_weather_profiles
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class EmbeddedLoadDesignerWidget(LoadDesigner):
    """
    Load profile designer embedded as a child widget inside the load editor tab.
    """

    generation_updated = QtCore.Signal(bool)

    def __init__(self,
                 time_array,
                 active_power: float,
                 reactive_power: float,
                 latitude: float | None,
                 longitude: float | None,
                 load_name: str,
                 bus_name: str,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """
        Build the embedded load designer widget.

        :param time_array: Time profile sequence.
        :param active_power: Snapshot active power in MW.
        :param reactive_power: Snapshot reactive power in MVAr.
        :param latitude: Bus latitude.
        :param longitude: Bus longitude.
        :param load_name: Load name.
        :param bus_name: Bus name.
        :param parent: Qt parent widget.
        """
        LoadDesigner.__init__(self,
                              time_array=time_array,
                              active_power=active_power,
                              reactive_power=reactive_power,
                              latitude=latitude,
                              longitude=longitude,
                              load_name=load_name,
                              bus_name=bus_name,
                              parent=parent)

        self.setWindowFlags(QtCore.Qt.WindowType.Widget)
        self.setWindowTitle("")
        self.accept_button.hide()
        self.cancel_button.hide()
        self.generation_updated.emit(bool(self.is_generated))

    def process_by_peak(self) -> None:
        """
        Generate profiles from peak points and notify listeners.
        """
        LoadDesigner.process_by_peak(self)
        self.generation_updated.emit(bool(self.is_generated))

    def generate_from_components(self) -> None:
        """
        Generate profiles from component definitions and notify listeners.
        """
        LoadDesigner.generate_from_components(self)
        self.generation_updated.emit(bool(self.is_generated))


class LoadDeviceEditor(TemplateDeviceEditor):
    """
    Load editor that extends ``TemplateDeviceEditor`` with an embedded profile designer.
    """

    def __init__(self, api_object: Load, circuit: MultiCircuit | None = None) -> None:
        """
        Build the load editor.

        :param api_object: Load edited in place.
        :param circuit: Optional circuit context.
        """
        TemplateDeviceEditor.__init__(self, api_object=api_object, circuit=circuit)
        self.api_object: Load = api_object
        self.setWindowTitle("Load editor")

        self.load_designer_widget: EmbeddedLoadDesignerWidget | None = None
        self._build_load_designer_tab()

    def _build_load_designer_tab(self) -> None:
        """
        Build and configure the embedded load-designer tab.
        """
        self.load_designer_tab: QtWidgets.QWidget = QtWidgets.QWidget(self.tab_widget)
        self.load_designer_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self.load_designer_tab)
        self.load_designer_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self.load_designer_apply_button: QtWidgets.QPushButton = QtWidgets.QPushButton(
            "Accept",
            self.load_designer_tab,
        )
        self.load_designer_apply_button.setIcon(QtGui.QIcon(":/Icons/icons/accept.png"))
        self.load_designer_apply_button.setEnabled(False)

        if self.circuit is not None and self.circuit.has_time_series:
            if self.api_object.bus is not None:
                bus_name: str = self.api_object.bus.name
                latitude: float | None = self.api_object.bus.latitude
                longitude: float | None = self.api_object.bus.longitude
            else:
                bus_name = ""
                latitude = None
                longitude = None

            self.load_designer_widget = EmbeddedLoadDesignerWidget(
                time_array=self.circuit.time_profile,
                active_power=self.api_object.P,
                reactive_power=self.api_object.Q,
                latitude=latitude,
                longitude=longitude,
                load_name=self.api_object.name,
                bus_name=bus_name,
                parent=self.load_designer_tab,
            )
            self.load_designer_widget.generation_updated.connect(self._on_load_generation_updated)
            self.load_designer_layout.addWidget(self.load_designer_widget)
            self.load_designer_apply_button.clicked.connect(self._apply_designed_profiles)
            self.load_designer_apply_button.setEnabled(bool(self.load_designer_widget.is_generated))
        else:
            self.load_designer_widget = None
            self.load_designer_apply_button.setEnabled(False)
            missing_msg: QtWidgets.QLabel = QtWidgets.QLabel(
                "Load profile designer requires circuit time profiles.",
                self.load_designer_tab,
            )
            self.load_designer_layout.addWidget(missing_msg)

        self.load_designer_button_layout.addStretch()
        self.load_designer_button_layout.addWidget(self.load_designer_apply_button)
        self.load_designer_layout.addLayout(self.load_designer_button_layout)

        load_tab_index: int = self.tab_widget.addTab(self.load_designer_tab, "Load designer")
        self.tab_widget.setTabIcon(load_tab_index, QtGui.QIcon(":/Icons/icons/load_wizard.png"))

    def _on_load_generation_updated(self, is_generated: bool) -> None:
        """
        Enable or disable profile application according to generation status.

        :param is_generated: Profile generation status.
        """
        self.load_designer_apply_button.setEnabled(is_generated)

    def _apply_designed_profiles(self) -> None:
        """
        Apply generated load profiles and refresh base tabs.
        """
        if self.load_designer_widget is None:
            warning_msg("Load designer is not available", "Load editor")
        elif not bool(self.load_designer_widget.is_generated):
            warning_msg("Generate a profile before applying it", "Load editor")
        else:
            active_profile = self.load_designer_widget.P
            reactive_profile = self.load_designer_widget.Q
            expected_size: int = self.api_object.P_prof.size()

            if len(active_profile) == expected_size and len(reactive_profile) == self.api_object.Q_prof.size():
                self.api_object.P_prof.set(active_profile)
                self.api_object.Q_prof.set(reactive_profile)

                if self.api_object.bus is not None:
                    fill_substation_weather_profiles(bus=self.api_object.bus,
                                                     temperature=self.load_designer_widget.temperature,
                                                     wind_speed=self.load_designer_widget.wind_speed,
                                                     irradiation=None,
                                                     expected_size=expected_size)
                else:
                    pass

                self.properties_model.set_time_index(time_index=self._get_current_time_index())
                self.refresh_profile_table()
                self.show_info_toast("Load profile applied")
            else:
                warning_msg("Wrong load profile length", "Load editor")


LoadDeviceEditorDialog = LoadDeviceEditor


if __name__ == "__main__":
    qt_app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    # Build one minimal circuit context so profile tabs and the designer can be inspected.
    circuit_demo: MultiCircuit = MultiCircuit(name="Load device editor demo", Sbase=100.0, fbase=50.0)
    circuit_demo.create_profiles(steps=24 * 7, step_length=1, step_unit="h")
    bus_demo: Bus = Bus(name="Bus demo", Vnom=66.0, latitude=41.390205, longitude=2.154007)
    circuit_demo.add_bus(obj=bus_demo)

    load_demo: Load = Load(name="Load demo", P=20.0, Q=5.0)
    circuit_demo.add_load(bus=bus_demo, api_obj=load_demo)

    if load_demo.P_prof.size() > 0:
        load_demo.P_prof[0] = 18.0
        load_demo.Q_prof[0] = 4.5
    else:
        pass

    dialog_demo: LoadDeviceEditor = LoadDeviceEditor(api_object=load_demo, circuit=circuit_demo)
    dialog_demo.resize(1320, 860)
    dialog_demo.show()
    sys.exit(qt_app.exec())
