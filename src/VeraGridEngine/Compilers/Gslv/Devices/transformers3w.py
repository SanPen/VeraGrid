# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from VeraGridEngine.Devices.Aggregation.branch_group import BranchGroup
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.transformer3w import Transformer3W
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Compilers.Gslv.activation import (
    pg,
    tap_module_control_mode_dict,
    tap_phase_control_mode_dict,
    winding_type_dict,
    windings_connection_dict,
)
from VeraGridEngine.Compilers.Gslv.common import fill_profile
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import IntVec
from typing import (
    Dict,
    Union,
)


def convert_transformer3w(elm: Transformer3W,
                          bus_dict: Dict[str, "pg.Bus"],
                          n_time: int,
                          use_time_series: bool,
                          time_indices: IntVec | None,
                          override_controls: bool) -> "pg.Transformer3W":
    """

    :param elm:
    :param bus_dict:
    :param n_time:
    :param use_time_series:
    :param time_indices:
    :param override_controls:
    :return:
    """

    tr3 = pg.Transformer3W(idtag=elm.idtag,
                           code=str(elm.code),
                           name=elm.name,
                           nt=n_time,
                           active=elm.active,
                           bus1=bus_dict[elm.bus1.idtag] if elm.bus1 else None,
                           bus2=bus_dict[elm.bus2.idtag] if elm.bus2 else None,
                           bus3=bus_dict[elm.bus3.idtag] if elm.bus3 else None,
                           V1=elm.V1,
                           V2=elm.V2,
                           V3=elm.V3,
                           r12=elm.r12, r23=elm.r23, r31=elm.r31,
                           x12=elm.x12, x23=elm.x23, x31=elm.x31,
                           rate12=elm.rate1, rate23=elm.rate2, rate31=elm.rate3)

    # this is because the central node is in the buses list already from VeraGrid
    tr3.central_node = bus_dict[elm.bus0.idtag]

    return tr3


def add_transformers3w(circuit: MultiCircuit,
                       gslv_grid: "pg.MultiCircuit",
                       bus_dict: Dict[str, "pg.Bus"],
                       time_series: bool,
                       n_time=1,
                       time_indices: Union[IntVec, None] = None,
                       override_controls=False):
    """

    :param circuit: VeraGrid circuit
    :param gslv_grid: GSLV circuit
    :param time_series: compile the time series from VeraGrid? otherwise just the snapshot
    :param bus_dict: dictionary of bus id to GSLV bus object
    :param n_time: number of time steps
    :param time_indices: Array of time indices
    :param override_controls: If true the controls are set to Fix
    """
    for i, elm in enumerate(circuit.transformers3w):
        tr3 = convert_transformer3w(elm=elm, bus_dict=bus_dict, n_time=n_time,
                                    use_time_series=time_series, time_indices=time_indices,
                                    override_controls=override_controls)

        # because the central bus was added already, do not add it here
        gslv_grid.add_transformer_3w(tr3)
