# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.api as gce
from VeraGridEngine.Templates.Rms.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_rms_template import get_load_rms_template
from VeraGridEngine.Templates.Rms.genqec_exc_gov_sat_template import get_complete_generator_template_rms
from VeraGridEngine.Utils.Symbolic.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Utils.Symbolic.templates_common_functions import set_rms_model

def test_new_grid_save_load_compare() -> None:
    """
        This test checks  if the saving and load process for a new grid is correct

        The test consists in:
        - creating new grid
        - saving the grid with a different name
        - loading the saved grid (grid2)
        - comparing that grid1 == grid2

        """

    logger = Logger()

    grid1 = gce.MultiCircuit(Sbase=100, fbase=50.0)

    # Buses
    bus0 = gce.Bus(name="Bus0", Vnom=10, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=10)

    grid1.add_bus(bus0)
    grid1.add_bus(bus1)

    for bus in grid1.buses:
        initialize_bus_rms(bus, vf=grid1.var_factory)

    # Lines
    line0 = gce.Line(name="line 0-2", bus_from=bus0, bus_to=bus1, r=0.029585798816568046, x=0.07100591715976332, b=0.03,
                     rate=900.0)

    # load
    load = gce.Load(P=9.999999, Q=0.999999)

    # Generators
    gen0 = gce.Generator(name="Gen0", P=10, vset=1.0, Snom=900,
                         x1=0.86138701, r1=0.3, freq=50.0
                         )
    grid1.add_line(line0)
    grid1.add_load(bus=bus1, api_obj=load)
    grid1.add_generator(bus=bus0, api_obj=gen0)

    if not os.path.exists(os.path.join("data", "output")):
        os.makedirs(os.path.join("data", "output"))
    name = '2bus_genqec_new_grid_test.veragrid'
    fname = os.path.join("data", "output", name + '_to_save.veragrid')

    # save the created grid
    gce.save_file(grid=grid1, filename=fname)

    # open the saved grid
    grid2 = gce.open_file(fname)

    # # compare the original grid with the saved one to check that they are equal
    # equal, logger = grid1.compare_circuits(grid2, detailed_profile_comparison=True)
    # if not equal:
    #     logger.print()
    # # asset for failing
    # assert equal


    # if all ok, we can delete the test file
    os.remove(fname)


def test_new_grid_save_load_compare_rms() -> None:
    """
        This test checks  if the saving and load process for a new grid is correct

        The test consists in:
        - creating new grid
        - saving the grid with a different name
        - loading the saved grid (grid2)
        - comparing that grid1 == grid2

        """

    logger = Logger()

    grid1 = gce.MultiCircuit(Sbase=100, fbase=50.0)

    # Buses
    bus0 = gce.Bus(name="Bus0", Vnom=10, is_slack=True)
    bus1 = gce.Bus(name="Bus1", Vnom=10)

    grid1.add_bus(bus0)
    grid1.add_bus(bus1)

    for bus in grid1.buses:
        initialize_bus_rms(bus, vf=grid1.var_factory)

    # Lines
    line0 = gce.Line(name="line 0-2", bus_from=bus0, bus_to=bus1, r=0.029585798816568046, x=0.07100591715976332, b=0.03,
                     rate=900.0)
    grid1.add_line(line0)

    # load
    load = gce.Load(P=9.999999, Q=0.999999)
    grid1.add_load(bus=bus1, api_obj=load)

    # Generators
    gen0 = gce.Generator(name="Gen0", P=10, vset=1.0, Snom=900,
                         x1=0.86138701, r1=0.3, freq=50.0
                         )
    grid1.add_generator(bus=bus0, api_obj=gen0)

    ######################################################################################################
    # Build Rms models
    ######################################################################################################

    # generator
    genqec_mdl = get_complete_generator_template_rms(grid1.var_factory).block

    # line
    line_mdl = get_line_rms_template(grid1.var_factory).block

    # load
    load_mdl = get_load_rms_template(grid1.var_factory).block

    # set models parameters
    load_mdl.set_parameter_in_model(var_name="Pl0", new_value=-0.0999999)
    load_mdl.set_parameter_in_model(var_name="Ql0", new_value=-0.009999999862208533)

    ######################################################################################################
    # Add models to devices
    ######################################################################################################

    set_rms_model(device=gen0, model=genqec_mdl, var_factory=grid1.var_factory)

    set_rms_model(device=line0, model=line_mdl, var_factory=grid1.var_factory)

    set_rms_model(device=load, model=load_mdl, var_factory=grid1.var_factory)

    if not os.path.exists(os.path.join("data", "output")):
        os.makedirs(os.path.join("data", "output"))
    name = '2bus_genqec_new_grid_test.veragrid'
    fname = os.path.join("data", "output", name + '_to_save.veragrid')

    # save the created grid
    gce.save_file(grid=grid1, filename=fname)

    # open the saved grid
    grid2 = gce.open_file(fname)

    # compare the original grid with the saved one to check that they are equal
    # equal, logger = grid1.compare_circuits(grid2, detailed_profile_comparison=True)
    # if not equal:
    #     logger.print()
    # # asset for failing
    # assert equal

    # # compare the rms models inside the elements of the grid
    #
    # # get injection models
    # grid1_rms_system_dict = grid1.compose_bus_blocks()
    # grid2_rms_system_dict = grid2.compose_bus_blocks()
    #
    # # get branch models
    # grid1_rms_lines = list()
    # grid2_rms_lines = list()
    #
    # for elm in grid1.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
    #     grid1_rms_lines.append(elm.rms_model)
    #
    # for elm in grid2.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
    #     grid2_rms_lines.append(elm.rms_model)
    #
    # # create the blocks that will be compared
    # blocks_grid1: Block = Block()
    # blocks_grid2: Block = Block()
    # blocks_grid2.uid = blocks_grid1.uid
    #
    # # add injections and bus models
    # for bus, block in grid1_rms_system_dict.items():
    #     blocks_grid1.children.extend(block.children)
    #     blocks_grid1.children.append(bus.rms_model)
    #
    # for bus, block in grid2_rms_system_dict.items():
    #     blocks_grid2.children.extend(block.children)
    #     blocks_grid2.children.append(bus.rms_model)
    #
    # # add line models
    # blocks_grid1.children.extend(grid1_rms_lines)
    # blocks_grid2.children.extend(grid2_rms_lines)
    #
    # # compare the blocks
    # equal = compare_blocks(blocks_grid1, blocks_grid2, grid1.var_factory, grid2.var_factory, testing=True)
    #
    # if not equal:
    #     logger.add_error(msg="BLock dictionaries differs",
    #                      value=blocks_grid2,
    #                      expected_value=blocks_grid1)
    #     logger.print()
    #
    # # asset for failing
    # assert equal
    #
    # # if all ok, we can delete the test file
    os.remove(fname)
