# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from VeraGridEngine.Compilers.Gslv.activation import build_status_dict, pg
from VeraGridEngine.Compilers.Gslv.common import fill_profile, fill_profile_with_array, set_generator_associations
from VeraGridEngine.Devices.Aggregation.facility import Facility
from VeraGridEngine.Devices.Aggregation.market_unit import MarketUnit
from VeraGridEngine.Devices.Associations.emission_gas import EmissionGas
from VeraGridEngine.Devices.Associations.fuel import Fuel
from VeraGridEngine.Devices.Associations.technology import Technology
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.OPF.opf_results import OptimalPowerFlowResults


def generator_tpe(elm: Generator) -> str:
    """
    Get the selected technology label for a VeraGrid generator.

    :param elm: VeraGrid generator.
    :return: Name of the strongest technology association, or ``Other``.
    """
    best_name: str = "Other"
    best_value: float = -1.0

    for association in elm.technologies:
        value: float = float(association.value)
        if value > best_value:
            best_value = value
            best_name = str(association.api_object.name)
        else:
            pass

    return best_name


def generator_control_mode(elm: Generator) -> "pg.GeneratorControlMode":
    """
    Convert one VeraGrid generator control mode to pygslv.

    :param elm: VeraGrid generator.
    :return: Equivalent pygslv control mode.
    """
    return pg.GeneratorControlMode.__members__[elm.control_mode.name]


