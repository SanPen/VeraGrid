# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Substation.substation import Substation
from VeraGridEngine.Devices.Branches.dc_line import DcLine
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Compilers.Gslv.common import fill_profile
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec
from typing import (
    Dict,
    Union,
)


def convert_dc_line(elm: DcLine, bus_dict: Dict[str, "pg.Bus"], n_time: int,
                    use_time_series: bool, time_indices: IntVec | None) -> "pg.DcLine":
    """

    :param elm:
    :param bus_dict:
    :param n_time:
    :param use_time_series:
    :param time_indices:
    :return:
    """
    lne = pg.DcLine(
        idtag=elm.idtag,
        code=str(elm.code),
        name=elm.name,
        bus_from=bus_dict[elm.bus_from.idtag],
        bus_to=bus_dict[elm.bus_to.idtag],
        nt=n_time,
        length=elm.length,
        rate=elm.rate if elm.rate > 0 else 9999,
        active=elm.active,
        r=float(elm.R),
        monitor_loading=elm.monitor_loading,
    )

    fill_profile(gslv_profile=lne.active,
                 gc_profile=elm.active_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.active)

    fill_profile(gslv_profile=lne.rate,
                 gc_profile=elm.rate_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.rate)

    fill_profile(gslv_profile=lne.contingency_factor,
                 gc_profile=elm.contingency_factor_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.contingency_factor)

    fill_profile(gslv_profile=lne.cost,
                 gc_profile=elm.Cost_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.Cost)

    return lne


def add_dc_lines(circuit: MultiCircuit,
                 gslv_grid: "pg.MultiCircuit",
                 bus_dict: Dict[str, "pg.Bus"],
                 time_series: bool,
                 n_time: int = 1,
                 time_indices: Union[IntVec, None] = None):
    """

    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV circuit
    :param time_series: compile the time series from VeraGrid? otherwise just the snapshot
    :param bus_dict: dictionary of bus id to GSLV bus object
    :param n_time: number of time steps
    :param time_indices: Array of time indices
    """
    # Compile the lines
    for i, elm in enumerate(circuit.dc_lines):
        lne = convert_dc_line(elm=elm, bus_dict=bus_dict, n_time=n_time,
                              use_time_series=time_series, time_indices=time_indices)
        gslv_grid.add_dc_line(lne)
