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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.vs_converter import VsConverter

class VsCapabilityCurve(Curve):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='VsConverterDCSides', class_type='VsConverter', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Capability curve of this converter.''', profiles=[]),
	)
	__slots__ = ('VsConverterDCSides',)
	def __init__(self, rdfid='', tpe='VsCapabilityCurve'):
		Curve.__init__(self, rdfid, tpe)

		self.VsConverterDCSides: VsConverter | None = None
