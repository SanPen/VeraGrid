# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equipment import Equipment
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.hydro_power_plant import HydroPowerPlant
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.rotating_machine import RotatingMachine

class HydroPump(Equipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='HydroPowerPlant', class_type='HydroPowerPlant', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The hydro pump may be a member of a pumped storage plant or a pump for distributing water.''', profiles=[]),
		CgmesProperty(property_name='RotatingMachine', class_type='RotatingMachine', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The synchronous machine drives the turbine which moves the water from a low elevation to a higher elevation. The direction of machine rotation for pumping may or may not be the same as for generating.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='HydroPump'):
		Equipment.__init__(self, rdfid, tpe)

		self.HydroPowerPlant: HydroPowerPlant | None = None
		self.RotatingMachine: RotatingMachine | None = None
