# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.curve import Curve
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.equivalent_injection import EquivalentInjection
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.synchronous_machine import SynchronousMachine

class ReactiveCapabilityCurve(Curve):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='EquivalentInjection', class_type='EquivalentInjection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The reactive capability curve used by this equivalent injection.''', profiles=[]),
		CgmesProperty(property_name='InitiallyUsedBySynchronousMachines', class_type='SynchronousMachine', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The default reactive capability curve for use by a synchronous machine.''', profiles=[]),
	)
	__slots__ = ('EquivalentInjection', 'InitiallyUsedBySynchronousMachines')
	def __init__(self, rdfid='', tpe='ReactiveCapabilityCurve'):
		Curve.__init__(self, rdfid, tpe)

		self.EquivalentInjection: EquivalentInjection | None = None
		self.InitiallyUsedBySynchronousMachines: SynchronousMachine | None = None
