# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.equipment import Equipment
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.base_voltage import BaseVoltage
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.sv_status import SvStatus
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.terminal import Terminal

class ConductingEquipment(Equipment):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='BaseVoltage', class_type='BaseVoltage', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''All conducting equipment with this base voltage.  
			Use only when there is no voltage level container used and only one base voltage applies.  
			For example, not used for transformers.''', profiles=[]),
		CgmesProperty(property_name='Terminals', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Conducting equipment have terminals that may be connected to other 
			conducting equipment terminals via connectivity nodes or topological nodes.''', profiles=[]),
		CgmesProperty(property_name='SvStatus', class_type='SvStatus', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The status state variable associated with this conducting equipment.''', profiles=[]),
	)
	__slots__ = ('BaseVoltage', 'Terminals', 'SvStatus')
	def __init__(self, rdfid='', tpe='ConductingEquipment'):
		Equipment.__init__(self, rdfid, tpe)

		self.BaseVoltage: BaseVoltage | None = None
		self.Terminals: Terminal | None = None
		self.SvStatus: SvStatus | None = None
