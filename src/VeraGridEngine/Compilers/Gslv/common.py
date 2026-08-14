# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Injections.controllable_shunt import ControllableShunt
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.Parents.shunt_parent import ShuntParent
from typing import List, Dict, Union, TYPE_CHECKING


from VeraGridEngine.Compilers.Gslv.activation import (pg, tap_module_control_mode_dict,
                                                           tap_phase_control_mode_dict, shunt_connection_type_dict,
                                                           GSLV_AVAILABLE)
from VeraGridEngine.basic_structures import IntVec, Vec
from VeraGridEngine.Devices.Profiles import AnyProfile
from VeraGridEngine.enumerations import (TapModuleControl, TapPhaseControl)

if TYPE_CHECKING:  # Only imports the below statements during type checking
    pass


def get_gslv_mip_solvers_list() -> List[str]:
    """
    Get list of available MIP solvers
    :return:
    """
    if GSLV_AVAILABLE:
        return list()
    else:
        return list()

def convert_tap_module_control_mode_dict(data: Dict[int, TapModuleControl]) -> Dict[int, "pg.TapModuleControl"]:
    """
    Function to convert a dictionary of TapModuleControl modes to pg.TapModuleControl modes
    :param data:
    :return:
    """
    return {i: tap_module_control_mode_dict[val] for i, val in data.items()}

def convert_tap_module_control_mode_lst(data: List[TapModuleControl]) -> List["pg.TapModuleControl"]:
    """
    Function to convert a list of TapModuleControl modes to pg.TapModuleControl modes
    :param data:
    :return:
    """
    return [tap_module_control_mode_dict[val] for val in data]

def convert_tap_phase_control_mode_dict(data: Dict[int, TapPhaseControl]) -> Dict[int, "pg.TapPhaseControl"]:
    """
    Function to convert a dictionary of TapPhaseControl modes to pg.TapPhaseControl modes
    :param data:
    :return:
    """
    return {i: tap_phase_control_mode_dict[val] for i, val in data.items()}

def convert_tap_phase_control_mode_lst(data: List[TapPhaseControl]) -> List["pg.TapPhaseControl"]:
    """
    Function to convert a list of TapPhaseControl modes to pg.TapPhaseControl modes
    :param data:
    :return:
    """
    return [tap_phase_control_mode_dict[val] for val in data]

def fill_profile(gslv_profile: "pg.Profiledouble|pg.Profilebool|pg.Profileint|pg.Profileuint",
                 gc_profile: AnyProfile,
                 use_time_series: bool,
                 time_indices: Union[IntVec, None],
                 n_time: int = 1,
                 default_val: int | float | bool | TapPhaseControl | TapModuleControl = 0) -> None:
    """
    Generates a default time series
    :param gslv_profile: Profile from gslv to fill in
    :param gc_profile: Profile from veragrid to convert
    :param use_time_series: use time series?
    :param time_indices: time series indices if any (optional)
    :param n_time: number of time steps
    :param default_val: Default value
    """

    if use_time_series:
        if gc_profile.is_sparse:
            if time_indices is None:

                default_val = gc_profile.sparse_array.default_value

                if isinstance(default_val, TapPhaseControl):
                    data = convert_tap_phase_control_mode_dict(data=gc_profile.sparse_array.get_map())

                    # we pick all the profile
                    gslv_profile.init_sparse(default_value=tap_phase_control_mode_dict[gc_profile.default_value],
                                             data=data)

                elif isinstance(default_val, TapModuleControl):
                    data = convert_tap_module_control_mode_dict(data=gc_profile.sparse_array.get_map())

                    # we pick all the profile
                    gslv_profile.init_sparse(default_value=tap_module_control_mode_dict[gc_profile.default_value],
                                             data=data)
                else:
                    data = gc_profile.sparse_array.get_map()

                    # we pick all the profile
                    gslv_profile.init_sparse(default_value=gc_profile.default_value, data=data)

            else:
                assert len(time_indices) == n_time

                # we need a sliced version
                sp_arr2 = gc_profile.sparse_array.slice(time_indices)

                if isinstance(default_val, TapPhaseControl):
                    data = convert_tap_phase_control_mode_dict(data=sp_arr2.get_map())
                    gslv_profile.init_sparse(default_value=tap_phase_control_mode_dict[gc_profile.default_value],
                                             data=data)

                elif isinstance(default_val, TapModuleControl):
                    data = convert_tap_module_control_mode_dict(data=sp_arr2.get_map())
                    gslv_profile.init_sparse(default_value=tap_module_control_mode_dict[gc_profile.default_value],
                                             data=data)

                else:
                    data = sp_arr2.get_map()
                    gslv_profile.init_sparse(default_value=gc_profile.default_value,
                                             data=data)

        else:
            if time_indices is None:
                # we pick all the profile

                if isinstance(default_val, TapPhaseControl):
                    data = convert_tap_phase_control_mode_lst(data=gc_profile.dense_array)
                elif isinstance(default_val, TapModuleControl):
                    data = convert_tap_module_control_mode_dict(data=gc_profile.dense_array)
                else:
                    data = gc_profile.dense_array

                gslv_profile.init_dense(data)

            else:
                assert len(time_indices) == n_time
                # we need a sliced version
                if isinstance(default_val, TapPhaseControl):
                    data = convert_tap_phase_control_mode_lst(data=gc_profile.dense_array[time_indices])
                elif isinstance(default_val, TapModuleControl):
                    data = convert_tap_module_control_mode_dict(data=gc_profile.dense_array[time_indices])
                else:
                    data = gc_profile.dense_array[time_indices]

                gslv_profile.init_dense(data)

    else:
        if isinstance(default_val, TapPhaseControl):
            gslv_profile.fill(tap_phase_control_mode_dict[default_val])

        elif isinstance(default_val, TapModuleControl):
            gslv_profile.fill(tap_module_control_mode_dict[default_val])

        else:
            gslv_profile.fill(default_val)

