from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions


def build_float_spin(minimum: float,
                     maximum: float,
                     decimals: int,
                     step: float) -> QtWidgets.QDoubleSpinBox:
    """Build one configured floating-point spin box.

    :param minimum: Minimum allowed value.
    :param maximum: Maximum allowed value.
    :param decimals: Decimal precision.
    :param step: Single-step size.
    :return: Configured spin box.
    """
    widget: QtWidgets.QDoubleSpinBox = QtWidgets.QDoubleSpinBox()
    widget.setRange(float(minimum), float(maximum))
    widget.setDecimals(int(decimals))
    widget.setSingleStep(float(step))
    widget.setAccelerated(True)
    return widget


def build_int_spin(minimum: int, maximum: int) -> QtWidgets.QSpinBox:
    """Build one configured integer spin box.

    :param minimum: Minimum allowed value.
    :param maximum: Maximum allowed value.
    :return: Configured spin box.
    """
    widget: QtWidgets.QSpinBox = QtWidgets.QSpinBox()
    widget.setRange(int(minimum), int(maximum))
    widget.setAccelerated(True)
    return widget


class JMartiLineEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one EMT J_Marti line block.
    """

    __slots__ = (
        "_phase_checks",
        "_float_inputs",
        "_int_inputs",
        "_bool_inputs",
        "_source_combo",
        "_source_form_layout",
        "_sampling_group",
        "_import_path_edit",
        "_import_path_widget",
        "_import_length_spin",
        "_source_help_label",
        "_status_label",
        "_diagnostics_text",
    )

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None) -> None:
        """
        Build the EMT J_Marti line configuration dialog.

        :param parent: Optional Qt parent.
        :param initial_config: Optional persisted modal configuration.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure EMT J_Marti Line")
        self.resize(700, 860)

        self._phase_checks: dict[str, QtWidgets.QCheckBox] = dict()
        self._float_inputs: dict[str, QtWidgets.QDoubleSpinBox] = dict()
        self._int_inputs: dict[str, QtWidgets.QSpinBox] = dict()
        self._bool_inputs: dict[str, QtWidgets.QCheckBox] = dict()

        options: JMartiFitOptions = JMartiFitOptions()
        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        description_label: QtWidgets.QLabel = QtWidgets.QLabel(
            "Configure the active phases, data source, and offline fitting options for this EMT J_Marti line. "
            "Accepting the dialog rebuilds the fit for the attached line when compatible data are available.",
            self,
        )
        description_label.setWordWrap(True)
        main_layout.addWidget(description_label)

        scroll_area: QtWidgets.QScrollArea = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_container: QtWidgets.QWidget = QtWidgets.QWidget(scroll_area)
        scroll_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(scroll_container)
        scroll_layout.addWidget(self._build_phase_group())
        scroll_layout.addWidget(self._build_data_source_group())
        self._sampling_group = self._build_sampling_group()
        scroll_layout.addWidget(self._sampling_group)
        scroll_layout.addWidget(self._build_window_group(options))
        scroll_layout.addWidget(self._build_fit_group(options))
        scroll_layout.addWidget(self._build_passivity_group(options))
        scroll_layout.addWidget(self._build_diagnostics_group())
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_container)
        main_layout.addWidget(scroll_area)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self._apply_default_values(options)

        if initial_config is not None:
            self.apply_initial_configuration(initial_config)
        else:
            pass

        self.update_source_mode_widgets()

    def _build_phase_group(self) -> QtWidgets.QGroupBox:
        """
        Build the phase-selection group.

        :return: Group box.
        """
        group = QtWidgets.QGroupBox("Active Phases", self)
        layout = QtWidgets.QHBoxLayout(group)

        self._phase_checks["phase_n"] = QtWidgets.QCheckBox("N", group)
        self._phase_checks["phase_a"] = QtWidgets.QCheckBox("A", group)
        self._phase_checks["phase_b"] = QtWidgets.QCheckBox("B", group)
        self._phase_checks["phase_c"] = QtWidgets.QCheckBox("C", group)

        layout.addWidget(self._phase_checks["phase_n"])
        layout.addWidget(self._phase_checks["phase_a"])
        layout.addWidget(self._phase_checks["phase_b"])
        layout.addWidget(self._phase_checks["phase_c"])
        layout.addStretch()
        return group

    def _build_data_source_group(self) -> QtWidgets.QGroupBox:
        """
        Build the data-source group.

        :return: Group box.
        """
        group = QtWidgets.QGroupBox("Data Source", self)
        self._source_form_layout = QtWidgets.QFormLayout(group)

        self._source_combo = QtWidgets.QComboBox(group)
        self._source_combo.addItem("Auto from attached template", "auto_template")
        self._source_combo.addItem("Import NPZ frequency samples", "import_frequency_samples")
        self._source_form_layout.addRow("Source mode", self._source_combo)

        self._float_inputs["nominal_frequency_hz"] = build_float_spin(minimum=0.0, maximum=1.0e9, decimals=4, step=1.0)
        self._source_form_layout.addRow("Nominal frequency [Hz]", self._float_inputs["nominal_frequency_hz"])

        self._import_path_edit = QtWidgets.QLineEdit(group)
        self._import_path_edit.setPlaceholderText(
            "Select one NPZ file with frequency_hz, z_per_length, and y_per_length arrays in pu/m"
        )
        browse_button = QtWidgets.QPushButton("Browse...", group)
        browse_button.clicked.connect(self.browse_import_file)
        self._import_path_widget = QtWidgets.QWidget(group)
        path_layout = QtWidgets.QHBoxLayout(self._import_path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.addWidget(self._import_path_edit)
        path_layout.addWidget(browse_button)
        self._source_form_layout.addRow("NPZ file", self._import_path_widget)

        self._import_length_spin = build_float_spin(minimum=0.0, maximum=1.0e12, decimals=6, step=1.0)
        self._source_form_layout.addRow("Imported line length [m]", self._import_length_spin)

        self._source_help_label = QtWidgets.QLabel(group)
        self._source_help_label.setWordWrap(True)
        self._source_form_layout.addRow("Source notes", self._source_help_label)

        self._source_combo.currentIndexChanged.connect(self.update_source_mode_widgets)
        return group

    def _build_sampling_group(self) -> QtWidgets.QGroupBox:
        """
        Build the sweep-frequency group.

        :return: Group box.
        """
        group = QtWidgets.QGroupBox("Automatic Sweep", self)
        form_layout = QtWidgets.QFormLayout(group)
        self._float_inputs["sweep_low_hz"] = build_float_spin(minimum=0.0, maximum=1.0e9, decimals=4, step=1.0)
        self._float_inputs["sweep_high_hz"] = build_float_spin(minimum=0.0, maximum=1.0e9, decimals=4, step=10.0)
        self._int_inputs["sweep_sample_count"] = build_int_spin(minimum=2, maximum=8192)
        form_layout.addRow("Sweep low [Hz]", self._float_inputs["sweep_low_hz"])
        form_layout.addRow("Sweep high [Hz]", self._float_inputs["sweep_high_hz"])
        form_layout.addRow("Sweep samples", self._int_inputs["sweep_sample_count"])
        return group

    def _build_window_group(self, options: JMartiFitOptions) -> QtWidgets.QGroupBox:
        """
        Build the frequency-window group.

        :param options: Default fit options.
        :return: Group box.
        """
        _unused = options
        group = QtWidgets.QGroupBox("Frequency Windows", self)
        form_layout = QtWidgets.QFormLayout(group)
        self._float_inputs["reference_frequency_hz"] = build_float_spin(minimum=0.0, maximum=1.0e9, decimals=4, step=1.0)
        self._bool_inputs["use_frequency_exploration_window"] = QtWidgets.QCheckBox(group)
        self._float_inputs["exploration_low_hz"] = build_float_spin(minimum=0.0, maximum=1.0e9, decimals=4, step=1.0)
        self._float_inputs["exploration_high_hz"] = build_float_spin(minimum=0.0, maximum=1.0e9, decimals=4, step=10.0)
        self._bool_inputs["use_delay_fit_window"] = QtWidgets.QCheckBox(group)
        self._float_inputs["delay_fit_low_hz"] = build_float_spin(minimum=0.0, maximum=1.0e9, decimals=4, step=1.0)
        self._float_inputs["delay_fit_high_hz"] = build_float_spin(minimum=0.0, maximum=1.0e9, decimals=4, step=10.0)
        form_layout.addRow("Reference frequency [Hz]", self._float_inputs["reference_frequency_hz"])
        form_layout.addRow("Use exploration window", self._bool_inputs["use_frequency_exploration_window"])
        form_layout.addRow("Exploration low [Hz]", self._float_inputs["exploration_low_hz"])
        form_layout.addRow("Exploration high [Hz]", self._float_inputs["exploration_high_hz"])
        form_layout.addRow("Use delay-fit window", self._bool_inputs["use_delay_fit_window"])
        form_layout.addRow("Delay-fit low [Hz]", self._float_inputs["delay_fit_low_hz"])
        form_layout.addRow("Delay-fit high [Hz]", self._float_inputs["delay_fit_high_hz"])
        return group

    def _build_fit_group(self, options: JMartiFitOptions) -> QtWidgets.QGroupBox:
        """
        Build the main fitting-parameter group.

        :param options: Default fit options.
        :return: Group box.
        """
        _unused = options
        group = QtWidgets.QGroupBox("Rational Fit", self)
        form_layout = QtWidgets.QFormLayout(group)
        self._float_inputs["decoupling_warning_tolerance"] = build_float_spin(minimum=0.0, maximum=1.0, decimals=10, step=1.0e-4)
        self._float_inputs["loewner_relative_tolerance"] = build_float_spin(minimum=0.0, maximum=1.0, decimals=12, step=1.0e-8)
        self._int_inputs["maximum_model_order"] = build_int_spin(minimum=1, maximum=2048)
        self._int_inputs["forced_model_order"] = build_int_spin(minimum=0, maximum=2048)
        self._int_inputs["minimum_frequency_samples"] = build_int_spin(minimum=2, maximum=8192)
        self._int_inputs["vf_max_iterations"] = build_int_spin(minimum=1, maximum=1024)
        self._float_inputs["vf_pole_shift_tolerance"] = build_float_spin(minimum=0.0, maximum=1.0, decimals=12, step=1.0e-8)
        self._bool_inputs["vf_enforce_stable_poles"] = QtWidgets.QCheckBox(group)
        self._float_inputs["vf_stability_real_part_floor"] = build_float_spin(minimum=0.0, maximum=1.0e6, decimals=12, step=1.0e-8)
        self._bool_inputs["vf_include_constant_term"] = QtWidgets.QCheckBox(group)
        self._bool_inputs["vf_include_proportional_term"] = QtWidgets.QCheckBox(group)
        form_layout.addRow("Decoupling warning tol.", self._float_inputs["decoupling_warning_tolerance"])
        form_layout.addRow("Loewner relative tol.", self._float_inputs["loewner_relative_tolerance"])
        form_layout.addRow("Maximum model order", self._int_inputs["maximum_model_order"])
        form_layout.addRow("Forced model order", self._int_inputs["forced_model_order"])
        form_layout.addRow("Minimum frequency samples", self._int_inputs["minimum_frequency_samples"])
        form_layout.addRow("VF max iterations", self._int_inputs["vf_max_iterations"])
        form_layout.addRow("VF pole-shift tol.", self._float_inputs["vf_pole_shift_tolerance"])
        form_layout.addRow("Enforce stable poles", self._bool_inputs["vf_enforce_stable_poles"])
        form_layout.addRow("Stability real-part floor", self._float_inputs["vf_stability_real_part_floor"])
        form_layout.addRow("Include constant term", self._bool_inputs["vf_include_constant_term"])
        form_layout.addRow("Include proportional term", self._bool_inputs["vf_include_proportional_term"])
        return group

    def _build_passivity_group(self, options: JMartiFitOptions) -> QtWidgets.QGroupBox:
        """
        Build the passivity-check group.

        :param options: Default fit options.
        :return: Group box.
        """
        _unused = options
        group = QtWidgets.QGroupBox("Passivity Checks", self)
        form_layout = QtWidgets.QFormLayout(group)
        self._int_inputs["passivity_frequency_sample_count"] = build_int_spin(minimum=2, maximum=65536)
        self._float_inputs["passivity_minimum_real_yc_tolerance"] = build_float_spin(minimum=0.0, maximum=1.0, decimals=12, step=1.0e-8)
        self._float_inputs["passivity_maximum_hres_gain_tolerance"] = build_float_spin(minimum=0.0, maximum=1.0, decimals=12, step=1.0e-8)
        form_layout.addRow("Check sample count", self._int_inputs["passivity_frequency_sample_count"])
        form_layout.addRow("Minimum Re(Yc) tol.", self._float_inputs["passivity_minimum_real_yc_tolerance"])
        form_layout.addRow("Maximum |Hres|-1 tol.", self._float_inputs["passivity_maximum_hres_gain_tolerance"])
        return group

    def _build_diagnostics_group(self) -> QtWidgets.QGroupBox:
        """
        Build the last-fit diagnostics group.

        :return: Group box.
        """
        group = QtWidgets.QGroupBox("Last Fit Diagnostics", self)
        layout = QtWidgets.QVBoxLayout(group)
        self._status_label = QtWidgets.QLabel(
            "Fit not computed yet. Accept the dialog to build or refresh the JMARTI fit for the attached line.",
            group,
        )
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        self._diagnostics_text = QtWidgets.QPlainTextEdit(group)
        self._diagnostics_text.setReadOnly(True)
        self._diagnostics_text.setPlaceholderText("Detailed fit diagnostics will be stored here after one successful fit.")
        layout.addWidget(self._diagnostics_text)
        return group

    def _apply_default_values(self, options: JMartiFitOptions) -> None:
        """
        Populate the widgets with one coherent default configuration.

        :param options: Default fit options.
        :return: None.
        """
        self._phase_checks["phase_n"].setChecked(False)
        self._phase_checks["phase_a"].setChecked(True)
        self._phase_checks["phase_b"].setChecked(True)
        self._phase_checks["phase_c"].setChecked(True)

        self._source_combo.setCurrentIndex(self._source_combo.findData("auto_template"))
        self._float_inputs["nominal_frequency_hz"].setValue(50.0)
        self._import_path_edit.setText("")
        self._import_length_spin.setValue(0.0)

        self._float_inputs["sweep_low_hz"].setValue(10.0)
        self._float_inputs["sweep_high_hz"].setValue(10000.0)
        self._int_inputs["sweep_sample_count"].setValue(48)

        self._float_inputs["reference_frequency_hz"].setValue(options.reference_frequency_hz)
        self._bool_inputs["use_frequency_exploration_window"].setChecked(options.use_frequency_exploration_window)
        self._float_inputs["exploration_low_hz"].setValue(options.exploration_low_hz)
        self._float_inputs["exploration_high_hz"].setValue(options.exploration_high_hz)
        self._bool_inputs["use_delay_fit_window"].setChecked(options.use_delay_fit_window)
        self._float_inputs["delay_fit_low_hz"].setValue(options.delay_fit_low_hz)
        self._float_inputs["delay_fit_high_hz"].setValue(options.delay_fit_high_hz)
        self._float_inputs["decoupling_warning_tolerance"].setValue(options.decoupling_warning_tolerance)
        self._float_inputs["loewner_relative_tolerance"].setValue(options.loewner_relative_tolerance)
        self._int_inputs["maximum_model_order"].setValue(options.maximum_model_order)
        self._int_inputs["forced_model_order"].setValue(options.forced_model_order)
        self._int_inputs["minimum_frequency_samples"].setValue(options.minimum_frequency_samples)
        self._int_inputs["vf_max_iterations"].setValue(options.vf_max_iterations)
        self._float_inputs["vf_pole_shift_tolerance"].setValue(options.vf_pole_shift_tolerance)
        self._bool_inputs["vf_enforce_stable_poles"].setChecked(options.vf_enforce_stable_poles)
        self._float_inputs["vf_stability_real_part_floor"].setValue(options.vf_stability_real_part_floor)
        self._bool_inputs["vf_include_constant_term"].setChecked(options.vf_include_constant_term)
        self._bool_inputs["vf_include_proportional_term"].setChecked(options.vf_include_proportional_term)
        self._int_inputs["passivity_frequency_sample_count"].setValue(options.passivity_frequency_sample_count)
        self._float_inputs["passivity_minimum_real_yc_tolerance"].setValue(options.passivity_minimum_real_yc_tolerance)
        self._float_inputs["passivity_maximum_hres_gain_tolerance"].setValue(options.passivity_maximum_hres_gain_tolerance)
        self._status_label.setText(
            "Fit not computed yet. Accept the dialog to build or refresh the JMARTI fit for the attached line."
        )
        self._diagnostics_text.setPlainText("")

    def _set_source_row_visible(self, field_widget: QtWidgets.QWidget, visible: bool) -> None:
        """
        Show or hide one row in the source form layout.

        :param field_widget: Row field widget.
        :param visible: Whether the row should be visible.
        :return: None.
        """
        field_widget.setVisible(visible)
        label_widget = self._source_form_layout.labelForField(field_widget)

        if label_widget is not None:
            label_widget.setVisible(visible)
        else:
            pass

    def update_source_mode_widgets(self) -> None:
        """
        Refresh the dialog widgets for the selected data source.

        :return: None.
        """
        import_mode_enabled: bool = self._source_combo.currentData() == "import_frequency_samples"
        self._set_source_row_visible(self._import_path_widget, import_mode_enabled)
        self._set_source_row_visible(self._import_length_spin, import_mode_enabled)
        self._float_inputs["nominal_frequency_hz"].setEnabled(not import_mode_enabled)
        self._sampling_group.setEnabled(not import_mode_enabled)

        if import_mode_enabled:
            self._source_help_label.setText(
                "Import one NPZ archive with arrays 'frequency_hz', 'z_per_length', and 'y_per_length'. "
                "Optional arrays are 'phase_labels' and 'line_length_m'. The file may also provide real/imag pairs "
                "under 'z_per_length_real'/'z_per_length_imag' and 'y_per_length_real'/'y_per_length_imag'. "
                "The imported Z/Y arrays are expected in per-unit per meter."
            )
        else:
            self._source_help_label.setText(
                "Automatic mode builds the frequency sweep from the attached line template. Overhead templates use "
                "their conductor geometry when available. Sequence and underground templates use one nominal RLGC reconstruction."
            )

    def browse_import_file(self) -> None:
        """
        Open one file dialog to select the imported JMARTI NPZ file.

        :return: None.
        """
        file_path, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open JMARTI Frequency Samples",
            "",
            "NumPy archive (*.npz)",
        )

        if file_path:
            self._import_path_edit.setText(file_path)
        else:
            pass

    def accept_dialog(self) -> None:
        """
        Validate the dialog state before accepting.

        :return: None.
        """
        sweep_low_hz: float = float(self._float_inputs["sweep_low_hz"].value())
        sweep_high_hz: float = float(self._float_inputs["sweep_high_hz"].value())
        minimum_frequency_samples: int = int(self._int_inputs["minimum_frequency_samples"].value())
        sweep_sample_count: int = int(self._int_inputs["sweep_sample_count"].value())
        forced_model_order: int = int(self._int_inputs["forced_model_order"].value())
        maximum_model_order: int = int(self._int_inputs["maximum_model_order"].value())
        import_mode_enabled: bool = self._source_combo.currentData() == "import_frequency_samples"

        if self._phase_checks["phase_a"].isChecked() or self._phase_checks["phase_b"].isChecked() or self._phase_checks["phase_c"].isChecked() or self._phase_checks["phase_n"].isChecked():
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "EMT J_Marti line", "Enable at least one phase.")
            return

        if import_mode_enabled:
            if self._import_path_edit.text().strip():
                pass
            else:
                QtWidgets.QMessageBox.warning(self, "EMT J_Marti line", "Select one NPZ file to import frequency samples.")
                return
        else:
            if sweep_high_hz > sweep_low_hz:
                pass
            else:
                QtWidgets.QMessageBox.warning(self, "EMT J_Marti line", "The sweep upper frequency must be greater than the lower frequency.")
                return

            if sweep_sample_count >= minimum_frequency_samples:
                pass
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "EMT J_Marti line",
                    "The sweep sample count must be greater than or equal to the minimum frequency sample requirement.",
                )
                return

        if forced_model_order == 0 or forced_model_order <= maximum_model_order:
            pass
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "EMT J_Marti line",
                "The forced model order must be zero or less than or equal to the maximum model order.",
            )
            return

        if self._bool_inputs["use_frequency_exploration_window"].isChecked():
            if import_mode_enabled:
                if self._validate_window_bounds_only("exploration_low_hz", "exploration_high_hz", "exploration"):
                    pass
                else:
                    return
            elif self._validate_window("exploration_low_hz", "exploration_high_hz", sweep_low_hz, sweep_high_hz, "exploration"):
                pass
            else:
                return
        else:
            pass

        if self._bool_inputs["use_delay_fit_window"].isChecked():
            if import_mode_enabled:
                if self._validate_window_bounds_only("delay_fit_low_hz", "delay_fit_high_hz", "delay-fit"):
                    pass
                else:
                    return
            elif self._validate_window("delay_fit_low_hz", "delay_fit_high_hz", sweep_low_hz, sweep_high_hz, "delay-fit"):
                pass
            else:
                return
        else:
            pass

        self.accept()

    def _validate_window(self,
                         low_key: str,
                         high_key: str,
                         sweep_low_hz: float,
                         sweep_high_hz: float,
                         window_name: str) -> bool:
        """
        Validate one optional frequency window against the full sweep.

        :param low_key: Lower-bound widget key.
        :param high_key: Upper-bound widget key.
        :param sweep_low_hz: Sweep lower bound.
        :param sweep_high_hz: Sweep upper bound.
        :param window_name: User-facing window label.
        :return: ``True`` when the window is valid.
        """
        low_hz: float = float(self._float_inputs[low_key].value())
        high_hz: float = float(self._float_inputs[high_key].value())

        if high_hz > low_hz:
            pass
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "EMT J_Marti line",
                f"The {window_name} upper frequency must be greater than the lower frequency.",
            )
            return False

        if low_hz >= sweep_low_hz and high_hz <= sweep_high_hz:
            return True
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "EMT J_Marti line",
                f"The {window_name} window must stay inside the configured sweep band.",
            )
            return False

    def _validate_window_bounds_only(self,
                                     low_key: str,
                                     high_key: str,
                                     window_name: str) -> bool:
        """
        Validate only the monotonicity of one imported-data frequency window.

        :param low_key: Lower-bound widget key.
        :param high_key: Upper-bound widget key.
        :param window_name: User-facing window label.
        :return: ``True`` when the window is valid.
        """
        low_hz: float = float(self._float_inputs[low_key].value())
        high_hz: float = float(self._float_inputs[high_key].value())

        if high_hz > low_hz:
            return True
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "EMT J_Marti line",
                f"The {window_name} upper frequency must be greater than the lower frequency.",
            )
            return False

    def get_configuration(self) -> dict[str, object]:
        """
        Return the current dialog configuration.

        :return: Serializable configuration dictionary.
        """
        config: dict[str, object] = dict()
        key_name: str

        for key_name, widget in self._phase_checks.items():
            config[key_name] = bool(widget.isChecked())

        for key_name, widget in self._float_inputs.items():
            config[key_name] = float(widget.value())

        for key_name, widget in self._int_inputs.items():
            config[key_name] = int(widget.value())

        for key_name, widget in self._bool_inputs.items():
            config[key_name] = bool(widget.isChecked())

        config["data_source_mode"] = str(self._source_combo.currentData())
        config["import_file_path"] = str(self._import_path_edit.text())
        config["import_line_length_m"] = float(self._import_length_spin.value())
        config["fit_status"] = str(self._status_label.text())
        config["fit_diagnostics_text"] = str(self._diagnostics_text.toPlainText())
        return config

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        """
        Load one persisted configuration into the dialog widgets.

        :param config: Persisted modal configuration.
        :return: None.
        """
        key_name: str

        for key_name, widget in self._phase_checks.items():
            if key_name in config:
                widget.setChecked(bool(config[key_name]))
            else:
                pass

        for key_name, widget in self._float_inputs.items():
            if key_name in config:
                widget.setValue(float(config[key_name]))
            else:
                pass

        for key_name, widget in self._int_inputs.items():
            if key_name in config:
                widget.setValue(int(config[key_name]))
            else:
                pass

        for key_name, widget in self._bool_inputs.items():
            if key_name in config:
                widget.setChecked(bool(config[key_name]))
            else:
                pass

        if "data_source_mode" in config:
            source_index: int = self._source_combo.findData(str(config["data_source_mode"]))
            if source_index >= 0:
                self._source_combo.setCurrentIndex(source_index)
            else:
                pass
        else:
            pass

        if "import_file_path" in config:
            self._import_path_edit.setText(str(config["import_file_path"]))
        else:
            pass

        if "import_line_length_m" in config:
            self._import_length_spin.setValue(float(config["import_line_length_m"]))
        else:
            pass

        if "fit_status" in config:
            self._status_label.setText(str(config["fit_status"]))
        else:
            pass

        if "fit_diagnostics_text" in config:
            self._diagnostics_text.setPlainText(str(config["fit_diagnostics_text"]))
        else:
            pass

        self.update_source_mode_widgets()
