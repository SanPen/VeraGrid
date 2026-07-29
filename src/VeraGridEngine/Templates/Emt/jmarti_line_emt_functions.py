# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Dict, List, Any

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime import set_jmarti_block_runtime_data, set_jmarti_block_fit_bundle

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import build_jmarti_fit_bundle_from_frequency_samples, load_jmarti_frequency_samples_from_npz, build_jmarti_frequency_samples_from_line
from VeraGridEngine.enumerations import BlockType
from VeraGridEngine.Devices.Branches.line import Line
from VeraGrid.Gui.DynamicModelEditor.ElementDialogues.jmarti_line_emt_dialog import JMartiLineEmtDialog
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_utilities import create_j_marti_line_block
from VeraGrid.Gui.DynamicModelEditor.dynamic_editor_graphics import GenericBlockItem

@staticmethod
def _extract_jmarti_phase_tuple(modal_config: Dict[str, Any]) -> tuple[bool, bool, bool, bool]:
    """
    Return the ordered phase tuple stored in one JMARTI modal configuration.

    :param modal_config: Persisted modal configuration.
    :return: ``(phase_n, phase_a, phase_b, phase_c)``.
    """
    return (
        bool(modal_config.get("phase_n", False)),
        bool(modal_config.get("phase_a", True)),
        bool(modal_config.get("phase_b", True)),
        bool(modal_config.get("phase_c", True)),
    )


def _build_jmarti_fit_options_from_modal_config(self, modal_config: Dict[str, Any]) -> JMartiFitOptions:
    """
    Build one typed JMARTI fit-options object from one modal configuration.

    :param modal_config: Persisted GUI configuration.
    :return: Typed fit options.
    """
    resolved_config: Dict[str, Any] = self._build_default_jmarti_line_modal_config()
    resolved_config.update(modal_config)
    options_kwargs: Dict[str, Any] = dict()
    option_key: str

    for option_key in self.JMARTI_MODAL_OPTION_KEYS:
        options_kwargs[option_key] = resolved_config[option_key]

    return JMartiFitOptions(**options_kwargs)


def _build_default_jmarti_line_modal_config(self,
                                            phase_n: bool = False,
                                            phase_a: bool = True,
                                            phase_b: bool = True,
                                            phase_c: bool = True) -> Dict[str, Any]:
    """
    Build one default persisted configuration for the JMARTI line modal.

    :param phase_n: Whether the neutral is enabled.
    :param phase_a: Whether phase A is enabled.
    :param phase_b: Whether phase B is enabled.
    :param phase_c: Whether phase C is enabled.
    :return: Default modal configuration.
    """
    options: JMartiFitOptions = JMartiFitOptions()
    nominal_frequency_hz: float = 50.0

    try:
        if self.circuit is not None and float(self.circuit.fbase) > 0.0:
            nominal_frequency_hz = float(self.circuit.fbase)
        else:
            pass
    except Exception:
        pass

    return dict({
        "phase_n": bool(phase_n),
        "phase_a": bool(phase_a),
        "phase_b": bool(phase_b),
        "phase_c": bool(phase_c),
        "data_source_mode": "auto_template",
        "nominal_frequency_hz": nominal_frequency_hz,
        "import_file_path": "",
        "import_line_length_m": 0.0,
        "sweep_low_hz": 10.0,
        "sweep_high_hz": 10000.0,
        "sweep_sample_count": 48,
        "reference_frequency_hz": float(options.reference_frequency_hz),
        "use_frequency_exploration_window": bool(options.use_frequency_exploration_window),
        "exploration_low_hz": float(options.exploration_low_hz),
        "exploration_high_hz": float(options.exploration_high_hz),
        "use_delay_fit_window": bool(options.use_delay_fit_window),
        "delay_fit_low_hz": float(options.delay_fit_low_hz),
        "delay_fit_high_hz": float(options.delay_fit_high_hz),
        "decoupling_warning_tolerance": float(options.decoupling_warning_tolerance),
        "loewner_relative_tolerance": float(options.loewner_relative_tolerance),
        "maximum_model_order": int(options.maximum_model_order),
        "forced_model_order": int(options.forced_model_order),
        "minimum_frequency_samples": int(options.minimum_frequency_samples),
        "vf_max_iterations": int(options.vf_max_iterations),
        "vf_pole_shift_tolerance": float(options.vf_pole_shift_tolerance),
        "vf_enforce_stable_poles": bool(options.vf_enforce_stable_poles),
        "vf_stability_real_part_floor": float(options.vf_stability_real_part_floor),
        "vf_include_constant_term": bool(options.vf_include_constant_term),
        "vf_include_proportional_term": bool(options.vf_include_proportional_term),
        "passivity_frequency_sample_count": int(options.passivity_frequency_sample_count),
        "passivity_minimum_real_yc_tolerance": float(options.passivity_minimum_real_yc_tolerance),
        "passivity_maximum_hres_gain_tolerance": float(options.passivity_maximum_hres_gain_tolerance),
        "fit_ready": False,
        "fit_source_description": "",
        "fit_status": (
            "Fit not computed yet. Accept the dialog to build or refresh the JMARTI fit for the attached line."
        ),
        "fit_diagnostics_text": "",
    })


