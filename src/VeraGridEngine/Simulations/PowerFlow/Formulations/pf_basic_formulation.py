# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple, List
import numpy as np
from VeraGridEngine.DataStructures.numerical_circuit import NumericalCircuit
from VeraGridEngine.Topology.admittance_matrices import AdmittanceMatrices
from VeraGridEngine.Simulations.PowerFlow.power_flow_results import NumericPowerFlowResults
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Derivatives.ac_jacobian import create_J_vc_csc
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import (compute_fx_error,
                                                                                    power_flow_post_process_nonlinear)
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.discrete_controls import (control_q_inside_method,
                                                                                     compute_slack_distribution)
from VeraGridEngine.Simulations.PowerFlow.Formulations.pf_formulation_template import PfFormulationTemplate
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import (compute_zip_power, compute_power,
                                                                                    compute_fx, polar_to_rect)
from VeraGridEngine.Topology.simulation_indices import compile_types
from VeraGridEngine.basic_structures import Vec, IntVec, CxVec
from VeraGridEngine.Utils.Sparse.csc2 import CSC
from VeraGridEngine.enumerations import ShuntControlMode


class PfBasicFormulation(PfFormulationTemplate):

    def __init__(self, V0: CxVec, S0: CxVec, I0: CxVec, Y0: CxVec, Qmin: Vec, Qmax: Vec,
                 nc: NumericalCircuit, options: PowerFlowOptions):
        """

        :param V0:
        :param S0:
        :param I0:
        :param Y0:
        :param Qmin:
        :param Qmax:
        :param options:
        """
        PfFormulationTemplate.__init__(self, V0=V0, options=options)

        self.nc = nc
        self.adm: AdmittanceMatrices = nc.get_admittance_matrices()
        if options.verbose > 1:
            print(f"Ybus: \n {self.adm.Ybus.toarray()}")
        self.S0: CxVec = S0
        self.I0: CxVec = I0
        self.Y0: CxVec = Y0

        self.Qmin = Qmin
        self.Qmax = Qmax

        self.vd, self.pq, self.pv, self.pqv, self.p, self.no_slack = compile_types(
            Pbus=S0.real,
            types=self.nc.bus_data.bus_types
        )

        self.idx_dVa = np.r_[self.pv, self.pq, self.pqv, self.p]
        self.idx_dVm = np.r_[self.pq, self.p]
        self.idx_dP = self.idx_dVa
        self.idx_dQ = np.r_[self.pq, self.pqv]

        self.buses_with_discrete_shunts_control: List[Tuple[int, int]] = list()
        self.shunt_step = self.nc.shunt_data.step.copy()
        for sh_i, bus_i in enumerate(self.nc.shunt_data.bus_idx):
            if self.nc.shunt_data.control_mode[sh_i] == ShuntControlMode.Discrete:
                self.buses_with_discrete_shunts_control.append((bus_i, sh_i))

    def x2var(self, x: Vec):
        """
        Convert X to decision variables
        :param x: solution vector
        """
        a = len(self.idx_dVa)
        b = a + len(self.idx_dVm)

        # update the vectors
        self.Va[self.idx_dVa] = x[0:a]
        self.Vm[self.idx_dVm] = x[a:b]

    def var2x(self) -> Vec:
        """
        Convert the internal decission variables into the vector
        :return: Vector
        """
        return np.r_[
            self.Va[self.idx_dVa],
            self.Vm[self.idx_dVm]
        ]

    def update_bus_types(self, pq: IntVec, pv: IntVec, pqv: IntVec, p: IntVec):
        """

        :param pq:
        :param pv:
        :param pqv:
        :param p:
        :return:
        """
        self.pq = pq
        self.pv = pv
        self.pqv = pqv
        self.p = p

        self.idx_dVa = np.r_[self.pv, self.pq, self.pqv, self.p]
        self.idx_dVm = np.r_[self.pq, self.p]
        self.idx_dP = self.idx_dVa
        self.idx_dQ = np.r_[self.pq, self.pqv]

    def size(self) -> int:
        """
        Size of the jacobian matrix
        :return:
        """
        return len(self.idx_dVa) + len(self.idx_dVm)

    def check_error(self, x: Vec) -> Tuple[float, Vec]:
        """
        Check error of the solution without affecting the problem
        :param x: Solution vector
        :return: error
        """
        a = len(self.idx_dVa)
        b = a + len(self.idx_dVm)

        # update the vectors
        Va = self.Va.copy()
        Vm = self.Vm.copy()
        Va[self.idx_dVa] = x[0:a]
        Vm[self.idx_dVm] = x[a:b]

        # compute the complex voltage
        V = polar_to_rect(Vm, Va)

        # compute the function residual
        # Assumes the internal vars were updated already with self.x2var()
        Sbus = compute_zip_power(self.S0, self.I0, self.Y0, Vm)
        Scalc = compute_power(self.adm.Ybus, V)
        dS = Scalc - Sbus  # compute the mismatch
        _f = np.r_[
            dS[self.idx_dP].real,
            dS[self.idx_dQ].imag
        ]
        
        # compute the error
        return compute_fx_error(_f), x

    def update(self, x: Vec, update_controls: bool = False) -> Tuple[float, bool, Vec, Vec]:
        """
        Update step
        :param x: Solution vector
        :param update_controls:
        :return: error, converged?, x
        """
        # set the problem state
        self.x2var(x)

        # compute the complex voltage
        self.V = polar_to_rect(self.Vm, self.Va)

        # compute the function residual
        # Assumes the internal vars were updated already with self.x2var()
        Sbus = compute_zip_power(self.S0, self.I0, self.Y0, self.Vm)
        self.Scalc = compute_power(self.adm.Ybus, self.V)
        dS = self.Scalc - Sbus  # compute the mismatch
        self._f = np.r_[
            dS[self.idx_dP].real,
            dS[self.idx_dQ].imag
        ]
        # self._f = compute_fx(self.Scalc, Sbus, self.idx_dP, self.idx_dQ)

        # compute the error
        self._error = compute_fx_error(self._f)

        # review reactive power limits
        # it is only worth checking Q limits with a low error
        # since with higher errors, the Q values may be far from realistic
        # finally, the Q control only makes sense if there are pv nodes
        if update_controls and self._error < self._controls_tol:
            any_change = False

            # update Q limits control
            if self.options.control_Q and (len(self.pv) + len(self.p)) > 0:

                # check and adjust the reactive power
                # this function passes pv buses to pq when the limits are violated,
                # but not pq to pv because that is unstable
                changed, pv, pq, pqv, p = control_q_inside_method(self.Scalc, self.S0,
                                                                  self.pv, self.pq,
                                                                  self.pqv, self.p,
                                                                  self.Qmin,
                                                                  self.Qmax)

                if len(changed) > 0:
                    any_change = True

                    # update the bus type lists
                    self.update_bus_types(pq=pq, pv=pv, pqv=pqv, p=p)

                    # the composition of x may have changed, so recompute
                    x = self.var2x()

            # discrete shunt logic
            for bus_i, sh_i in self.buses_with_discrete_shunts_control:
                if self.Vm[bus_i] > self.nc.shunt_data.vmax[sh_i]:
                    # decrease B
                    g_steps: IntVec = self.nc.shunt_data.g_steps[sh_i]
                    b_steps: IntVec = self.nc.shunt_data.b_steps[sh_i]
                    if self.shunt_step[sh_i] > 0:
                        prev_g = g_steps[self.shunt_step[sh_i]] / self.nc.Sbase
                        prev_b = b_steps[self.shunt_step[sh_i]] / self.nc.Sbase
                        self.shunt_step[sh_i] -= 1
                        g = prev_g - g_steps[self.shunt_step[sh_i]] / self.nc.Sbase
                        b = prev_b - b_steps[self.shunt_step[sh_i]] / self.nc.Sbase
                        self.adm.Ybus[bus_i, bus_i] += complex(g, b) - complex(prev_g, prev_b)
                        any_change = True

                elif self.Vm[bus_i] < self.nc.shunt_data.vmin[sh_i]:
                    # increase B
                    g_steps: IntVec = self.nc.shunt_data.g_steps[sh_i]
                    b_steps: IntVec = self.nc.shunt_data.b_steps[sh_i]
                    if self.shunt_step[sh_i] < (len(b_steps) - 1):
                        prev_g = g_steps[self.shunt_step[sh_i]] / self.nc.Sbase
                        prev_b = b_steps[self.shunt_step[sh_i]] / self.nc.Sbase
                        self.shunt_step[sh_i] += 1
                        g = prev_g + g_steps[self.shunt_step[sh_i]] / self.nc.Sbase
                        b = prev_b + b_steps[self.shunt_step[sh_i]] / self.nc.Sbase
                        self.adm.Ybus[bus_i, bus_i] += complex(g, b) - complex(prev_g, prev_b)
                        any_change = True
                else:
                    # within boundaries
                    pass

            # update Slack control
            if self.options.distributed_slack:
                ok, delta = compute_slack_distribution(Scalc=self.Scalc,
                                                       vd=self.vd,
                                                       bus_installed_power=self.nc.bus_data.installed_power)
                if ok:
                    any_change = True
                    # Update the objective power to reflect the slack distribution
                    self.S0 += delta

            if any_change:
                # recompute the error based on the new Scalc and S0
                self._f = self.fx()

                # compute the error
                self._error = compute_fx_error(self._f)

        # converged?
        self._converged = self._error < self.options.tolerance

        return self._error, self._converged, x, self.f

    def fx(self) -> Vec:
        """

        :return:
        """
        # Assumes the internal vars were updated already with self.x2var()
        Sbus = compute_zip_power(self.S0, self.I0, self.Y0, self.Vm)
        self.Scalc = compute_power(self.adm.Ybus, self.V)
        self._f = compute_fx(self.Scalc, Sbus, self.idx_dP, self.idx_dQ)
        return self._f

    def Jacobian(self) -> CSC:
        """

        :return:
        """
        # Assumes the internal vars were updated already with self.x2var()
        if self.adm.Ybus.format != 'csc':
            self.adm.Ybus = self.adm.Ybus.tocsc()

        nbus = self.adm.Ybus.shape[0]

        if self.options.verbose >= 2:
            print("Ybus:")
            print(self.adm.Ybus.toarray())

        # Create J in CSC order
        J = create_J_vc_csc(nbus, self.adm.Ybus.data, self.adm.Ybus.indptr, self.adm.Ybus.indices,
                            self.V, self.idx_dVa, self.idx_dVm, self.idx_dP, self.idx_dQ)

        return J

    def get_x_names(self) -> List[str]:
        """
        Names matching x
        :return:
        """
        cols = [f'dVa {i}' for i in self.idx_dVa]
        cols += [f'dVm {i}' for i in self.idx_dVm]

        return cols

    def get_fx_names(self) -> List[str]:
        """
        Names matching fx
        :return:
        """
        rows = [f'dP {i}' for i in self.idx_dP]
        rows += [f'dQ {i}' for i in self.idx_dQ]

        return rows

    def get_solution(self, elapsed: float, iterations: int) -> NumericPowerFlowResults:
        """
        Get the problem solution
        :param elapsed: Elapsed seconds
        :param iterations: Iteration number
        :return: NumericPowerFlowResults
        """
        # Compute the Branches power and the slack buses power
        Sf, St, If, It, Vbranch, loading, losses, Sbus = power_flow_post_process_nonlinear(
            Sbus=self.Scalc,
            V=self.V,
            F=self.nc.passive_branch_data.F,
            T=self.nc.passive_branch_data.T,
            pv=self.pv,
            vd=self.vd,
            Ybus=self.adm.Ybus,
            Yf=self.adm.Yf,
            Yt=self.adm.Yt,
            Yshunt_bus=self.adm.Yshunt_bus,
            branch_rates=self.nc.passive_branch_data.rates,
            Sbase=self.nc.Sbase
        )

        return NumericPowerFlowResults(V=self.V,
                                       Scalc=Sbus * self.nc.Sbase,
                                       m=self.nc.active_branch_data.tap_module,
                                       tau=self.nc.active_branch_data.tap_angle,
                                       Sf=Sf,
                                       St=St,
                                       If=If,
                                       It=It,
                                       loading=loading,
                                       losses=losses,
                                       Pfp_vsc=np.zeros(self.nc.nvsc, dtype=float),
                                       Pfn_vsc=np.zeros(self.nc.nvsc, dtype=float),
                                       St_vsc=np.zeros(self.nc.nvsc, dtype=complex),
                                       If_vsc=np.zeros(self.nc.nvsc, dtype=float),
                                       It_vsc=np.zeros(self.nc.nvsc, dtype=complex),
                                       losses_vsc=np.zeros(self.nc.nvsc, dtype=float),
                                       loading_vsc=np.zeros(self.nc.nvsc, dtype=float),
                                       Sf_hvdc=np.zeros(self.nc.nhvdc, dtype=complex),
                                       St_hvdc=np.zeros(self.nc.nhvdc, dtype=complex),
                                       losses_hvdc=np.zeros(self.nc.nhvdc, dtype=complex),
                                       loading_hvdc=np.zeros(self.nc.nhvdc, dtype=complex),
                                       norm_f=self.error,
                                       converged=self.converged,
                                       iterations=iterations,
                                       elapsed=elapsed)
