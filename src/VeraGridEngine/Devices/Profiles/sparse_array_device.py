from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from VeraGridEngine.basic_structures import IntVec
from VeraGridEngine.enumerations import DeviceType

if TYPE_CHECKING:
    from VeraGridEngine.Devices.Parents.editable_device import EditableDevice


class SparseArrayDevice:
    """
    Sparse array specialized for editable-device references.
    """

    __slots__ = (
        "_dtype",
        "_default_value",
        "_size",
        "_map",
    )

    def __init__(self, default_value: "EditableDevice | str | None", device_type: DeviceType, size: int = 0) -> None:
        """
        Build a device sparse array.

        :param default_value: Default sparse value.
        :param device_type: Allowed device selector.
        :param size: Logical array size.
        """
        self._dtype: DeviceType = device_type
        self._default_value: EditableDevice | str | None = self._coerce_value(default_value)
        self._size: int = size
        self._map: dict[int, EditableDevice | str | None] = dict()

    def _coerce_value(self, value: Any) -> "EditableDevice | str | None":
        """
        Coerce the raw device payload.

        :param value: Raw value.
        :return: Device reference, serialized idtag, or ``None``.
        """
        if value == "None":
            return None
        else:
            return value

    def copy(self) -> "SparseArrayDevice":
        """
        Build a deep copy of the sparse array.

        :return: New sparse array copy.
        """
        copied_array: SparseArrayDevice = SparseArrayDevice(
            default_value=self._default_value,
            device_type=self._dtype,
            size=self._size,
        )
        copied_array._map = self._map.copy()
        return copied_array

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
        Get the default sparse value.

        :return: Default sparse value.
        """
        return self._default_value

    @default_value.setter
    def default_value(self, val: "EditableDevice | str | None") -> None:
        """
        Change the default sparse value while preserving the represented dense data.

        :param val: New default value.
        :return: ``None``.
        """
        coerced_value: EditableDevice | str | None = self._coerce_value(val)

        if coerced_value != self._default_value:
            if self._size > 0 and len(self._map) < self._size:
                old_default_value: EditableDevice | str | None = self._default_value

                # Materialize implicit positions before changing the default so values do not change logically.
                for idx in range(self._size):
                    if idx not in self._map:
                        self._map[idx] = old_default_value
                    else:
                        self._map[idx] = self._map[idx]
            else:
                pass

            keys_to_remove: list[int] = list()
            for key, value in self._map.items():
                if value == coerced_value:
                    keys_to_remove.append(key)
                else:
                    keys_to_remove = keys_to_remove

            for key in keys_to_remove:
                del self._map[key]

            self._default_value = coerced_value
        else:
            self._default_value = self._default_value

    def info(self) -> dict[str, Any]:
        """
        Get diagnostic information.

        :return: Information dictionary.
        """
        return {
            "me": hex(id(self)),
            "default_value": self._default_value,
            "size": self._size,
            "map": hex(id(self._map)),
        }

    def get_map(self) -> dict[int, "EditableDevice | str | None"]:
        """
        Get the sparse map.

        :return: Sparse index-value map.
        """
        return self._map

    def insert(self, i: int, x: "EditableDevice | str | None") -> None:
        """
        Insert a sparse value explicitly.

        :param i: Target index.
        :param x: Value to store.
        :return: ``None``.
        """
        self._map[i] = self._coerce_value(x)

    def get_sparsity(self) -> float:
        """
        Get the stored-entry ratio.

        :return: Sparsity ratio.
        """
        if self._size > 0:
            return float(len(self._map)) / float(self._size)
        else:
            return 0.0

    def create(
        self,
        size: int,
        default_value: "EditableDevice | str | None",
        data: dict[int, "EditableDevice | str | None"] | None = None,
    ) -> "SparseArrayDevice":
        """
        Create the sparse array from explicit sparse data.

        :param size: Logical size.
        :param default_value: Default sparse value.
        :param data: Sparse map.
        :return: ``self``.
        """
        self.default_value = default_value
        self._size = size

        if data is None:
            self._map = dict()
        else:
            self.set_data(data)

        return self

    def create_from_array(
        self,
        array: np.ndarray,
        default_value: "EditableDevice | str | None",
    ) -> "SparseArrayDevice":
        """
        Create the sparse array from a dense array.

        :param array: Dense object array.
        :param default_value: Default sparse value.
        :return: ``self``.
        """
        self.default_value = default_value
        self._size = len(array)
        self._map = dict()

        # Device values are object references, so the sparse extraction stays explicit and type-safe.
        for idx, raw_value in enumerate(array):
            value: EditableDevice | str | None = self._coerce_value(raw_value)

            if value != self._default_value:
                self._map[idx] = value
            else:
                self._map = self._map

        return self

    def create_from_dict(
        self,
        default_value: "EditableDevice | str | None",
        size: int,
        map_data: dict[int, "EditableDevice | str | None"],
    ) -> "SparseArrayDevice":
        """
        Create the sparse array from a sparse map.

        :param default_value: Default sparse value.
        :param size: Logical size.
        :param map_data: Sparse map.
        :return: ``self``.
        """
        self.default_value = default_value
        self._size = size
        self.set_data(map_data)
        return self

    def fill(self, value: "EditableDevice | str | None") -> None:
        """
        Fill the logical array with the same value.

        :param value: Fill value.
        :return: ``None``.
        """
        self.default_value = value
        self._map = dict()

    def toarray(self) -> np.ndarray:
        """
        Expand the sparse array into a dense numpy array.

        :return: Dense object array.
        """
        dense_array: np.ndarray = np.full(self._size, self._default_value, dtype=object)

        # Scatter the explicitly stored sparse entries into the dense output.
        for key, value in self._map.items():
            dense_array[key] = value

        return dense_array

    def at(self, idx: int) -> "EditableDevice | str | None":
        """
        Get a value at a given position.

        :param idx: Position to read.
        :return: Value at ``idx``.
        """
        if len(self._map) == 0:
            return self._default_value
        else:
            value: EditableDevice | str | None = self._map.get(idx, None)
            if value is None:
                return self._default_value
            else:
                return value

    def __getitem__(self, key: int) -> "EditableDevice | str | None":
        """
        Get a value using index syntax.

        :param key: Position to read.
        :return: Value at ``key``.
        """
        return self.at(idx=key)

    def __setitem__(self, key: int, value: "EditableDevice | str | None") -> None:
        """
        Set a value using index syntax.

        :param key: Position to write.
        :param value: Value to store.
        :return: ``None``.
        """
        if isinstance(key, int):
            if key < self._size:
                coerced_value: EditableDevice | str | None = self._coerce_value(value)

                if coerced_value != self._default_value:
                    self._map[key] = coerced_value
                else:
                    if key in self._map:
                        del self._map[key]
                    else:
                        self._map = self._map
            else:
                raise AssertionError("Key out of bounds")
        else:
            raise TypeError("Key must be an integer")

    def __eq__(self, other: object) -> bool:
        """
        Compare two sparse arrays.

        :param other: Object to compare against.
        :return: ``True`` when both sparse arrays match.
        """
        if isinstance(other, SparseArrayDevice):
            if self._default_value != other._default_value:
                return False
            else:
                if self._size != other._size:
                    return False
                else:
                    if self._map != other._map:
                        return False
                    else:
                        return True
        else:
            return False

    def size(self) -> int:
        """
        Get the logical size.

        :return: Logical size.
        """
        return self._size

    def clear(self) -> None:
        """
        Clear the sparse contents.

        :return: ``None``.
        """
        self._map.clear()
        self._size = 0

    def set_data(self, d: dict[int, "EditableDevice | str | None"]) -> None:
        """
        Replace the sparse map.

        :param d: New sparse map.
        :return: ``None``.
        """
        new_map: dict[int, EditableDevice | str | None] = dict()

        for key, value in d.items():
            coerced_key: int = int(key)
            coerced_value: EditableDevice | str | None = self._coerce_value(value)

            if coerced_value != self._default_value:
                new_map[coerced_key] = coerced_value
            else:
                new_map = new_map

        self._map = new_map

    def resize(self, n: int) -> None:
        """
        Resize the sparse array.

        :param n: New logical size.
        :return: ``None``.
        """
        if n < self._size:
            keys_to_remove: list[int] = list()

            for key in self._map.keys():
                if key >= n:
                    keys_to_remove.append(key)
                else:
                    keys_to_remove = keys_to_remove

            for key in keys_to_remove:
                del self._map[key]
        else:
            pass

        self._size = n

    def resample(self, indices: IntVec) -> None:
        """
        Resample the sparse array in place.

        :param indices: New index selection.
        :return: ``None``.
        """
        self._size = len(indices)
        new_map: dict[int, EditableDevice | str | None] = dict()

        # Reindex only the explicitly stored values that survive the new selection.
        for new_idx, old_idx in enumerate(indices):
            sparse_value: EditableDevice | str | None = self._map.get(int(old_idx), None)

            if sparse_value is not None:
                new_map[new_idx] = sparse_value
            else:
                new_map = new_map

        self._map = new_map

    def slice(self, indices: IntVec) -> "SparseArrayDevice":
        """
        Get a resampled copy.

        :param indices: New index selection.
        :return: Resampled sparse array.
        """
        sliced_array: SparseArrayDevice = self.copy()
        sliced_array.resample(indices)
        return sliced_array

    def get_sparse_representation(self) -> tuple[list[int], list["EditableDevice | str | None"]]:
        """
        Export the sparse contents as parallel index and value lists.

        :return: Tuple ``(indices, values)``.
        """
        indptr: list[int] = list()
        data: list[EditableDevice | str | None] = list()

        for idx, value in self._map.items():
            indptr.append(idx)
            data.append(value)

        return indptr, data

    def set_sparse_data_from_data(self, indptr: list[int], data: list["EditableDevice | str | None"]) -> None:
        """
        Load sparse data from parallel lists.

        :param indptr: Sparse indices.
        :param data: Sparse values.
        :return: ``None``.
        """
        self._map = dict()

        for idx, value in zip(indptr, data):
            self._map[int(idx)] = self._coerce_value(value)
