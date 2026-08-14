# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.area import Area
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from typing import Dict

def convert_area(area: Area) -> "pg.Area":
    """
    
    :param area:
    :return:
    """
    return pg.Area(idtag=area.idtag, code=str(area.code), name=area.name)


def add_areas(circuit: MultiCircuit,
              gslv_grid: "pg.MultiCircuit") -> Dict[Area, "pg.Area"]:
    """
    Add GSLV Areas
    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV Circuit
    :return: Dictionary [VeraGrid area] -> GSLV Area
    """
    d = dict()

    for i, area in enumerate(circuit.areas):
        elm = convert_area(area)
        gslv_grid.add_area(elm)
        d[area] = elm

    return d

