# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Statically typed Sienna GeneralGovModel schema object."""

from __future__ import annotations
from VeraGridEngine.IO.sienna.devices.schema_object import SiennaSchemaModel

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import SiennaMinMax
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import SiennaUpDown

from VeraGridEngine.IO.sienna.devices.common import get_required_value

class SiennaGeneralGovModel(SiennaSchemaModel):
    """Expose every declared GeneralGovModel property through fixed slots."""

    __slots__ = ('id', 'Rselect', 'fuel_flag', 'R', 'Tpelec', 'speed_error_signal', 'Kp_gov', 'Ki_gov', 'Kd_gov', 'Td_gov', 'valve_position_limits', 'T_act', 'K_turb', 'Wf_nl', 'Tb', 'Tc', 'T_eng', 'Tf_load', 'Kp_load', 'Ki_load', 'Ld_ref', 'Dm', 'R_open', 'R_close', 'Ki_mw', 'A_set', 'Ka', 'Ta', 'T_rate', 'db', 'Tsa', 'Tsb', 'R_lim', 'P_ref',)

    def __init__(self, id: int, Rselect: int, fuel_flag: int, R: float, Tpelec: float, speed_error_signal: SiennaMinMax, Kp_gov: float, Ki_gov: float, Kd_gov: float, Td_gov: float, valve_position_limits: SiennaMinMax, T_act: float, K_turb: float, Wf_nl: float, Tb: float, Tc: float, T_eng: float, Tf_load: float, Kp_load: float, Ki_load: float, Ld_ref: float, Dm: float, R_open: float, R_close: float, Ki_mw: float, A_set: float, Ka: float, Ta: float, T_rate: float, db: float, Tsa: float, Tsb: float, R_lim: SiennaUpDown, P_ref: float) -> None:
        """Store schema properties without a dynamic payload dictionary.

        :return: None.
        """
        self.id: int = id
        self.Rselect: int = Rselect
        self.fuel_flag: int = fuel_flag
        self.R: float = R
        self.Tpelec: float = Tpelec
        self.speed_error_signal: SiennaMinMax = speed_error_signal
        self.Kp_gov: float = Kp_gov
        self.Ki_gov: float = Ki_gov
        self.Kd_gov: float = Kd_gov
        self.Td_gov: float = Td_gov
        self.valve_position_limits: SiennaMinMax = valve_position_limits
        self.T_act: float = T_act
        self.K_turb: float = K_turb
        self.Wf_nl: float = Wf_nl
        self.Tb: float = Tb
        self.Tc: float = Tc
        self.T_eng: float = T_eng
        self.Tf_load: float = Tf_load
        self.Kp_load: float = Kp_load
        self.Ki_load: float = Ki_load
        self.Ld_ref: float = Ld_ref
        self.Dm: float = Dm
        self.R_open: float = R_open
        self.R_close: float = R_close
        self.Ki_mw: float = Ki_mw
        self.A_set: float = A_set
        self.Ka: float = Ka
        self.Ta: float = Ta
        self.T_rate: float = T_rate
        self.db: float = db
        self.Tsa: float = Tsa
        self.Tsb: float = Tsb
        self.R_lim: SiennaUpDown = R_lim
        self.P_ref: float = P_ref


