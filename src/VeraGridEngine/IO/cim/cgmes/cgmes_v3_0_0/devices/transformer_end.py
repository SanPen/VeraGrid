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
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.base_voltage import BaseVoltage
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.phase_tap_changer import PhaseTapChanger
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.ratio_tap_changer import RatioTapChanger
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.terminal import Terminal

class TransformerEnd(IdentifiedObject):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='BaseVoltage', class_type='BaseVoltage', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Base voltage of the transformer end.  This is essential for PU calculation.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='PhaseTapChanger', class_type='PhaseTapChanger', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Phase tap changer associated with this transformer end.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='RatioTapChanger', class_type='RatioTapChanger', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Ratio tap changer associated with this transformer end.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='Terminal', class_type='Terminal', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Terminal of the power transformer to which this transformer end belongs.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='endNumber', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Number for this transformer end, corresponding to the end's order in the power transformer vector group or phase angle clock number.  Highest voltage winding should be 1.  Each end within a power transformer should have a unique subsequent end number.   Note the transformer end number need not match the terminal sequence number.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='rground', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='grounded', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''(for Yn and Zn connections) True if the neutral is solidly grounded.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='xground', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', profiles=[CgmesProfileType.SC]),
	)
	__slots__ = ('BaseVoltage', 'PhaseTapChanger', 'RatioTapChanger', 'Terminal', 'endNumber', 'rground', 'grounded', 'xground')
	def __init__(self, rdfid='', tpe='TransformerEnd'):
		IdentifiedObject.__init__(self, rdfid, tpe)

		self.BaseVoltage: BaseVoltage | None = None
		self.PhaseTapChanger: PhaseTapChanger | None = None
		self.RatioTapChanger: RatioTapChanger | None = None
		self.Terminal: Terminal | None = None
		self.endNumber: int = None
		self.rground: float = None
		self.grounded: bool = None
		self.xground: float = None
