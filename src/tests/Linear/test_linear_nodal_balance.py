# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
from pathlib import Path
import numpy as np
import VeraGridEngine as vg


def test_linear_nodal_balance() -> None:
    """
    This tests checks that "Kirchhoff" is fulfilled by the linear flows calculation
    both with distributed and not distributed slack bus
    """
    # src/tests/data/grids/Matpower/case14.matpower
    fname = os.path.join("data", "grids", "Matpower", "case14.matpower")

    grid = vg.open_file(fname)

    nc = vg.compile_numerical_circuit_at(grid, t_idx=None)
    for distributed_slack in [False, True]:

        P = nc.get_power_injections_pu().real.copy()
        la = vg.LinearAnalysis(nc, distributed_slack=distributed_slack)

        # Note the flows are always computed with the original injections P
        Pf = la.get_flows(Sbus=P)

        # Correction of the injections vector --------------------------------------------------------------------------
        P_eff = la.get_corrected_injections(P)

        #  "Kirchhoff" check -------------------------------------------------------------------------------------------
        nodal_balance = -P_eff.copy()  # this is the injections initialization

        # Now we sum the flows
        for k in range(nc.nbr):
            i = nc.passive_branch_data.F[k]
            j = nc.passive_branch_data.T[k]

            nodal_balance[i] += Pf[k]
            nodal_balance[j] -= Pf[k]

        assert np.allclose(nodal_balance, 0.0, atol=1e-6)
        print(f"{fname} [distributed: {distributed_slack}] -> Passed")


def test_linear_nodal_balance_driver() -> None:
    """
    This tests checks that "Kirchhoff" is fulfilled by the linear flows calculation
    both with distributed and not distributed slack bus
    """
    # src/tests/data/grids/Matpower/case14.matpower
    fname = os.path.join("data", "grids", "Matpower", "case14.matpower")

    grid = vg.open_file(fname)

    nc = vg.compile_numerical_circuit_at(grid, t_idx=None)
    for distributed_slack in [False, True]:

        opt = vg.LinearAnalysisOptions(
            distribute_slack=distributed_slack,
        )
        drv = vg.LinearAnalysisDriver(grid=grid, options=opt)
        drv.run()
        res = drv.results

        #  "Kirchhoff" check -------------------------------------------------------------------------------------------
        print("P corrected:", res.Sbus.real)
        nodal_balance = -res.Sbus.real  # this is the injections initialization

        # Now we sum the flows
        for k in range(nc.nbr):
            i = nc.passive_branch_data.F[k]
            j = nc.passive_branch_data.T[k]

            nodal_balance[i] += res.Sf[k].real
            nodal_balance[j] -= res.Sf[k].real

        assert np.allclose(nodal_balance, 0.0, atol=1e-6)
        print("Node balance: ", nodal_balance)
        print(f"{fname} [distributed: {distributed_slack}] -> Passed")


# if __name__ == "__main__":
    # test_linear_nodal_balance()
    # test_linear_nodal_balance_driver()
