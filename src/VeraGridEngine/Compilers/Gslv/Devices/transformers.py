# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.branch_group import BranchGroup
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.transformer3w import Transformer3W
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Compilers.Gslv.activation import (
    pg,
    tap_module_control_mode_dict,
    tap_phase_control_mode_dict,
    winding_type_dict,
    windings_connection_dict,
)
from VeraGridEngine.Compilers.Gslv.common import fill_profile
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec
from typing import (
    Dict,
    Union,
)


def convert_transformer(elm: Transformer2W,
                        bus_dict: Dict[str, "pg.Bus"],
                        branch_groups_dict: Dict[BranchGroup, "pg.BranchGroup"],
                        n_time: int,
                        use_time_series: bool, time_indices: IntVec | None,
                        override_controls: bool,
                        add_three_phase_data: bool = False) -> "pg.Transformer2W":
    """
    Convert one VeraGrid two-winding transformer into one GSLV transformer.

    :param elm: VeraGrid transformer.
    :param bus_dict: Bus lookup by VeraGrid id tag.
    :param branch_groups_dict: Branch-group lookup.
    :param n_time: Number of exported time steps.
    :param use_time_series: Whether the export is time-series based.
    :param time_indices: Optional time-series selection.
    :param override_controls: Whether transformer control modes must be forced to fixed.
    :param add_three_phase_data: Export sequence parameters and winding connections.
    :return: GSLV transformer.
    """

    tr2 = pg.Transformer2W(
        nt=n_time,
        name=elm.name,
        idtag=elm.idtag,
        code=str(elm.code),
        bus_from=bus_dict[elm.bus_from.idtag],
        bus_to=bus_dict[elm.bus_to.idtag],
        HV=elm.HV,
        LV=elm.LV,
        nominal_power=elm.Sn,
        copper_losses=elm.Pcu,
        iron_losses=elm.Pfe,
        no_load_current=elm.I0,
        short_circuit_voltage=elm.Vsc,
        active=elm.active,
        rate=elm.rate if elm.rate > 0.0 else 9999.0,
        r=elm.R,
        x=elm.X,
        g=elm.G,
        b=elm.B,
        tap_module=elm.tap_module,
        tap_module_max=elm.tap_module_max,
        tap_module_min=elm.tap_module_min,
        tap_phase=elm.tap_phase,
        tap_phase_max=elm.tap_phase_max,
        tap_phase_min=elm.tap_phase_min,
        tolerance=elm.tolerance,
        cost=elm.Cost,
        mttf=elm.mttf,
        mttr=elm.mttr,
        vset=elm.vset,
        Pset=elm.Pset,
        Qset=elm.Qset,
        temp_base=elm.temp_base,
        temp_oper=elm.temp_oper,
        alpha=elm.alpha,
        tap_module_control_mode=tap_module_control_mode_dict[elm.tap_module_control_mode],
        tap_phase_control_mode=tap_phase_control_mode_dict[elm.tap_phase_control_mode],
        contingency_factor=elm.contingency_factor,
        protection_rating_factor=1.4,
        monitor_loading=True,
        r0=elm.R0,
        x0=elm.X0,
        g0=elm.G0,
        b0=elm.B0,
        r2=elm.R2,
        x2=elm.X2,
        g2=elm.G2,
        b2=elm.B2,
        conn=windings_connection_dict[elm.conn],
        capex=elm.capex,
        opex=elm.opex,
        build_status=pg.BuildStatus.Commissioned,
        tc_total_positions = elm._tap_changer.total_positions,
        tc_neutral_position = elm._tap_changer.neutral_position,
        tc_normal_position = elm._tap_changer.normal_position,
        tc_dV = elm._tap_changer.dV,
        tc_asymmetry_angle = elm._tap_changer.asymmetry_angle,
        tc_type = pg.TapChangerTypes.NoRegulation,
        # template=None,
        # design_rate=0.0,
        # contingency_enabled=True,
    )

    if add_three_phase_data:
        tr2.conn_f = winding_type_dict[elm.conn_f]
        tr2.conn_t = winding_type_dict[elm.conn_t]
    else:
        pass

    if elm.regulation_bus is not None:
        tr2.regulation_bus = bus_dict[elm.regulation_bus.idtag]
    else:
        pass

    if elm.group is not None:
        tr2.group = branch_groups_dict[elm.group]

    fill_profile(gslv_profile=tr2.active,
                 gc_profile=elm.active_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.active)

    fill_profile(gslv_profile=tr2.rate,
                 gc_profile=elm.rate_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.rate)

    fill_profile(gslv_profile=tr2.contingency_factor,
                 gc_profile=elm.contingency_factor_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.contingency_factor)

    fill_profile(gslv_profile=tr2.cost,
                 gc_profile=elm.Cost_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.Cost)

    fill_profile(gslv_profile=tr2.Pset,
                 gc_profile=elm.Pset_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.Pset)

    fill_profile(gslv_profile=tr2.Qset,
                 gc_profile=elm.Qset_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.Qset)

    fill_profile(gslv_profile=tr2.vset,
                 gc_profile=elm.vset_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.vset)

    fill_profile(gslv_profile=tr2.temp_oper,
                 gc_profile=elm.temp_oper_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.temp_oper)

    fill_profile(gslv_profile=tr2.tap_phase,
                 gc_profile=elm.tap_phase_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.tap_phase)

    fill_profile(gslv_profile=tr2.tap_phase_control_mode,
                 gc_profile=elm.tap_phase_control_mode_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.tap_phase_control_mode)

    fill_profile(gslv_profile=tr2.tap_module,
                 gc_profile=elm.tap_module_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.tap_module)

    fill_profile(gslv_profile=tr2.tap_module_control_mode,
                 gc_profile=elm.tap_module_control_mode_prof,
                 use_time_series=use_time_series,
                 time_indices=time_indices,
                 n_time=n_time,
                 default_val=elm.tap_module_control_mode)

    # control vars
    if override_controls:
        tr2.tap_module_control_mode.fill(pg.TapModuleControl.fixed)
        tr2.tap_phase_control_mode.fill(pg.TapPhaseControl.fixed)
    else:
        pass

    return tr2


def add_transformers(circuit: MultiCircuit,
                     gslv_grid: "pg.MultiCircuit",
                     bus_dict: Dict[str, "pg.Bus"],
                     branch_groups_dict: Dict[BranchGroup, "pg.BranchGroup"],
                     time_series: bool,
                     n_time: int = 1,
                     time_indices: Union[IntVec, None] = None,
                     override_controls: bool = False,
                     add_three_phase_data: bool = False) -> None:
    """

    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV circuit
    :param time_series: compile the time series from VeraGrid? otherwise just the snapshot
    :param bus_dict: dictionary of bus id to GSLV bus object
    :param branch_groups_dict: dictionary of branch grous converetd
    :param n_time: number of time steps
    :param time_indices: Array of time indices
    :param override_controls: If true the controls are set to Fix
    :param add_three_phase_data: Export sequence parameters and winding connections.
    :return: None.
    """

    for i, elm in enumerate(circuit.transformers2w):
        tr2 = convert_transformer(elm=elm,
                                  bus_dict=bus_dict,
                                  branch_groups_dict=branch_groups_dict,
                                  n_time=n_time,
                                  use_time_series=time_series,
                                  time_indices=time_indices,
                                  override_controls=override_controls,
                                  add_three_phase_data=add_three_phase_data)
        gslv_grid.add_transformer(tr2)
