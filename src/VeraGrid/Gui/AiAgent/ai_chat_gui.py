# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ai_chat_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
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
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QSplitter, QTabWidget, QTextBrowser, QVBoxLayout,
    QWidget)

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
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.message_plain_text_edit.sizePolicy().hasHeightForWidth())
        self.message_plain_text_edit.setSizePolicy(sizePolicy)
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
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.status_label.sizePolicy().hasHeightForWidth())
        self.status_label.setSizePolicy(sizePolicy1)
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
        self.groupBox.setMinimumSize(QSize(300, 0))
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.local_model_combo_box = QComboBox(self.groupBox)
        self.local_model_combo_box.setObjectName(u"local_model_combo_box")
        self.local_model_combo_box.setEditable(True)
        self.local_model_combo_box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.gridLayout_2.addWidget(self.local_model_combo_box, 6, 0, 1, 3)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 16, 1, 1, 1)

        self.local_model_path_line_edit = QLineEdit(self.groupBox)
        self.local_model_path_line_edit.setObjectName(u"local_model_path_line_edit")

        self.gridLayout_2.addWidget(self.local_model_path_line_edit, 4, 0, 1, 3)

        self.local_timeout_double_spin_box = QDoubleSpinBox(self.groupBox)
        self.local_timeout_double_spin_box.setObjectName(u"local_timeout_double_spin_box")
        self.local_timeout_double_spin_box.setDecimals(1)
        self.local_timeout_double_spin_box.setMinimum(1.000000000000000)
        self.local_timeout_double_spin_box.setMaximum(600.000000000000000)
        self.local_timeout_double_spin_box.setSingleStep(5.000000000000000)
        self.local_timeout_double_spin_box.setValue(60.000000000000000)

        self.gridLayout_2.addWidget(self.local_timeout_double_spin_box, 7, 1, 1, 2)

        self.local_ai_radioButton = QRadioButton(self.groupBox)
        self.local_ai_radioButton.setObjectName(u"local_ai_radioButton")
        self.local_ai_radioButton.setChecked(True)

        self.gridLayout_2.addWidget(self.local_ai_radioButton, 0, 0, 1, 2)

        self.local_refresh_models_button = QPushButton(self.groupBox)
        self.local_refresh_models_button.setObjectName(u"local_refresh_models_button")

        self.gridLayout_2.addWidget(self.local_refresh_models_button, 5, 2, 1, 1)

        self.local_model_label = QLabel(self.groupBox)
        self.local_model_label.setObjectName(u"local_model_label")

        self.gridLayout_2.addWidget(self.local_model_label, 5, 0, 1, 2)

        self.local_model_path_label = QLabel(self.groupBox)
        self.local_model_path_label.setObjectName(u"local_model_path_label")

        self.gridLayout_2.addWidget(self.local_model_path_label, 3, 0, 1, 1)

        self.local_timeout_label = QLabel(self.groupBox)
        self.local_timeout_label.setObjectName(u"local_timeout_label")

        self.gridLayout_2.addWidget(self.local_timeout_label, 7, 0, 1, 1)

        self.local_context_tokens_label = QLabel(self.groupBox)
        self.local_context_tokens_label.setObjectName(u"local_context_tokens_label")

        self.gridLayout_2.addWidget(self.local_context_tokens_label, 8, 0, 1, 1)

        self.local_context_tokens_spin_box = QSpinBox(self.groupBox)
        self.local_context_tokens_spin_box.setObjectName(u"local_context_tokens_spin_box")
        self.local_context_tokens_spin_box.setMinimum(512)
        self.local_context_tokens_spin_box.setMaximum(32768)
        self.local_context_tokens_spin_box.setSingleStep(512)
        self.local_context_tokens_spin_box.setValue(4096)

        self.gridLayout_2.addWidget(self.local_context_tokens_spin_box, 8, 1, 1, 2)

        self.local_completion_tokens_label = QLabel(self.groupBox)
        self.local_completion_tokens_label.setObjectName(u"local_completion_tokens_label")

        self.gridLayout_2.addWidget(self.local_completion_tokens_label, 9, 0, 1, 1)

        self.local_completion_tokens_spin_box = QSpinBox(self.groupBox)
        self.local_completion_tokens_spin_box.setObjectName(u"local_completion_tokens_spin_box")
        self.local_completion_tokens_spin_box.setMinimum(64)
        self.local_completion_tokens_spin_box.setMaximum(8192)
        self.local_completion_tokens_spin_box.setSingleStep(64)
        self.local_completion_tokens_spin_box.setValue(1024)

        self.gridLayout_2.addWidget(self.local_completion_tokens_spin_box, 9, 1, 1, 2)

        self.local_gpu_layers_label = QLabel(self.groupBox)
        self.local_gpu_layers_label.setObjectName(u"local_gpu_layers_label")

        self.gridLayout_2.addWidget(self.local_gpu_layers_label, 10, 0, 1, 1)

        self.local_gpu_layers_spin_box = QSpinBox(self.groupBox)
        self.local_gpu_layers_spin_box.setObjectName(u"local_gpu_layers_spin_box")
        self.local_gpu_layers_spin_box.setMinimum(-1)
        self.local_gpu_layers_spin_box.setMaximum(512)
        self.local_gpu_layers_spin_box.setValue(33)

        self.gridLayout_2.addWidget(self.local_gpu_layers_spin_box, 10, 1, 1, 2)

        self.local_temperature_label = QLabel(self.groupBox)
        self.local_temperature_label.setObjectName(u"local_temperature_label")

        self.gridLayout_2.addWidget(self.local_temperature_label, 11, 0, 1, 1)

        self.local_temperature_double_spin_box = QDoubleSpinBox(self.groupBox)
        self.local_temperature_double_spin_box.setObjectName(u"local_temperature_double_spin_box")
        self.local_temperature_double_spin_box.setDecimals(2)
        self.local_temperature_double_spin_box.setMinimum(0.000000000000000)
        self.local_temperature_double_spin_box.setMaximum(2.000000000000000)
        self.local_temperature_double_spin_box.setSingleStep(0.050000000000000)
        self.local_temperature_double_spin_box.setValue(0.150000000000000)

        self.gridLayout_2.addWidget(self.local_temperature_double_spin_box, 11, 1, 1, 2)

        self.local_top_p_label = QLabel(self.groupBox)
        self.local_top_p_label.setObjectName(u"local_top_p_label")

        self.gridLayout_2.addWidget(self.local_top_p_label, 12, 0, 1, 1)

        self.local_top_p_double_spin_box = QDoubleSpinBox(self.groupBox)
        self.local_top_p_double_spin_box.setObjectName(u"local_top_p_double_spin_box")
        self.local_top_p_double_spin_box.setDecimals(2)
        self.local_top_p_double_spin_box.setMinimum(0.050000000000000)
        self.local_top_p_double_spin_box.setMaximum(1.000000000000000)
        self.local_top_p_double_spin_box.setSingleStep(0.050000000000000)
        self.local_top_p_double_spin_box.setValue(0.900000000000000)

        self.gridLayout_2.addWidget(self.local_top_p_double_spin_box, 12, 1, 1, 2)

        self.local_history_messages_label = QLabel(self.groupBox)
        self.local_history_messages_label.setObjectName(u"local_history_messages_label")

        self.gridLayout_2.addWidget(self.local_history_messages_label, 13, 0, 1, 1)

        self.local_history_messages_spin_box = QSpinBox(self.groupBox)
        self.local_history_messages_spin_box.setObjectName(u"local_history_messages_spin_box")
        self.local_history_messages_spin_box.setMinimum(1)
        self.local_history_messages_spin_box.setMaximum(64)
        self.local_history_messages_spin_box.setValue(6)

        self.gridLayout_2.addWidget(self.local_history_messages_spin_box, 13, 1, 1, 2)

        self.local_history_chars_label = QLabel(self.groupBox)
        self.local_history_chars_label.setObjectName(u"local_history_chars_label")

        self.gridLayout_2.addWidget(self.local_history_chars_label, 14, 0, 1, 1)

        self.local_history_chars_spin_box = QSpinBox(self.groupBox)
        self.local_history_chars_spin_box.setObjectName(u"local_history_chars_spin_box")
        self.local_history_chars_spin_box.setMinimum(512)
        self.local_history_chars_spin_box.setMaximum(64000)
        self.local_history_chars_spin_box.setSingleStep(256)
        self.local_history_chars_spin_box.setValue(2200)

        self.gridLayout_2.addWidget(self.local_history_chars_spin_box, 14, 1, 1, 2)

        self.local_grounding_chars_label = QLabel(self.groupBox)
        self.local_grounding_chars_label.setObjectName(u"local_grounding_chars_label")

        self.gridLayout_2.addWidget(self.local_grounding_chars_label, 15, 0, 1, 1)

        self.local_grounding_chars_spin_box = QSpinBox(self.groupBox)
        self.local_grounding_chars_spin_box.setObjectName(u"local_grounding_chars_spin_box")
        self.local_grounding_chars_spin_box.setMinimum(256)
        self.local_grounding_chars_spin_box.setMaximum(64000)
        self.local_grounding_chars_spin_box.setSingleStep(256)
        self.local_grounding_chars_spin_box.setValue(1800)

        self.gridLayout_2.addWidget(self.local_grounding_chars_spin_box, 15, 1, 1, 2)


        self.gridLayout.addWidget(self.groupBox, 0, 0, 1, 2)

        self.groupBox_2 = QGroupBox(self.tab_2)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setMinimumSize(QSize(300, 0))
        self.gridLayout_3 = QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.api_api_key_label = QLabel(self.groupBox_2)
        self.api_api_key_label.setObjectName(u"api_api_key_label")

        self.gridLayout_3.addWidget(self.api_api_key_label, 6, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer_2, 12, 1, 1, 1)

        self.api_timeout_double_spin_box = QDoubleSpinBox(self.groupBox_2)
        self.api_timeout_double_spin_box.setObjectName(u"api_timeout_double_spin_box")
        self.api_timeout_double_spin_box.setDecimals(1)
        self.api_timeout_double_spin_box.setMinimum(1.000000000000000)
        self.api_timeout_double_spin_box.setMaximum(600.000000000000000)
        self.api_timeout_double_spin_box.setSingleStep(5.000000000000000)
        self.api_timeout_double_spin_box.setValue(60.000000000000000)

        self.gridLayout_3.addWidget(self.api_timeout_double_spin_box, 11, 1, 1, 2)

        self.api_base_url_line_edit = QLineEdit(self.groupBox_2)
        self.api_base_url_line_edit.setObjectName(u"api_base_url_line_edit")

        self.gridLayout_3.addWidget(self.api_base_url_line_edit, 5, 0, 1, 3)

        self.api_api_key_line_edit = QLineEdit(self.groupBox_2)
        self.api_api_key_line_edit.setObjectName(u"api_api_key_line_edit")
        self.api_api_key_line_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.gridLayout_3.addWidget(self.api_api_key_line_edit, 7, 0, 1, 3)

        self.api_timeout_label = QLabel(self.groupBox_2)
        self.api_timeout_label.setObjectName(u"api_timeout_label")

        self.gridLayout_3.addWidget(self.api_timeout_label, 11, 0, 1, 1)

        self.api_provider_label = QLabel(self.groupBox_2)
        self.api_provider_label.setObjectName(u"api_provider_label")

        self.gridLayout_3.addWidget(self.api_provider_label, 2, 0, 1, 1)

        self.api_model_label = QLabel(self.groupBox_2)
        self.api_model_label.setObjectName(u"api_model_label")

        self.gridLayout_3.addWidget(self.api_model_label, 8, 0, 1, 1)

        self.api_model_combo_box = QComboBox(self.groupBox_2)
        self.api_model_combo_box.setObjectName(u"api_model_combo_box")
        self.api_model_combo_box.setEditable(True)
        self.api_model_combo_box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.gridLayout_3.addWidget(self.api_model_combo_box, 9, 0, 1, 3)

        self.api_ai_radioButton = QRadioButton(self.groupBox_2)
        self.api_ai_radioButton.setObjectName(u"api_ai_radioButton")

        self.gridLayout_3.addWidget(self.api_ai_radioButton, 0, 0, 1, 2)

        self.api_base_url_label = QLabel(self.groupBox_2)
        self.api_base_url_label.setObjectName(u"api_base_url_label")

        self.gridLayout_3.addWidget(self.api_base_url_label, 4, 0, 1, 1)

        self.api_provider_combo_box = QComboBox(self.groupBox_2)
        self.api_provider_combo_box.setObjectName(u"api_provider_combo_box")

        self.gridLayout_3.addWidget(self.api_provider_combo_box, 3, 0, 1, 3)

        self.api_refresh_models_button = QPushButton(self.groupBox_2)
        self.api_refresh_models_button.setObjectName(u"api_refresh_models_button")

        self.gridLayout_3.addWidget(self.api_refresh_models_button, 8, 2, 1, 1)


        self.gridLayout.addWidget(self.groupBox_2, 0, 2, 1, 1)

        self.controls_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.controls_spacer, 2, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 3, 1, 1)

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
        self.groupBox.setTitle(QCoreApplication.translate("AiChatDialog", u"Local AI", None))
        self.local_model_path_line_edit.setPlaceholderText(QCoreApplication.translate("AiChatDialog", u"/path/to/model.gguf or /path/to/models", None))
        self.local_ai_radioButton.setText(QCoreApplication.translate("AiChatDialog", u"Local AI settings", None))
        self.local_refresh_models_button.setText(QCoreApplication.translate("AiChatDialog", u"Scan", None))
        self.local_model_label.setText(QCoreApplication.translate("AiChatDialog", u"GGUF model", None))
        self.local_model_path_label.setText(QCoreApplication.translate("AiChatDialog", u"Model path", None))
        self.local_timeout_label.setText(QCoreApplication.translate("AiChatDialog", u"Timeout [s]", None))
        self.local_context_tokens_label.setText(QCoreApplication.translate("AiChatDialog", u"Context tokens", None))
        self.local_completion_tokens_label.setText(QCoreApplication.translate("AiChatDialog", u"Completion tokens", None))
        self.local_gpu_layers_label.setText(QCoreApplication.translate("AiChatDialog", u"GPU layers", None))
        self.local_temperature_label.setText(QCoreApplication.translate("AiChatDialog", u"Temperature", None))
        self.local_top_p_label.setText(QCoreApplication.translate("AiChatDialog", u"Top p", None))
        self.local_history_messages_label.setText(QCoreApplication.translate("AiChatDialog", u"History messages", None))
        self.local_history_chars_label.setText(QCoreApplication.translate("AiChatDialog", u"History chars", None))
        self.local_grounding_chars_label.setText(QCoreApplication.translate("AiChatDialog", u"Grounding chars", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("AiChatDialog", u"Remote AI", None))
        self.api_api_key_label.setText(QCoreApplication.translate("AiChatDialog", u"API key", None))
        self.api_base_url_line_edit.setPlaceholderText(QCoreApplication.translate("AiChatDialog", u"https://api.example.com/v1", None))
        self.api_api_key_line_edit.setPlaceholderText(QCoreApplication.translate("AiChatDialog", u"Leave empty for unauthenticated endpoints", None))
        self.api_timeout_label.setText(QCoreApplication.translate("AiChatDialog", u"Timeout [s]", None))
        self.api_provider_label.setText(QCoreApplication.translate("AiChatDialog", u"API provider", None))
        self.api_model_label.setText(QCoreApplication.translate("AiChatDialog", u"Model", None))
        self.api_ai_radioButton.setText(QCoreApplication.translate("AiChatDialog", u"API AI settings", None))
        self.api_base_url_label.setText(QCoreApplication.translate("AiChatDialog", u"Base URL", None))
        self.api_refresh_models_button.setText(QCoreApplication.translate("AiChatDialog", u"Refresh", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("AiChatDialog", u"Settings", None))
    # retranslateUi

