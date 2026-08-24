# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Dict

from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.Associations.emission_gas import EmissionGas
from VeraGridEngine.Devices.Associations.fuel import Fuel
from VeraGridEngine.Devices.Associations.technology import Technology
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


def convert_technology(elm: Technology) -> "pg.Technology":
    """
    Convert one VeraGrid technology into one GSLV technology.

    :param elm: VeraGrid technology.
    :return: GSLV technology.
    """
    technology: pg.Technology = pg.Technology(idtag=elm.idtag, code=str(elm.code), name=elm.name)
    technology.name2 = elm.name2
    technology.name3 = elm.name3
    technology.name4 = elm.name4
    technology.color = elm.color
    return technology


def convert_fuel(elm: Fuel) -> "pg.Fuel":
    """
    Convert one VeraGrid fuel into one GSLV fuel.

    :param elm: VeraGrid fuel.
    :return: GSLV fuel.
    """
    fuel: pg.Fuel = pg.Fuel(idtag=elm.idtag, code=str(elm.code), name=elm.name)
    fuel.cost = elm.cost
    fuel.color = elm.color
    return fuel


def convert_emission_gas(elm: EmissionGas) -> "pg.EmissionGas":
    """
    Convert one VeraGrid emission gas into one GSLV emission gas.

    :param elm: VeraGrid emission gas.
    :return: GSLV emission gas.
    """
    emission_gas: pg.EmissionGas = pg.EmissionGas(idtag=elm.idtag, code=str(elm.code), name=elm.name)
    emission_gas.cost = elm.cost
    emission_gas.color = elm.color
    return emission_gas


def add_technologies(circuit: MultiCircuit, gslv_grid: "pg.MultiCircuit") -> Dict[Technology, "pg.Technology"]:
    """
    Add every VeraGrid technology to the target GSLV grid.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: GSLV circuit.
    :return: VeraGrid-to-GSLV technology lookup.
    """
    technology_dict: Dict[Technology, pg.Technology] = dict()

    for elm in circuit.technologies:
        technology: pg.Technology = convert_technology(elm=elm)
        gslv_grid.add_technology(technology)
        technology_dict[elm] = technology

    return technology_dict


def add_fuels(circuit: MultiCircuit, gslv_grid: "pg.MultiCircuit") -> Dict[Fuel, "pg.Fuel"]:
    """
    Add every VeraGrid fuel to the target GSLV grid.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: GSLV circuit.
    :return: VeraGrid-to-GSLV fuel lookup.
    """
    fuel_dict: Dict[Fuel, pg.Fuel] = dict()

    for elm in circuit.fuels:
        fuel: pg.Fuel = convert_fuel(elm=elm)
        gslv_grid.add_fuel(fuel)
        fuel_dict[elm] = fuel

    return fuel_dict


def add_emission_gases(circuit: MultiCircuit, gslv_grid: "pg.MultiCircuit") -> Dict[EmissionGas, "pg.EmissionGas"]:
    """
    Add every VeraGrid emission gas to the target GSLV grid.

    :param circuit: VeraGrid circuit.
    :param gslv_grid: GSLV circuit.
    :return: VeraGrid-to-GSLV emission gas lookup.
    """
    emission_gas_dict: Dict[EmissionGas, pg.EmissionGas] = dict()

    for elm in circuit.emission_gases:
        emission_gas: pg.EmissionGas = convert_emission_gas(elm=elm)
        gslv_grid.add_emission_gas(emission_gas)
        emission_gas_dict[elm] = emission_gas

    return emission_gas_dict
