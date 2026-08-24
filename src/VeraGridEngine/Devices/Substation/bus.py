# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Tuple, Union
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from VeraGridEngine.enumerations import BusMode, DeviceType, BusGraphicType, BuildStatus, PrpCat

from VeraGridEngine.Devices.Aggregation import Area, Zone, Country, Community, Region, Municipality
from VeraGridEngine.Devices.Substation.substation import Substation
from VeraGridEngine.Devices.Substation.busbar import BusBar
from VeraGridEngine.Devices.Substation.voltage_level import VoltageLevel
from VeraGridEngine.Devices.Profiles import ProfileBool, ProfileFloat
from VeraGridEngine.Devices.Parents.editable_device import get_at, GCProp
from VeraGridEngine.Devices.Parents.dynamic_bus_parent import DynamicBusDevice
from VeraGridEngine.basic_structures import BoolVec


class Bus(DynamicBusDevice):
    __slots__ = (
        '_active',
        '_active_prof',
        'color',
        '_Vnom',
        '_Vmin',
        '_Vm_cost',
        '_Vmax',
        '_Vm0',
        '_Va0',
        '_Vm0_prof',
        '_Va0_prof',
        '_Vmin_prof',
        '_Vmax_prof',
        '_angle_min',
        '_angle_max',
        '_angle_cost',
        'Qmin_sum',
        'Qmax_sum',

        'country',
        'area',
        'zone',
        'substation',
        '_voltage_level',
        '_bus_type',
        '_is_slack',
        '_is_slack_prof',
        '_is_dc',
        '_x',
        '_y',
        '_h',
        '_w',
        '_longitude',
        '_latitude',
        '_is_grounded',
        'graphic_type',
        '_bus_bar'
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='active',
            units='',
            tpe=bool,
            definition='Is the bus active? used to disable the bus.',
            profile_name='active_prof',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='is_slack',
            units='',
            tpe=bool,
            definition='Force the bus to be of slack type.',
            profile_name='is_slack_prof',
            cat=[PrpCat.TP, PrpCat.PF, PrpCat.PF3],
        ),
        GCProp(
            prop_name='is_dc',
            units='',
            tpe=bool,
            definition='Is this bus of DC type?.',
            profile_name='',
            cat=[PrpCat.TP, PrpCat.PF],
        ),
        GCProp(
            prop_name='is_grounded',
            units='',
            tpe=bool,
            definition='Is this bus connected to ground?.',
            profile_name='',
            cat=[PrpCat.TP, PrpCat.PF],
        ),
        GCProp(
            prop_name='graphic_type',
            units='',
            tpe=BusGraphicType,
            definition='Graphic to use in the schematic.',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='Vnom',
            units='kV',
            tpe=float,
            definition='Nominal line voltage of the bus.',
            profile_name='',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Vm0',
            units='p.u.',
            tpe=float,
            definition='Voltage module guess.',
            profile_name='Vm0_prof',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Va0',
            units='rad.',
            tpe=float,
            definition='Voltage angle guess.',
            profile_name='Va0_prof',
            cat=[PrpCat.PF],
        ),
        GCProp(
            prop_name='Vmin',
            units='p.u.',
            tpe=float,
            definition='Lower range of allowed voltage module.',
            profile_name='Vmin_prof',
            cat=[PrpCat.OPF],
        ),
        GCProp(
            prop_name='Vmax',
            units='p.u.',
            tpe=float,
            definition='Higher range of allowed voltage module.',
            profile_name='Vmax_prof',
            cat=[PrpCat.OPF],
        ),
        GCProp(
            prop_name='Vm_cost',
            units='e/unit',
            tpe=float,
            definition='Cost of over and under voltages',
            old_names=['voltage_module_cost'],
            cat=[PrpCat.OPF],
        ),
        GCProp(
            prop_name='angle_min',
            units='rad.',
            tpe=float,
            definition='Lower range of allowed voltage angle.',
            profile_name='',
            cat=[PrpCat.OPF],
        ),
        GCProp(
            prop_name='angle_max',
            units='rad.',
            tpe=float,
            definition='Higher range of allowed voltage angle.',
            profile_name='',
            cat=[PrpCat.OPF],
        ),
        GCProp(
            prop_name='angle_cost',
            units='e/unit',
            tpe=float,
            definition='Cost of over and under angles',
            old_names=['voltage_angle_cost'],
            cat=[PrpCat.OPF],
        ),
        GCProp(
            prop_name='x',
            units='px',
            tpe=float,
            definition='x position in pixels.',
            profile_name='',
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='y',
            units='px',
            tpe=float,
            definition='y position in pixels.',
            profile_name='',
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='h',
            units='px',
            tpe=float,
            definition='height of the bus in pixels.',
            profile_name='',
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='w',
            units='px',
            tpe=float,
            definition='Width of the bus in pixels.',
            profile_name='',
            editable=False,
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='country',
            units='',
            tpe=DeviceType.CountryDevice,
            definition='Country of the bus',
            profile_name='',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='area',
            units='',
            tpe=DeviceType.AreaDevice,
            definition='Area of the bus',
            profile_name='',
            cat=[PrpCat.TP, PrpCat.NTC],
        ),
        GCProp(
            prop_name='zone',
            units='',
            tpe=DeviceType.ZoneDevice,
            definition='Zone of the bus',
            profile_name='',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='substation',
            units='',
            tpe=DeviceType.SubstationDevice,
            definition='Substation of the bus.',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='voltage_level',
            units='',
            tpe=DeviceType.VoltageLevelDevice,
            definition='Voltage level of the bus.',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='bus_bar',
            units='',
            tpe=DeviceType.BusBarDevice,
            definition='Busbar associated to the bus.',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='longitude',
            units='deg',
            tpe=float,
            definition='longitude of the bus.',
            profile_name='',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='latitude',
            units='deg',
            tpe=float,
            definition='latitude of the bus.',
            profile_name='',
            cat=[PrpCat.TP],
        ),
        GCProp(
            prop_name='color',
            units='',
            tpe=str,
            definition='Color to paint the element in the diagram',
            is_color=True,
            cat=[PrpCat.TP],
        ),
    )

    def __init__(self, name="Bus",
                 idtag=None,
                 code='',
                 Vnom=10,
                 vmin=0.9,
                 vmax=1.1,
                 angle_min=-6.28,
                 angle_max=6.28,
                 xpos=0,
                 ypos=0,
                 height=0,
                 width=0,
                 active=True,
                 is_slack=False,
                 is_dc=False,
                 is_internal=False,
                 is_grounded=False,
                 area: Area = None,
                 zone: Zone = None,
                 substation: Substation = None,
                 voltage_level: VoltageLevel = None,
                 country: Country = None,
                 longitude=0.0,
                 latitude=0.0,
                 Vm0=1,
                 Va0=0,
                 graphic_type: BusGraphicType = BusGraphicType.BusBar,
                 bus_bar: BusBar | None = None,
                 build_status: BuildStatus = BuildStatus.Commissioned,
                 color: str | None = None):
        """
        The Bus object is the container of all the possible devices that can be attached to
        a bus bar or Substation. Such objects can be loads, voltage controlled generators,
        static generators, batteries, shunt elements, etc.
        :param name: Name of the bus
        :param idtag: Unique identifier, if empty or None, a random one is generated
        :param code: Compatibility id with legacy systems
        :param Vnom: Nominal voltage in kV
        :param vmin: Minimum per unit voltage (p.u.)
        :param vmax: Maximum per unit voltage (p.u.)
        :param angle_min: Minimum voltage angle (rad)
        :param angle_max: Maximum voltage angle (rad)

        :param xpos: X position in pixels (GUI only)
        :param ypos: Y position in pixels (GUI only)
        :param height: Height of the graphic object (GUI only)
        :param width: Width of the graphic object (GUI only)
        :param active: Is the bus active?
        :param is_slack: Is this bus a slack bus?
        :param is_dc: Is this bus a DC bus?
        :param is_internal: Is this bus an internal bus?
                            (i.e. the central bus on a 3W transformer, or the bus of a FluidNode)
        :param is_grounded: Is this bus grounded, i.e., at V=0? Sometimes used for DC buses connected to a VSC
        :param area: Area object
        :param zone: Zone object
        :param substation: Substation object
        :param country: Country object
        :param longitude: longitude (deg)
        :param latitude: latitude (deg)
        :param Vm0: initial solution for the voltage module (p.u.)
        :param Va0: initial solution for the voltage angle (rad)
        :param graphic_type: BusGraphicType to represent the bus in the schematic
        :param color: Bus color mark
        """

        DynamicBusDevice.__init__(self,
                                  name=name,
                                  idtag=idtag,
                                  code=code,
                                  device_type=DeviceType.BusDevice,
                                  build_status=build_status)

        self._active = bool(active)
        self._active_prof = ProfileBool(default_value=self._active)

        # Nominal voltage (kV)
        self._Vnom = float(Vnom)

        # minimum voltage limit
        self._Vmin = float(vmin)
        self._Vmin_prof = ProfileFloat(default_value=self._Vmin)

        self._Vm_cost = 1.0

        # maximum voltage limit
        self._Vmax = float(vmax)
        self._Vmax_prof = ProfileFloat(default_value=self._Vmax)

        self._Vm0 = float(Vm0)
        self._Vm0_prof = ProfileFloat(default_value=self._Vm0)

        self._Va0 = float(Va0)
        self._Va0_prof = ProfileFloat(default_value=self._Va0)

        self._angle_min = float(angle_min)

        self._angle_max = float(angle_max)

        self._angle_cost = 0

        # summation of lower reactive power limits connected
        self.Qmin_sum = 0

        # summation of upper reactive power limits connected
        self.Qmax_sum = 0

        self.country: Country | None = country

        self.area: Area | None = area

        self.zone: Zone | None = zone

        self.substation: Substation | None = substation

        self._voltage_level: VoltageLevel | None = voltage_level

        self._bus_bar: BusBar | None = bus_bar

        if is_internal:
            self.graphic_type: BusGraphicType = BusGraphicType.Internal
        else:
            self.graphic_type: BusGraphicType = graphic_type

        if voltage_level is not None:

            if voltage_level.Vnom != Vnom:
                print(f"{self.idtag} {self.name} "
                      f"The nominal voltage of the voltage level is different from bus nominal voltage!"
                      f"{voltage_level.Vnom} != {Vnom}")

            if voltage_level.substation is not None:
                if substation is None:
                    self.substation = voltage_level.substation
                else:
                    if substation != voltage_level.substation:
                        print(f"{self.idtag} {self.name} "
                              f"The substation from the voltage level is different from bus substation!")

        # Bus type
        self._bus_type = BusMode.PQ_tpe

        # Flag to determine if the bus is a slack bus or not
        self._is_slack = bool(is_slack)
        self._is_slack_prof = ProfileBool(default_value=self._is_slack)

        # determined if this bus is an AC or DC bus
        self._is_dc = bool(is_dc)

        # determine if the bus is solidly grounded
        self._is_grounded = bool(is_grounded)

        # position and dimensions
        self._x = float(xpos)
        self._y = float(ypos)
        self._h = float(height)
        self._w = float(width)
        self._longitude = float(longitude)
        self._latitude = float(latitude)

        self.color = color if color is not None else "#000000"

    @property
    def active_prof(self) -> ProfileBool:
        """
        Cost profile
        :return: Profile
        """
        return self._active_prof

    @active_prof.setter
    def active_prof(self, val: Union[ProfileBool, np.ndarray]):
        if isinstance(val, ProfileBool):
            self._active_prof = val
        elif isinstance(val, np.ndarray):
            self._active_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a active_prof')

    def get_active_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.active, self.active_prof, t)

    @property
    def Vmin_prof(self) -> ProfileFloat:
        """
        Pmin profile
        :return: Profile
        """
        return self._Vmin_prof

    @Vmin_prof.setter
    def Vmin_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Vmin_prof = val
        elif isinstance(val, np.ndarray):
            self._Vmin_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Vmin_prof')

    def get_Vmin_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Vmin, self.Vmin_prof, t)

    @property
    def Vmax_prof(self) -> ProfileFloat:
        """
        Pmin profile
        :return: Profile
        """
        return self._Vmax_prof

    @Vmax_prof.setter
    def Vmax_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Vmax_prof = val
        elif isinstance(val, np.ndarray):
            self._Vmax_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Vmax_prof')

    def get_Vmax_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Vmax, self.Vmax_prof, t)

    @property
    def Vm0_prof(self) -> ProfileFloat:
        """
        Vm0 profile
        :return: Profile
        """
        return self._Vm0_prof

    @Vm0_prof.setter
    def Vm0_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Vm0_prof = val
        elif isinstance(val, np.ndarray):
            self._Vm0_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Vm0_prof')

    def get_Vm0_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Vm0, self.Vm0_prof, t)

    @property
    def Va0_prof(self) -> ProfileFloat:
        """
        Va0 profile
        :return: Profile
        """
        return self._Va0_prof

    @Va0_prof.setter
    def Va0_prof(self, val: Union[ProfileFloat, np.ndarray]):
        if isinstance(val, ProfileFloat):
            self._Va0_prof = val
        elif isinstance(val, np.ndarray):
            self._Va0_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a Va0_prof')

    def get_Va0_at(self, t: int | None) -> float:
        """
        :param t:
        :return:
        """
        return get_at(self.Va0, self.Va0_prof, t)

    @property
    def voltage_level(self) -> Union[VoltageLevel, None]:
        """
        voltage_level getter
        :return: Union[VoltageLevel, None]
        """
        return self._voltage_level

    @voltage_level.setter
    def voltage_level(self, val: Union[VoltageLevel, None]):
        """
        voltage_level getter
        :param val: value
        """
        if isinstance(val, Union[VoltageLevel, None]):
            self._voltage_level = val

            if val is not None:
                if val.substation is not None and self.substation is None:
                    self.substation = val.substation
        else:
            raise Exception(f'{type(val)} not supported to be set into a '
                            f'voltage_level of type Union[VoltageLevel, None]')

    def determine_snapshot_bus_type(self) -> BusMode:
        """
        Infer the bus type from the devices attached to it
        @return: BusMode
        """
        if not self.active:
            return BusMode.PQ_tpe

        if self.is_slack:
            # if it is set as slack, set the bus as slack and exit
            self._bus_type = BusMode.Slack_tpe
            return BusMode.Slack_tpe

        return BusMode.PQ_tpe

    @property
    def bus_type(self) -> BusMode:
        return self._bus_type

    @bus_type.setter
    def bus_type(self, val: BusMode):
        if isinstance(val, BusMode):
            self._bus_type = val
        else:
            raise Exception(f"Invalid bus_type value={val}")

    def get_country(self) -> Country | None:
        """
        Get the country associated to this bus.

        The bus-level reference has priority because it is the most specific
        assignment for this object. If it is not available, the method falls
        back to the substation hierarchy.

        :return: Country object or ``None``
        """
        if self.country is not None:
            return self.country
        else:
            substation: Substation | None = self.get_substation()
            if substation is not None:
                return substation.country
            else:
                return None

    def get_area(self) -> Area | None:
        """
        Get the area associated to this bus.

        The bus-level reference has priority because it is the most specific
        assignment for this object. If it is not available, the method falls
        back to the substation hierarchy.

        :return: Area object or ``None``
        """
        if self.area is not None:
            return self.area
        else:
            substation: Substation | None = self.get_substation()
            if substation is not None:
                return substation.area
            else:
                return None

    def get_zone(self) -> Zone | None:
        """
        Get the zone associated to this bus.

        The bus-level reference has priority because it is the most specific
        assignment for this object. If it is not available, the method falls
        back to the substation hierarchy.

        :return: Zone object or ``None``
        """
        if self.zone is not None:
            return self.zone
        else:
            substation: Substation | None = self.get_substation()
            if substation is not None:
                return substation.zone
            else:
                return None

    def get_substation(self) -> Substation | None:
        """
        Get the substation associated to this bus.

        The bus-level reference has priority because it is the direct
        association stored by the bus. If it is not available, the method
        falls back to the voltage-level hierarchy.

        :return: Substation object or ``None``
        """
        if self.substation is not None:
            return self.substation
        else:
            if self.voltage_level is not None:
                return self.voltage_level.substation
            else:
                return None

    def get_voltage_level(self) -> VoltageLevel | None:
        """
        Get the voltage level associated to this bus.

        The bus stores the voltage-level reference directly, so there is no
        alternative hierarchy to inspect.

        :return: VoltageLevel object or ``None``
        """
        if self.voltage_level is not None:
            return self.voltage_level
        else:
            return None

    def get_community(self) -> Community | None:
        """
        Get the community associated to this bus.

        The value is obtained through the substation hierarchy because the bus
        does not store a direct community reference.

        :return: Community object or ``None``
        """
        substation: Substation | None = self.get_substation()
        if substation is not None:
            return substation.community
        else:
            return None

    def get_region(self) -> Region | None:
        """
        Get the region associated to this bus.

        The value is obtained through the substation hierarchy because the bus
        does not store a direct region reference.

        :return: Region object or ``None``
        """
        substation: Substation | None = self.get_substation()
        if substation is not None:
            return substation.region
        else:
            return None

    def get_municipality(self) -> Municipality | None:
        """
        Get the municipality associated to this bus.

        The value is obtained through the substation hierarchy because the bus
        does not store a direct municipality reference.

        :return: Municipality object or ``None``
        """
        substation: Substation | None = self.get_substation()
        if substation is not None:
            return substation.municipality
        else:
            return None

    def get_voltage_guess_at(self, t_idx: int | None, use_stored_guess=False) -> complex:
        """
        Determine the voltage initial guess
        :param t_idx: time step
        :param use_stored_guess: use the stored guess or get one from the devices
        :return: voltage guess
        """
        if use_stored_guess:
            return self.get_Vm0_at(t_idx) * np.exp(1j * self.get_Va0_at(t_idx))
        else:
            return complex(1, 0)

    def plot_profiles(self, time_profile, ax_load=None, ax_voltage=None, time_series_driver=None, my_index=0):
        """
        plot the profiles of this bus
        :param time_profile: Master profile of time steps (stored in the MultiCircuit)
        :param time_series_driver: time series driver
        :param ax_load: Load axis, if not provided one will be created
        :param ax_voltage: Voltage axis, if not provided one will be created
        :param my_index: index of this object in the time series results
        """

        if ax_load is None:
            fig = plt.figure(figsize=(12, 8))
            fig.suptitle(self.name, fontsize=20)
            if time_series_driver is not None:
                # 2 plots: load + voltage
                ax_load = fig.add_subplot(211)
                ax_voltage = fig.add_subplot(212, sharex=ax_load)
            else:
                # only 1 plot: load
                ax_load = fig.add_subplot(111)
                ax_voltage = None
            show_fig = True
        else:
            show_fig = False

        if time_series_driver is not None:
            v = np.abs(time_series_driver.results.voltage[:, my_index])
            p = time_series_driver.results.S[:, my_index].real
            p_load = p.copy()
            p_load[p_load > 0] = 0
            p_gen = p.copy()
            p_gen[p_gen < 0] = 0
            P_data = {"Load": p_load, "Gen": p_gen}
            t = time_series_driver.results.time_array
            pd.DataFrame(data=v, index=t, columns=['Voltage (p.u.)']).plot(ax=ax_voltage)
            pd.DataFrame(data=P_data, index=t).plot(ax=ax_load)

            ax_load.set_ylabel('Power [MW]', fontsize=11)
            ax_load.legend()
        else:
            pass

        if ax_voltage is not None:
            ax_voltage.set_ylabel('Voltage module [p.u.]', fontsize=11)
            ax_voltage.legend()

        if show_fig:
            plt.show()

    def get_coordinates(self) -> Tuple[float, float]:
        """
        Get tuple of the bus coordinates (longitude, latitude)
        """
        return self.longitude, self.latitude

    def try_to_find_coordinates(self):
        """
        Try to find the bus coordinates
        """
        lon, lat = self.longitude, self.latitude

        if self.substation is not None:
            if lon == 0.0:
                lon = self.substation.longitude

        if self.substation is not None:
            if lat == 0.0:
                lat = self.substation.latitude

        return lon, lat

    @property
    def internal(self) -> bool:
        """
        Is the bus internal?
        """
        return self.graphic_type == BusGraphicType.Internal

    @internal.setter
    def internal(self, val: bool):
        if val:
            self.graphic_type = BusGraphicType.Internal
        else:
            pass

    @property
    def bus_bar(self) -> BusBar | None:
        """
        Get the BusBar
        """
        return self._bus_bar

    @bus_bar.setter
    def bus_bar(self, val: BusBar):
        if isinstance(val, BusBar) or val is None:
            self._bus_bar = val
        else:
            raise ValueError("The value must be a BusBar")

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def active(self) -> bool:
        """
        Get ``active``.

        :return: bool
        """
        return self._active

    @active.setter
    def active(self, val: bool) -> None:
        """
        Set ``active``.

        :param val: Value to assign.
        :return: None
        """
        self._active = bool(val)

    @property
    def is_slack(self) -> bool:
        """
        Get ``is_slack``.

        :return: bool
        """
        return self._is_slack

    @is_slack.setter
    def is_slack(self, val: bool) -> None:
        """
        Set ``is_slack``.

        :param val: Value to assign.
        :return: None
        """
        self._is_slack = bool(val)

        if self.auto_update_enabled:
            # This is to ease out the difficulty imposed by being able to update the slack
            self.is_slack_prof.fill(self.is_slack)

    @property
    def is_slack_prof(self) -> ProfileBool:
        """
        Get ``is_slack``.

        :return: bool
        """
        return self._is_slack_prof

    @is_slack_prof.setter
    def is_slack_prof(self, val: ProfileBool | BoolVec) -> None:
        """
        Set ``is_slack``.

        :param val: Value to assign.
        :return: None
        """
        if isinstance(val, ProfileBool):
            self._is_slack_prof = val
        elif isinstance(val, np.ndarray):
            self._is_slack_prof.set(arr=val)
        else:
            raise Exception(str(type(val)) + 'not supported to be set into a active_prof')

    def get_is_slack_at(self, t: int | None) -> bool:
        """
        :param t:
        :return:
        """
        return get_at(self.is_slack, self.is_slack_prof, t)

    def set_is_slack_at(self, t: int | None, val: bool):

        if t is None:
            self.is_slack = val
        else:
            self.is_slack_prof[t] = val

    @property
    def is_dc(self) -> bool:
        """
        Get ``is_dc``.

        :return: bool
        """
        return self._is_dc

    @is_dc.setter
    def is_dc(self, val: bool) -> None:
        """
        Set ``is_dc``.

        :param val: Value to assign.
        :return: None
        """
        self._is_dc = bool(val)

    @property
    def Vnom(self) -> float:
        """
        Get ``Vnom``.

        :return: float
        """
        return self._Vnom

    @Vnom.setter
    def Vnom(self, val: float) -> None:
        """
        Set ``Vnom``.

        :param val: Value to assign.
        :return: None
        """
        self._Vnom = float(val)

    @property
    def Vm0(self) -> float:
        """
        Get ``Vm0``.

        :return: float
        """
        return self._Vm0

    @Vm0.setter
    def Vm0(self, val: float) -> None:
        """
        Set ``Vm0``.

        :param val: Value to assign.
        :return: None
        """
        self._Vm0 = float(val)

    @property
    def Va0(self) -> float:
        """
        Get ``Va0``.

        :return: float
        """
        return self._Va0

    @Va0.setter
    def Va0(self, val: float) -> None:
        """
        Set ``Va0``.

        :param val: Value to assign.
        :return: None
        """
        self._Va0 = float(val)

    @property
    def Vmin(self) -> float:
        """
        Get ``Vmin``.

        :return: float
        """
        return self._Vmin

    @Vmin.setter
    def Vmin(self, val: float) -> None:
        """
        Set ``Vmin``.

        :param val: Value to assign.
        :return: None
        """
        self._Vmin = float(val)

    @property
    def Vmax(self) -> float:
        """
        Get ``Vmax``.

        :return: float
        """
        return self._Vmax

    @Vmax.setter
    def Vmax(self, val: float) -> None:
        """
        Set ``Vmax``.

        :param val: Value to assign.
        :return: None
        """
        self._Vmax = float(val)

    @property
    def Vm_cost(self) -> float:
        """
        Get ``Vm_cost``.

        :return: float
        """
        return self._Vm_cost

    @Vm_cost.setter
    def Vm_cost(self, val: float) -> None:
        """
        Set ``Vm_cost``.

        :param val: Value to assign.
        :return: None
        """
        self._Vm_cost = float(val)

    @property
    def angle_min(self) -> float:
        """
        Get ``angle_min``.

        :return: float
        """
        return self._angle_min

    @angle_min.setter
    def angle_min(self, val: float) -> None:
        """
        Set ``angle_min``.

        :param val: Value to assign.
        :return: None
        """
        self._angle_min = float(val)

    @property
    def angle_max(self) -> float:
        """
        Get ``angle_max``.

        :return: float
        """
        return self._angle_max

    @angle_max.setter
    def angle_max(self, val: float) -> None:
        """
        Set ``angle_max``.

        :param val: Value to assign.
        :return: None
        """
        self._angle_max = float(val)

    @property
    def angle_cost(self) -> float:
        """
        Get ``angle_cost``.

        :return: float
        """
        return self._angle_cost

    @angle_cost.setter
    def angle_cost(self, val: float) -> None:
        """
        Set ``angle_cost``.

        :param val: Value to assign.
        :return: None
        """
        self._angle_cost = float(val)

    @property
    def x(self) -> float:
        """
        Get ``x``.

        :return: float
        """
        return self._x

    @x.setter
    def x(self, val: float) -> None:
        """
        Set ``x``.

        :param val: Value to assign.
        :return: None
        """
        self._x = float(val)

    @property
    def y(self) -> float:
        """
        Get ``y``.

        :return: float
        """
        return self._y

    @y.setter
    def y(self, val: float) -> None:
        """
        Set ``y``.

        :param val: Value to assign.
        :return: None
        """
        self._y = float(val)

    @property
    def h(self) -> float:
        """
        Get ``h``.

        :return: float
        """
        return self._h

    @h.setter
    def h(self, val: float) -> None:
        """
        Set ``h``.

        :param val: Value to assign.
        :return: None
        """
        self._h = float(val)

    @property
    def w(self) -> float:
        """
        Get ``w``.

        :return: float
        """
        return self._w

    @w.setter
    def w(self, val: float) -> None:
        """
        Set ``w``.

        :param val: Value to assign.
        :return: None
        """
        self._w = float(val)

    @property
    def longitude(self) -> float:
        """
        Get ``longitude``.

        :return: float
        """
        return self._longitude

    @longitude.setter
    def longitude(self, val: float) -> None:
        """
        Set ``longitude``.

        :param val: Value to assign.
        :return: None
        """
        self._longitude = float(val)

    @property
    def latitude(self) -> float:
        """
        Get ``latitude``.

        :return: float
        """
        return self._latitude

    @latitude.setter
    def latitude(self, val: float) -> None:
        """
        Set ``latitude``.

        :param val: Value to assign.
        :return: None
        """
        self._latitude = float(val)

    @property
    def is_grounded(self) -> bool:
        """
        Get ``is_grounded``.

        :return: bool
        """
        return self._is_grounded

    @is_grounded.setter
    def is_grounded(self, val: bool) -> None:
        """
        Set ``is_grounded``.

        :param val: Value to assign.
        :return: None
        """
        self._is_grounded = bool(val)
