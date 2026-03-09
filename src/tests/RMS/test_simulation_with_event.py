# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import pandas as pd
from pandas.testing import assert_frame_equal

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import get_complete_generator_template
from VeraGridEngine.Templates.Rms.bus_rms_template import initialize_bus_rms

from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, DynamicIntegrationMethod, RmsInitializationMethod, ResultTypes
from VeraGridEngine.Devices.Aggregation import RmsEvent
import VeraGridEngine.api as gce


def find_name_in_block(name: str, block: Block):
    for var in block.algebraic_vars + block.state_vars + list(block.event_dict.keys()):
        if name == var.name:
            return var

    for mdl in block.children:
        res = find_name_in_block(name, mdl)
        if res is not None:
            return res

def test_simulation_with_event():
    """
    This test creates a grid, adds rms models and events and rens simulation. Then it compares results with reference.
    :return:
    :rtype:
    """

    #########
    # retrieve reference results df

    folder = os.path.join('data', 'dynamics')
    name = "simulation_with_event.csv"

    fname = os.path.join(folder, name)

    reference_df = pd.read_csv(fname)

    ###########################################################################################################################
    # Build VeraGrid object




    grid = gce.MultiCircuit(Sbase=100, fbase=50.0)

    # Buses
    bus0 = gce.Bus(name="Bus0", Vnom=10, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=10)

    grid.add_bus(bus0)
    grid.add_bus(bus1)

    for bus in grid.buses:
        initialize_bus_rms(bus, vf=grid.var_factory)

    # Lines
    line0 = gce.Line(name="line 0-2", bus_from=bus0, bus_to=bus1, r=0.029585798816568046, x=0.07100591715976332, b=0.03,
                     rate=900.0)

    # load
    load = gce.Load(P=9.999999, Q=0.999999)

    # Generators
    gen0 = gce.Generator(name="Gen0", P=10, vset=1.0, Snom=900,
                         x1=0.86138701, r1=0.3, freq=50.0,
                         M=10.0,
                         D=1.0,
                         omega_ref=1.0,
                         Kp=1.0,
                         Ki=10.0,
                         )

    ######################################################################################################
    # Build Rms models
    ######################################################################################################

    # generator
    genqec_mdl = get_complete_generator_template(grid.var_factory).block

    # line
    line_mdl = get_line_rms_template(grid.var_factory).block

    # load
    load_mdl = get_load_rms_template(grid.var_factory).block

    # connection with buses

    genqec_mdl.connect([genqec_mdl.in_vars[0]], [bus0.rms_model.model.out_vars[0]])
    genqec_mdl.connect([genqec_mdl.in_vars[1]], [bus0.rms_model.model.out_vars[1]])

    line_mdl.connect([line_mdl.in_vars[0]], [bus0.rms_model.model.out_vars[0]])
    line_mdl.connect([line_mdl.in_vars[1]], [bus0.rms_model.model.out_vars[1]])

    line_mdl.connect([line_mdl.in_vars[2]], [bus1.rms_model.model.out_vars[0]])
    line_mdl.connect([line_mdl.in_vars[3]], [bus1.rms_model.model.out_vars[1]])

    # u_gov = find_name_in_block("u_gov1", gov1_mdl)

    load_mdl.connect([load_mdl.in_vars[0]], [bus1.rms_model.model.out_vars[0]])
    load_mdl.connect([load_mdl.in_vars[1]], [bus1.rms_model.model.out_vars[1]])

    # external mapping

    big_gen1 = Block(children=[genqec_mdl])

    big_gen1.external_mapping.update({VarPowerFlowRefferenceType.P: genqec_mdl.out_vars[0]})
    big_gen1.external_mapping.update({VarPowerFlowRefferenceType.Q: genqec_mdl.out_vars[1]})

    # add models to dyn_host
    line0.rms_model.model = line_mdl
    load.rms_model.model = load_mdl
    gen0.rms_model.model = big_gen1

    # apply event
    Pl0 = find_name_in_block('Pl0', load_mdl)
    event = RmsEvent(device=load, parameter=Pl0, time=0.1, value=-0.09)
    grid.add_rms_event(event)

    grid.add_line(line0)
    grid.add_load(bus=bus1, api_obj=load)
    grid.add_generator(bus=bus0, api_obj=gen0)


    options = gce.PowerFlowOptions(
        solver_type=gce.SolverType.NR,
        retry_with_other_methods=False,
        verbose=0,
        initialize_with_existing_solution=True,
        tolerance=1e-6,
        max_iter=25,
        control_q=False,
        control_taps_modules=True,
        control_taps_phase=True,
        control_remote_voltage=True,
        orthogonalize_controls=True,
        apply_temperature_correction=True,
        branch_impedance_tolerance_mode=gce.BranchImpedanceMode.Specified,
        distributed_slack=False,
        ignore_single_node_islands=False,
        trust_radius=1.0,
        backtracking_parameter=0.05,
        use_stored_guess=False,
        initialize_angles=False,
        generate_report=False,
    )
    res = gce.power_flow(grid, options=options)

    print(f"Converged: {res.converged}")
    print(res.get_bus_df())
    print(res.get_branch_df())

    params_mapping = dict()

    options = RmsOptions(time_step=0.001,
                         simulation_time=1,
                         tolerance=1e-6,
                         integration_method=DynamicIntegrationMethod.DaeBackEuler,
                         initialization_method=RmsInitializationMethod.Explicit,
                         use_init_values=False,
                         max_iter=1000,
                         verbose=0)

    problem = RmsProblemDae(grid=grid,
                            options=options,
                            pf_results=res)

    solver = BackEulerImplicitIntegration(
        problem=problem,
        t0=0,
        t_end=options.simulation_time,
        h=options.time_step,
        max_iter=options.max_iter
    )

    t, y, well_initialized, converged = solver.simulate()
    cols = [f"var{i}" for i in range(0, y.shape[1])]
    results_df = pd.DataFrame(y, columns=cols)

    results_df = results_df[reference_df.columns]

    assert_frame_equal(
        results_df.reset_index(drop=True),
        reference_df.reset_index(drop=True),
        check_dtype=False,
        check_index_type=False,
        atol=1e-6
    )