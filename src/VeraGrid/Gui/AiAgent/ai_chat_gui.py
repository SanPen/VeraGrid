# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ai_chat_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDoubleSpinBox,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSplitter, QTabWidget,
    QTextBrowser, QVBoxLayout, QWidget)

class Ui_AiChatDialog(object):
    def setupUi(self, AiChatDialog):
        if not AiChatDialog.objectName():
            AiChatDialog.setObjectName(u"AiChatDialog")
        AiChatDialog.resize(654, 605)
        self.verticalLayout_4 = QVBoxLayout(AiChatDialog)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(AiChatDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_2 = QVBoxLayout(self.tab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.splitter = QSplitter(self.tab)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.frame = QFrame(self.splitter)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.conversation_text_browser = QTextBrowser(self.frame)
        self.conversation_text_browser.setObjectName(u"conversation_text_browser")
        self.conversation_text_browser.setFrameShape(QFrame.Shape.NoFrame)
        self.conversation_text_browser.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.conversation_text_browser)

        self.splitter.addWidget(self.frame)
        self.chat_frame = QFrame(self.splitter)
        self.chat_frame.setObjectName(u"chat_frame")
        self.chat_frame.setMaximumSize(QSize(16777215, 16777215))
        self.chat_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.chat_layout = QVBoxLayout(self.chat_frame)
        self.chat_layout.setObjectName(u"chat_layout")
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.message_plain_text_edit = QPlainTextEdit(self.chat_frame)
        self.message_plain_text_edit.setObjectName(u"message_plain_text_edit")
        self.message_plain_text_edit.setMinimumSize(QSize(0, 120))
        self.message_plain_text_edit.setMaximumSize(QSize(16777215, 16777215))
        self.message_plain_text_edit.setFrameShape(QFrame.Shape.NoFrame)
        self.message_plain_text_edit.setTabChangesFocus(True)

        self.chat_layout.addWidget(self.message_plain_text_edit)

        self.splitter.addWidget(self.chat_frame)

        self.verticalLayout_2.addWidget(self.splitter)

        self.frame_2 = QFrame(self.tab)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.clear_chat_button = QPushButton(self.frame_2)
        self.clear_chat_button.setObjectName(u"clear_chat_button")

        self.horizontalLayout.addWidget(self.clear_chat_button)

        self.status_label = QLabel(self.frame_2)
        self.status_label.setObjectName(u"status_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.status_label.sizePolicy().hasHeightForWidth())
        self.status_label.setSizePolicy(sizePolicy)
        self.status_label.setWordWrap(True)

        self.horizontalLayout.addWidget(self.status_label)

        self.send_button = QPushButton(self.frame_2)
        self.send_button.setObjectName(u"send_button")

        self.horizontalLayout.addWidget(self.send_button)


        self.verticalLayout_2.addWidget(self.frame_2)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.gridLayout = QGridLayout(self.tab_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.groupBox = QGroupBox(self.tab_2)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMinimumSize(QSize(340, 0))
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.ollama_status_label = QLabel(self.groupBox)
        self.ollama_status_label.setObjectName(u"ollama_status_label")

        self.gridLayout_2.addWidget(self.ollama_status_label, 0, 0, 1, 1)

        self.ollama_status_value_label = QLabel(self.groupBox)
        self.ollama_status_value_label.setObjectName(u"ollama_status_value_label")
        self.ollama_status_value_label.setWordWrap(True)

        self.gridLayout_2.addWidget(self.ollama_status_value_label, 0, 1, 1, 2)

        self.local_model_path_label = QLabel(self.groupBox)
        self.local_model_path_label.setObjectName(u"local_model_path_label")

        self.gridLayout_2.addWidget(self.local_model_path_label, 1, 0, 1, 1)

        self.local_model_path_line_edit = QLineEdit(self.groupBox)
        self.local_model_path_line_edit.setObjectName(u"local_model_path_line_edit")

        self.gridLayout_2.addWidget(self.local_model_path_line_edit, 1, 1, 1, 2)

        self.local_model_label = QLabel(self.groupBox)
        self.local_model_label.setObjectName(u"local_model_label")

        self.gridLayout_2.addWidget(self.local_model_label, 2, 0, 1, 1)

        self.local_model_combo_box = QComboBox(self.groupBox)
        self.local_model_combo_box.setObjectName(u"local_model_combo_box")
        self.local_model_combo_box.setEditable(True)
        self.local_model_combo_box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.gridLayout_2.addWidget(self.local_model_combo_box, 2, 1, 1, 1)

        self.local_refresh_models_button = QPushButton(self.groupBox)
        self.local_refresh_models_button.setObjectName(u"local_refresh_models_button")

        self.gridLayout_2.addWidget(self.local_refresh_models_button, 2, 2, 1, 1)

        self.local_timeout_label = QLabel(self.groupBox)
        self.local_timeout_label.setObjectName(u"local_timeout_label")

        self.gridLayout_2.addWidget(self.local_timeout_label, 3, 0, 1, 1)

        self.local_timeout_double_spin_box = QDoubleSpinBox(self.groupBox)
        self.local_timeout_double_spin_box.setObjectName(u"local_timeout_double_spin_box")
        self.local_timeout_double_spin_box.setDecimals(1)
        self.local_timeout_double_spin_box.setMinimum(1.000000000000000)
        self.local_timeout_double_spin_box.setMaximum(600.000000000000000)
        self.local_timeout_double_spin_box.setSingleStep(5.000000000000000)
        self.local_timeout_double_spin_box.setValue(60.000000000000000)

        self.gridLayout_2.addWidget(self.local_timeout_double_spin_box, 3, 1, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 4, 1, 1, 1)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 1, 1, 1)

        self.controls_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.controls_spacer, 1, 0, 1, 1)

        self.tabWidget.addTab(self.tab_2, "")

        self.verticalLayout_4.addWidget(self.tabWidget)


        self.retranslateUi(AiChatDialog)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AiChatDialog)
    # setupUi

    def retranslateUi(self, AiChatDialog):
        AiChatDialog.setWindowTitle(QCoreApplication.translate("AiChatDialog", u"AI dialogue", None))
        self.message_plain_text_edit.setPlaceholderText(QCoreApplication.translate("AiChatDialog", u"Ask about the active VeraGrid project, the selected study or the current network model.", None))
        self.clear_chat_button.setText(QCoreApplication.translate("AiChatDialog", u"Clear chat", None))
        self.status_label.setText(QCoreApplication.translate("AiChatDialog", u"Ready.", None))
        self.send_button.setText(QCoreApplication.translate("AiChatDialog", u"Send", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("AiChatDialog", u"Dialogue", None))
        self.groupBox.setTitle(QCoreApplication.translate("AiChatDialog", u"Ollama", None))
        self.ollama_status_label.setText(QCoreApplication.translate("AiChatDialog", u"Status", None))
        self.ollama_status_value_label.setText(QCoreApplication.translate("AiChatDialog", u"Checked automatically when the chat opens.", None))
        self.local_model_path_label.setText(QCoreApplication.translate("AiChatDialog", u"Base URL", None))
        self.local_model_path_line_edit.setPlaceholderText(QCoreApplication.translate("AiChatDialog", u"http://localhost:11434/v1", None))
        self.local_model_label.setText(QCoreApplication.translate("AiChatDialog", u"Model", None))
        self.local_refresh_models_button.setText(QCoreApplication.translate("AiChatDialog", u"Refresh", None))
        self.local_timeout_label.setText(QCoreApplication.translate("AiChatDialog", u"Timeout [s]", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("AiChatDialog", u"Settings", None))
    # retranslateUi

