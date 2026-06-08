from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import ShuntConnectionType


class LoadTopologyEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure one EMT load topology block.
    """

    __slots__ = (
        "_static_connection_type",
        "_allow_static_device_values",
        "phase_a_check",
        "phase_b_check",
        "phase_c_check",
        "connection_combo",
        "static_connection_label",
        "use_static_device_values_check",
    )

    def __init__(self,
                 title: str,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None,
                 allow_static_device_values: bool = False,
                 static_connection_type: ShuntConnectionType | None = None) -> None:
        """
        Build the EMT load-topology configuration dialog.

        :param title: Window title.
        :param parent: Optional Qt parent.
        :param initial_config: Optional persisted modal configuration.
        :return: None.
        """
        super().__init__(parent)
        self._static_connection_type = static_connection_type
        self._allow_static_device_values = allow_static_device_values
        self.setWindowTitle(title)
        self.resize(360, 180)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        form_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(form_layout)

        phase_widget = QtWidgets.QWidget(self)
        phase_layout = QtWidgets.QHBoxLayout(phase_widget)
        phase_layout.setContentsMargins(0, 0, 0, 0)
        self.phase_a_check = QtWidgets.QCheckBox("A", phase_widget)
        self.phase_b_check = QtWidgets.QCheckBox("B", phase_widget)
        self.phase_c_check = QtWidgets.QCheckBox("C", phase_widget)
        self.phase_a_check.setChecked(True)
        self.phase_b_check.setChecked(True)
        self.phase_c_check.setChecked(True)
        phase_layout.addWidget(self.phase_a_check)
        phase_layout.addWidget(self.phase_b_check)
        phase_layout.addWidget(self.phase_c_check)
        phase_layout.addStretch()
        form_layout.addRow("Phases", phase_widget)

        self.connection_combo = QtWidgets.QComboBox(self)
        self.connection_combo.addItem("Grounded Star (Yg)", ShuntConnectionType.GroundedStar)
        self.connection_combo.addItem("Neutral Star (Yn)", ShuntConnectionType.NeutralStar)
        self.connection_combo.addItem("Floating Star (Y)", ShuntConnectionType.FloatingStar)
        self.connection_combo.addItem("Delta", ShuntConnectionType.Delta)
        form_layout.addRow("Connection", self.connection_combo)

        self.static_connection_label = QtWidgets.QLabel(self)
        self.static_connection_label.setWordWrap(True)
        form_layout.addRow("Static connection", self.static_connection_label)

        self.use_static_device_values_check = QtWidgets.QCheckBox("Use static device connection", self)
        self.use_static_device_values_check.setEnabled(self._allow_static_device_values)
        self.use_static_device_values_check.setChecked(False)
        form_layout.addRow("Connection Source", self.use_static_device_values_check)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.use_static_device_values_check.toggled.connect(self.update_connection_widgets)

        if initial_config is not None:
            self.apply_initial_configuration(initial_config)
        else:
            pass

        self._apply_static_connection_state()

    @staticmethod
    def _get_connection_type_label(connection_type: ShuntConnectionType) -> str:
        """
        Return the user-facing label for one shunt connection type.

        :param connection_type: Static or modal shunt connection type.
        :return: Human-readable label.
        """
        if connection_type == ShuntConnectionType.GroundedStar:
            return "Grounded Star (Yg)"
        elif connection_type == ShuntConnectionType.NeutralStar:
            return "Neutral Star (Yn)"
        elif connection_type == ShuntConnectionType.FloatingStar:
            return "Floating Star (Y)"
        elif connection_type == ShuntConnectionType.Delta:
            return "Delta"
        else:
            return str(connection_type)

    def _apply_static_connection_state(self) -> None:
        """
        Enforce the static connection contract in the dialog widgets.

        :return: None.
        """
        if self._static_connection_type is None:
            self.static_connection_label.setText("No static connection override was resolved for this device.")
            self.connection_combo.setEnabled(True)
        else:
            self.static_connection_label.setText(
                "Static object connection available: " + self._get_connection_type_label(self._static_connection_type)
            )
            if self.use_static_device_values_check.isChecked():
                index: int = self.connection_combo.findData(self._static_connection_type)
                if index >= 0:
                    self.connection_combo.setCurrentIndex(index)
                else:
                    pass
            else:
                pass
            self.connection_combo.setEnabled(not self.use_static_device_values_check.isChecked())

    def update_connection_widgets(self) -> None:
        """
        Refresh the connection editor state for the current source mode.

        :return: None.
        """
        self._apply_static_connection_state()

    def accept_dialog(self) -> None:
        """
        Validate the modal state before accepting.

        :return: None.
        """
        if self.phase_a_check.isChecked() or self.phase_b_check.isChecked() or self.phase_c_check.isChecked():
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "EMT Load", "Enable at least one phase.")

    def get_configuration(self) -> dict[str, object]:
        """
        Return the current modal configuration.

        :return: Configuration dictionary.
        """
        return dict({
            "phA": self.phase_a_check.isChecked(),
            "phB": self.phase_b_check.isChecked(),
            "phC": self.phase_c_check.isChecked(),
            "connection_type": self.connection_combo.currentData(),
            "use_static_device_values": self.use_static_device_values_check.isChecked(),
        })

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        """
        Load one persisted configuration into the dialog widgets.

        :param config: Persisted configuration.
        :return: None.
        """
        self.phase_a_check.setChecked(bool(config.get("phA", True)))
        self.phase_b_check.setChecked(bool(config.get("phB", True)))
        self.phase_c_check.setChecked(bool(config.get("phC", True)))
        self.use_static_device_values_check.setChecked(bool(config.get("use_static_device_values", False)) and self._allow_static_device_values)

        connection_type = config.get("connection_type", ShuntConnectionType.GroundedStar)
        index = self.connection_combo.findData(connection_type)
        if index >= 0:
            self.connection_combo.setCurrentIndex(index)
        else:
            pass

        self.update_connection_widgets()
