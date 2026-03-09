# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import OperationalLimitDirectionKind, LimitTypeKind, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.operational_limit import OperationalLimit

class OperationalLimitType(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='OperationalLimit', class_type='OperationalLimit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The operational limits associated with this type of limit.''', profiles=[]),
		CgmesProperty(property_name='acceptableDuration', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.s, description='''Time, in seconds.''', profiles=[]),
		CgmesProperty(property_name='limitType', class_type=LimitTypeKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Types of limits defined in the ENTSO-E Operational Handbook Policy 3.''', profiles=[]),
		CgmesProperty(property_name='direction', class_type=OperationalLimitDirectionKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The direction of the limit.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='OperationalLimitType'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.OperationalLimit: OperationalLimit | None = None
		self.acceptableDuration: float = None
		self.limitType: LimitTypeKind = None
		self.direction: OperationalLimitDirectionKind = None