def convert_generator(k: int,
                      elm: Generator,
                      bus_dict: Dict[str, "pg.Bus"],
                      facility_dict: Dict[Facility, "pg.Facility"],
                      market_unit_dict: Dict[MarketUnit, "pg.MarketUnit"],
                      technology_dict: Dict[Technology, "pg.Technology"],
                      fuel_dict: Dict[Fuel, "pg.Fuel"],
                      emission_gas_dict: Dict[EmissionGas, "pg.EmissionGas"],
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
    :param facility_dict: VeraGrid-to-GSLV facility lookup.
    :param market_unit_dict: VeraGrid-to-GSLV market-unit lookup.
    :param technology_dict: VeraGrid-to-GSLV technology lookup.
    :param fuel_dict: VeraGrid-to-GSLV fuel lookup.
    :param emission_gas_dict: VeraGrid-to-GSLV emission gas lookup.
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
        code=elm.code,
        tpe=generator_tpe(elm=elm),
        active=elm.active,
        P=elm.P,
        Q=elm.Q,
        power_factor=elm.Pf,
        vset=elm.Vset,
        Pmin=elm.Pmin,
        Pmax=elm.Pmax,
        Qmin=elm.Qmin,
        Qmax=elm.Qmax,
        Snom=elm.Snom,
        Cost=elm.Cost,
        Cost2=elm.Cost2,
        Cost0=elm.Cost0,
        Sbase=elm.Sbase,
        is_controlled=elm.is_controlled,
        enabled_dispatch=elm.enabled_dispatch,
        mttf=elm.mttf,
        mttr=elm.mttr,
        q_points=elm.q_curve.get_data().tolist(),
        use_reactive_power_curve=elm.use_reactive_power_curve,
        r1=elm.R1,
        x1=elm.X1,
        r0=generator_r0,
        x0=generator_x0,
        r2=generator_r2,
        x2=generator_x2,
        capex=elm.capex,
        opex=elm.opex,
        srap_enabled=elm.srap_enabled,
        build_status=build_status_dict[elm.build_status],
        must_run=elm.must_run,
        startup_cost=elm.startup_cost,
        shutdown_cost=elm.shutdown_cost,
        min_time_up=elm.min_time_up,
        min_time_down=elm.min_time_down,
        ramp_up=elm.ramp_up,
        ramp_down=elm.ramp_down,
        control_mode=generator_control_mode(elm=elm),
        k_droop=elm.k_droop,
        dead_band=elm.dead_band,
        rs=elm.Rs,
        xs=elm.Xs,
        xm=elm.Xm,
        rr=elm.Rr,
        xr=elm.Xr,
        freq=elm.freq,
        market_unit=market_unit_dict.get(elm.market_unit, None),
        market_unit_share=elm.market_unit_share,
        is_static_generator=elm.is_static_generator,
    )
    if elm.control_bus is None:
        pass
    else:
        gen.set_control_bus_val(bus_dict[elm.control_bus.idtag])

    set_generator_associations(
        gslv_elm=gen,
        elm=elm,
        facility_dict=facility_dict,
        technology_dict=technology_dict,
        fuel_dict=fuel_dict,
        emission_gas_dict=emission_gas_dict,
    )

    fill_profile(gen.active, elm.active_prof, use_time_series, time_indices, n_time, elm.active)
    fill_profile(gen.srap_enabled, elm.srap_enabled_prof, use_time_series, time_indices, n_time, elm.srap_enabled)

    gen.enabled_dispatch = fill_profile(
        gen.enabled_dispatch,
        elm.enabled_dispatch_prof,
        use_time_series,
        time_indices,
        n_time,
        elm.enabled_dispatch,
    )

    gen.must_run = fill_profile(gen.must_run, elm.must_run_prof, use_time_series, time_indices, n_time, elm.must_run)

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
    fill_profile(gen.power_factor, elm.Pf_prof, use_time_series, time_indices, n_time, elm.Pf)

    gen.Pmin = fill_profile(gen.Pmin, elm.Pmin_prof, use_time_series, time_indices, n_time, elm.Pmin)
    gen.Pmax = fill_profile(gen.Pmax, elm.Pmax_prof, use_time_series, time_indices, n_time, elm.Pmax)
    gen.qmin_set = fill_profile(gen.qmin_set, elm.Qmin_prof, use_time_series, time_indices, n_time, elm.Qmin)
    gen.qmax_set = fill_profile(gen.qmax_set, elm.Qmax_prof, use_time_series, time_indices, n_time, elm.Qmax)

    fill_profile(gen.Vset, elm.Vset_prof, use_time_series, time_indices, n_time, elm.Vset)
    fill_profile(gen.cost, elm.Cost_prof, use_time_series, time_indices, n_time, elm.Cost)
    fill_profile(gen.Cost0, elm.Cost0_prof, use_time_series, time_indices, n_time, elm.Cost0)
    fill_profile(gen.Cost2, elm.Cost2_prof, use_time_series, time_indices, n_time, elm.Cost2)
    fill_profile(gen.market_unit_share,
                 elm.market_unit_share_prof,
                 use_time_series,
                 time_indices,
                 n_time,
                 elm.market_unit_share)

    return gen


def add_generators(circuit: MultiCircuit,
                   gslv_grid: "pg.MultiCircuit",
                   bus_dict: Dict[str, "pg.Bus"],
                   facility_dict: Dict[Facility, "pg.Facility"],
                   market_unit_dict: Dict[MarketUnit, "pg.MarketUnit"],
                   technology_dict: Dict[Technology, "pg.Technology"],
                   fuel_dict: Dict[Fuel, "pg.Fuel"],
                   emission_gas_dict: Dict[EmissionGas, "pg.EmissionGas"],
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
    :param facility_dict: VeraGrid-to-GSLV facility lookup.
    :param market_unit_dict: VeraGrid-to-GSLV market-unit lookup.
    :param technology_dict: VeraGrid-to-GSLV technology lookup.
    :param fuel_dict: VeraGrid-to-GSLV fuel lookup.
    :param emission_gas_dict: VeraGrid-to-GSLV emission gas lookup.
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
            facility_dict=facility_dict,
            market_unit_dict=market_unit_dict,
            technology_dict=technology_dict,
            fuel_dict=fuel_dict,
            emission_gas_dict=emission_gas_dict,
            n_time=n_time,
            use_time_series=time_series,
            time_indices=time_indices,
            opf_results=opf_results,
            add_three_phase_data=add_three_phase_data,
        )
        gslv_grid.add_generator(gen)
