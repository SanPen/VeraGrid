# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Sequence
import numpy as np
import pandas as pd
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_advanced_formulation import (
    PfAdvancedFormulation)
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Compilers.circuit_to_data import compile_numerical_circuit_at
from VeraGridEngine.enumerations import EngineType, BusMode, BranchImpedanceMode
from VeraGridEngine.basic_structures import Logger


def PackDf(data: np.ndarray,
           columns: Sequence,
           index: Sequence,
           enumerate_index: bool = True,
           enumerate_cols: bool = False) -> pd.DataFrame:
    """
    Function to wrap DataFrame creation with index re-enumeration for easy reading
    :param data:
    :param columns:
    :param index:
    :param enumerate_index:
    :param enumerate_cols:
    :return: DataFrame
    """
    return pd.DataFrame(data=data,
                        columns=[f"{i}:{val}" for i, val in enumerate(columns)] if enumerate_cols else columns,
                        index=[f"{i}:{val}" for i, val in enumerate(index)] if enumerate_index else index
                        )


class CompiledArraysModule:
    available_structures = {
        "Bus arrays": [
            'V', 'Va', 'Vm',
            'S', 'P', 'Q',
            'I',
            'Y',
            'Qmin',
            'Qmax',
        ],
        "Bus indices": [
            'Types',
            'bus_ctrl',
            'pq',
            'pqv',
            'p',
            'pv',
            'vd',
            # 'pqpv',
        ],
        "Branch arrays": [
            'r',
            'x',
            'g',
            'b',
            'tap_f',
            'tap_t',
            'Pf_set',
            'Qf_set',
            'Pt_set',
            'Qt_set',
        ],

        "System matrices": [
            'Ybus',
            'G',
            'B',
            'Yf',
            'Yt',
            'Bbus',
            'Bf',
            'Cf',
            'Ct',
            "B'",
            "B''",
            'Yshunt',
            'Yseries',
        ],
        "Power flow arrays": [
            'idx_dPf',
            'idx_dQf',
            'idx_dPt',
            'idx_dQt',
            'idx_dVa',
            'idx_dVm',
            'idx_dm',
            'idx_dtau',
            'x0',
            'f(x0)',
            'Jacobian',
        ]
    }

    def __init__(self, grid: MultiCircuit,
                 t_idx: int | None,
                 engine: EngineType,
                 apply_temperature=False,
                 branch_tolerance_mode=BranchImpedanceMode.Specified,
                 use_stored_guess=False,
                 control_taps_modules: bool = True,
                 control_taps_phase: bool = True,
                 control_remote_voltage: bool = True,
                 fill_gep: bool = False,
                 fill_three_phase: bool = False):
        """

        :param grid:
        :param t_idx:
        :param engine:
        :param apply_temperature:
        :param branch_tolerance_mode:
        :param use_stored_guess:
        :param control_taps_modules:
        :param control_taps_phase:
        :param control_remote_voltage:
        :param fill_gep:
        :param fill_three_phase:
        """
        self.grid = grid

        if engine == EngineType.VeraGrid:
            nc = compile_numerical_circuit_at(
                circuit=self.grid,
                t_idx=t_idx,
                apply_temperature=apply_temperature,
                branch_tolerance_mode=branch_tolerance_mode,
                use_stored_guess=use_stored_guess,
                control_taps_phase=control_taps_phase,
                control_taps_modules=control_taps_modules,
                control_remote_voltage=control_remote_voltage,
                fill_gep=fill_gep,
                fill_three_phase=fill_three_phase,
            )
            self.islands = nc.split_into_islands()

        elif engine == EngineType.Bentayga:
            import VeraGridEngine.Compilers.circuit_to_bentayga as ben
            self.calculation_inputs_to_display = ben.get_snapshots_from_bentayga(self.grid)

        elif engine == EngineType.NewtonPA:
            import VeraGridEngine.Compilers.circuit_to_newton_pa as ne
            self.calculation_inputs_to_display = ne.get_snapshots_from_newtonpa(self.grid)

        else:
            # fallback to VeraGrid
            nc = compile_numerical_circuit_at(self.grid)
            self.islands = nc.split_into_islands()

    def get_structure(self, idx: int, structure_type: str) -> pd.DataFrame:
        """
        Get a DataFrame with the input.
        :param: structure_type: String representing structure type
        :return: pandas DataFrame
        """
        island = self.islands[idx]

        Sbus = island.get_power_injections_pu()
        idx = island.get_simulation_indices(Sbus=Sbus)

        Qmax_bus, Qmin_bus = island.get_reactive_power_limits()

        formulation = PfAdvancedFormulation(V0=island.bus_data.Vbus,
                                            S0=Sbus,
                                            I0=island.get_current_injections_pu(),
                                            Y0=island.get_admittance_injections_pu(),
                                            Qmin=Qmin_bus,
                                            Qmax=Qmax_bus,
                                            nc=island,
                                            options=PowerFlowOptions(),
                                            logger=Logger())

        if structure_type == 'V':
            df = PackDf(
                data=island.bus_data.Vbus,
                columns=['Voltage (p.u.)'],
                index=island.bus_data.names,
            )

        elif structure_type == 'Va':
            df = PackDf(
                data=np.angle(island.bus_data.Vbus),
                columns=['Voltage angles (rad)'],
                index=island.bus_data.names,
            )
        elif structure_type == 'Vm':
            df = PackDf(
                data=np.abs(island.bus_data.Vbus),
                columns=['Voltage modules (p.u.)'],
                index=island.bus_data.names,
            )
        elif structure_type == 'S':
            df = PackDf(
                data=Sbus,
                columns=['Power (p.u.)'],
                index=island.bus_data.names,
            )

        elif structure_type == 'P':
            df = PackDf(
                data=Sbus.real,
                columns=['Power (p.u.)'],
                index=island.bus_data.names,
            )

        elif structure_type == 'Q':
            df = PackDf(
                data=Sbus.imag,
                columns=['Power (p.u.)'],
                index=island.bus_data.names,
            )

        elif structure_type == 'I':
            df = PackDf(
                data=island.get_current_injections_pu(),
                columns=['Current (p.u.)'],
                index=island.bus_data.names,
            )

        elif structure_type == 'Y':
            df = PackDf(
                data=island.get_admittance_injections_pu(),
                columns=['Admittance (p.u.)'],
                index=island.bus_data.names,
            )

        elif structure_type == 'Ybus':
            adm = island.get_admittance_matrices()
            df = PackDf(
                data=adm.Ybus.toarray(),
                columns=island.bus_data.names,
                index=island.bus_data.names,
            )

        elif structure_type == 'G':
            adm = island.get_admittance_matrices()
            df = PackDf(
                data=adm.Ybus.real.toarray(),
                columns=island.bus_data.names,
                index=island.bus_data.names,
            )

        elif structure_type == 'B':
            adm = island.get_admittance_matrices()
            df = PackDf(
                data=adm.Ybus.imag.toarray(),
                columns=island.bus_data.names,
                index=island.bus_data.names,
            )

        elif structure_type == 'Yf':
            adm = island.get_admittance_matrices()
            df = PackDf(
                data=adm.Yf.toarray(),
                columns=island.bus_data.names,
                index=island.passive_branch_data.names,
            )

        elif structure_type == 'Yt':
            adm = island.get_admittance_matrices()
            df = PackDf(
                data=adm.Yt.toarray(),
                columns=island.bus_data.names,
                index=island.passive_branch_data.names,
            )

        elif structure_type == 'Bbus':
            adm = island.get_linear_admittance_matrices(idx)
            df = PackDf(
                data=adm.Bbus.toarray(),
                columns=island.bus_data.names,
                index=island.bus_data.names,
            )

        elif structure_type == 'Bf':
            adm = island.get_linear_admittance_matrices(idx)
            df = PackDf(
                data=adm.Bf.toarray(),
                columns=island.bus_data.names,
                index=island.passive_branch_data.names,
            )

        elif structure_type == 'Cf':
            df = PackDf(
                data=island.passive_branch_data.Cf.toarray(),
                columns=island.bus_data.names,
                index=island.passive_branch_data.names,
            )

        elif structure_type == 'Ct':
            df = PackDf(
                data=island.passive_branch_data.Ct.toarray(),
                columns=island.bus_data.names,
                index=island.passive_branch_data.names,
            )

        elif structure_type == 'Yshunt':
            df = PackDf(
                data=island.get_Yshunt_bus_pu(),
                columns=['Shunt admittance (p.u.)'],
                index=island.bus_data.names,
            )

        elif structure_type == 'Yseries':
            adms = island.get_series_admittance_matrices()
            df = PackDf(
                data=adms.Yseries.toarray(),
                columns=island.bus_data.names,
                index=island.bus_data.names,
            )

        elif structure_type == "B'":
            adm = island.get_fast_decoupled_amittances()

            if adm.B1.shape[0] == len(idx.pq):
                data = adm.B1.toarray()
                names = island.bus_data.names[idx.pq]
            else:
                data = adm.B1[np.ix_(idx.pq, idx.pq)].toarray()
                names = island.bus_data.names[idx.pq]

            df = PackDf(
                data=data,
                columns=names,
                index=names,
            )

        elif structure_type == "B''":
            adm = island.get_fast_decoupled_amittances()

            if adm.B2.shape[0] == len(idx.pq):
                data = adm.B2.toarray()
                names = island.bus_data.names[idx.pq]
            else:
                data = adm.B2[np.ix_(idx.pq, idx.pq)].toarray()
                names = island.bus_data.names[idx.pq]

            df = PackDf(
                data=data,
                columns=names,
                index=names,
            )

        elif structure_type == 'Types':
            data = island.bus_data.bus_types
            df = PackDf(
                data=data,
                columns=['Bus types'],
                index=island.bus_data.names,
            )

        elif structure_type == 'x0':
            df = PackDf(
                data=formulation.var2x(),
                columns=['x0'],
                index=formulation.get_x_names(),
            )

        elif structure_type == 'f(x0)':
            df = PackDf(
                data=formulation.fx(),
                columns=['f(x0)'],
                index=formulation.get_fx_names(),
            )

        elif structure_type == 'Jacobian':
            df = formulation.get_jacobian_df(autodiff=False)

        elif structure_type == 'Qmin':
            df = PackDf(
                data=Qmin_bus,
                columns=['Qmin'],
                index=island.bus_data.names,
            )

        elif structure_type == 'Qmax':
            df = PackDf(
                data=Qmax_bus,
                columns=['Qmax'],
                index=island.bus_data.names,
            )

        elif structure_type == 'bus_ctrl':
            data1 = [BusMode.as_str(val) for val in island.bus_data.bus_types]

            df = PackDf(
                data=np.array(data1),
                columns=['bus_ctrl'],
                index=island.bus_data.names,
            )

        elif structure_type == 'branch_ctrl':

            data1 = [val.value if val != 0 else "-" for val in island.active_branch_data.tap_module_control_mode]
            data2 = [val.value if val != 0 else "-" for val in island.active_branch_data.tap_phase_control_mode]

            df = PackDf(
                data=np.c_[
                    island.passive_branch_data.F,
                    island.passive_branch_data.T,
                    island.active_branch_data.tap_controlled_buses,
                    data1,
                    data2
                ],
                columns=['bus F', 'bus T', 'V ctrl bus', 'm control', 'tau control'],
                index=[f"{k}) {name}" for k, name in enumerate(island.passive_branch_data.names)],
            )

        elif structure_type == 'pq':
            df = PackDf(
                data=idx.pq.astype(int).astype(str),
                columns=['pq'],
                index=island.bus_data.names[idx.pq],
            )

        elif structure_type == 'pv':
            df = PackDf(
                data=idx.pv.astype(int).astype(str),
                columns=['pv'],
                index=island.bus_data.names[idx.pv],
            )

        elif structure_type == 'pqv':
            df = PackDf(
                data=idx.pqv.astype(int).astype(str),
                columns=['pqv'],
                index=island.bus_data.names[idx.pqv],
            )

        elif structure_type == 'p':
            df = PackDf(
                data=idx.p.astype(int).astype(str),
                columns=['p'],
                index=island.bus_data.names[idx.p],
            )

        elif structure_type == 'vd':
            df = PackDf(
                data=idx.vd.astype(int).astype(str),
                columns=['vd'],
                index=island.bus_data.names[idx.vd],
            )

        elif structure_type == 'r':
            df = PackDf(
                data=island.passive_branch_data.R,
                columns=['Resistance (p.u.)'],
                index=island.passive_branch_data.names,
            )

        elif structure_type == 'x':
            df = PackDf(
                data=island.passive_branch_data.X,
                columns=['Reactance (p.u.)'],
                index=island.passive_branch_data.names,
            )

        elif structure_type == 'g':
            df = PackDf(
                data=island.passive_branch_data.G,
                columns=['Conductance (p.u.)'],
                index=island.passive_branch_data.names,
            )

        elif structure_type == 'b':
            df = PackDf(
                data=island.passive_branch_data.B,
                columns=['Susceptance (p.u.)'],
                index=island.passive_branch_data.names,
            )
        elif structure_type == 'tap_f':
            df = PackDf(
                data=island.passive_branch_data.virtual_tap_f,
                columns=['Virtual tap from (p.u.)'],
                index=island.passive_branch_data.names,
            )

        elif structure_type == 'tap_t':
            df = PackDf(
                data=island.passive_branch_data.virtual_tap_t,
                columns=['Virtual tap to (p.u.)'],
                index=island.passive_branch_data.names,
            )


        elif structure_type == 'idx_dPf':
            df = PackDf(
                data=formulation.idx_dPf.astype(int).astype(str),
                columns=['idx_dPf'],
                index=island.passive_branch_data.names[formulation.idx_dPf],
            )

        elif structure_type == 'idx_dQf':
            df = PackDf(
                data=formulation.idx_dQf.astype(int).astype(str),
                columns=['idx_dQf'],
                index=island.passive_branch_data.names[formulation.idx_dQf],
            )

        elif structure_type == 'idx_dPt':
            df = PackDf(
                data=formulation.idx_dPt.astype(int).astype(str),
                columns=['idx_dPt'],
                index=island.passive_branch_data.names[formulation.idx_dPt],
            )

        elif structure_type == 'idx_dQt':
            df = PackDf(
                data=formulation.idx_dQt.astype(int).astype(str),
                columns=['idx_dQt'],
                index=island.passive_branch_data.names[formulation.idx_dQt],
            )

        elif structure_type == 'idx_dVa':
            df = PackDf(
                data=formulation.idx_dVa.astype(int).astype(str),
                columns=['idx_dVa'],
                index=island.bus_data.names[formulation.idx_dVa],
            )

        elif structure_type == 'idx_dVm':
            df = PackDf(
                data=formulation.idx_dVm.astype(int).astype(str),
                columns=['idx_dVm'],
                index=island.bus_data.names[formulation.idx_dVm],
            )

        elif structure_type == 'idx_dm':
            df = PackDf(
                data=formulation.idx_dm.astype(int).astype(str),
                columns=['idx_dm'],
                index=island.passive_branch_data.names[formulation.idx_dm],
            )

        elif structure_type == 'idx_dtau':
            df = PackDf(
                data=formulation.idx_dtau.astype(int).astype(str),
                columns=['idx_dtau'],
                index=island.passive_branch_data.names[formulation.idx_dtau],
            )

        elif structure_type == 'Pf_set':
            df = PackDf(
                data=island.active_branch_data.Pset[formulation.idx_dPf],
                columns=['Pf_set'],
                index=island.passive_branch_data.names[formulation.idx_dPf],
            )

        elif structure_type == 'Pt_set':
            df = PackDf(
                data=island.active_branch_data.Pset[formulation.idx_dPt],
                columns=['Pt_set'],
                index=island.passive_branch_data.names[formulation.idx_dPt],
            )

        elif structure_type == 'Qf_set':
            df = PackDf(
                data=island.active_branch_data.Qset[formulation.idx_dQf],
                columns=['Qf_set'],
                index=island.passive_branch_data.names[formulation.idx_dQf],
            )

        elif structure_type == 'Qt_set':
            df = PackDf(
                data=island.active_branch_data.Qset[formulation.idx_dQt],
                columns=['Qt_set'],
                index=island.passive_branch_data.names[formulation.idx_dQt],
            )

        else:
            raise Exception('PF input: structure type not found' + str(structure_type))

        return df

    def export_to_excel(self, file_name: str):
        """
        Export all to Excel
        :param file_name: file name
        :return: 
        """
        if not file_name.endswith('.xlsx'):
            file_name += '.xlsx'

        with pd.ExcelWriter(file_name) as writer:  # pylint: disable=abstract-class-instantiated

            for c, calc_input in enumerate(self.islands):

                for category, elms_in_category in self.available_structures.items():
                    for elm_type in elms_in_category:
                        name = f"{category}_{elm_type}@{c}"
                        df = self.get_structure(idx=c, structure_type=elm_type).astype(str)

                        if isinstance(df, pd.DataFrame):
                            df.to_excel(excel_writer=writer,
                                        sheet_name=name[:31])  # excel supports 31 chars per sheet name

