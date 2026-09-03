# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import pandas as pd
from typing import Union, Dict
from VeraGridEngine.Utils.NumericalMethods.common import find_closest_number
from VeraGridEngine.enumerations import TapChangerTypes
from VeraGridEngine.basic_structures import Logger


class TapChanger:
    """
    Tap changer
    """
    __slots__ = (
        '_asymmetry_angle',
        '_total_positions',
        '_dV',
        '_neutral_position',
        '_normal_position',
        '_tap_position',
        '_tc_type',
        '_low_step',
        '_negative_low',
        '_ndv',
        '_tau_array',
        '_m_array',
        '_k_re_array',
        '_k_im_array',
        '_uses_explicit_table',
    )

    def __init__(self,
                 total_positions: int = 5,
                 neutral_position: int = 2,
                 normal_position: int = 2,
                 dV: float = 0.01,
                 asymmetry_angle: float = 90.0,
                 tc_type: TapChangerTypes = TapChangerTypes.NoRegulation) -> None:
        """
        Tap changer
        :param total_positions: Total number of positions
        :param neutral_position: Neutral position
        :param dV: per unit of voltage increment (p.u.)
        :param asymmetry_angle: Asymmetry angle (deg)
        :param tc_type: Tap changer type
        """
        neutral_position = int(neutral_position)
        total_positions = int(total_positions)
        if neutral_position >= total_positions:
            neutral_position = total_positions - 1
            print(f"Neutral position exceeding the total positions {neutral_position} >= {total_positions}")

        # asymmetry angle (Theta)
        self._asymmetry_angle = float(asymmetry_angle)

        # total number of positions
        self._total_positions = int(total_positions) if total_positions > 0 else 1

        # voltage increment in p.u.
        self._dV = float(dV)

        # neutral position
        self._neutral_position = int(neutral_position)

        # normal position
        self._normal_position = int(normal_position)

        # index with respect to the neutral position
        self._tap_position = int(neutral_position)

        # tap changer mode
        self._tc_type: TapChangerTypes = tc_type

        # original CGMES low step, when this tap changer comes from CGMES
        self._low_step = 0

        # for CGMES compatibility we store if the low step is negative
        self._negative_low = False

        # Calculated arrays
        self._ndv = np.zeros(self._total_positions)  # increment of voltage positions
        self._tau_array = np.zeros(self._total_positions)  # tap phase positions
        self._m_array = np.zeros(self._total_positions)  # tap module positions
        self._k_re_array = np.ones(self._total_positions)  # impedance correction positions (real)
        self._k_im_array = np.ones(self._total_positions)  # impedance correction positions (imag)
        self._uses_explicit_table: bool = False
        self.recalc()

    def copy(self) -> "TapChanger":
        """

        :return:
        """
        elm = TapChanger(
            total_positions=self._total_positions,
            neutral_position=self._neutral_position,
            normal_position=self._normal_position,
            dV=self._dV,
            asymmetry_angle=self._asymmetry_angle,
            tc_type=self._tc_type
        )
        elm._low_step = self._low_step
        elm._negative_low = self._negative_low
        elm._tap_position = self._tap_position
        elm._k_re_array = self._k_re_array.copy()
        elm._k_im_array = self._k_im_array.copy()
        table_was_copied: bool = elm.set_tap_module_phase_values(
            tap_modules=self._m_array,
            tap_phases=self._tau_array,
        )
        if table_was_copied:
            # ``set_tap_module_phase_values`` marks every accepted table as
            # explicit.  Restore the source semantic because a generic table
            # is copied through the same numerical API.
            elm._uses_explicit_table = self._uses_explicit_table
        else:
            elm.recalc()
        return elm

    @property
    def asymmetry_angle(self) -> float:
        return self._asymmetry_angle

    @asymmetry_angle.setter
    def asymmetry_angle(self, asymmetry_angle: float) -> None:
        self._asymmetry_angle = float(asymmetry_angle)
        self.recalc()

    @property
    def dV(self) -> float:
        return self._dV

    @dV.setter
    def dV(self, dV: float) -> None:
        self._dV = float(dV)
        self.recalc()

    @property
    def normal_position(self) -> int:
        return self._normal_position

    @normal_position.setter
    def normal_position(self, normal_position: int) -> None:
        self._normal_position = int(normal_position)
        self.recalc()

    @property
    def tc_type(self) -> TapChangerTypes:
        return self._tc_type

    @tc_type.setter
    def tc_type(self, tc_type: TapChangerTypes) -> None:
        self._tc_type = tc_type
        self.recalc()

    @property
    def total_positions(self) -> int:
        """
        Tap changer total number of positions
        :return: int
        """
        return self._total_positions

    @total_positions.setter
    def total_positions(self, value: int) -> None:
        """Set the number of discrete tap positions and resize the tables.

        :param value: Positive number of positions available to the tap changer.
        :return: None.
        """
        if isinstance(value, int):
            self._total_positions = value
            self.resize()
        else:
            raise TypeError(f'Expected int but got {type(value)}')

    @property
    def tap_position(self) -> int:
        """
        Get the tap position
        :return: int
        """
        return self._tap_position

    @tap_position.setter
    def tap_position(self, val: int) -> None:
        """
        Set the tap position (zero indexing)
        :param val: tap value
        """
        if val < self._total_positions:
            self._tap_position = int(val)
            self.recalc()
        else:
            print(f"Max tap changer value exceeded {val} > {self._total_positions}")

    @property
    def neutral_position(self) -> int:
        """
        Get the neutral position
        :return: int
        """
        return self._neutral_position

    @neutral_position.setter
    def neutral_position(self, val: int) -> None:
        """
        Set the neutral position
        :param val: neutral position value
        """
        self._neutral_position = int(val)
        self.recalc()

    @property
    def tap_modules_array(self):
        """
        Get the tap modules array
        :return:
        """
        return self._m_array

    @property
    def tap_angles_array(self):
        """

        :return:
        """
        return self._tau_array

    @property
    def uses_explicit_table(self) -> bool:
        """
        Return whether the tap table came from an explicit native definition.

        :return: ``True`` for imported or user-supplied tables that must retain
            their discrete entries exactly; ``False`` for arrays derived from
            the generic VeraGrid tap law.
        """
        return self._uses_explicit_table

    @property
    def impedance_correction_real_array(self) -> np.ndarray:
        """
        Get the real impedance correction factors per tap position.

        :return: Array of length ``total_positions``.
        """
        return self._k_re_array

    @property
    def impedance_correction_imag_array(self) -> np.ndarray:
        """
        Get the imaginary impedance correction factors per tap position.
        A value of 1.0 at every position means no correction (default).
        :return: array of length total_positions
        """
        return self._k_im_array

    def set_impedance_correction_values(
            self,
            correction_real: np.ndarray,
            correction_imag: np.ndarray,
    ) -> bool:
        """
        Install exact real and imaginary impedance factors by tap position.

        The stored branch impedance is the neutral reference.  Each factor is
        applied only when numerical data is compiled, which keeps the tap
        characteristic reusable after editing or serialisation.

        :param correction_real: Non-negative resistance factors.
        :param correction_imag: Non-negative reactance factors.
        :return: ``True`` when both complete arrays were accepted.
        """
        real_values: np.ndarray = np.asarray(correction_real, dtype=float)
        imag_values: np.ndarray = np.asarray(correction_imag, dtype=float)
        expected_shape: tuple[int, ...] = (self.total_positions,)
        shapes_are_valid: bool = (
            real_values.shape == expected_shape
            and imag_values.shape == expected_shape
        )
        values_are_valid: bool = bool(
            np.all(np.isfinite(real_values))
            and np.all(real_values >= 0.0)
            and np.all(np.isfinite(imag_values))
            and np.all(imag_values >= 0.0)
        )
        if shapes_are_valid and values_are_valid:
            self._k_re_array = real_values.copy()
            self._k_im_array = imag_values.copy()
            accepted: bool = True
        else:
            accepted = False
        return accepted

    def get_impedance_correction(self) -> tuple[float, float]:
        """
        Return the impedance factors at the current discrete position.

        :return: Resistance and reactance correction factors.
        """
        position: int = int(self.tap_position)
        position_is_valid: bool = (
            0 <= position < len(self._k_re_array)
            and 0 <= position < len(self._k_im_array)
        )
        if position_is_valid:
            correction_real: float = float(self._k_re_array[position])
            correction_imag: float = float(self._k_im_array[position])
        else:
            correction_real = 1.0
            correction_imag = 1.0
        return correction_real, correction_imag

    def resize(self) -> None:
        """
        Resize and recalc the tap positions array
        """
        self._ndv = np.zeros(self.total_positions)
        self._tau_array = np.zeros(self.total_positions)
        self._m_array = np.zeros(self.total_positions)
        # A resized tap window invalidates the positional correction contract;
        # reset it explicitly until an importer installs a matching table.
        self._k_re_array = np.ones(self.total_positions)
        self._k_im_array = np.ones(self.total_positions)
        self.recalc()

    def recalc(self) -> None:
        """
        Recalculate the phase and modules corresponding to each tap position
        """
        positions = np.arange(self.total_positions)
        self._ndv = (positions - self.neutral_position) * self.dV
        self._tau_array = self.get_tap_phase2(positions)
        self._m_array = self.get_tap_module2(positions)
        self._uses_explicit_table = False

    def set_tap_module_phase_values(
            self,
            tap_modules: np.ndarray,
            tap_phases: np.ndarray,
    ) -> bool:
        """
        Install one exact discrete complex-tap table.

        This table is required by importers whose native tap law contains a
        fixed vector-group shift, a winding-side reciprocal or another
        relationship that cannot be represented by the generic ``dV`` and
        asymmetry parameters alone.  Core tap-configuration setters still call
        :meth:`recalc`, intentionally returning the object to its generic law.

        :param tap_modules: Positive tap magnitudes by zero-based position.
        :param tap_phases: Unwrapped tap phases in radians by position.
        :return: ``True`` when the complete table was accepted.
        """
        module_values: np.ndarray = np.asarray(tap_modules, dtype=float)
        phase_values: np.ndarray = np.asarray(tap_phases, dtype=float)
        expected_shape: tuple[int, ...] = (self.total_positions,)
        shapes_are_valid: bool = (
            module_values.shape == expected_shape
            and phase_values.shape == expected_shape
        )
        values_are_valid: bool = bool(
            np.all(np.isfinite(module_values))
            and np.all(module_values > 0.0)
            and np.all(np.isfinite(phase_values))
        )
        if shapes_are_valid and values_are_valid:
            self._m_array = module_values.copy()
            self._tau_array = phase_values.copy()
            self._uses_explicit_table = True
            result: bool = True
        else:
            result = False
        return result

    def to_dict(self) -> Dict[str, object]:
        """
        Get a dictionary representation of the tap
        :return:
        """
        tap_data: Dict[str, object] = dict()
        tap_data["asymmetry_angle"] = self.asymmetry_angle
        tap_data["total_positions"] = self.total_positions
        tap_data["dV"] = self.dV
        tap_data["neutral_position"] = self.neutral_position
        tap_data["normal_position"] = self.normal_position
        tap_data["tap_position"] = self._tap_position
        tap_data["type"] = str(self.tc_type)
        tap_data["low_step"] = self._low_step
        tap_data["negative_low"] = self._negative_low
        tap_data["tap_module_table"] = self._m_array.tolist()
        tap_data["tap_phase_table"] = self._tau_array.tolist()
        tap_data["uses_explicit_table"] = self._uses_explicit_table
        tap_data["impedance_correction_real"] = self._k_re_array.tolist()
        tap_data["impedance_correction_imag"] = self._k_im_array.tolist()
        return tap_data

    def parse(self, data: Dict[str, Union[str, float]], logger: Logger = Logger()) -> None:
        """
        Parse the tap data
        :param data: dictionary representation of the tap
        :param logger: logger instance
        """
        self.asymmetry_angle = data.get("asymmetry_angle", 90.0)
        self.total_positions = data.get("total_positions", 5)
        self.dV = data.get("dV", 0.01)
        self.neutral_position = data.get("neutral_position", 2)
        self.normal_position = data.get("normal_position", 2)
        self.tap_position = data.get("tap_position", 2)
        self.tc_type = TapChangerTypes(data.get("type", TapChangerTypes.NoRegulation.value))
        low_step = data.get("low_step", None)
        if low_step is None:
            negative_low = data.get("negative_low", False)
            self._low_step = 1 - self.neutral_position if negative_low else 0
        else:
            self._low_step = int(low_step)
        self._negative_low = self._low_step < 0

        # parse the impedance correction factors

        _k_re_array = data.get("impedance_correction_real", None)
        if _k_re_array is not None:
            if len(_k_re_array) == self.total_positions:
                self._k_re_array = np.array(_k_re_array)
            else:
                self._k_re_array = np.ones(self._total_positions)
                logger.add_warning("Incorrect impedance table length")

        _k_im_array = data.get("impedance_correction_imag", None)
        if _k_im_array is not None:
            if len(_k_im_array) == self.total_positions:
                self._k_im_array = np.array(_k_im_array)
            else:
                self._k_im_array = np.ones(self._total_positions)
                logger.add_warning("Incorrect impedance table length")

        self.recalc()

        # New files preserve exact native tap tables.  Older files omit these
        # keys and continue to use the generic VeraGrid tap law above.
        tap_module_table_obj: object | None = data.get("tap_module_table", None)
        tap_phase_table_obj: object | None = data.get("tap_phase_table", None)
        if isinstance(tap_module_table_obj, list) and isinstance(tap_phase_table_obj, list):
            try:
                tap_module_table: np.ndarray = np.asarray(tap_module_table_obj, dtype=float)
                tap_phase_table: np.ndarray = np.asarray(tap_phase_table_obj, dtype=float)
            except (TypeError, ValueError):
                exact_table_was_loaded: bool = False
            else:
                exact_table_was_loaded = self.set_tap_module_phase_values(
                    tap_modules=tap_module_table,
                    tap_phases=tap_phase_table,
                )
            if exact_table_was_loaded:
                explicit_table_object: object | None = data.get(
                    "uses_explicit_table",
                    None,
                )
                if isinstance(explicit_table_object, bool):
                    self._uses_explicit_table = explicit_table_object
                else:
                    # Legacy files persisted generated tables before recording
                    # their provenance.  Treat them as generic unless their
                    # values differ from the current generic tap law.
                    generic_modules: np.ndarray = self.get_tap_module2(
                        np.arange(self.total_positions)
                    )
                    generic_phases: np.ndarray = self.get_tap_phase2(
                        np.arange(self.total_positions)
                    )
                    self._uses_explicit_table = bool(
                        not np.allclose(
                            tap_module_table,
                            generic_modules,
                            atol=1.0e-12,
                            rtol=0.0,
                        )
                        or not np.allclose(
                            tap_phase_table,
                            generic_phases,
                            atol=1.0e-12,
                            rtol=0.0,
                        )
                    )
            else:
                logger.add_warning("Incorrect exact tap table")
        else:
            pass

    def to_df(self) -> pd.DataFrame:
        """
        Get DaraFrame of the values
        :return: DataFrame
        """
        return pd.DataFrame(data={
            'Steps': self._ndv,
            'tau': self._tau_array,
            'm': self._m_array,
            'impedance_correction_real': self._k_re_array,
            'impedance_correction_imag': self._k_im_array,
        })

    def reset(self) -> None:
        """
        Resets the tap changer to the neutral position
        """
        self.tap_position = self.neutral_position

    def tap_up(self) -> None:
        """
        Go to the next upper tap position
        """
        if self.tap_position + 1 < len(self._ndv):
            self.tap_position += 1

    def tap_down(self) -> None:
        """
        Go to the next upper tap position
        """
        if self.tap_position - 1 > 0:
            self.tap_position -= 1

    def get_tap_phase2(self, tap_position: Union[int, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Get the tap phase in radians
        :return: phase in radians (single value or array)
        """
        if self.tc_type == TapChangerTypes.NoRegulation:
            if isinstance(tap_position, int):
                return 0.0
            elif isinstance(tap_position, np.ndarray):
                return np.zeros(len(tap_position))
            else:
                raise ValueError("tap position must be int or np.ndarray of int type")

        elif self.tc_type == TapChangerTypes.VoltageRegulation:
            if isinstance(tap_position, int):
                return 0.0
            elif isinstance(tap_position, np.ndarray):
                return np.zeros(len(tap_position))
            else:
                raise ValueError("tap position must be int or np.ndarray of int type")

        elif self.tc_type == TapChangerTypes.Asymmetrical:
            ndu = self._ndv[tap_position]
            theta = np.deg2rad(self.asymmetry_angle)
            a = ndu * np.sin(theta)
            b = ndu * np.cos(theta)
            alpha = np.arctan(a / (1.0 + b))
            return alpha

        elif self.tc_type == TapChangerTypes.Symmetrical:
            ndu = self._ndv[tap_position]
            alpha = 2.0 * np.arctan(ndu / 2.0)
            return alpha

        else:
            raise Exception("Unknown tap phase type")

    def get_tap_module2(self, tap_position: Union[int, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Get the tap voltage regulation module
        :return: voltage regulation module (single value or array)
        """

        if self.tc_type == TapChangerTypes.NoRegulation:
            if isinstance(tap_position, int):
                return 1.0
            elif isinstance(tap_position, np.ndarray):
                return np.ones(len(tap_position))
            else:
                raise ValueError("tap position must be int or np.ndarray of int type")

        elif self.tc_type == TapChangerTypes.VoltageRegulation:
            ndu = self._ndv[tap_position]
            return 1.0 / (1.0 - ndu + 1e-20)

        elif self.tc_type == TapChangerTypes.Asymmetrical:
            ndu = self._ndv[tap_position]
            theta = np.deg2rad(self.asymmetry_angle)
            a = ndu * np.sin(theta)
            b = ndu * np.cos(theta)
            rho = 1.0 / np.sqrt(np.power(a, 2) + np.power(1.0 + b, 2))
            return rho

        elif self.tc_type == TapChangerTypes.Symmetrical:
            if isinstance(tap_position, int):
                return 1.0
            elif isinstance(tap_position, np.ndarray):
                return np.ones(len(tap_position))
            else:
                raise ValueError("tap position must be int or np.ndarray of int type")
        else:
            raise Exception("Unknown tap phase type")

    def get_tap_phase(self) -> float:
        """
        Get the tap phase in radians
        :return: phase in radians
        """
        if self.tap_position < len(self._tau_array):
            return float(self._tau_array[self.tap_position])
        else:
            print("tap position out of range")
            return 0.0

    def get_tap_module(self) -> float:
        """
        Get the tap voltage regulation module
        :return: voltage regulation module
        """
        if self.tap_position < len(self._m_array):
            return float(self._m_array[self.tap_position])
        else:
            print("tap position out of range")
            return 1.0

    def get_tap_module_at(self, tap_position: int) -> float:
        """Return the exact stored module at one discrete position.

        Importers may install a native explicit tap table whose direction is
        not represented by the generic positive ``dV`` parameter.  Station
        controls therefore need read-only positional access to that table.

        :param tap_position: Zero-based discrete position.
        :return: Exact tap module, or ``nan`` for an invalid position.
        """
        position_is_valid: bool = bool(
            0 <= tap_position < len(self._m_array)
        )
        if position_is_valid:
            tap_module: float = float(self._m_array[tap_position])
        else:
            tap_module = 1.0
        return tap_module

    def set_tap_module(self, tap_module: float) -> float:
        """
        Set the tap position closest to the tap module
        :param tap_module: float value of the tap module
        """
        if self.tc_type != TapChangerTypes.NoRegulation:
            pos, val = find_closest_number(arr=self._m_array, target=tap_module)
            self.tap_position = pos
            return val
        else:
            return 1.0

    def set_tap_phase(self, tap_phase: float) -> float:
        """
        Set the tap position closest to the tap phase
        :param tap_phase: float value of the tap phase
        """
        if self.tc_type != TapChangerTypes.NoRegulation:
            pos, val = find_closest_number(arr=self._tau_array, target=tap_phase)
            self.tap_position = pos
            return val
        else:
            return 0.0

    def get_tap_module_min(self) -> float:
        """
        Min tap module, computed on the fly
        :return: float
        """
        return float(np.min(self._m_array))

    def get_tap_module_max(self) -> float:
        """
        Max tap module, computed on the fly
        :return: float
        """
        return float(np.max(self._m_array))

    def get_tap_phase_min(self) -> float:
        """
        Min tap phase, computed on the fly
        :return: float
        """
        return float(np.min(self._tau_array))

    def get_tap_phase_max(self) -> float:
        """
        Maximum tap phase (calculated)
        :return: float
        """
        return float(np.max(self._tau_array))

    def __eq__(self, other: "TapChanger") -> bool:
        """
        Equality check
        :param other: TapChanger
        :return: ok?
        """
        return ((self.asymmetry_angle == other.asymmetry_angle)
                and (self.total_positions == other.total_positions)
                and np.allclose(self.dV, other.dV, atol=1e-06)
                and (self.neutral_position == other.neutral_position)
                and (self.normal_position == other.normal_position)
                and (self.tap_position == other.tap_position)
                and (self.tc_type == other.tc_type))

    def __str__(self) -> str:
        """
        String representation
        :return:
        """
        return "Tap changer"

    def init_from_cgmes(self,
                        low: int,
                        high: int,
                        normal: int,
                        neutral: int,
                        stepVoltageIncrement: float,
                        step: int,
                        asymmetry_angle: float = 0.0,
                        tc_type: TapChangerTypes = TapChangerTypes.NoRegulation) -> None:
        """
        Import TapChanger object from CGMES

        :param low:
        :param high:
        :param normal:
        :param neutral:
        :param stepVoltageIncrement:
        :param step:
        :param asymmetry_angle:
        :param tc_type:
        :return:
        """

        self._low_step = int(low)
        self._negative_low = self._low_step < 0

        self.asymmetry_angle = float(asymmetry_angle)  # asymmetry angle (Theta)
        self._total_positions = int(high - low + 1)  # total number of positions
        self.dV = float(stepVoltageIncrement / 100)  # voltage increment in p.u.
        self.neutral_position = int(neutral - low)  # zero-based neutral position
        self.normal_position = int(normal - low)  # zero-based normal position
        self._tap_position = int(step - low)  # zero-based tap position
        self.tc_type = tc_type  # tap changer mode

        # Calculated arrays
        self._ndv = np.zeros(self._total_positions)
        self._tau_array = np.zeros(self._total_positions)
        self._m_array = np.zeros(self._total_positions)
        self._k_re_array = np.ones(self._total_positions)  # impedance correction positions (real)
        self._k_im_array = np.ones(self._total_positions)  # impedance correction positions (imag)
        self.recalc()

    def get_cgmes_values(self):
        """
        Returns with values of a Tap Changer in CGMES
        
        :return: 
        :rtype: 
        """

        low = self._low_step
        high = low + self.total_positions - 1
        normal = self.normal_position + low
        neutral = self.neutral_position + low
        sVI = round(self.dV * 100, 6)
        step = self.tap_position + low

        return low, high, normal, neutral, sVI, step