def fill_profile_with_array(gslv_profile: "pg.Profiledouble",
                            arr: Vec,
                            use_time_series: bool,
                            time_indices: Union[IntVec, None],
                            n_time: int = 1,
                            default_val: float = 0.0) -> None:
    """
    Generate one profile from a dense array.

    :param gslv_profile: GSLV profile to fill.
    :param arr: Dense VeraGrid array.
    :param use_time_series: Whether time-series data is being exported.
    :param time_indices: Optional time-series selection.
    :param n_time: Number of exported time steps.
    :param default_val: Scalar fallback value for snapshot exports.
    :return: None.
    """

    if use_time_series:
        if time_indices is None:
            # When there is no slicing request, the entire dense profile is exported.
            gslv_profile.init_dense(arr)
        else:
            assert len(time_indices) == n_time
            # The time-series export must preserve the selected VeraGrid slice only.
            gslv_profile.init_dense(arr[time_indices])
    else:
        # Snapshot exports collapse the profile to a single scalar value.
        gslv_profile.fill(default_val)

def get_single_three_phase_snapshot_index(
        use_time_series: bool,
        time_indices: Union[IntVec, None],
        n_time: int) -> int | None:
    """
    Return the original VeraGrid snapshot index when one three-phase slice is being exported.

    :param use_time_series: Whether the conversion uses time-series slicing.
    :param time_indices: Requested time indices.
    :param n_time: Number of exported time steps.
    :return: Original time index when there is exactly one slice, else ``None``.
    """
    if use_time_series:
        if time_indices is not None:
            if n_time == 1:
                return int(time_indices[0])
            else:
                return None
        else:
            return None
    else:
        return None

