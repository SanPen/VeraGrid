# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'analysis_gui.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMenu, QMenuBar, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QStatusBar,
    QTabWidget, QTextBrowser, QTreeView, QVBoxLayout,
    QWidget)

from VeraGrid.Gui.Widgets.matplotlibwidget import MatplotlibWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1460, 920)
        MainWindow.setMinimumSize(QSize(1240, 760))
        self.actionAnalyze = QAction(MainWindow)
        self.actionAnalyze.setObjectName(u"actionAnalyze")
        self.actionFixIssues = QAction(MainWindow)
        self.actionFixIssues.setObjectName(u"actionFixIssues")
        self.actionSaveDiagnostic = QAction(MainWindow)
        self.actionSaveDiagnostic.setObjectName(u"actionSaveDiagnostic")
        self.actionExportReport = QAction(MainWindow)
        self.actionExportReport.setObjectName(u"actionExportReport")
        self.actionCopySigmaTable = QAction(MainWindow)
        self.actionCopySigmaTable.setObjectName(u"actionCopySigmaTable")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_6 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_6.setSpacing(14)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(18, 18, 18, 18)
        self.mainTabWidget = QTabWidget(self.centralwidget)
        self.mainTabWidget.setObjectName(u"mainTabWidget")
        self.mainTabWidget.setCurrentIndex(0)
        self.overviewPage = QWidget()
        self.overviewPage.setObjectName(u"overviewPage")
        self.verticalLayout_overviewPage = QVBoxLayout(self.overviewPage)
        self.verticalLayout_overviewPage.setObjectName(u"verticalLayout_overviewPage")
        self.verticalLayout_overviewPage.setContentsMargins(10, 10, 10, 10)
        self.overviewScrollArea = QScrollArea(self.overviewPage)
        self.overviewScrollArea.setObjectName(u"overviewScrollArea")
        self.overviewScrollArea.setFrameShape(QFrame.NoFrame)
        self.overviewScrollArea.setWidgetResizable(True)
        self.overviewScrollWidget = QWidget()
        self.overviewScrollWidget.setObjectName(u"overviewScrollWidget")
        self.verticalLayout_overviewScroll = QVBoxLayout(self.overviewScrollWidget)
        self.verticalLayout_overviewScroll.setSpacing(14)
        self.verticalLayout_overviewScroll.setObjectName(u"verticalLayout_overviewScroll")
        self.verticalLayout_overviewScroll.setContentsMargins(0, 0, 0, 0)
        self.heroFrame = QFrame(self.overviewScrollWidget)
        self.heroFrame.setObjectName(u"heroFrame")
        self.heroFrame.setFrameShape(QFrame.NoFrame)
        self.horizontalLayout_hero = QHBoxLayout(self.heroFrame)
        self.horizontalLayout_hero.setSpacing(20)
        self.horizontalLayout_hero.setObjectName(u"horizontalLayout_hero")
        self.horizontalLayout_hero.setContentsMargins(28, 24, 28, 24)
        self.verticalLayout_heroText = QVBoxLayout()
        self.verticalLayout_heroText.setSpacing(10)
        self.verticalLayout_heroText.setObjectName(u"verticalLayout_heroText")
        self.statusChipLabel = QLabel(self.heroFrame)
        self.statusChipLabel.setObjectName(u"statusChipLabel")

        self.verticalLayout_heroText.addWidget(self.statusChipLabel)

        self.titleLabel = QLabel(self.heroFrame)
        self.titleLabel.setObjectName(u"titleLabel")

        self.verticalLayout_heroText.addWidget(self.titleLabel)

        self.subtitleLabel = QLabel(self.heroFrame)
        self.subtitleLabel.setObjectName(u"subtitleLabel")
        self.subtitleLabel.setWordWrap(True)

        self.verticalLayout_heroText.addWidget(self.subtitleLabel)

        self.gridNameLabel = QLabel(self.heroFrame)
        self.gridNameLabel.setObjectName(u"gridNameLabel")

        self.verticalLayout_heroText.addWidget(self.gridNameLabel)


        self.horizontalLayout_hero.addLayout(self.verticalLayout_heroText)

        self.horizontalSpacer_hero = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_hero.addItem(self.horizontalSpacer_hero)

        self.verticalLayout_heroActions = QVBoxLayout()
        self.verticalLayout_heroActions.setSpacing(10)
        self.verticalLayout_heroActions.setObjectName(u"verticalLayout_heroActions")
        self.analyzeButton = QPushButton(self.heroFrame)
        self.analyzeButton.setObjectName(u"analyzeButton")

        self.verticalLayout_heroActions.addWidget(self.analyzeButton)

        self.fixIssuesButton = QPushButton(self.heroFrame)
        self.fixIssuesButton.setObjectName(u"fixIssuesButton")

        self.verticalLayout_heroActions.addWidget(self.fixIssuesButton)

        self.exportReportButton = QPushButton(self.heroFrame)
        self.exportReportButton.setObjectName(u"exportReportButton")

        self.verticalLayout_heroActions.addWidget(self.exportReportButton)


        self.horizontalLayout_hero.addLayout(self.verticalLayout_heroActions)


        self.verticalLayout_overviewScroll.addWidget(self.heroFrame)

        self.cardsWidget = QWidget(self.overviewScrollWidget)
        self.cardsWidget.setObjectName(u"cardsWidget")
        self.gridLayout_cards = QGridLayout(self.cardsWidget)
        self.gridLayout_cards.setObjectName(u"gridLayout_cards")
        self.gridLayout_cards.setHorizontalSpacing(14)
        self.gridLayout_cards.setVerticalSpacing(14)
        self.scoreCardFrame = QFrame(self.cardsWidget)
        self.scoreCardFrame.setObjectName(u"scoreCardFrame")
        self.scoreCardFrame.setMinimumSize(QSize(0, 138))
        self.scoreCardFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_scoreCard = QVBoxLayout(self.scoreCardFrame)
        self.verticalLayout_scoreCard.setSpacing(8)
        self.verticalLayout_scoreCard.setObjectName(u"verticalLayout_scoreCard")
        self.verticalLayout_scoreCard.setContentsMargins(22, 18, 22, 18)
        self.scoreCaptionLabel = QLabel(self.scoreCardFrame)
        self.scoreCaptionLabel.setObjectName(u"scoreCaptionLabel")

        self.verticalLayout_scoreCard.addWidget(self.scoreCaptionLabel)

        self.horizontalLayout_scoreValue = QHBoxLayout()
        self.horizontalLayout_scoreValue.setObjectName(u"horizontalLayout_scoreValue")
        self.scoreValueLabel = QLabel(self.scoreCardFrame)
        self.scoreValueLabel.setObjectName(u"scoreValueLabel")

        self.horizontalLayout_scoreValue.addWidget(self.scoreValueLabel)

        self.horizontalSpacer_scoreCard = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_scoreValue.addItem(self.horizontalSpacer_scoreCard)

        self.scoreGradeLabel = QLabel(self.scoreCardFrame)
        self.scoreGradeLabel.setObjectName(u"scoreGradeLabel")

        self.horizontalLayout_scoreValue.addWidget(self.scoreGradeLabel)


        self.verticalLayout_scoreCard.addLayout(self.horizontalLayout_scoreValue)

        self.scoreProgressBar = QProgressBar(self.scoreCardFrame)
        self.scoreProgressBar.setObjectName(u"scoreProgressBar")
        self.scoreProgressBar.setValue(0)
        self.scoreProgressBar.setTextVisible(False)

        self.verticalLayout_scoreCard.addWidget(self.scoreProgressBar)

        self.scoreExplainerLabel = QLabel(self.scoreCardFrame)
        self.scoreExplainerLabel.setObjectName(u"scoreExplainerLabel")
        self.scoreExplainerLabel.setWordWrap(True)

        self.verticalLayout_scoreCard.addWidget(self.scoreExplainerLabel)


        self.gridLayout_cards.addWidget(self.scoreCardFrame, 0, 0, 1, 1)

        self.issueCardFrame = QFrame(self.cardsWidget)
        self.issueCardFrame.setObjectName(u"issueCardFrame")
        self.issueCardFrame.setMinimumSize(QSize(0, 138))
        self.issueCardFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_issueCard = QVBoxLayout(self.issueCardFrame)
        self.verticalLayout_issueCard.setObjectName(u"verticalLayout_issueCard")
        self.verticalLayout_issueCard.setContentsMargins(22, 18, 22, 18)
        self.issueCaptionLabel = QLabel(self.issueCardFrame)
        self.issueCaptionLabel.setObjectName(u"issueCaptionLabel")

        self.verticalLayout_issueCard.addWidget(self.issueCaptionLabel)

        self.issueCountValueLabel = QLabel(self.issueCardFrame)
        self.issueCountValueLabel.setObjectName(u"issueCountValueLabel")

        self.verticalLayout_issueCard.addWidget(self.issueCountValueLabel)

        self.issueFootnoteLabel = QLabel(self.issueCardFrame)
        self.issueFootnoteLabel.setObjectName(u"issueFootnoteLabel")
        self.issueFootnoteLabel.setWordWrap(True)

        self.verticalLayout_issueCard.addWidget(self.issueFootnoteLabel)


        self.gridLayout_cards.addWidget(self.issueCardFrame, 0, 1, 1, 1)

        self.criticalCardFrame = QFrame(self.cardsWidget)
        self.criticalCardFrame.setObjectName(u"criticalCardFrame")
        self.criticalCardFrame.setMinimumSize(QSize(0, 138))
        self.criticalCardFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_criticalCard = QVBoxLayout(self.criticalCardFrame)
        self.verticalLayout_criticalCard.setObjectName(u"verticalLayout_criticalCard")
        self.verticalLayout_criticalCard.setContentsMargins(22, 18, 22, 18)
        self.criticalCaptionLabel = QLabel(self.criticalCardFrame)
        self.criticalCaptionLabel.setObjectName(u"criticalCaptionLabel")

        self.verticalLayout_criticalCard.addWidget(self.criticalCaptionLabel)

        self.criticalCountValueLabel = QLabel(self.criticalCardFrame)
        self.criticalCountValueLabel.setObjectName(u"criticalCountValueLabel")

        self.verticalLayout_criticalCard.addWidget(self.criticalCountValueLabel)

        self.criticalFootnoteLabel = QLabel(self.criticalCardFrame)
        self.criticalFootnoteLabel.setObjectName(u"criticalFootnoteLabel")
        self.criticalFootnoteLabel.setWordWrap(True)

        self.verticalLayout_criticalCard.addWidget(self.criticalFootnoteLabel)


        self.gridLayout_cards.addWidget(self.criticalCardFrame, 0, 2, 1, 1)

        self.fixableCardFrame = QFrame(self.cardsWidget)
        self.fixableCardFrame.setObjectName(u"fixableCardFrame")
        self.fixableCardFrame.setMinimumSize(QSize(0, 138))
        self.fixableCardFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_fixableCard = QVBoxLayout(self.fixableCardFrame)
        self.verticalLayout_fixableCard.setObjectName(u"verticalLayout_fixableCard")
        self.verticalLayout_fixableCard.setContentsMargins(22, 18, 22, 18)
        self.fixableCaptionLabel = QLabel(self.fixableCardFrame)
        self.fixableCaptionLabel.setObjectName(u"fixableCaptionLabel")

        self.verticalLayout_fixableCard.addWidget(self.fixableCaptionLabel)

        self.fixableCountValueLabel = QLabel(self.fixableCardFrame)
        self.fixableCountValueLabel.setObjectName(u"fixableCountValueLabel")

        self.verticalLayout_fixableCard.addWidget(self.fixableCountValueLabel)

        self.fixableFootnoteLabel = QLabel(self.fixableCardFrame)
        self.fixableFootnoteLabel.setObjectName(u"fixableFootnoteLabel")
        self.fixableFootnoteLabel.setWordWrap(True)

        self.verticalLayout_fixableCard.addWidget(self.fixableFootnoteLabel)


        self.gridLayout_cards.addWidget(self.fixableCardFrame, 1, 0, 1, 1)

        self.sigmaCardFrame = QFrame(self.cardsWidget)
        self.sigmaCardFrame.setObjectName(u"sigmaCardFrame")
        self.sigmaCardFrame.setMinimumSize(QSize(0, 138))
        self.sigmaCardFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_sigmaCard = QVBoxLayout(self.sigmaCardFrame)
        self.verticalLayout_sigmaCard.setObjectName(u"verticalLayout_sigmaCard")
        self.verticalLayout_sigmaCard.setContentsMargins(22, 18, 22, 18)
        self.sigmaCaptionLabel = QLabel(self.sigmaCardFrame)
        self.sigmaCaptionLabel.setObjectName(u"sigmaCaptionLabel")

        self.verticalLayout_sigmaCard.addWidget(self.sigmaCaptionLabel)

        self.sigmaHealthValueLabel = QLabel(self.sigmaCardFrame)
        self.sigmaHealthValueLabel.setObjectName(u"sigmaHealthValueLabel")

        self.verticalLayout_sigmaCard.addWidget(self.sigmaHealthValueLabel)

        self.sigmaFootnoteLabel = QLabel(self.sigmaCardFrame)
        self.sigmaFootnoteLabel.setObjectName(u"sigmaFootnoteLabel")
        self.sigmaFootnoteLabel.setWordWrap(True)

        self.verticalLayout_sigmaCard.addWidget(self.sigmaFootnoteLabel)


        self.gridLayout_cards.addWidget(self.sigmaCardFrame, 1, 1, 1, 1)

        self.overviewHintFrame = QFrame(self.cardsWidget)
        self.overviewHintFrame.setObjectName(u"overviewHintFrame")
        self.overviewHintFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_overviewHint = QVBoxLayout(self.overviewHintFrame)
        self.verticalLayout_overviewHint.setSpacing(10)
        self.verticalLayout_overviewHint.setObjectName(u"verticalLayout_overviewHint")
        self.verticalLayout_overviewHint.setContentsMargins(22, 18, 22, 18)
        self.overviewHintTitleLabel = QLabel(self.overviewHintFrame)
        self.overviewHintTitleLabel.setObjectName(u"overviewHintTitleLabel")

        self.verticalLayout_overviewHint.addWidget(self.overviewHintTitleLabel)

        self.overviewHintBodyLabel = QLabel(self.overviewHintFrame)
        self.overviewHintBodyLabel.setObjectName(u"overviewHintBodyLabel")
        self.overviewHintBodyLabel.setWordWrap(True)

        self.verticalLayout_overviewHint.addWidget(self.overviewHintBodyLabel)


        self.gridLayout_cards.addWidget(self.overviewHintFrame, 1, 2, 1, 1)


        self.verticalLayout_overviewScroll.addWidget(self.cardsWidget)

        self.overviewScrollArea.setWidget(self.overviewScrollWidget)

        self.verticalLayout_overviewPage.addWidget(self.overviewScrollArea)


        self.mainTabWidget.addTab(self.overviewPage, "")

        self.findingsPage = QWidget()
        self.findingsPage.setObjectName(u"findingsPage")
        self.verticalLayout_findingsPage = QVBoxLayout(self.findingsPage)
        self.verticalLayout_findingsPage.setObjectName(u"verticalLayout_findingsPage")
        self.verticalLayout_findingsPage.setContentsMargins(10, 10, 10, 10)
        self.findingsFrame = QFrame(self.findingsPage)
        self.findingsFrame.setObjectName(u"findingsFrame")
        self.findingsFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_findings = QVBoxLayout(self.findingsFrame)
        self.verticalLayout_findings.setSpacing(12)
        self.verticalLayout_findings.setObjectName(u"verticalLayout_findings")
        self.verticalLayout_findings.setContentsMargins(22, 18, 22, 18)
        self.horizontalLayout_findingsHeader = QHBoxLayout()
        self.horizontalLayout_findingsHeader.setObjectName(u"horizontalLayout_findingsHeader")
        self.findingsTitleLabel = QLabel(self.findingsFrame)
        self.findingsTitleLabel.setObjectName(u"findingsTitleLabel")

        self.horizontalLayout_findingsHeader.addWidget(self.findingsTitleLabel)

        self.horizontalSpacer_findingsHeader = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_findingsHeader.addItem(self.horizontalSpacer_findingsHeader)

        self.expandAllIssuesButton = QPushButton(self.findingsFrame)
        self.expandAllIssuesButton.setObjectName(u"expandAllIssuesButton")

        self.horizontalLayout_findingsHeader.addWidget(self.expandAllIssuesButton)

        self.collapseAllIssuesButton = QPushButton(self.findingsFrame)
        self.collapseAllIssuesButton.setObjectName(u"collapseAllIssuesButton")

        self.horizontalLayout_findingsHeader.addWidget(self.collapseAllIssuesButton)

        self.filtersHintLabel = QLabel(self.findingsFrame)
        self.filtersHintLabel.setObjectName(u"filtersHintLabel")

        self.horizontalLayout_findingsHeader.addWidget(self.filtersHintLabel)


        self.verticalLayout_findings.addLayout(self.horizontalLayout_findingsHeader)

        self.horizontalLayout_filters = QHBoxLayout()
        self.horizontalLayout_filters.setSpacing(10)
        self.horizontalLayout_filters.setObjectName(u"horizontalLayout_filters")
        self.severityFilterComboBox = QComboBox(self.findingsFrame)
        self.severityFilterComboBox.setObjectName(u"severityFilterComboBox")

        self.horizontalLayout_filters.addWidget(self.severityFilterComboBox)

        self.objectTypeFilterComboBox = QComboBox(self.findingsFrame)
        self.objectTypeFilterComboBox.setObjectName(u"objectTypeFilterComboBox")

        self.horizontalLayout_filters.addWidget(self.objectTypeFilterComboBox)

        self.fixableOnlyCheckBox = QCheckBox(self.findingsFrame)
        self.fixableOnlyCheckBox.setObjectName(u"fixableOnlyCheckBox")

        self.horizontalLayout_filters.addWidget(self.fixableOnlyCheckBox)

        self.issueSearchLineEdit = QLineEdit(self.findingsFrame)
        self.issueSearchLineEdit.setObjectName(u"issueSearchLineEdit")

        self.horizontalLayout_filters.addWidget(self.issueSearchLineEdit)


        self.verticalLayout_findings.addLayout(self.horizontalLayout_filters)

        self.issuesTreeView = QTreeView(self.findingsFrame)
        self.issuesTreeView.setObjectName(u"issuesTreeView")

        self.verticalLayout_findings.addWidget(self.issuesTreeView)


        self.verticalLayout_findingsPage.addWidget(self.findingsFrame)


        self.mainTabWidget.addTab(self.findingsPage, "")

        self.narrativePage = QWidget()
        self.narrativePage.setObjectName(u"narrativePage")
        self.verticalLayout_narrativePage = QVBoxLayout(self.narrativePage)
        self.verticalLayout_narrativePage.setObjectName(u"verticalLayout_narrativePage")
        self.verticalLayout_narrativePage.setContentsMargins(10, 10, 10, 10)
        self.narrativeFrame = QFrame(self.narrativePage)
        self.narrativeFrame.setObjectName(u"narrativeFrame")
        self.narrativeFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_narrative = QVBoxLayout(self.narrativeFrame)
        self.verticalLayout_narrative.setSpacing(12)
        self.verticalLayout_narrative.setObjectName(u"verticalLayout_narrative")
        self.verticalLayout_narrative.setContentsMargins(22, 18, 22, 18)
        self.narrativeTitleLabel = QLabel(self.narrativeFrame)
        self.narrativeTitleLabel.setObjectName(u"narrativeTitleLabel")

        self.verticalLayout_narrative.addWidget(self.narrativeTitleLabel)

        self.narrativeBrowser = QTextBrowser(self.narrativeFrame)
        self.narrativeBrowser.setObjectName(u"narrativeBrowser")
        self.narrativeBrowser.setOpenExternalLinks(False)

        self.verticalLayout_narrative.addWidget(self.narrativeBrowser)


        self.verticalLayout_narrativePage.addWidget(self.narrativeFrame)


        self.mainTabWidget.addTab(self.narrativePage, "")

        self.sigmaPage = QWidget()
        self.sigmaPage.setObjectName(u"sigmaPage")
        self.verticalLayout_sigmaPage = QVBoxLayout(self.sigmaPage)
        self.verticalLayout_sigmaPage.setObjectName(u"verticalLayout_sigmaPage")
        self.verticalLayout_sigmaPage.setContentsMargins(10, 10, 10, 10)
        self.sigmaPanelFrame = QFrame(self.sigmaPage)
        self.sigmaPanelFrame.setObjectName(u"sigmaPanelFrame")
        self.sigmaPanelFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_sigmaPanel = QVBoxLayout(self.sigmaPanelFrame)
        self.verticalLayout_sigmaPanel.setSpacing(12)
        self.verticalLayout_sigmaPanel.setObjectName(u"verticalLayout_sigmaPanel")
        self.verticalLayout_sigmaPanel.setContentsMargins(22, 18, 22, 18)
        self.horizontalLayout_sigmaHeader = QHBoxLayout()
        self.horizontalLayout_sigmaHeader.setObjectName(u"horizontalLayout_sigmaHeader")
        self.sigmaTitleLabel = QLabel(self.sigmaPanelFrame)
        self.sigmaTitleLabel.setObjectName(u"sigmaTitleLabel")

        self.horizontalLayout_sigmaHeader.addWidget(self.sigmaTitleLabel)

        self.horizontalSpacer_sigmaHeader = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_sigmaHeader.addItem(self.horizontalSpacer_sigmaHeader)

        self.sigmaStatusLabel = QLabel(self.sigmaPanelFrame)
        self.sigmaStatusLabel.setObjectName(u"sigmaStatusLabel")

        self.horizontalLayout_sigmaHeader.addWidget(self.sigmaStatusLabel)


        self.verticalLayout_sigmaPanel.addLayout(self.horizontalLayout_sigmaHeader)

        self.sigmaPlotWidget = MatplotlibWidget(self.sigmaPanelFrame)
        self.sigmaPlotWidget.setObjectName(u"sigmaPlotWidget")

        self.verticalLayout_sigmaPanel.addWidget(self.sigmaPlotWidget)


        self.verticalLayout_sigmaPage.addWidget(self.sigmaPanelFrame)


        self.mainTabWidget.addTab(self.sigmaPage, "")

        self.controlsPage = QWidget()
        self.controlsPage.setObjectName(u"controlsPage")
        self.verticalLayout_controlsPage = QVBoxLayout(self.controlsPage)
        self.verticalLayout_controlsPage.setObjectName(u"verticalLayout_controlsPage")
        self.verticalLayout_controlsPage.setContentsMargins(10, 10, 10, 10)
        self.controlsFrame = QFrame(self.controlsPage)
        self.controlsFrame.setObjectName(u"controlsFrame")
        self.controlsFrame.setFrameShape(QFrame.NoFrame)
        self.verticalLayout_controls = QVBoxLayout(self.controlsFrame)
        self.verticalLayout_controls.setSpacing(12)
        self.verticalLayout_controls.setObjectName(u"verticalLayout_controls")
        self.verticalLayout_controls.setContentsMargins(22, 18, 22, 18)
        self.controlsTitleLabel = QLabel(self.controlsFrame)
        self.controlsTitleLabel.setObjectName(u"controlsTitleLabel")

        self.verticalLayout_controls.addWidget(self.controlsTitleLabel)

        self.controlsHintLabel = QLabel(self.controlsFrame)
        self.controlsHintLabel.setObjectName(u"controlsHintLabel")
        self.controlsHintLabel.setWordWrap(True)

        self.verticalLayout_controls.addWidget(self.controlsHintLabel)

        self.controlsScrollArea = QScrollArea(self.controlsFrame)
        self.controlsScrollArea.setObjectName(u"controlsScrollArea")
        self.controlsScrollArea.setFrameShape(QFrame.NoFrame)
        self.controlsScrollArea.setWidgetResizable(True)
        self.controlsScrollWidget = QWidget()
        self.controlsScrollWidget.setObjectName(u"controlsScrollWidget")
        self.verticalLayout_controlsScroll = QVBoxLayout(self.controlsScrollWidget)
        self.verticalLayout_controlsScroll.setSpacing(12)
        self.verticalLayout_controlsScroll.setObjectName(u"verticalLayout_controlsScroll")
        self.verticalLayout_controlsScroll.setContentsMargins(0, 0, 0, 0)
        self.formLayout_controls = QFormLayout()
        self.formLayout_controls.setObjectName(u"formLayout_controls")
        self.formLayout_controls.setLabelAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.formLayout_controls.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.formLayout_controls.setHorizontalSpacing(12)
        self.formLayout_controls.setVerticalSpacing(12)
        self.activePowerImbalanceLabel = QLabel(self.controlsScrollWidget)
        self.activePowerImbalanceLabel.setObjectName(u"activePowerImbalanceLabel")

        self.formLayout_controls.setWidget(0, QFormLayout.ItemRole.LabelRole, self.activePowerImbalanceLabel)

        self.activePowerImbalanceSpinBox = QDoubleSpinBox(self.controlsScrollWidget)
        self.activePowerImbalanceSpinBox.setObjectName(u"activePowerImbalanceSpinBox")
        self.activePowerImbalanceSpinBox.setDecimals(2)
        self.activePowerImbalanceSpinBox.setMaximum(100.000000000000000)
        self.activePowerImbalanceSpinBox.setValue(2.000000000000000)

        self.formLayout_controls.setWidget(0, QFormLayout.ItemRole.FieldRole, self.activePowerImbalanceSpinBox)

        self.genVsetLabel = QLabel(self.controlsScrollWidget)
        self.genVsetLabel.setObjectName(u"genVsetLabel")

        self.formLayout_controls.setWidget(1, QFormLayout.ItemRole.LabelRole, self.genVsetLabel)

        self.horizontalLayout_genVset = QHBoxLayout()
        self.horizontalLayout_genVset.setObjectName(u"horizontalLayout_genVset")
        self.genVsetMinSpinBox = QDoubleSpinBox(self.controlsScrollWidget)
        self.genVsetMinSpinBox.setObjectName(u"genVsetMinSpinBox")
        self.genVsetMinSpinBox.setDecimals(3)
        self.genVsetMinSpinBox.setMaximum(10.000000000000000)
        self.genVsetMinSpinBox.setSingleStep(0.010000000000000)
        self.genVsetMinSpinBox.setValue(0.950000000000000)

        self.horizontalLayout_genVset.addWidget(self.genVsetMinSpinBox)

        self.genVsetMaxSpinBox = QDoubleSpinBox(self.controlsScrollWidget)
        self.genVsetMaxSpinBox.setObjectName(u"genVsetMaxSpinBox")
        self.genVsetMaxSpinBox.setDecimals(3)
        self.genVsetMaxSpinBox.setMaximum(10.000000000000000)
        self.genVsetMaxSpinBox.setSingleStep(0.010000000000000)
        self.genVsetMaxSpinBox.setValue(1.050000000000000)

        self.horizontalLayout_genVset.addWidget(self.genVsetMaxSpinBox)


        self.formLayout_controls.setLayout(1, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_genVset)

        self.tapModuleLabel = QLabel(self.controlsScrollWidget)
        self.tapModuleLabel.setObjectName(u"tapModuleLabel")

        self.formLayout_controls.setWidget(2, QFormLayout.ItemRole.LabelRole, self.tapModuleLabel)

        self.horizontalLayout_tapModule = QHBoxLayout()
        self.horizontalLayout_tapModule.setObjectName(u"horizontalLayout_tapModule")
        self.transformerTapModuleMinSpinBox = QDoubleSpinBox(self.controlsScrollWidget)
        self.transformerTapModuleMinSpinBox.setObjectName(u"transformerTapModuleMinSpinBox")
        self.transformerTapModuleMinSpinBox.setDecimals(3)
        self.transformerTapModuleMinSpinBox.setMaximum(10.000000000000000)
        self.transformerTapModuleMinSpinBox.setSingleStep(0.010000000000000)
        self.transformerTapModuleMinSpinBox.setValue(0.950000000000000)

        self.horizontalLayout_tapModule.addWidget(self.transformerTapModuleMinSpinBox)

        self.transformerTapModuleMaxSpinBox = QDoubleSpinBox(self.controlsScrollWidget)
        self.transformerTapModuleMaxSpinBox.setObjectName(u"transformerTapModuleMaxSpinBox")
        self.transformerTapModuleMaxSpinBox.setDecimals(3)
        self.transformerTapModuleMaxSpinBox.setMaximum(10.000000000000000)
        self.transformerTapModuleMaxSpinBox.setSingleStep(0.010000000000000)
        self.transformerTapModuleMaxSpinBox.setValue(1.050000000000000)

        self.horizontalLayout_tapModule.addWidget(self.transformerTapModuleMaxSpinBox)


        self.formLayout_controls.setLayout(2, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_tapModule)

        self.virtualTapToleranceLabel = QLabel(self.controlsScrollWidget)
        self.virtualTapToleranceLabel.setObjectName(u"virtualTapToleranceLabel")

        self.formLayout_controls.setWidget(3, QFormLayout.ItemRole.LabelRole, self.virtualTapToleranceLabel)

        self.virtualTapToleranceSpinBox = QDoubleSpinBox(self.controlsScrollWidget)
        self.virtualTapToleranceSpinBox.setObjectName(u"virtualTapToleranceSpinBox")
        self.virtualTapToleranceSpinBox.setDecimals(2)
        self.virtualTapToleranceSpinBox.setMaximum(1000.000000000000000)
        self.virtualTapToleranceSpinBox.setValue(10.000000000000000)

        self.formLayout_controls.setWidget(3, QFormLayout.ItemRole.FieldRole, self.virtualTapToleranceSpinBox)

        self.lineVoltageToleranceLabel = QLabel(self.controlsScrollWidget)
        self.lineVoltageToleranceLabel.setObjectName(u"lineVoltageToleranceLabel")

        self.formLayout_controls.setWidget(4, QFormLayout.ItemRole.LabelRole, self.lineVoltageToleranceLabel)

        self.lineNominalVoltageToleranceSpinBox = QDoubleSpinBox(self.controlsScrollWidget)
        self.lineNominalVoltageToleranceSpinBox.setObjectName(u"lineNominalVoltageToleranceSpinBox")
        self.lineNominalVoltageToleranceSpinBox.setDecimals(2)
        self.lineNominalVoltageToleranceSpinBox.setMaximum(1000.000000000000000)
        self.lineNominalVoltageToleranceSpinBox.setValue(10.000000000000000)

        self.formLayout_controls.setWidget(4, QFormLayout.ItemRole.FieldRole, self.lineNominalVoltageToleranceSpinBox)

        self.transformerVccLabel = QLabel(self.controlsScrollWidget)
        self.transformerVccLabel.setObjectName(u"transformerVccLabel")

        self.formLayout_controls.setWidget(5, QFormLayout.ItemRole.LabelRole, self.transformerVccLabel)

        self.horizontalLayout_vcc = QHBoxLayout()
        self.horizontalLayout_vcc.setObjectName(u"horizontalLayout_vcc")
        self.transformerVccMinSpinBox = QDoubleSpinBox(self.controlsScrollWidget)
        self.transformerVccMinSpinBox.setObjectName(u"transformerVccMinSpinBox")
        self.transformerVccMinSpinBox.setDecimals(2)
        self.transformerVccMinSpinBox.setMaximum(100.000000000000000)
        self.transformerVccMinSpinBox.setValue(8.000000000000000)

        self.horizontalLayout_vcc.addWidget(self.transformerVccMinSpinBox)

        self.transformerVccMaxSpinBox = QDoubleSpinBox(self.controlsScrollWidget)
        self.transformerVccMaxSpinBox.setObjectName(u"transformerVccMaxSpinBox")
        self.transformerVccMaxSpinBox.setDecimals(2)
        self.transformerVccMaxSpinBox.setMaximum(100.000000000000000)
        self.transformerVccMaxSpinBox.setValue(18.000000000000000)

        self.horizontalLayout_vcc.addWidget(self.transformerVccMaxSpinBox)


        self.formLayout_controls.setLayout(5, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_vcc)


        self.verticalLayout_controlsScroll.addLayout(self.formLayout_controls)

        self.fixTimeSeriesCheckBox = QCheckBox(self.controlsScrollWidget)
        self.fixTimeSeriesCheckBox.setObjectName(u"fixTimeSeriesCheckBox")
        self.fixTimeSeriesCheckBox.setChecked(True)

        self.verticalLayout_controlsScroll.addWidget(self.fixTimeSeriesCheckBox)

        self.verticalSpacer_controls = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_controlsScroll.addItem(self.verticalSpacer_controls)

        self.controlsScrollArea.setWidget(self.controlsScrollWidget)

        self.verticalLayout_controls.addWidget(self.controlsScrollArea)


        self.verticalLayout_controlsPage.addWidget(self.controlsFrame)


        self.mainTabWidget.addTab(self.controlsPage, "")

        self.verticalLayout_6.addWidget(self.mainTabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1460, 22))
        self.menuActions = QMenu(self.menubar)
        self.menuActions.setObjectName(u"menuActions")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuActions.menuAction())
        self.menuActions.addAction(self.actionAnalyze)
        self.menuActions.addAction(self.actionFixIssues)
        self.menuActions.addAction(self.actionExportReport)
        self.menuActions.addAction(self.actionSaveDiagnostic)
        self.menuActions.addAction(self.actionCopySigmaTable)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Grid Health Dashboard", None))
        self.actionAnalyze.setText(QCoreApplication.translate("MainWindow", u"Refresh score", None))
        self.actionFixIssues.setText(QCoreApplication.translate("MainWindow", u"Fix safe issues", None))
        self.actionSaveDiagnostic.setText(QCoreApplication.translate("MainWindow", u"Export issues only", None))
        self.actionExportReport.setText(QCoreApplication.translate("MainWindow", u"Export full report", None))
        self.actionCopySigmaTable.setText(QCoreApplication.translate("MainWindow", u"Copy sigma table", None))
        self.statusChipLabel.setText(QCoreApplication.translate("MainWindow", u"SCORING DASHBOARD", None))
        self.titleLabel.setText(QCoreApplication.translate("MainWindow", u"Grid Health Dashboard", None))
        self.subtitleLabel.setText(QCoreApplication.translate("MainWindow", u"One dashboard for structural issues, numerical conditioning and sigma stability margin. Review what is wrong, fix safe items and export a decision-ready report.", None))
        self.gridNameLabel.setText(QCoreApplication.translate("MainWindow", u"Grid", None))
        self.analyzeButton.setText(QCoreApplication.translate("MainWindow", u"Refresh Score", None))
        self.fixIssuesButton.setText(QCoreApplication.translate("MainWindow", u"Fix Safe Issues", None))
        self.exportReportButton.setText(QCoreApplication.translate("MainWindow", u"Export Report", None))
        self.scoreCaptionLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardCaption", None))
        self.scoreCaptionLabel.setText(QCoreApplication.translate("MainWindow", u"Overall Score", None))
        self.scoreValueLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardValue", None))
        self.scoreValueLabel.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.scoreGradeLabel.setText(QCoreApplication.translate("MainWindow", u"Grade --", None))
        self.scoreExplainerLabel.setText(QCoreApplication.translate("MainWindow", u"Score blends issue severity with sigma stability margin.", None))
        self.issueCaptionLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardCaption", None))
        self.issueCaptionLabel.setText(QCoreApplication.translate("MainWindow", u"Total Findings", None))
        self.issueCountValueLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardValue", None))
        self.issueCountValueLabel.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.issueFootnoteLabel.setText(QCoreApplication.translate("MainWindow", u"All messages included in the current score.", None))
        self.criticalCaptionLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardCaption", None))
        self.criticalCaptionLabel.setText(QCoreApplication.translate("MainWindow", u"Critical Issues", None))
        self.criticalCountValueLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardValue", None))
        self.criticalCountValueLabel.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.criticalFootnoteLabel.setText(QCoreApplication.translate("MainWindow", u"Errors and divergences deserve first attention.", None))
        self.fixableCaptionLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardCaption", None))
        self.fixableCaptionLabel.setText(QCoreApplication.translate("MainWindow", u"Auto-Fix Ready", None))
        self.fixableCountValueLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardValue", None))
        self.fixableCountValueLabel.setText(QCoreApplication.translate("MainWindow", u"0", None))
        self.fixableFootnoteLabel.setText(QCoreApplication.translate("MainWindow", u"Safe corrections available from the dashboard.", None))
        self.sigmaCaptionLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardCaption", None))
        self.sigmaCaptionLabel.setText(QCoreApplication.translate("MainWindow", u"Sigma Margin", None))
        self.sigmaHealthValueLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"cardValue", None))
        self.sigmaHealthValueLabel.setText(QCoreApplication.translate("MainWindow", u"--", None))
        self.sigmaFootnoteLabel.setText(QCoreApplication.translate("MainWindow", u"Minimum stability distance from the sigma boundary.", None))
        self.overviewHintTitleLabel.setText(QCoreApplication.translate("MainWindow", u"How To Use This Dashboard", None))
        self.overviewHintBodyLabel.setText(QCoreApplication.translate("MainWindow", u"Use the tabs below to review the executive overview, detailed findings, action narrative, sigma stability view and threshold controls.", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.overviewPage), QCoreApplication.translate("MainWindow", u"Executive Overview", None))
        self.findingsTitleLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"sectionTitle", None))
        self.findingsTitleLabel.setText(QCoreApplication.translate("MainWindow", u"Findings", None))
        self.expandAllIssuesButton.setText(QCoreApplication.translate("MainWindow", u"Expand All", None))
        self.collapseAllIssuesButton.setText(QCoreApplication.translate("MainWindow", u"Collapse All", None))
        self.filtersHintLabel.setText(QCoreApplication.translate("MainWindow", u"Filter by severity, auto-fix support or free text.", None))
        self.fixableOnlyCheckBox.setText(QCoreApplication.translate("MainWindow", u"Only auto-fixable", None))
        self.issueSearchLineEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Search message, device, property or value", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.findingsPage), QCoreApplication.translate("MainWindow", u"Findings Explorer", None))
        self.narrativeTitleLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"sectionTitle", None))
        self.narrativeTitleLabel.setText(QCoreApplication.translate("MainWindow", u"What Needs Attention", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.narrativePage), QCoreApplication.translate("MainWindow", u"Action Narrative", None))
        self.sigmaTitleLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"sectionTitle", None))
        self.sigmaTitleLabel.setText(QCoreApplication.translate("MainWindow", u"Sigma Stability", None))
        self.sigmaStatusLabel.setText(QCoreApplication.translate("MainWindow", u"Sigma analysis pending.", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.sigmaPage), QCoreApplication.translate("MainWindow", u"Sigma Stability", None))
        self.controlsTitleLabel.setProperty(u"cssClass", QCoreApplication.translate("MainWindow", u"sectionTitle", None))
        self.controlsTitleLabel.setText(QCoreApplication.translate("MainWindow", u"Assessment Controls", None))
        self.controlsHintLabel.setText(QCoreApplication.translate("MainWindow", u"Adjust the guardrails used by the diagnostics, then refresh the score to compare scenarios before exporting the report.", None))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.controlsPage), QCoreApplication.translate("MainWindow", u"Assessment Controls", None))
        self.activePowerImbalanceLabel.setText(QCoreApplication.translate("MainWindow", u"Active power imbalance (%)", None))
        self.genVsetLabel.setText(QCoreApplication.translate("MainWindow", u"Generator Vset range (min / max)", None))
        self.tapModuleLabel.setText(QCoreApplication.translate("MainWindow", u"Transformer tap module (min / max)", None))
        self.virtualTapToleranceLabel.setText(QCoreApplication.translate("MainWindow", u"Virtual tap tolerance (%)", None))
        self.lineVoltageToleranceLabel.setText(QCoreApplication.translate("MainWindow", u"Line voltage mismatch tolerance (%)", None))
        self.transformerVccLabel.setText(QCoreApplication.translate("MainWindow", u"Transformer Vcc (%) min / max", None))
        self.fixTimeSeriesCheckBox.setText(QCoreApplication.translate("MainWindow", u"Apply safe fixes to time-series profiles too", None))
        self.menuActions.setTitle(QCoreApplication.translate("MainWindow", u"Actions", None))
    # retranslateUi
