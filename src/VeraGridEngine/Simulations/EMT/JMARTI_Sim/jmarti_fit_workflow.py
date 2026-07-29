# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Sequence

import numpy as np

from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType
from VeraGridEngine.Devices.Branches.overhead_line_type import calc_y_matrix
from VeraGridEngine.Devices.Branches.overhead_line_type import calc_z_matrix
from VeraGridEngine.Devices.Branches.sequence_line_type import SequenceLineType
from VeraGridEngine.Devices.Branches.underground_line_type import UndergroundLineType
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_bundle import JMartiFitBundle
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_bundle import build_jmarti_fit_bundle
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_frequency_samples import JMartiFrequencySamples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_frequency_samples import build_jmarti_frequency_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_loewner_seed import build_jmarti_mode_loewner_seed
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import JMartiModalSamples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import JMartiModeDelayEstimate
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import build_jmarti_modal_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import estimate_jmarti_mode_delays
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_passivity import JMartiPassivityReport
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_passivity import evaluate_jmarti_passivity_report
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import JMartiRationalModeFit
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import build_jmarti_mode_vector_fit


def _normalize_phase_label(label: object) -> str:
    """
    Normalize one imported phase label to the internal upper-case representation.

    :param label: Imported phase-like object.
    :return: Normalized phase label.
    """
    if isinstance(label, bytes):
        return label.decode("utf-8").strip().upper()
    else:
        return str(label).strip().upper()


def _load_complex_array_from_npz(archive: np.lib.npyio.NpzFile, base_key: str) -> np.ndarray:
    """
    Load one complex array from one NPZ archive.

    The loader accepts either one native complex array under ``base_key`` or one
    explicit real/imag pair under ``<base_key>_real`` and ``<base_key>_imag``.

    :param archive: Open NPZ archive.
    :param base_key: Base array key.
    :return: Complex array.
    :raises ValueError: If the expected arrays are missing.
    """
    if base_key in archive.files:
        return np.asarray(archive[base_key], dtype=np.complex128)
    elif f"{base_key}_real" in archive.files and f"{base_key}_imag" in archive.files:
        return (
            np.asarray(archive[f"{base_key}_real"], dtype=np.float64)
            + 1j * np.asarray(archive[f"{base_key}_imag"], dtype=np.float64)
        )
    else:
        raise ValueError(
            f"JMARTI import requires '{base_key}' or the pair '{base_key}_real'/'{base_key}_imag' in the NPZ file"
        )


def _build_symmetric_abc_matrix_from_sequence_values(positive_sequence_value: complex,
                                                     zero_sequence_value: complex) -> np.ndarray:
    """
    Reconstruct one phase-domain matrix from positive and zero sequence values.

    :param positive_sequence_value: Positive-sequence scalar value.
    :param zero_sequence_value: Zero-sequence scalar value.
    :return: Symmetric 3x3 phase-domain matrix.
    """
    diagonal_value: complex = (2.0 * positive_sequence_value + zero_sequence_value) / 3.0
    off_diagonal_value: complex = (zero_sequence_value - positive_sequence_value) / 3.0
    matrix_abc: np.ndarray = np.full((3, 3), off_diagonal_value, dtype=np.complex128)
    np.fill_diagonal(matrix_abc, diagonal_value)
    return matrix_abc


def _build_sequence_shunt_admittance_from_susceptance(frequency_hz: float,
                                                      nominal_frequency_hz: float,
                                                      susceptance_micro_siemens_per_km: float) -> complex:
    """
    Build one frequency-scaled shunt admittance from one nominal susceptance.

    :param frequency_hz: Target frequency in Hz.
    :param nominal_frequency_hz: Nominal frequency in Hz.
    :param susceptance_micro_siemens_per_km: Nominal susceptance in uS/km.
    :return: Complex shunt admittance in S/km.
    """
    return 1j * float(susceptance_micro_siemens_per_km) * 1.0e-6 * float(frequency_hz) / float(nominal_frequency_hz)


