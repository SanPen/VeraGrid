# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from VeraGridEngine.Compilers.Gslv.activation import build_status_dict, pg
from VeraGridEngine.Compilers.Gslv.common import (
    apply_three_phase_load_data,
    fill_profile,
    fill_profile_with_array,
    get_single_three_phase_snapshot_index,
    set_injection_associations,
)
from VeraGridEngine.Devices.Aggregation.facility import Facility
from VeraGridEngine.Devices.Associations.technology import Technology
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.OPF.opf_results import OptimalPowerFlowResults


def convert_load(k: int, elm: Load, bus_dict: Dict[str, "pg.Bus"],
                 facility_dict: Dict[Facility, "pg.Facility"],
                 technology_dict: Dict[Technology, "pg.Technology"],
                 n_time: int,
                 use_time_series: bool, time_indices: IntVec | None = None,
                 opf_results: OptimalPowerFlowResults | None = None,
                 add_three_phase_data: bool = False) -> "pg.Load":
    """
    Convert one VeraGrid load into one GSLV load.

    :param k: Load index.
    :param elm: VeraGrid load.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param facility_dict: VeraGrid-to-GSLV facility lookup.
    :param technology_dict: VeraGrid-to-GSLV technology lookup.
    :param n_time: Number of exported time steps.
    :param use_time_series: Whether the export is time-series based.
    :param time_indices: Optional time-series selection.
    :param opf_results: Optional OPF results.
    :param add_three_phase_data: Export explicit three-phase fields when available.
    :return: GSLV load.
    """
    load = pg.Load(
        nt=n_time,
        bus=None if elm.bus is None else bus_dict[elm.bus.idtag],
        name=elm.name,
        idtag=elm.idtag,
        code=str(elm.code),
        G=elm.G,
        B=elm.B,
        Ir=elm.Ir,
        Ii=elm.Ii,
        P=elm.P if opf_results is None else elm.P - opf_results.load_shedding[k],
        Q=elm.Q,
        Cost=elm.Cost,
        active=elm.active,
        mttf=elm.mttf,
        mttr=elm.mttr,
        capex=elm.capex,
        opex=elm.opex,
        build_status=build_status_dict[elm.build_status],
    )
    set_injection_associations(
        gslv_elm=load,
        elm=elm,
        facility_dict=facility_dict,
        technology_dict=technology_dict,
    )

    fill_profile(load.active, elm.active_prof, use_time_series, time_indices, n_time, elm.active)

    if opf_results is None:
        fill_profile(load.P, elm.P_prof, use_time_series, time_indices, n_time, elm.P)
    else:
        fill_profile_with_array(
            gslv_profile=load.P,
            arr=elm.P_prof.toarray() - opf_results.load_shedding[:, k],
            use_time_series=use_time_series,
            time_indices=time_indices,
            n_time=n_time,
            default_val=elm.P,
        )

    fill_profile(load.Q, elm.Q_prof, use_time_series, time_indices, n_time, elm.Q)
    fill_profile(load.G, elm.G_prof, use_time_series, time_indices, n_time, elm.G)
    fill_profile(load.B, elm.B_prof, use_time_series, time_indices, n_time, elm.B)
    fill_profile(load.Ir, elm.Ir_prof, use_time_series, time_indices, n_time, elm.Ir)
    fill_profile(load.Ii, elm.Ii_prof, use_time_series, time_indices, n_time, elm.Ii)
    fill_profile(load.cost, elm.Cost_prof, use_time_series, time_indices, n_time, elm.Cost)

    if add_three_phase_data:
        snapshot_time_index: int | None = get_single_three_phase_snapshot_index(
            use_time_series=use_time_series,
            time_indices=time_indices,
            n_time=n_time,
        )
        apply_three_phase_load_data(gslv_load=load, elm=elm, time_index=snapshot_time_index)
    else:
        pass

    return load


def add_loads(circuit: MultiCircuit,
              gslv_grid: "pg.MultiCircuit",
              bus_dict: Dict[str, "pg.Bus"],
              facility_dict: Dict[Facility, "pg.Facility"],
              technology_dict: Dict[Technology, "pg.Technology"],
              use_time_series: bool,
              n_time: int = 1,
              time_indices: IntVec | None = None,
              opf_results: OptimalPowerFlowResults | None = None,
              add_three_phase_data: bool = False) -> None:
    """
    Add every VeraGrid load to the target GSLV grid.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: GSLV circuit.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param facility_dict: VeraGrid-to-GSLV facility lookup.
    :param technology_dict: VeraGrid-to-GSLV technology lookup.
    :param use_time_series: Whether the export is time-series based.
    :param n_time: Number of exported time steps.
    :param time_indices: Optional time-series selection.
    :param opf_results: Optional OPF results.
    :param add_three_phase_data: Export explicit three-phase fields when available.
    :return: None.
    """
    devices = circuit.get_loads()
    for k, elm in enumerate(devices):
        load = convert_load(
            k=k,
            elm=elm,
            bus_dict=bus_dict,
            facility_dict=facility_dict,
            technology_dict=technology_dict,
            n_time=n_time,
            use_time_series=use_time_series,
            time_indices=time_indices,
            opf_results=opf_results,
            add_three_phase_data=add_three_phase_data,
        )
        gslv_grid.add_load(load)
