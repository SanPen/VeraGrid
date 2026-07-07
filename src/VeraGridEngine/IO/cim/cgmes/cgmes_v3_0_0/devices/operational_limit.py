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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.operational_limit_set import OperationalLimitSet
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.operational_limit_type import OperationalLimitType

class OperationalLimit(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='OperationalLimitSet', class_type='OperationalLimitSet', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The limit set to which the limit values belong.''', profiles=[]),
		CgmesProperty(property_name='OperationalLimitType', class_type='OperationalLimitType', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The limit type associated with this limit.''', profiles=[]),
	)
	__slots__ = ('OperationalLimitSet', 'OperationalLimitType')
	def __init__(self, rdfid='', tpe='OperationalLimit'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.OperationalLimitSet: OperationalLimitSet | None = None
		self.OperationalLimitType: OperationalLimitType | None = None