def _build_sequence_shunt_admittance_from_capacitance(frequency_hz: float,
                                                      capacitance_per_km: float,
                                                      capacitance_scale: float) -> complex:
    """
    Build one shunt admittance from one capacitance density.

    :param frequency_hz: Target frequency in Hz.
    :param capacitance_per_km: Capacitance value in user units per km.
    :param capacitance_scale: Unit scale to Farad/km.
    :return: Complex shunt admittance in S/km.
    """
    return 1j * 2.0 * np.pi * float(frequency_hz) * float(capacitance_per_km) * float(capacitance_scale)


def _resolve_template_nominal_frequency_hz(template: object,
                                           nominal_frequency_hz: float | None = None) -> float:
    """
    Resolve the nominal frequency attached to one line template.

    :param template: Candidate template object.
    :param nominal_frequency_hz: Optional user override.
    :return: Positive nominal frequency in Hz.
    :raises ValueError: If no positive nominal frequency is available.
    """
    if nominal_frequency_hz is not None and float(nominal_frequency_hz) > 0.0:
        return float(nominal_frequency_hz)
    else:
        pass

    if isinstance(template, OverheadLineType) and float(template.frequency) > 0.0:
        return float(template.frequency)
    elif isinstance(template, UndergroundLineType) and float(template.freq) > 0.0:
        return float(template.freq)
    else:
        raise ValueError(
            "JMARTI automatic fitting requires one positive nominal frequency for this line template"
        )


def _build_sequence_line_frequency_sweep(template: SequenceLineType,
                                         frequency_hz: np.ndarray,
                                         nominal_frequency_hz: float) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    """
    Build one approximate frequency sweep from one ``SequenceLineType``.

    :param template: Sequence line template.
    :param frequency_hz: Target frequency grid in Hz.
    :param nominal_frequency_hz: Nominal reference frequency in Hz.
    :return: ``(Z, Y, phase_labels)`` with per-km units.
    """
    sample_count: int = int(frequency_hz.size)
    z_per_length: np.ndarray = np.empty((sample_count, 3, 3), dtype=np.complex128)
    y_per_length: np.ndarray = np.empty((sample_count, 3, 3), dtype=np.complex128)
    positive_inductance_per_km: float = float(template.X) / (2.0 * np.pi * nominal_frequency_hz)
    zero_inductance_per_km: float = float(template.X0) / (2.0 * np.pi * nominal_frequency_hz)
    sample_index: int = 0
    z1: complex
    z0: complex
    y1: complex
    y0: complex

    while sample_index < sample_count:
        z1 = complex(float(template.R), 2.0 * np.pi * float(frequency_hz[sample_index]) * positive_inductance_per_km)
        z0 = complex(float(template.R0), 2.0 * np.pi * float(frequency_hz[sample_index]) * zero_inductance_per_km)

        if bool(template.use_conductance):
            y1 = _build_sequence_shunt_admittance_from_capacitance(float(frequency_hz[sample_index]), float(template.Cnf), 1.0e-9)
            y0 = _build_sequence_shunt_admittance_from_capacitance(float(frequency_hz[sample_index]), float(template.Cnf0), 1.0e-9)
        else:
            y1 = _build_sequence_shunt_admittance_from_susceptance(float(frequency_hz[sample_index]), nominal_frequency_hz, float(template.B))
            y0 = _build_sequence_shunt_admittance_from_susceptance(float(frequency_hz[sample_index]), nominal_frequency_hz, float(template.B0))

        z_per_length[sample_index, :, :] = _build_symmetric_abc_matrix_from_sequence_values(z1, z0)
        y_per_length[sample_index, :, :] = _build_symmetric_abc_matrix_from_sequence_values(y1, y0)
        sample_index += 1

    return z_per_length, y_per_length, ("A", "B", "C")


