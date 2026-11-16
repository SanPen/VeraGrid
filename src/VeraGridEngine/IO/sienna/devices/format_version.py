# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Pinned Sienna format revisions and their compatibility boundary."""

from enum import Enum


class SiennaFormatVersion(Enum):
    """Sienna SystemDocument formats explicitly implemented by this adapter."""

    V0_4_0 = "0.4.0"


class SiennaFormatProfile:
    """Describe one independently versioned Sienna interchange contract."""

    __slots__ = ("version", "schema_checkout_tag")

    def __init__(self, version: SiennaFormatVersion, schema_checkout_tag: str) -> None:
        """Store the exact external schema revision used to build an adapter.

        :param version: SystemDocument format version.
        :param schema_checkout_tag: Pinned SiennaSchemas checkout tag.
        :return: None.
        """
        self.version: SiennaFormatVersion = version
        self.schema_checkout_tag: str = schema_checkout_tag


def resolve_sienna_format_version(value: str) -> SiennaFormatProfile:
    """Resolve a wire-format version without silently applying another revision.

    :param value: Declared SystemDocument schema version.
    :return: Matching pinned format profile.
    :raises ValueError: When the format revision is not implemented.
    """
    try:
        version: SiennaFormatVersion = SiennaFormatVersion(value)
    except ValueError as error:
        raise ValueError(f"Unsupported Sienna schema_version '{value}'") from error
    if version is SiennaFormatVersion.V0_4_0:
        return SiennaFormatProfile(version=version, schema_checkout_tag="v0.4.0")
    else:
        raise ValueError(f"Sienna schema_version '{value}' has no adapter profile")
