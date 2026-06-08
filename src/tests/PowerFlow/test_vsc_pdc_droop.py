# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Tests for the VSC DC-power / DC-voltage droop control (ConverterControlType.Pdc_droop).

The droop law implemented is:

    Pdc = Pdc* - Pdroop * (Vdc* - Vdc)

with Pdroop = S_r * 100 / droop[%].

The system-level test reproduces the multiterminal HVDC-VSC offshore wind farm
case from:

    Gomis-Bellmunt, O., Liang, J., Ekanayake, J. & Jenkins, N. (2011).
    Voltage-current characteristics of multiterminal HVDC-VSC for offshore
    wind farms. Electric Power Systems Research, 81(2), 440-450.
    https://doi.org/10.1016/j.epsr.2010.10.007
"""

import numpy as np

from VeraGridEngine.enumerations import ConverterControlType
from VeraGridEngine.Simulations.PowerFlow.NumericalMethods.common_functions import voltage_pdc_droop
import VeraGridEngine.api as gce


def test_voltage_pdc_droop_function() -> None:
    """
    Unit test of the droop law itself, independent of the power flow solver.
    """
    S_base = 100.0
    S_r = 100.0
    droop = 1.0  # [%]
    u_setpoint = 1.0
    Pdc_setpoint = 0.0  # [MW]

    P_droop = S_r * 100.0 / droop  # 10000 MW

    # Linear region: Pdc = Pdc* - Pdroop * (Vdc* - Vdc)
    for u in (0.95, 0.99, 1.0, 1.02, 1.08):
        expected = (Pdc_setpoint * S_base - P_droop * (u_setpoint - u)) / S_base
        got = voltage_pdc_droop(ut=complex(u, 0.0),
                                u_setpoint_min=0.9, u_setpoint_max=1.1,
                                u_setpoint=u_setpoint, Pdc_setpoint=Pdc_setpoint,
                                S_r=S_r, droop=droop,
                                P_min=-9999.0, P_max=9999.0, S_base=S_base)
        assert np.isclose(got, expected, atol=1e-9)

    # At nominal voltage the droop term vanishes and the converter outputs
    # exactly its dispatch setpoint.
    got = voltage_pdc_droop(ut=complex(1.0, 0.0),
                            u_setpoint_min=0.9, u_setpoint_max=1.1,
                            u_setpoint=1.0, Pdc_setpoint=50.0,
                            S_r=S_r, droop=droop,
                            P_min=-9999.0, P_max=9999.0, S_base=S_base)
    assert np.isclose(got, 50.0, atol=1e-9)

    # Voltage clamping: below u_min and above u_max the voltage saturates
    p_low = voltage_pdc_droop(ut=complex(0.5, 0.0), u_setpoint_min=0.9, u_setpoint_max=1.1,
                              u_setpoint=1.0, Pdc_setpoint=0.0, S_r=S_r, droop=droop,
                              P_min=-9999.0, P_max=9999.0, S_base=S_base)
    p_at_min = voltage_pdc_droop(ut=complex(0.9, 0.0), u_setpoint_min=0.9, u_setpoint_max=1.1,
                                 u_setpoint=1.0, Pdc_setpoint=0.0, S_r=S_r, droop=droop,
                                 P_min=-9999.0, P_max=9999.0, S_base=S_base)
    assert np.isclose(p_low, p_at_min, atol=1e-9)

    # Power clamping. With the Pdc = Pdc* - Pdroop*(Vdc* - Vdc) law:
    #  - voltage below setpoint pushes Pdc towards -inf  -> clamps at P_min
    #  - voltage above setpoint pushes Pdc towards +inf  -> clamps at P_max
    p_min_clamp = voltage_pdc_droop(ut=complex(0.9, 0.0), u_setpoint_min=0.9, u_setpoint_max=1.1,
                                    u_setpoint=1.0, Pdc_setpoint=0.0, S_r=S_r, droop=droop,
                                    P_min=-50.0, P_max=50.0, S_base=S_base)
    assert np.isclose(p_min_clamp, -50.0 / S_base, atol=1e-9)

    p_max_clamp = voltage_pdc_droop(ut=complex(1.1, 0.0), u_setpoint_min=0.9, u_setpoint_max=1.1,
                                    u_setpoint=1.0, Pdc_setpoint=0.0, S_r=S_r, droop=droop,
                                    P_min=-50.0, P_max=50.0, S_base=S_base)
    assert np.isclose(p_max_clamp, 50.0 / S_base, atol=1e-9)


def _build_case_study():
    """
    Build the Pdc/Vdc droop case study (Oriol Gomis 2011 reference grid).
    Self-contained, no data files required.
    """
    Ub = 150
    Sb = 100
    Rb = (Ub ** 2) / Sb
    Ib = Sb / Ub

    a = 0.5515 / Sb
    b = 0.887 * (Ib / Sb)
    c = 3.77 * ((Ib ** 2) / Sb)

    r = 0.0224  # ohms/km
    d31, d34, d42 = 90, 50, 110  # km
    rlin_31, rlin_34, rlin_42 = (r * d31) / Rb, (r * d34) / Rb, (r * d42) / Rb

    grid = gce.MultiCircuit(name="Pdc_Vdroop_CaseStudy", Sbase=Sb)

    # AC buses
    bus1_ac = gce.Bus(name="Bus1_ac_gs1", Vnom=Ub, is_slack=True)
    grid.add_bus(bus1_ac)
    bus2_ac = gce.Bus(name="Bus2_ac_gs2", Vnom=Ub, is_slack=True)
    grid.add_bus(bus2_ac)
    bus3_ac = gce.Bus(name="Bus3_ac_wf3", Vnom=Ub)
    grid.add_bus(bus3_ac)
    bus4_ac = gce.Bus(name="Bus4_ac_wf3", Vnom=Ub)
    grid.add_bus(bus4_ac)

    # DC buses
    bus1_dc = gce.Bus(name="Bus1_dc", Vnom=Ub, is_dc=True)
    grid.add_bus(bus1_dc)
    bus2_dc = gce.Bus(name="Bus2_dc", Vnom=Ub, is_dc=True)
    grid.add_bus(bus2_dc)
    bus3_dc = gce.Bus(name="Bus3_dc", Vnom=Ub, is_dc=True)
    grid.add_bus(bus3_dc)
    bus4_dc = gce.Bus(name="Bus4_dc", Vnom=Ub, is_dc=True)
    grid.add_bus(bus4_dc)

    # DC lines
    grid.add_dc_line(gce.DcLine(name="dc_line_31", bus_from=bus3_dc, bus_to=bus1_dc, r=rlin_31))
    grid.add_dc_line(gce.DcLine(name="dc_line_34", bus_from=bus3_dc, bus_to=bus4_dc, r=rlin_34))
    grid.add_dc_line(gce.DcLine(name="dc_line_42", bus_from=bus4_dc, bus_to=bus2_dc, r=rlin_42))

    # Generators
    grid.add_generator(bus1_ac, gce.Generator(name='GS1', vset=1.0))
    grid.add_generator(bus2_ac, gce.Generator(name='GS2', vset=1.0))
    grid.add_generator(bus3_ac, gce.Generator(name='WF3', P=102.95))
    grid.add_generator(bus4_ac, gce.Generator(name='WF4', P=102.95))

    # Onshore VSCs: Qac + Pdc_droop (DC voltage droop)
    grid.add_vsc(gce.VSC(name="VSC_GS_1", bus_from=bus1_dc, bus_to=bus1_ac,
                         rate=100.0,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Qac,
                         control2=ConverterControlType.Pdc_droop,
                         control1_val=1, control2_val=0.0,
                         control2_droop=1,
                         control2_droop_val=1.0,
                         control2_droop_val_min=0.9,
                         control2_droop_val_max=1.1))
    grid.add_vsc(gce.VSC(name="VSC_GS_2", bus_from=bus2_dc, bus_to=bus2_ac,
                         rate=100.0,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Qac,
                         control2=ConverterControlType.Pdc_droop,
                         control1_val=1, control2_val=0.0,
                         control2_droop=1,
                         control2_droop_val=1.0,
                         control2_droop_val_min=0.9,
                         control2_droop_val_max=1.1))

    # Offshore VSCs: Vm_ac + Va_ac (grid-forming for the wind farms)
    grid.add_vsc(gce.VSC(name="VSC_WF_3", bus_from=bus3_dc, bus_to=bus3_ac,
                         rate=100.0,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Vm_ac,
                         control2=ConverterControlType.Va_ac,
                         control1_val=1.0, control2_val=0.0))
    grid.add_vsc(gce.VSC(name="VSC_WF_4", bus_from=bus4_dc, bus_to=bus4_ac,
                         rate=100.0,
                         alpha1=a, alpha2=b, alpha3=c,
                         control1=ConverterControlType.Vm_ac,
                         control2=ConverterControlType.Va_ac,
                         control1_val=1.0, control2_val=0.0))
    return grid, Sb


def test_pdc_vdroop_case_study() -> None:
    """
    System-level validation: the converged solution must match the published
    reference values, and the converter DC powers must satisfy the droop law.
    """
    grid, Sb = _build_case_study()

    options = gce.PowerFlowOptions(verbose=0, generate_report=True,
                                   retry_with_other_methods=False)
    res = gce.power_flow(grid, options=options)

    assert res.converged

    # Bus ordering: 0..3 AC buses, 4..7 DC buses
    # Reference DC voltages from the Gomis-Bellmunt 2011 grid
    vm = np.abs(res.voltage)
    assert np.isclose(vm[4], 1.010346, atol=1e-4)  # Bus1_dc
    assert np.isclose(vm[5], 1.009466, atol=1e-4)  # Bus2_dc
    assert np.isclose(vm[6], 1.019521, atol=1e-4)  # Bus3_dc
    assert np.isclose(vm[7], 1.019736, atol=1e-4)  # Bus4_dc

    # Onshore converters share the wind power per the droop characteristic.
    # Reference "power from positive pole": VSC_GS_1 = 103.46, VSC_GS_2 = 94.66 MW
    assert np.isclose(res.Pfp_vsc[0], 103.461723, atol=1e-3)
    assert np.isclose(res.Pfp_vsc[1], 94.662482, atol=1e-3)

    # Offshore converters deliver the full wind farm generation
    assert np.isclose(res.St_vsc[2].real, 102.95, atol=1e-3)
    assert np.isclose(res.St_vsc[3].real, 102.95, atol=1e-3)

    # The droop relationship must hold at the converged solution:
    # Pfp(VSC) == voltage_pdc_droop(Vdc_from, ...) for the two GS converters.
    for k, dc_bus in ((0, 4), (1, 5)):
        vsc = grid.vsc_devices[k]
        expected_pu = voltage_pdc_droop(
            ut=res.voltage[dc_bus],
            u_setpoint_min=vsc.control2_droop_val_min,
            u_setpoint_max=vsc.control2_droop_val_max,
            u_setpoint=vsc.control2_droop_val,
            Pdc_setpoint=vsc.control2_val,
            S_r=vsc.rate,
            droop=vsc.control2_val_droop,
            P_min=vsc.control2_val_min,
            P_max=vsc.control2_val_max,
            S_base=Sb,
        )
        assert np.isclose(res.Pfp_vsc[k], expected_pu * Sb, atol=1e-3)


def test_pdc_droop_sharing_responds_to_droop_gain() -> None:
    """
    The droop gain must change how the two converters share power:
    a softer droop on VSC_GS_1 (larger droop[%] -> smaller Pdroop) shifts
    load towards VSC_GS_2.
    """
    grid, _ = _build_case_study()
    res_base = gce.power_flow(grid, options=gce.PowerFlowOptions(retry_with_other_methods=False))
    assert res_base.converged
    share_base = res_base.Pfp_vsc[0] - res_base.Pfp_vsc[1]

    # Soften VSC_GS_1's droop (higher droop[%] => smaller Pdroop slope)
    grid.vsc_devices[0].control2_val_droop = 3.0
    res_soft = gce.power_flow(grid, options=gce.PowerFlowOptions(retry_with_other_methods=False))
    assert res_soft.converged
    share_soft = res_soft.Pfp_vsc[0] - res_soft.Pfp_vsc[1]

    # VSC_GS_1 should now carry relatively less power than before
    assert share_soft < share_base
