# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.area import Area
from VeraGridEngine.Devices.Aggregation.country import Country
from VeraGridEngine.Devices.Aggregation.zone import Zone
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Substation.substation import Substation
from VeraGridEngine.Devices.Substation.voltage_level import VoltageLevel
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Compilers.Gslv.common import fill_profile
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec
from typing import (
    Dict,
    Union,
)

def convert_bus(elm: Bus, n_time: int,
                area_dict: Dict[Area, "pg.Area"],
                zone_dict: Dict[Zone, "pg.Zone"],
                substation_dict: Dict[Substation, "pg.Substation"],
                voltage_level_dict: Dict[VoltageLevel, "pg.VoltageLevel"],
                country_dict: Dict[Country, "pg.Country"],
                time_indices: IntVec,
                use_time_series: bool) -> "pg.Bus":
    """

    :param elm:
    :param n_time:
    :param area_dict:
    :param zone_dict:
    :param substation_dict:
    :param voltage_level_dict:
    :param country_dict:
    :param time_indices:
    :param use_time_series:
    :return:
    """
    bus = pg.Bus(nt=n_time,
                 name=str(elm.name),
                 idtag=elm.idtag,
                 code=str(elm.code),
                 Vnom=elm.Vnom,
                 vmin=elm.Vmin,
                 vmax=elm.Vmax,
                 angle_min=elm.angle_min,
                 angle_max=elm.angle_max,
                 # r_fault=elm.r_fault,
                 # x_fault=elm.x_fault,
                 active_default=elm.active,

                 is_slack=elm.is_slack,
                 is_dc=elm.is_dc,
                 is_internal=elm.internal,

                 area=area_dict.get(elm.area, None),
                 zone=zone_dict.get(elm.zone, None),
                 substation=substation_dict.get(elm.substation, None),
                 voltage_level=voltage_level_dict.get(elm.substation, None),
                 country=country_dict.get(elm.country, None),
                 latitude=elm.latitude,
                 longitude=elm.longitude,
                 Vm0=elm.Vm0,
                 Va0=elm.Va0,
                 )

    fill_profile(gslv_profile=bus.active,
                 gc_profile=elm.active_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.active)
    if use_time_series:
        fill_profile(gslv_profile=bus.Vm0,
                     gc_profile=elm.Vm0_prof,
                     use_time_series=use_time_series,
                     time_indices=time_indices,
                     n_time=n_time,
                     default_val=elm.Vm0)
        fill_profile(gslv_profile=bus.Va0,
                     gc_profile=elm.Va0_prof,
                     use_time_series=use_time_series,
                     time_indices=time_indices,
                     n_time=n_time,
                     default_val=elm.Va0)

    return bus

def add_buses(
        circuit: MultiCircuit,
        gslv_grid: "pg.MultiCircuit",
        area_dict: Dict[Area, "pg.Area"],
        zone_dict: Dict[Zone, "pg.Zone"],
        substation_dict: Dict[Substation, "pg.Substation"],
        voltage_level_dict: Dict[VoltageLevel, "pg.VoltageLevel"],
        country_dict: Dict[Country, "pg.Country"],
        use_time_series: bool,
        n_time: int = 1,
        time_indices: Union[IntVec, None] = None,
) -> Dict[str, "pg.Bus"]:
    """
    Convert the buses to GSLV buses
    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV circuit
    :param use_time_series: compile the time series from VeraGrid? otherwise, just the snapshot
    :param n_time: number of time steps
    :param time_indices: Array of time indices
    :param area_dict: Area object translation dictionary
    :param zone_dict: Zone object translation dictionary
    :param substation_dict: Substation object translation dictionary
    :param voltage_level_dict: Voltage level object translation dictionary
    :param country_dict: Country object translation dictionary
    :return: bus dictionary buses[uuid] -> Bus
    """

    if time_indices is not None:
        assert (len(time_indices) == n_time)

    if area_dict is None:
        area_dict = {elm: k for k, elm in enumerate(circuit.areas)}

    bus_dict: Dict[str, "pg.Bus"] = dict()

    for i, bus in enumerate(circuit.buses):
        elm = convert_bus(elm=bus, n_time=n_time,
                          area_dict=area_dict,
                          zone_dict=zone_dict,
                          substation_dict=substation_dict,
                          voltage_level_dict=voltage_level_dict,
                          country_dict=country_dict,
                          use_time_series=use_time_series,
                          time_indices=time_indices)

        gslv_grid.add_bus(elm)
        bus_dict[bus.idtag] = elm

    return bus_dict

