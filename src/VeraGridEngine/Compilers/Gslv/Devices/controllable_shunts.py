# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict

import numpy as np

from VeraGridEngine.Compilers.Gslv.activation import build_status_dict, pg
from VeraGridEngine.Compilers.Gslv.common import (
    apply_three_phase_shunt_data,
    fill_profile,
    get_single_three_phase_snapshot_index,
    set_injection_associations,
)
from VeraGridEngine.Devices.Aggregation.facility import Facility
from VeraGridEngine.Devices.Associations.technology import Technology
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec
from VeraGridEngine.enumerations import ShuntControlMode


def convert_controllable_shunt(elm: ControllableShunt,
                               bus_dict: Dict[str, "pg.Bus"],
                               facility_dict: Dict[Facility, "pg.Facility"],
                               technology_dict: Dict[Technology, "pg.Technology"],
                               n_time: int,
                               use_time_series: bool,
                               shunt_control_mode_dict: Dict[ShuntControlMode, "pg.ShuntControlMode"],
                               time_indices: IntVec | None = None,
                               add_three_phase_data: bool = False) -> "pg.ControllableShunt":
    """
    Convert one VeraGrid controllable shunt into one GSLV controllable shunt.

    :param elm: VeraGrid controllable shunt.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param facility_dict: VeraGrid-to-GSLV facility lookup.
    :param technology_dict: VeraGrid-to-GSLV technology lookup.
    :param n_time: Number of exported time steps.
    :param use_time_series: Whether the export is time-series based.
    :param shunt_control_mode_dict: Shunt-control enum translator.
    :param time_indices: Optional time-series selection.
    :param add_three_phase_data: Export explicit three-phase fields when available.
    :return: GSLV controllable shunt.
    """
    if not isinstance(elm.g_steps, np.ndarray):
        raise TypeError(f"ControllableShunt.g_steps must be np.ndarray, got {type(elm.g_steps)}")
    else:
        pass

    if not isinstance(elm.b_steps, np.ndarray):
        raise TypeError(f"ControllableShunt.b_steps must be np.ndarray, got {type(elm.b_steps)}")
    else:
        pass

    g_steps: np.ndarray = np.asarray(elm.g_steps, dtype=float).reshape(-1)
    b_steps: np.ndarray = np.asarray(elm.b_steps, dtype=float).reshape(-1)

    number_of_steps: int = max(int(g_steps.size), int(b_steps.size), 1)
    if g_steps.size == 0:
        g_steps = np.zeros(number_of_steps, dtype=float)
    elif b_steps.size not in (0, g_steps.size):
        raise ValueError(f"ControllableShunt {elm.name} has mismatched step arrays")
    else:
        pass

    if b_steps.size == 0:
        b_steps = np.zeros(number_of_steps, dtype=float)
    elif g_steps.size != b_steps.size:
        raise ValueError(f"ControllableShunt {elm.name} has mismatched step arrays")
    else:
        pass

    step: int = min(max(int(elm.step), 0), number_of_steps - 1)

    sh = pg.ControllableShunt(
        nt=n_time,
        bus=None if elm.bus is None else bus_dict[elm.bus.idtag],
        name=elm.name,
        idtag=elm.idtag,
        code=str(elm.code),
        number_of_steps=number_of_steps,
        step=step,
        g_per_step=0.0,
        b_per_step=0.0,
        Cost=elm.Cost,
        active=elm.active,
        G=elm.G,
        B=elm.B,
        G0=elm.G0,
        B0=elm.B0,
        vset=elm.Vset,
        vmin=elm.Vmin,
        vmax=elm.Vmax,
        mttf=elm.mttf,
        mttr=elm.mttr,
        capex=elm.capex,
        opex=elm.opex,
        control_bus=None if elm.control_bus is None else bus_dict[elm.control_bus.idtag],
        control_mode=shunt_control_mode_dict[elm.control_mode],
        build_status=build_status_dict[elm.build_status],
    )
    set_injection_associations(
        gslv_elm=sh,
        elm=elm,
        facility_dict=facility_dict,
        technology_dict=technology_dict,
    )

    sh.g_steps = g_steps.tolist()
    sh.b_steps = b_steps.tolist()

    if add_three_phase_data:
        snapshot_time_index: int | None = get_single_three_phase_snapshot_index(
            use_time_series=use_time_series,
            time_indices=time_indices,
            n_time=n_time,
        )
        apply_three_phase_shunt_data(gslv_shunt=sh, elm=elm, time_index=snapshot_time_index)
    else:
        pass

    fill_profile(sh.active, elm.active_prof, use_time_series, time_indices, n_time, elm.active)
    fill_profile(sh.G, elm.G_prof, use_time_series, time_indices, n_time, elm.G)
    fill_profile(sh.B, elm.B_prof, use_time_series, time_indices, n_time, elm.B)
    fill_profile(sh.cost, elm.Cost_prof, use_time_series, time_indices, n_time, elm.Cost)
    fill_profile(sh.Vset, elm.Vset_prof, use_time_series, time_indices, n_time, elm.Vset)

    return sh


def add_controllable_shunts(circuit: MultiCircuit,
                            gslv_grid: "pg.MultiCircuit",
                            bus_dict: Dict[str, "pg.Bus"],
                            facility_dict: Dict[Facility, "pg.Facility"],
                            technology_dict: Dict[Technology, "pg.Technology"],
                            time_series: bool,
                            n_time: int = 1,
                            time_indices: IntVec | None = None,
                            add_three_phase_data: bool = False) -> None:
    """
    Add every VeraGrid controllable shunt to the target GSLV grid.

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
    shunt_control_mode_dict: Dict[ShuntControlMode, "pg.ShuntControlMode"] = {
        ShuntControlMode.Locked: pg.ShuntControlMode.Locked,
        ShuntControlMode.Continuous: pg.ShuntControlMode.Continuous,
        ShuntControlMode.Discrete: pg.ShuntControlMode.Discrete,
    }

    devices = circuit.get_controllable_shunts()
    for elm in devices:
        sh = convert_controllable_shunt(
            elm=elm,
            bus_dict=bus_dict,
            facility_dict=facility_dict,
            technology_dict=technology_dict,
            n_time=n_time,
            use_time_series=time_series,
            time_indices=time_indices,
            shunt_control_mode_dict=shunt_control_mode_dict,
            add_three_phase_data=add_three_phase_data,
        )
        gslv_grid.add_controllable_shunt(sh)
