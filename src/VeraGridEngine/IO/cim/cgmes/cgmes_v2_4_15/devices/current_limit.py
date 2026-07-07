# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.operational_limit import OperationalLimit
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

class CurrentLimit(OperationalLimit):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='value', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the 
			conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[]),
	)
	__slots__ = ('value',)
	def __init__(self, rdfid='', tpe='CurrentLimit'):
		OperationalLimit.__init__(self, rdfid, tpe)

		self.value: float = None
