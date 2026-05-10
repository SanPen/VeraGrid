# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Tuple

from VeraGridEngine.Devices.Parents.editable_device import GCProp
from VeraGridEngine.Simulations.options_template import OptionsTemplate


class JMartiFitOptions(OptionsTemplate):
    """
    User-configurable numerical options for the JMARTI fitting workflow.

    The fitting stages must remain externally configurable because real line data
    sets vary strongly in frequency span, modal coupling, and required rational
    order. The object centralizes all public knobs used by the current offline
    preprocessing stages.
    """

    __slots__ = (
        '_reference_frequency_hz',
        '_use_frequency_exploration_window',
        '_exploration_low_hz',
        '_exploration_high_hz',
        '_use_delay_fit_window',
        '_delay_fit_low_hz',
        '_delay_fit_high_hz',
        '_decoupling_warning_tolerance',
        '_loewner_relative_tolerance',
        '_maximum_model_order',
        '_forced_model_order',
        '_minimum_frequency_samples',
        '_vf_max_iterations',
        '_vf_pole_shift_tolerance',
        '_vf_enforce_stable_poles',
        '_vf_stability_real_part_floor',
        '_vf_include_constant_term',
        '_vf_include_proportional_term',
        '_passivity_frequency_sample_count',
        '_passivity_minimum_real_yc_tolerance',
        '_passivity_maximum_hres_gain_tolerance',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(key='reference_frequency_hz', tpe=float),
        GCProp(key='use_frequency_exploration_window', tpe=bool),
        GCProp(key='exploration_low_hz', tpe=float),
        GCProp(key='exploration_high_hz', tpe=float),
        GCProp(key='use_delay_fit_window', tpe=bool),
        GCProp(key='delay_fit_low_hz', tpe=float),
        GCProp(key='delay_fit_high_hz', tpe=float),
        GCProp(key='decoupling_warning_tolerance', tpe=float),
        GCProp(key='loewner_relative_tolerance', tpe=float),
        GCProp(key='maximum_model_order', tpe=int),
        GCProp(key='forced_model_order', tpe=int),
        GCProp(key='minimum_frequency_samples', tpe=int),
        GCProp(key='vf_max_iterations', tpe=int),
        GCProp(key='vf_pole_shift_tolerance', tpe=float),
        GCProp(key='vf_enforce_stable_poles', tpe=bool),
        GCProp(key='vf_stability_real_part_floor', tpe=float),
        GCProp(key='vf_include_constant_term', tpe=bool),
        GCProp(key='vf_include_proportional_term', tpe=bool),
        GCProp(key='passivity_frequency_sample_count', tpe=int),
        GCProp(key='passivity_minimum_real_yc_tolerance', tpe=float),
        GCProp(key='passivity_maximum_hres_gain_tolerance', tpe=float),
    )

    def __init__(self,
                 reference_frequency_hz: float = 0.0,
                 use_frequency_exploration_window: bool = False,
                 exploration_low_hz: float = 0.0,
                 exploration_high_hz: float = 0.0,
                 use_delay_fit_window: bool = False,
                 delay_fit_low_hz: float = 0.0,
                 delay_fit_high_hz: float = 0.0,
                 decoupling_warning_tolerance: float = 1.0e-2,
                 loewner_relative_tolerance: float = 1.0e-8,
                 maximum_model_order: int = 40,
                 forced_model_order: int = 0,
                 minimum_frequency_samples: int = 4,
                 vf_max_iterations: int = 8,
                 vf_pole_shift_tolerance: float = 1.0e-6,
                 vf_enforce_stable_poles: bool = True,
                 vf_stability_real_part_floor: float = 1.0e-8,
                 vf_include_constant_term: bool = True,
                 vf_include_proportional_term: bool = False,
                 passivity_frequency_sample_count: int = 1024,
                 passivity_minimum_real_yc_tolerance: float = 1.0e-8,
                 passivity_maximum_hres_gain_tolerance: float = 1.0e-6) -> None:
        """
        Initialize the JMARTI fitting options.

        :param reference_frequency_hz: Reference frequency used to freeze the modal basis. ``0.0`` means automatic.
        :param use_frequency_exploration_window: Whether to restrict the fitting band.
        :param exploration_low_hz: Lower edge of the fitting band in Hz.
        :param exploration_high_hz: Upper edge of the fitting band in Hz.
        :param use_delay_fit_window: Whether to restrict the delay-fit band.
        :param delay_fit_low_hz: Lower delay-fit frequency in Hz.
        :param delay_fit_high_hz: Upper delay-fit frequency in Hz.
        :param decoupling_warning_tolerance: Maximum acceptable modal off-diagonal error before warning/failing higher layers.
        :param loewner_relative_tolerance: Relative singular-value tolerance for order estimation.
        :param maximum_model_order: Upper cap for the reduced rational order.
        :param forced_model_order: Fixed order. ``0`` means automatic order estimation.
        :param minimum_frequency_samples: Minimum number of frequency samples required by the fitting stages.
        :param vf_max_iterations: Maximum number of pole-relocation iterations in Vector Fitting.
        :param vf_pole_shift_tolerance: Relative pole-shift stopping tolerance.
        :param vf_enforce_stable_poles: Whether unstable poles are reflected into the left half-plane.
        :param vf_stability_real_part_floor: Minimum magnitude imposed on reflected negative real parts.
        :param vf_include_constant_term: Whether the rational fit includes one constant term.
        :param vf_include_proportional_term: Whether the rational fit includes one proportional ``s`` term.
        :param passivity_frequency_sample_count: Number of dense frequency samples used for passivity checks.
        :param passivity_minimum_real_yc_tolerance: Maximum allowed negativity margin for ``Re(Yc(jw))``.
        :param passivity_maximum_hres_gain_tolerance: Maximum allowed gain slack above unity for ``|Hres(jw)|``.
        :return: None.
        """
        OptionsTemplate.__init__(self, name='JMartiFitOptions')

        self._reference_frequency_hz: float = 0.0
        self._use_frequency_exploration_window: bool = False
        self._exploration_low_hz: float = 0.0
        self._exploration_high_hz: float = 0.0
        self._use_delay_fit_window: bool = False
        self._delay_fit_low_hz: float = 0.0
        self._delay_fit_high_hz: float = 0.0
        self._decoupling_warning_tolerance: float = 1.0e-2
        self._loewner_relative_tolerance: float = 1.0e-8
        self._maximum_model_order: int = 40
        self._forced_model_order: int = 0
        self._minimum_frequency_samples: int = 4
        self._vf_max_iterations: int = 8
        self._vf_pole_shift_tolerance: float = 1.0e-6
        self._vf_enforce_stable_poles: bool = True
        self._vf_stability_real_part_floor: float = 1.0e-8
        self._vf_include_constant_term: bool = True
        self._vf_include_proportional_term: bool = False
        self._passivity_frequency_sample_count: int = 1024
        self._passivity_minimum_real_yc_tolerance: float = 1.0e-8
        self._passivity_maximum_hres_gain_tolerance: float = 1.0e-6

        self.set_reference_frequency_hz(reference_frequency_hz)
        self.set_use_frequency_exploration_window(use_frequency_exploration_window)
        self.set_exploration_low_hz(exploration_low_hz)
        self.set_exploration_high_hz(exploration_high_hz)
        self.set_use_delay_fit_window(use_delay_fit_window)
        self.set_delay_fit_low_hz(delay_fit_low_hz)
        self.set_delay_fit_high_hz(delay_fit_high_hz)
        self.set_decoupling_warning_tolerance(decoupling_warning_tolerance)
        self.set_loewner_relative_tolerance(loewner_relative_tolerance)
        self.set_maximum_model_order(maximum_model_order)
        self.set_forced_model_order(forced_model_order)
        self.set_minimum_frequency_samples(minimum_frequency_samples)
        self.set_vf_max_iterations(vf_max_iterations)
        self.set_vf_pole_shift_tolerance(vf_pole_shift_tolerance)
        self.set_vf_enforce_stable_poles(vf_enforce_stable_poles)
        self.set_vf_stability_real_part_floor(vf_stability_real_part_floor)
        self.set_vf_include_constant_term(vf_include_constant_term)
        self.set_vf_include_proportional_term(vf_include_proportional_term)
        self.set_passivity_frequency_sample_count(passivity_frequency_sample_count)
        self.set_passivity_minimum_real_yc_tolerance(passivity_minimum_real_yc_tolerance)
        self.set_passivity_maximum_hres_gain_tolerance(passivity_maximum_hres_gain_tolerance)

    def get_reference_frequency_hz(self) -> float:
        """
        Return the reference frequency used to freeze the modal basis.

        :return: Reference frequency in Hz. ``0.0`` means automatic.
        """
        return self._reference_frequency_hz

    def set_reference_frequency_hz(self, value: float) -> None:
        """
        Set the reference frequency used to freeze the modal basis.

        :param value: Requested reference frequency in Hz.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._reference_frequency_hz = sanitized_value
        else:
            self._reference_frequency_hz = 0.0

    @property
    def reference_frequency_hz(self) -> float:
        """
        Property wrapper for the reference frequency.

        :return: Reference frequency in Hz.
        """
        return self.get_reference_frequency_hz()

    @reference_frequency_hz.setter
    def reference_frequency_hz(self, value: float) -> None:
        """
        Property wrapper for the reference frequency.

        :param value: Requested reference frequency in Hz.
        :return: None.
        """
        self.set_reference_frequency_hz(value)

    def get_use_frequency_exploration_window(self) -> bool:
        """
        Return whether the fitting band restriction is enabled.

        :return: Boolean state.
        """
        return self._use_frequency_exploration_window

    def set_use_frequency_exploration_window(self, value: bool) -> None:
        """
        Enable or disable the fitting band restriction.

        :param value: Requested boolean state.
        :return: None.
        """
        self._use_frequency_exploration_window = bool(value)

    @property
    def use_frequency_exploration_window(self) -> bool:
        """
        Property wrapper for the fitting band restriction flag.

        :return: Boolean state.
        """
        return self.get_use_frequency_exploration_window()

    @use_frequency_exploration_window.setter
    def use_frequency_exploration_window(self, value: bool) -> None:
        """
        Property wrapper for the fitting band restriction flag.

        :param value: Requested boolean state.
        :return: None.
        """
        self.set_use_frequency_exploration_window(value)

    def get_exploration_low_hz(self) -> float:
        """
        Return the lower edge of the fitting band.

        :return: Lower edge in Hz.
        """
        return self._exploration_low_hz

    def set_exploration_low_hz(self, value: float) -> None:
        """
        Set the lower edge of the fitting band.

        :param value: Requested lower edge in Hz.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._exploration_low_hz = sanitized_value
        else:
            self._exploration_low_hz = 0.0

    @property
    def exploration_low_hz(self) -> float:
        """
        Property wrapper for the lower fitting-band edge.

        :return: Lower edge in Hz.
        """
        return self.get_exploration_low_hz()

    @exploration_low_hz.setter
    def exploration_low_hz(self, value: float) -> None:
        """
        Property wrapper for the lower fitting-band edge.

        :param value: Requested lower edge in Hz.
        :return: None.
        """
        self.set_exploration_low_hz(value)

    def get_exploration_high_hz(self) -> float:
        """
        Return the upper edge of the fitting band.

        :return: Upper edge in Hz.
        """
        return self._exploration_high_hz

    def set_exploration_high_hz(self, value: float) -> None:
        """
        Set the upper edge of the fitting band.

        :param value: Requested upper edge in Hz.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._exploration_high_hz = sanitized_value
        else:
            self._exploration_high_hz = 0.0

    @property
    def exploration_high_hz(self) -> float:
        """
        Property wrapper for the upper fitting-band edge.

        :return: Upper edge in Hz.
        """
        return self.get_exploration_high_hz()

    @exploration_high_hz.setter
    def exploration_high_hz(self, value: float) -> None:
        """
        Property wrapper for the upper fitting-band edge.

        :param value: Requested upper edge in Hz.
        :return: None.
        """
        self.set_exploration_high_hz(value)

    def get_use_delay_fit_window(self) -> bool:
        """
        Return whether the delay-fit band restriction is enabled.

        :return: Boolean state.
        """
        return self._use_delay_fit_window

    def set_use_delay_fit_window(self, value: bool) -> None:
        """
        Enable or disable the delay-fit band restriction.

        :param value: Requested boolean state.
        :return: None.
        """
        self._use_delay_fit_window = bool(value)

    @property
    def use_delay_fit_window(self) -> bool:
        """
        Property wrapper for the delay-fit band restriction flag.

        :return: Boolean state.
        """
        return self.get_use_delay_fit_window()

    @use_delay_fit_window.setter
    def use_delay_fit_window(self, value: bool) -> None:
        """
        Property wrapper for the delay-fit band restriction flag.

        :param value: Requested boolean state.
        :return: None.
        """
        self.set_use_delay_fit_window(value)

    def get_delay_fit_low_hz(self) -> float:
        """
        Return the lower edge of the delay-fit band.

        :return: Lower edge in Hz.
        """
        return self._delay_fit_low_hz

    def set_delay_fit_low_hz(self, value: float) -> None:
        """
        Set the lower edge of the delay-fit band.

        :param value: Requested lower edge in Hz.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._delay_fit_low_hz = sanitized_value
        else:
            self._delay_fit_low_hz = 0.0

    @property
    def delay_fit_low_hz(self) -> float:
        """
        Property wrapper for the lower delay-fit edge.

        :return: Lower edge in Hz.
        """
        return self.get_delay_fit_low_hz()

    @delay_fit_low_hz.setter
    def delay_fit_low_hz(self, value: float) -> None:
        """
        Property wrapper for the lower delay-fit edge.

        :param value: Requested lower edge in Hz.
        :return: None.
        """
        self.set_delay_fit_low_hz(value)

    def get_delay_fit_high_hz(self) -> float:
        """
        Return the upper edge of the delay-fit band.

        :return: Upper edge in Hz.
        """
        return self._delay_fit_high_hz

    def set_delay_fit_high_hz(self, value: float) -> None:
        """
        Set the upper edge of the delay-fit band.

        :param value: Requested upper edge in Hz.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._delay_fit_high_hz = sanitized_value
        else:
            self._delay_fit_high_hz = 0.0

    @property
    def delay_fit_high_hz(self) -> float:
        """
        Property wrapper for the upper delay-fit edge.

        :return: Upper edge in Hz.
        """
        return self.get_delay_fit_high_hz()

    @delay_fit_high_hz.setter
    def delay_fit_high_hz(self, value: float) -> None:
        """
        Property wrapper for the upper delay-fit edge.

        :param value: Requested upper edge in Hz.
        :return: None.
        """
        self.set_delay_fit_high_hz(value)

    def get_decoupling_warning_tolerance(self) -> float:
        """
        Return the maximum acceptable modal decoupling error.

        :return: Non-negative error tolerance.
        """
        return self._decoupling_warning_tolerance

    def set_decoupling_warning_tolerance(self, value: float) -> None:
        """
        Set the maximum acceptable modal decoupling error.

        :param value: Requested non-negative tolerance.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._decoupling_warning_tolerance = sanitized_value
        else:
            self._decoupling_warning_tolerance = 0.0

    @property
    def decoupling_warning_tolerance(self) -> float:
        """
        Property wrapper for the modal decoupling tolerance.

        :return: Non-negative error tolerance.
        """
        return self.get_decoupling_warning_tolerance()

    @decoupling_warning_tolerance.setter
    def decoupling_warning_tolerance(self, value: float) -> None:
        """
        Property wrapper for the modal decoupling tolerance.

        :param value: Requested non-negative tolerance.
        :return: None.
        """
        self.set_decoupling_warning_tolerance(value)

    def get_loewner_relative_tolerance(self) -> float:
        """
        Return the relative Loewner singular-value tolerance.

        :return: Positive relative tolerance.
        """
        return self._loewner_relative_tolerance

    def set_loewner_relative_tolerance(self, value: float) -> None:
        """
        Set the relative Loewner singular-value tolerance.

        :param value: Requested positive tolerance.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value > 0.0:
            self._loewner_relative_tolerance = sanitized_value
        else:
            self._loewner_relative_tolerance = 1.0e-8

    @property
    def loewner_relative_tolerance(self) -> float:
        """
        Property wrapper for the Loewner singular-value tolerance.

        :return: Positive relative tolerance.
        """
        return self.get_loewner_relative_tolerance()

    @loewner_relative_tolerance.setter
    def loewner_relative_tolerance(self, value: float) -> None:
        """
        Property wrapper for the Loewner singular-value tolerance.

        :param value: Requested positive tolerance.
        :return: None.
        """
        self.set_loewner_relative_tolerance(value)

    def get_maximum_model_order(self) -> int:
        """
        Return the maximum rational order allowed by the user.

        :return: Positive order cap.
        """
        return self._maximum_model_order

    def set_maximum_model_order(self, value: int) -> None:
        """
        Set the maximum rational order allowed by the user.

        :param value: Requested positive order cap.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 1:
            self._maximum_model_order = sanitized_value
        else:
            self._maximum_model_order = 1

    @property
    def maximum_model_order(self) -> int:
        """
        Property wrapper for the maximum model order.

        :return: Positive order cap.
        """
        return self.get_maximum_model_order()

    @maximum_model_order.setter
    def maximum_model_order(self, value: int) -> None:
        """
        Property wrapper for the maximum model order.

        :param value: Requested positive order cap.
        :return: None.
        """
        self.set_maximum_model_order(value)

    def get_forced_model_order(self) -> int:
        """
        Return the user-forced rational order.

        :return: Forced order, or ``0`` when order estimation remains automatic.
        """
        return self._forced_model_order

    def set_forced_model_order(self, value: int) -> None:
        """
        Set the user-forced rational order.

        :param value: Requested order. ``0`` keeps automatic order estimation.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 0:
            self._forced_model_order = sanitized_value
        else:
            self._forced_model_order = 0

    @property
    def forced_model_order(self) -> int:
        """
        Property wrapper for the forced model order.

        :return: Forced order, or ``0`` when automatic.
        """
        return self.get_forced_model_order()

    @forced_model_order.setter
    def forced_model_order(self, value: int) -> None:
        """
        Property wrapper for the forced model order.

        :param value: Requested order. ``0`` keeps automatic order estimation.
        :return: None.
        """
        self.set_forced_model_order(value)

    def get_minimum_frequency_samples(self) -> int:
        """
        Return the minimum number of frequency samples required.

        :return: Minimum sample count.
        """
        return self._minimum_frequency_samples

    def set_minimum_frequency_samples(self, value: int) -> None:
        """
        Set the minimum number of frequency samples required.

        :param value: Requested minimum sample count.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 4:
            self._minimum_frequency_samples = sanitized_value
        else:
            self._minimum_frequency_samples = 4

    @property
    def minimum_frequency_samples(self) -> int:
        """
        Property wrapper for the minimum sample count.

        :return: Minimum sample count.
        """
        return self.get_minimum_frequency_samples()

    @minimum_frequency_samples.setter
    def minimum_frequency_samples(self, value: int) -> None:
        """
        Property wrapper for the minimum sample count.

        :param value: Requested minimum sample count.
        :return: None.
        """
        self.set_minimum_frequency_samples(value)

    def get_vf_max_iterations(self) -> int:
        """
        Return the maximum number of Vector Fitting relocation iterations.

        :return: Positive iteration cap.
        """
        return self._vf_max_iterations

    def set_vf_max_iterations(self, value: int) -> None:
        """
        Set the maximum number of Vector Fitting relocation iterations.

        :param value: Requested positive iteration cap.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 1:
            self._vf_max_iterations = sanitized_value
        else:
            self._vf_max_iterations = 1

    @property
    def vf_max_iterations(self) -> int:
        """
        Property wrapper for the Vector Fitting iteration cap.

        :return: Positive iteration cap.
        """
        return self.get_vf_max_iterations()

    @vf_max_iterations.setter
    def vf_max_iterations(self, value: int) -> None:
        """
        Property wrapper for the Vector Fitting iteration cap.

        :param value: Requested positive iteration cap.
        :return: None.
        """
        self.set_vf_max_iterations(value)

    def get_vf_pole_shift_tolerance(self) -> float:
        """
        Return the Vector Fitting pole-shift stopping tolerance.

        :return: Positive relative tolerance.
        """
        return self._vf_pole_shift_tolerance

    def set_vf_pole_shift_tolerance(self, value: float) -> None:
        """
        Set the Vector Fitting pole-shift stopping tolerance.

        :param value: Requested positive relative tolerance.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value > 0.0:
            self._vf_pole_shift_tolerance = sanitized_value
        else:
            self._vf_pole_shift_tolerance = 1.0e-6

    @property
    def vf_pole_shift_tolerance(self) -> float:
        """
        Property wrapper for the Vector Fitting pole-shift tolerance.

        :return: Positive relative tolerance.
        """
        return self.get_vf_pole_shift_tolerance()

    @vf_pole_shift_tolerance.setter
    def vf_pole_shift_tolerance(self, value: float) -> None:
        """
        Property wrapper for the Vector Fitting pole-shift tolerance.

        :param value: Requested positive relative tolerance.
        :return: None.
        """
        self.set_vf_pole_shift_tolerance(value)

    def get_vf_enforce_stable_poles(self) -> bool:
        """
        Return whether unstable poles must be reflected into the left half-plane.

        :return: Boolean state.
        """
        return self._vf_enforce_stable_poles

    def set_vf_enforce_stable_poles(self, value: bool) -> None:
        """
        Enable or disable pole reflection into the left half-plane.

        :param value: Requested boolean state.
        :return: None.
        """
        self._vf_enforce_stable_poles = bool(value)

    @property
    def vf_enforce_stable_poles(self) -> bool:
        """
        Property wrapper for the stable-pole enforcement flag.

        :return: Boolean state.
        """
        return self.get_vf_enforce_stable_poles()

    @vf_enforce_stable_poles.setter
    def vf_enforce_stable_poles(self, value: bool) -> None:
        """
        Property wrapper for the stable-pole enforcement flag.

        :param value: Requested boolean state.
        :return: None.
        """
        self.set_vf_enforce_stable_poles(value)

    def get_vf_stability_real_part_floor(self) -> float:
        """
        Return the minimum absolute negative real part used after pole reflection.

        :return: Positive floor value.
        """
        return self._vf_stability_real_part_floor

    def set_vf_stability_real_part_floor(self, value: float) -> None:
        """
        Set the minimum absolute negative real part used after pole reflection.

        :param value: Requested positive floor value.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value > 0.0:
            self._vf_stability_real_part_floor = sanitized_value
        else:
            self._vf_stability_real_part_floor = 1.0e-8

    @property
    def vf_stability_real_part_floor(self) -> float:
        """
        Property wrapper for the reflected-pole real-part floor.

        :return: Positive floor value.
        """
        return self.get_vf_stability_real_part_floor()

    @vf_stability_real_part_floor.setter
    def vf_stability_real_part_floor(self, value: float) -> None:
        """
        Property wrapper for the reflected-pole real-part floor.

        :param value: Requested positive floor value.
        :return: None.
        """
        self.set_vf_stability_real_part_floor(value)

    def get_vf_include_constant_term(self) -> bool:
        """
        Return whether the rational fit includes one constant term.

        :return: Boolean state.
        """
        return self._vf_include_constant_term

    def set_vf_include_constant_term(self, value: bool) -> None:
        """
        Enable or disable the constant term in the rational fit.

        :param value: Requested boolean state.
        :return: None.
        """
        self._vf_include_constant_term = bool(value)

    @property
    def vf_include_constant_term(self) -> bool:
        """
        Property wrapper for the constant-term flag.

        :return: Boolean state.
        """
        return self.get_vf_include_constant_term()

    @vf_include_constant_term.setter
    def vf_include_constant_term(self, value: bool) -> None:
        """
        Property wrapper for the constant-term flag.

        :param value: Requested boolean state.
        :return: None.
        """
        self.set_vf_include_constant_term(value)

    def get_vf_include_proportional_term(self) -> bool:
        """
        Return whether the rational fit includes one proportional ``s`` term.

        :return: Boolean state.
        """
        return self._vf_include_proportional_term

    def set_vf_include_proportional_term(self, value: bool) -> None:
        """
        Enable or disable the proportional ``s`` term in the rational fit.

        :param value: Requested boolean state.
        :return: None.
        """
        self._vf_include_proportional_term = bool(value)

    @property
    def vf_include_proportional_term(self) -> bool:
        """
        Property wrapper for the proportional-term flag.

        :return: Boolean state.
        """
        return self.get_vf_include_proportional_term()

    @vf_include_proportional_term.setter
    def vf_include_proportional_term(self, value: bool) -> None:
        """
        Property wrapper for the proportional-term flag.

        :param value: Requested boolean state.
        :return: None.
        """
        self.set_vf_include_proportional_term(value)

    def get_passivity_frequency_sample_count(self) -> int:
        """
        Return the dense frequency-grid size used for passivity checks.

        :return: Positive sample count.
        """
        return self._passivity_frequency_sample_count

    def set_passivity_frequency_sample_count(self, value: int) -> None:
        """
        Set the dense frequency-grid size used for passivity checks.

        :param value: Requested positive sample count.
        :return: None.
        """
        sanitized_value: int = int(value)

        if sanitized_value >= 16:
            self._passivity_frequency_sample_count = sanitized_value
        else:
            self._passivity_frequency_sample_count = 16

    @property
    def passivity_frequency_sample_count(self) -> int:
        """
        Property wrapper for the passivity frequency-grid size.

        :return: Positive sample count.
        """
        return self.get_passivity_frequency_sample_count()

    @passivity_frequency_sample_count.setter
    def passivity_frequency_sample_count(self, value: int) -> None:
        """
        Property wrapper for the passivity frequency-grid size.

        :param value: Requested positive sample count.
        :return: None.
        """
        self.set_passivity_frequency_sample_count(value)

    def get_passivity_minimum_real_yc_tolerance(self) -> float:
        """
        Return the allowed negativity slack for ``Re(Yc(jw))``.

        :return: Non-negative tolerance.
        """
        return self._passivity_minimum_real_yc_tolerance

    def set_passivity_minimum_real_yc_tolerance(self, value: float) -> None:
        """
        Set the allowed negativity slack for ``Re(Yc(jw))``.

        :param value: Requested non-negative tolerance.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._passivity_minimum_real_yc_tolerance = sanitized_value
        else:
            self._passivity_minimum_real_yc_tolerance = 0.0

    @property
    def passivity_minimum_real_yc_tolerance(self) -> float:
        """
        Property wrapper for the ``Re(Yc)`` negativity tolerance.

        :return: Non-negative tolerance.
        """
        return self.get_passivity_minimum_real_yc_tolerance()

    @passivity_minimum_real_yc_tolerance.setter
    def passivity_minimum_real_yc_tolerance(self, value: float) -> None:
        """
        Property wrapper for the ``Re(Yc)`` negativity tolerance.

        :param value: Requested non-negative tolerance.
        :return: None.
        """
        self.set_passivity_minimum_real_yc_tolerance(value)

    def get_passivity_maximum_hres_gain_tolerance(self) -> float:
        """
        Return the allowed gain slack above unity for ``|Hres(jw)|``.

        :return: Non-negative tolerance.
        """
        return self._passivity_maximum_hres_gain_tolerance

    def set_passivity_maximum_hres_gain_tolerance(self, value: float) -> None:
        """
        Set the allowed gain slack above unity for ``|Hres(jw)|``.

        :param value: Requested non-negative tolerance.
        :return: None.
        """
        sanitized_value: float = float(value)

        if sanitized_value >= 0.0:
            self._passivity_maximum_hres_gain_tolerance = sanitized_value
        else:
            self._passivity_maximum_hres_gain_tolerance = 0.0

    @property
    def passivity_maximum_hres_gain_tolerance(self) -> float:
        """
        Property wrapper for the ``|Hres|`` gain slack tolerance.

        :return: Non-negative tolerance.
        """
        return self.get_passivity_maximum_hres_gain_tolerance()

    @passivity_maximum_hres_gain_tolerance.setter
    def passivity_maximum_hres_gain_tolerance(self, value: float) -> None:
        """
        Property wrapper for the ``|Hres|`` gain slack tolerance.

        :param value: Requested non-negative tolerance.
        :return: None.
        """
        self.set_passivity_maximum_hres_gain_tolerance(value)
