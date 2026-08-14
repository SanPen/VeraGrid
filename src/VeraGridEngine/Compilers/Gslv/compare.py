# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Compilers.Gslv.activation import (
    bus_type_dict,
    converter_control_type_dict,
    hvdc_control_mode_dict,
    pg,
)
from VeraGridEngine.DataStructures.branch_parent_data import BranchParentData
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.basic_structures import Vec
import numpy as np
from typing import Dict


def CheckArr(arr: Vec, arr_expected: Vec, tol: float, name: str, test: str, verbose=False):
    """

    :param arr:
    :param arr_expected:
    :param tol:
    :param name:
    :param test:
    :param verbose:
    :return:
    """
    if arr.shape != arr_expected.shape:
        print('failed (shape):', name, test)
        print(f"got     : {arr}, \n"
              f"expected: {arr_expected}")
        return 1

    if np.allclose(arr, arr_expected, atol=tol):
        if verbose:
            print('ok:', name, test)
            print('ok:', name, test)
        return 0
    else:
        diff = arr - arr_expected
        print('failed:', name, test, '| max:', diff.max(), 'min:', diff.min())
        return 1

def CheckArrEq(arr: np.ndarray, arr_expected: np.ndarray,
               name: str, test: str, verbose=False):
    """

    :param arr:
    :param arr_expected:
    :param name:
    :param test:
    :param verbose:
    :return:
    """
    if arr.shape != arr_expected.shape:
        print('failed (shape):', name, test)
        print(f"got     : {arr}, \n"
              f"expected: {arr_expected}")
        return 1

    if np.all(arr == arr_expected):
        if verbose:
            print('ok:', name, test)
        return 0
    else:
        print('failed:', name, test)
        return 1

def convert_arr(arr, d: Dict):
    return np.array([d[e] for e in arr])

def convert_gslv_arr_to_idx(arr, d: Dict):
    pg_to_idx = {pg_val: gc_val.idx() for gc_val, pg_val in d.items()}
    return np.array([pg_to_idx[e] for e in arr], dtype=int)

def compare_branch_parent_data(gslv_branch_data: pg.BranchParentData,
                               gc_branch_data: BranchParentData,
                               tol: float,
                               parent_name: str):
    """

    :param gslv_branch_data:
    :param gc_branch_data:
    :param tol:
    :param parent_name:
    :return:
    """
    errors = 0

    # branch data
    errors += CheckArrEq(np.array(gslv_branch_data.idtag), np.array(gc_branch_data.idtag), parent_name, 'idtag')
    errors += CheckArrEq(gslv_branch_data.F, gc_branch_data.F, parent_name, 'F')
    errors += CheckArrEq(gslv_branch_data.T, gc_branch_data.T, parent_name, 'T')
    errors += CheckArrEq(gslv_branch_data.active, gc_branch_data.active, parent_name, 'active')
    errors += CheckArr(gslv_branch_data.rates, gc_branch_data.rates, tol, parent_name, 'rates')

    errors += CheckArr(gslv_branch_data.contingency_rates, gc_branch_data.contingency_rates, tol,
                       parent_name, 'contingency_rates')

    errors += CheckArr(gslv_branch_data.protection_rates, gc_branch_data.protection_rates, tol,
                       parent_name, 'protection_rates')

    errors += CheckArr(gslv_branch_data.mttf, gc_branch_data.mttf, tol, parent_name, 'mttf')
    errors += CheckArr(gslv_branch_data.mttr, gc_branch_data.mttr, tol, parent_name, 'mttr')

    # errors += CheckArrEq(gslv_branch_data.contingency_enabled, gc_branch_data.contingency_enabled,
    #                      parent_name, 'contingency_enabled')
    errors += CheckArrEq(gslv_branch_data.monitor_loading, gc_branch_data.monitor_loading,
                         parent_name, 'monitor_loading')

    errors += CheckArr(gslv_branch_data.overload_cost, gc_branch_data.overload_cost, tol,
                       parent_name, 'overload_cost')
    errors += CheckArrEq(gslv_branch_data.original_idx, gc_branch_data.original_idx,
                         parent_name, 'original_idx')
    # errors += CheckArr(gslv_branch_data.reducible, gc_branch_data.reducible, tol, parent_name, 'reducible')

    return errors

