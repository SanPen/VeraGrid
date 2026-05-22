# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, GCProp
from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Devices.Aggregation.investments_group import InvestmentsGroup
from VeraGridEngine.enumerations import DeviceType, PrpCat
from VeraGridEngine.basic_structures import Logger


class Investment(PointerDeviceParent):
    """
    Investment
    """
    __slots__ = (
        '_CAPEX',
        '_group',
        '_status',
        '_commissioning_date',
        '_decommissioning_date',
        '_prop',
        '_value'
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='CAPEX',
            units='M€',
            tpe=float,
            definition='Capital expenditures. This is the investment value, '
                       'it overrides the CAPEX value of the device if it exits.',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='status',
            units='',
            tpe=bool,
            definition='If true the investment activates when applied, otherwise is deactivated.',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='group',
            units='',
            tpe=DeviceType.InvestmentsGroupDevice,
            definition='Investment group',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='commissioning_date',
            units='',
            tpe=float,
            definition='Date when the investment is commissioned',
            cat=[PrpCat.INV],
            is_date=True
        ),
        GCProp(
            prop_name='decommissioning_date',
            units='',
            tpe=float,
            definition='Date when the investment is decommissioned',
            cat=[PrpCat.INV],
            is_date=True
        ),
        GCProp(
            prop_name='prop',
            units='',
            tpe=str,
            definition='device property',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='value',
            units='',
            tpe=float,
            definition='value status',
            cat=[PrpCat.INV],
        ),
    )

    def __init__(self,
                 device: EditableDevice | None = None,
                 idtag: Union[str, None] = None,
                 name="Investment",
                 code='',
                 CAPEX: float = 0.0,
                 status: bool = True,
                 commissioning_date: float = 0,
                 decommissioning_date: float = 0,
                 prop: str = "",
                 value: float = 0,
                 group: InvestmentsGroup = None,
                 comment: str = ""):
        """
        Investment
        :param device: Some device to point at
        :param idtag: String. Element unique identifier
        :param name: String. Contingency name
        :param code: String. Contingency code name
        :param CAPEX: Float. Capital expenditures
        :param status: If true the investment activates when applied, otherwise is deactivated
        :param group: InvestmentGroup. Investment group
        :param comment: Comment
        """

        PointerDeviceParent.__init__(self,
                                     idtag=idtag,
                                     device=device,
                                     code=code,
                                     name=name,
                                     device_type=DeviceType.InvestmentDevice,
                                     comment=comment)

        self.CAPEX: float = CAPEX
        self._group: InvestmentsGroup | None = group
        self.status: bool = status
        self._commissioning_date: float = commissioning_date
        self._decommissioning_date: float = decommissioning_date
        self._prop: str = prop
        self._value: float = value

    @property
    def group(self) -> InvestmentsGroup | None:
        """
        Group of investments
        :return:
        """
        return self._group

    @group.setter
    def group(self, val: InvestmentsGroup):
        self._group = val

    @property
    def category(self) -> str:
        """
        Display the group category
        :return:
        """
        if self.group is None:
            return ""
        else:
            return self.group.category

    @category.setter
    def category(self, val):
        # The category is set through the group, so no implementation here
        pass

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def CAPEX(self) -> float:
        """
        Get ``CAPEX``.

        :return: float
        """
        return self._CAPEX

    @CAPEX.setter
    def CAPEX(self, val: float) -> None:
        """
        Set ``CAPEX``.

        :param val: Value to assign.
        :return: None
        """
        self._CAPEX = float(val)

    @property
    def status(self) -> bool:
        """
        Get ``status``.

        :return: bool
        """
        return self._status

    @status.setter
    def status(self, val: bool) -> None:
        """
        Set ``status``.

        :param val: Value to assign.
        :return: None
        """
        self._status = bool(val)

    @property
    def commissioning_date(self) -> float:
        """
        Get ``status``.

        :return: bool
        """
        return self._commissioning_date

    @commissioning_date.setter
    def commissioning_date(self, val: float) -> None:
        """
        Set ``status``.

        :param val: Value to assign.
        :return: None
        """
        self._commissioning_date = val

    @property
    def decommissioning_date(self) -> float:
        """
        Get ``status``.

        :return: bool
        """
        return self._decommissioning_date

    @decommissioning_date.setter
    def decommissioning_date(self, val: float) -> None:
        """
        Set ``status``.

        :param val: Value to assign.
        :return: None
        """
        self._decommissioning_date = val

    @property
    def prop(self) -> str:
        """
        Get ``status``.

        :return: bool
        """
        return self._prop

    @prop.setter
    def prop(self, val: str) -> None:
        """
        Set ``status``.

        :param val: Value to assign.
        :return: None
        """
        if self.auto_update_enabled:
            if self.device is None:
                raise ValueError("device is None")
            else:
                if hasattr(self.device, val):
                    self._prop = val
                else:
                    raise ValueError(f"No {val} in {self.device}")
        else:
            # don't check
            self._prop = val

    @property
    def value(self) -> float:
        """
        Get ``status``.

        :return: bool
        """
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        """
        Set ``status``.

        :param val: Value to assign.
        :return: None
        """
        self._value = val
