# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.country import Country
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from typing import Dict

def convert_country(country: Country) -> "pg.Country":
    """

    :param country:
    :return:
    """
    return pg.Country(idtag=country.idtag, code=str(country.code), name=country.name)


def add_countries(circuit: MultiCircuit,
                  gslv_grid: "pg.MultiCircuit") -> Dict[Country, "pg.Country"]:
    """
    Add GSLV countries
    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV Circuit
    :return: Dictionary [VeraGrid country] -> GSLV country
    """
    d = dict()

    for i, country in enumerate(circuit.countries):
        elm = convert_country(country)
        gslv_grid.add_country(elm)
        d[country] = elm

    return d

