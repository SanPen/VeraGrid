# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conducting_equipment import ConductingEquipment
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.sv_switch import SvSwitch

class Switch(ConductingEquipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='normalOpen', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The attribute is used in cases when no Measurement for the status value is present. If the Switch has a status measurement the Discrete.normalValue is expected to match with the Switch.normalOpen.''', mandatory=True, profiles=[CgmesProfileType.EQ], default_value=False),
		CgmesProperty(property_name='ratedCurrent', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.A, description='''Electrical current with sign convention: positive flow is out of the conducting equipment into the connectivity node. Can be both AC and DC.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='retained', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Branch is retained in the topological solution.  The flow through retained switches will normally be calculated in power flow.''', mandatory=True, profiles=[CgmesProfileType.EQ], default_value=False),
		CgmesProperty(property_name='SvSwitch', class_type='SvSwitch', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The switch state associated with the switch.''', profiles=[CgmesProfileType.SV]),
		CgmesProperty(property_name='open', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The attribute tells if the switch is considered open when used as input to topology processing.''', mandatory=True, profiles=[CgmesProfileType.SSH], default_value=False),
		CgmesProperty(property_name='locked', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''If true, the switch is locked. The resulting switch state is a combination of locked and Switch.open attributes as follows:
<ul>
	<li>locked=true and Switch.open=true. The resulting state is open and locked;</li>
	<li>locked=false and Switch.open=true. The resulting state is open;</li>
	<li>locked=false and Switch.open=false. The resulting state is closed.</li>
</ul>''', mandatory=True, profiles=[CgmesProfileType.SSH], default_value=False),
	)
	__slots__ = ('normalOpen', 'ratedCurrent', 'retained', 'SvSwitch', 'open', 'locked')
	def __init__(self, rdfid='', tpe='Switch'):
		ConductingEquipment.__init__(self, rdfid, tpe)

		self.normalOpen: bool = None
		self.ratedCurrent: float = None
		self.retained: bool = None
		self.SvSwitch: SvSwitch | None = None
		self.open: bool = None
		self.locked: bool = None
