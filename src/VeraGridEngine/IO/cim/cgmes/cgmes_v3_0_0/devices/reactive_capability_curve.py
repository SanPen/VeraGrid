# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.curve import Curve
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.equivalent_injection import EquivalentInjection
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.synchronous_machine import SynchronousMachine

class ReactiveCapabilityCurve(Curve):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='EquivalentInjection', class_type='EquivalentInjection', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The equivalent injection using this reactive capability curve.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='InitiallyUsedBySynchronousMachines', class_type='SynchronousMachine', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Synchronous machines using this curve as default.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
	)
	__slots__ = ('EquivalentInjection', 'InitiallyUsedBySynchronousMachines')
	def __init__(self, rdfid='', tpe='ReactiveCapabilityCurve'):
		Curve.__init__(self, rdfid, tpe)

		self.EquivalentInjection: EquivalentInjection | None = None
		self.InitiallyUsedBySynchronousMachines: SynchronousMachine | None = None
