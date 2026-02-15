# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import os
import pandas as pd
import numpy as np

from VeraGridEngine.IO.file_open import FileOpen
from VeraGridEngine.Simulations.PowerFlow.power_flow_worker import PowerFlowOptions
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import SolverType
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import PowerFlowDriver


def test_dgs_ieee_grids():
    """
    Checks the .DGS files of IEEE grids against the PSS/e results
    This test checks 2 things:
    - DGS import fidelity
    - PSS/e vs VeraGrid results
    :return: Nothing if ok, fails if not
    """

    files = [
        ('IEEE14_test.dgs', 'IEEE 14 bus.sav.xlsx'),
        ('IEEE30_test.dgs', 'IEEE 30 bus.sav.xlsx'),
        ('IEEE118_v2_test.dgs', 'IEEE 118 Bus.sav.xlsx'),
    ]

    for solver_type in [SolverType.NR,
                        SolverType.IWAMOTO,
                        SolverType.LM,
                        SolverType.FASTDECOUPLED,
                        SolverType.PowellDogLeg,
                        SolverType.HELM]:

        print(solver_type)

        options = PowerFlowOptions(solver_type,
                                   verbose=0,
                                   control_q=False,
                                   retry_with_other_methods=False)

        for f1, f2 in files:
            print(f1, end=' ')

            fname = os.path.join('data', 'grids', 'DGS', f1)

            main_circuit = FileOpen(fname).open()
            power_flow = PowerFlowDriver(main_circuit, options)
            power_flow.run()

            # reference results are stored under src/tests/data/results
            results_file = os.path.join('data', 'results', f2)

            # load the associated results file
            df_v = pd.read_excel(results_file, sheet_name='Vabs', index_col=0)
            df_p = pd.read_excel(results_file, sheet_name='Pbranch', index_col=0)

            v_gc = np.abs(power_flow.results.voltage)
            v_psse = df_v.values[:, 0]
            p_gc = power_flow.results.Sf.real
            p_psse = df_p.values[:, 0]

            v_ok = np.allclose(v_gc, v_psse, atol=1e-4)
            flow_ok = np.allclose(p_gc, p_psse, atol=1e-2)
            if not v_ok:
                print('power flow voltages test for {} failed'.format(fname))
            if not flow_ok:
                print('power flow flows test for {} failed'.format(fname))

            assert v_ok
            #assert flow_ok

        print(solver_type, 'ok')
