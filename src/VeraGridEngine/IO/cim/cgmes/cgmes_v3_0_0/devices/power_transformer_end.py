# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.transformer_end import TransformerEnd
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import WindingConnection, UnitSymbol, CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_transformer import PowerTransformer

class PowerTransformerEnd(TransformerEnd):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='PowerTransformer', class_type='PowerTransformer', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The power transformer of this power transformer end.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='b', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='connectionKind', class_type=WindingConnection, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Kind of connection.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='ratedS', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VA, description='''Product of the RMS value of the voltage and the RMS value of the current.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='g', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='ratedU', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='r', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='x', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.EQ]),
		CgmesProperty(property_name='b0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Imaginary part of admittance.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='phaseAngleClock', class_type=int, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Terminal voltage phase angle displacement where 360 degrees are represented with clock hours. The valid values are 0 to 11. For example, for the secondary side end of a transformer with vector group code of 'Dyn11', specify the connection kind as wye with neutral and specify the phase angle of the clock as 11.  The clock value of the transformer end number specified as 1, is assumed to be zero.  Note the transformer end number is not assumed to be the same as the terminal sequence number.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='g0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.S, description='''Factor by which voltage must be multiplied to give corresponding power lost from a circuit. Real part of admittance.''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='r0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Resistance (real part of impedance).''', mandatory=True, profiles=[CgmesProfileType.SC]),
		CgmesProperty(property_name='x0', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.ohm, description='''Reactance (imaginary part of impedance), at rated frequency.''', mandatory=True, profiles=[CgmesProfileType.SC]),
	)
	__slots__ = ('PowerTransformer', 'b', 'connectionKind', 'ratedS', 'g', 'ratedU', 'r', 'x', 'b0', 'phaseAngleClock', 'g0', 'r0', 'x0')
	def __init__(self, rdfid='', tpe='PowerTransformerEnd'):
		TransformerEnd.__init__(self, rdfid, tpe)

		self.PowerTransformer: PowerTransformer | None = None
		self.b: float = None
		self.connectionKind: WindingConnection = None
		self.ratedS: float = None
		self.g: float = None
		self.ratedU: float = None
		self.r: float = None
		self.x: float = None
		self.b0: float = None
		self.phaseAngleClock: int = None
		self.g0: float = None
		self.r0: float = None
		self.x0: float = None
