# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Retain reviewed DYR schemas and leave release-uncertain layouts unsupported."""
from VeraGridEngine.IO.raw.psse_auxiliary import PsseVersion
from VeraGridEngine.IO.raw.versioned.base.dyr import DynamicModelSchema, UserDynamicModelSchema
from VeraGridEngine.IO.raw.versioned.v35.dyr import RawDyrV35


class RawDyrV36(RawDyrV35):
    """PSS/E 36 DYR data; inherit only unchanged grammar."""

    __slots__ = ()

    def __init__(self, source: str = '<dyr>') -> None:
        """Select the documented PSS/E 36 grammar.

        :param source: Diagnostic source label.
        """
        super().__init__(source)
        self.version = PsseVersion.V36

    def get_model_schema(self, model: str) -> DynamicModelSchema | None:
        """Leave unverified ST6B, WESGOV, ST9C and UEL2C 36 layouts unavailable.

        :param model: Source model identifier, case insensitive.
        :return: Inherited schema except records lacking a release-specific sheet.
        """
        if model.upper() in (
                'AC3C', 'AC11C', 'BBGOV1', 'BEPSST', 'CGEN1', 'MAXEX1', 'MAXEX2', 'PSS4B',
                'ST6B', 'WESGOV', 'WESGOVD', 'ST9C', 'UEL2C', 'REECC1', 'DERA1', 'GAST2A',
                'OSTB2T', 'OSTB5T', 'HYGOVR1', 'TGOV4', 'TGOV5',
                'CIM5AL','CIM5AR','CIM5BL','CIM5OW','CIM5ZN',
                'CIM6AL','CIM6AR','CIM6BL','CIM6OW','CIM6ZN',
                'CIMWAL','CIMWAR','CIMWBL','CIMWOW','CIMWZN',
                'CMLDBLU2','CMLDOWU2','CMLDZNU2','CMLDARU2','CMLDALU2'):
            return None
        else:
            return super().get_model_schema(model)

    def get_auxiliary_signal_schema(self, model: str) -> DynamicModelSchema | None:
        """Keep the inherited CPAAUT layout gated without a 36.1 source sheet.

        :param model: Source model identifier, case-insensitive.
        :return: None for unreviewed CPAAUT, otherwise an inherited layout.
        """
        if model.upper() == 'CPAAUT':
            return None
        else:
            return super().get_auxiliary_signal_schema(model)

    def get_user_model_schema(self, name: str) -> UserDynamicModelSchema | None:
        """Keep PSS7C and AC8BBU2 gated without 36.1 source contracts.

        :param name: Exact user-subroutine identifier.
        :return: No PSS7C schema for 36; otherwise an inherited reviewed layout.
        """
        if name.upper() in (
                'PSS7C','AC8BBU2',
                'ACMTBLU1','ACMTOWU1','ACMTZNU1','ACMTARU1','ACMTALU1',
                'CMLDBLU2','CMLDOWU2','CMLDZNU2','CMLDARU2','CMLDALU2'):
            return None
        else:
            return super().get_user_model_schema(name)
