from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

import numpy as np

from VeraGridEngine.basic_structures import IntVec
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Devices.Profiles.sparse_array_device import SparseArrayDevice

if TYPE_CHECKING:
    from VeraGridEngine.Devices.Parents.editable_device import EditableDevice


class ProfileDevice:
    """
    Profile specialized for editable-device references.
    """

    __slots__ = (
        "_is_sparse",
        "_sparse_array",
        "_dense_array",
        "_sparsity_threshold",
        "_dtype",
        "_initialized",
        "_default_value",
    )

    def __init__(
        self,
        default_value: "EditableDevice | str | None",
        device_type: DeviceType,
        arr: np.ndarray | None = None,
        sparsity_threshold: float = 0.8,
        is_sparse: bool = False,
    ) -> None:
        """
        Build a device profile.

        :param default_value: Declared default value.
        :param device_type: Allowed device selector.
        :param arr: Optional dense source array.
        :param sparsity_threshold: Sparse storage threshold.
        :param is_sparse: Requested initial sparse state.
        """
        self._is_sparse: bool = is_sparse
        self._sparse_array: SparseArrayDevice | None = None
        self._dense_array: np.ndarray | None = None
        self._sparsity_threshold: float = sparsity_threshold
        self._dtype: DeviceType = device_type
        self._initialized: bool = False
        self._default_value: EditableDevice | str | None = self._coerce_value(default_value)

        if arr is not None:
            self.set(arr=arr)
        else:
            self._initialized = False

    def _coerce_value(self, value: Any) -> "EditableDevice | str | None":
        """
        Coerce a raw device payload.

        :param value: Raw value.
        :return: Device reference, serialized idtag, or ``None``.
        """
        if value == "None":
            return None
        else:
            return value

    def clear(self) -> None:
        """
        Clear the profile contents.

        :return: ``None``.
        """
        self._is_sparse = False
        self._sparse_array = None
        self._dense_array = None
        self._initialized = False

    def info(self) -> dict[str, Any]:
        """
        Get diagnostic information.

        :return: Information dictionary.
        """
        return {
            "me": hex(id(self)),
            "initialized": self._initialized,
            "size": self.size(),
            "is_sparse": self._is_sparse,
            "sparsity_threshold": self._sparsity_threshold,
            "default_value": self.default_value,
            "dense_array": {
                "me": hex(id(self._dense_array)),
                "size": len(self._dense_array),
            } if self._dense_array is not None else "None",
            "sparse_array": self._sparse_array.info() if self._sparse_array is not None else "None",
        }

    def get_sparse_map(self) -> dict[int, "EditableDevice | str | None"]:
        """
        Get the sparse map when the profile is sparse.

        :return: Sparse map or an empty dictionary.
        """
        if self._sparse_array is not None:
            return self._sparse_array.get_map()
        else:
            return dict()

    @property
    def dtype(self) -> DeviceType:
        """
        Get the declared selector type.

        :return: Device selector.
        """
        return self._dtype

    @property
    def default_value(self) -> "EditableDevice | str | None":
        """
        Get the profile default value.

        :return: Default value.
        """
        if self._sparse_array is not None:
            return self._sparse_array.default_value
        else:
            return self._default_value

    @default_value.setter
    def default_value(self, val: "EditableDevice | str | None") -> None:
        """
        Set the profile default value.

        :param val: New default value.
        :return: ``None``.
        """
        self._default_value = self._coerce_value(val)

        if self._sparse_array is not None:
            self._sparse_array.default_value = self._default_value
        else:
            self._sparse_array = self._sparse_array

    @property
    def is_sparse(self) -> bool:
        """
        Get whether the profile uses sparse storage.

        :return: Sparse state.
        """
        return self._is_sparse

    @property
    def is_initialized(self) -> bool:
        """
        Get whether the profile has been initialized.

        :return: Initialization state.
        """
        return self._initialized

    def set_initialized(self) -> None:
        """
        Mark the profile as initialized.

        :return: ``None``.
        """
        self._initialized = True

    @property
    def sparse_array(self) -> SparseArrayDevice | None:
        """
        Get the sparse backing array.

        :return: Sparse array or ``None``.
        """
        return self._sparse_array

    @property
    def dense_array(self) -> np.ndarray | None:
        """
        Get the dense backing array.

        :return: Dense array or ``None``.
        """
        return self._dense_array

    def create_sparse(
        self,
        size: int,
        default_value: "EditableDevice | str | None",
        map_data: dict[int, "EditableDevice | str | None"] | None = None,
    ) -> None:
        """
        Create the profile in sparse form.

        :param size: Logical size.
        :param default_value: Sparse default value.
        :param map_data: Optional sparse map.
        :return: ``None``.
        """
        self._is_sparse = True
        self._default_value = self._coerce_value(default_value)
        self._sparse_array = SparseArrayDevice(default_value=self._default_value, device_type=self._dtype)

        if map_data is None:
            self._sparse_array.create(size=size, default_value=self._default_value)
        else:
            self._sparse_array.create_from_dict(default_value=self._default_value, size=size, map_data=map_data)

        self._dense_array = None
        self._initialized = True

    def create_dense(self, size: int, default_value: "EditableDevice | str | None") -> None:
        """
        Create the profile in dense form.

        :param size: Logical size.
        :param default_value: Dense fill value.
        :return: ``None``.
        """
        self._is_sparse = False
        self._default_value = self._coerce_value(default_value)
        self._dense_array = np.full(size, self._default_value, dtype=object)
        self._sparse_array = None
        self._initialized = True

    @property
    def sparsity(self) -> float:
        """
        Get the sparse stored-entry ratio.

        :return: Sparsity ratio.
        """
        if self._is_sparse and self._sparse_array is not None:
            return self._sparse_array.get_sparsity()
        else:
            return 0.0

    def set(self, arr: np.ndarray) -> bool:
        """
        Set the profile from a dense array.

        :param arr: Dense device-reference array.
        :return: ``True`` when the assignment succeeds.
        """
        if not isinstance(arr, np.ndarray):
            print("You can only set numpy arrays")
            return False
        else:
            if arr.ndim != 1:
                print("You can only set 1D numpy arrays")
                return False
            else:
                if len(arr) == 0:
                    return False
                else:
                    arr_values: list[EditableDevice | str | None] = list()

                    # Coerce every element explicitly so the profile never keeps mixed device payloads.
                    for raw_value in arr:
                        arr_values.append(self._coerce_value(raw_value))

                    arr_mod: np.ndarray = np.array(arr_values, dtype=object)

                    if self.size() > 0:
                        if len(arr_mod) != self.size():
                            raise ValueError("The array must have the same size as the profile")
                        else:
                            arr_mod = arr_mod
                    else:
                        arr_mod = arr_mod

                    counts: Counter[EditableDevice | str | None] = Counter(arr_mod.tolist())
                    most_common_element: EditableDevice | str | None
                    most_common_count: int
                    most_common_element, most_common_count = counts.most_common(1)[0]
                    sparsity_factor: float = most_common_count / len(arr_mod)

                    if sparsity_factor >= self._sparsity_threshold:
                        base_value: EditableDevice | str | None = self._coerce_value(most_common_element)
                        data_map: dict[int, EditableDevice | str | None] = dict()

                        for idx, raw_value in enumerate(arr_mod):
                            coerced_value: EditableDevice | str | None = self._coerce_value(raw_value)
                            if coerced_value != base_value:
                                data_map[idx] = coerced_value
                            else:
                                data_map = data_map

                        self._is_sparse = True
                        self._default_value = base_value
                        self._sparse_array = SparseArrayDevice(default_value=base_value, device_type=self._dtype)
                        self._sparse_array.create(size=len(arr_mod), default_value=base_value, data=data_map)
                        self._dense_array = None
                    else:
                        self._is_sparse = False
                        self._dense_array = arr_mod
                        self._sparse_array = None
                        self._default_value = self._coerce_value(arr_mod[0])

                    self._initialized = True
                    return True

    def __eq__(self, other: object) -> bool:
        """
        Compare two profiles.

        :param other: Object to compare against.
        :return: ``True`` when both profiles match.
        """
        if isinstance(other, ProfileDevice):
            if self._is_sparse == other._is_sparse:
                if self._is_sparse:
                    if self._sparse_array is None and other._sparse_array is None:
                        return self.default_value == other.default_value
                    else:
                        if self._sparse_array is not None and other._sparse_array is not None:
                            return self._sparse_array == other._sparse_array
                        else:
                            return False
                else:
                    if self._dense_array is None and other._dense_array is None:
                        return self.default_value == other.default_value
                    else:
                        if self._dense_array is not None and other._dense_array is not None:
                            return np.array_equal(self._dense_array, other._dense_array)
                        else:
                            return False
            else:
                return False
        else:
            return False

    def __ne__(self, other: object) -> bool:
        """
        Compare two profiles for inequality.

        :param other: Object to compare against.
        :return: ``True`` when both profiles differ.
        """
        return not self.__eq__(other)

    def __getitem__(self, key: int) -> "EditableDevice | str | None":
        """
        Get a value by index.

        :param key: Position to read.
        :return: Value at ``key``.
        """
        if self._is_sparse:
            if self._sparse_array is not None:
                return self._sparse_array[key]
            else:
                return self.default_value
        else:
            if self._dense_array is None:
                self._is_sparse = True
                self._sparse_array = SparseArrayDevice(default_value=self.default_value, device_type=self._dtype)
                print("Initializing sparse when querying, this signals a mis initialization")
                return self.default_value
            else:
                return self._coerce_value(self._dense_array[key])

    def __setitem__(self, key: int, value: "EditableDevice | str | None") -> None:
        """
        Set a value by index.

        :param key: Position to write.
        :param value: Value to store.
        :return: ``None``.
        """
        if isinstance(key, int):
            coerced_value: EditableDevice | str | None = self._coerce_value(value)

            if self._is_sparse:
                if self._sparse_array is not None:
                    if key < self._sparse_array.size():
                        self._sparse_array[key] = coerced_value
                    else:
                        raise AssertionError("Key out of bounds")
                else:
                    raise AssertionError("Sparse profile not initialized")
            else:
                if self._dense_array is not None:
                    if key < len(self._dense_array):
                        self._dense_array[key] = coerced_value
                    else:
                        raise AssertionError("Key out of bounds")
                else:
                    raise AssertionError("Dense profile not initialized")
        else:
            raise TypeError("Key must be an integer")

    def __imul__(self, other: float | int) -> "ProfileDevice":
        """
        Reject in-place scaling because device profiles are not numeric.

        :param other: Scalar multiplier.
        :return: ``self``.
        """
        raise TypeError(f"Unsupported type {type(other)}")

    def convert_sparse_to_dense(self) -> None:
        """
        Convert the sparse profile into dense storage.

        :return: ``None``.
        """
        if self._is_sparse and self._sparse_array is not None:
            self._dense_array = self._sparse_array.toarray()
            self._sparse_array = None
            self._is_sparse = False
        else:
            self._is_sparse = self._is_sparse

    def resize(self, n: int) -> None:
        """
        Resize the profile.

        :param n: New logical size.
        :return: ``None``.
        """
        if isinstance(n, int):
            if self._initialized:
                if self._is_sparse:
                    if self._sparse_array is not None:
                        self._sparse_array.resize(n=n)
                    else:
                        raise AssertionError("Sparse profile not initialized")
                else:
                    if self._dense_array is not None:
                        new_array: np.ndarray = np.full(n, self.default_value, dtype=object)
                        copy_size: int = min(len(self._dense_array), n)
                        new_array[:copy_size] = self._dense_array[:copy_size]
                        self._dense_array = new_array
                    else:
                        raise AssertionError("Dense profile not initialized")
            else:
                self._initialized = True
                self.create_sparse(size=n, default_value=self.default_value)
        else:
            raise TypeError("The size must be an integer")

    def resample(self, indices: IntVec) -> None:
        """
        Resample the profile in place.

        :param indices: New index selection.
        :return: ``None``.
        """
        if self._is_sparse:
            if self._sparse_array is not None:
                self._sparse_array.resample(indices=indices)
            else:
                raise AssertionError("Sparse profile not initialized")
        else:
            if self._dense_array is not None:
                self._dense_array = self._dense_array[indices]
            else:
                raise AssertionError("Dense profile not initialized")

    def fill(self, value: "EditableDevice | str | None") -> None:
        """
        Fill the profile with a single value.

        :param value: Fill value.
        :return: ``None``.
        """
        coerced_value: EditableDevice | str | None = self._coerce_value(value)
        self.default_value = coerced_value
        self._is_sparse = True

        if self._sparse_array is None:
            self._sparse_array = SparseArrayDevice(default_value=coerced_value, device_type=self._dtype)
        else:
            self._sparse_array = self._sparse_array

        self._sparse_array.fill(coerced_value)
        self._dense_array = None
        self._initialized = True

    def scale(self, value: float | int) -> None:
        """
        Reject scaling because device profiles are not numeric.

        :param value: Scalar multiplier.
        :return: ``None``.
        """
        raise TypeError("This profile type does not support scaling")

    def size(self) -> int:
        """
        Get the profile size.

        :return: Logical size.
        """
        if self._initialized:
            if self._is_sparse:
                if self._sparse_array is not None:
                    return self._sparse_array.size()
                else:
                    return 0
            else:
                if self._dense_array is not None:
                    return len(self._dense_array)
                else:
                    return 0
        else:
            return 0

    def toarray(self) -> np.ndarray:
        """
        Get the dense numpy representation.

        :return: Dense object array.
        """
        if self.size() > 0:
            if self._is_sparse:
                if self._sparse_array is not None:
                    return self._sparse_array.toarray()
                else:
                    return np.zeros(0, dtype=object)
            else:
                if self._dense_array is not None:
                    return self._dense_array
                else:
                    return np.zeros(0, dtype=object)
        else:
            return np.zeros(0, dtype=object)

    def tolist(self) -> list["EditableDevice | str | None"]:
        """
        Get the dense list representation.

        :return: Dense list.
        """
        return self.toarray().tolist()

    def astype(self, tpe: Any) -> np.ndarray:
        """
        Cast the dense representation to another dtype.

        :param tpe: Target dtype.
        :return: Cast dense array.
        """
        return self.toarray().astype(tpe)

    def get_sparse_representation(self) -> tuple[list[int], list["EditableDevice | str | None"]]:
        """
        Export the sparse contents as parallel index and value lists.

        :return: Tuple ``(indices, values)``.
        """
        if self._sparse_array is not None:
            return self._sparse_array.get_sparse_representation()
        else:
            return list(), list()

    def set_sparse_data_from_data(self, indptr: list[int], data: list["EditableDevice | str | None"]) -> None:
        """
        Load sparse data from parallel lists.

        :param indptr: Sparse indices.
        :param data: Sparse values.
        :return: ``None``.
        """
        if self._sparse_array is not None:
            self._sparse_array.set_sparse_data_from_data(indptr=indptr, data=data)
        else:
            raise AssertionError("Sparse profile not initialized")

    def fix_nan(self, default_value: float = 0.0) -> None:
        """
        Keep the device profile API aligned with the generic profile.

        :param default_value: Unused placeholder.
        :return: ``None``.
        """
        self._default_value = self._default_value

    def copy(self) -> "ProfileDevice":
        """
        Build a deep copy of the profile.

        :return: New profile copy.
        """
        copied_profile: ProfileDevice = ProfileDevice(
            default_value=self.default_value,
            device_type=self._dtype,
            arr=None,
            sparsity_threshold=self._sparsity_threshold,
            is_sparse=self.is_sparse,
        )

        if self._sparse_array is not None:
            copied_profile._sparse_array = self._sparse_array.copy()
        else:
            copied_profile._sparse_array = None

        if self._dense_array is not None:
            copied_profile._dense_array = self._dense_array.copy()
        else:
            copied_profile._dense_array = None

        copied_profile._default_value = self.default_value
        copied_profile._initialized = self.is_initialized

        return copied_profile
