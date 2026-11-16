# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna MarketBidTimeSeriesCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import SiennaCostCurve
    from VeraGridEngine.IO.sienna.devices.core.common.curve_multi_step import SiennaCurveMultiStep
    from VeraGridEngine.IO.sienna.devices.core.common.curve_styles import SiennaCurveStyles
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_input_output_curve import SiennaTimeSeriesInputOutputCurve

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaMarketBidTimeSeriesCost(SiennaSchemaModel):
    """Expose every declared MarketBidTimeSeriesCost property through fixed slots."""

    __slots__ = ('cost_type', 'minimum_energy_offer', 'start_up_association_id', 'shut_down', 'incremental_offer_curves', 'decremental_offer_curves', 'ancillary_service_offers', 'incremental_slope', 'decremental_slope', 'curve_style', 'curve_multistep',)

    def __init__(self, cost_type: str, minimum_energy_offer: SiennaTimeSeriesInputOutputCurve, start_up_association_id: int, shut_down: SiennaTimeSeriesInputOutputCurve, incremental_offer_curves: SiennaCostCurve, decremental_offer_curves: SiennaCostCurve, ancillary_service_offers: list[int], incremental_slope: bool, decremental_slope: bool, curve_style: SiennaCurveStyles, curve_multistep: SiennaCurveMultiStep) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.cost_type: str = cost_type
        self.minimum_energy_offer: SiennaTimeSeriesInputOutputCurve = minimum_energy_offer
        self.start_up_association_id: int = start_up_association_id
        self.shut_down: SiennaTimeSeriesInputOutputCurve = shut_down
        self.incremental_offer_curves: SiennaCostCurve = incremental_offer_curves
        self.decremental_offer_curves: SiennaCostCurve = decremental_offer_curves
        self.ancillary_service_offers: list[int] = ancillary_service_offers
        self.incremental_slope: bool = incremental_slope
        self.decremental_slope: bool = decremental_slope
        self.curve_style: SiennaCurveStyles = curve_style
        self.curve_multistep: SiennaCurveMultiStep = curve_multistep


def parse_sienna_market_bid_time_series_cost(data: dict[str, Any]) -> SiennaMarketBidTimeSeriesCost:
    """Parse declared MarketBidTimeSeriesCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed MarketBidTimeSeriesCost object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import parse_sienna_cost_curve
    from VeraGridEngine.IO.sienna.devices.core.common.curve_multi_step import parse_sienna_curve_multi_step
    from VeraGridEngine.IO.sienna.devices.core.common.curve_styles import parse_sienna_curve_styles
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_input_output_curve import parse_sienna_time_series_input_output_curve
    return SiennaMarketBidTimeSeriesCost(cost_type=get_required_value(data, 'cost_type', 'MarketBidTimeSeriesCost'), minimum_energy_offer=parse_sienna_time_series_input_output_curve(get_required_value(data, 'minimum_energy_offer', 'MarketBidTimeSeriesCost')), start_up_association_id=get_required_value(data, 'start_up_association_id', 'MarketBidTimeSeriesCost'), shut_down=parse_sienna_time_series_input_output_curve(get_required_value(data, 'shut_down', 'MarketBidTimeSeriesCost')), incremental_offer_curves=parse_sienna_cost_curve(get_required_value(data, 'incremental_offer_curves', 'MarketBidTimeSeriesCost')), decremental_offer_curves=parse_sienna_cost_curve(get_required_value(data, 'decremental_offer_curves', 'MarketBidTimeSeriesCost')), ancillary_service_offers=get_required_value(data, 'ancillary_service_offers', 'MarketBidTimeSeriesCost'), incremental_slope=data.get('incremental_slope', None), decremental_slope=data.get('decremental_slope', None), curve_style=None if data.get('curve_style', None) is None else parse_sienna_curve_styles(data.get('curve_style', None)), curve_multistep=None if data.get('curve_multistep', None) is None else parse_sienna_curve_multi_step(data.get('curve_multistep', None)))

def sienna_market_bid_time_series_cost_to_json(value: SiennaMarketBidTimeSeriesCost) -> dict[str, Any]:
    """Write every MarketBidTimeSeriesCost slot to explicit schema property names.

    :param value: Typed MarketBidTimeSeriesCost object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import sienna_cost_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.curve_multi_step import sienna_curve_multi_step_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.curve_styles import sienna_curve_styles_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.time_series_input_output_curve import sienna_time_series_input_output_curve_to_json
    return {'cost_type': value.cost_type, 'minimum_energy_offer': sienna_time_series_input_output_curve_to_json(value.minimum_energy_offer), 'start_up_association_id': value.start_up_association_id, 'shut_down': sienna_time_series_input_output_curve_to_json(value.shut_down), 'incremental_offer_curves': sienna_cost_curve_to_json(value.incremental_offer_curves), 'decremental_offer_curves': sienna_cost_curve_to_json(value.decremental_offer_curves), 'ancillary_service_offers': value.ancillary_service_offers, 'incremental_slope': value.incremental_slope, 'decremental_slope': value.decremental_slope, 'curve_style': None if value.curve_style is None else sienna_curve_styles_to_json(value.curve_style), 'curve_multistep': None if value.curve_multistep is None else sienna_curve_multi_step_to_json(value.curve_multistep)}
