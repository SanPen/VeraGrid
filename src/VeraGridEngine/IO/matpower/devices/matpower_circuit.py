# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import List
import numpy as np

from VeraGridEngine.IO.matpower.devices.branch import MatpowerBranch
from VeraGridEngine.IO.matpower.devices.bus import MatpowerBus
from VeraGridEngine.IO.matpower.devices.area import MatpowerArea
from VeraGridEngine.IO.matpower.devices.generator import MatpowerGenerator
from VeraGridEngine.IO.matpower.devices.bus_dc import MatAcDcBus
from VeraGridEngine.IO.matpower.devices.branch_dc import MatAcDcBranch
from VeraGridEngine.IO.matpower.devices.converter_dc import MatAcDcConverter
from VeraGridEngine.IO.matpower.matpower_utils import txt2mat, find_between
from VeraGridEngine.basic_structures import Logger


class MatpowerCircuit:

    def __init__(self):
        """
        Constructor
        """
        self.areas: List[MatpowerArea] = list()
        self.buses: List[MatpowerBus] = list()
        self.generators: List[MatpowerGenerator] = list()
        self.branches: List[MatpowerBranch] = list()

        self.dc_buses: List[MatAcDcBus] = list()
        self.converters: List[MatAcDcConverter] = list()
        self.dc_branches: List[MatAcDcBranch] = list()

        self.Sbase = 100.0

        self.logger = Logger()

    def read_file(self, file_name: str):
        """
        Read matpower .m file
        :param file_name:
        :return:
        """
        # open the file as text
        with open(file_name, 'r') as my_file:
            text = my_file.read()

        # split the file into its case variables (the case variables always start with 'mpc.')
        chunks = text.split('mpc.')

        buses_found = False

        # further process the loaded text
        for chunk in chunks:

            if ',' in chunk:
                chunk = chunk.replace(',', '')

            vals = chunk.split('=')
            key = vals[0].strip()

            if key == "baseMVA":
                v = find_between(chunk, '=', ';')
                self.Sbase = float(v)

            elif key == "bus":
                buses_found = True
                if chunk.startswith("bus_name"):
                    data = txt2mat(find_between(chunk, '{', '}'), line_splitter=';', to_float=False)
                    bus_names = np.ndarray.flatten(data)

                    if len(bus_names) == len(self.buses):
                        for i in range(len(bus_names)):
                            self.buses[i].name = bus_names[i]

                else:
                    data = txt2mat(find_between(chunk, '[', ']'), line_splitter=';')

                    for i in range(len(data)):
                        elm = MatpowerBus()
                        elm.parse_row(data[i])
                        self.buses.append(elm)

            elif key == "bus_name":
                data = find_between(chunk, '{', '}').split(";")
                # at this point all buses should be read
                n = len(self.buses)
                for i, name in enumerate(data):
                    if i < n:
                        self.buses[i].name = name.replace("\n", "").replace("\t", "").replace("'", "").strip()

            elif key == "areas":
                data = txt2mat(find_between(chunk, '[', ']'), line_splitter=';')

                for i in range(len(data)):
                    elm = MatpowerArea()
                    elm.parse_row(data[i])
                    self.areas.append(elm)

            elif key == "gencost":
                gen_cost_data = txt2mat(find_between(chunk, '[', ']'), line_splitter=';')

                if len(gen_cost_data) == len(self.generators):
                    for i in range(len(gen_cost_data)):
                        self.generators[i].parse_cost(row=gen_cost_data[i, :], logger=self.logger)

            elif key == "gen":
                data = txt2mat(find_between(chunk, '[', ']'), line_splitter=';')

                for i in range(len(data)):
                    elm = MatpowerGenerator()
                    elm.parse_row(data[i])
                    self.generators.append(elm)

            elif key == "branch":
                data = txt2mat(find_between(chunk, '[', ']'), line_splitter=';')

                for i in range(len(data)):
                    elm = MatpowerBranch()
                    elm.parse_row(data[i])
                    self.branches.append(elm)

            elif key in ["dcbus", "busdc"]:
                data = txt2mat(find_between(chunk, '[', ']'), line_splitter=';')

                for i in range(len(data)):
                    elm = MatAcDcBus()
                    elm.parse_row(data[i])
                    self.dc_buses.append(elm)

            elif key in ["dcconv", "convdc"]:
                data = txt2mat(find_between(chunk, '[', ']'), line_splitter=';')

                for i in range(len(data)):
                    elm = MatAcDcConverter()
                    elm.parse_row(data[i])
                    self.converters.append(elm)

            elif key in ["dcbranch", "branchdc"]:
                data = txt2mat(find_between(chunk, '[', ']'), line_splitter=';')

                for i in range(len(data)):
                    elm = MatAcDcBranch()
                    elm.parse_row(data[i])
                    self.dc_branches.append(elm)

        if "Ohms to p.u." in text:
            # convert branch impedance to p.u. like matpower does...
            Vbase = self.buses[0].base_kv * 1e3
            Sbase = self.Sbase * 1e6
            zbase = (Vbase * Vbase / Sbase)
            for branch in self.branches:
                branch.br_r /= zbase
                branch.br_x /= zbase

            self.logger.add_warning("Converted Ohms to p.u.")

        if "kW to MW" in text:
            for bus in self.buses:
                bus.pd /= 1e3
                bus.qd /= 1e3
            self.logger.add_warning("Converted kW to MW")

        # if self.Sbase != 100.0:
        #     self.logger.add_warning("Sbase was not 100, in VeraGrid it always should be 100MVA",
        #                             value=self.Sbase, expected_value=100.0)
        #     self.Sbase = 100.0

        if not buses_found:
            self.logger.add_error('No bus data')
