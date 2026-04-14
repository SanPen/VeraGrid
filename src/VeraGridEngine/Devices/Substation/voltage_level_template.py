# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.enumerations import DeviceType, VoltageLevelTypes


class VoltageLevelTemplate(EditableDevice):

    def __init__(self, name='', code='', idtag: str | None = None,
                 device_type=DeviceType.GenericArea, voltage: float = 10):
        """

        :param name:
        :param code:
        :param idtag:
        :param device_type:
        :param voltage:
        """
        EditableDevice.__init__(self,
                                name=name,
                                code=code,
                                idtag=idtag,
                                device_type=device_type)

        self.vl_type: VoltageLevelTypes = VoltageLevelTypes.SingleBar
        self.voltage: float = voltage
        self.n_bays: int = 1
        self.add_disconnectors: bool = False

        self.register(key='vl_type', units='', tpe=VoltageLevelTypes, definition='Voltage level type', editable=True)

        self.register(key='voltage', units='kV', tpe=float, definition='Voltage.', editable=True)

        self.register(key='n_bays', units='', tpe=int,
                      definition='Number of bays or modules to add.', editable=True)

        self.register(key='add_disconnectors', units='', tpe=bool,
                      definition='Add disconnectors additionally to the circuit breakers', editable=True)