@staticmethod
def _build_jmarti_fit_diagnostics_text(source_description: str,
                                       fit_bundle) -> str:
    """
    Build one human-readable JMARTI fit report for the GUI.

    :param source_description: Data-source description.
    :param fit_bundle: Computed fit bundle.
    :return: Multiline diagnostics text.
    """
    frequency_hz = fit_bundle.get_frequency_hz()
    passivity_report = fit_bundle.get_passivity_report()
    mode_delays = fit_bundle.get_mode_delays()
    yc_fits = fit_bundle.get_yc_fits()
    hres_fits = fit_bundle.get_hres_fits()
    diagnostics_lines: List[str] = list()
    mode_index: int = 0

    diagnostics_lines.append(f"Source: {source_description}")
    diagnostics_lines.append(f"Phases: {', '.join(fit_bundle.get_phase_labels())}")
    diagnostics_lines.append(
        f"Frequency band: {float(frequency_hz[0]):.6g} Hz to {float(frequency_hz[-1]):.6g} Hz ({frequency_hz.size} samples)"
    )
    diagnostics_lines.append(f"Reference modal frequency: {fit_bundle.get_reference_frequency_hz():.6g} Hz")
    diagnostics_lines.append(f"Line length: {fit_bundle.get_line_length_m():.6f} m")
    diagnostics_lines.append(
        f"Max decoupling Z/Y: {float(fit_bundle.get_decoupling_error_z().max()):.3e} / {float(fit_bundle.get_decoupling_error_y().max()):.3e}"
    )

    if passivity_report is None:
        diagnostics_lines.append("Passivity checks: not available")
    elif passivity_report.get_all_checks_pass():
        diagnostics_lines.append("Passivity checks: PASS")
    else:
        diagnostics_lines.append("Passivity checks: WARN")

    while mode_index < fit_bundle.get_mode_count():
        diagnostics_lines.append(
            f"Mode {mode_index}: tau = {mode_delays[mode_index].get_tau_s():.6e} s, phase RMS = {mode_delays[mode_index].get_rms_phase_error_rad():.3e} rad"
        )
        diagnostics_lines.append(
            f"  Yc: order {yc_fits[mode_index].get_poles_s().size}, rms {yc_fits[mode_index].get_fit_error_rms():.3e}, max {yc_fits[mode_index].get_max_relative_error():.3e}, stable {yc_fits[mode_index].get_stable()}, converged {yc_fits[mode_index].get_converged()}"
        )
        diagnostics_lines.append(
            f"  Hres: order {hres_fits[mode_index].get_poles_s().size}, rms {hres_fits[mode_index].get_fit_error_rms():.3e}, max {hres_fits[mode_index].get_max_relative_error():.3e}, stable {hres_fits[mode_index].get_stable()}, converged {hres_fits[mode_index].get_converged()}"
        )
        mode_index += 1

    return "\n".join(diagnostics_lines)


@staticmethod
def _build_jmarti_modal_tooltip(modal_config: Dict[str, Any]) -> str:
    """
    Build the tooltip shown for one JMARTI block item.

    :param modal_config: Persisted modal configuration.
    :return: Tooltip text.
    """
    diagnostics_text: str = str(modal_config.get("fit_diagnostics_text", "")).strip()

    if diagnostics_text:
        return diagnostics_text
    else:
        return str(modal_config.get("fit_status", "J_Marti line"))


