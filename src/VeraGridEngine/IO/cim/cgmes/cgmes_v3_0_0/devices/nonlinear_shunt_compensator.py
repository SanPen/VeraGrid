# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.shunt_compensator import ShuntCompensator
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.nonlinear_shunt_compensator_point import \
		NonlinearShuntCompensatorPoint

class NonlinearShuntCompensator(ShuntCompensator):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='NonlinearShuntCompensatorPoints', class_type='NonlinearShuntCompensatorPoint', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''All points of the non-linear shunt compensator.''', profiles=[]),
	)
	def __init__(self, rdfid='', tpe='NonlinearShuntCompensator'):
		ShuntCompensator.__init__(self, rdfid, tpe)

		self.NonlinearShuntCompensatorPoints: NonlinearShuntCompensatorPoint | None = None
