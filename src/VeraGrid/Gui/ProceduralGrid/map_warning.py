from PySide6 import QtWidgets
from VeraGrid.Gui.ProceduralGrid.map_warning_ui import Ui_Dialog


class MapWarningDialog(QtWidgets.QDialog):
    """
    Warning dialog for missing Map diagram selection.
    """

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = Ui_Dialog() # antes era self.ui = Ui_MapWarningDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr('Action Required'))

        # Connect the OK button to close the window
        self.ui.okButton.clicked.connect(self.accept)