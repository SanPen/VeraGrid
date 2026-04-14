# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.iidm.devices.iidm_object import IidmObject


class IidmBusbarSection(IidmObject):
    def __init__(self, _id: str):
        super().__init__("BusbarSection")
        self.id = _id

        self.register_property("id", str, description="Busbar section ID")
