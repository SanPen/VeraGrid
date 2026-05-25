# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from pathlib import Path

MATPOWER_FIXTURES: Path = Path(__file__).resolve().parents[2] / "data" / "grids" / "Matpower"
