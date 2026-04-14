# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
import os
import VeraGridEngine.api as vge


def test_add_stuff_roundtrip() -> None:
    """
    This test does the following:
    We open IEEE57 twice, one for modification and another as baseline
    We open Lynn5bus and add it to the IEEE57 for modification
    We compute the difference between the modified grid and the baseline,
    The difference should be equal to what we added: i.e Lynn5bus
    """
    original = vge.open_file(filename=os.path.join("data", "grids", "IEEE57.gridcal"))  # we use this for diff

    # NOTE: it may fail if new properties are added, just save the original file
    # vge.save_file(original, os.path.join("data", "grids", "IEEE57.gridcal"))

    grid1 = vge.open_file(filename=os.path.join("data", "grids", "IEEE57.gridcal"))  # we modify this one in place

    # add stuff
    lynn_original = vge.open_file(filename=os.path.join("data", "grids", "lynn5node.gridcal"))

    # add elements one by one
    for elm in lynn_original.items():
        grid1.add_element(obj=elm)

    # calculate the difference of the modified grid with the original
    ok_diff, diff_logger, diff = grid1.differentiate_circuits(base_grid=original)

    # Align the comparison grid to the diff time axis so profile-aware comparisons stay valid.
    if diff.time_profile is not None:
        lynn_original.time_profile = diff.time_profile.copy()
        lynn_original.ensure_profiles_exist()

    # the calculated difference should be equal to the grid we added
    ok_compare, comp_logger = diff.compare_circuits(grid2=lynn_original, skip_internals=True)

    if not ok_compare:
        comp_logger.print()

    assert ok_compare


def test_grid_modifications() -> None:
    """
    This test does the following:
    We open IEEE14 as if we were modifying the grid in two different computers.
    We add stuff, delete_with_dialogue stuff and modify stuff, including some collisions when editing.
    We compute the difference between the modified grids and the base, and we merge
    We should get a file with the independent modifications, and some sort of message for colliding modifications
    """
    original = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))  # we use this for diff

    # NOTE: it may fail if new properties are added, just save the original file
    # vge.save_file(original, os.path.join("data", "grids", "case14.gridcal"))

    grid1 = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))
    grid2 = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))

    grid1.remove_diagram(diagram=grid1.diagrams[0])
    grid2.remove_diagram(diagram=grid2.diagrams[0])

    # add stuff

    busPC1 = vge.Bus(name='Bus_addedPC1', Vnom=0.0)
    busPC2 = vge.Bus(name='Bus_addedPC2', Vnom=0.0)

    linePC1 = vge.Line(name='AddedLinePC1', bus_from=busPC1, bus_to=grid1.buses[5])

    grid1.add_bus(busPC1)
    grid2.add_bus(busPC2)
    grid1.add_line(linePC1)

    # Modify stuff

    grid1.loads[8].bus = busPC1
    grid2.lines[15].bus_from = busPC2

    # drop stuff

    grid1.delete_bus(obj=grid1.buses[11], delete_associated=True)

    # If it was done in a single PC:

    merged_grid = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))

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
    vge.save_file(grid=original, filename=f1)

    merge_logger2 = original.merge_circuit(diff2)
    f2 = os.path.join("data", "grids", "case14_merge2.gridcal")
    vge.save_file(grid=original, filename=f2)

    # the calculated difference should be equal to the grid we added
    ok_compare, comp_logger = original.compare_circuits(grid2=merged_grid, skip_internals=True)
    #
    if not ok_compare:
        comp_logger.print()
    #
    assert ok_compare

    if os.path.exists(f1):
        os.remove(f1)
    if os.path.exists(f2):
        os.remove(f2)
    return