def _apply_jmarti_line_fit_configuration(self, modal_config: Dict[str, Any]) -> tuple[Dict[str, Any], Any | None]:
    """
    Apply one JMARTI GUI configuration to the attached line object when possible.

    :param modal_config: Dialog configuration.
    :return: Updated persisted configuration including fit status.
    """

    options: JMartiFitOptions = JMartiFitOptions()

    updated_config = dict({
        "block_type": BlockType.EMT_JMARTI_LINE.name,
        "phase_n": bool(modal_config.get("phase_n", False)),
        "phase_a": bool(modal_config.get("phase_a", True)),
        "phase_b": bool(modal_config.get("phase_b", True)),
        "phase_c": bool(modal_config.get("phase_c", True)),
        "data_source_mode": "auto_template",
        "nominal_frequency_hz": 50.0,
        # "nominal_frequency_hz": float(self.circuit.fbase) if self.circuit is not None and float(self.circuit.fbase) > 0.0 else 50.0,
        "import_file_path": "",
        "import_line_length_m": float(options.import_line_length) if options.import_line_length > 0 else (
            float(self.api_object.length) * 1000.0 if self.api_object is not None and float(
                self.api_object.length) > 0 else None),
        "sweep_low_hz": 10.0,  #
        "sweep_high_hz": 10000.0,
        "sweep_sample_count": 48,
        "reference_frequency_hz": float(options.reference_frequency_hz),
        "use_frequency_exploration_window": bool(options.use_frequency_exploration_window),
        "exploration_low_hz": float(options.exploration_low_hz),
        "exploration_high_hz": float(options.exploration_high_hz),
        "use_delay_fit_window": bool(options.use_delay_fit_window),
        "delay_fit_low_hz": float(options.delay_fit_low_hz),
        "delay_fit_high_hz": float(options.delay_fit_high_hz),
        "decoupling_warning_tolerance": float(options.decoupling_warning_tolerance),
        "loewner_relative_tolerance": float(options.loewner_relative_tolerance),
        "maximum_model_order": int(options.maximum_model_order),
        "forced_model_order": int(options.forced_model_order),
        "minimum_frequency_samples": int(options.minimum_frequency_samples),
        "vf_max_iterations": int(options.vf_max_iterations),
        "vf_pole_shift_tolerance": float(options.vf_pole_shift_tolerance),
        "vf_enforce_stable_poles": bool(options.vf_enforce_stable_poles),
        "vf_stability_real_part_floor": float(options.vf_stability_real_part_floor),
        "vf_include_constant_term": bool(options.vf_include_constant_term),
        "vf_include_proportional_term": bool(options.vf_include_proportional_term),
        "passivity_frequency_sample_count": int(options.passivity_frequency_sample_count),
        "passivity_minimum_real_yc_tolerance": float(options.passivity_minimum_real_yc_tolerance),
        "passivity_maximum_hres_gain_tolerance": float(options.passivity_maximum_hres_gain_tolerance),
        "fit_ready": False,
        "fit_source_description": "",
        "fit_status": (
            "Fit not computed yet. Accept the dialog to build or refresh the JMARTI fit for the attached line."
        ),
        "fit_diagnostics_text": "",
    })

    updated_config.update(modal_config)

    # maby not useful at all
    fit_ready: bool = False
    fit_status: str = str(updated_config.get("fit_status", ""))
    fit_diagnostics_text: str = str(updated_config.get("fit_diagnostics_text", ""))
    line_object: Line | None
    fit_bundle = None
    #####

    if str(updated_config.get("data_source_mode", "auto_template")) == "import_frequency_samples":

        try:
            fit_bundle = build_jmarti_fit_bundle_from_frequency_samples(
                samples=load_jmarti_frequency_samples_from_npz(
                    file_path=str(updated_config.get("import_file_path", "")),
                    phase_n=bool(updated_config["phase_n"]),
                    phase_a=bool(updated_config["phase_a"]),
                    phase_b=bool(updated_config["phase_b"]),
                    phase_c=bool(updated_config["phase_c"]),
                    fallback_line_length_m=updated_config["import_line_length_m"],
                ),
                options=self._build_jmarti_fit_options_from_modal_config(updated_config),
            )
        except ValueError as exc:
            fit_status = f"Fit not computed: {exc}"
            fit_diagnostics_text = fit_status
            QtWidgets.QMessageBox.warning(self, "EMT J_Marti line", fit_status)

    else:
        if self.api_object.template is None:
            fit_status = "Fit not computed: attach one compatible line template to the line device first."
            fit_diagnostics_text = fit_status
        else:
            try:
                fit_bundle = build_jmarti_fit_bundle_from_frequency_samples(
                    samples=build_jmarti_frequency_samples_from_line(
                        line=line_object,
                        phase_n=bool(updated_config["phase_n"]),
                        phase_a=bool(updated_config["phase_a"]),
                        phase_b=bool(updated_config["phase_b"]),
                        phase_c=bool(updated_config["phase_c"]),
                        low_hz=float(updated_config["sweep_low_hz"]),
                        high_hz=float(updated_config["sweep_high_hz"]),
                        sample_count=int(updated_config["sweep_sample_count"]),
                        nominal_frequency_hz=float(updated_config["nominal_frequency_hz"]),
                        sbase_mva=float(self.circuit.Sbase) if self.circuit is not None else None,
                    ),
                    options=self._build_jmarti_fit_options_from_modal_config(updated_config),
                )
            except ValueError as exc:
                fit_status = f"Fit not computed: {exc}"
                fit_diagnostics_text = fit_status
                QtWidgets.QMessageBox.warning(self, "EMT J_Marti line", fit_status)

    if fit_bundle is not None:
        passivity_report = fit_bundle.get_passivity_report()
        decoupling_error_z = fit_bundle.get_decoupling_error_z()
        decoupling_error_y = fit_bundle.get_decoupling_error_y()
        max_decoupling_z: float = float(decoupling_error_z.max()) if decoupling_error_z.size > 0 else 0.0
        max_decoupling_y: float = float(decoupling_error_y.max()) if decoupling_error_y.size > 0 else 0.0

        if passivity_report is None or passivity_report.get_all_checks_pass():
            passivity_state = "pass"
        else:
            passivity_state = "warn"

        fit_ready = True
        fit_status = (
            "Fit computed: "
            f"{fit_bundle.get_mode_count()} modes, "
            f"{fit_bundle.get_frequency_hz().size} samples, "
            f"max decoupling Z/Y = {max_decoupling_z:.3e}/{max_decoupling_y:.3e}, "
            f"passivity = {passivity_state}."
        )
        fit_diagnostics_text = self._build_jmarti_fit_diagnostics_text("fit_source_description_not_needed", fit_bundle)

    updated_config["fit_ready"] = fit_ready
    updated_config["fit_source_description"] = "fit_source_description_not_needed"
    updated_config["fit_status"] = fit_status
    updated_config["fit_diagnostics_text"] = fit_diagnostics_text
    return updated_config, fit_bundle


