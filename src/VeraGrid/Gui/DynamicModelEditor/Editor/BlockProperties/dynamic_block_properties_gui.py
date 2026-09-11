# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dynamic_block_properties.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog,
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QSizePolicy,
    QSpacerItem, QTabWidget, QTableView, QToolBox,
    QToolButton, QTreeView, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_DynamicBlockPropertiesDialog(object):
    def setupUi(self, DynamicBlockPropertiesDialog):
        if not DynamicBlockPropertiesDialog.objectName():
            DynamicBlockPropertiesDialog.setObjectName(u"DynamicBlockPropertiesDialog")
        DynamicBlockPropertiesDialog.resize(701, 557)
        self.main_layout = QVBoxLayout(DynamicBlockPropertiesDialog)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.tab_widget = QTabWidget(DynamicBlockPropertiesDialog)
        self.tab_widget.setObjectName(u"tab_widget")
        self.general_page = QWidget()
        self.general_page.setObjectName(u"general_page")
        self.verticalLayout_3 = QVBoxLayout(self.general_page)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.property_tools_panel = QWidget(self.general_page)
        self.property_tools_panel.setObjectName(u"property_tools_panel")
        self.verticalLayout_4 = QVBoxLayout(self.property_tools_panel)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.property_tree_panel = QWidget(self.property_tools_panel)
        self.property_tree_panel.setObjectName(u"property_tree_panel")
        self.property_tree_panel.setMinimumSize(QSize(260, 0))
        self.property_tree_layout = QVBoxLayout(self.property_tree_panel)
        self.property_tree_layout.setObjectName(u"property_tree_layout")
        self.property_tree_layout.setContentsMargins(0, 0, 0, 0)
        self.property_search = QLineEdit(self.property_tree_panel)
        self.property_search.setObjectName(u"property_search")
        self.property_search.setClearButtonEnabled(True)

        self.property_tree_layout.addWidget(self.property_search)

        self.property_tree = QTreeView(self.property_tree_panel)
        self.property_tree.setObjectName(u"property_tree")
        self.property_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.property_tree.setFrameShape(QFrame.Shape.NoFrame)
        self.property_tree.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked|QAbstractItemView.EditTrigger.EditKeyPressed)
        self.property_tree.setAlternatingRowColors(True)
        self.property_tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.property_tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.property_tree.setRootIsDecorated(True)
        self.property_tree.setUniformRowHeights(True)
        self.property_tree.setItemsExpandable(True)

        self.property_tree_layout.addWidget(self.property_tree)


        self.verticalLayout_4.addWidget(self.property_tree_panel)


        self.verticalLayout_3.addWidget(self.property_tools_panel)

        icon = QIcon()
        icon.addFile(u":/Icons/icons/gear.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tab_widget.addTab(self.general_page, icon, "")
        self.dae_model_page = QWidget()
        self.dae_model_page.setObjectName(u"dae_model_page")
        self.verticalLayout = QVBoxLayout(self.dae_model_page)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_2 = QFrame(self.dae_model_page)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.procedural_add_button = QPushButton(self.frame_2)
        self.procedural_add_button.setObjectName(u"procedural_add_button")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/plus (gray).png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.procedural_add_button.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.procedural_add_button)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.equation_owner_label = QLabel(self.frame_2)
        self.equation_owner_label.setObjectName(u"equation_owner_label")

        self.horizontalLayout_2.addWidget(self.equation_owner_label)

        self.equation_owner_combo = QComboBox(self.frame_2)
        self.equation_owner_combo.setObjectName(u"equation_owner_combo")
        self.equation_owner_combo.setMinimumSize(QSize(300, 0))

        self.horizontalLayout_2.addWidget(self.equation_owner_combo)


        self.verticalLayout.addWidget(self.frame_2)

        self.dae_editor_container = QWidget(self.dae_model_page)
        self.dae_editor_container.setObjectName(u"dae_editor_container")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dae_editor_container.sizePolicy().hasHeightForWidth())
        self.dae_editor_container.setSizePolicy(sizePolicy)
        self.dae_editor_layout = QVBoxLayout(self.dae_editor_container)
        self.dae_editor_layout.setObjectName(u"dae_editor_layout")
        self.dae_editor_layout.setContentsMargins(0, 0, 0, 0)

        self.verticalLayout.addWidget(self.dae_editor_container)

        self.frame = QFrame(self.dae_model_page)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.dae_code_search = QLineEdit(self.frame)
        self.dae_code_search.setObjectName(u"dae_code_search")
        self.dae_code_search.setClearButtonEnabled(True)

        self.horizontalLayout.addWidget(self.dae_code_search)

        self.dae_search_previous_button = QToolButton(self.frame)
        self.dae_search_previous_button.setObjectName(u"dae_search_previous_button")
        self.dae_search_previous_button.setEnabled(False)

        self.horizontalLayout.addWidget(self.dae_search_previous_button)

        self.dae_search_next_button = QToolButton(self.frame)
        self.dae_search_next_button.setObjectName(u"dae_search_next_button")
        self.dae_search_next_button.setEnabled(False)

        self.horizontalLayout.addWidget(self.dae_search_next_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addWidget(self.frame)

        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/equation.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tab_widget.addTab(self.dae_model_page, icon2, "")
        self.latex_page = QWidget()
        self.latex_page.setObjectName(u"latex_page")
        self.verticalLayout_2 = QVBoxLayout(self.latex_page)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_4 = QFrame(self.latex_page)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.latex_select_all_button = QPushButton(self.frame_4)
        self.latex_select_all_button.setObjectName(u"latex_select_all_button")
        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/check_all.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.latex_select_all_button.setIcon(icon3)

        self.horizontalLayout_4.addWidget(self.latex_select_all_button)

        self.latex_clear_button = QPushButton(self.frame_4)
        self.latex_clear_button.setObjectName(u"latex_clear_button")
        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/uncheck_all.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.latex_clear_button.setIcon(icon4)

        self.horizontalLayout_4.addWidget(self.latex_clear_button)

        self.selection_button_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.selection_button_spacer)

        self.export_rendered_button = QPushButton(self.frame_4)
        self.export_rendered_button.setObjectName(u"export_rendered_button")
        icon5 = QIcon()
        icon5.addFile(u":/Icons/icons/pdf.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.export_rendered_button.setIcon(icon5)

        self.horizontalLayout_4.addWidget(self.export_rendered_button)


        self.verticalLayout_2.addWidget(self.frame_4)

        self.toolBox = QToolBox(self.latex_page)
        self.toolBox.setObjectName(u"toolBox")
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.page.setGeometry(QRect(0, 0, 667, 371))
        self.verticalLayout_7 = QVBoxLayout(self.page)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.latex_selection_tree = QTreeWidget(self.page)
        self.latex_selection_tree.setObjectName(u"latex_selection_tree")
        self.latex_selection_tree.setFrameShape(QFrame.Shape.NoFrame)
        self.latex_selection_tree.setAlternatingRowColors(True)

        self.verticalLayout_7.addWidget(self.latex_selection_tree)

        self.toolBox.addItem(self.page, u"Equations")
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.page_2.setGeometry(QRect(0, 0, 893, 477))
        self.verticalLayout_8 = QVBoxLayout(self.page_2)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.latex_source_preview = QPlainTextEdit(self.page_2)
        self.latex_source_preview.setObjectName(u"latex_source_preview")
        self.latex_source_preview.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.latex_source_preview.setReadOnly(True)

        self.verticalLayout_8.addWidget(self.latex_source_preview)

        self.toolBox.addItem(self.page_2, u"LaTex source")

        self.verticalLayout_2.addWidget(self.toolBox)

        icon6 = QIcon()
        icon6.addFile(u":/Icons/icons/new2.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tab_widget.addTab(self.latex_page, icon6, "")
        self.special_settings_page = QWidget()
        self.special_settings_page.setObjectName(u"special_settings_page")
        self.special_settings_layout = QVBoxLayout(self.special_settings_page)
        self.special_settings_layout.setObjectName(u"special_settings_layout")
        self.special_settings_description = QLabel(self.special_settings_page)
        self.special_settings_description.setObjectName(u"special_settings_description")
        self.special_settings_description.setWordWrap(True)

        self.special_settings_layout.addWidget(self.special_settings_description)

        self.special_settings_table = QTableView(self.special_settings_page)
        self.special_settings_table.setObjectName(u"special_settings_table")
        self.special_settings_table.setFrameShape(QFrame.Shape.NoFrame)
        self.special_settings_table.setAlternatingRowColors(True)

        self.special_settings_layout.addWidget(self.special_settings_table)

        self.tab_widget.addTab(self.special_settings_page, "")

        self.main_layout.addWidget(self.tab_widget)

        self.frame_3 = QFrame(DynamicBlockPropertiesDialog)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.validate_code_button = QPushButton(self.frame_3)
        self.validate_code_button.setObjectName(u"validate_code_button")
        icon7 = QIcon()
        icon7.addFile(u":/Icons/icons/calculator.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.validate_code_button.setIcon(icon7)

        self.horizontalLayout_3.addWidget(self.validate_code_button)

        self.button_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.button_spacer)

        self.apply_button = QPushButton(self.frame_3)
        self.apply_button.setObjectName(u"apply_button")
        icon8 = QIcon()
        icon8.addFile(u":/Icons/icons/accept.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.apply_button.setIcon(icon8)

        self.horizontalLayout_3.addWidget(self.apply_button)


        self.main_layout.addWidget(self.frame_3)


        self.retranslateUi(DynamicBlockPropertiesDialog)

        self.tab_widget.setCurrentIndex(0)
        self.toolBox.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(DynamicBlockPropertiesDialog)
    # setupUi

    def retranslateUi(self, DynamicBlockPropertiesDialog):
        DynamicBlockPropertiesDialog.setWindowTitle(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Block properties", None))
        self.property_search.setPlaceholderText(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Search properties...", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.general_page), QCoreApplication.translate("DynamicBlockPropertiesDialog", u"General options", None))
#if QT_CONFIG(tooltip)
        self.procedural_add_button.setToolTip(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Add one procedural behavior to the active equation owner's Python code.", None))
#endif // QT_CONFIG(tooltip)
        self.procedural_add_button.setText("")
        self.equation_owner_label.setText(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Equation owner", None))
        self.dae_code_search.setPlaceholderText(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Search Python code...", None))
        self.dae_search_previous_button.setText(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"<<", None))
        self.dae_search_next_button.setText(QCoreApplication.translate("DynamicBlockPropertiesDialog", u">>", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.dae_model_page), QCoreApplication.translate("DynamicBlockPropertiesDialog", u"DAE model", None))
#if QT_CONFIG(statustip)
        self.latex_select_all_button.setStatusTip(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Select all", None))
#endif // QT_CONFIG(statustip)
        self.latex_select_all_button.setText("")
#if QT_CONFIG(statustip)
        self.latex_clear_button.setStatusTip(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Select None", None))
#endif // QT_CONFIG(statustip)
        self.latex_clear_button.setText("")
#if QT_CONFIG(tooltip)
        self.export_rendered_button.setToolTip(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Save redered PDF", None))
#endif // QT_CONFIG(tooltip)
        self.export_rendered_button.setText("")
        ___qtreewidgetitem = self.latex_selection_tree.headerItem()
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Equations", None))
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Block / equation group", None))
#if QT_CONFIG(tooltip)
        self.latex_selection_tree.setToolTip(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Select the equation groups to include. Each internal block and each DAE section can be selected independently.", None))
#endif // QT_CONFIG(tooltip)
        self.toolBox.setItemText(self.toolBox.indexOf(self.page), QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Equations", None))
        self.latex_source_preview.setPlaceholderText(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Select equation groups to generate copyable LaTeX source.", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), QCoreApplication.translate("DynamicBlockPropertiesDialog", u"LaTex source", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.latex_page), QCoreApplication.translate("DynamicBlockPropertiesDialog", u"LaTeX rendering", None))
        self.special_settings_description.setText(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"These settings contain structured data used to regenerate the block. Edit sequences with valid Python tuple/list syntax.", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.special_settings_page), QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Special configuration", None))
#if QT_CONFIG(tooltip)
        self.validate_code_button.setToolTip(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Validate model", None))
#endif // QT_CONFIG(tooltip)
        self.validate_code_button.setText("")
#if QT_CONFIG(tooltip)
        self.apply_button.setToolTip(QCoreApplication.translate("DynamicBlockPropertiesDialog", u"Accept changes", None))
#endif // QT_CONFIG(tooltip)
        self.apply_button.setText("")
    # retranslateUi

