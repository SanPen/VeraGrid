# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Union
from VeraGridEngine.enumerations import BuildStatus, DeviceType
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice


class ControlPc(DynamicDevice):
    """
    This class serves as a place where to put global controls
    """

    __slots__ = ()

    def __init__(self,
                 name: str = "Control PC",
                 idtag: Union[str, None] = None,
                 code: str = "",
                 build_status: BuildStatus = BuildStatus.Commissioned):
        """

        :param name: name of the branch
        :param idtag: UUID code
        :param code: secondary id
        :param build_status: Branch build status.
        """

        DynamicDevice.__init__(self,
                               name=name,
                               idtag=idtag,
                               code=code,
                               device_type=DeviceType.ControlPc,
                               build_status=build_status)
