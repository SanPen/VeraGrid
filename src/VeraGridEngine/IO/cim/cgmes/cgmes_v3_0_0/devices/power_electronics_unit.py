# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equipment import Equipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_electronics_connection import PowerElectronicsConnection

class PowerElectronicsUnit(Equipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='PowerElectronicsConnection', class_type='PowerElectronicsConnection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A power electronics unit has a connection to the AC network.''', profiles=[]),
		CgmesProperty(property_name='maxP', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
		CgmesProperty(property_name='minP', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='PowerElectronicsUnit'):
		Equipment.__init__(self, rdfid, tpe)

		self.PowerElectronicsConnection: PowerElectronicsConnection | None = None
		self.maxP: float = None
		self.minP: float = None
