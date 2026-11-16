# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np
from numpy import random
import VeraGridEngine as gce

def test_CDF_expectation():

    x = random.normal(4, 1, size=20)

    assert np.allclose(x.mean(), gce.CDF(x).expectation(), atol=1e-5)

    x = random.rand(200)

    assert np.allclose(x.mean(), gce.CDF(x).expectation(), atol=1e-5)
