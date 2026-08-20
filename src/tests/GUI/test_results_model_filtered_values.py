# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
from PySide6 import QtCore

from VeraGrid.Gui.results_model import ResultsModel
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.enumerations import DeviceType


def test_results_model_displays_filtered_nan_as_an_empty_cell() -> None:
    """
    Verify filtered-out results do not display the literal text ``nan``.

    :return: None.
    """
    table: ResultsTable = ResultsTable(
        data=np.array(((np.nan,),), dtype=float),
        columns=np.array(("Mode 0",), dtype=str),
        index=np.array(("delta1",), dtype=str),
        title="Missing value display test",
        cols_device_type=DeviceType.NoDevice,
        idx_device_type=DeviceType.NoDevice,
    )
    model: ResultsModel = ResultsModel(table=table)
    index: QtCore.QModelIndex = model.index(0, 0)

    assert model.data(index=index, role=QtCore.Qt.ItemDataRole.DisplayRole) == ""
