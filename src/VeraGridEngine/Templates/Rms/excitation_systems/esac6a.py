# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Public module path for the original ESAC6A excitation realization."""

from VeraGridEngine.Templates.Rms.excitation_systems.ac6a import (
    build_esac6a_template,
)

__all__: list[str] = ['build_esac6a_template']
