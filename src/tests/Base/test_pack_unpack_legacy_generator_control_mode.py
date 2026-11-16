# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import pandas as pd
from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.Devices as dev
from VeraGridEngine.IO.veragrid.pack_unpack import parse_object_type_from_dataframe, parse_object_type_from_json
from VeraGridEngine.enumerations import GeneratorControlMode, TapPhaseControl, WindingType


def test_parse_object_type_from_json_maps_legacy_is_controlled_to_control_mode() -> None:
    template = dev.Generator()
    logger = Logger()

    devices, _ = parse_object_type_from_json(
        template_elm=template,
        data_list=[
            {"idtag": "gen-v", "name": "Gen V", "is_controlled": True},
            {"idtag": "gen-q", "name": "Gen Q", "is_controlled": False},
        ],
        elements_dict_by_type={},
        time_profile=None,
        block_parser=None,
        logger=logger,
    )

    assert devices[0].control_mode == GeneratorControlMode.V
    assert devices[1].control_mode == GeneratorControlMode.Q


def test_parse_object_type_from_dataframe_maps_legacy_transformer_connection() -> None:
    """Translate a legacy transformer pair into canonical winding connections."""
    dataframe: pd.DataFrame = pd.DataFrame(({'idtag': 'transformer-gd', 'conn': 'GD'},))
    logger: Logger = Logger()
    devices, _, _ = parse_object_type_from_dataframe(
        main_df=dataframe,
        template_elm=dev.Transformer2W(),
        elements_dict_by_type=dict(),
        time_profile=None,
        object_type_key='transformer2w',
        data=dict(),
        logger=logger,
        reflexive_references=list(),
        physical_device_references=list(),
    )

    assert devices[0].conn_f == WindingType.GroundedStar
    assert devices[0].conn_t == WindingType.Delta


def test_parse_object_type_from_json_maps_legacy_transformer_connection() -> None:
    """Translate the unknown legacy connection field from declarative JSON."""
    devices, _ = parse_object_type_from_json(
        template_elm=dev.Transformer2W(),
        data_list=[{'idtag': 'transformer-dd', 'conn': 'DD'}],
        elements_dict_by_type=dict(),
        time_profile=None,
        block_parser=None,
        logger=Logger(),
    )

    assert devices[0].conn_f == WindingType.Delta
    assert devices[0].conn_t == WindingType.Delta


def test_parse_object_type_from_dataframe_maps_legacy_transformer_control_mode() -> None:
    """Delegate a retired combined tap-control field to the transformer."""
    dataframe: pd.DataFrame = pd.DataFrame(({'idtag': 'transformer-pf', 'control_mode': 'Pf'},))
    devices, _, _ = parse_object_type_from_dataframe(
        main_df=dataframe,
        template_elm=dev.Transformer2W(),
        elements_dict_by_type=dict(),
        time_profile=None,
        object_type_key='transformer2w',
        data=dict(),
        logger=Logger(),
        reflexive_references=list(),
        physical_device_references=list(),
    )

    assert devices[0].tap_phase_control_mode == TapPhaseControl.Pf
