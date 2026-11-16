# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna RenewableEnergyConverterTypeA schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaRenewableEnergyConverterTypeA(SiennaSchemaModel):
    """Expose every declared RenewableEnergyConverterTypeA property through fixed slots."""

    __slots__ = ('T_g', 'Rrpwr', 'Brkpt', 'Zerox', 'Lvpl1', 'Vo_lim', 'Lv_pnts', 'Io_lim', 'T_fltr', 'K_hv', 'Iqr_lims', 'Accel', 'Lvpl_sw', 'Q_ref', 'R_source', 'X_source',)

    def __init__(self, T_g: float, Rrpwr: float, Brkpt: float, Zerox: float, Lvpl1: float, Vo_lim: float, Lv_pnts: SiennaMinMax, Io_lim: float, T_fltr: float, K_hv: float, Iqr_lims: SiennaMinMax, Accel: float, Lvpl_sw: int, Q_ref: float, R_source: float, X_source: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.T_g: float = T_g
        self.Rrpwr: float = Rrpwr
        self.Brkpt: float = Brkpt
        self.Zerox: float = Zerox
        self.Lvpl1: float = Lvpl1
        self.Vo_lim: float = Vo_lim
        self.Lv_pnts: SiennaMinMax = Lv_pnts
        self.Io_lim: float = Io_lim
        self.T_fltr: float = T_fltr
        self.K_hv: float = K_hv
        self.Iqr_lims: SiennaMinMax = Iqr_lims
        self.Accel: float = Accel
        self.Lvpl_sw: int = Lvpl_sw
        self.Q_ref: float = Q_ref
        self.R_source: float = R_source
        self.X_source: float = X_source


def parse_sienna_renewable_energy_converter_type_a(data: dict[str, Any]) -> SiennaRenewableEnergyConverterTypeA:
    """Parse declared RenewableEnergyConverterTypeA properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed RenewableEnergyConverterTypeA object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    return SiennaRenewableEnergyConverterTypeA(T_g=get_required_value(data, 'T_g', 'RenewableEnergyConverterTypeA'), Rrpwr=get_required_value(data, 'Rrpwr', 'RenewableEnergyConverterTypeA'), Brkpt=get_required_value(data, 'Brkpt', 'RenewableEnergyConverterTypeA'), Zerox=get_required_value(data, 'Zerox', 'RenewableEnergyConverterTypeA'), Lvpl1=get_required_value(data, 'Lvpl1', 'RenewableEnergyConverterTypeA'), Vo_lim=get_required_value(data, 'Vo_lim', 'RenewableEnergyConverterTypeA'), Lv_pnts=parse_sienna_min_max(get_required_value(data, 'Lv_pnts', 'RenewableEnergyConverterTypeA')), Io_lim=get_required_value(data, 'Io_lim', 'RenewableEnergyConverterTypeA'), T_fltr=get_required_value(data, 'T_fltr', 'RenewableEnergyConverterTypeA'), K_hv=get_required_value(data, 'K_hv', 'RenewableEnergyConverterTypeA'), Iqr_lims=parse_sienna_min_max(get_required_value(data, 'Iqr_lims', 'RenewableEnergyConverterTypeA')), Accel=get_required_value(data, 'Accel', 'RenewableEnergyConverterTypeA'), Lvpl_sw=get_required_value(data, 'Lvpl_sw', 'RenewableEnergyConverterTypeA'), Q_ref=data.get('Q_ref', None), R_source=data.get('R_source', None), X_source=data.get('X_source', None))

def sienna_renewable_energy_converter_type_a_to_json(value: SiennaRenewableEnergyConverterTypeA) -> dict[str, Any]:
    """Write every RenewableEnergyConverterTypeA slot to explicit schema property names.

    :param value: Typed RenewableEnergyConverterTypeA object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    return {'T_g': value.T_g, 'Rrpwr': value.Rrpwr, 'Brkpt': value.Brkpt, 'Zerox': value.Zerox, 'Lvpl1': value.Lvpl1, 'Vo_lim': value.Vo_lim, 'Lv_pnts': sienna_min_max_to_json(value.Lv_pnts), 'Io_lim': value.Io_lim, 'T_fltr': value.T_fltr, 'K_hv': value.K_hv, 'Iqr_lims': sienna_min_max_to_json(value.Iqr_lims), 'Accel': value.Accel, 'Lvpl_sw': value.Lvpl_sw, 'Q_ref': value.Q_ref, 'R_source': value.R_source, 'X_source': value.X_source}