def apply_three_phase_load_data(gslv_load: "pg.Load", elm: Load, time_index: int | None) -> None:
    """
    Copy explicit three-phase load data into one GSLV load object.

    :param gslv_load: Target GSLV load.
    :param elm: Source VeraGrid load.
    :param time_index: Source time index when exporting one time slice.
    :return: None.
    """
    pa: float
    pb: float
    pc: float
    qa: float
    qb: float
    qc: float
    g1: float
    g2: float
    g3: float
    b1: float
    b2: float
    b3: float
    ir1: float
    ir2: float
    ir3: float
    ii1: float
    ii2: float
    ii3: float

    # The GSLV wrapper only exposes scalar three-phase setters, so each export must
    # resolve the VeraGrid phase values at one concrete time slice.
    if time_index is None:
        pa = float(elm.Pa)
        pb = float(elm.Pb)
        pc = float(elm.Pc)
        qa = float(elm.Qa)
        qb = float(elm.Qb)
        qc = float(elm.Qc)
        g1 = float(elm.G1)
        g2 = float(elm.G2)
        g3 = float(elm.G3)
        b1 = float(elm.B1)
        b2 = float(elm.B2)
        b3 = float(elm.B3)
        ir1 = float(elm.Ir1)
        ir2 = float(elm.Ir2)
        ir3 = float(elm.Ir3)
        ii1 = float(elm.Ii1)
        ii2 = float(elm.Ii2)
        ii3 = float(elm.Ii3)
    else:
        pa = float(elm.get_Pa_at(time_index))
        pb = float(elm.get_Pb_at(time_index))
        pc = float(elm.get_Pc_at(time_index))
        qa = float(elm.get_Qa_at(time_index))
        qb = float(elm.get_Qb_at(time_index))
        qc = float(elm.get_Qc_at(time_index))
        g1 = float(elm.get_G1_at(time_index))
        g2 = float(elm.get_G2_at(time_index))
        g3 = float(elm.get_G3_at(time_index))
        b1 = float(elm.get_B1_at(time_index))
        b2 = float(elm.get_B2_at(time_index))
        b3 = float(elm.get_B3_at(time_index))
        ir1 = float(elm.get_Ir1_at(time_index))
        ir2 = float(elm.get_Ir2_at(time_index))
        ir3 = float(elm.get_Ir3_at(time_index))
        ii1 = float(elm.get_Ii1_at(time_index))
        ii2 = float(elm.get_Ii2_at(time_index))
        ii3 = float(elm.get_Ii3_at(time_index))

    # The connection enum changes how the solver maps the phase injections.
    gslv_load.conn = shunt_connection_type_dict[elm.conn]
    gslv_load.set_P1_val(pa)
    gslv_load.set_P2_val(pb)
    gslv_load.set_P3_val(pc)
    gslv_load.set_Q1_val(qa)
    gslv_load.set_Q2_val(qb)
    gslv_load.set_Q3_val(qc)
    gslv_load.set_G1_val(g1)
    gslv_load.set_G2_val(g2)
    gslv_load.set_G3_val(g3)
    gslv_load.set_B1_val(b1)
    gslv_load.set_B2_val(b2)
    gslv_load.set_B3_val(b3)
    gslv_load.set_Ir1_val(ir1)
    gslv_load.set_Ir2_val(ir2)
    gslv_load.set_Ir3_val(ir3)
    gslv_load.set_Ii1_val(ii1)
    gslv_load.set_Ii2_val(ii2)
    gslv_load.set_Ii3_val(ii3)

def apply_three_phase_shunt_data(
        gslv_shunt: "pg.Shunt | pg.ControllableShunt",
        elm: ShuntParent,
        time_index: int | None) -> None:
    """
    Copy explicit three-phase shunt data into one GSLV shunt-like object.

    :param gslv_shunt: Target GSLV shunt-like object.
    :param elm: Source VeraGrid shunt-like object.
    :param time_index: Source time index when exporting one time slice.
    :return: None.
    """
    ga: float
    gb: float
    gc: float
    ba: float
    bb: float
    bc: float

    # The shunt connection and per-phase admittances define the unbalanced branch to neutral.
    if time_index is None:
        ga = float(elm.Ga)
        gb = float(elm.Gb)
        gc = float(elm.Gc)
        ba = float(elm.Ba)
        bb = float(elm.Bb)
        bc = float(elm.Bc)
    else:
        ga = float(elm.get_Ga_at(time_index))
        gb = float(elm.get_Gb_at(time_index))
        gc = float(elm.get_Gc_at(time_index))
        ba = float(elm.get_Ba_at(time_index))
        bb = float(elm.get_Bb_at(time_index))
        bc = float(elm.get_Bc_at(time_index))

    gslv_shunt.conn = shunt_connection_type_dict[elm.conn]
    gslv_shunt.set_Ga_val(ga)
    gslv_shunt.set_Gb_val(gb)
    gslv_shunt.set_Gc_val(gc)
    gslv_shunt.set_Ba_val(ba)
    gslv_shunt.set_Bb_val(bb)
    gslv_shunt.set_Bc_val(bc)

