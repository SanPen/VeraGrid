from __future__ import annotations

from PySide6 import QtWidgets

from VeraGridEngine.enumerations import WindingType


class TransformerTopologyEmtDialog(QtWidgets.QDialog):
    """
    Modal dialog used to configure EMT transformer winding topologies.
    """

    __slots__ = (
        "from_combo",
        "to_combo",
    )

    def __init__(self,
                 title: str,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None) -> None:
        """
        Build the EMT transformer-topology dialog.

        :param title: Window title.
        :param parent: Optional Qt parent.
        :param initial_config: Optional persisted modal configuration.
        :return: None.
        """
        super().__init__(parent)
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
