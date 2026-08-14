# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Compilers.Gslv.common import fill_profile, fill_profile_with_array
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.OPF.opf_results import OptimalPowerFlowResults


def convert_generator(k: int,
                      elm: Generator,
                      bus_dict: Dict[str, "pg.Bus"],
                      n_time: int,
                      use_time_series: bool,
                      time_indices: IntVec | None = None,
                      opf_results: OptimalPowerFlowResults | None = None,
                      add_three_phase_data: bool = False) -> "pg.Generator":
    """
    Convert one VeraGrid generator into one GSLV generator.

    :param k: Generator index.
    :param elm: VeraGrid generator.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param n_time: Number of exported time steps.
    :param use_time_series: Whether the export is time-series based.
    :param time_indices: Optional time-series selection.
    :param opf_results: Optional OPF results.
    :param add_three_phase_data: Export sequence impedances needed by three-phase studies.
    :return: GSLV generator.
    """
    generator_r0: float
    generator_x0: float
    generator_r2: float
    generator_x2: float

    if add_three_phase_data:
        generator_r0 = float(elm.R0)
        generator_x0 = float(elm.X0)
        generator_r2 = float(elm.R2)
        generator_x2 = float(elm.X2)
    else:
        generator_r0 = 1e-20
        generator_x0 = 1e-20
        generator_r2 = 1e-20
        generator_x2 = 1e-20

    gen = pg.Generator(
        nt=n_time,
        bus=None if elm.bus is None else bus_dict[elm.bus.idtag],
        name=elm.name,
        idtag=elm.idtag,
        active=elm.active,
        P=elm.P,
        Q=elm.Q,
        vset=elm.Vset,
        Pmin=elm.Pmin,
        Pmax=elm.Pmax,
        Qmin=elm.Qmin,
        Qmax=elm.Qmax,
        Snom=elm.Snom,
        is_controlled=elm.is_controlled,
        enabled_dispatch=elm.enabled_dispatch,
        q_points=elm.q_curve.get_data().tolist(),
        use_reactive_power_curve=elm.use_reactive_power_curve,
        r0=generator_r0,
        x0=generator_x0,
        r2=generator_r2,
        x2=generator_x2,
    )

    fill_profile(gen.active, elm.active_prof, use_time_series, time_indices, n_time, elm.active)

    if opf_results is None:
        fill_profile(gen.P, elm.P_prof, use_time_series, time_indices, n_time, elm.P)
    else:
        fill_profile_with_array(
            gslv_profile=gen.P,
            arr=opf_results.generator_power[:, k] - opf_results.generator_shedding[:, k],
            use_time_series=use_time_series,
            time_indices=time_indices,
            n_time=n_time,
            default_val=elm.P,
        )

    fill_profile(gen.Q, elm.Q_prof, use_time_series, time_indices, n_time, elm.Q)
    fill_profile(gen.Vset, elm.Vset_prof, use_time_series, time_indices, n_time, elm.Vset)
    fill_profile(gen.cost, elm.Cost_prof, use_time_series, time_indices, n_time, elm.Cost)
    fill_profile(gen.Cost0, elm.Cost0_prof, use_time_series, time_indices, n_time, elm.Cost0)
    fill_profile(gen.Cost2, elm.Cost2_prof, use_time_series, time_indices, n_time, elm.Cost2)

    return gen


def add_generators(circuit: MultiCircuit,
                   gslv_grid: "pg.MultiCircuit",
                   bus_dict: Dict[str, "pg.Bus"],
                   time_series: bool,
                   n_time: int = 1,
                   time_indices: IntVec | None = None,
                   opf_results: OptimalPowerFlowResults | None = None,
                   add_three_phase_data: bool = False) -> None:
    """
    Add every VeraGrid generator to the target GSLV grid.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: GSLV circuit.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param time_series: Whether the export is time-series based.
    :param n_time: Number of exported time steps.
    :param time_indices: Optional time-series selection.
    :param opf_results: Optional OPF results.
    :param add_three_phase_data: Export sequence impedances needed by three-phase studies.
    :return: None.
    """
    devices = circuit.get_generators()

    for k, elm in enumerate(devices):
        gen = convert_generator(
            k=k,
            elm=elm,
            bus_dict=bus_dict,
            n_time=n_time,
            use_time_series=time_series,
            time_indices=time_indices,
            opf_results=opf_results,
            add_three_phase_data=add_three_phase_data,
        )
        gslv_grid.add_generator(gen)
