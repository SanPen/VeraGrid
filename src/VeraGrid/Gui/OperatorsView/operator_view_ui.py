# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'operator_view.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QSizePolicy,
    QSplitter, QTableView, QToolBar, QVBoxLayout,
    QWidget)
from VeraGrid.Gui.Icons.icons_rc import *

class Ui_OperatorView(object):
    def setupUi(self, OperatorView):
        if not OperatorView.objectName():
            OperatorView.setObjectName(u"OperatorView")
        OperatorView.resize(1116, 537)
        icon = QIcon()
        icon.addFile(u":/Icons/icons/operator_view.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        OperatorView.setWindowIcon(icon)
        self.actionPower_flow = QAction(OperatorView)
        self.actionPower_flow.setObjectName(u"actionPower_flow")
        icon1 = QIcon()
        icon1.addFile(u":/Icons/icons/pf.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionPower_flow.setIcon(icon1)
        self.actionShort_Circuit = QAction(OperatorView)
        self.actionShort_Circuit.setObjectName(u"actionShort_Circuit")
        icon2 = QIcon()
        icon2.addFile(u":/Icons/icons/short_circuit.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionShort_Circuit.setIcon(icon2)
        self.actionRun_Dynamic_RMS_Simulation = QAction(OperatorView)
        self.actionRun_Dynamic_RMS_Simulation.setObjectName(u"actionRun_Dynamic_RMS_Simulation")
        icon3 = QIcon()
        icon3.addFile(u":/Icons/icons/dyn.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionRun_Dynamic_RMS_Simulation.setIcon(icon3)
        self.actionOPF = QAction(OperatorView)
        self.actionOPF.setObjectName(u"actionOPF")
        icon4 = QIcon()
        icon4.addFile(u":/Icons/icons/dcopf.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.actionOPF.setIcon(icon4)
        self.centralwidget = QWidget(OperatorView)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralLayout = QVBoxLayout(self.centralwidget)
        self.centralLayout.setObjectName(u"centralLayout")
        self.centralLayout.setContentsMargins(6, 6, 6, 6)
        self.mainSplitter = QSplitter(self.centralwidget)
        self.mainSplitter.setObjectName(u"mainSplitter")
        self.mainSplitter.setOrientation(Qt.Orientation.Horizontal)
        self.deviceListFrame = QFrame(self.mainSplitter)
        self.deviceListFrame.setObjectName(u"deviceListFrame")
        self.deviceListFrame.setMinimumSize(QSize(300, 0))
        self.deviceListFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.deviceListLayout = QVBoxLayout(self.deviceListFrame)
        self.deviceListLayout.setObjectName(u"deviceListLayout")
        self.deviceListLayout.setContentsMargins(0, 0, 0, 0)
        self.deviceTypeComboBox = QComboBox(self.deviceListFrame)
        self.deviceTypeComboBox.setObjectName(u"deviceTypeComboBox")

        self.deviceListLayout.addWidget(self.deviceTypeComboBox)

        self.devicesTableView = QTableView(self.deviceListFrame)
        self.devicesTableView.setObjectName(u"devicesTableView")
        self.devicesTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.deviceListLayout.addWidget(self.devicesTableView)

        self.deviceSearchLineEdit = QLineEdit(self.deviceListFrame)
        self.deviceSearchLineEdit.setObjectName(u"deviceSearchLineEdit")
        self.deviceSearchLineEdit.setClearButtonEnabled(True)

        self.deviceListLayout.addWidget(self.deviceSearchLineEdit)

        self.mainSplitter.addWidget(self.deviceListFrame)
        self.leftSplitter = QSplitter(self.mainSplitter)
        self.leftSplitter.setObjectName(u"leftSplitter")
        self.leftSplitter.setOrientation(Qt.Orientation.Vertical)
        self.operatorDiagramPanelFrame = QFrame(self.leftSplitter)
        self.operatorDiagramPanelFrame.setObjectName(u"operatorDiagramPanelFrame")
        self.operatorDiagramPanelFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.operatorDiagramLayout = QVBoxLayout(self.operatorDiagramPanelFrame)
        self.operatorDiagramLayout.setObjectName(u"operatorDiagramLayout")
        self.operatorDiagramLayout.setContentsMargins(0, 0, 0, 0)
        self.operatorDiagramLabel = QLabel(self.operatorDiagramPanelFrame)
        self.operatorDiagramLabel.setObjectName(u"operatorDiagramLabel")

        self.operatorDiagramLayout.addWidget(self.operatorDiagramLabel)

        self.operatorDiagramFrame = QFrame(self.operatorDiagramPanelFrame)
        self.operatorDiagramFrame.setObjectName(u"operatorDiagramFrame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.operatorDiagramFrame.sizePolicy().hasHeightForWidth())
        self.operatorDiagramFrame.setSizePolicy(sizePolicy)
        self.operatorDiagramFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.operatorDiagramFrame.setFrameShadow(QFrame.Shadow.Sunken)
        self.operatorDiagramContentLayout = QVBoxLayout(self.operatorDiagramFrame)
        self.operatorDiagramContentLayout.setObjectName(u"operatorDiagramContentLayout")
        self.operatorDiagramContentLayout.setContentsMargins(0, 0, 0, 0)

        self.operatorDiagramLayout.addWidget(self.operatorDiagramFrame)

        self.leftSplitter.addWidget(self.operatorDiagramPanelFrame)
        self.selectionInformationFrame = QFrame(self.leftSplitter)
        self.selectionInformationFrame.setObjectName(u"selectionInformationFrame")
        self.selectionInformationFrame.setFrameShape(QFrame.Shape.NoFrame)
        self.selectionInformationLayout = QVBoxLayout(self.selectionInformationFrame)
        self.selectionInformationLayout.setObjectName(u"selectionInformationLayout")
        self.selectionInformationLayout.setContentsMargins(0, 0, 0, 0)
        self.selectionInformationLabel = QLabel(self.selectionInformationFrame)
        self.selectionInformationLabel.setObjectName(u"selectionInformationLabel")

        self.selectionInformationLayout.addWidget(self.selectionInformationLabel)

        self.selectionInformationTableView = QTableView(self.selectionInformationFrame)
        self.selectionInformationTableView.setObjectName(u"selectionInformationTableView")
        self.selectionInformationTableView.setFrameShape(QFrame.Shape.NoFrame)

        self.selectionInformationLayout.addWidget(self.selectionInformationTableView)

        self.leftSplitter.addWidget(self.selectionInformationFrame)
        self.mainSplitter.addWidget(self.leftSplitter)

        self.centralLayout.addWidget(self.mainSplitter)

        OperatorView.setCentralWidget(self.centralwidget)
        self.toolBar = QToolBar(OperatorView)
        self.toolBar.setObjectName(u"toolBar")
        self.simulationResultsComboBox = QComboBox(self.toolBar)
        self.simulationResultsComboBox.setObjectName(u"simulationResultsComboBox")
        self.simulationResultsComboBox.setMinimumSize(QSize(180, 0))
        self.toolBar.addWidget(self.simulationResultsComboBox)
        OperatorView.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolBar)

        self.toolBar.addAction(self.actionPower_flow)
        self.toolBar.addAction(self.actionShort_Circuit)
        self.toolBar.addAction(self.actionRun_Dynamic_RMS_Simulation)
        self.toolBar.addAction(self.actionOPF)

        self.retranslateUi(OperatorView)

        QMetaObject.connectSlotsByName(OperatorView)
    # setupUi

    def retranslateUi(self, OperatorView):
        OperatorView.setWindowTitle(QCoreApplication.translate("OperatorView", u"Operator View", None))
        self.actionPower_flow.setText(QCoreApplication.translate("OperatorView", u"Power Flow", None))
#if QT_CONFIG(tooltip)
        self.actionPower_flow.setToolTip(QCoreApplication.translate("OperatorView", u"Run a power flow analysis", None))
#endif // QT_CONFIG(tooltip)
        self.actionShort_Circuit.setText(QCoreApplication.translate("OperatorView", u"Short Circuit", None))
#if QT_CONFIG(tooltip)
        self.actionShort_Circuit.setToolTip(QCoreApplication.translate("OperatorView", u"Run a short circuit study over the snapshot data", None))
#endif // QT_CONFIG(tooltip)
        self.actionRun_Dynamic_RMS_Simulation.setText(QCoreApplication.translate("OperatorView", u"Dynamic RMS Simulation", None))
#if QT_CONFIG(tooltip)
        self.actionRun_Dynamic_RMS_Simulation.setToolTip(QCoreApplication.translate("OperatorView", u"Run a dynamic RMS simulation", None))
#endif // QT_CONFIG(tooltip)
        self.actionOPF.setText(QCoreApplication.translate("OperatorView", u"Optimal Power Flow", None))
#if QT_CONFIG(tooltip)
        self.actionOPF.setToolTip(QCoreApplication.translate("OperatorView", u"Run an optimal power flow analysis", None))
#endif // QT_CONFIG(tooltip)
        self.deviceSearchLineEdit.setPlaceholderText(QCoreApplication.translate("OperatorView", u"Search devices", None))
        self.operatorDiagramLabel.setText(QCoreApplication.translate("OperatorView", u"Operator diagrams", None))
        self.selectionInformationLabel.setText(QCoreApplication.translate("OperatorView", u"Selection information", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("OperatorView", u"toolBar", None))
#if QT_CONFIG(tooltip)
        self.simulationResultsComboBox.setToolTip(QCoreApplication.translate("OperatorView", u"Available simulation results to show on the operator diagram", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi
