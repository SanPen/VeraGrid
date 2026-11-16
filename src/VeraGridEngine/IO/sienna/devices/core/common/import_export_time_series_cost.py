# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna ImportExportTimeSeriesCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import SiennaCostCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaImportExportTimeSeriesCost(SiennaSchemaModel):
    """Expose every declared ImportExportTimeSeriesCost property through fixed slots."""

    __slots__ = ('cost_type', 'import_offer_curves', 'export_offer_curves', 'energy_import_weekly_limit', 'energy_export_weekly_limit', 'ancillary_service_offers',)

    def __init__(self, cost_type: str, import_offer_curves: SiennaCostCurve, export_offer_curves: SiennaCostCurve, energy_import_weekly_limit: float, energy_export_weekly_limit: float, ancillary_service_offers: list[int]) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.cost_type: str = cost_type
        self.import_offer_curves: SiennaCostCurve = import_offer_curves
        self.export_offer_curves: SiennaCostCurve = export_offer_curves
        self.energy_import_weekly_limit: float = energy_import_weekly_limit
        self.energy_export_weekly_limit: float = energy_export_weekly_limit
        self.ancillary_service_offers: list[int] = ancillary_service_offers


def parse_sienna_import_export_time_series_cost(data: dict[str, Any]) -> SiennaImportExportTimeSeriesCost:
    """Parse declared ImportExportTimeSeriesCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed ImportExportTimeSeriesCost object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import parse_sienna_cost_curve
    return SiennaImportExportTimeSeriesCost(cost_type=get_required_value(data, 'cost_type', 'ImportExportTimeSeriesCost'), import_offer_curves=parse_sienna_cost_curve(get_required_value(data, 'import_offer_curves', 'ImportExportTimeSeriesCost')), export_offer_curves=parse_sienna_cost_curve(get_required_value(data, 'export_offer_curves', 'ImportExportTimeSeriesCost')), energy_import_weekly_limit=get_required_value(data, 'energy_import_weekly_limit', 'ImportExportTimeSeriesCost'), energy_export_weekly_limit=get_required_value(data, 'energy_export_weekly_limit', 'ImportExportTimeSeriesCost'), ancillary_service_offers=get_required_value(data, 'ancillary_service_offers', 'ImportExportTimeSeriesCost'))

def sienna_import_export_time_series_cost_to_json(value: SiennaImportExportTimeSeriesCost) -> dict[str, Any]:
    """Write every ImportExportTimeSeriesCost slot to explicit schema property names.

    :param value: Typed ImportExportTimeSeriesCost object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import sienna_cost_curve_to_json
    return {'cost_type': value.cost_type, 'import_offer_curves': sienna_cost_curve_to_json(value.import_offer_curves), 'export_offer_curves': sienna_cost_curve_to_json(value.export_offer_curves), 'energy_import_weekly_limit': value.energy_import_weekly_limit, 'energy_export_weekly_limit': value.energy_export_weekly_limit, 'ancillary_service_offers': value.ancillary_service_offers}