def _build_underground_line_frequency_sweep(template: UndergroundLineType,
                                            frequency_hz: np.ndarray,
                                            nominal_frequency_hz: float) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    """
    Build one approximate frequency sweep from one ``UndergroundLineType``.

    :param template: Underground line template.
    :param frequency_hz: Target frequency grid in Hz.
    :param nominal_frequency_hz: Nominal reference frequency in Hz.
    :return: ``(Z, Y, phase_labels)`` with per-km units.
    """
    sample_count: int = int(frequency_hz.size)
    z_per_length: np.ndarray = np.empty((sample_count, 3, 3), dtype=np.complex128)
    y_per_length: np.ndarray = np.empty((sample_count, 3, 3), dtype=np.complex128)
    positive_inductance_per_km: float = float(template.X) / (2.0 * np.pi * nominal_frequency_hz)
    zero_inductance_per_km: float = float(template.X0) / (2.0 * np.pi * nominal_frequency_hz)
    sample_index: int = 0
    z1: complex
    z0: complex
    y1: complex
    y0: complex

    while sample_index < sample_count:
        z1 = complex(float(template.R), 2.0 * np.pi * float(frequency_hz[sample_index]) * positive_inductance_per_km)
        z0 = complex(float(template.R0), 2.0 * np.pi * float(frequency_hz[sample_index]) * zero_inductance_per_km)

        if abs(float(template.C)) > 0.0 or abs(float(template.C0)) > 0.0:
            y1 = _build_sequence_shunt_admittance_from_capacitance(float(frequency_hz[sample_index]), float(template.C), 1.0e-6)
            y0 = _build_sequence_shunt_admittance_from_capacitance(float(frequency_hz[sample_index]), float(template.C0), 1.0e-6)
        else:
            y1 = _build_sequence_shunt_admittance_from_susceptance(float(frequency_hz[sample_index]), nominal_frequency_hz, float(template.B))
            y0 = _build_sequence_shunt_admittance_from_susceptance(float(frequency_hz[sample_index]), nominal_frequency_hz, float(template.B0))

        z_per_length[sample_index, :, :] = _build_symmetric_abc_matrix_from_sequence_values(z1, z0)
        y_per_length[sample_index, :, :] = _build_symmetric_abc_matrix_from_sequence_values(y1, y0)
        sample_index += 1

    return z_per_length, y_per_length, ("A", "B", "C")


def load_jmarti_frequency_samples_from_npz(file_path: str,
                                           phase_n: bool,
                                           phase_a: bool,
                                           phase_b: bool,
                                           phase_c: bool,
                                           fallback_line_length_m: float | None = None) -> JMartiFrequencySamples:
    """
    Load one JMARTI frequency-domain sample set from one NPZ archive.

    Required arrays:
    - ``frequency_hz`` with shape ``(nf,)``
    - ``z_per_length`` or ``z_per_length_real``/``z_per_length_imag`` with shape ``(nf, np, np)``
    - ``y_per_length`` or ``y_per_length_real``/``y_per_length_imag`` with shape ``(nf, np, np)``

    Optional arrays:
    - ``phase_labels`` with shape ``(np,)``
    - ``line_length_m`` scalar

    Unit convention:
    - ``z_per_length`` must already be expressed in per-unit per meter
    - ``y_per_length`` must already be expressed in per-unit per meter

    :param file_path: NPZ file path.
    :param phase_n: Whether the neutral is enabled.
    :param phase_a: Whether phase A is enabled.
    :param phase_b: Whether phase B is enabled.
    :param phase_c: Whether phase C is enabled.
    :param fallback_line_length_m: Optional line-length fallback in meters.
    :return: Imported and validated frequency-domain samples.
    :raises ValueError: If the archive is missing required data.
    """
    resolved_file_path: str = str(file_path).strip()

    if resolved_file_path:
        pass
    else:
        raise ValueError("JMARTI import requires one NPZ file path")

    try:
        with np.load(resolved_file_path, allow_pickle=False) as archive:
            frequency_hz: np.ndarray = np.asarray(archive["frequency_hz"], dtype=np.float64)
            z_per_length: np.ndarray = _load_complex_array_from_npz(archive, "z_per_length")
            y_per_length: np.ndarray = _load_complex_array_from_npz(archive, "y_per_length")
            line_length_m: float

            if "phase_labels" in archive.files:
                available_labels: tuple[str, ...] = tuple(
                    _normalize_phase_label(label) for label in np.asarray(archive["phase_labels"]).tolist()
                )
            else:
                available_labels = _build_available_phase_labels(None, int(z_per_length.shape[1]))

            if "line_length_m" in archive.files:
                line_length_m = float(np.asarray(archive["line_length_m"], dtype=np.float64).reshape(-1)[0])
            elif fallback_line_length_m is not None:
                line_length_m = float(fallback_line_length_m)
            else:
                raise ValueError("JMARTI NPZ import requires one line_length_m array or one GUI fallback line length")
    except KeyError as exc:
        raise ValueError(f"JMARTI NPZ import is missing the array '{exc.args[0]}'") from exc
    except OSError as exc:
        raise ValueError(f"Unable to read JMARTI NPZ file '{resolved_file_path}': {exc}") from exc

    requested_labels: list[str] = list()
    if phase_n:
        requested_labels.append("N")
    if phase_a:
        requested_labels.append("A")
    if phase_b:
        requested_labels.append("B")
    if phase_c:
        requested_labels.append("C")
    phase_selection, selected_labels = _build_phase_selection_indices(available_labels, requested_labels)

    return build_jmarti_frequency_samples(
        frequency_hz=frequency_hz,
        z_per_length=_select_square_submatrices(z_per_length, phase_selection),
        y_per_length=_select_square_submatrices(y_per_length, phase_selection),
        line_length_m=line_length_m,
        phase_labels=selected_labels,
    )


