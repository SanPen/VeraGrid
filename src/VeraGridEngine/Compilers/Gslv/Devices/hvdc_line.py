# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict

from VeraGridEngine.Compilers.Gslv.activation import hvdc_control_mode_dict, pg
from VeraGridEngine.Compilers.Gslv.common import fill_profile
from VeraGridEngine.Devices.Branches.hvdc_line import HvdcLine
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec


def convert_hvdc_line(elm: HvdcLine,
                      bus_dict: Dict[str, "pg.Bus"],
                      n_time: int,
                      use_time_series: bool,
                      time_indices: IntVec | None) -> "pg.HvdcLine":
    """
    Convert one VeraGrid HVDC line into one GSLV HVDC line.

    :param elm: VeraGrid HVDC line.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param n_time: Number of exported time steps.
    :param use_time_series: Whether the export is time-series based.
    :param time_indices: Optional time-series selection.
    :return: GSLV HVDC line.
    """
    hvdc = pg.HvdcLine(
        idtag=elm.idtag,
        code=str(elm.code),
        name=elm.name,
        bus_from=bus_dict[elm.bus_from.idtag],
        bus_to=bus_dict[elm.bus_to.idtag],
        nt=n_time,
        active=elm.active,
        rate=elm.rate,
        contingency_factor=elm.contingency_factor,
        pset=elm.Pset,
        Vset_f=elm.Vset_f,
        Vset_t=elm.Vset_t,
        r=float(elm.r),
        angle_droop=elm.angle_droop,
        length=elm.length,
        min_firing_angle_f=elm.min_firing_angle_f,
        max_firing_angle_f=elm.max_firing_angle_f,
        min_firing_angle_t=elm.min_firing_angle_t,
        max_firing_angle_t=elm.max_firing_angle_t,
        control_mode=hvdc_control_mode_dict[elm.control_mode],
    )

    fill_profile(hvdc.active, elm.active_prof, use_time_series, time_indices, n_time, elm.active)
    fill_profile(hvdc.Vset_f, elm.Vset_f_prof, use_time_series, time_indices, n_time, elm.Vset_f)
    fill_profile(hvdc.Vset_f, elm.Vset_f_prof, use_time_series, time_indices, n_time, elm.Vset_f)
    fill_profile(hvdc.Vset_t, elm.Vset_t_prof, use_time_series, time_indices, n_time, elm.Vset_t)
    fill_profile(hvdc.angle_droop, elm.angle_droop_prof, use_time_series, time_indices, n_time, elm.angle_droop)
    fill_profile(hvdc.rate, elm.rate_prof, use_time_series, time_indices, n_time, elm.rate)
    fill_profile(
        hvdc.contingency_factor,
        elm.contingency_factor_prof,
        use_time_series,
        time_indices,
        n_time,
        elm.contingency_factor,
    )
    fill_profile(hvdc.cost, elm.Cost_prof, use_time_series, time_indices, n_time, elm.Cost)

    return hvdc


def add_hvdcs(circuit: MultiCircuit,
              gslv_grid: "pg.MultiCircuit",
              bus_dict: Dict[str, "pg.Bus"],
              time_series: bool,
              n_time: int = 1,
              time_indices: IntVec | None = None) -> None:
    """
    Add every VeraGrid HVDC line to the target GSLV grid.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: GSLV circuit.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param time_series: Whether the export is time-series based.
    :param n_time: Number of exported time steps.
    :param time_indices: Optional time-series selection.
    :return: None.
    """
    for elm in circuit.hvdc_lines:
        hvdc = convert_hvdc_line(
            elm=elm,
            bus_dict=bus_dict,
            n_time=n_time,
            use_time_series=time_series,
            time_indices=time_indices,
        )
        gslv_grid.add_hvdc_line(hvdc)
