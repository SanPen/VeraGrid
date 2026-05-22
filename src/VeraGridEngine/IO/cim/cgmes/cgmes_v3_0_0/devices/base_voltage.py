# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conducting_equipment import ConductingEquipment
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.topological_node import TopologicalNode
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.transformer_end import TransformerEnd
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.voltage_level import VoltageLevel

class BaseVoltage(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='nominalVoltage', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', mandatory=True, profiles=[CgmesProfileType.EQ, CgmesProfileType.EQ_BD]),
		CgmesProperty(property_name='ConductingEquipment', class_type='ConductingEquipment', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''All conducting equipment with this base voltage.  Use only when there is no voltage level container used and only one base voltage applies.  For example, not used for transformers.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='VoltageLevel', class_type='VoltageLevel', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The voltage levels having this base voltage.''', profiles=[CgmesProfileType.EQ, CgmesProfileType.EQ_BD]),
		CgmesProperty(property_name='TransformerEnds', class_type='TransformerEnd', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Transformer ends at the base voltage.  This is essential for PU calculation.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='TopologicalNode', class_type='TopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The topological nodes at the base voltage.''', profiles=[CgmesProfileType.TP]),
	)
	__slots__ = ('nominalVoltage', 'ConductingEquipment', 'VoltageLevel', 'TransformerEnds', 'TopologicalNode')
	def __init__(self, rdfid='', tpe='BaseVoltage'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.nominalVoltage: float = None

		self.ConductingEquipment: ConductingEquipment | None = None

		self.VoltageLevel: VoltageLevel | None = None

		self.TransformerEnds: TransformerEnd | None = None

		self.TopologicalNode: TopologicalNode | None = None
