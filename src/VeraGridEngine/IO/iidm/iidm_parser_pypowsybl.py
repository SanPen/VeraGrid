# Copyright (c) 2020-2025, RTE (http://www.rte-france.com)
# See AUTHORS.md
# All rights reserved.
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of the deeac project.
import os
from typing import Dict
import numpy as np
import VeraGridEngine.Devices as dev
from VeraGridEngine.basic_structures import Logger

try:
    import pypowsybl as pp

    PYPOWSYBL_AVAILABLE = True

except ImportError:
    pp = None
    PYPOWSYBL_AVAILABLE = False


class IidmParser:
    """
    Xiidm file parser
    """

    def __init__(self, fname: str, logger: Logger | None = None):
        """

        :param fname: xiidm file
        """
        if os.path.exists(fname):
            self.ps_grid = pp.network.load(fname)
        else:
            self.ps_grid = None

        self.logger = Logger() if logger is None else logger

    def parse(self) -> dev.MultiCircuit:
        """
        Convert the PowSybl structures to  deeac
        :return: Network
        """

        grid = dev.MultiCircuit()

        if self.ps_grid is None:
            return grid
        else:
            substations = self.ps_grid.get_substations(all_attributes=True)
            voltage_levels = self.ps_grid.get_voltage_levels(all_attributes=True)
            buses = self.ps_grid.get_buses(all_attributes=True)

            lines = self.ps_grid.get_lines(all_attributes=True)
            # branches = self.ps_grid.get_branches(all_attributes=True)
            switches = self.ps_grid.get_switches(all_attributes=True)
            transformers = self.ps_grid.get_2_windings_transformers(all_attributes=True)

            self.ps_grid.get_phase_tap_changers(all_attributes=True)
            self.ps_grid.get_phase_tap_changer_steps(all_attributes=True)

            hvdc = self.ps_grid.get_hvdc_lines(all_attributes=True)

            loads = self.ps_grid.get_loads(all_attributes=True)
            gens = self.ps_grid.get_generators(all_attributes=True)
            capacitor_banks = self.ps_grid.get_shunt_compensators(all_attributes=True)
            svc = self.ps_grid.get_static_var_compensators(all_attributes=True)

            grid.name = self.ps_grid.name
            grid.Sbase = self.ps_grid.nominal_apparent_power
            is_in_pu = self.ps_grid.per_unit

            """
            Substation
            0 = {str} 'name'
            1 = {str} 'TSO'
            2 = {str} 'geo_tags'
            3 = {str} 'country'
            4 = {str} 'fictitious'
            """
            country_dict: Dict[str, dev.Substation] = dict()
            se_dict: Dict[str, dev.Substation] = dict()
            for i, row in substations.iterrows():

                country = country_dict.get(row["country"], None)
                if country is None:
                    country = dev.Country(name=row["country"])
                    grid.add_country(obj=country)
                    country_dict[country.name] = country

                name = row["name"]
                if name == "":
                    name = i

                elm = dev.Substation(
                    name=name,
                    code=i,
                    country=country
                )
                grid.add_substation(obj=elm)
                se_dict[i] = elm

            """
            Voltage Level
            0 = {str} 'name'
            1 = {str} 'substation_id'
            2 = {str} 'nominal_v'
            3 = {str} 'high_voltage_limit'
            4 = {str} 'low_voltage_limit'
            """
            vl_dict: Dict[str, dev.VoltageLevel] = dict()
            for i, row in voltage_levels.iterrows():
                se = se_dict.get(row["substation_id"], None)

                if se is None:
                    self.logger.add_error("Substation not found",
                                          value=row["substation_id"])

                name = row["name"]
                if name == "":
                    name = i

                elm = dev.VoltageLevel(
                    name=name,
                    code=i,
                    Vnom=float(row["nominal_v"]),
                    substation=se
                )
                grid.add_voltage_level(obj=elm)
                vl_dict[i] = elm

                try:
                    topology = self.ps_grid.get_node_breaker_topology(voltage_level_id=i)
                except pp.PyPowsyblError:
                    pass

            """
            Bus
            0 = {str} 'name'
            1 = {str} 'v_mag'
            2 = {str} 'v_angle'
            3 = {str} 'connected_component'
            4 = {str} 'synchronous_component'
            5 = {str} 'voltage_level_id'
            6 = {str} 'fictitious'
            """
            bus_dict: Dict[str, dev.Bus] = dict()
            for idx, row in buses.iterrows():
                vl = vl_dict.get(row["voltage_level_id"], None)

                if vl is None:
                    self.logger.add_error("Voltage level not found",
                                          value=row["voltage_level_id"])

                bus = dev.Bus(
                    name=row["name"] if row["name"] != "" else idx,
                    code=idx,
                    Vnom=10 if vl is None else vl.Vnom,
                    Vm0=float(row["v_mag"]),
                    Va0=float(row["v_angle"]),
                    voltage_level=vl
                )
                grid.add_bus(obj=bus)
                bus_dict[idx] = bus

            """
            Line
            00 = {str} 'name'
            01 = {str} 'r'
            02 = {str} 'x'
            03 = {str} 'g1'
            04 = {str} 'b1'
            05 = {str} 'g2'
            06 = {str} 'b2'
            07 = {str} 'p1'
            08 = {str} 'q1'
            09 = {str} 'i1'
            10 = {str} 'p2'
            11 = {str} 'q2'
            12 = {str} 'i2'
            13 = {str} 'voltage_level1_id'
            14 = {str} 'voltage_level2_id'
            15 = {str} 'bus1_id'
            16 = {str} 'bus_breaker_bus1_id'
            17 = {str} 'node1'
            18 = {str} 'bus2_id'
            19 = {str} 'bus_breaker_bus2_id'
            20 = {str} 'node2'
            21 = {str} 'connected1'
            22 = {str} 'connected2'
            23 = {str} 'fictitious'
            24 = {str} 'selected_limits_group_1'
            25 = {str} 'selected_limits_group_2'
            """
            for i, row in lines.iterrows():
                bus1: dev.Bus = bus_dict[row["bus1_id"]]
                bus2: dev.Bus = bus_dict[row["bus2_id"]]

                Vn = max(bus1.Vnom, bus2.Vnom)
                Zbase = Vn * Vn / grid.Sbase
                Ybase = 1.0 / Zbase
                elm = dev.Line(
                    name=row["name"] if row["name"] != "" else i,
                    code=i,
                    bus_from=bus1,
                    bus_to=bus2,
                    r=row["r"] / Zbase,
                    x=row["x"] / Zbase,
                    b=row["b1"] / Ybase,
                )

                grid.add_line(obj=elm, logger=self.logger)

            """
            Switch
            00 = {str} 'name'
            01 = {str} 'kind'
            02 = {str} 'open'
            03 = {str} 'retained'
            04 = {str} 'voltage_level_id'
            05 = {str} 'bus_breaker_bus1_id'
            06 = {str} 'bus_breaker_bus2_id'
            07 = {str} 'node1'
            08 = {str} 'node2'
            09 = {str} 'fictitious'
            """
            # TODO: Unclear when these are available or how they're connected
            # for i, row in switches.iterrows():
            #     bus1: dev.Bus = bus_dict[row["bus_breaker_bus1_id"]]
            #     bus2: dev.Bus = bus_dict[row["bus_breaker_bus2_id"]]
            #
            #     elm = dev.Switch(
            #         name=row["name"],
            #         code = i,
            #         bus_from=bus1,
            #         bus_to=bus2,
            #         retained=bool(row["retained"]),
            #         active=not bool(row["open"])
            #     )
            #
            #     grid.add_switch(obj=elm)

            """
            Transformer
            00 = {str} 'name'
            01 = {str} 'r'
            02 = {str} 'x'
            03 = {str} 'g'
            04 = {str} 'b'
            05 = {str} 'rated_u1'
            06 = {str} 'rated_u2'
            07 = {str} 'rated_s'
            08 = {str} 'p1'
            09 = {str} 'q1'
            10 = {str} 'i1'
            11 = {str} 'p2'
            12 = {str} 'q2'
            13 = {str} 'i2'
            14 = {str} 'voltage_level1_id'
            15 = {str} 'voltage_level2_id'
            16 = {str} 'bus1_id'
            17 = {str} 'bus_breaker_bus1_id'
            18 = {str} 'node1'
            19 = {str} 'bus2_id'
            20 = {str} 'bus_breaker_bus2_id'
            21 = {str} 'node2'
            22 = {str} 'connected1'
            23 = {str} 'connected2'
            24 = {str} 'fictitious'
            25 = {str} 'selected_limits_group_1'
            26 = {str} 'selected_limits_group_2'
            27 = {str} 'rho'
            28 = {str} 'alpha'
            29 = {str} 'r_at_current_tap'
            30 = {str} 'x_at_current_tap'
            31 = {str} 'g_at_current_tap'
            32 = {str} 'b_at_current_tap'
            """
            for i, row in transformers.iterrows():
                bus1: dev.Bus = bus_dict[row["bus1_id"]]
                bus2: dev.Bus = bus_dict[row["bus2_id"]]

                rated_u1 = float(row["rated_u1"])
                rated_u2 = float(row["rated_u2"])
                if rated_u1 > rated_u2:
                    HV = rated_u1
                    LV = rated_u2
                else:
                    HV = rated_u2
                    LV = rated_u1

                rate = float(row["rated_s"])
                if np.isnan(rate):
                    rate = 9999.0

                elm = dev.Transformer2W(
                    name=row["name"] if row["name"] != "" else i,
                    code=i,
                    bus_from=bus1,
                    bus_to=bus2,
                    r=float(row["r"]),
                    x=float(row["x"]),
                    g=float(row["g"]),
                    b=float(row["b"]),
                    HV=HV,
                    LV=LV,
                    rate=rate,
                    tap_module=float(row["rho"]),
                    tap_phase=float(row["alpha"]),  # TODO in deg or rad? we need rad
                )

                grid.add_transformer2w(obj=elm)

            """
            HVDC
            00 = {str} 'name'
            01 = {str} 'converters_mode'
            02 = {str} 'target_p'
            03 = {str} 'max_p'
            04 = {str} 'nominal_v'
            05 = {str} 'r'
            06 = {str} 'converter_station1_id'
            07 = {str} 'converter_station2_id'
            08 = {str} 'connected1'
            09 = {str} 'connected2'
            10 = {str} 'fictitious'
            """
            for i, row in hvdc.iterrows():
                bus1: dev.Bus = bus_dict[row["converter_station1_id"]]
                bus2: dev.Bus = bus_dict[row["converter_station2_id"]]

                connected1 = bool(row["connected1"])
                connected2 = bool(row["connected2"])

                # TODO, what is the content of converters_mode? PMODE1, PMODE3 stuff probably but investigate

                elm = dev.HvdcLine(
                    name=row["name"] if row["name"] != "" else i,
                    bus_from=bus1,
                    bus_to=bus2,
                    dc_link_voltage=float(row["nominal_v"]),
                    Pset=float(row["target_p"]),
                    rate=float(row["max_p"]),
                    r=float(row["r"]),  # TODO: Ohm?, we need Ohm
                    active=connected1 and connected2
                )

                grid.add_hvdc(obj=elm)

            """
            Load
            00 = {str} 'name'
            01 = {str} 'type'
            02 = {str} 'p0'
            03 = {str} 'q0'
            04 = {str} 'p'
            05 = {str} 'q'
            06 = {str} 'i'
            07 = {str} 'voltage_level_id'
            08 = {str} 'bus_id'
            09 = {str} 'bus_breaker_bus_id'
            10 = {str} 'node'
            11 = {str} 'connected'
            12 = {str} 'fictitious'
            """
            for i, row in loads.iterrows():
                bus1 = bus_dict[row["bus_id"]]
                elm = dev.Load(
                    name=row["name"] if row["name"] != "" else i,
                    code=i,
                    P1=float(row["p"]),
                    Q1=float(row["q"]),
                    active=bool(row["connected"])
                )
                grid.add_load(bus=bus1, api_obj=elm)

            """
            Generator
            00 = {str} 'name'
            01 = {str} 'energy_source'
            02 = {str} 'target_p'
            03 = {str} 'min_p'
            04 = {str} 'max_p'
            05 = {str} 'min_q'
            06 = {str} 'max_q'
            07 = {str} 'min_q_at_target_p'
            08 = {str} 'max_q_at_target_p'
            09 = {str} 'min_q_at_p'
            10 = {str} 'max_q_at_p'
            11 = {str} 'rated_s'
            12 = {str} 'reactive_limits_kind'
            13 = {str} 'target_v'
            14 = {str} 'target_q'
            15 = {str} 'voltage_regulator_on'
            16 = {str} 'regulated_element_id'
            17 = {str} 'regulated_bus_id'
            18 = {str} 'regulated_bus_breaker_bus_id'
            19 = {str} 'p'
            20 = {str} 'q'
            21 = {str} 'i'
            22 = {str} 'voltage_level_id'
            23 = {str} 'bus_id'
            24 = {str} 'bus_breaker_bus_id'
            25 = {str} 'node'
            26 = {str} 'condenser'
            27 = {str} 'connected'
            28 = {str} 'fictitious'
            """
            for i, row in gens.iterrows():
                bus1 = bus_dict[row["bus_id"]]

                p = float(row["p"])
                q = float(row["q"])
                S = p + 1j * q
                Sabs = abs(S)
                if Sabs > 0.0:
                    pf = p / Sabs
                else:
                    pf = 0.0

                elm = dev.Generator(
                    name=row["name"] if row["name"] != "" else i,
                    code=i,
                    P=row["p"],
                    power_factor=pf,
                    vset=float(row["target_v"]),
                    Pmin=float(row["min_p"]),
                    Pmax=float(row["max_p"]),
                    Qmin=float(row["min_q"]),
                    Qmax=float(row["max_q"]),
                    Snom=float(row["rated_s"]),
                    active=bool(row["connected"]),
                    is_controlled=bool(row["voltage_regulator_on"]),
                )
                elm.control_bus = bus_dict.get(row["regulated_bus_id"], None)
                grid.add_generator(bus=bus1, api_obj=elm)

            """
            Capacitor bank
            00 = {str} 'name'
            01 = {str} 'g'
            02 = {str} 'b'
            03 = {str} 'model_type'
            04 = {str} 'max_section_count'
            05 = {str} 'section_count'
            06 = {str} 'solved_section_count'
            07 = {str} 'voltage_regulation_on'
            08 = {str} 'target_v'
            09 = {str} 'target_deadband'
            10 = {str} 'regulating_bus_id'
            11 = {str} 'p'
            12 = {str} 'q'
            13 = {str} 'i'
            14 = {str} 'voltage_level_id'
            15 = {str} 'bus_id'
            16 = {str} 'bus_breaker_bus_id'
            17 = {str} 'node'
            18 = {str} 'connected'
            19 = {str} 'fictitious'
            """
            for i, row in capacitor_banks.iterrows():
                bus1 = bus_dict[row["bus_id"]]
                elm = dev.Shunt(
                    name=row["name"] if row["name"] != "" else i,
                    code=i,
                    G1=float(row["g"]),
                    B1=float(row["b"]),
                    active=bool(row["connected"])
                )
                grid.add_shunt(bus=bus1, api_obj=elm)

            """
            SVC
            00 = {str} 'name'
            01 = {str} 'b_min'
            02 = {str} 'b_max'
            03 = {str} 'target_v'
            04 = {str} 'target_q'
            05 = {str} 'regulation_mode'
            06 = {str} 'regulating'
            07 = {str} 'regulated_element_id'
            08 = {str} 'regulated_bus_id'
            09 = {str} 'regulated_bus_breaker_bus_id'
            10 = {str} 'p'
            11 = {str} 'q'
            12 = {str} 'i'
            13 = {str} 'voltage_level_id'
            14 = {str} 'bus_id'
            15 = {str} 'bus_breaker_bus_id'
            16 = {str} 'node'
            17 = {str} 'connected'
            18 = {str} 'fictitious'
            """
            for i, row in svc.iterrows():
                bus1 = bus_dict[row["bus_id"]]
                elm = dev.ControllableShunt(
                    name=row["name"] if row["name"] != "" else i,
                    code=i,
                    G1=float(row["g"]),
                    B1=float(row["b"]),
                    active=bool(row["connected"]),
                    Bmin=float(row["b_min"]),
                    Bmax=float(row["b_max"]),
                    vset=float(row["target_v"]),
                    is_controlled=bool(row["regulating"]),
                )
                elm.control_bus = bus_dict.get(row["regulated_bus_id"], None)
                grid.add_controllable_shunt(bus=bus1, api_obj=elm)

            return grid
