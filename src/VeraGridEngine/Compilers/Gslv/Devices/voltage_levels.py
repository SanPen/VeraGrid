# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.zone import Zone
from VeraGridEngine.Devices.Substation.substation import Substation
from VeraGridEngine.Devices.Substation.voltage_level import VoltageLevel
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from typing import Dict


def convert_voltage_level(elm: VoltageLevel,
                          substations_dict: Dict[Substation, "pg.Substation"]) -> "pg.VoltageLevel":
    """

    :param elm:
    :param substations_dict:
    :return:
    """
    return pg.VoltageLevel(
        idtag=elm.idtag,
        code=str(elm.code),
        name=elm.name,
        Vnom=elm.Vnom,
        substation=substations_dict.get(elm.substation, None)
    )


def add_voltage_levels(
        circuit: MultiCircuit,
        gslv_grid: "pg.MultiCircuit",
        substations_dict: Dict[Substation, "pg.Substation"]
) -> Dict[VoltageLevel, "pg.VoltageLevel"]:
    """
    Add GSLV substations
    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV Circuit
    :param substations_dict: substations mapping dictionary
    :return: Dictionary [VeraGrid Zone] -> GSLV Zone
    """
    d = dict()

    for i, vl in enumerate(circuit.voltage_levels):
        elm = convert_voltage_level(vl, substations_dict=substations_dict)
        gslv_grid.add_voltage_level(elm)
        d[vl] = elm

    return d
