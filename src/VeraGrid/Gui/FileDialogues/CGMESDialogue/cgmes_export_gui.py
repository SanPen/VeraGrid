# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cgmes_export_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFrame, QGridLayout, QLabel, QListView,
    QPushButton, QSizePolicy, QSlider, QVBoxLayout,
    QWidget)
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_CgmesExportDialog(object):
    def setupUi(self, CgmesExportDialog):
        if not CgmesExportDialog.objectName():
            CgmesExportDialog.setObjectName(u"CgmesExportDialog")
        CgmesExportDialog.resize(425, 660)
        self.verticalLayout_2 = QVBoxLayout(CgmesExportDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_79 = QFrame(CgmesExportDialog)
        self.frame_79.setObjectName(u"frame_79")
        self.frame_79.setMinimumSize(QSize(300, 0))
        self.frame_79.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_79.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_5 = QGridLayout(self.frame_79)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.label_139 = QLabel(self.frame_79)
        self.label_139.setObjectName(u"label_139")

        self.gridLayout_5.addWidget(self.label_139, 15, 0, 1, 3)

        self.cgmes_version_comboBox = QComboBox(self.frame_79)
        self.cgmes_version_comboBox.setObjectName(u"cgmes_version_comboBox")

        self.gridLayout_5.addWidget(self.cgmes_version_comboBox, 7, 0, 1, 3)

        self.line_31 = QFrame(self.frame_79)
        self.line_31.setObjectName(u"line_31")
        palette = QPalette()
        brush = QBrush(QColor(186, 189, 182, 255))
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush)
        palette.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush)
        brush1 = QBrush(QColor(190, 190, 190, 255))
        brush1.setStyle(Qt.BrushStyle.SolidPattern)
        palette.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, brush1)
        self.line_31.setPalette(palette)
        self.line_31.setFrameShadow(QFrame.Shadow.Plain)
        self.line_31.setLineWidth(4)
        self.line_31.setFrameShape(QFrame.Shape.HLine)

        self.gridLayout_5.addWidget(self.line_31, 1, 0, 1, 3)

        self.selectCGMESBoundarySetButton = QPushButton(self.frame_79)
        self.selectCGMESBoundarySetButton.setObjectName(u"selectCGMESBoundarySetButton")
        self.selectCGMESBoundarySetButton.setMaximumSize(QSize(80, 16777215))

        self.gridLayout_5.addWidget(self.selectCGMESBoundarySetButton, 13, 2, 1, 1)

        self.cgmes_map_regions_like_raw_checkBox = QCheckBox(self.frame_79)
        self.cgmes_map_regions_like_raw_checkBox.setObjectName(u"cgmes_map_regions_like_raw_checkBox")

        self.gridLayout_5.addWidget(self.cgmes_map_regions_like_raw_checkBox, 18, 0, 1, 3)

        self.cgmes_single_profile_per_file_checkBox = QCheckBox(self.frame_79)
        self.cgmes_single_profile_per_file_checkBox.setObjectName(u"cgmes_single_profile_per_file_checkBox")

        self.gridLayout_5.addWidget(self.cgmes_single_profile_per_file_checkBox, 17, 0, 1, 3)

        self.label_135 = QLabel(self.frame_79)
        self.label_135.setObjectName(u"label_135")

        self.gridLayout_5.addWidget(self.label_135, 6, 0, 1, 3)

        self.label_102 = QLabel(self.frame_79)
        self.label_102.setObjectName(u"label_102")

        self.gridLayout_5.addWidget(self.label_102, 14, 0, 1, 1)

        self.label_export_mode = QLabel(self.frame_79)
        self.label_export_mode.setObjectName(u"label_export_mode")

        self.gridLayout_5.addWidget(self.label_export_mode, 2, 0, 1, 3)

        self.cgmes_export_mode_comboBox = QComboBox(self.frame_79)
        self.cgmes_export_mode_comboBox.setObjectName(u"cgmes_export_mode_comboBox")

        self.gridLayout_5.addWidget(self.cgmes_export_mode_comboBox, 3, 0, 1, 3)

        self.label_time_slot = QLabel(self.frame_79)
        self.label_time_slot.setObjectName(u"label_time_slot")

        self.gridLayout_5.addWidget(self.label_time_slot, 4, 0, 1, 3)

        self.time_slot_slider = QSlider(self.frame_79)
        self.time_slot_slider.setObjectName(u"time_slot_slider")
        self.time_slot_slider.setMinimum(-1)
        self.time_slot_slider.setMaximum(-1)
        self.time_slot_slider.setOrientation(Qt.Orientation.Horizontal)

        self.gridLayout_5.addWidget(self.time_slot_slider, 5, 0, 1, 3)

        self.time_slot_label = QLabel(self.frame_79)
        self.time_slot_label.setObjectName(u"time_slot_label")

        self.gridLayout_5.addWidget(self.time_slot_label, 8, 0, 1, 3)

        self.label_134 = QLabel(self.frame_79)
        self.label_134.setObjectName(u"label_134")
        palette1 = QPalette()
        brush2 = QBrush(QColor(85, 87, 83, 255))
        brush2.setStyle(Qt.BrushStyle.SolidPattern)
        palette1.setBrush(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, brush2)
        brush3 = QBrush(QColor(0, 0, 0, 255))
        brush3.setStyle(Qt.BrushStyle.SolidPattern)
        palette1.setBrush(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, brush3)
        palette1.setBrush(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, brush1)
        self.label_134.setPalette(palette1)
        font = QFont()
        font.setPointSize(16)
        self.label_134.setFont(font)

        self.gridLayout_5.addWidget(self.label_134, 0, 1, 1, 2)

        self.label_90 = QLabel(self.frame_79)
        self.label_90.setObjectName(u"label_90")

        self.gridLayout_5.addWidget(self.label_90, 12, 0, 1, 3)

        self.cgmes_dc_as_hvdclines_checkBox = QCheckBox(self.frame_79)
        self.cgmes_dc_as_hvdclines_checkBox.setObjectName(u"cgmes_dc_as_hvdclines_checkBox")

        self.gridLayout_5.addWidget(self.cgmes_dc_as_hvdclines_checkBox, 19, 0, 1, 3)

        self.label_137 = QLabel(self.frame_79)
        self.label_137.setObjectName(u"label_137")
        self.label_137.setMinimumSize(QSize(24, 24))
        self.label_137.setMaximumSize(QSize(24, 24))
        self.label_137.setPixmap(QPixmap(u":/Icons/icons/new2.png"))
        self.label_137.setScaledContents(True)

        self.gridLayout_5.addWidget(self.label_137, 0, 0, 1, 1)

        self.cgmes_profiles_listView = QListView(self.frame_79)
        self.cgmes_profiles_listView.setObjectName(u"cgmes_profiles_listView")

        self.gridLayout_5.addWidget(self.cgmes_profiles_listView, 16, 0, 1, 3)

        self.cgmes_boundary_set_label = QLabel(self.frame_79)
        self.cgmes_boundary_set_label.setObjectName(u"cgmes_boundary_set_label")

        self.gridLayout_5.addWidget(self.cgmes_boundary_set_label, 13, 0, 1, 2)

        self.exportButton = QPushButton(self.frame_79)
        self.exportButton.setObjectName(u"exportButton")

        self.gridLayout_5.addWidget(self.exportButton, 20, 2, 1, 1)


        self.verticalLayout_2.addWidget(self.frame_79)


        self.retranslateUi(CgmesExportDialog)

        QMetaObject.connectSlotsByName(CgmesExportDialog)
    # setupUi

    def retranslateUi(self, CgmesExportDialog):
        CgmesExportDialog.setWindowTitle(QCoreApplication.translate("CgmesExportDialog", u"CGMES Export", None))
        self.label_139.setText(QCoreApplication.translate("CgmesExportDialog", u"Profiles to export", None))
