# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType, GCProp


class RmsEventsGroup(EditableDevice):
    """
    RMS events group.
    """
    __slots__ = (
        "_active",
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='active',
            units='',
            tpe=bool,
            definition='True if this RMS events group must be simulated.',
        ),
    )

    def __init__(self,
                 idtag: Union[str, None] = None,
                 active: bool = True,
                 name: str = "RmsEventsGroup",
                 comment: str = "") -> None:
        """
        Build an RMS events group.

        :param idtag: Unique identifier.
        :param active: True if this RMS events group must be simulated.
        :param name: Group name.
        :param comment: User comment.
        :return: None.
        """
        # Initialize the common editable-device state first so the inherited
        # schema and metadata are ready before assigning local properties.
        EditableDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code='',
                                device_type=DeviceType.RmsEventsGroupDevice,
                                comment=comment)

        # Store the activation flag on the instance so serializers and the GUI
        # can read the registered property value from the object state.
        self.active = active

    @property
    def active(self) -> bool:
        """
        Get whether this events group is active.

        :return: True when the group must be simulated.
        """
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        """
        Set whether this events group is active.

        :param value: Activation state to store.
        :return: None.
        """
        # Coerce the stored state to the declared schema type so the model,
        # persistence layer and editors all observe a stable boolean value.
        self._active = bool(value)
