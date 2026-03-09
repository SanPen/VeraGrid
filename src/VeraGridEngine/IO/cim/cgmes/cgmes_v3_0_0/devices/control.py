# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING
import datetime
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.io_point import IOPoint
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.power_system_resource import PowerSystemResource

class Control(IOPoint):
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='controlType', class_type=str, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Specifies the type of Control. For example, this specifies if the Control represents BreakerOpen, BreakerClose, GeneratorVoltageSetPoint, GeneratorRaise, GeneratorLower, etc.''', profiles=[]),
        CgmesProperty(property_name='operationInProgress', class_type=bool, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Indicates that a client is currently sending control commands that has not completed.''', profiles=[]),
        CgmesProperty(property_name='timeStamp', class_type=datetime.datetime, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The last time a control output was sent.''', profiles=[]),
        CgmesProperty(property_name='unitMultiplier', class_type=UnitMultiplier, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The unit multiplier of the controlled quantity.''', profiles=[]),
        CgmesProperty(property_name='unitSymbol', class_type=UnitSymbol, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The unit of measure of the controlled quantity.''', profiles=[]),
        CgmesProperty(property_name='PowerSystemResource', class_type='PowerSystemResource', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Regulating device governed by this control output.''', profiles=[]),
    )
    def __init__(self, rdfid='', tpe='Control'):
        IOPoint.__init__(self, rdfid, tpe)

        self.controlType: str = None
        self.operationInProgress: bool = None

        self.timeStamp: datetime.datetime | None = None
        self.unitMultiplier: UnitMultiplier = None
        self.unitSymbol: UnitSymbol = None

        self.PowerSystemResource: PowerSystemResource | None = None
