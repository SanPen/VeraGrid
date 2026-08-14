# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.zone import Zone
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from typing import Dict


def convert_zone(zone: Zone) -> "pg.Zone":
    """

    :param zone:
    :return:
    """
    return pg.Zone(idtag=zone.idtag, code=str(zone.code), name=zone.name)


def add_zones(circuit: MultiCircuit,
              gslv_grid: "pg.MultiCircuit") -> Dict[Zone, "pg.Zone"]:
    """
    Add GSLV Zones
    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV Circuit
    :return: Dictionary [VeraGrid Zone] -> GSLV Zone
    """
    d = dict()

    for i, zone in enumerate(circuit.zones):
        elm = convert_zone(zone)
        gslv_grid.add_zone(elm)
        d[zone] = elm

    return d
