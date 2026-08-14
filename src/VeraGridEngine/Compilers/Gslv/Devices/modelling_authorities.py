# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.modelling_authority import ModellingAuthority
from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from typing import Dict


def convert_modelling_authority(elm: ModellingAuthority) -> "pg.ModellingAuthority":
    """

    :param elm:
    :return:
    """
    return pg.ModellingAuthority(idtag=elm.idtag,
                                 code=str(elm.code),
                                 name=elm.name)


def add_modelling_authorities(circuit: MultiCircuit,
                              gslv_grid: "pg.MultiCircuit") -> Dict[ModellingAuthority, "pg.ModellingAuthority"]:
    """

    :param circuit:
    :param gslv_grid:
    :return:
    """
    d = dict()

    for i, elm in enumerate(circuit.modelling_authorities):
        ma = convert_modelling_authority(elm)
        gslv_grid.add_modelling_authority(ma)
        d[elm] = ma

    return d
