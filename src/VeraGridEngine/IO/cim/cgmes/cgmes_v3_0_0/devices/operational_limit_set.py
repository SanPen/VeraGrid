# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.acdc_terminal import ACDCTerminal
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equipment import Equipment
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.operational_limit import OperationalLimit

class OperationalLimitSet(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='Terminal', class_type='ACDCTerminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The terminal where the operational limit set apply.''', profiles=[]),
		CgmesProperty(property_name='Equipment', class_type='Equipment', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The equipment to which the limit set applies.''', profiles=[]),
		CgmesProperty(property_name='OperationalLimitValue', class_type='OperationalLimit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Values of equipment limits.''', profiles=[]),
	)
	__slots__ = ('Terminal', 'Equipment', 'OperationalLimitValue')
	def __init__(self, rdfid='', tpe='OperationalLimitSet'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.Terminal: ACDCTerminal | None = None
		self.Equipment: Equipment | None = None
		self.OperationalLimitValue: OperationalLimit | None = None
