# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native catalogue module for the OSTB5T Ontario Hydro stabilizer."""

from VeraGridEngine.Templates.Rms.power_system_stabilizers.ostb2t import (
    Ostb2tParameters,
    build_ostb2t_template,
)

__all__ = ('Ostb2tParameters', 'build_ostb2t_template')
