# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import numpy as np
from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.api as gce
from VeraGridEngine.Utils.Symbolic import Block
from VeraGridEngine.Utils.Symbolic.symbolic_io import compare_blocks


def test_load_save_load() -> None:
    """
    This test checks if the saving and load process is correct

    The test consists in:
    - loading grids in different gridcal variations (grid1)
    - saving the grid with a different name
    - loading the saved grid (grid2)
    - comparing that grid1 == grid2

    """
    folder = os.path.join('data', 'grids')

    if not os.path.exists("output"):
        os.makedirs("output")

    for name in ['IEEE39_1W.gridcal',
                 'hydro_grid_IEEE39.gridcal',
                 'IEEE57.gridcal',
                 'fubm_caseHVDC_vt.gridcal',
                 'Test_SRAP.gridcal']:

        fname = os.path.join(folder, name)

        # open the main grid
        grid1 = gce.open_file(fname)

        name, ext = os.path.splitext(os.path.basename(fname))

        fname2 = os.path.join("output", name + '_to_save.veragrid')

        gce.save_file(grid=grid1, filename=fname2)

        # open the main grid again
        grid2 = gce.open_file(fname2)

        # compare the original grid with the saved one to check that they are equal
        equal, logger = grid1.compare_circuits(grid2, detailed_profile_comparison=True)

        if not equal:
            logger.print()

        # asset for failing
        assert equal

        # if all ok, we can delete the test file
        os.remove(fname2)


def test_load_save_load2() -> None:
    """
    This test checks if the saving and load process is correct with sparse profile changing.
    This is according to issue #309
    :return:
    """
    grid1 = gce.MultiCircuit(Sbase=45)
    grid1.set_unix_time(np.array([0, 3600]))
    b1 = grid1.add_bus()
    b2 = grid1.add_bus()
    b3 = grid1.add_bus()
    l1 = grid1.add_line(gce.Line(name='l1', bus_from=b1, bus_to=b2, rate=10.0))
    l2 = grid1.add_line(gce.Line(name='l2', bus_from=b2, bus_to=b3, rate=10.0))
    l3 = grid1.add_line(gce.Line(name='l3', bus_from=b3, bus_to=b1, rate=10.0))

    wire1 = gce.Wire(name="w1")
    wire2 = gce.Wire(name="w2")
    wire3 = gce.Wire(name="w3")
    tower = gce.OverheadLineType(name="Tower")
    tower.add_wire_relationship(wire1, xpos=0, ypos=7, phase=1)
    tower.add_wire_relationship(wire2, xpos=1.5, ypos=7, phase=1)
    tower.add_wire_relationship(wire3, xpos=3, ypos=7, phase=1)
    grid1.add_wire(wire1)
    grid1.add_wire(wire2)
    grid1.add_wire(wire3)

    grid1.add_overhead_line(tower)

    l1.rate_prof[1] = 20.0
    l2.rate_prof[1] = 30.0
    l3.rate_prof[1] = 40.0

    if not os.path.exists("output"):
        os.makedirs("output")

    o_file = os.path.join("output", "test_load_save_load2.veragrid")

    gce.save_file(grid=grid1, filename=o_file)

    grid2 = gce.open_file(o_file)

    equal, logger = grid2.compare_circuits(grid1, detailed_profile_comparison=True)

    if not equal:
        logger.print()

    assert equal

    os.remove(o_file)


def test_load_save_load_xlsx() -> None:
    """
    This test checks if the saving and load process is correct

    The test consists in:
    - loading grids in different gridcal variations (grid1)
    - saving the grid with a different name
    - loading the saved grid (grid2)
    - comparing that grid1 == grid2

    """
    folder = os.path.join('data', 'grids')

    if not os.path.exists("output"):
        os.makedirs("output")

    for name in ['IEEE39_1W.gridcal',
                 'hydro_grid_IEEE39.gridcal',
                 'IEEE57.gridcal',
                 'fubm_caseHVDC_vt.gridcal',
                 'Test_SRAP.gridcal']:
        fname = os.path.join(folder, name)

        grid1 = gce.open_file(fname)

        name, ext = os.path.splitext(os.path.basename(fname))

        fname2 = os.path.join("output", name + '_to_save.xlsx')

        gce.save_file(grid=grid1, filename=fname2)

        # open the main grid again
        grid2 = gce.open_file(fname2)


