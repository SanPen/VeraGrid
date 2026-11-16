# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native catalogue module for the WT12T1 Type 1/2 shaft model."""

from VeraGridEngine.Templates.Rms.renewable_controls.wt12t1_drive_train import (
    Wt12t1DriveTrainSettings,
    build_wt12t1_drive_train_template,
)

__all__ = ('Wt12t1DriveTrainSettings', 'build_wt12t1_drive_train_template')
