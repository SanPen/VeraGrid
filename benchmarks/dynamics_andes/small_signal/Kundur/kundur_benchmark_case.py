# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Construct the Kundur network and its benchmark RMS models."""

from __future__ import annotations

from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.enumerations import VarPowerFlowReferenceType
from VeraGridEngine.Templates.Rms.synchronous_machines.genrow1_rms_template import get_genrow1_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrow2_rms_template import get_genrow2_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrow3_rms_template import get_genrow3_rms_template
from VeraGridEngine.Templates.Rms.synchronous_machines.genrow4_rms_template import get_genrow4_rms_template
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Templates.Rms.load_characteristics.load_rms_template import get_load_rms_template
from VeraGridEngine.Utils.Symbolic import Block
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
import VeraGridEngine.api as gce


def build_kundur_rms_benchmark_grid() -> gce.MultiCircuit:
    """Build the Kundur RMS-ready benchmark grid.

    :return: RMS-ready Kundur grid.
    """
    ###########################################################################################################################
    # Build VeraGrid object
    ###########################################################################################################################

    grid = gce.MultiCircuit()

    # Buses
    bus1 = Bus(name="Bus1", Vnom=20)
    bus2 = Bus(name="Bus2", Vnom=20)
    bus3 = Bus(name="Bus3", Vnom=20, is_slack=True)
    bus4 = Bus(name="Bus4", Vnom=20)
    bus5 = Bus(name="Bus5", Vnom=230)
    bus6 = Bus(name="Bus6", Vnom=230)
    bus7 = Bus(name="Bus7", Vnom=230)
    bus8 = Bus(name="Bus8", Vnom=230)
    bus9 = Bus(name="Bus9", Vnom=230)
    bus10 = Bus(name="Bus10", Vnom=230)
    bus11 = Bus(name="Bus11", Vnom=230)

    grid.add_bus(bus1)
    grid.add_bus(bus2)
    grid.add_bus(bus3)
    grid.add_bus(bus4)
    grid.add_bus(bus5)
    grid.add_bus(bus6)
    grid.add_bus(bus7)
    grid.add_bus(bus8)
    grid.add_bus(bus9)
    grid.add_bus(bus10)
    grid.add_bus(bus11)

    for bus in grid.buses:
        initialize_bus_rms(bus, vf=grid.var_factory)

    # Line

    line0 = gce.Line(name="line 5-6-1", bus_from=bus5, bus_to=bus6,
                     r=0.00500, x=0.05000, b=0.02187, rate=750.0)

    line1 = gce.Line(name="line 5-6-2", bus_from=bus5, bus_to=bus6,
                     r=0.00500, x=0.05000, b=0.02187, rate=750.0)

    line2 = gce.Line(name="line 6-7-1", bus_from=bus6, bus_to=bus7,
                     r=0.00300, x=0.03000, b=0.00583, rate=700.0)

    line3 = gce.Line(name="line 6-7-2", bus_from=bus6, bus_to=bus7,
                     r=0.00300, x=0.03000, b=0.00583, rate=700.0)

    line4 = gce.Line(name="line 6-7-3", bus_from=bus6, bus_to=bus7,
                     r=0.00300, x=0.03000, b=0.00583, rate=700.0)

    line5 = gce.Line(name="line 7-8-1", bus_from=bus7, bus_to=bus8,
                     r=0.01100, x=0.11000, b=0.19250, rate=400.0)

    line6 = gce.Line(name="line 7-8-2", bus_from=bus7, bus_to=bus8,
                     r=0.01100, x=0.11000, b=0.19250, rate=400.0)

    line7 = gce.Line(name="line 8-9-1", bus_from=bus8, bus_to=bus9,
                     r=0.01100, x=0.11000, b=0.19250, rate=400.0)

    line8 = gce.Line(name="line 8-9-2", bus_from=bus8, bus_to=bus9,
                     r=0.01100, x=0.11000, b=0.19250, rate=400.0)

    line9 = gce.Line(name="line 9-10-1", bus_from=bus9, bus_to=bus10,
                     r=0.00300, x=0.03000, b=0.00583, rate=700.0)

    line10 = gce.Line(name="line 9-10-2", bus_from=bus9, bus_to=bus10,
                      r=0.00300, x=0.03000, b=0.00583, rate=700.0)

    line11 = gce.Line(name="line 9-10-3", bus_from=bus9, bus_to=bus10,
                      r=0.00300, x=0.03000, b=0.00583, rate=700.0)

    line12 = gce.Line(name="line 10-11-1", bus_from=bus10, bus_to=bus11,
                      r=0.00500, x=0.05000, b=0.02187, rate=750.0)

    line13 = gce.Line(name="line 10-11-2", bus_from=bus10, bus_to=bus11,
                      r=0.00500, x=0.05000, b=0.02187, rate=750.0)

    # Transformers
    xt1 = 0.15 * (100.0 / 900.0)
    trafo_G1 = Line(name="trafo 5-1", bus_from=bus5, bus_to=bus1,
                    r=0.00000, x=0.15 * (100.0 / 900.0), b=0.0, rate=900.0)

    trafo_G2 = gce.Line(name="trafo 6-2", bus_from=bus6, bus_to=bus2,
                        r=0.00000, x=0.15 * (100.0 / 900.0), b=0.0, rate=900.0)

    trafo_G3 = gce.Line(name="trafo 11-3", bus_from=bus11, bus_to=bus3,
                        r=0.00000, x=0.15 * (100.0 / 900.0), b=0.0, rate=900.0)

    trafo_G4 = gce.Line(name="trafo 10-4", bus_from=bus10, bus_to=bus4,
                        r=0.00000, x=0.15 * (100.0 / 900.0), b=0.0, rate=900.0)

    # load
    load1 = gce.Load(name="load1", P=967.0, Q=100.0)

    load2 = gce.Load(name="load2", P=1767.0, Q=100.0)

    # Generators
    fn_1 = 60.0
    M_1 = 13.0 * 9.0
    D_1 = 10.0 * 9.0
    ra_1 = 0.0
    xd_1 = 0.3 * 100.0 / 900.0
    omega_ref_1 = 1.0
    Kp_1 = 0.0
    Ki_1 = 0.0

    fn_2 = 60.0
    M_2 = 13.0 * 9.0
    D_2 = 10.0 * 9.0
    ra_2 = 0.0
    xd_2 = 0.3 * 100.0 / 900.0
    omega_ref_2 = 1.0
    Kp_2 = 0.0
    Ki_2 = 0.0

    fn_3 = 60.0
    M_3 = 12.35 * 9.0
    D_3 = 10.0 * 9.0
    ra_3 = 0.0
    xd_3 = 0.3 * 100.0 / 900.0
    omega_ref_3 = 1.0
    Kp_3 = 0.0
    Ki_3 = 0.0

    fn_4 = 60.0
    M_4 = 12.35 * 9.0
    D_4 = 10.0 * 9.0
    ra_4 = 0.0
    xd_4 = 0.3 * 100.0 / 900.0
    omega_ref_4 = 1.0
    Kp_4 = 0.0
    Ki_4 = 0.0

    # Generators
    gen1 = Generator(
        name="Gen1", P=700.0, vset=1.03, Snom=900.0,
        x1=xd_1, r1=ra_1, freq=fn_1,
    )

    gen2 = Generator(
        name="Gen2", P=700.0, vset=1.01, Snom=900.0,
        x1=xd_2, r1=ra_2, freq=fn_2,
    )

    gen3 = Generator(
        name="Gen3", P=719.091, vset=1.03, Snom=900.0,
        x1=xd_3, r1=ra_3, freq=fn_3,
    )

    gen4 = Generator(
        name="Gen4", P=700.0, vset=1.01, Snom=900.0,
        x1=xd_4, r1=ra_4, freq=fn_4,
    )

    ######################################################################################################
    # Build Rms models
    ######################################################################################################

    # Build rms models from template
    # generators
    genrow_mdl1 = get_genrow1_rms_template(grid.var_factory).block
    genrow_mdl2 = get_genrow2_rms_template(grid.var_factory).block
    genrow_mdl3 = get_genrow3_rms_template(grid.var_factory).block
    genrow_mdl4 = get_genrow4_rms_template(grid.var_factory).block

    # lines
    line0_mdl = get_line_rms_template(grid.var_factory).block
    line1_mdl = get_line_rms_template(grid.var_factory).block
    line2_mdl = get_line_rms_template(grid.var_factory).block
    line3_mdl = get_line_rms_template(grid.var_factory).block
    line4_mdl = get_line_rms_template(grid.var_factory).block
    line5_mdl = get_line_rms_template(grid.var_factory).block
    line6_mdl = get_line_rms_template(grid.var_factory).block
    line7_mdl = get_line_rms_template(grid.var_factory).block
    line8_mdl = get_line_rms_template(grid.var_factory).block
    line9_mdl = get_line_rms_template(grid.var_factory).block
    line10_mdl = get_line_rms_template(grid.var_factory).block
    line11_mdl = get_line_rms_template(grid.var_factory).block
    line12_mdl = get_line_rms_template(grid.var_factory).block
    line13_mdl = get_line_rms_template(grid.var_factory).block

    # trafos
    trafo1_mdl = get_line_rms_template(grid.var_factory).block
    trafo2_mdl = get_line_rms_template(grid.var_factory).block
    trafo3_mdl = get_line_rms_template(grid.var_factory).block
    trafo4_mdl = get_line_rms_template(grid.var_factory).block

    # loads
    load1_mdl = get_load_rms_template(grid.var_factory).block
    load2_mdl = get_load_rms_template(grid.var_factory).block

    # set models parameters
    load1_mdl.set_parameter_in_model(var_name="Pl0", new_value=-9.670000000007317)
    load1_mdl.set_parameter_in_model(var_name="Ql0", new_value=-0.9999999999967969)

    load2_mdl.set_parameter_in_model(var_name="Pl0", new_value=-17.6699999999199)
    load2_mdl.set_parameter_in_model(var_name="Ql0", new_value=-0.999999999989467)

    # connection with buses

    grid.var_factory.add_connections([genrow_mdl1.in_vars[0]], [bus1.rms_model.out_vars[0]])
    grid.var_factory.add_connections([genrow_mdl1.in_vars[1]], [bus1.rms_model.out_vars[1]])

    grid.var_factory.add_connections([genrow_mdl2.in_vars[0]], [bus2.rms_model.out_vars[0]])
    grid.var_factory.add_connections([genrow_mdl2.in_vars[1]], [bus2.rms_model.out_vars[1]])

    grid.var_factory.add_connections([genrow_mdl3.in_vars[0]], [bus3.rms_model.out_vars[0]])
    grid.var_factory.add_connections([genrow_mdl3.in_vars[1]], [bus3.rms_model.out_vars[1]])

    grid.var_factory.add_connections([genrow_mdl4.in_vars[0]], [bus4.rms_model.out_vars[0]])
    grid.var_factory.add_connections([genrow_mdl4.in_vars[1]], [bus4.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line0_mdl.in_vars[0]], [bus5.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line0_mdl.in_vars[1]], [bus5.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line0_mdl.in_vars[2]], [bus6.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line0_mdl.in_vars[3]], [bus6.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line1_mdl.in_vars[0]], [bus5.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line1_mdl.in_vars[1]], [bus5.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line1_mdl.in_vars[2]], [bus6.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line1_mdl.in_vars[3]], [bus6.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line2_mdl.in_vars[0]], [bus6.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line2_mdl.in_vars[1]], [bus6.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line2_mdl.in_vars[2]], [bus7.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line2_mdl.in_vars[3]], [bus7.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line3_mdl.in_vars[0]], [bus6.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line3_mdl.in_vars[1]], [bus6.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line3_mdl.in_vars[2]], [bus7.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line3_mdl.in_vars[3]], [bus7.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line4_mdl.in_vars[0]], [bus6.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line4_mdl.in_vars[1]], [bus6.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line4_mdl.in_vars[2]], [bus7.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line4_mdl.in_vars[3]], [bus7.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line5_mdl.in_vars[0]], [bus7.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line5_mdl.in_vars[1]], [bus7.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line5_mdl.in_vars[2]], [bus8.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line5_mdl.in_vars[3]], [bus8.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line6_mdl.in_vars[0]], [bus7.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line6_mdl.in_vars[1]], [bus7.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line6_mdl.in_vars[2]], [bus8.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line6_mdl.in_vars[3]], [bus8.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line7_mdl.in_vars[0]], [bus8.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line7_mdl.in_vars[1]], [bus8.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line7_mdl.in_vars[2]], [bus9.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line7_mdl.in_vars[3]], [bus9.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line8_mdl.in_vars[0]], [bus8.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line8_mdl.in_vars[1]], [bus8.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line8_mdl.in_vars[2]], [bus9.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line8_mdl.in_vars[3]], [bus9.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line9_mdl.in_vars[0]], [bus9.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line9_mdl.in_vars[1]], [bus9.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line9_mdl.in_vars[2]], [bus10.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line9_mdl.in_vars[3]], [bus10.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line10_mdl.in_vars[0]], [bus9.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line10_mdl.in_vars[1]], [bus9.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line10_mdl.in_vars[2]], [bus10.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line10_mdl.in_vars[3]], [bus10.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line11_mdl.in_vars[0]], [bus9.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line11_mdl.in_vars[1]], [bus9.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line11_mdl.in_vars[2]], [bus10.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line11_mdl.in_vars[3]], [bus10.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line12_mdl.in_vars[0]], [bus10.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line12_mdl.in_vars[1]], [bus10.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line12_mdl.in_vars[2]], [bus11.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line12_mdl.in_vars[3]], [bus11.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line13_mdl.in_vars[0]], [bus10.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line13_mdl.in_vars[1]], [bus10.rms_model.out_vars[1]])

    grid.var_factory.add_connections([line13_mdl.in_vars[2]], [bus11.rms_model.out_vars[0]])
    grid.var_factory.add_connections([line13_mdl.in_vars[3]], [bus11.rms_model.out_vars[1]])

    grid.var_factory.add_connections([trafo1_mdl.in_vars[0]], [bus5.rms_model.out_vars[0]])
    grid.var_factory.add_connections([trafo1_mdl.in_vars[1]], [bus5.rms_model.out_vars[1]])

    grid.var_factory.add_connections([trafo1_mdl.in_vars[2]], [bus1.rms_model.out_vars[0]])
    grid.var_factory.add_connections([trafo1_mdl.in_vars[3]], [bus1.rms_model.out_vars[1]])

    grid.var_factory.add_connections([trafo2_mdl.in_vars[0]], [bus6.rms_model.out_vars[0]])
    grid.var_factory.add_connections([trafo2_mdl.in_vars[1]], [bus6.rms_model.out_vars[1]])

    grid.var_factory.add_connections([trafo2_mdl.in_vars[2]], [bus2.rms_model.out_vars[0]])
    grid.var_factory.add_connections([trafo2_mdl.in_vars[3]], [bus2.rms_model.out_vars[1]])

    grid.var_factory.add_connections([trafo3_mdl.in_vars[0]], [bus11.rms_model.out_vars[0]])
    grid.var_factory.add_connections([trafo3_mdl.in_vars[1]], [bus11.rms_model.out_vars[1]])

    grid.var_factory.add_connections([trafo3_mdl.in_vars[2]], [bus3.rms_model.out_vars[0]])
    grid.var_factory.add_connections([trafo3_mdl.in_vars[3]], [bus3.rms_model.out_vars[1]])

    grid.var_factory.add_connections([trafo4_mdl.in_vars[0]], [bus10.rms_model.out_vars[0]])
    grid.var_factory.add_connections([trafo4_mdl.in_vars[1]], [bus10.rms_model.out_vars[1]])

    grid.var_factory.add_connections([trafo4_mdl.in_vars[2]], [bus4.rms_model.out_vars[0]])
    grid.var_factory.add_connections([trafo4_mdl.in_vars[3]], [bus4.rms_model.out_vars[1]])

    grid.var_factory.add_connections([load1_mdl.in_vars[0]], [bus7.rms_model.out_vars[0]])
    grid.var_factory.add_connections([load1_mdl.in_vars[1]], [bus7.rms_model.out_vars[1]])

    grid.var_factory.add_connections([load2_mdl.in_vars[0]], [bus9.rms_model.out_vars[0]])
    grid.var_factory.add_connections([load2_mdl.in_vars[1]], [bus9.rms_model.out_vars[1]])

    # external mapping

    big_gen1 = Block(children=[genrow_mdl1])
    big_gen2 = Block(children=[genrow_mdl2])
    big_gen3 = Block(children=[genrow_mdl3])
    big_gen4 = Block(children=[genrow_mdl4])

    big_gen1.external_mapping.update({VarPowerFlowReferenceType.P: genrow_mdl1.out_vars[0]})
    big_gen1.external_mapping.update({VarPowerFlowReferenceType.Q: genrow_mdl1.out_vars[1]})

    big_gen2.external_mapping.update({VarPowerFlowReferenceType.P: genrow_mdl2.out_vars[0]})
    big_gen2.external_mapping.update({VarPowerFlowReferenceType.Q: genrow_mdl2.out_vars[1]})

    big_gen3.external_mapping.update({VarPowerFlowReferenceType.P: genrow_mdl3.out_vars[0]})
    big_gen3.external_mapping.update({VarPowerFlowReferenceType.Q: genrow_mdl3.out_vars[1]})

    big_gen4.external_mapping.update({VarPowerFlowReferenceType.P: genrow_mdl4.out_vars[0]})
    big_gen4.external_mapping.update({VarPowerFlowReferenceType.Q: genrow_mdl4.out_vars[1]})

    # add models to opi objects

    gen1.rms_model = big_gen1
    gen2.rms_model = big_gen2
    gen3.rms_model = big_gen3
    gen4.rms_model = big_gen4

    line0.rms_model = line0_mdl
    line1.rms_model = line1_mdl
    line2.rms_model = line2_mdl
    line3.rms_model = line3_mdl
    line4.rms_model = line4_mdl
    line5.rms_model = line5_mdl
    line6.rms_model = line6_mdl
    line7.rms_model = line7_mdl
    line8.rms_model = line8_mdl
    line9.rms_model = line9_mdl
    line10.rms_model = line10_mdl
    line11.rms_model = line11_mdl
    line12.rms_model = line12_mdl
    line13.rms_model = line13_mdl

    trafo_G1.rms_model = trafo1_mdl
    trafo_G2.rms_model = trafo2_mdl
    trafo_G3.rms_model = trafo3_mdl
    trafo_G4.rms_model = trafo4_mdl

    load1.rms_model = load1_mdl
    load2.rms_model = load2_mdl

    grid.add_line(line0)
    grid.add_line(line1)
    grid.add_line(line2)
    grid.add_line(line3)
    grid.add_line(line4)
    grid.add_line(line5)
    grid.add_line(line6)
    grid.add_line(line7)
    grid.add_line(line8)
    grid.add_line(line9)
    grid.add_line(line10)
    grid.add_line(line11)
    grid.add_line(line12)
    grid.add_line(line13)

    grid.add_line(trafo_G1)
    grid.add_line(trafo_G2)
    grid.add_line(trafo_G3)
    grid.add_line(trafo_G4)

    grid.add_load(bus=bus7, api_obj=load1)
    grid.add_load(bus=bus9, api_obj=load2)

    grid.add_generator(bus=bus1, api_obj=gen1)
    grid.add_generator(bus=bus2, api_obj=gen2)
    grid.add_generator(bus=bus3, api_obj=gen3)
    grid.add_generator(bus=bus4, api_obj=gen4)

    return grid
