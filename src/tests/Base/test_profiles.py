# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import math
import os
import numpy as np
from VeraGridEngine.Devices.Profiles import check_if_sparse
from VeraGridEngine.Devices.Profiles.profile_bool import ProfileBool
from VeraGridEngine.Devices.Profiles.profile_device import ProfileDevice
from VeraGridEngine.Devices.Profiles.profile_enum import ProfileEnum
from VeraGridEngine.Devices.Profiles.profile_float import ProfileFloat
from VeraGridEngine.Devices.Profiles.profile_int import ProfileInt
from VeraGridEngine.Devices.Profiles.sparse_array_bool import SparseArrayBool
from VeraGridEngine.Devices.Profiles.sparse_array_device import SparseArrayDevice
from VeraGridEngine.Devices.Profiles.sparse_array_enum import SparseArrayEnum
from VeraGridEngine.Devices.Profiles.sparse_array_float import SparseArrayFloat
from VeraGridEngine.Devices.Profiles.sparse_array_int import SparseArrayInt
from VeraGridEngine.enumerations import DeviceType, TapPhaseControl


class DummyDevice:
    """
    Lightweight editable-device stand-in used by unit tests.
    """

    __slots__ = ("idtag", "name")

    def __init__(self, idtag: str, name: str) -> None:
        """
        Build a deterministic dummy device.

        :param idtag: Stable identifier.
        :param name: Human-readable device name.
        :return: ``None``.
        """
        self.idtag: str = idtag
        self.name: str = name


def test_sparse_array_float_dense_roundtrip() -> None:
    """
    Test that float sparse arrays preserve dense input values.

    :return: ``None``.
    """
    n: int = 10
    x: np.ndarray = np.sin(np.arange(n) + 1.0)

    s: SparseArrayFloat = SparseArrayFloat(default_value=0.0)
    s.create_from_array(x, default_value=0.0)

    assert np.allclose(s.toarray(), x)
    assert len(s.get_map()) == n


def test_sparse_array_float_sparse_roundtrip() -> None:
    """
    Test that float sparse arrays keep sparse maps compact.

    :return: ``None``.
    """
    n: int = 100
    x: np.ndarray = np.zeros(n)
    for i in range(10, 30):
        x[i] = math.sin(i)

    s: SparseArrayFloat = SparseArrayFloat(default_value=0.0)
    s.create_from_array(x, default_value=0.0)

    assert np.allclose(s.toarray(), x)
    assert len(s.get_map()) == 20


def test_sparse_array_int_sparse_roundtrip() -> None:
    """
    Test that integer sparse arrays preserve sparse integer data.

    :return: ``None``.
    """
    n: int = 100
    x: np.ndarray = np.full(n, 15)
    x[20] = 30

    is_sparse: bool
    most_frequent: int
    is_sparse, most_frequent = check_if_sparse(arr=x)

    assert is_sparse

    s: SparseArrayInt = SparseArrayInt(default_value=0)
    s.create_from_array(x, default_value=most_frequent)

    assert np.array_equal(s.toarray(), x)
    assert len(s.get_map()) == 1


def test_sparse_array_float_resample() -> None:
    """
    Test that float sparse arrays resample without changing represented values.

    :return: ``None``.
    """
    n: int = 100
    x: np.ndarray = np.zeros(n)
    for i in range(10, 30):
        x[i] = math.sin(i)

    s: SparseArrayFloat = SparseArrayFloat(default_value=0.0)
    s.create_from_array(x, default_value=0)

    rng: np.random.Generator = np.random.default_rng(seed=1234)
    indices: np.ndarray = rng.integers(low=0, high=n, size=n)

    s.resample(indices=indices)
    x2: np.ndarray = x[indices]

    assert np.allclose(s.toarray(), x2)
    assert len(s.get_map()) == len(x2[x2 != 0.0])


