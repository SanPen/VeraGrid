# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Regression checks for grid base frequency in current and legacy archives."""

import pandas as pd

from VeraGridEngine.api import open_file, save_file
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.IO.veragrid.generic_io_functions import parse_config_df
from VeraGridEngine.IO.veragrid.pack_unpack import gather_model_as_data_frames, parse_veragrid_data
from VeraGridEngine.basic_structures import Logger


def test_gridcal_base_frequency_roundtrip(tmp_path):
    grid = MultiCircuit(fbase=60.0)
    path = tmp_path / "frequency.gridcal"

    save_file(grid, str(path))

    assert open_file(str(path)).fBase == 60.0


def test_legacy_config_base_frequency_and_missing_value():
    grid = MultiCircuit(fbase=60.0)
    config = gather_model_as_data_frames(grid, legacy=True)["config"].set_index("Property")

    assert parse_veragrid_data(parse_config_df(config), logger=Logger()).fBase == 60.0

    old_config = pd.DataFrame(
        [("BaseMVA", "100")], columns=["Property", "Value"]
    ).set_index("Property")
    assert parse_veragrid_data(parse_config_df(old_config), logger=Logger()).fBase == 50.0
