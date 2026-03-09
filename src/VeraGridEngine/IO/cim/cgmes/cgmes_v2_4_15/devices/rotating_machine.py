# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.regulating_cond_eq import RegulatingCondEq
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.generating_unit import GeneratingUnit
	from VeraGridEngine.IO.cim.cgmes.cgmes_v2_4_15.devices.hydro_pump import HydroPump

class RotatingMachine(RegulatingCondEq):
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='GeneratingUnit', class_type='GeneratingUnit', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A synchronous machine may operate as a generator and as such becomes a member of a generating unit.''', profiles=[]),
        CgmesProperty(property_name='HydroPump', class_type='HydroPump', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The synchronous machine drives the turbine which moves the water from a low elevation to a higher elevation. The direction of machine rotation for pumping may or may not be the same as for generating.''', profiles=[]),
        CgmesProperty(property_name='ratedPowerFactor', class_type=float, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''A floating point number. The range is unspecified and not limited.''', profiles=[]),
        CgmesProperty(property_name='ratedS', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VA, description='''Product of the RMS value of the voltage and the RMS value of the current.''', profiles=[]),
        CgmesProperty(property_name='ratedU', class_type=float, multiplier=UnitMultiplier.k, unit=UnitSymbol.V, description='''Electrical voltage, can be both AC and DC.''', profiles=[]),
        CgmesProperty(property_name='p', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.W, description='''Product of RMS value of the voltage and the RMS value of the in-phase component of the current.''', profiles=[]),
        CgmesProperty(property_name='q', class_type=float, multiplier=UnitMultiplier.M, unit=UnitSymbol.VAr, description='''Product of RMS value of the voltage and the RMS value of the quadrature component of the current.''', profiles=[]),
    )
    def __init__(self, rdfid='', tpe='RotatingMachine'):
        RegulatingCondEq.__init__(self, rdfid, tpe)

        self.GeneratingUnit: GeneratingUnit | None = None
        self.HydroPump: HydroPump | None = None
        self.ratedPowerFactor: float = None
        self.ratedS: float = None
        self.ratedU: float = None
        self.p: float = None
        self.q: float = None