#if QT_CONFIG(tooltip)
        self.selectCGMESBoundarySetButton.setToolTip(QCoreApplication.translate("CgmesExportDialog", u"Select the CGMES boundary set (single zip file)", None))
#endif // QT_CONFIG(tooltip)
        self.selectCGMESBoundarySetButton.setText(QCoreApplication.translate("CgmesExportDialog", u"Select", None))
#if QT_CONFIG(tooltip)
        self.cgmes_map_regions_like_raw_checkBox.setToolTip(QCoreApplication.translate("CgmesExportDialog", u"<html><head/><body><p>If active the CGMEs mapping will be:</p><p>GeographicalRegion &lt;-&gt; Area</p><p>SubGeographicalRegion &lt;-&gt; Zone</p><p>Otherwise:</p><p>GeographicalRegion &lt;-&gt; Country</p><p>SubGeographicalRegion &lt;-&gt; Community</p><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.cgmes_map_regions_like_raw_checkBox.setText(QCoreApplication.translate("CgmesExportDialog", u"Map regions like raw files", None))
        self.cgmes_single_profile_per_file_checkBox.setText(QCoreApplication.translate("CgmesExportDialog", u"One file per profile", None))
        self.label_135.setText(QCoreApplication.translate("CgmesExportDialog", u"Export version", None))
        self.label_102.setText("")
        self.label_export_mode.setText(QCoreApplication.translate("CgmesExportDialog", u"Export mode", None))
        self.label_time_slot.setText(QCoreApplication.translate("CgmesExportDialog", u"Time slot", None))
        self.time_slot_label.setText(QCoreApplication.translate("CgmesExportDialog", u"Snapshot", None))
        self.label_134.setText(QCoreApplication.translate("CgmesExportDialog", u"CGMES", None))
        self.label_90.setText(QCoreApplication.translate("CgmesExportDialog", u"Boundary set", None))
#if QT_CONFIG(tooltip)
        self.cgmes_dc_as_hvdclines_checkBox.setToolTip(QCoreApplication.translate("CgmesExportDialog", u"<html><head/><body><p>Converters and DC lines in CGMES are attempted to be converted to the simplified HvdcLine objects in VeraGrid</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.cgmes_dc_as_hvdclines_checkBox.setText(QCoreApplication.translate("CgmesExportDialog", u"Treat DC equipement as HvdcLines", None))
        self.label_137.setText("")
#if QT_CONFIG(tooltip)
        self.cgmes_boundary_set_label.setToolTip(QCoreApplication.translate("CgmesExportDialog", u"Path of the CGMES default boundary set (single zip file)", None))
#endif // QT_CONFIG(tooltip)
        self.cgmes_boundary_set_label.setText(QCoreApplication.translate("CgmesExportDialog", u"...", None))
        self.exportButton.setText(QCoreApplication.translate("CgmesExportDialog", u"Export", None))
    # retranslateUi
