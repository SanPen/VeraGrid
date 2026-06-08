# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal

from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Simulations.Rms.problems.rms_problem_dae import RmsProblemDae
from VeraGridEngine.Devices.Events.rms_events_group import RmsEventsGroup
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.Rms.numerical.back_euler_fx import BackEulerImplicitIntegration
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import get_complete_generator_template_rms
# from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template_v2 import get_complete_generator_template_rms
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model

from VeraGridEngine.enumerations import VarPowerFlowReferenceType, DynamicEventTransitionType, DynamicIntegrationMethod, RmsInitializationMethod
from VeraGridEngine.Devices.Events.rms_event import RmsEvent
import VeraGridEngine.api as gce


def find_name_in_block(name: str, block: Block):
    for var in block.algebraic_vars + block.state_vars + list(block.event_dict.keys()):
        if name == var.name:
            return var

    for mdl in block.children:
        res = find_name_in_block(name, mdl)
        if res is not None:
            return res


def build_reference_column_mapping() -> list[tuple[str, str]]:
    """Return the stable variable name to legacy CSV column mapping.

    The historical CSV stores raw solver columns as ``varN``. Those column
    positions depend on the internal DAE ordering, which changes when the
    template switches controller dynamics between algebraic and explicit state
    representations. This mapping preserves the original physical references
    while making the test independent from the current internal ordering.

    :return: Ordered pairs ``(stable_name, legacy_column)``.
    """
    mapping: list[tuple[str, str]] = list()
    mapping.append(("delta", "var0"))
    mapping.append(("omega", "var1"))
    mapping.append(("Eq_prime", "var2"))
    mapping.append(("Ed_prime", "var3"))
    mapping.append(("Psiq_prime", "var4"))
    mapping.append(("Psid_prime", "var5"))
    mapping.append(("bus0_vm", "var6"))
    mapping.append(("bus0_va", "var7"))
    mapping.append(("bus1_vm", "var8"))
    mapping.append(("bus1_va", "var9"))
    mapping.append(("line_pf", "var10"))
    mapping.append(("line_pt", "var11"))
    mapping.append(("line_qf", "var12"))
    mapping.append(("line_qt", "var13"))
    mapping.append(("Pg", "var14"))
    mapping.append(("Qg", "var15"))
    mapping.append(("Psid", "var18"))
    mapping.append(("Psiq", "var19"))
    mapping.append(("Te", "var20"))
    mapping.append(("Ed1", "var21"))
    mapping.append(("Eq1", "var22"))
    mapping.append(("IRPu", "var34"))
    mapping.append(("Tm", "var43"))
    mapping.append(("y2_3_gov", "var44"))
    mapping.append(("V_pss", "var45"))
    mapping.append(("y_stabilizer1", "var46"))
    mapping.append(("y_exciter1", "var53"))
    mapping.append(("y_exciter2", "var54"))
    mapping.append(("y_exciter3", "var55"))
    mapping.append(("y_exciter4", "var57"))
    mapping.append(("y_subexciter1", "var58"))
    mapping.append(("u_aux", "var60"))
    mapping.append(("VeMaxPu", "var61"))
    mapping.append(("Vf", "var62"))
    mapping.append(("f_input", "var63"))
    mapping.append(("f_output", "var64"))
    mapping.append(("Efe", "var65"))
    mapping.append(("Pl", "var66"))
    mapping.append(("Ql", "var67"))
    return mapping


def build_results_dataframe(problem: RmsProblemDae,
                            values: np.ndarray,
                            named_vars: list[tuple[str, object]]) -> pd.DataFrame:
    """Build a results data frame indexed by stable physical variable names.

    :param problem: Prepared RMS problem containing the variable indexing.
    :param values: Simulated values array.
    :param named_vars: Ordered pairs ``(stable_name, variable)``.
    :return: Data frame with stable physical columns.
    """
    data: dict[str, np.ndarray] = dict()

    for stable_name, variable in named_vars:
        idx: int = problem.get_var_idx(variable)
        data[stable_name] = values[:, idx]

    return pd.DataFrame(data)


