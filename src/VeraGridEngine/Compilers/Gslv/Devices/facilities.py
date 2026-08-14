# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.facility import Facility
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from typing import Dict

def convert_facility(elm: Facility) -> "pg.Facility":
    """

    :param elm:
    :return:
    """
    return pg.Facility(idtag=elm.idtag,
                       code=str(elm.code),
                       name=elm.name)


def add_facilities(circuit: MultiCircuit,
                   gslv_grid: "pg.MultiCircuit") -> Dict[Facility, "pg.Facility"]:
    """

    :param circuit:
    :param gslv_grid:
    :return:
    """
    d = dict()

    for i, elm in enumerate(circuit.facilities):
        facility = convert_facility(elm)
        gslv_grid.add_facility(facility)
        d[elm] = facility

    return d

