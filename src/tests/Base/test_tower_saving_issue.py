import sys
import pytest
from PySide6 import QtWidgets
import VeraGridEngine.api as vge
from VeraGrid.Gui.Main.VeraGridMain import VeraGridMainGUI


# @pytest.mark.skip(reason="...")
def test_tower_saving_issue():
    """
    This test is because when saving from the GUI it
    fails because of the dynamic block saving mechanism.
    Simply not crashing should pass the test
    :return:
    """

    # ----------------------------------------------------------------------------------------------------------------------
    # GUI
    # ----------------------------------------------------------------------------------------------------------------------
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    gui = VeraGridMainGUI()
    gui.add_default_catalogue()

    logger = vge.Logger()
    grid = gui.circuit

    # ----------------------------------------------------------------------------------------------------------------------
    # Buses
    # ----------------------------------------------------------------------------------------------------------------------
    bus_slack = vge.Bus(name='Slack', xpos=0, ypos=0)
    bus_slack.is_slack = True
    grid.add_bus(obj=bus_slack)

    bus_load = vge.Bus(name='Load', xpos=0, ypos=200)
    grid.add_bus(obj=bus_load)

    # ----------------------------------------------------------------------------------------------------------------------
    # Generators
    # ----------------------------------------------------------------------------------------------------------------------
    gen_slack = vge.Generator()
    grid.add_generator(bus=bus_slack, api_obj=gen_slack)

    # ----------------------------------------------------------------------------------------------------------------------
    # Tower
    # ----------------------------------------------------------------------------------------------------------------------
    tower = vge.OverheadLineType(name="Tower",
                                 Vnom=10.0)

    wire = vge.Wire(name="Alex Blanco",
                    diameter=23.0,
                    diameter_internal=9.0,
                    is_tube=True,
                    r=0.19,
                    max_current=1)

    tower.add_wire_relationship(wire=wire, xpos=-2, ypos=20, phase=1)
    tower.add_wire_relationship(wire=wire, xpos=0, ypos=20, phase=2)
    tower.add_wire_relationship(wire=wire, xpos=2, ypos=20, phase=3)

    # ----------------------------------------------------------------------------------------------------------------------
    # Line
    # ----------------------------------------------------------------------------------------------------------------------
    line = vge.Line(bus_from=bus_slack,
                    bus_to=bus_load)
    line.apply_template(tower, grid.Sbase, grid.fBase, logger)
    grid.add_line(obj=line)

    # ----------------------------------------------------------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------------------------------------------------------
    load = vge.Load(P=4.0,
                    Q=2.0)
    grid.add_load(bus=bus_load, api_obj=load)

    # ----------------------------------------------------------------------------------------------------------------------
    # Save the grid
    # ----------------------------------------------------------------------------------------------------------------------
    # vge.save_file(grid=grid, )
    gui.save_file_now(filename='../tower.veragrid')
    # ----------------------------------------------------------------------------------------------------------------------
    # Run power flow
    # ----------------------------------------------------------------------------------------------------------------------
    res = vge.power_flow(grid=grid, options=vge.PowerFlowOptions())
    print(res.get_voltage_df())