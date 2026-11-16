# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Retain legacy DYR framing and USRSWS. ReleaseNotes 35.0 section 7.4 establishes that USRSWS2 is a version-35 addition."""
from VeraGridEngine.IO.raw.psse_auxiliary import PsseVersion
from VeraGridEngine.IO.raw.versioned.base.auxiliary import FeatureSupport
from VeraGridEngine.IO.raw.versioned.v33.dyr import RawDyrV33
from VeraGridEngine.IO.raw.versioned.base.dyr import DynamicModelSchema, UserDynamicModelSchema


class RawDyrV34(RawDyrV33):
    """PSS/E 34 DYR data; inherit only unchanged grammar."""

    __slots__ = ()

    def __init__(self, source: str = '<dyr>') -> None:
        """Select the documented PSS/E 34 grammar.

        :param source: Diagnostic source label.
        """
        super().__init__(source)
        self.version = PsseVersion.V34
        # The available 34.1 manual does not specify DYR IC=108.
        self.torque_model_support = FeatureSupport.UNVERIFIED

    def get_model_schema(self, model: str) -> DynamicModelSchema | None:
        """Decline a changed constant order without a release-specific source sheet.

        :param model: Source model identifier, case insensitive.
        :return: Reviewed inherited layout, or None for ambiguous ordering.
        """
        if model.upper() in ('BBGOV1', 'BEPSST', 'BUDCZT', 'CGEN1', 'COMPCC', 'FRQTPAT', 'GAST2A', 'MAXEX1', 'MAXEX2', 'OSTB2T', 'OSTB5T', 'PSS4B', 'ST6B', 'TGOV2', 'TGOV3', 'TGOV4', 'TGOV5', 'VTGTPAT', 'WESGOV'):
            # These source sheets do not establish the exact PSS/E 34 layouts.
            return None
        else:
            return super().get_model_schema(model)

    def get_auxiliary_signal_schema(self, model: str) -> DynamicModelSchema | None:
        """Decline CPAAUT until a PSS/E 34 source sheet is reviewed.

        :param model: Source model identifier, case-insensitive.
        :return: None for unreviewed CPAAUT, otherwise the unchanged inherited layout.
        """
        if model.upper() == 'CPAAUT':
            return None
        else:
            return super().get_auxiliary_signal_schema(model)

    def get_user_model_schema(self, name: str) -> UserDynamicModelSchema | None:
        """Keep legacy wrapper contracts unreviewed without a release-specific sheet.

        Profiles 35/36 inherit this restriction and review direct built-ins
        separately. Header grammar compatibility does not establish that a user
        subroutine is supplied with the same allocations in another release.

        :param name: Source subroutine identifier.
        :return: None; retain generic user payload without an activated schema.
        """
        return None
