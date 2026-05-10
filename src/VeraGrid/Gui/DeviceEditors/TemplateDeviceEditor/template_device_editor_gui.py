# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'template_device_editor_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QSlider, QSpacerItem, QTabWidget,
    QTableView, QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_TemplateDeviceEditorDialog(object):
    def setupUi(self, TemplateDeviceEditorDialog):
        if not TemplateDeviceEditorDialog.objectName():
            TemplateDeviceEditorDialog.setObjectName(u"TemplateDeviceEditorDialog")
        TemplateDeviceEditorDialog.resize(623, 600)
        self.main_layout = QVBoxLayout(TemplateDeviceEditorDialog)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.tab_widget = QTabWidget(TemplateDeviceEditorDialog)
        self.tab_widget.setObjectName(u"tab_widget")
        self.properties_tab = QWidget()
        self.properties_tab.setObjectName(u"properties_tab")
        self.properties_layout = QVBoxLayout(self.properties_tab)
        self.properties_layout.setObjectName(u"properties_layout")
        self.time_controls_frame = QFrame(self.properties_tab)
        self.time_controls_frame.setObjectName(u"time_controls_frame")
        self.time_controls_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.time_controls_frame.setFrameShadow(QFrame.Shadow.Plain)
        self.time_controls_layout = QHBoxLayout(self.time_controls_frame)
        self.time_controls_layout.setObjectName(u"time_controls_layout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.time_controls_layout.addItem(self.horizontalSpacer)

        self.label = QLabel(self.time_controls_frame)
        self.label.setObjectName(u"label")

        self.time_controls_layout.addWidget(self.label)

        self.filterComboBox = QComboBox(self.time_controls_frame)
        self.filterComboBox.setObjectName(u"filterComboBox")

        self.time_controls_layout.addWidget(self.filterComboBox)


        self.properties_layout.addWidget(self.time_controls_frame)

        self.properties_table_view = QTableView(self.properties_tab)
        self.properties_table_view.setObjectName(u"properties_table_view")
        self.properties_table_view.setFrameShape(QFrame.Shape.NoFrame)

        self.properties_layout.addWidget(self.properties_table_view)

        self.frame = QFrame(self.properties_tab)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.time_step_title_label = QLabel(self.frame)
        self.time_step_title_label.setObjectName(u"time_step_title_label")

        self.horizontalLayout.addWidget(self.time_step_title_label)

        self.time_step_slider = QSlider(self.frame)
        self.time_step_slider.setObjectName(u"time_step_slider")
        self.time_step_slider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout.addWidget(self.time_step_slider)

        self.time_step_label = QLabel(self.frame)
        self.time_step_label.setObjectName(u"time_step_label")
        self.time_step_label.setMinimumSize(QSize(260, 0))

        self.horizontalLayout.addWidget(self.time_step_label)


        self.properties_layout.addWidget(self.frame)

        icon = QIcon()
        icon.addFile(u":/Icons/icons/data.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tab_widget.addTab(self.properties_tab, icon, "")
        self.profiles_tab = QWidget()
        self.profiles_tab.setObjectName(u"profiles_tab")
        self.profiles_layout = QVBoxLayout(self.profiles_tab)
        self.profiles_layout.setObjectName(u"profiles_layout")
        self.profiles_tools_frame = QFrame(self.profiles_tab)
        self.profiles_tools_frame.setObjectName(u"profiles_tools_frame")
        self.profiles_tools_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.profiles_tools_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.profiles_tools_layout = QHBoxLayout(self.profiles_tools_frame)
        self.profiles_tools_layout.setObjectName(u"profiles_tools_layout")
        self.profiles_copy_button = QPushButton(self.profiles_tools_frame)
        self.profiles_copy_button.setObjectName(u"profiles_copy_button")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/copy.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.profiles_copy_button.setIcon(icon1)

        self.profiles_tools_layout.addWidget(self.profiles_copy_button)

        self.profiles_paste_button = QPushButton(self.profiles_tools_frame)
        self.profiles_paste_button.setObjectName(u"profiles_paste_button")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/paste.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.profiles_paste_button.setIcon(icon2)

        self.profiles_tools_layout.addWidget(self.profiles_paste_button)

        self.profiles_plot_selected_button = QPushButton(self.profiles_tools_frame)
        self.profiles_plot_selected_button.setObjectName(u"profiles_plot_selected_button")
        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/plot.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.profiles_plot_selected_button.setIcon(icon3)

        self.profiles_tools_layout.addWidget(self.profiles_plot_selected_button)

        self.profiles_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.profiles_tools_layout.addItem(self.profiles_spacer)


        self.profiles_layout.addWidget(self.profiles_tools_frame)

        self.profiles_table_view = QTableView(self.profiles_tab)
        self.profiles_table_view.setObjectName(u"profiles_table_view")
        self.profiles_table_view.setFrameShape(QFrame.Shape.NoFrame)

        self.profiles_layout.addWidget(self.profiles_table_view)

        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/array.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tab_widget.addTab(self.profiles_tab, icon4, "")
        self.associations_tab = QWidget()
        self.associations_tab.setObjectName(u"associations_tab")
        self.associations_layout = QVBoxLayout(self.associations_tab)
        self.associations_layout.setObjectName(u"associations_layout")
        self.associations_controls_frame = QFrame(self.associations_tab)
        self.associations_controls_frame.setObjectName(u"associations_controls_frame")
        self.associations_controls_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.associations_controls_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.associations_controls_layout = QHBoxLayout(self.associations_controls_frame)
        self.associations_controls_layout.setObjectName(u"associations_controls_layout")
        self.associations_property_label = QLabel(self.associations_controls_frame)
        self.associations_property_label.setObjectName(u"associations_property_label")

        self.associations_controls_layout.addWidget(self.associations_property_label)

        self.associations_combo_box = QComboBox(self.associations_controls_frame)
        self.associations_combo_box.setObjectName(u"associations_combo_box")
        self.associations_combo_box.setMinimumSize(QSize(220, 0))

        self.associations_controls_layout.addWidget(self.associations_combo_box)

        self.associations_units_title_label = QLabel(self.associations_controls_frame)
        self.associations_units_title_label.setObjectName(u"associations_units_title_label")

        self.associations_controls_layout.addWidget(self.associations_units_title_label)

        self.associations_units_value_label = QLabel(self.associations_controls_frame)
        self.associations_units_value_label.setObjectName(u"associations_units_value_label")
        self.associations_units_value_label.setMinimumSize(QSize(120, 0))

        self.associations_controls_layout.addWidget(self.associations_units_value_label)

        self.associations_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.associations_controls_layout.addItem(self.associations_spacer)


        self.associations_layout.addWidget(self.associations_controls_frame)

        self.associations_table_view = QTableView(self.associations_tab)
        self.associations_table_view.setObjectName(u"associations_table_view")
        self.associations_table_view.setFrameShape(QFrame.Shape.NoFrame)

        self.associations_layout.addWidget(self.associations_table_view)

        icon5 = QIcon()
        icon5.addFile(u":/Icons/icons/associations.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tab_widget.addTab(self.associations_tab, icon5, "")

        self.main_layout.addWidget(self.tab_widget)


        self.retranslateUi(TemplateDeviceEditorDialog)

        self.tab_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(TemplateDeviceEditorDialog)
    # setupUi

    def retranslateUi(self, TemplateDeviceEditorDialog):
        TemplateDeviceEditorDialog.setWindowTitle(QCoreApplication.translate("TemplateDeviceEditorDialog", u"Device editor", None))
        self.label.setText(QCoreApplication.translate("TemplateDeviceEditorDialog", u"Filter", None))
        self.time_step_title_label.setText(QCoreApplication.translate("TemplateDeviceEditorDialog", u"Time step", None))
        self.time_step_label.setText(QCoreApplication.translate("TemplateDeviceEditorDialog", u"Snapshot", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.properties_tab), QCoreApplication.translate("TemplateDeviceEditorDialog", u"Properties", None))
        self.profiles_copy_button.setText("")
        self.profiles_paste_button.setText("")
        self.profiles_plot_selected_button.setText("")
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.profiles_tab), QCoreApplication.translate("TemplateDeviceEditorDialog", u"Profiles", None))
        self.associations_property_label.setText(QCoreApplication.translate("TemplateDeviceEditorDialog", u"Association", None))
        self.associations_units_title_label.setText(QCoreApplication.translate("TemplateDeviceEditorDialog", u"Units", None))
        self.associations_units_value_label.setText("")
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.associations_tab), QCoreApplication.translate("TemplateDeviceEditorDialog", u"Associations", None))
    # retranslateUi

