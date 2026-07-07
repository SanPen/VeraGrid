from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.Devices as dev
from VeraGridEngine.IO.veragrid.pack_unpack import parse_object_type_from_json
from VeraGridEngine.enumerations import GeneratorControlMode


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
