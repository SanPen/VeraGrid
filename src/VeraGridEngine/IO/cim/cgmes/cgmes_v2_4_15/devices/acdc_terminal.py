# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.bus_name_marker import BusNameMarker
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.measurement import Measurement
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.operational_limit_set import OperationalLimitSet

class ACDCTerminal(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='BusNameMarker', class_type='BusNameMarker', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The bus name marker used to name the bus (topological node).''', profiles=[]),
		CgmesProperty(property_name='Measurements', class_type='Measurement', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Measurements associated with this terminal defining  where the measurement is placed in the network topology.  It may be used, for instance, to capture the sensor position, such as a voltage transformer (PT) at a busbar or a current transformer (CT) at the bar between a breaker and an isolator.''', profiles=[]),
		CgmesProperty(property_name='sequenceNumber', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The orientation of the terminal connections for a multiple terminal conducting equipment.  The sequence numbering starts with 1 and additional terminals should follow in increasing order.   The first terminal is the &quot;starting point&quot; for a two terminal branch.''', profiles=[]),
		CgmesProperty(property_name='OperationalLimitSet', class_type='OperationalLimitSet', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''None''', profiles=[]),
		CgmesProperty(property_name='connected', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The connected status is related to a bus-branch model and the topological node to terminal relation.  True implies the terminal is connected to the related topological node and false implies it is not. 
In a bus-branch model, the connected status is used to tell if equipment is disconnected without having to change the connectivity described by the topological node to terminal relation. A valid case is that conducting equipment can be connected in one end and open in the other. In particular for an AC line segment, where the reactive line charging can be significant, this is a relevant case.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='ACDCTerminal'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.BusNameMarker: BusNameMarker | None = None
		self.Measurements: Measurement | None = None
		self.sequenceNumber: int = None
		self.OperationalLimitSet: OperationalLimitSet | None = None
		self.connected: bool = None