def _convert_template_phase_id_to_label(phase_id: int) -> str:
    """
    Convert one NABC phase identifier to the GUI/runtime label.

    :param phase_id: Template phase identifier.
    :return: Phase label.
    :raises ValueError: If the phase layout is outside the first single-circuit NABC set.
    """
    if phase_id == 0:
        return "N"
    elif phase_id == 1:
        return "A"
    elif phase_id == 2:
        return "B"
    elif phase_id == 3:
        return "C"
    else:
        raise ValueError(
            "The first JMARTI GUI workflow currently supports only single-circuit NABC overhead templates"
        )


def _build_available_phase_labels(template_phase_ids: Sequence[int] | None,
                                  matrix_dimension: int) -> tuple[str, ...]:
    """
    Resolve one label set for the sampled phase-domain matrices.

    :param template_phase_ids: Optional stored phase identifiers.
    :param matrix_dimension: Matrix order.
    :return: Ordered phase labels.
    :raises ValueError: If the phase metadata is inconsistent.
    """
    if template_phase_ids is not None and len(template_phase_ids) == matrix_dimension:
        return tuple(_convert_template_phase_id_to_label(int(phase_id)) for phase_id in template_phase_ids)
    elif matrix_dimension == 4:
        return "N", "A", "B", "C"
    elif matrix_dimension == 3:
        return "A", "B", "C"
    elif matrix_dimension == 2:
        return "A", "B"
    elif matrix_dimension == 1:
        return ("A",)
    else:
        raise ValueError(
            "JMARTI GUI fitting expects one NABC-like overhead-line matrix with at most four conductors"
        )

def _build_phase_selection_indices(available_labels: Sequence[str],
                                   requested_labels: Sequence[str]) -> tuple[np.ndarray, tuple[str, ...]]:
    """
    Map one requested phase layout to matrix row and column indices.

    :param available_labels: Labels available in the sampled matrices.
    :param requested_labels: Labels requested by the GUI configuration.
    :return: Selected matrix indices and ordered labels.
    :raises ValueError: If the selected block phases are not available.
    """
    available_label_list: list[str] = list(str(label) for label in available_labels)
    selected_indices: list[int] = list()
    requested_label: str

    for requested_label in requested_labels:
        if requested_label in available_label_list:
            selected_indices.append(available_label_list.index(requested_label))
        else:
            raise ValueError(
                f"Requested JMARTI phase '{requested_label}' is not available in the attached line template"
            )

    return np.asarray(selected_indices, dtype=np.int64), tuple(requested_labels)


def _select_square_submatrices(matrices: np.ndarray, selection: np.ndarray) -> np.ndarray:
    """
    Select one consistent square submatrix across a whole frequency sweep.

    :param matrices: Sweep tensor with shape ``(nf, np, np)``.
    :param selection: Selected phase indices.
    :return: Reduced sweep tensor.
    """
    return matrices[:, selection, :][:, :, selection]


def _convert_per_km_tensor_to_per_m(matrices_per_km: np.ndarray) -> np.ndarray:
    """
    Convert one per-km sweep tensor to one per-meter sweep tensor.

    :param matrices_per_km: Sweep tensor expressed per km.
    :return: Sweep tensor expressed per meter.
    """
    return np.asarray(matrices_per_km, dtype=np.complex128) / 1000.0




