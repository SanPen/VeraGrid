# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna DataSource schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import Any

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaDataSource(SiennaSchemaModel):
    """Expose every declared DataSource property through fixed slots."""

    __slots__ = ('id', 'organization', 'retrieved_at', 'dataset', 'url', 'version', 'license', 'published_at', 'confidence', 'recorded_by', 'fields', 'extra',)

    def __init__(self, id: int, organization: str, retrieved_at: str, dataset: str, url: str, version: str, license: str, published_at: str | None, confidence: str, recorded_by: str | None, fields: list[str], extra: dict[str, object]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.organization: str = organization
        self.retrieved_at: str = retrieved_at
        self.dataset: str = dataset
        self.url: str = url
        self.version: str = version
        self.license: str = license
        self.published_at: str | None = published_at
        self.confidence: str = confidence
        self.recorded_by: str | None = recorded_by
        self.fields: list[str] = fields
        self.extra: dict[str, object] = extra


def parse_sienna_data_source(data: dict[str, Any]) -> SiennaDataSource:
    """Parse declared DataSource properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed DataSource object.
    """
    return SiennaDataSource(id=get_required_value(data, 'id', 'DataSource'), organization=data.get('organization', None), retrieved_at=get_required_value(data, 'retrieved_at', 'DataSource'), dataset=data.get('dataset', None), url=data.get('url', None), version=data.get('version', None), license=data.get('license', None), published_at=data.get('published_at', None), confidence=data.get('confidence', None), recorded_by=data.get('recorded_by', None), fields=get_required_value(data, 'fields', 'DataSource'), extra=data.get('extra', None))


def sienna_data_source_to_json(value: SiennaDataSource) -> dict[str, Any]:
    """Write every DataSource slot to explicit schema property names.

    :param value: Typed DataSource object.
    :return: JSON object with declared schema properties.
    """
    return {'id': value.id, 'organization': value.organization, 'retrieved_at': value.retrieved_at, 'dataset': value.dataset, 'url': value.url, 'version': value.version, 'license': value.license, 'published_at': value.published_at, 'confidence': value.confidence, 'recorded_by': value.recorded_by, 'fields': value.fields, 'extra': value.extra}
