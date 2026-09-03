# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about_gui.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit,
    QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
    QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        if not AboutDialog.objectName():
            AboutDialog.setObjectName(u"AboutDialog")
        AboutDialog.resize(641, 413)
        icon = QIcon()
        icon.addFile(u":/Program icon/icons/VeraGrid_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        AboutDialog.setWindowIcon(icon)
        self.verticalLayout_2 = QVBoxLayout(AboutDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.tabWidget = QTabWidget(AboutDialog)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalLayout_4 = QVBoxLayout(self.tab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.frame = QFrame(self.tab)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.frame)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMaximumSize(QSize(32, 32))
        self.label_3.setPixmap(QPixmap(u":/Program icon/icons/VeraGrid_icon.png"))
        self.label_3.setScaledContents(True)

        self.horizontalLayout.addWidget(self.label_3)

        self.mainLabel = QLabel(self.frame)
        self.mainLabel.setObjectName(u"mainLabel")
        self.mainLabel.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.mainLabel.setTextFormat(Qt.TextFormat.RichText)
        self.mainLabel.setScaledContents(True)
        self.mainLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.mainLabel.setWordWrap(True)
        self.mainLabel.setOpenExternalLinks(True)
        self.mainLabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.horizontalLayout.addWidget(self.mainLabel)


        self.verticalLayout_4.addWidget(self.frame)

        self.librariesTableWidget = QTableWidget(self.tab)
        self.librariesTableWidget.setObjectName(u"librariesTableWidget")

        self.verticalLayout_4.addWidget(self.librariesTableWidget)

        self.updateLabel = QLabel(self.tab)
        self.updateLabel.setObjectName(u"updateLabel")
        self.updateLabel.setOpenExternalLinks(True)
        self.updateLabel.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextBrowserInteraction|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.verticalLayout_4.addWidget(self.updateLabel)

        self.copyrightLabel = QLabel(self.tab)
        self.copyrightLabel.setObjectName(u"copyrightLabel")
        self.copyrightLabel.setWordWrap(True)
        self.copyrightLabel.setOpenExternalLinks(True)
        self.copyrightLabel.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.verticalLayout_4.addWidget(self.copyrightLabel)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalLayout = QVBoxLayout(self.tab_2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.contributorsTextEdit = QPlainTextEdit(self.tab_2)
        self.contributorsTextEdit.setObjectName(u"contributorsTextEdit")

        self.verticalLayout.addWidget(self.contributorsTextEdit)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.gridLayout_3 = QGridLayout(self.tab_5)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.copyLibsButton = QPushButton(self.tab_5)
        self.copyLibsButton.setObjectName(u"copyLibsButton")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/copy.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.copyLibsButton.setIcon(icon1)

        self.gridLayout_3.addWidget(self.copyLibsButton, 2, 5, 1, 1)

        self.allLibsTableWidget = QTableWidget(self.tab_5)
        self.allLibsTableWidget.setObjectName(u"allLibsTableWidget")

        self.gridLayout_3.addWidget(self.allLibsTableWidget, 0, 0, 1, 6)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer, 2, 0, 1, 5)

        self.tabWidget.addTab(self.tab_5, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.verticalLayout_3 = QVBoxLayout(self.tab_4)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_2 = QLabel(self.tab_4)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setTextFormat(Qt.TextFormat.RichText)
        self.label_2.setScaledContents(True)
        self.label_2.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.label_2)

        self.licenseTextEdit = QTextEdit(self.tab_4)
        self.licenseTextEdit.setObjectName(u"licenseTextEdit")
        font = QFont()
        font.setFamilies([u"Cousine"])
        self.licenseTextEdit.setFont(font)
        self.licenseTextEdit.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByKeyboard|Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextBrowserInteraction|Qt.TextInteractionFlag.TextSelectableByKeyboard|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.verticalLayout_3.addWidget(self.licenseTextEdit)

        self.tabWidget.addTab(self.tab_4, "")

        self.verticalLayout_2.addWidget(self.tabWidget)


        self.retranslateUi(AboutDialog)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AboutDialog)
    # setupUi

    def retranslateUi(self, AboutDialog):
        AboutDialog.setWindowTitle(QCoreApplication.translate("AboutDialog", u"About VeraGrid", None))
        self.label_3.setText("")
        self.mainLabel.setText(QCoreApplication.translate("AboutDialog", u"<html><head/><body><p align=\"justify\"><span style=\" font-weight:600;\">VeraGrid</span> has been carefully crafted since 2015 to serve as a platform for research and consultancy. Visit <a href=\"https://www.eroots.tech/\"><span style=\" text-decoration: underline; color:#26a269;\">eRoots</span></a> for more details. The source of VeraGrid can be found <a href=\"https://github.com/SanPen/VeraGrid\"><span style=\" text-decoration: underline; color:#26a269;\">here.</span></a></p></body></html>", None))
        self.updateLabel.setText("")
        self.copyrightLabel.setText(QCoreApplication.translate("AboutDialog", u"Copyright", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("AboutDialog", u"About", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("AboutDialog", u"Contributors", None))
#if QT_CONFIG(tooltip)
        self.copyLibsButton.setToolTip(QCoreApplication.translate("AboutDialog", u"Copy the table", None))
#endif // QT_CONFIG(tooltip)
        self.copyLibsButton.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("AboutDialog", u"Libraries", None))
        self.label_2.setText(QCoreApplication.translate("AboutDialog", u"<html><head/><body><p align=\"justify\">This program comes with absolutelly no warranty. This is free software, and you are welcome to redistribute it under the conditions set by the license. VeraGrid is licensed under the <a href=\"https://www.mozilla.org/en-US/MPL/2.0/\"><span style=\" text-decoration: underline; color:#26a269;\">Mozilla Public License V2</span></a>.</p></body></html>", None))
        self.licenseTextEdit.setHtml(QCoreApplication.translate("AboutDialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Cousine'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">+==============+==========================================+</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">| Package      | License                                  |</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; mar"
                        "gin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">+==============+==========================================+</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">| setuptools   | MIT                                      |</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">+--------------+------------------------------------------+</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">| wheel        | MIT                                      |</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">+--------------+------"
                        "------------------------------------+</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">| PySide6      | LGPL                                     |</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">+--------------+------------------------------------------+</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">| numpy        | BSD                                      |</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">+--------------+------------------------------------------+</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-le"
                        "ft:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">| scipy        | BSD                                      |</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">+--------------+------------------------------------------+</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">| networkx     | BSD                                      |</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:11pt;\">+--------------+------------------------------------------+</span></p></body></html>", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("AboutDialog", u"License", None))
    # retranslateUi

