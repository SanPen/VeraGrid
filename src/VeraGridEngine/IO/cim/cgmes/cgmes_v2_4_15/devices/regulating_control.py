# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.power_system_resource import PowerSystemResource
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import RegulatingControlModeKind, UnitMultiplier
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.regulating_cond_eq import RegulatingCondEq
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal

class RegulatingControl(PowerSystemResource):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='Terminal', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The controls regulating this terminal.''', profiles=[]),
		CgmesProperty(property_name='RegulatingCondEq', class_type='RegulatingCondEq', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The equipment that participates in this regulating control scheme.''', profiles=[]),
		CgmesProperty(property_name='mode', class_type=RegulatingControlModeKind, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The regulating control mode presently available.  This specification allows for determining the kind of regulation without need for obtaining the units from a schedule.''', profiles=[]),
		CgmesProperty(property_name='discrete', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The regulation is performed in a discrete mode. This applies to equipment with discrete controls, e.g. tap changers and shunt compensators.''', profiles=[]),
		CgmesProperty(property_name='enabled', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The flag tells if regulation is enabled.''', profiles=[]),
		CgmesProperty(property_name='targetDeadband', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', profiles=[]),
		CgmesProperty(property_name='targetValue', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', profiles=[]),
		CgmesProperty(property_name='targetValueUnitMultiplier', class_type=UnitMultiplier, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Specify the multiplier for used for the targetValue.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='RegulatingControl'):
		PowerSystemResource.__init__(self, rdfid, tpe)

		self.Terminal: Terminal | None = None
		self.RegulatingCondEq: RegulatingCondEq | None = None
		self.mode: RegulatingControlModeKind = None
		self.discrete: bool = None
		self.enabled: bool = None
		self.targetDeadband: float = None
		self.targetValue: float = None
		self.targetValueUnitMultiplier: UnitMultiplier = None
