# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.branch_group import BranchGroup
from VeraGridEngine.Compilers.Gslv.activation import (
    group_type_dict,
    pg,
)
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from typing import Dict

def convert_branch_group(country: BranchGroup) -> "pg.BranchGroup":
    """

    :param country:
    :return:
    """
    return pg.BranchGroup(
        idtag=country.idtag,
        code=str(country.code),
        name=country.name,
        group_type=group_type_dict[country.group_type]
    )


def add_branch_groups(circuit: MultiCircuit,
                      gslv_grid: "pg.MultiCircuit") -> Dict[BranchGroup, "pg.BranchGroup"]:
    """
    Add GSLV countries
    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV Circuit
    :return: Dictionary [VeraGrid country] -> GSLV country
    """
    d = dict()

    for i, branch_group in enumerate(circuit.branch_groups):
        elm = convert_branch_group(branch_group)
        gslv_grid.add_branch_group(elm)
        d[branch_group] = elm

    return d

