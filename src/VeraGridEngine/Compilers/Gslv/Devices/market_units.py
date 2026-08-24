# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict

from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.Aggregation.market_unit import MarketUnit
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


def convert_market_unit(elm: MarketUnit) -> "pg.MarketUnit":
    """
    Convert one VeraGrid market unit into one GSLV market unit.

    :param elm: VeraGrid market unit.
    :return: GSLV market unit.
    """
    return pg.MarketUnit(name=elm.name,
                         code=str(elm.code),
                         idtag=elm.idtag,
                         color=elm.color)


def add_market_units(circuit: MultiCircuit) -> Dict[MarketUnit, "pg.MarketUnit"]:
    """
    Add every VeraGrid market unit to the target GSLV grid.

    :param circuit: VeraGrid circuit.
    :return: VeraGrid-to-GSLV market-unit lookup.
    """
    market_units_dict: Dict[MarketUnit, "pg.MarketUnit"] = dict()
    elm: MarketUnit
    market_unit: "pg.MarketUnit"

    for elm in circuit.market_units:
        market_unit = convert_market_unit(elm=elm)
        market_units_dict[elm] = market_unit

    return market_units_dict
