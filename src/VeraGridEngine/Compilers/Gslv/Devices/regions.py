# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.country import Country
from VeraGridEngine.Devices.Aggregation.region import Region
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from typing import Dict


def convert_region(country: Region) -> "pg.Region":
    """

    :param country:
    :return:
    """
    return pg.Region(idtag=country.idtag, code=str(country.code), name=country.name)


def add_regions(circuit: MultiCircuit,
                gslv_grid: "pg.MultiCircuit") -> Dict[Country, "pg.Country"]:
    """
    Add GSLV countries
    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV Circuit
    :return: Dictionary [VeraGrid country] -> GSLV country
    """
    d = dict()

    for region in circuit.regions:
        elm = convert_region(region)
        gslv_grid.add_region(elm)
        d[region] = elm

    return d
