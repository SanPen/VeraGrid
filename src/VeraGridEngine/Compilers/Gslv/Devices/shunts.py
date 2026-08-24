# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict

from VeraGridEngine.Compilers.Gslv.activation import build_status_dict, pg
from VeraGridEngine.Compilers.Gslv.common import (
    apply_three_phase_shunt_data,
    fill_profile,
    get_single_three_phase_snapshot_index,
    set_injection_associations,
)
from VeraGridEngine.Devices.Aggregation.facility import Facility
from VeraGridEngine.Devices.Associations.technology import Technology
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec


def convert_shunt(elm: Shunt,
                  bus_dict: Dict[str, "pg.Bus"],
                  facility_dict: Dict[Facility, "pg.Facility"],
                  technology_dict: Dict[Technology, "pg.Technology"],
                  n_time: int,
                  use_time_series: bool,
                  time_indices: IntVec | None = None,
                  add_three_phase_data: bool = False) -> "pg.Shunt":
    """
    Convert one VeraGrid shunt into one GSLV shunt.

    :param elm: VeraGrid shunt.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param facility_dict: VeraGrid-to-GSLV facility lookup.
    :param technology_dict: VeraGrid-to-GSLV technology lookup.
    :param n_time: Number of exported time steps.
    :param use_time_series: Whether the export is time-series based.
    :param time_indices: Optional time-series selection.
    :param add_three_phase_data: Export explicit three-phase fields when available.
    :return: GSLV shunt.
    """
    sh = pg.Shunt(
        nt=n_time,
        bus=None if elm.bus is None else bus_dict[elm.bus.idtag],
        name=elm.name,
        idtag=elm.idtag,
        code=str(elm.code),
        G=elm.G,
        B=elm.B,
        build_status=build_status_dict[elm.build_status],
    )
    set_injection_associations(
        gslv_elm=sh,
        elm=elm,
        facility_dict=facility_dict,
        technology_dict=technology_dict,
    )

    fill_profile(sh.active, elm.active_prof, use_time_series, time_indices, n_time, elm.active)
    fill_profile(sh.G, elm.G_prof, use_time_series, time_indices, n_time, elm.G)
    fill_profile(sh.B, elm.B_prof, use_time_series, time_indices, n_time, elm.B)
    fill_profile(sh.cost, elm.Cost_prof, use_time_series, time_indices, n_time, elm.Cost)

    if add_three_phase_data:
        snapshot_time_index: int | None = get_single_three_phase_snapshot_index(
            use_time_series=use_time_series,
            time_indices=time_indices,
            n_time=n_time,
        )
        apply_three_phase_shunt_data(gslv_shunt=sh, elm=elm, time_index=snapshot_time_index)
    else:
        pass

    return sh


def add_shunts(circuit: MultiCircuit,
               gslv_grid: "pg.MultiCircuit",
               bus_dict: Dict[str, "pg.Bus"],
               facility_dict: Dict[Facility, "pg.Facility"],
               technology_dict: Dict[Technology, "pg.Technology"],
               time_series: bool,
               n_time: int = 1,
               time_indices: IntVec | None = None,
               add_three_phase_data: bool = False) -> None:
    """
    Add every VeraGrid shunt to the target GSLV grid.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: GSLV circuit.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param facility_dict: VeraGrid-to-GSLV facility lookup.
    :param technology_dict: VeraGrid-to-GSLV technology lookup.
    :param time_series: Whether the export is time-series based.
    :param n_time: Number of exported time steps.
    :param time_indices: Optional time-series selection.
    :param add_three_phase_data: Export explicit three-phase fields when available.
    :return: None.
    """
    devices = circuit.get_shunts()
    for elm in devices:
        sh = convert_shunt(
            elm=elm,
            bus_dict=bus_dict,
            facility_dict=facility_dict,
            technology_dict=technology_dict,
            n_time=n_time,
            use_time_series=time_series,
            time_indices=time_indices,
            add_three_phase_data=add_three_phase_data,
        )
        gslv_grid.add_shunt(sh)
