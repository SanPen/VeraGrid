# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.enumerations import DeviceType


class PointerDeviceParent(EditableDevice):
    """
    Investment
    """

    __slots__ = (
        '_device_idtag',
        '_device_name',
        '_tpe',
        '_device'
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key='device_idtag', units='', tpe=str, definition='Unique ID', editable=False),
        GCProp(key='tpe', units='', tpe=DeviceType, definition='Device type', editable=False),
        GCProp(key='device_name', units='', tpe=str, definition='Device name', editable=False),
    )

    def __init__(self,
                 idtag: Union[str, None],
                 device: EditableDevice | None,
                 name: str,
                 code: str,
                 comment: str,
                 device_type: DeviceType):
        """
        Investment
        :param idtag: String. Element unique identifier
        :param device: Device to point at
        :param name: String. Contingency name
        :param code: String. Contingency code name
        :param comment: Comment
        """

        EditableDevice.__init__(self,
                                idtag=idtag,
                                code=code,
                                name=name,
                                device_type=device_type,
                                comment=comment)

        self._device_idtag: str = device.idtag if device is not None else ""
        self._tpe: DeviceType = device.device_type if device is not None else DeviceType.NoDevice
        self._device_name: str = device.name if device is not None else "No device"
        self._device = device

    @property
    def device_idtag(self) -> str:
        """
        Group of investments
        :return:
        """
        return self._device_idtag

    @device_idtag.setter
    def device_idtag(self, val: str):
        if isinstance(val, str):
            self._device_idtag = val
        else:
            raise ValueError(f"device_idtag must be a string not {val}")

    @property
    def device_name(self) -> str:
        """

        :return:
        """
        return self._device.name if self._device is not None else "No device"

    @device_name.setter
    def device_name(self, val: str):
        if isinstance(val, str):
            self._device_name = val
        else:
            raise ValueError(f"tpe must be a string not {val}")

    @property
    def tpe(self) -> DeviceType:
        """
        Display the group category
        :return:
        """
        return self._tpe

    @tpe.setter
    def tpe(self, val: DeviceType):
        if isinstance(val, DeviceType):
            self._tpe = val
        else:
            raise ValueError(f"tpe must be a string not {val}")

    @property
    def device(self) -> EditableDevice:
        """
        device getter
        :return:
        """
        return self._device

    @device.setter
    def device(self, val: EditableDevice):
        if isinstance(val, EditableDevice):
            if val is not None:
                self._tpe = val.device_type
                self._device_idtag = val.idtag
                self.device_name = val.name
                self._device = val
            else:
                raise ValueError(f"device cannot be None")
        else:
            raise ValueError(f"tpe must be a EditableDevice not {val}")

    def set_device(self, elm: EditableDevice):
        """
        Set the device
        :param elm: Device to be pointed
        """
        self.device = elm

    def rebind_device_references(self, objects_by_idtag, props=None) -> None:
        """
        Rebind the pointed device to an equivalent object from a target lookup.

        :param objects_by_idtag: idtag -> target object lookup.
        :param props: Optional subset of registered properties to process.
        """
        super().rebind_device_references(objects_by_idtag=objects_by_idtag, props=props)

        pointed = None
        if self._device is not None and hasattr(self._device, "idtag"):
            pointed = objects_by_idtag.get(self._device.idtag, None)

        if pointed is None and self._device_idtag:
            pointed = objects_by_idtag.get(self._device_idtag, None)

        if pointed is not None:
            self._device = pointed
            self._device_idtag = pointed.idtag
            self._device_name = pointed.name
            self._tpe = pointed.device_type
