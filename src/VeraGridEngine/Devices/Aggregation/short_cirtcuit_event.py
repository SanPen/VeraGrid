# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union

from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.enumerations import DeviceType, FaultType, MethodShortCircuit, PhasesShortCircuit


class ShortCircuitEvent(PointerDeviceParent):
    """
    Investment
    """
    __slots__ = (
        '_fault_type',
        '_method',
        '_phases',
        'active',
    )

    def __init__(self,
                 device: EditableDevice | None = None,
                 idtag: Union[str, None] = None,
                 name="Fault",
                 code='',
                 active: bool = True,
                 fault_type: FaultType = FaultType.LLLG,
                 method: MethodShortCircuit = MethodShortCircuit.sequences,
                 phases: PhasesShortCircuit = PhasesShortCircuit.abc,
                 comment: str = ""):
        """
        Investment
        :param device: Some device to point at
        :param idtag: String. Element unique identifier
        :param name: String. Contingency name
        :param code: String. Contingency code name
        :param active: If true the investment activates when applied, otherwise is deactivated
        :param comment: Comment
        """

        PointerDeviceParent.__init__(self,
                                     idtag=idtag,
                                     device=device,
                                     code=code,
                                     name=name,
                                     device_type=DeviceType.ShortCircuitEvent,
                                     comment=comment)

        self._fault_type: FaultType = fault_type
        self._method: MethodShortCircuit = method
        self._phases: PhasesShortCircuit = phases
        self.active: bool = active

        self.register(key='fault_type', units='', tpe=FaultType, definition='Type of short circuit')
        self.register(key='method', units='', tpe=MethodShortCircuit, definition='Method of short circuit')
        self.register(key='phases', units='', tpe=PhasesShortCircuit, definition='Phases involved')
        self.register(key='active', units='', tpe=bool,
                      definition='If true the short-circuit activates when calculated, otherwise is deactivated.')

    def _check(self):

        if self._fault_type == FaultType.LLLG:
            if self._phases != PhasesShortCircuit.abc:
                self._phases = PhasesShortCircuit.abc

    @property
    def fault_type(self) -> FaultType:
        """

        :return:
        """
        return self._fault_type

    @fault_type.setter
    def fault_type(self, val: FaultType):

        if self.auto_update_enabled:
            self._check()
        else:
            self._fault_type = val

    @property
    def phases(self) -> PhasesShortCircuit:
        """

        :return:
        """
        return self._phases

    @phases.setter
    def phases(self, val: PhasesShortCircuit):

        if self.auto_update_enabled:
            self._check()
        else:
            self._phases = val

    @property
    def method(self) -> MethodShortCircuit:
        """

        :return:
        """
        return self._method

    @method.setter
    def method(self, val: MethodShortCircuit):

        if self.auto_update_enabled:
            self._check()
        else:
            self._method = val