def compare_nc(nc_gslv: "pg.NumericalCircuit", nc_gc: NumericalCircuit, tol: float):
    """

    :param nc_gslv:
    :param nc_gc:
    :param tol:
    :return:
    """
    errors = 0

    # bus data
    errors += CheckArrEq(nc_gslv.bus_data.active, nc_gc.bus_data.active, 'BusData', 'active')
    errors += CheckArr(nc_gslv.bus_data.Vbus.real, nc_gc.bus_data.Vbus.real, tol, 'BusData', 'V0')
    errors += CheckArr(nc_gslv.bus_data.installed_power, nc_gc.bus_data.installed_power, tol,
                       'BusData', 'installed power')
    errors += CheckArrEq(np.array(nc_gslv.bus_data.bus_types),
                         convert_arr(nc_gc.bus_data.bus_types, bus_type_dict),
                         'BusData', 'bus_types')

    # branch data
    errors += compare_branch_parent_data(nc_gslv.passive_branch_data, nc_gc.passive_branch_data, tol,
                                         "PassiveBranchData")
    errors += CheckArr(nc_gslv.passive_branch_data.R, nc_gc.passive_branch_data.R, tol, 'PassiveBranchData', 'r')
    errors += CheckArr(nc_gslv.passive_branch_data.X, nc_gc.passive_branch_data.X, tol, 'PassiveBranchData', 'x')
    errors += CheckArr(nc_gslv.passive_branch_data.G, nc_gc.passive_branch_data.G, tol, 'PassiveBranchData', 'g')
    errors += CheckArr(nc_gslv.passive_branch_data.B, nc_gc.passive_branch_data.B, tol, 'PassiveBranchData', 'b')
    errors += CheckArr(nc_gslv.passive_branch_data.virtual_tap_f, nc_gc.passive_branch_data.virtual_tap_f, tol,
                       'PassiveBranchData', 'vtap_f')
    errors += CheckArr(nc_gslv.passive_branch_data.virtual_tap_t, nc_gc.passive_branch_data.virtual_tap_t, tol,
                       'PassiveBranchData', 'vtap_t')

    errors += CheckArr(nc_gslv.active_branch_data.tap_module, nc_gc.active_branch_data.tap_module, tol,
                       'BranchData', 'tap_module')
    errors += CheckArr(nc_gslv.active_branch_data.tap_angle, nc_gc.active_branch_data.tap_angle, tol,
                       'BranchData', 'tap_angle')

    # VSC data
    errors += compare_branch_parent_data(nc_gslv.vsc_data, nc_gc.vsc_data, tol, "VscData")
    errors += CheckArr(nc_gslv.vsc_data.alpha1, nc_gc.vsc_data.alpha1, tol, 'VscData', 'alpha1')
    errors += CheckArr(nc_gslv.vsc_data.alpha2, nc_gc.vsc_data.alpha2, tol, 'VscData', 'alpha2')
    errors += CheckArr(nc_gslv.vsc_data.alpha3, nc_gc.vsc_data.alpha3, tol, 'VscData', 'alpha3')

    errors += CheckArrEq(convert_gslv_arr_to_idx(np.array(nc_gslv.vsc_data.control1), converter_control_type_dict),
                         nc_gc.vsc_data.control1_int,
                         'VscData', 'control1')
    errors += CheckArrEq(convert_gslv_arr_to_idx(np.array(nc_gslv.vsc_data.control2), converter_control_type_dict),
                         nc_gc.vsc_data.control2_int,
                         'VscData', 'control2')

    errors += CheckArr(nc_gslv.vsc_data.control1_val, nc_gc.vsc_data.control1_val, tol, 'VscData', 'control1_val')
    errors += CheckArr(nc_gslv.vsc_data.control2_val, nc_gc.vsc_data.control2_val, tol, 'VscData', 'control2_val')

    errors += CheckArrEq(nc_gslv.vsc_data.control1_bus_idx, nc_gc.vsc_data.control1_bus_idx, 'VscData',
                         'control1_bus_idx')
    errors += CheckArrEq(nc_gslv.vsc_data.control2_bus_idx, nc_gc.vsc_data.control2_bus_idx, 'VscData',
                         'control2_bus_idx')
    errors += CheckArrEq(nc_gslv.vsc_data.control1_branch_idx, nc_gc.vsc_data.control1_branch_idx, 'VscData',
                         'control1_branch_idx')
    errors += CheckArrEq(nc_gslv.vsc_data.control2_branch_idx, nc_gc.vsc_data.control2_branch_idx, 'VscData',
                         'control2_branch_idx')

    # HVDC data
    errors += compare_branch_parent_data(nc_gslv.hvdc_data, nc_gc.hvdc_data, tol, "HvdcData")
    errors += CheckArrEq(nc_gslv.hvdc_data.dispatchable, nc_gc.hvdc_data.dispatchable,
                         'HvdcData', 'dispatchable')
    errors += CheckArr(nc_gslv.hvdc_data.r, nc_gc.hvdc_data.r, tol, 'HvdcData', 'r')
    errors += CheckArr(nc_gslv.hvdc_data.Pset, nc_gc.hvdc_data.Pset, tol, 'HvdcData', 'Pset')
    errors += CheckArr(nc_gslv.hvdc_data.Pt, nc_gc.hvdc_data.Pt, tol, 'HvdcData', 'Pt')
    errors += CheckArr(nc_gslv.hvdc_data.Vset_f, nc_gc.hvdc_data.Vset_f, tol, 'HvdcData', 'Vset_f')
    errors += CheckArr(nc_gslv.hvdc_data.Vset_t, nc_gc.hvdc_data.Vset_t, tol, 'HvdcData', 'Vset_t')
    errors += CheckArr(nc_gslv.hvdc_data.Vnf, nc_gc.hvdc_data.Vnf, tol, 'HvdcData', 'Vnf')
    errors += CheckArr(nc_gslv.hvdc_data.Vnt, nc_gc.hvdc_data.Vnt, tol, 'HvdcData', 'Vnt')
    errors += CheckArr(nc_gslv.hvdc_data.angle_droop, nc_gc.hvdc_data.angle_droop, tol, 'HvdcData', 'control1_val')

    errors += CheckArrEq(convert_gslv_arr_to_idx(np.array(nc_gslv.hvdc_data.control_mode), hvdc_control_mode_dict),
                         nc_gc.hvdc_data.control_mode_int,
                         'HvdcData', 'control_mode')

    errors += CheckArr(nc_gslv.hvdc_data.Qmin_f, nc_gc.hvdc_data.Qmin_f, tol, 'HvdcData', 'Qmin_f')
    errors += CheckArr(nc_gslv.hvdc_data.Qmax_f, nc_gc.hvdc_data.Qmax_f, tol, 'HvdcData', 'Qmax_f')
    errors += CheckArr(nc_gslv.hvdc_data.Qmin_t, nc_gc.hvdc_data.Qmin_t, tol, 'HvdcData', 'Qmin_t')
    errors += CheckArr(nc_gslv.hvdc_data.Qmax_t, nc_gc.hvdc_data.Qmax_t, tol, 'HvdcData', 'Qmax_t')

    # generator data
    errors += CheckArrEq(nc_gslv.generator_data.bus_idx, nc_gc.generator_data.bus_idx, 'GenData', 'bus_idx')
    errors += CheckArrEq(nc_gslv.generator_data.active, nc_gc.generator_data.active, 'GenData', 'active')
    errors += CheckArr(nc_gslv.generator_data.p, nc_gc.generator_data.p, tol, 'GenData', 'P')
    # errors += CheckArr(nc_gslv.generator_data.pf, nc_gc.generator_data.pf, tol, 'GenData', 'Pf')
    errors += CheckArr(nc_gslv.generator_data.v, nc_gc.generator_data.v, tol, 'GenData', 'v')
    errors += CheckArr(nc_gslv.generator_data.qmin, nc_gc.generator_data.qmin, tol, 'GenData', 'qmin')
    errors += CheckArr(nc_gslv.generator_data.qmax, nc_gc.generator_data.qmax, tol, 'GenData', 'qmax')

    # load data
    errors += CheckArr(nc_gslv.load_data.bus_idx, nc_gc.load_data.bus_idx, tol, 'LoadData', 'bus_idx')
    errors += CheckArr(nc_gslv.load_data.active, nc_gc.load_data.active.astype(int), tol, 'LoadData', 'active')
    errors += CheckArr(nc_gslv.load_data.S, nc_gc.load_data.S, tol, 'LoadData', 'S')
    errors += CheckArr(nc_gslv.load_data.I, nc_gc.load_data.I, tol, 'LoadData', 'I')
    errors += CheckArr(nc_gslv.load_data.Y, nc_gc.load_data.Y, tol, 'LoadData', 'Y')

    # shunt
    errors += CheckArr(nc_gslv.shunt_data.bus_idx, nc_gc.shunt_data.bus_idx, tol, 'ShuntData', 'bus_idx')
    errors += CheckArrEq(nc_gslv.shunt_data.active, nc_gc.shunt_data.active, 'ShuntData', 'active')
    errors += CheckArr(nc_gslv.shunt_data.Y, nc_gc.shunt_data.Y, tol, 'ShuntData', 'Y')

    # ------------------------------------------------------------------------------------------------------------------
    #  Compare arrays and data
    # ------------------------------------------------------------------------------------------------------------------

    gslv_inj = nc_gslv.get_power_injections()
    gslv_types = nc_gslv.get_simulation_indices(gslv_inj.real)
    gslv_conn = nc_gslv.get_connectivity_matrices()
    gslv_adm = nc_gslv.get_admittance_matrices()

    gc_inj = nc_gc.get_power_injections()
    gc_types = nc_gc.get_simulation_indices(gc_inj)
    gc_conn = nc_gc.get_connectivity_matrices()
    gc_adm = nc_gc.get_admittance_matrices()

    errors += CheckArr(gslv_inj.real, gc_inj.real, tol, 'Pbus', 'P')
    errors += CheckArr(gslv_inj.imag, gc_inj.imag, tol, 'Qbus', 'Q')

    errors += CheckArrEq(np.array(gslv_types.types),
                         convert_arr(gc_types.bus_types, bus_type_dict),
                         'Types', 'bus_types')
    errors += CheckArr(gslv_types.pq, gc_types.pq, tol, 'Types', 'pq')
    errors += CheckArr(gslv_types.pv, gc_types.pv, tol, 'Types', 'pv')
    errors += CheckArr(gslv_types.vd, gc_types.vd, tol, 'Types', 'vd')
    errors += CheckArr(gslv_types.pqv, gc_types.pqv, tol, 'Types', 'pqv')
    errors += CheckArr(gslv_types.p, gc_types.p, tol, 'Types', 'p')

    errors += CheckArr(gslv_conn.Cf.toarray(), gc_conn.Cf.toarray(), tol, 'Connectivity', 'Cf (dense)')
    errors += CheckArr(gslv_conn.Ct.toarray(), gc_conn.Ct.toarray(), tol, 'Connectivity', 'Ct (dense)')
    errors += CheckArr(gslv_conn.Cf.data, gc_conn.Cf.tocsc().data, tol, 'Connectivity', 'Cf')
    errors += CheckArr(gslv_conn.Ct.data, gc_conn.Ct.tocsc().data, tol, 'Connectivity', 'Ct')

    errors += CheckArr(gslv_adm.Ybus.toarray(), gc_adm.Ybus.toarray(), tol, 'Admittances', 'Ybus (dense)')
    errors += CheckArr(gslv_adm.Ybus.data.real, gc_adm.Ybus.tocsc().data.real, tol,
                       'Admittances', 'Ybus (real)')
    errors += CheckArr(gslv_adm.Ybus.data.imag, gc_adm.Ybus.tocsc().data.imag, tol,
                       'Admittances', 'Ybus (imag)')
    errors += CheckArr(gslv_adm.Yf.data.real, gc_adm.Yf.tocsc().data.real, tol, 'Admittances', 'Yf (real)')
    errors += CheckArr(gslv_adm.Yf.data.imag, gc_adm.Yf.tocsc().data.imag, tol, 'Admittances', 'Yf (imag)')
    errors += CheckArr(gslv_adm.Yt.data.real, gc_adm.Yt.tocsc().data.real, tol, 'Admittances', 'Yt (real)')
    errors += CheckArr(gslv_adm.Yt.data.imag, gc_adm.Yt.tocsc().data.imag, tol, 'Admittances', 'Yt (imag)')

    return errors
