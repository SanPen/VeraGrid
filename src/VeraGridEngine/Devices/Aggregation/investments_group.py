# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType, GCProp
from VeraGridEngine.enumerations import PrpCat


class InvestmentsGroup(EditableDevice):
    """
    Investments group
    """
    __slots__ = (
        'category',
        '_discount_rate',
        '_CAPEX',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='category',
            units='',
            tpe=str,
            definition='Some tag to category the investment group',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='discount_rate',
            units='%',
            tpe=float,
            definition='Investment group discount rate',
            cat=[PrpCat.INV],
        ),
        GCProp(
            prop_name='CAPEX',
            units='€',
            tpe=float,
            definition="Capital Expenditure of the group (added to the individual investments' capex)",
        ),
    )

    def __init__(self,
                 idtag: Union[str, None] = None,
                 name: str = "InvestmentGroup",
                 category: str = '',
                 comment: str = "",
                 discount_rate: float = 5.0,
                 CAPEX: float =0):
        """
        Contingency group
        :param idtag: Unique identifier
        :param name: contingency group name
        :param category: tag to category the group
        :param comment: comment
        :param discount_rate: discount rate (%)
        :param CAPEX: Capital Expenditure of the group (added to the individual investments' capex)
        """

        EditableDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code='',
                                device_type=DeviceType.InvestmentsGroupDevice,
                                comment=comment)

        # Contingency type
        self.category = category

        self.discount_rate = discount_rate

        self.CAPEX = CAPEX

    # Scalar property accessors coerce assignments to the declared schema types.

    @property
    def discount_rate(self) -> float:
        """
        Get ``discount_rate``.

        :return: float
        """
        return self._discount_rate

    @discount_rate.setter
    def discount_rate(self, val: float) -> None:
        """
        Set ``discount_rate``.

        :param val: Value to assign.
        :return: None
        """
        self._discount_rate = float(val)

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