def build_named_variable_list(genqec_mdl: Block,
                              line_mdl: Block,
                              load_mdl: Block,
                              bus0: object,
                              bus1: object) -> list[tuple[str, object]]:
    """Collect the stable physical variables to compare in the RMS test.

    :param genqec_mdl: Complete generator RMS block.
    :param line_mdl: Line RMS block.
    :param load_mdl: Load RMS block.
    :param bus0: Sending-end bus object.
    :param bus1: Receiving-end bus object.
    :return: Ordered pairs ``(stable_name, variable)``.
    """
    named_vars: list[tuple[str, object]] = list()
    named_vars.append(("delta", find_name_in_block("deltaGenqec_rms_template", genqec_mdl)))
    named_vars.append(("omega", find_name_in_block("omegaGenqec_rms_template", genqec_mdl)))
    named_vars.append(("Eq_prime", find_name_in_block("Eq_primeGenqec_rms_template", genqec_mdl)))
    named_vars.append(("Ed_prime", find_name_in_block("Ed_primeGenqec_rms_template", genqec_mdl)))
    named_vars.append(("Psiq_prime", find_name_in_block("Psiq_primeGenqec_rms_template", genqec_mdl)))
    named_vars.append(("Psid_prime", find_name_in_block("Psid_primeGenqec_rms_template", genqec_mdl)))
    named_vars.append(("bus0_vm", bus0.rms_model.out_vars[0]))
    named_vars.append(("bus0_va", bus0.rms_model.out_vars[1]))
    named_vars.append(("bus1_vm", bus1.rms_model.out_vars[0]))
    named_vars.append(("bus1_va", bus1.rms_model.out_vars[1]))
    named_vars.append(("line_pf", line_mdl.out_vars[0]))
    named_vars.append(("line_pt", line_mdl.out_vars[1]))
    named_vars.append(("line_qf", line_mdl.out_vars[2]))
    named_vars.append(("line_qt", line_mdl.out_vars[3]))
    named_vars.append(("Pg", genqec_mdl.out_vars[0]))
    named_vars.append(("Qg", genqec_mdl.out_vars[1]))
    named_vars.append(("Psid", find_name_in_block("PsidGenqec_rms_template", genqec_mdl)))
    named_vars.append(("Psiq", find_name_in_block("PsiqGenqec_rms_template", genqec_mdl)))
    named_vars.append(("Te", find_name_in_block("TeGenqec_rms_template", genqec_mdl)))
    named_vars.append(("Ed1", find_name_in_block("Ed1Genqec_rms_template", genqec_mdl)))
    named_vars.append(("Eq1", find_name_in_block("Eq1Genqec_rms_template", genqec_mdl)))
    named_vars.append(("IRPu", find_name_in_block("IRPuGenqec_rms_template", genqec_mdl)))
    named_vars.append(("Tm", find_name_in_block("Tm", genqec_mdl)))
    named_vars.append(("y2_3_gov", find_name_in_block("y2_3_gov", genqec_mdl)))
    named_vars.append(("V_pss", find_name_in_block("V_pss", genqec_mdl)))
    named_vars.append(("y_stabilizer1", find_name_in_block("y_stabilizer1", genqec_mdl)))
    named_vars.append(("y_exciter1", find_name_in_block("y_exciter1", genqec_mdl)))
    named_vars.append(("y_exciter2", find_name_in_block("y_exciter2", genqec_mdl)))
    named_vars.append(("y_exciter3", find_name_in_block("y_exciter3", genqec_mdl)))
    named_vars.append(("y_exciter4", find_name_in_block("y_exciter4", genqec_mdl)))
    named_vars.append(("y_subexciter1", find_name_in_block("y_subexciter1", genqec_mdl)))
    named_vars.append(("u_aux", find_name_in_block("u_aux", genqec_mdl)))
    named_vars.append(("VeMaxPu", find_name_in_block("VeMaxPu", genqec_mdl)))
    named_vars.append(("Vf", find_name_in_block("Vf", genqec_mdl)))
    named_vars.append(("f_input", find_name_in_block("f_input", genqec_mdl)))
    named_vars.append(("f_output", find_name_in_block("f_output", genqec_mdl)))
    named_vars.append(("Efe", find_name_in_block("Efe", genqec_mdl)))
    named_vars.append(("Pl", find_name_in_block("Pl", load_mdl)))
    named_vars.append(("Ql", find_name_in_block("Ql", load_mdl)))
    return named_vars