def _convert_physical_per_meter_series_shunt_to_per_unit(z_per_meter: np.ndarray,
                                                          y_per_meter: np.ndarray,
                                                          sbase_mva: float,
                                                          vbase_kv: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert one physical per-meter ``(Z, Y)`` sweep pair to per unit.

    :param z_per_meter: Physical series impedance per meter in ohm/m.
    :param y_per_meter: Physical shunt admittance per meter in S/m.
    :param sbase_mva: System base power in MVA.
    :param vbase_kv: Voltage base in kV.
    :return: Per-unit per-meter ``(Z, Y)`` tensors.
    """
    z_base_ohm: float = (float(vbase_kv) * float(vbase_kv)) / float(sbase_mva)
    y_base_siemens: float = 1.0 / z_base_ohm
    return (
        np.asarray(z_per_meter, dtype=np.complex128) / z_base_ohm,
        np.asarray(y_per_meter, dtype=np.complex128) / y_base_siemens,
    )


def _build_nominal_rlgc_frequency_sweep(z_nominal_per_length: np.ndarray,
                                        y_nominal_per_length: np.ndarray,
                                        nominal_frequency_hz: float,
                                        frequency_hz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Build one approximate RLGC sweep from one nominal overhead-line matrix pair.

    When only one nominal-frequency matrix pair is available, the first GUI flow
    assumes frequency-independent ``R``, ``L``, ``G`` and ``C`` matrices and
    reconstructs the sweep as ``R + jwL`` and ``G + jwC``.

    :param z_nominal_per_length: Nominal series-impedance matrix.
    :param y_nominal_per_length: Nominal shunt-admittance matrix.
    :param nominal_frequency_hz: Frequency where the nominal matrices were computed.
    :param frequency_hz: Sweep grid in Hz.
    :return: Frequency-dependent ``(Z, Y)`` tensors.
    :raises ValueError: If the nominal frequency is not positive.
    """
    resolved_nominal_frequency_hz: float = float(nominal_frequency_hz)
    sample_count: int = int(frequency_hz.size)
    phase_count: int = int(z_nominal_per_length.shape[0])
    angular_reference: float = 2.0 * np.pi * resolved_nominal_frequency_hz
    angular_frequency: np.ndarray = 2.0 * np.pi * np.asarray(frequency_hz, dtype=np.float64)
    z_sweep: np.ndarray = np.empty((sample_count, phase_count, phase_count), dtype=np.complex128)
    y_sweep: np.ndarray = np.empty((sample_count, phase_count, phase_count), dtype=np.complex128)
    resistance_matrix: np.ndarray
    inductance_matrix: np.ndarray
    conductance_matrix: np.ndarray
    capacitance_matrix: np.ndarray
    sample_index: int = 0

    if resolved_nominal_frequency_hz > 0.0:
        pass
    else:
        raise ValueError("JMARTI nominal overhead-line matrices require one positive reference frequency")

    resistance_matrix = np.real(z_nominal_per_length)
    inductance_matrix = np.imag(z_nominal_per_length) / angular_reference
    conductance_matrix = np.real(y_nominal_per_length)
    capacitance_matrix = np.imag(y_nominal_per_length) / angular_reference

    while sample_index < sample_count:
        z_sweep[sample_index, :, :] = resistance_matrix + 1j * angular_frequency[sample_index] * inductance_matrix
        y_sweep[sample_index, :, :] = conductance_matrix + 1j * angular_frequency[sample_index] * capacitance_matrix
        sample_index += 1

    return z_sweep, y_sweep


def build_jmarti_frequency_samples_from_line(line: Line,
                                             phase_n: bool,
                                             phase_a: bool,
                                             phase_b: bool,
                                             phase_c: bool,
                                             low_hz: float,
                                             high_hz: float,
                                             sample_count: int,
                                             nominal_frequency_hz: float | None = None,
                                             sbase_mva: float | None = None) -> JMartiFrequencySamples:
    """
    Build one JMARTI frequency-domain dataset from one physical line object.

    The GUI-driven flow targets concrete ``Line`` devices backed by one overhead,
    sequence, or underground template. When the template still carries conductor
    geometry, the sweep is evaluated directly over frequency. Otherwise the first
    implementation falls back to one frequency-independent RLGC extrapolation
    reconstructed from the nominal template values.

    :param line: Concrete line device being edited.
    :param phase_n: Whether the neutral is enabled on the EMT block.
    :param phase_a: Whether phase A is enabled.
    :param phase_b: Whether phase B is enabled.
    :param phase_c: Whether phase C is enabled.
    :param low_hz: Lower sweep frequency in Hz.
    :param high_hz: Upper sweep frequency in Hz.
    :param sample_count: Number of sweep samples.
    :param nominal_frequency_hz: Optional nominal frequency used to reconstruct RLGC sweeps.
    :param sbase_mva: System base power in MVA used to convert the line data to per unit.
    :return: Frequency-domain JMARTI sample set.
    :raises ValueError: If the line cannot provide compatible data.
    """

    template = line.template

    if line.bus_from.Vnom > 0:
        resolved_vbase_kv = float(line.bus_from.Vnom)
    elif line.bus_to.Vnom > 0:
        resolved_vbase_kv = float(line.bus_to.Vnom)
    elif isinstance(line.template, (OverheadLineType, SequenceLineType, UndergroundLineType)) and float(
            line.template.Vnom) > 0.0:
        resolved_vbase_kv = float(line.template.Vnom)
    else:
        raise ValueError("JMARTI fitting requires one positive nominal voltage to convert the line data to per unit")

    if low_hz > 0.0:
        frequency_hz = np.logspace(np.log10(float(low_hz)),
                           np.log10(float(high_hz)),
                           int(sample_count),
                           dtype=np.float64)
    else:
        frequency_hz = np.linspace(float(low_hz),
                           float(high_hz),
                           int(sample_count),
                           dtype=np.float64)

    requested_labels: list[str] = list()
    if phase_n:
        requested_labels.append("N")
    if phase_a:
        requested_labels.append("A")
    if phase_b:
        requested_labels.append("B")
    if phase_c:
        requested_labels.append("C")


    phase_selection: np.ndarray
    selected_labels: tuple[str, ...]

    if isinstance(template, OverheadLineType) and len(template.wires_in_tower.data) > 0:
        z_per_length: np.ndarray | None = None
        y_per_length: np.ndarray | None = None
        available_labels: tuple[str, ...] | None = None
        sample_index: int = 0
        z_full: np.ndarray
        y_full: np.ndarray
        z_phase_ids: Sequence[int]
        y_phase_ids: Sequence[int]

        while sample_index < frequency_hz.size:
            z_full, z_phase_ids, _, _, _ = calc_z_matrix(template.wires_in_tower,
                                                         f=float(frequency_hz[sample_index]),
                                                         rho=template.earth_resistivity)
            y_full, y_phase_ids, _, _, _ = calc_y_matrix(template.wires_in_tower,
                                                         f=float(frequency_hz[sample_index]))

            if tuple(z_phase_ids) == tuple(y_phase_ids):
                pass
            else:
                raise ValueError("JMARTI overhead-line frequency sweep produced inconsistent Z/Y phase layouts")

            if available_labels is None:
                available_labels = _build_available_phase_labels(z_phase_ids, z_full.shape[0])
                phase_selection, selected_labels = _build_phase_selection_indices(available_labels, requested_labels)
                z_per_length = np.empty((frequency_hz.size, phase_selection.size, phase_selection.size), dtype=np.complex128)
                y_per_length = np.empty((frequency_hz.size, phase_selection.size, phase_selection.size), dtype=np.complex128)
            else:
                pass

            z_per_length[sample_index, :, :] = z_full[np.ix_(phase_selection, phase_selection)]
            y_per_length[sample_index, :, :] = y_full[np.ix_(phase_selection, phase_selection)]
            sample_index += 1

        z_per_length_pu, y_per_length_pu = _convert_physical_per_meter_series_shunt_to_per_unit(
            z_per_meter=_convert_per_km_tensor_to_per_m(z_per_length),
            y_per_meter=_convert_per_km_tensor_to_per_m(y_per_length),
            sbase_mva=sbase_mva,
            vbase_kv=resolved_vbase_kv,
        )

        return build_jmarti_frequency_samples(
            frequency_hz=frequency_hz,
            z_per_length=z_per_length_pu,
            y_per_length=y_per_length_pu,
            line_length_m=float(line.length) * 1000.0,
            phase_labels=selected_labels,
        )
    elif isinstance(template, OverheadLineType) and template.z_nabc is not None and template.y_nabc is not None:
        available_labels = _build_available_phase_labels(template.z_phases_nabc, template.z_nabc.shape[0])
        phase_selection, selected_labels = _build_phase_selection_indices(available_labels, requested_labels)
        z_full_sweep, y_full_sweep = _build_nominal_rlgc_frequency_sweep(
            z_nominal_per_length=np.asarray(template.z_nabc, dtype=np.complex128),
            y_nominal_per_length=np.asarray(template.y_nabc, dtype=np.complex128),
            nominal_frequency_hz=_resolve_template_nominal_frequency_hz(template, nominal_frequency_hz),
            frequency_hz=frequency_hz,
        )

        z_per_length_pu, y_per_length_pu = _convert_physical_per_meter_series_shunt_to_per_unit(
            z_per_meter=_convert_per_km_tensor_to_per_m(_select_square_submatrices(z_full_sweep, phase_selection)),
            y_per_meter=_convert_per_km_tensor_to_per_m(_select_square_submatrices(y_full_sweep, phase_selection)),
            sbase_mva=sbase_mva,
            vbase_kv=resolved_vbase_kv,
        )

        return build_jmarti_frequency_samples(
            frequency_hz=frequency_hz,
            z_per_length=z_per_length_pu,
            y_per_length=y_per_length_pu,
            line_length_m=float(line.length) * 1000.0,
            phase_labels=selected_labels,
        )
    elif isinstance(template, SequenceLineType):
        z_full_sweep, y_full_sweep, available_labels = _build_sequence_line_frequency_sweep(
            template=template,
            frequency_hz=frequency_hz,
            nominal_frequency_hz=_resolve_template_nominal_frequency_hz(template, nominal_frequency_hz),
        )
        phase_selection, selected_labels = _build_phase_selection_indices(available_labels, requested_labels)

        z_per_length_pu, y_per_length_pu = _convert_physical_per_meter_series_shunt_to_per_unit(
            z_per_meter=_convert_per_km_tensor_to_per_m(_select_square_submatrices(z_full_sweep, phase_selection)),
            y_per_meter=_convert_per_km_tensor_to_per_m(_select_square_submatrices(y_full_sweep, phase_selection)),
            sbase_mva=sbase_mva,
            vbase_kv=resolved_vbase_kv,
        )

        return build_jmarti_frequency_samples(
            frequency_hz=frequency_hz,
            z_per_length=z_per_length_pu,
            y_per_length=y_per_length_pu,
            line_length_m=float(line.length) * 1000.0,
            phase_labels=selected_labels,
        )
    elif isinstance(template, UndergroundLineType):
        z_full_sweep, y_full_sweep, available_labels = _build_underground_line_frequency_sweep(
            template=template,
            frequency_hz=frequency_hz,
            nominal_frequency_hz=_resolve_template_nominal_frequency_hz(template, nominal_frequency_hz),
        )
        phase_selection, selected_labels = _build_phase_selection_indices(available_labels, requested_labels)

        z_per_length_pu, y_per_length_pu = _convert_physical_per_meter_series_shunt_to_per_unit(
            z_per_meter=_convert_per_km_tensor_to_per_m(_select_square_submatrices(z_full_sweep, phase_selection)),
            y_per_meter=_convert_per_km_tensor_to_per_m(_select_square_submatrices(y_full_sweep, phase_selection)),
            sbase_mva=sbase_mva,
            vbase_kv=resolved_vbase_kv,
        )

        return build_jmarti_frequency_samples(
            frequency_hz=frequency_hz,
            z_per_length=z_per_length_pu,
            y_per_length=y_per_length_pu,
            line_length_m=float(line.length) * 1000.0,
            phase_labels=selected_labels,
        )
    else:
        raise ValueError(
            "JMARTI GUI fitting requires one compatible line template with geometry, nominal matrices, or sequence data"
        )


def build_jmarti_hres_modal_responses(modal_samples: JMartiModalSamples,
                                      mode_delays: Sequence[JMartiModeDelayEstimate]) -> np.ndarray:
    """
    Build the residual propagation responses fitted as ``Hres`` per mode.

    ``Hres`` is the propagation operator left after extracting one pure delay
    from each modal channel. It combines attenuation and the residual dispersive
    phase not captured by the affine delay estimate.

    :param modal_samples: Modalized frequency samples.
    :param mode_delays: Per-mode delay estimates.
    :return: Complex response matrix with shape ``(nf, nmodes)``.
    :raises ValueError: If the modal objects do not align.
    """
    mode_count: int = modal_samples.get_mode_count()
    tau_values_s: np.ndarray

    if len(mode_delays) == mode_count:
        pass
    else:
        raise ValueError("JMARTI Hres construction requires exactly one delay estimate per mode")

    tau_values_s = np.asarray([delay.get_tau_s() for delay in mode_delays], dtype=np.float64)[None, :]

    return np.exp(
        -(modal_samples.get_gamma_modal() * modal_samples.get_line_length_m())
        + 1j * modal_samples.get_angular_frequency_rad_per_s()[:, None] * tau_values_s
    )


def build_jmarti_fit_bundle_from_frequency_samples(samples: JMartiFrequencySamples,
                                                   options: JMartiFitOptions | None = None) -> JMartiFitBundle:
    """
    Run the full first-generation JMARTI fitting pipeline on one sample set.

    The helper centralizes the modal preprocessing, delay extraction, Loewner
    seeding, Vector Fitting, and passivity-like checks so higher layers such as
    the GUI can trigger one consistent offline preprocessing workflow.

    :param samples: Frequency-domain line dataset.
    :param options: Optional user-configurable fit options.
    :return: Offline JMARTI fit bundle.
    """
    resolved_options: JMartiFitOptions = JMartiFitOptions() if options is None else options
    modal_samples: JMartiModalSamples = build_jmarti_modal_samples(samples=samples, options=resolved_options)
    mode_delays: list[JMartiModeDelayEstimate] = estimate_jmarti_mode_delays(modal_samples, options=resolved_options)
    hres_modal: np.ndarray = build_jmarti_hres_modal_responses(modal_samples=modal_samples, mode_delays=mode_delays)
    frequency_hz: np.ndarray = modal_samples.get_frequency_hz()
    mode_count: int = modal_samples.get_mode_count()
    yc_fits: list[JMartiRationalModeFit] = list()
    hres_fits: list[JMartiRationalModeFit] = list()
    mode_index: int = 0
    yc_response_values: np.ndarray
    hres_response_values: np.ndarray
    combined_fits: list[JMartiRationalModeFit]
    passivity_report: JMartiPassivityReport

    while mode_index < mode_count:
        yc_response_values = modal_samples.get_yc_modal()[:, mode_index]
        hres_response_values = hres_modal[:, mode_index]
        yc_fits.append(
            build_jmarti_mode_vector_fit(
                frequency_hz=frequency_hz,
                response_values=yc_response_values,
                loewner_seed=build_jmarti_mode_loewner_seed(
                    frequency_hz=frequency_hz,
                    response_values=yc_response_values,
                    target_name="Yc",
                    mode_index=mode_index,
                    options=resolved_options,
                ),
                options=resolved_options,
            )
        )
        hres_fits.append(
            build_jmarti_mode_vector_fit(
                frequency_hz=frequency_hz,
                response_values=hres_response_values,
                loewner_seed=build_jmarti_mode_loewner_seed(
                    frequency_hz=frequency_hz,
                    response_values=hres_response_values,
                    target_name="Hres",
                    mode_index=mode_index,
                    options=resolved_options,
                ),
                options=resolved_options,
            )
        )
        mode_index += 1

    combined_fits = list(yc_fits)
    combined_fits.extend(hres_fits)
    passivity_report = evaluate_jmarti_passivity_report(
        fits=combined_fits,
        low_hz=float(frequency_hz[0]),
        high_hz=float(frequency_hz[-1]),
        options=resolved_options,
    )

    return build_jmarti_fit_bundle(
        modal_samples=modal_samples,
        mode_delays=mode_delays,
        yc_fits=yc_fits,
        hres_fits=hres_fits,
        passivity_report=passivity_report,
    )