def test_load_save_load_rms() -> None:
    """
        This test checks if the saving and load process is correct when the grid contains rms models

        The test consists in:
        - loading grids in different veragrid variations (grid1)
        - saving the grid with a different name
        - loading the saved grid (grid2)
        - comparing that grid1 == grid2

        """

    logger = Logger()

    folder = os.path.join('data', 'grids')
    if not os.path.exists("output"):
        os.makedirs("output")

    name = '2bus_genqec_load_test.veragrid'
    fname = os.path.join(folder, name)

    # open the main grid
    grid1 = gce.open_file(fname)

    name, ext = os.path.splitext(os.path.basename(fname))

    fname2 = os.path.join("output", name + '_to_save.veragrid')

    gce.save_file(grid=grid1, filename=fname2)

    # open the main grid again
    grid2 = gce.open_file(fname2)

    # compare the original grid with the saved one to check that they are equal
    equal, logger = grid1.compare_circuits(grid2, detailed_profile_comparison=True)
    if not equal:
        logger.print()
    # asset for failing
    assert equal

    # compare the rms models inside the elements of the grid

    # get injection models
    grid1_rms_system_dict = grid1.compose_bus_blocks()
    grid2_rms_system_dict = grid2.compose_bus_blocks()

    # get branch models
    grid1_rms_lines = list()
    grid2_rms_lines = list()

    for elm in grid1.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
        grid1_rms_lines.append(elm.rms_model)

    for elm in grid2.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
        grid2_rms_lines.append(elm.rms_model)

    # create the blocks that will be compared
    blocks_grid1: Block = Block()
    blocks_grid2: Block = Block()
    blocks_grid2.uid = blocks_grid1.uid

    # add injections and bus models
    for bus, block in grid1_rms_system_dict.items():
        blocks_grid1.children.extend(block.children)
        blocks_grid1.children.append(bus.rms_model)

    for bus, block in grid2_rms_system_dict.items():
        blocks_grid2.children.extend(block.children)
        blocks_grid2.children.append(bus.rms_model)

    # add line models
    blocks_grid1.children.extend(grid1_rms_lines)
    blocks_grid2.children.extend(grid2_rms_lines)

    # compare the blocks
    equal = compare_blocks(blocks_grid1, blocks_grid2, grid1.var_factory, grid2.var_factory, testing=True)

    if not equal:
        logger.add_error(msg="BLock dictionaries differs",
                         value=blocks_grid2,
                         expected_value=blocks_grid1)
        logger.print()

    # asset for failing
    assert equal

    # if all ok, we can delete the test file
    os.remove(fname2)

# def test_load_save_load_evt_rms() -> None:
#     """
#         This test checks if the saving and load process is correct when the grid contains rms models
#
#         The test consists in:
#         - loading grids in different veragrid variations (grid1)
#         - saving the grid with a different name
#         - loading the saved grid (grid2)
#         - comparing that grid1 == grid2
#
#         """
#
#     logger = Logger()
#
#     folder = os.path.join('data', 'grids')
#     if not os.path.exists("output"):
#         os.makedirs("output")
#
#     name = '2bus_gen_load_evt_test.veragrid'
#     fname = os.path.join(folder, name)
#
#     # open the main grid
#     grid1 = gce.open_file(fname)
#
#     name, ext = os.path.splitext(os.path.basename(fname))
#
#     fname2 = os.path.join("output", name + '_to_save.veragrid')
#
#     gce.save_file(grid=grid1, filename=fname2)
#
#     # open the main grid again
#     grid2 = gce.open_file(fname2)
#
#     # compare the original grid with the saved one to check that they are equal
#     equal, logger = grid1.compare_circuits(grid2, detailed_profile_comparison=True)
#     if not equal:
#         logger.print()
#     # asset for failing
#     assert equal
#
#     # compare the rms models inside the elements of the grid
#
#     # get injection models
#     grid1_rms_system_dict = grid1.compose_bus_blocks()
#     grid2_rms_system_dict = grid2.compose_bus_blocks()
#
#     # get branch models
#     grid1_rms_lines = list()
#     grid2_rms_lines = list()
#
#     for elm in grid1.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
#         grid1_rms_lines.append(elm.rms_model.model)
#
#     for elm in grid2.get_branches_iter(add_vsc=True, add_hvdc=True, add_switch=True):
#         grid2_rms_lines.append(elm.rms_model.model)
#
#     # create the blocks that will be compared
#     blocks_grid1: Block = Block()
#     blocks_grid2: Block = Block()
#     blocks_grid2.uid = blocks_grid1.uid
#
#     # add injections and bus models
#     for bus, block in grid1_rms_system_dict.items():
#         blocks_grid1.children.extend(block.children)
#         blocks_grid1.children.append(bus.rms_model.model)
#
#     for bus, block in grid2_rms_system_dict.items():
#         blocks_grid2.children.extend(block.children)
#         blocks_grid2.children.append(bus.rms_model.model)
#
#     # add line models
#     blocks_grid1.children.extend(grid1_rms_lines)
#     blocks_grid2.children.extend(grid2_rms_lines)
#
#     # compare the blocks
#     equal = compare_blocks(blocks_grid1, blocks_grid2, grid1.var_factory, grid2.var_factory, testing=True)
#
#     if not equal:
#         logger.add_error(msg="BLock dictionaries differs",
#                          value=blocks_grid2,
#                          expected_value=blocks_grid1)
#         logger.print()
#
#     # asset for failing
#     assert equal
#
#     # if all ok, we can delete the test file
#     os.remove(fname2)