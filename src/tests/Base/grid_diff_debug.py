# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
import VeraGridEngine.api as gce


def add_stuff_roundtrip() -> None:
    """
    This test does the following:
    We open IEEE57 twice, one for modification and another as baseline
    We open Lynn5bus and add it to the IEEE57 for modification
    We compute the difference between the modified grid and the baseline,
    The difference should be equal to what we added: i.e Lynn5bus
    """
    original = gce.open_file(filename=os.path.join("data", "grids", "IEEE57.gridcal"))  # we use this for diff
    n_orig = 0
    for elem in original.items():
        n_orig+=1

    # NOTE: it may fail if new properties are added, just save the original file
    # gce.save_file(original, os.path.join("data", "grids", "IEEE57.gridcal"))

    grid1 = gce.open_file(filename=os.path.join("data", "grids", "IEEE57.gridcal"))
    # fname2 = "IEEE57.gridcal"
    #
    # gce.save_file(grid=grid1, filename=fname2)
    # we modify this one in place

    n_grid1 = 0
    for elem in grid1.items():
        n_grid1 += 1

    # add stuff
    lynn_original = gce.open_file(filename=os.path.join("data", "grids", "lynn5node.gridcal"))
    lynn_original.delete_profiles()

    # add elements one by one
    n_lin = 0
    for elem in lynn_original.items():
        n_lin += 1


    for elm in lynn_original.items():
        grid1.add_element(obj=elm)

    n_grid1_after = 0
    for elem in grid1.items():
        n_grid1_after += 1

    # calculate the difference of the modified grid with the original
    ok_diff, diff_logger, diff = grid1.differentiate_circuits(base_grid=original)

    n_diff = 0
    for elem in diff.items():
        n_diff += 1
    # the calculated difference should be equal to the grid we added
    ok_compare, comp_logger = diff.compare_circuits(grid2=lynn_original, skip_internals=True)

    if not ok_compare:
        comp_logger.print()

    assert ok_compare


def grid_modifications() -> None:
    """
    This test does the following:
    We open IEEE14 as if we were modifying the grid in two different computers.
    We add stuff, delete_with_dialogue stuff and modify stuff, including some collisions when editing.
    We compute the difference between the modified grids and the base, and we merge
    We should get a file with the independent modifications, and some sort of message for colliding modifications
    """
    original = gce.open_file(filename=os.path.join("data", "grids", "data/grids/case14.gridcal"))  # we use this for diff

    gce.save_file(grid=original, filename="data/grids/case14.gridcal")


    # NOTE: it may fail if new properties are added, just save the original file
    # gce.save_file(original, os.path.join("data", "grids", "case14.gridcal"))

    grid1 = gce.open_file(filename=os.path.join("data", "grids", "data/grids/case14.gridcal"))
    grid2 = gce.open_file(filename=os.path.join("data", "grids", "data/grids/case14.gridcal"))

    grid1.remove_diagram(diagram=grid1.diagrams[0])
    grid2.remove_diagram(diagram=grid2.diagrams[0])

    # add stuff

    busPC1 = gce.Bus(name='Bus_addedPC1', Vnom=0.0)
    busPC2 = gce.Bus(name='Bus_addedPC2', Vnom=0.0)

    linePC1 = gce.Line(name='AddedLinePC1', bus_from=busPC1, bus_to=grid1.buses[5])

    grid1.add_bus(busPC1)
    grid2.add_bus(busPC2)
    grid1.add_line(linePC1)

    # Modify stuff

    grid1.loads[8].bus = busPC1
    grid2.lines[15].bus_from = busPC2

    # drop stuff

    grid1.delete_bus(obj=grid1.buses[11], delete_associated=True)

    # If it was done in a single PC:

    merged_grid = gce.open_file(filename=os.path.join("data", "grids", "data/grids/case14.gridcal"))

    merged_grid.add_bus(busPC1)
    merged_grid.add_line(linePC1)
    merged_grid.loads[8].bus = busPC1

    merged_grid.add_bus(busPC2)
    merged_grid.lines[15].bus_from = busPC2
    lin = merged_grid.lines[15]
    merged_grid.delete_line(obj=lin)
    merged_grid.delete_bus(obj=merged_grid.buses[11], delete_associated=False)
    merged_grid.delete_line(obj=merged_grid.lines[8])
    merged_grid.add_line(obj=lin)

    # calculate the difference of the modified grid with the original
    ok_diff1, diff_logger1, diff1 = grid1.differentiate_circuits(base_grid=original)
    ok_diff2, diff_logger2, diff2 = grid2.differentiate_circuits(base_grid=original)

    merge_logger1 = original.merge_circuit(diff1)
    f1 = os.path.join("data", "grids", "case14_merge1.gridcal")
    gce.save_file(grid=original, filename=f1)

    merge_logger2 = original.merge_circuit(diff2)
    f2 = os.path.join("data", "grids", "case14_merge2.gridcal")
    gce.save_file(grid=original, filename=f2)

    # the calculated difference should be equal to the grid we added
    ok_compare, comp_logger = original.compare_circuits(grid2=merged_grid, skip_internals=True)
    #
    if not ok_compare:
        comp_logger.print()
    #
    assert ok_compare

    os.remove(f1)
    os.remove(f2)
    return


grid_modifications()