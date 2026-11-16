# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna MarketBidCost schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import SiennaCostCurve
    from VeraGridEngine.IO.sienna.devices.core.common.curve_multi_step import SiennaCurveMultiStep
    from VeraGridEngine.IO.sienna.devices.core.common.curve_styles import SiennaCurveStyles
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import SiennaInputOutputCurve
    from VeraGridEngine.IO.sienna.devices.core.common.start_up_stages import SiennaStartUpStages

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaMarketBidCost(SiennaSchemaModel):
    """Expose every declared MarketBidCost property through fixed slots."""

    __slots__ = ('cost_type', 'minimum_energy_offer', 'start_up', 'shut_down', 'incremental_offer_curves', 'decremental_offer_curves', 'ancillary_service_offers', 'incremental_slope', 'decremental_slope', 'curve_style', 'curve_multistep',)

    def __init__(self, cost_type: str, minimum_energy_offer: SiennaInputOutputCurve, start_up: SiennaStartUpStages, shut_down: SiennaInputOutputCurve, incremental_offer_curves: SiennaCostCurve, decremental_offer_curves: SiennaCostCurve, ancillary_service_offers: list[int], incremental_slope: bool, decremental_slope: bool, curve_style: SiennaCurveStyles, curve_multistep: SiennaCurveMultiStep) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.cost_type: str = cost_type
        self.minimum_energy_offer: SiennaInputOutputCurve = minimum_energy_offer
        self.start_up: SiennaStartUpStages = start_up
        self.shut_down: SiennaInputOutputCurve = shut_down
        self.incremental_offer_curves: SiennaCostCurve = incremental_offer_curves
        self.decremental_offer_curves: SiennaCostCurve = decremental_offer_curves
        self.ancillary_service_offers: list[int] = ancillary_service_offers
        self.incremental_slope: bool = incremental_slope
        self.decremental_slope: bool = decremental_slope
        self.curve_style: SiennaCurveStyles = curve_style
        self.curve_multistep: SiennaCurveMultiStep = curve_multistep


def parse_sienna_market_bid_cost(data: dict[str, Any]) -> SiennaMarketBidCost:
    """Parse declared MarketBidCost properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed MarketBidCost object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import parse_sienna_cost_curve
    from VeraGridEngine.IO.sienna.devices.core.common.curve_multi_step import parse_sienna_curve_multi_step
    from VeraGridEngine.IO.sienna.devices.core.common.curve_styles import parse_sienna_curve_styles
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import parse_sienna_input_output_curve
    from VeraGridEngine.IO.sienna.devices.core.common.start_up_stages import parse_sienna_start_up_stages
    return SiennaMarketBidCost(cost_type=data.get('cost_type', None), minimum_energy_offer=parse_sienna_input_output_curve(get_required_value(data, 'minimum_energy_offer', 'MarketBidCost')), start_up=parse_sienna_start_up_stages(get_required_value(data, 'start_up', 'MarketBidCost')), shut_down=parse_sienna_input_output_curve(get_required_value(data, 'shut_down', 'MarketBidCost')), incremental_offer_curves=parse_sienna_cost_curve(get_required_value(data, 'incremental_offer_curves', 'MarketBidCost')), decremental_offer_curves=parse_sienna_cost_curve(get_required_value(data, 'decremental_offer_curves', 'MarketBidCost')), ancillary_service_offers=get_required_value(data, 'ancillary_service_offers', 'MarketBidCost'), incremental_slope=data.get('incremental_slope', None), decremental_slope=data.get('decremental_slope', None), curve_style=None if data.get('curve_style', None) is None else parse_sienna_curve_styles(data.get('curve_style', None)), curve_multistep=None if data.get('curve_multistep', None) is None else parse_sienna_curve_multi_step(data.get('curve_multistep', None)))

def sienna_market_bid_cost_to_json(value: SiennaMarketBidCost) -> dict[str, Any]:
    """Write every MarketBidCost slot to explicit schema property names.

    :param value: Typed MarketBidCost object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.cost_curve import sienna_cost_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.curve_multi_step import sienna_curve_multi_step_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.curve_styles import sienna_curve_styles_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.input_output_curve import sienna_input_output_curve_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.start_up_stages import sienna_start_up_stages_to_json
    return {'cost_type': value.cost_type, 'minimum_energy_offer': sienna_input_output_curve_to_json(value.minimum_energy_offer), 'start_up': sienna_start_up_stages_to_json(value.start_up), 'shut_down': sienna_input_output_curve_to_json(value.shut_down), 'incremental_offer_curves': sienna_cost_curve_to_json(value.incremental_offer_curves), 'decremental_offer_curves': sienna_cost_curve_to_json(value.decremental_offer_curves), 'ancillary_service_offers': value.ancillary_service_offers, 'incremental_slope': value.incremental_slope, 'decremental_slope': value.decremental_slope, 'curve_style': None if value.curve_style is None else sienna_curve_styles_to_json(value.curve_style), 'curve_multistep': None if value.curve_multistep is None else sienna_curve_multi_step_to_json(value.curve_multistep)}