def create_jmarti_line_emt_block_item(self, x_pos: float, y_pos: float) -> GenericBlockItem | None:
    """
    Create one EMT J_Marti line block configured through its dedicated modal.

    :param x_pos: Drop x position.
    :param y_pos: Drop y position.
    :return: Created block item or ``None`` when the dialog is cancelled.
    """
    dialog = JMartiLineEmtDialog(self, initial_config=self._build_default_jmarti_line_modal_config())

    if dialog.exec() == QDialog.DialogCode.Accepted:
        modal_config, fit_bundle = self._apply_jmarti_line_fit_configuration(dialog.get_configuration())
    else:
        return None

    phase_n, phase_a, phase_b, phase_c = self._extract_jmarti_phase_tuple(modal_config)
    count: int = self.block_counters.get(BlockType.EMT_JMARTI_LINE, 0) + 1
    item_name: str = f"{BlockType.EMT_JMARTI_LINE.name}_{count}"
    block_model = create_j_marti_line_block(
        phase_n=phase_n,
        phase_a=phase_a,
        phase_b=phase_b,
        phase_c=phase_c,
        var_factory=self.var_factory,
        block_type=BlockType.EMT_JMARTI_LINE,
        item_name=item_name,
    )
    block_item: GenericBlockItem = GenericBlockItem(
        editor=self,
        var_factory=self.var_factory,
        subsys=block_model,
        api_object=self.api_object,
        mode=self.mode,
        name=item_name,
        position_changed_callback=self.build_position_changed_callback(block_model.uid)
    )

    if block_model is None:
        return None
    else:
        pass

    self.set_modal_template_metadata(block_model, kind="jmarti_line_emt", config=modal_config)
    set_jmarti_block_fit_bundle(block_model, fit_bundle)
    set_jmarti_block_runtime_data(block_model, None)
    self.block_counters[BlockType.EMT_JMARTI_LINE] = count
    block_item.set_subsystem(block_model)
    block_item.position_changed_callback = self.build_position_changed_callback(block_model.uid)
    block_item.build_item()
    # block_item.setToolTip(self._build_jmarti_modal_tooltip(modal_config))
    self.main_block.add(block_model)
    self.scene.addItem(block_item)
    block_item.setPos(QtCore.QPointF(x_pos, y_pos))
    self.diagram.add_node(
        name=item_name,
        x=x_pos,
        y=y_pos,
        tpe=BlockType.EMT_JMARTI_LINE.name,
        device_uid=block_model.uid,
    )
    self.mark_unapplied_changes()
    return block_item