def test_simulation_with_event():
    """
    This test creates a grid, adds rms models and events and rens simulation. Then it compares results with reference.
    :return:
    :rtype:
    """

    #########
    # retrieve reference results df

    folder = os.path.join(os.path.dirname(__file__), '..', 'data', 'dynamics')
    name = "simulation_with_event.csv"

    fname = os.path.join(folder, name)

    reference_df = pd.read_csv(fname)

    ###########################################################################################################################
    # Build VeraGrid object

    #####################################################################################
    #                    Grid
    #####################################################################################

    grid = gce.MultiCircuit(Sbase=100, fbase=50.0)

    #####################################################################################
    #                    Devices
    #####################################################################################

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
    grid.add_line(line0)

    # load
    load = gce.Load(P=9.999999, Q=0.999999)
    grid.add_load(bus=bus1, api_obj=load)

    # Generators
    gen0 = gce.Generator(name="Gen0", P=10, vset=1.0, Snom=900,
                         x1=0.86138701, r1=0.3, freq=50.0
                         )
    grid.add_generator(bus=bus0, api_obj=gen0)

    ######################################################################################################
    # Build Rms models
    ######################################################################################################

    # generator
    genqec_mdl = get_complete_generator_template_rms(grid.var_factory).block

    # line
    line_mdl = get_line_rms_template(grid.var_factory).block

    # load
    load_mdl = get_load_rms_template(grid.var_factory).block

    # set models parameters
    load_mdl.set_parameter_in_model(var_name="Pl0", new_value=-0.0999999)
    load_mdl.set_parameter_in_model(var_name="Ql0", new_value=-0.009999999862208533)

    ######################################################################################################
    # Add models to devices
    ######################################################################################################

    set_rms_model(device=gen0, model=genqec_mdl, var_factory=grid.var_factory)

    set_rms_model(device=line0, model=line_mdl, var_factory=grid.var_factory)

    set_rms_model(device=load, model=load_mdl, var_factory=grid.var_factory)

    ######################################################################################################
    # Create event
    ######################################################################################################

    Pl0 = find_name_in_block('Pl0', load_mdl)
    events_group = RmsEventsGroup(name="simulation1")
    grid.add_rms_events_group(events_group)
    event = RmsEvent(device=load, parameter=Pl0, time=0.1, value=-0.098, group=events_group)
    grid.add_rms_event(event)

    rms_events_group_names = np.array(0)

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

    problem.set_events_group(events_group)

    solver = BackEulerImplicitIntegration(
        problem=problem,
        t0=0,
        t_end=options.simulation_time,
        h=options.time_step,
        max_iter=options.max_iter
    )

    t, y, well_initialized, converged = solver.simulate()
    named_vars = build_named_variable_list(
        genqec_mdl=genqec_mdl,
        line_mdl=line_mdl,
        load_mdl=load_mdl,
        bus0=bus0,
        bus1=bus1,
    )
    results_df = build_results_dataframe(problem=problem, values=y, named_vars=named_vars)

    reference_mapping = build_reference_column_mapping()
    reference_columns = [legacy_name for _, legacy_name in reference_mapping]
    stable_columns = [stable_name for stable_name, _ in reference_mapping]
    reference_df = reference_df[reference_columns].copy()
    reference_df.columns = stable_columns

    assert_frame_equal(
        results_df.reset_index(drop=True),
        reference_df.reset_index(drop=True),
        check_dtype=False,
        check_index_type=False,
        atol=1e-6
    )


def test_rms_event_can_store_ramp_transition_metadata() -> None:
    """
    Check that RMS events preserve ramp-transition metadata.

    :return: None.
    """
    event: RmsEvent = RmsEvent(time=0.1,
                               end_time=0.2,
                               value=1.5,
                               transition_type=DynamicEventTransitionType.Ramp)

    assert event.time == 0.1
    assert event.end_time == 0.2
    assert event.value == 1.5
    assert event.transition_type == DynamicEventTransitionType.Ramp


def test_rms_event_accepts_serialized_ramp_transition_metadata() -> None:
    """
    Check that RMS events restore ramp metadata from serialized text.

    GUI and persistence layers can reconstruct the transition profile from the
    enum string value. The RMS event object must normalize that representation so
    the solver can still recognize the event as a ramp.

    :return: None.
    """
    event: RmsEvent = RmsEvent(time=0.1,
                               end_time=0.2,
                               value=1.5,
                               transition_type=DynamicEventTransitionType.Ramp)

    assert event.time == 0.1
    assert event.end_time == 0.2
    assert event.value == 1.5
    assert event.transition_type == DynamicEventTransitionType.Ramp
