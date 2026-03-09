# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, TYPE_CHECKING
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty

if TYPE_CHECKING:
	pass

class FullModel(IdentifiedObject):
    LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
        CgmesProperty(property_name='scenarioTime', class_type=str, description="scenarioTime.", profiles=[CgmesProfileType.TP_BD, CgmesProfileType.DL, CgmesProfileType.SSH, CgmesProfileType.EQ,
                      CgmesProfileType.DY, CgmesProfileType.TP, CgmesProfileType.EQ_BD, CgmesProfileType.GL,
                      CgmesProfileType.SV]),
        CgmesProperty(property_name='created', class_type=str, description="Creation date.", profiles=[CgmesProfileType.TP_BD, CgmesProfileType.DL, CgmesProfileType.SSH, CgmesProfileType.EQ,
                      CgmesProfileType.DY, CgmesProfileType.TP, CgmesProfileType.EQ_BD, CgmesProfileType.GL,
                      CgmesProfileType.SV]),
        CgmesProperty(property_name='version', class_type=int, description="version.", profiles=[CgmesProfileType.TP_BD, CgmesProfileType.DL, CgmesProfileType.SSH, CgmesProfileType.EQ,
                      CgmesProfileType.DY, CgmesProfileType.TP, CgmesProfileType.EQ_BD, CgmesProfileType.GL,
                      CgmesProfileType.SV]),
        CgmesProperty(property_name='profile', class_type=str, description="profile.", profiles=[CgmesProfileType.TP_BD, CgmesProfileType.DL, CgmesProfileType.SSH, CgmesProfileType.EQ,
                      CgmesProfileType.DY, CgmesProfileType.TP, CgmesProfileType.EQ_BD, CgmesProfileType.GL,
                      CgmesProfileType.SV]),
        CgmesProperty(property_name='modelingAuthoritySet', class_type=str, description="modelingAuthoritySet", profiles=[CgmesProfileType.TP_BD, CgmesProfileType.DL, CgmesProfileType.SSH, CgmesProfileType.EQ,
                      CgmesProfileType.DY, CgmesProfileType.TP, CgmesProfileType.EQ_BD, CgmesProfileType.GL,
                      CgmesProfileType.SV]),
        CgmesProperty(property_name='DependentOn', class_type=str, description="DependentOn.", profiles=[CgmesProfileType.TP_BD, CgmesProfileType.DL, CgmesProfileType.SSH, CgmesProfileType.EQ,
                      CgmesProfileType.DY, CgmesProfileType.TP, CgmesProfileType.EQ_BD, CgmesProfileType.GL,
                      CgmesProfileType.SV]),
        CgmesProperty(property_name='longDependentOnPF', class_type=str, description="longDependentOnPF.", profiles=[CgmesProfileType.TP_BD, CgmesProfileType.DL, CgmesProfileType.SSH, CgmesProfileType.EQ,
                      CgmesProfileType.DY, CgmesProfileType.TP, CgmesProfileType.EQ_BD, CgmesProfileType.GL,
                      CgmesProfileType.SV]),
        CgmesProperty(property_name='Supersedes', class_type=str, description="Supersedes.", profiles=[CgmesProfileType.TP_BD, CgmesProfileType.DL, CgmesProfileType.SSH, CgmesProfileType.EQ,
                      CgmesProfileType.DY, CgmesProfileType.TP, CgmesProfileType.EQ_BD, CgmesProfileType.GL,
                      CgmesProfileType.SV]),
    )

    def __init__(self, rdfid, tpe):
        IdentifiedObject.__init__(self, rdfid, tpe)

        self.scenarioTime: str | None = None
        self.created: str | None = None
        self.version: str | None = None
        self.profile: str | List[str] | None = None  # TODO: Crazy polymorphism
        self.modelingAuthoritySet: str | List[str] | None = None  # TODO: Crazy polymorphism
        self.DependentOn: str | list | None = None  # TODO: Crazy polymorphism
        self.longDependentOnPF: str | None = None
        self.Supersedes: str | None = None
