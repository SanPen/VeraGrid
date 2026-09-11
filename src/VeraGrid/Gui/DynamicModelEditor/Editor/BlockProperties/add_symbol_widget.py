# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'add_symbol_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(378, 554)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.add_symbol_group = QGroupBox(Form)
        self.add_symbol_group.setObjectName(u"add_symbol_group")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.add_symbol_group.sizePolicy().hasHeightForWidth())
        self.add_symbol_group.setSizePolicy(sizePolicy)
        self.add_symbol_layout = QGridLayout(self.add_symbol_group)
        self.add_symbol_layout.setObjectName(u"add_symbol_layout")
        self.add_symbol_layout.setHorizontalSpacing(6)
        self.add_symbol_layout.setVerticalSpacing(3)
        self.add_symbol_layout.setContentsMargins(6, 4, 6, 4)
        self.new_variable_options = QWidget(self.add_symbol_group)
        self.new_variable_options.setObjectName(u"new_variable_options")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.new_variable_options.sizePolicy().hasHeightForWidth())
        self.new_variable_options.setSizePolicy(sizePolicy1)
        self.new_variable_options_layout = QHBoxLayout(self.new_variable_options)
        self.new_variable_options_layout.setObjectName(u"new_variable_options_layout")
        self.new_variable_options_layout.setContentsMargins(0, 0, 0, 0)
        self.new_symbol_exported = QCheckBox(self.new_variable_options)
        self.new_symbol_exported.setObjectName(u"new_symbol_exported")

        self.new_variable_options_layout.addWidget(self.new_symbol_exported)

        self.new_state_derivative = QCheckBox(self.new_variable_options)
        self.new_state_derivative.setObjectName(u"new_state_derivative")

        self.new_variable_options_layout.addWidget(self.new_state_derivative)

        self.new_variable_options_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.new_variable_options_layout.addItem(self.new_variable_options_spacer)


        self.add_symbol_layout.addWidget(self.new_variable_options, 8, 0, 1, 1)

        self.new_symbol_owner = QComboBox(self.add_symbol_group)
        self.new_symbol_owner.setObjectName(u"new_symbol_owner")
        sizePolicy1.setHeightForWidth(self.new_symbol_owner.sizePolicy().hasHeightForWidth())
        self.new_symbol_owner.setSizePolicy(sizePolicy1)

        self.add_symbol_layout.addWidget(self.new_symbol_owner, 1, 0, 1, 1)

        self.new_external_reference = QComboBox(self.add_symbol_group)
        self.new_external_reference.setObjectName(u"new_external_reference")
        sizePolicy1.setHeightForWidth(self.new_external_reference.sizePolicy().hasHeightForWidth())
        self.new_external_reference.setSizePolicy(sizePolicy1)
        self.new_external_reference.setEditable(True)

        self.add_symbol_layout.addWidget(self.new_external_reference, 13, 0, 1, 1)

        self.new_symbol_kind = QComboBox(self.add_symbol_group)
        self.new_symbol_kind.setObjectName(u"new_symbol_kind")
        sizePolicy1.setHeightForWidth(self.new_symbol_kind.sizePolicy().hasHeightForWidth())
        self.new_symbol_kind.setSizePolicy(sizePolicy1)

        self.add_symbol_layout.addWidget(self.new_symbol_kind, 7, 0, 1, 1)

        self.new_symbol_category = QComboBox(self.add_symbol_group)
        self.new_symbol_category.setObjectName(u"new_symbol_category")
        sizePolicy1.setHeightForWidth(self.new_symbol_category.sizePolicy().hasHeightForWidth())
        self.new_symbol_category.setSizePolicy(sizePolicy1)

        self.add_symbol_layout.addWidget(self.new_symbol_category, 5, 0, 1, 1)

        self.new_symbol_name_label = QLabel(self.add_symbol_group)
        self.new_symbol_name_label.setObjectName(u"new_symbol_name_label")

        self.add_symbol_layout.addWidget(self.new_symbol_name_label, 2, 0, 1, 1)

        self.new_symbol_category_label = QLabel(self.add_symbol_group)
        self.new_symbol_category_label.setObjectName(u"new_symbol_category_label")

        self.add_symbol_layout.addWidget(self.new_symbol_category_label, 4, 0, 1, 1)

        self.new_symbol_owner_label = QLabel(self.add_symbol_group)
        self.new_symbol_owner_label.setObjectName(u"new_symbol_owner_label")

        self.add_symbol_layout.addWidget(self.new_symbol_owner_label, 0, 0, 1, 1)

        self.new_symbol_kind_label = QLabel(self.add_symbol_group)
        self.new_symbol_kind_label.setObjectName(u"new_symbol_kind_label")

        self.add_symbol_layout.addWidget(self.new_symbol_kind_label, 6, 0, 1, 1)

        self.add_symbol_button = QPushButton(self.add_symbol_group)
        self.add_symbol_button.setObjectName(u"add_symbol_button")

        self.add_symbol_layout.addWidget(self.add_symbol_button, 16, 0, 1, 1)

        self.add_symbol_status_label = QLabel(self.add_symbol_group)
        self.add_symbol_status_label.setObjectName(u"add_symbol_status_label")
        self.add_symbol_status_label.setVisible(False)
        self.add_symbol_status_label.setWordWrap(True)
        self.add_symbol_status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.add_symbol_layout.addWidget(self.add_symbol_status_label, 15, 0, 1, 1)

        self.new_static_reference_label = QLabel(self.add_symbol_group)
        self.new_static_reference_label.setObjectName(u"new_static_reference_label")

        self.add_symbol_layout.addWidget(self.new_static_reference_label, 10, 0, 1, 1)

        self.new_external_reference_label = QLabel(self.add_symbol_group)
        self.new_external_reference_label.setObjectName(u"new_external_reference_label")

        self.add_symbol_layout.addWidget(self.new_external_reference_label, 12, 0, 1, 1)

        self.new_parameter_value = QDoubleSpinBox(self.add_symbol_group)
        self.new_parameter_value.setObjectName(u"new_parameter_value")
        sizePolicy1.setHeightForWidth(self.new_parameter_value.sizePolicy().hasHeightForWidth())
        self.new_parameter_value.setSizePolicy(sizePolicy1)
        self.new_parameter_value.setDecimals(12)
        self.new_parameter_value.setMinimum(-10000000000000000159028911097599180468360808563945281389781327557747838772170381060813469985856815104.000000000000000)
        self.new_parameter_value.setMaximum(10000000000000000159028911097599180468360808563945281389781327557747838772170381060813469985856815104.000000000000000)

        self.add_symbol_layout.addWidget(self.new_parameter_value, 11, 0, 1, 1)

        self.new_static_reference = QComboBox(self.add_symbol_group)
        self.new_static_reference.setObjectName(u"new_static_reference")
        sizePolicy1.setHeightForWidth(self.new_static_reference.sizePolicy().hasHeightForWidth())
        self.new_static_reference.setSizePolicy(sizePolicy1)
        self.new_static_reference.setEditable(True)

        self.add_symbol_layout.addWidget(self.new_static_reference, 11, 0, 1, 1)

        self.add_symbol_spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.add_symbol_layout.addItem(self.add_symbol_spacer, 14, 0, 1, 1)

        self.new_symbol_name = QLineEdit(self.add_symbol_group)
        self.new_symbol_name.setObjectName(u"new_symbol_name")
        sizePolicy1.setHeightForWidth(self.new_symbol_name.sizePolicy().hasHeightForWidth())
        self.new_symbol_name.setSizePolicy(sizePolicy1)

        self.add_symbol_layout.addWidget(self.new_symbol_name, 3, 0, 1, 1)

        self.new_parameter_value_label = QLabel(self.add_symbol_group)
        self.new_parameter_value_label.setObjectName(u"new_parameter_value_label")

        self.add_symbol_layout.addWidget(self.new_parameter_value_label, 9, 0, 1, 1)


        self.verticalLayout.addWidget(self.add_symbol_group)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Add block property", None))
        self.add_symbol_group.setTitle(QCoreApplication.translate("Form", u"Add symbol to selected block", None))
        self.new_symbol_exported.setText(QCoreApplication.translate("Form", u"Output", None))
        self.new_state_derivative.setText(QCoreApplication.translate("Form", u"Create derivative variable", None))
        self.new_symbol_name_label.setText(QCoreApplication.translate("Form", u"New symbol name", None))
        self.new_symbol_category_label.setText(QCoreApplication.translate("Form", u"Symbol category", None))
        self.new_symbol_owner_label.setText(QCoreApplication.translate("Form", u"Owner block", None))
        self.new_symbol_kind_label.setText(QCoreApplication.translate("Form", u"Type", None))
        self.add_symbol_button.setText(QCoreApplication.translate("Form", u"Add symbol", None))
        self.add_symbol_status_label.setText("")
        self.new_static_reference_label.setText(QCoreApplication.translate("Form", u"Static device mapping", None))
#if QT_CONFIG(tooltip)
        self.new_external_reference_label.setToolTip(QCoreApplication.translate("Form", u"Power-flow variable used to initialize this dynamic variable.", None))
#endif // QT_CONFIG(tooltip)
        self.new_external_reference_label.setText(QCoreApplication.translate("Form", u"Power-flow variable", None))
        self.new_symbol_name.setPlaceholderText(QCoreApplication.translate("Form", u"Enter a name", None))
        self.new_parameter_value_label.setText(QCoreApplication.translate("Form", u"Initial numeric value", None))
    # retranslateUi