def parse_sienna_general_gov_model(data: dict[str, Any]) -> SiennaGeneralGovModel:
    """Parse declared GeneralGovModel properties into fixed slots.

    :param data: Schema-validated JSON object.
    :return: Typed GeneralGovModel object.
    """
    # concrete-nested-conversion: each declared reference is materialized explicitly.
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import parse_sienna_min_max
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import parse_sienna_up_down
    return SiennaGeneralGovModel(id=get_required_value(data, 'id', 'GeneralGovModel'), Rselect=get_required_value(data, 'Rselect', 'GeneralGovModel'), fuel_flag=get_required_value(data, 'fuel_flag', 'GeneralGovModel'), R=data.get('R', None), Tpelec=get_required_value(data, 'Tpelec', 'GeneralGovModel'), speed_error_signal=parse_sienna_min_max(get_required_value(data, 'speed_error_signal', 'GeneralGovModel')), Kp_gov=get_required_value(data, 'Kp_gov', 'GeneralGovModel'), Ki_gov=get_required_value(data, 'Ki_gov', 'GeneralGovModel'), Kd_gov=get_required_value(data, 'Kd_gov', 'GeneralGovModel'), Td_gov=get_required_value(data, 'Td_gov', 'GeneralGovModel'), valve_position_limits=parse_sienna_min_max(get_required_value(data, 'valve_position_limits', 'GeneralGovModel')), T_act=get_required_value(data, 'T_act', 'GeneralGovModel'), K_turb=get_required_value(data, 'K_turb', 'GeneralGovModel'), Wf_nl=get_required_value(data, 'Wf_nl', 'GeneralGovModel'), Tb=get_required_value(data, 'Tb', 'GeneralGovModel'), Tc=get_required_value(data, 'Tc', 'GeneralGovModel'), T_eng=get_required_value(data, 'T_eng', 'GeneralGovModel'), Tf_load=get_required_value(data, 'Tf_load', 'GeneralGovModel'), Kp_load=get_required_value(data, 'Kp_load', 'GeneralGovModel'), Ki_load=get_required_value(data, 'Ki_load', 'GeneralGovModel'), Ld_ref=get_required_value(data, 'Ld_ref', 'GeneralGovModel'), Dm=get_required_value(data, 'Dm', 'GeneralGovModel'), R_open=get_required_value(data, 'R_open', 'GeneralGovModel'), R_close=get_required_value(data, 'R_close', 'GeneralGovModel'), Ki_mw=get_required_value(data, 'Ki_mw', 'GeneralGovModel'), A_set=get_required_value(data, 'A_set', 'GeneralGovModel'), Ka=get_required_value(data, 'Ka', 'GeneralGovModel'), Ta=get_required_value(data, 'Ta', 'GeneralGovModel'), T_rate=get_required_value(data, 'T_rate', 'GeneralGovModel'), db=get_required_value(data, 'db', 'GeneralGovModel'), Tsa=get_required_value(data, 'Tsa', 'GeneralGovModel'), Tsb=get_required_value(data, 'Tsb', 'GeneralGovModel'), R_lim=parse_sienna_up_down(get_required_value(data, 'R_lim', 'GeneralGovModel')), P_ref=data.get('P_ref', None))

def sienna_general_gov_model_to_json(value: SiennaGeneralGovModel) -> dict[str, Any]:
    """Write every GeneralGovModel slot to explicit schema property names.

    :param value: Typed GeneralGovModel object.
    :return: JSON object with declared schema properties.
    """
    from VeraGridEngine.IO.sienna.devices.core.common.min_max import sienna_min_max_to_json
    from VeraGridEngine.IO.sienna.devices.core.common.up_down import sienna_up_down_to_json
    return {'id': value.id, 'Rselect': value.Rselect, 'fuel_flag': value.fuel_flag, 'R': value.R, 'Tpelec': value.Tpelec, 'speed_error_signal': sienna_min_max_to_json(value.speed_error_signal), 'Kp_gov': value.Kp_gov, 'Ki_gov': value.Ki_gov, 'Kd_gov': value.Kd_gov, 'Td_gov': value.Td_gov, 'valve_position_limits': sienna_min_max_to_json(value.valve_position_limits), 'T_act': value.T_act, 'K_turb': value.K_turb, 'Wf_nl': value.Wf_nl, 'Tb': value.Tb, 'Tc': value.Tc, 'T_eng': value.T_eng, 'Tf_load': value.Tf_load, 'Kp_load': value.Kp_load, 'Ki_load': value.Ki_load, 'Ld_ref': value.Ld_ref, 'Dm': value.Dm, 'R_open': value.R_open, 'R_close': value.R_close, 'Ki_mw': value.Ki_mw, 'A_set': value.A_set, 'Ka': value.Ka, 'Ta': value.Ta, 'T_rate': value.T_rate, 'db': value.db, 'Tsa': value.Tsa, 'Tsb': value.Tsb, 'R_lim': sienna_up_down_to_json(value.R_lim), 'P_ref': value.P_ref}