def test_sparse_array_bool_roundtrip() -> None:
    """
    Test that boolean sparse arrays preserve their logical values.

    :return: ``None``.
    """
    x: np.ndarray = np.array([True, True, False, True, False, False], dtype=bool)
    s: SparseArrayBool = SparseArrayBool(default_value=False)
    s.create_from_array(x, default_value=False)

    assert np.array_equal(s.toarray(), x)
    assert s.dtype == bool
    assert len(s.get_map()) == 3


def test_sparse_array_enum_roundtrip() -> None:
    """
    Test that enum sparse arrays preserve enum values.

    :return: ``None``.
    """
    x: np.ndarray = np.array(
        [
            TapPhaseControl.fixed,
            TapPhaseControl.fixed,
            TapPhaseControl.Pf,
            TapPhaseControl.fixed,
        ],
        dtype=object,
    )
    s: SparseArrayEnum = SparseArrayEnum(default_value=TapPhaseControl.fixed, enum_type=TapPhaseControl)
    s.create_from_array(x, default_value=TapPhaseControl.fixed)

    assert s.dtype == TapPhaseControl
    assert s.toarray().tolist() == x.tolist()
    assert len(s.get_map()) == 1


def test_sparse_array_device_roundtrip() -> None:
    """
    Test that device sparse arrays preserve editable-device references.

    :return: ``None``.
    """
    device_a: DummyDevice = DummyDevice(idtag="bus_a", name="Bus A")
    device_b: DummyDevice = DummyDevice(idtag="bus_b", name="Bus B")
    x: np.ndarray = np.array([device_a, device_a, device_b, None], dtype=object)
    s: SparseArrayDevice = SparseArrayDevice(default_value=device_a, device_type=DeviceType.BusOrBranch)
    s.create_from_array(x, default_value=device_a)

    assert s.dtype == DeviceType.BusOrBranch
    assert s.toarray().tolist() == x.tolist()
    assert len(s.get_map()) == 2


def test_profile_float_dense_and_sparse_threshold() -> None:
    """
    Test that float profiles switch storage according to the sparsity threshold.

    :return: ``None``.
    """
    n: int = 100
    x: np.ndarray = np.zeros(n)
    for i in range(10, 30):
        x[i] = math.sin(i)

    dense_profile: ProfileFloat = ProfileFloat(default_value=0.0, arr=x, sparsity_threshold=0.9)
    sparse_profile: ProfileFloat = ProfileFloat(default_value=0.0, arr=x, sparsity_threshold=0.75)

    assert not dense_profile.is_sparse
    assert np.allclose(dense_profile.toarray(), x)

    assert sparse_profile.is_sparse
    assert np.allclose(sparse_profile.toarray(), x)
    assert len(sparse_profile.get_sparse_map()) == 20


def test_profile_int_sparse_roundtrip() -> None:
    """
    Test that integer profiles preserve sparse integer data.

    :return: ``None``.
    """
    n: int = 100
    x: np.ndarray = np.full(n, 15)
    x[20] = 30

    profile: ProfileInt = ProfileInt(default_value=15, arr=x)

    assert profile.is_sparse
    assert np.array_equal(profile.toarray(), x)
    assert len(profile.get_sparse_map()) == 1


def test_profile_bool_sparse_roundtrip() -> None:
    """
    Test that boolean profiles preserve logical values through sparse conversion.

    :return: ``None``.
    """
    x: np.ndarray = np.array([True, True, True, False], dtype=bool)
    profile: ProfileBool = ProfileBool(default_value=True, arr=x, sparsity_threshold=0.75)

    assert profile.is_sparse
    assert profile.dtype == bool
    assert np.array_equal(profile.toarray(), x)
    assert len(profile.get_sparse_map()) == 1


