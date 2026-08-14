# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.branch_group import BranchGroup
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Compilers.Gslv.common import fill_profile
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec
from typing import (
    Dict,
    Union,
)


def convert_line(elm: Line,
                 n_time: int,
                 bus_dict: Dict[str, "pg.Bus"],
                 branch_groups_dict: Dict[BranchGroup, "pg.BranchGroup"],
                 use_time_series: bool, time_indices: IntVec | None = None,
                 add_three_phase_data: bool = False) -> "pg.Line":
    """
    Convert one VeraGrid line into one GSLV line.

    :param elm: VeraGrid line.
    :param n_time: Number of exported time steps.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param branch_groups_dict: Branch-group lookup.
    :param use_time_series: Whether the export is time-series based.
    :param time_indices: Optional time-series selection.
    :param add_three_phase_data: Export sequence parameters needed by three-phase studies.
    :return: GSLV line.
    """
    line_r0: float
    line_x0: float
    line_b0: float
    line_r2: float
    line_x2: float
    line_b2: float

    if add_three_phase_data:
        line_r0 = float(elm.R0)
        line_x0 = float(elm.X0)
        line_b0 = float(elm.B0)
        line_r2 = float(elm.R2)
        line_x2 = float(elm.X2)
        line_b2 = float(elm.B2)
    else:
        line_r0 = 1e-20
        line_x0 = 1e-20
        line_b0 = 1e-20
        line_r2 = 1e-20
        line_x2 = 1e-20
        line_b2 = 1e-20

    lne = pg.Line(
        idtag=elm.idtag,
        code=str(elm.code),
        name=elm.name,
        bus_from=bus_dict[elm.bus_from.idtag],
        bus_to=bus_dict[elm.bus_to.idtag],
        nt=n_time,
        length=elm.length,
        rate=elm.rate if elm.rate > 0 else 9999,
        active=elm.active,
        r=elm.R,
        x=elm.X,
        b=elm.B,
        monitor_loading=elm.monitor_loading,
        r0=line_r0,
        x0=line_x0,
        b0=line_b0,
        r2=line_r2,
        x2=line_x2,
        b2=line_b2,
    )

    lne.group = branch_groups_dict.get(elm.group, None)

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


def add_lines(circuit: MultiCircuit,
              gslv_grid: "pg.MultiCircuit",
              bus_dict: Dict[str, "pg.Bus"],
              branch_groups_dict: Dict[BranchGroup, "pg.BranchGroup"],
              time_series: bool,
              n_time: int = 1,
              time_indices: Union[IntVec, None] = None,
              add_three_phase_data: bool = False) -> None:
    """

    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV circuit
    :param time_series: compile the time series from VeraGrid? otherwise just the snapshot
    :param bus_dict: dictionary of bus id to GSLV bus object
    :param branch_groups_dict: dictionary of converted branch groups
    :param n_time: number of time steps
    :param time_indices: Array of time indices
    :param add_three_phase_data: Export sequence parameters needed by three-phase studies.
    :return: None.
    """

    # Compile the lines
    for i, elm in enumerate(circuit.lines):
        lne = convert_line(elm=elm,
                           bus_dict=bus_dict,
                           branch_groups_dict=branch_groups_dict,
                           n_time=n_time,
                           use_time_series=time_series,
                           time_indices=time_indices,
                           add_three_phase_data=add_three_phase_data)
        gslv_grid.add_line(lne)
