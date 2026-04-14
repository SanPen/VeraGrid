from __future__ import annotations

from collections import Counter
from enum import Enum
from typing import Any, TypeAlias

import numpy as np

from VeraGridEngine.enumerations import DeviceType

ProfileDataType: TypeAlias = type[bool] | type[int] | type[float] | type[Enum] | DeviceType


def is_enum_data_type(data_type: Any) -> bool:
    """
    Check whether the declared profile type is an enum class.

    :param data_type: Declared profile type.
    :return: ``True`` when the type is an enum class, ``False`` otherwise.
    """
    if isinstance(data_type, type):
        return issubclass(data_type, Enum)
    else:
        return False


def coerce_bool_value(value: Any) -> bool:
    """
    Convert an incoming value into a boolean.

    :param value: Value to coerce.
    :return: Boolean representation of ``value``.
    """
    if isinstance(value, str):
        normalized_value: str = value.strip().lower()
        if normalized_value in {"true", "1"}:
            return True
        else:
            if normalized_value in {"false", "0"}:
                return False
            else:
                return bool(value)
    else:
        return bool(value)


def check_type(dtype: ProfileDataType, value: Any) -> bool:
    """
    Check that a value is compatible with a declared profile type.

    :param dtype: Declared profile type.
    :param value: Value to validate.
    :return: ``True`` when ``value`` matches ``dtype``.
    """
    if value is None:
        if isinstance(dtype, DeviceType):
            return True
        else:
            return False

    tpe: type[Any] = type(value)

    if tpe in [bool, np.bool_]:
        return dtype == bool
    else:
        if tpe in [int, np.int32, np.int64]:
            return dtype == int or dtype == float
        else:
            if tpe in [float, np.float32, np.float64]:
                return dtype == float
            else:
                if is_enum_data_type(dtype):
                    if isinstance(value, Enum):
                        return type(value) == dtype
                    else:
                        return False
                else:
                    if isinstance(dtype, DeviceType):
                        return True
                    else:
                        return False


def check_if_sparse(arr: np.ndarray, sparsity: float = 0.8) -> tuple[bool, Any]:
    """
    Check whether an array should be stored as sparse.

    :param arr: Array to inspect.
    :param sparsity: Minimum repetition ratio required for sparse storage.
    :return: Tuple ``(is_sparse, most_frequent_value)``.
    """
    if sparsity > 0.99:
        effective_sparsity: float = 0.9
    else:
        effective_sparsity = sparsity

    min_elements: int = int(float(len(arr)) * (1.0 - effective_sparsity))
    if min_elements < 1:
        min_elements = 1
    else:
        min_elements = min_elements

    if len(arr) < min_elements:
        return False, 0
    else:
        values_list: list[Any] = arr.tolist()
        counts: Counter[Any] = Counter(values_list)

        if len(counts) > min_elements:
            return False, 0.0
        else:
            most_common_value: Any
            most_common_count: int
            most_common_value, most_common_count = counts.most_common(1)[0]

            if most_common_count > 0:
                return True, most_common_value
            else:
                return False, 0.0