def test_grid_collisions() -> None:
    """
    This test does the following:
    We open IEEE14 as if we were modifying the grid in two different computers.
    We add stuff, delete_with_dialogue stuff and modify stuff, including some collisions when editing.
    We compute the difference between the modified grids and the base, and we merge
    We should get a file with the independent modifications, and some sort of message for colliding modifications
    """
    original = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))  # we use this for diff
    original_moded = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))  # we use this for diff

    # NOTE: it may fail if new properties are added, just save the original file
    # gce.save_file(original, os.path.join("data", "grids", "case14.gridcal"))

    grid1 = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))
    grid2 = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))

    grid1.lines[0].name = 'TEST_LINE1'
    grid2.lines[0].comment = 'TEST_LINE2'

    original_moded.lines[0].name = 'TEST_LINE1'
    original_moded.lines[0].comment = 'TEST_LINE2'

    # calculate the difference of the modified grid with the original
    ok_diff1, diff_logger1, diff1 = grid1.differentiate_circuits(base_grid=original)
    ok_diff2, diff_logger2, diff2 = grid2.differentiate_circuits(base_grid=original)

    merge_logger1 = original.merge_circuit(diff1)
    merge_logger2 = original.merge_circuit(diff2)
    ok_compare, comp_logger = original.compare_circuits(grid2=original_moded, skip_internals=True)
    #
    if not ok_compare:
        comp_logger.print()
    #
    assert ok_compare

def test_grid_collisions_with_save_load() -> None:
    """
    This test does the following:
    We open IEEE14 as if we were modifying the grid in two different computers.
    We add stuff, delete_with_dialogue stuff and modify stuff, including some collisions when editing.
    We compute the difference between the modified grids and the base, and we merge
    We should get a file with the independent modifications, and some sort of message for colliding modifications
    """
    original = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))  # we use this for diff
    original_moded = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))  # we use this for diff

    # NOTE: it may fail if new properties are added, just save the original file
    # gce.save_file(original, os.path.join("data", "grids", "case14.gridcal"))

    grid1 = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))
    grid2 = vge.open_file(filename=os.path.join("data", "grids", "case14.gridcal"))

    grid1.lines[0].name = 'TEST_LINE1'
    grid2.lines[0].comment = 'TEST_LINE2'

    original_moded.lines[0].name = 'TEST_LINE1'
    original_moded.lines[0].comment = 'TEST_LINE2'

    # calculate the difference of the modified grid with the original
    ok_diff1, diff_logger1, diff1 = grid1.differentiate_circuits(base_grid=original)
    ok_diff2, diff_logger2, diff2 = grid2.differentiate_circuits(base_grid=original)

    vge.save_file(grid=diff1, filename=os.path.join("data", "grids", "differential1.dgridcal"))
    vge.save_file(grid=diff2, filename=os.path.join("data", "grids", "differential2.dgridcal"))

    diff1_load = vge.open_file(filename=os.path.join("data", "grids", "differential1.dgridcal"))
    diff2_load = vge.open_file(filename=os.path.join("data", "grids", "differential2.dgridcal"))

    merge_logger1 = original.merge_circuit(diff1)
    merge_logger2 = original.merge_circuit(diff2)
    ok_compare, comp_logger = original.compare_circuits(grid2=original_moded, skip_internals=True)
    #
    if not ok_compare:
        comp_logger.print()
    #
    assert ok_compare


def test_differentiate_circuits_preserves_time_profile_consistency() -> None:
    """
    Verify that a differential grid created from a time-series circuit keeps a valid time profile.

    This protects the case where a diff is produced from a time-series grid and later serialized
    or loaded through multiverse logic. The diff must carry the source time axis and keep its
    contained object profiles aligned with that axis.
    """
    original = vge.open_file(filename=os.path.join("data", "grids", "IEEE39_1W.gridcal"))
    modified = vge.open_file(filename=os.path.join("data", "grids", "IEEE39_1W.gridcal"))

    assert original.time_profile is not None
    assert modified.time_profile is not None

    modified.buses[0].active_prof[0] = not modified.buses[0].active_prof[0]
    modified.loads[0].P_prof[0] *= 1.1

    ok_diff, diff_logger, diff = modified.differentiate_circuits(base_grid=original)

    if not ok_diff:
        diff_logger.print()

    assert ok_diff
    assert diff.time_profile is not None
    assert diff.get_time_number() == modified.get_time_number()

    for bus in diff.buses:
        assert bus.active_prof.size() == diff.get_time_number()

    for load in diff.loads:
        assert load.active_prof.size() == diff.get_time_number()
        assert load.P_prof.size() == diff.get_time_number()
