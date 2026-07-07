# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.energy_connection import EnergyConnection
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.load_response_characteristic import LoadResponseCharacteristic

class EnergyConsumer(EnergyConnection):
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='pfixed', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[CgmesProfileType.EQ]),
        CgmesProperty(property_name='pfixedPct', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[CgmesProfileType.EQ]),
        CgmesProperty(property_name='qfixed', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[CgmesProfileType.EQ]),
        CgmesProperty(property_name='qfixedPct', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Percentage on a defined base.   For example, specify as 100 to indicate at the defined base.''', profiles=[CgmesProfileType.EQ]),
        CgmesProperty(property_name='LoadResponse', class_type='LoadResponseCharacteristic', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The load response characteristic of this load.  If missing, this load is assumed to be constant power.''', profiles=[CgmesProfileType.EQ]),
        CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', mandatory=True, profiles=[CgmesProfileType.SSH]),
        CgmesProperty(property_name='q', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', mandatory=True, profiles=[CgmesProfileType.SSH]),
    )
    __slots__ = ('pfixed', 'pfixedPct', 'qfixed', 'qfixedPct', 'LoadResponse', 'p', 'q')
    def __init__(self, rdfid='', tpe='EnergyConsumer'):
        EnergyConnection.__init__(self, rdfid, tpe)

        self.pfixed: float = None
        self.pfixedPct: float = None
        self.qfixed: float = None
        self.qfixedPct: float = None
        self.LoadResponse: LoadResponseCharacteristic | None = None
        self.p: float = None
        self.q: float = None
