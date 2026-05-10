# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum

from PySide6 import QtWidgets


class InductionMotorEmtLevel(Enum):
    """Enumeration of the supported induction-motor EMT template levels."""

    SINGLE_CAGE = 2
    DOUBLE_CAGE = 3


def coerce_induction_motor_emt_level(value: object) -> InductionMotorEmtLevel:
    """Convert one persisted configuration value into an induction-motor level.

    :param value: Persisted modal value.
    :return: Parsed induction-motor level.
    :raises ValueError: If the value cannot be converted.
    """
    if isinstance(value, InductionMotorEmtLevel):
        return value
    elif isinstance(value, str):
        try:
            return InductionMotorEmtLevel[value]
        except KeyError as exc:
            raise ValueError(f"Unsupported induction motor EMT level value '{value}'") from exc
    elif isinstance(value, int):
        try:
            return InductionMotorEmtLevel(value)
        except ValueError as exc:
            raise ValueError(f"Unsupported induction motor EMT level value '{value}'") from exc
    else:
        raise ValueError(f"Unsupported induction motor EMT level value '{value}'")


def get_induction_motor_emt_level_label(level: InductionMotorEmtLevel) -> str:
    """Return the user-facing label for one induction-motor level.

    :param level: Selected template level.
    :return: Short descriptive label.
    """
    if level == InductionMotorEmtLevel.SINGLE_CAGE:
        return "Level 2: single cage"
    elif level == InductionMotorEmtLevel.DOUBLE_CAGE:
        return "Level 3: double cage"
    else:
        raise ValueError(f"Unsupported induction motor EMT level '{level}'")


def get_induction_motor_emt_template_level(level: InductionMotorEmtLevel) -> int:
    """Return the builder level code for one induction-motor level.

    :param level: Selected template level.
    :return: Integer level accepted by the EMT template builder.
    """
    if level == InductionMotorEmtLevel.SINGLE_CAGE:
        return 2
    elif level == InductionMotorEmtLevel.DOUBLE_CAGE:
        return 3
    else:
        raise ValueError(f"Unsupported induction motor EMT level '{level}'")


class InductionMotorEmtDialog(QtWidgets.QDialog):
    """Modal dialog used to configure one induction-motor EMT block."""

    __slots__ = (
        "level_combo",
        "description_label",
    )

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 initial_config: dict[str, object] | None = None) -> None:
        """Build the induction-motor EMT configuration dialog.

        :param parent: Optional Qt parent.
        :param initial_config: Optional persisted modal configuration.
        :return: None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure Induction Motor EMT")
        self.resize(360, 160)

        main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        form_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(form_layout)

        self.level_combo = QtWidgets.QComboBox(self)
        self.level_combo.addItem(
            get_induction_motor_emt_level_label(InductionMotorEmtLevel.SINGLE_CAGE),
            InductionMotorEmtLevel.SINGLE_CAGE,
        )
        self.level_combo.addItem(
            get_induction_motor_emt_level_label(InductionMotorEmtLevel.DOUBLE_CAGE),
            InductionMotorEmtLevel.DOUBLE_CAGE,
        )
        form_layout.addRow("Template level", self.level_combo)

        self.description_label = QtWidgets.QLabel(
            "Select the induction motor EMT fidelity level before the block is created.",
            self,
        )
        self.description_label.setWordWrap(True)
        main_layout.addWidget(self.description_label)

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
        """Return the current modal configuration.

        :return: Persistable configuration dictionary.
        """
        selected_level: InductionMotorEmtLevel = self.level_combo.currentData()
        return dict({"level": selected_level.name})

    def apply_initial_configuration(self, config: dict[str, object]) -> None:
        """Load one persisted configuration into the dialog widgets.

        :param config: Persisted configuration.
        :return: None.
        """
        selected_level: InductionMotorEmtLevel = coerce_induction_motor_emt_level(
            config.get("level", InductionMotorEmtLevel.SINGLE_CAGE.name)
        )
        index: int = self.level_combo.findData(selected_level)

        if index >= 0:
            self.level_combo.setCurrentIndex(index)
        else:
            raise ValueError(f"Unsupported induction motor EMT level '{selected_level}'")