def test_profile_enum_sparse_roundtrip() -> None:
    """
    Test that enum profiles keep enum values through sparse conversion.

    :return: ``None``.
    """
    x: np.ndarray = np.array(
        [
            TapPhaseControl.fixed,
            TapPhaseControl.fixed,
            TapPhaseControl.fixed,
            TapPhaseControl.Pf,
        ],
        dtype=object,
    )

    profile: ProfileEnum = ProfileEnum(
        default_value=TapPhaseControl.fixed,
        enum_type=TapPhaseControl,
        arr=x,
        sparsity_threshold=0.75,
    )

    assert profile.is_sparse
    assert profile.default_value == TapPhaseControl.fixed
    assert profile[3] == TapPhaseControl.Pf
    assert profile.toarray().tolist() == x.tolist()
    assert len(profile.get_sparse_map()) == 1


def test_profile_device_sparse_roundtrip() -> None:
    """
    Test that device profiles keep editable-device references through sparse conversion.

    :return: ``None``.
    """
    device_a: DummyDevice = DummyDevice(idtag="bus_a", name="Bus A")
    device_b: DummyDevice = DummyDevice(idtag="bus_b", name="Bus B")
    x: np.ndarray = np.array([device_a, device_a, device_b, device_a], dtype=object)

    profile: ProfileDevice = ProfileDevice(
        default_value=device_a,
        device_type=DeviceType.BusOrBranch,
        arr=x,
        sparsity_threshold=0.75,
    )

    assert profile.is_sparse
    assert profile.default_value is device_a
    assert profile[2] is device_b
    assert profile.toarray().tolist() == x.tolist()
    assert len(profile.get_sparse_map()) == 1


def test_typed_profile_and_sparse_array_construction() -> None:
    """
    Test that every concrete profile and sparse-array class exposes the expected type.

    :return: ``None``.
    """
    profile_float: ProfileFloat = ProfileFloat(default_value=0.0)
    profile_int: ProfileInt = ProfileInt(default_value=1)
    profile_bool: ProfileBool = ProfileBool(default_value=True)
    profile_enum: ProfileEnum = ProfileEnum(default_value=TapPhaseControl.fixed, enum_type=TapPhaseControl)
    profile_device: ProfileDevice = ProfileDevice(default_value=None, device_type=DeviceType.BusOrBranch)

    sparse_float: SparseArrayFloat = SparseArrayFloat(default_value=0.0)
    sparse_int: SparseArrayInt = SparseArrayInt(default_value=0)
    sparse_bool: SparseArrayBool = SparseArrayBool(default_value=False)
    sparse_enum: SparseArrayEnum = SparseArrayEnum(default_value=TapPhaseControl.fixed, enum_type=TapPhaseControl)
    sparse_device: SparseArrayDevice = SparseArrayDevice(default_value=None, device_type=DeviceType.BusOrBranch)

    assert profile_float.dtype == float
    assert profile_int.dtype == int
    assert profile_bool.dtype == bool
    assert profile_enum.dtype == TapPhaseControl
    assert profile_device.dtype == DeviceType.BusOrBranch

    assert sparse_float.dtype == float
    assert sparse_int.dtype == int
    assert sparse_bool.dtype == bool
    assert sparse_enum.dtype == TapPhaseControl
    assert sparse_device.dtype == DeviceType.BusOrBranch


def test_grid_profile_initialization() -> None:
    """
    This test checks that when creating a profile, the profile slices are identical to the snapshot

    :return: ``None``.
    """
    import VeraGridEngine.api as gce

    fname1: str = os.path.join('data', 'grids', 'Matpower', 'case14.matpower')
    fname2: str = os.path.join('data', 'grids', 'ACTIVSg2000.gridcal')

    for fname in [fname1, fname2]:
        grid = gce.open_file(fname)

        # the original grid has no profiles for sure, so we create them
        grid.delete_profiles()
        grid.create_profiles(steps=5, step_length=1.0, step_unit="h")

        nc_base = gce.compile_numerical_circuit_at(circuit=grid, t_idx=None)

        for t_idx in range(grid.get_time_number()):
            nc_t = gce.compile_numerical_circuit_at(circuit=grid, t_idx=t_idx)

            ok, logger = nc_base.compare(nc_t)

            if not ok:
                logger.print()

            assert ok
