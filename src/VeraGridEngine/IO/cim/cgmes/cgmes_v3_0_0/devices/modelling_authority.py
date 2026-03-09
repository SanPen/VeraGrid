# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.identified_object import IdentifiedObject


class ModellingAuthority(IdentifiedObject):
    def __init__(self, rdfid: str = '', tpe: str = 'ModellingAuthority'):
        IdentifiedObject.__init__(self, rdfid=rdfid, tpe=tpe)
