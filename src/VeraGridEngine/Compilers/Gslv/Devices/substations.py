# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Substation.substation import Substation
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from typing import Dict


def convert_substation(se: Substation, n_time: int) -> "pg.Substation":
    """

    :param se:
    :param n_time:
    :return:
    """
    return pg.Substation(
        nt=n_time,
        idtag=se.idtag,
        code=str(se.code),
        name=se.name
    )


def add_substations(circuit: MultiCircuit,
                    gslv_grid: "pg.MultiCircuit",
                    n_time: int) -> Dict[Substation, "pg.Substation"]:
    """
    Add GSLV substations
    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV Circuit
    :param n_time: number of time steps
    :return: Dictionary [VeraGrid Zone] -> GSLV Zone
    """
    d = dict()

    for i, se in enumerate(circuit.substations):
        elm = convert_substation(se, n_time=n_time)
        gslv_grid.add_substation(elm)
        d[se] = elm

    return d
