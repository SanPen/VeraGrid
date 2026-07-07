# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)


class Ui_VscDeviceEditorWidget(object):
    def setupUi(self, VscDeviceEditorWidget):
        if not VscDeviceEditorWidget.objectName():
            VscDeviceEditorWidget.setObjectName("VscDeviceEditorWidget")
        VscDeviceEditorWidget.resize(620, 260)

        self.main_layout = QVBoxLayout(VscDeviceEditorWidget)
        self.main_layout.setObjectName("main_layout")

        self.summary_frame = QFrame(VscDeviceEditorWidget)
        self.summary_frame.setObjectName("summary_frame")
        self.summary_form_layout = QFormLayout(self.summary_frame)
        self.summary_form_layout.setObjectName("summary_form_layout")

        self.bus_ac_title_label = QLabel(self.summary_frame)
        self.bus_ac_title_label.setObjectName("bus_ac_title_label")
        self.summary_form_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.bus_ac_title_label)
        self.bus_ac_value_label = QLabel(self.summary_frame)
        self.bus_ac_value_label.setObjectName("bus_ac_value_label")
        self.summary_form_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.bus_ac_value_label)

        self.bus_dc_plus_title_label = QLabel(self.summary_frame)
        self.bus_dc_plus_title_label.setObjectName("bus_dc_plus_title_label")
        self.summary_form_layout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.bus_dc_plus_title_label)
        self.bus_dc_plus_value_label = QLabel(self.summary_frame)
        self.bus_dc_plus_value_label.setObjectName("bus_dc_plus_value_label")
        self.summary_form_layout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.bus_dc_plus_value_label)

        self.bus_dc_minus_title_label = QLabel(self.summary_frame)
        self.bus_dc_minus_title_label.setObjectName("bus_dc_minus_title_label")
        self.summary_form_layout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.bus_dc_minus_title_label)
        self.bus_dc_minus_value_label = QLabel(self.summary_frame)
        self.bus_dc_minus_value_label.setObjectName("bus_dc_minus_value_label")
        self.summary_form_layout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.bus_dc_minus_value_label)

        self.control_1_title_label = QLabel(self.summary_frame)
        self.control_1_title_label.setObjectName("control_1_title_label")
        self.summary_form_layout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.control_1_title_label)
        self.control_1_value_label = QLabel(self.summary_frame)
        self.control_1_value_label.setObjectName("control_1_value_label")
        self.summary_form_layout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.control_1_value_label)

        self.control_2_title_label = QLabel(self.summary_frame)
        self.control_2_title_label.setObjectName("control_2_title_label")
        self.summary_form_layout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.control_2_title_label)
        self.control_2_value_label = QLabel(self.summary_frame)
        self.control_2_value_label.setObjectName("control_2_value_label")
        self.summary_form_layout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.control_2_value_label)

        self.fault_control_title_label = QLabel(self.summary_frame)
        self.fault_control_title_label.setObjectName("fault_control_title_label")
        self.summary_form_layout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.fault_control_title_label)
        self.fault_control_value_label = QLabel(self.summary_frame)
        self.fault_control_value_label.setObjectName("fault_control_value_label")
        self.summary_form_layout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.fault_control_value_label)

        self.main_layout.addWidget(self.summary_frame)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setObjectName("buttons_layout")

        self.refresh_button = QPushButton(VscDeviceEditorWidget)
        self.refresh_button.setObjectName("refresh_button")
        self.buttons_layout.addWidget(self.refresh_button)

        self.rms_button = QPushButton(VscDeviceEditorWidget)
        self.rms_button.setObjectName("rms_button")
        self.buttons_layout.addWidget(self.rms_button)

        self.emt_button = QPushButton(VscDeviceEditorWidget)
        self.emt_button.setObjectName("emt_button")
        self.buttons_layout.addWidget(self.emt_button)

        self.buttons_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.buttons_layout.addItem(self.buttons_spacer)
        self.main_layout.addLayout(self.buttons_layout)

        self.vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.main_layout.addItem(self.vertical_spacer)

        self.retranslateUi(VscDeviceEditorWidget)
        QMetaObject.connectSlotsByName(VscDeviceEditorWidget)

    def retranslateUi(self, VscDeviceEditorWidget):
        VscDeviceEditorWidget.setWindowTitle(QCoreApplication.translate("VscDeviceEditorWidget", "VSC", None))
        self.bus_ac_title_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "AC bus", None))
        self.bus_ac_value_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "", None))
        self.bus_dc_plus_title_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "DC+ bus", None))
        self.bus_dc_plus_value_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "", None))
        self.bus_dc_minus_title_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "DC- bus", None))
        self.bus_dc_minus_value_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "", None))
        self.control_1_title_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "Control 1", None))
        self.control_1_value_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "", None))
        self.control_2_title_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "Control 2", None))
        self.control_2_value_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "", None))
        self.fault_control_title_label.setText(
            QCoreApplication.translate("VscDeviceEditorWidget", "Fault control", None)
        )
        self.fault_control_value_label.setText(QCoreApplication.translate("VscDeviceEditorWidget", "", None))
        self.refresh_button.setText(QCoreApplication.translate("VscDeviceEditorWidget", "Refresh summary", None))
        self.rms_button.setText(QCoreApplication.translate("VscDeviceEditorWidget", "Open RMS editor", None))
        self.emt_button.setText(QCoreApplication.translate("VscDeviceEditorWidget", "Open EMT editor", None))
