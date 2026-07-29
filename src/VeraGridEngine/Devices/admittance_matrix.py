# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Dict, Union, List
import numpy as np
from VeraGridEngine.basic_structures import CxMat, Mat


def list_to_matrix(data: List[List[float]] | None, size: int) -> Mat:
    """
    Attempts converting a list of lists to matrix
    :param data: list of lists of floats representing a matrix
    :param size: size of the matrix (square)
    :return: Numpy array representing a matrix
    """
    if size > 0 and len(data) > 0:
        if data is None:
            return np.zeros((size, size), dtype=complex)
        else:

            candidate = np.array(data)

            if candidate.ndim == 2:
                if candidate.shape[1] == size and candidate.shape[0] == size:
                    return candidate
                else:
                    raise ValueError("AdmittanceMatrix values must be a square matrix")
            else:
                raise ValueError("AdmittanceMatrix values must be a matrix")
    else:
        return np.zeros((size, size), dtype=complex)


class AdmittanceMatrix:
    """
    This is the admittance matrix to store the three-phases admittance of a branch
    """

    __slots__ = (
        "__size",
        "__values",
        "_phN",
        "_phA",
        "_phB",
        "_phC",
    )

    def __init__(self, size: int = 0):
        """
        Constructor
        :param size: size of the matrix (0 to 4)
        """
        self.__size: int = size

        self.__values: CxMat = np.zeros((size, size), dtype=complex)

        self._phN: bool = False
        self._phA: bool = False
        self._phB: bool = False
        self._phC: bool = False

    def copy(self) -> AdmittanceMatrix:
        """
        Make a copy of the admittance matrix
        :return:
        """
        elm = AdmittanceMatrix(size=self.size)
        elm.__values = self.__values.copy()
        elm._phN = self._phN
        elm._phA = self._phA
        elm._phB = self._phB
        elm._phC = self._phC
        return elm

    def __str__(self):
        return f"size {self.__size}: {self._phN}, {self._phA}, {self._phB}, {self._phC}"

    def __repr__(self):
        return self.__str__()

    @property
    def phN(self):
        """

        :return:
        """
        return self._phN

    @phN.setter
    def phN(self, val: bool):
        if isinstance(val, bool):
            self._phN = val
        else:
            raise ValueError(f'{val} is not a bool')

    @property
    def phA(self):
        """

        :return:
        """
        return self._phA

    @phA.setter
    def phA(self, val: bool):
        if isinstance(val, bool):
            self._phA = val
        else:
            raise ValueError(f'{val} is not a bool')

    @property
    def phB(self):
        return self._phB

    @phB.setter
    def phB(self, val: bool):
        if isinstance(val, bool):
            self._phB = val
        else:
            raise ValueError(f'{val} is not a bool')

    @property
    def phC(self):
        return self._phC

    @phC.setter
    def phC(self, val: bool):
        if isinstance(val, bool):
            self._phC = val
        else:
            raise ValueError(f'{val} is not a bool')

    @property
    def size(self) -> int:
        return self.__size

    @size.setter
    def size(self, size: int) -> None:
        self.__size = size
        self.__values: CxMat = np.zeros((size, size), dtype=complex)

    @property
    def values(self) -> CxMat:
        return self.__values

    @values.setter
    def values(self, value: CxMat):
        if isinstance(value, np.ndarray):
            if value.dtype == complex:
                self.__values = value
                self.__size = value.shape[0]
            else:
                raise ValueError("AdmittanceMatrix only supports complex values")
        else:
            raise ValueError("AdmittanceMatrix only supports complex numpy arrays")

    def to_dict(self) -> Dict[str, Union[str, float, bool]]:
        """
        Get a dictionary representation of the tap
        :return:
        """
        return {
            "size": self.__size,
            "values_r": self.__values.real.tolist(),
            "values_i": self.__values.imag.tolist(),
            "phase_n": self._phN,
            "phase_a": self._phA,
            "phase_b": self._phB,
            "phase_c": self._phC,
        }

    def parse(self, data: Dict[str, Union[str, float, bool]]) -> None:
        """
        Parse the tap data
        :param data: dictionary representation of the tap
        """

        self.size: int = data.get("size", 3)

        data_r = list_to_matrix(data.get("values_r", None), self.__size)
        data_i = list_to_matrix(data.get("values_i", None), self.__size)
        self.phN = bool(data.get("phase_n", False))
        self.phA = bool(data.get("phase_a", False))
        self.phB = bool(data.get("phase_b", False))
        self.phC = bool(data.get("phase_c", False))

        self.values = data_r + 1j * data_i

    def __eq__(self, other: "AdmittanceMatrix") -> bool:

        if self.size != other.size:
            return False

        if not np.allclose(self.values, other.values, atol=1e-10):
            return False

        return True
