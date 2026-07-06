from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import WindingType


class TransformerTopologyEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure EMT transformer winding topologies.
    """

    __slots__ = (
        "_static_from_connection",
        "_static_to_connection",
        "from_combo",
        "to_combo",
        "static_from_label",
        "static_to_label",
    )

    def __init__(self,
                 title: str,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None,
                 static_from_connection: WindingType | None = None,
                 static_to_connection: WindingType | None = None) -> None:
        """
        Build the EMT transformer-topology dialog.

        :param title: Window title.
        :param parent: Optional Qt parent.
        :param initial_config: Optional persisted modal configuration.
        :return: None.
        """
        super().__init__(parent)
        self._static_from_connection = static_from_connection
        self._static_to_connection = static_to_connection
        self.setWindowTitle(title)
        self.resize(360, 160)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        form_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(form_layout)

        self.from_combo = QtWidgets.QComboBox(self)
        self.to_combo = QtWidgets.QComboBox(self)

        for combo in (self.from_combo, self.to_combo):
            combo.addItem("Grounded Star (Yg)", WindingType.GroundedStar)
            combo.addItem("Neutral Star (Yn)", WindingType.NeutralStar)
            combo.addItem("Floating Star (Y)", WindingType.FloatingStar)
            combo.addItem("Delta", WindingType.Delta)
            combo.addItem("ZigZag (Z)", WindingType.ZigZag)

        form_layout.addRow("From winding", self.from_combo)
        form_layout.addRow("To winding", self.to_combo)

        self.static_from_label = QtWidgets.QLabel(self)
        self.static_from_label.setWordWrap(True)
        form_layout.addRow("Static from", self.static_from_label)

        self.static_to_label = QtWidgets.QLabel(self)
        self.static_to_label.setWordWrap(True)
        form_layout.addRow("Static to", self.static_to_label)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        if initial_config is not None:
            self.apply_initial_configuration(initial_config)
        else:
            pass

        self._apply_static_connection_state()

    @staticmethod
    def _get_winding_type_label(connection_type: WindingType) -> str:
        """
        Return the user-facing label for one transformer winding type.

        :param connection_type: Static or modal winding type.
        :return: Human-readable label.
        """
        if connection_type == WindingType.GroundedStar:
            return "Grounded Star (Yg)"
        elif connection_type == WindingType.NeutralStar:
            return "Neutral Star (Yn)"
        elif connection_type == WindingType.FloatingStar:
            return "Floating Star (Y)"
        elif connection_type == WindingType.Delta:
            return "Delta"
        elif connection_type == WindingType.ZigZag:
            return "ZigZag (Z)"
        else:
            return str(connection_type)

    def _apply_static_connection_state(self) -> None:
        """
        Enforce the static transformer connection contract in the dialog widgets.

        :return: None.
        """
        if self._static_from_connection is None:
            self.static_from_label.setText("No static from-winding override was resolved for this device.")
            self.from_combo.setEnabled(True)
        else:
            self.static_from_label.setText(
                "Taken from static object: " + self._get_winding_type_label(self._static_from_connection)
            )
            index_from: int = self.from_combo.findData(self._static_from_connection)
            if index_from >= 0:
                self.from_combo.setCurrentIndex(index_from)
            else:
                pass
            self.from_combo.setEnabled(False)

        if self._static_to_connection is None:
            self.static_to_label.setText("No static to-winding override was resolved for this device.")
            self.to_combo.setEnabled(True)
        else:
            self.static_to_label.setText(
                "Taken from static object: " + self._get_winding_type_label(self._static_to_connection)
            )
            index_to: int = self.to_combo.findData(self._static_to_connection)
            if index_to >= 0:
                self.to_combo.setCurrentIndex(index_to)
            else:
                pass
            self.to_combo.setEnabled(False)

    def get_configuration(self) -> dict[str, object]:
        """
        Return the current winding-topology configuration.

        :return: Configuration dictionary.
        """
        return dict({
            "conn_f": self.from_combo.currentData(),
            "conn_t": self.to_combo.currentData(),
        })

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        """
        Load one persisted configuration into the dialog widgets.

        :param config: Persisted configuration.
        :return: None.
        """
        from_conn = config.get("conn_f", WindingType.GroundedStar)
        to_conn = config.get("conn_t", WindingType.GroundedStar)

        index = self.from_combo.findData(from_conn)
        if index >= 0:
            self.from_combo.setCurrentIndex(index)
        else:
            pass

        index = self.to_combo.findData(to_conn)
        if index >= 0:
            self.to_combo.setCurrentIndex(index)
        else:
            pass

        self._apply_static_connection_state()
