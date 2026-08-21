# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import sys
import numpy as np
from PySide6 import QtWidgets

from VeraGrid.Gui.SigmaAnalysis.sigma_analysis_gui import Ui_MainWindow
from VeraGrid.Gui.results_model import ResultsModel
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.enumerations import ResultTypes
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.SigmaAnalysis.sigma_analysis_driver import SigmaAnalysisDriver, SigmaAnalysisResults


class SigmaAnalysisGUI(QtWidgets.QMainWindow):
    """
    SigmaAnalysisGUI
    """

    def __init__(self,
                 parent: QtWidgets.QWidget | None = None,
                 results: SigmaAnalysisResults | None = None,
                 bus_names: np.ndarray | None = None,
                 grid: MultiCircuit | None = None,
                 options: PowerFlowOptions | None = None,
                 t_idx: int | None = None,
                 classical_sigma: bool = False,
                 dpr_use_stored_guess: bool = True,
                 dpr_control_q: bool | None = None,
                 dpr_control_discrete_shunts: bool = True,
                 dpr_control_qv_droop: bool = True,
                 dpr_distributed_slack: bool | None = None) -> None:
        """

        :param parent: Parent widget.
        :param results: Sigma analysis results to display.
        :param bus_names: Bus names in display order.
        :param grid: Circuit used to rerun sigma analysis.
        :param options: Power-flow options used as sigma analysis base options.
        :param t_idx: Time-series index used for the displayed results. None means snapshot.
        :param classical_sigma: Use the original single-embedding HELM sigma instead of DPR path sigma.
        :param dpr_use_stored_guess: Use stored voltages as DPR initial germ instead of the classical no-load germ.
        :param dpr_control_q: Apply PV/P reactive limit control in DPR sigma. If None, use the power-flow option.
        :param dpr_control_discrete_shunts: Apply discrete shunt controls in DPR sigma.
        :param dpr_control_qv_droop: Apply generator QV droop controls in DPR sigma.
        :param dpr_distributed_slack: Apply distributed slack in DPR sigma. If None, use the power-flow option.
        """
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(self.tr("HELM-Sigma analysis dialogue"))

        self.results: SigmaAnalysisResults | None = results
        self.bus_names: np.ndarray | None = None if bus_names is None else np.asarray(bus_names)
        self.grid: MultiCircuit | None = grid
        self.options: PowerFlowOptions | None = options
        self.t_idx: int | None = t_idx
        self.mdl: ResultsModel | None = None

        self.setup_time_slider(t_idx=t_idx)
        self.configure_sigma_options(classical_sigma=classical_sigma,
                                     dpr_use_stored_guess=dpr_use_stored_guess,
                                     dpr_control_q=dpr_control_q,
                                     dpr_control_discrete_shunts=dpr_control_discrete_shunts,
                                     dpr_control_qv_droop=dpr_control_qv_droop,
                                     dpr_distributed_slack=dpr_distributed_slack)
        self.apply_results(results=results, bus_names=self.bus_names)

        if self.grid is not None and self.options is not None:
            self.ui.sigmaRerunButton.setEnabled(True)
        else:
            self.ui.sigmaRerunButton.setEnabled(False)

        self.ui.actionCopy_to_clipboard.triggered.connect(self.copy_to_clipboard)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.sigmaMethodComboBox.currentIndexChanged.connect(self.update_dpr_options_enabled)
        self.ui.timeSlider.valueChanged.connect(self.update_time_label)
        self.ui.sigmaRerunButton.clicked.connect(self.rerun_sigma_analysis)

    def setup_time_slider(self, t_idx: int | None) -> None:
        """
        Configure the sigma time slider using the same convention as the main diagram slider.

        :param t_idx: Initial time-series index. None selects the snapshot values.
        :return: None.
        """

        if self.grid is not None:
            if self.grid.has_time_series:
                self.ui.timeSlider.setRange(-1, self.grid.get_time_number() - 1)
                self.ui.timeSlider.setEnabled(True)
            else:
                self.ui.timeSlider.setRange(-1, -1)
                self.ui.timeSlider.setEnabled(False)

            if t_idx is None:
                self.ui.timeSlider.setValue(-1)
            else:
                if self.grid.has_time_series:
                    self.ui.timeSlider.setValue(t_idx)
                else:
                    self.ui.timeSlider.setValue(-1)

            self.update_time_label()
        else:
            self.ui.timeSlider.setRange(-1, -1)
            self.ui.timeSlider.setValue(-1)
            self.ui.timeSlider.setEnabled(False)
            self.update_time_label()

    def get_selected_time_index(self) -> int | None:
        """
        Get the selected time-series index from the sigma time slider.

        :return: None for snapshot, otherwise the selected time-series index.
        """

        value: int = self.ui.timeSlider.value()

        if self.grid is not None and self.grid.has_time_series and value > -1:
            t_idx: int | None = value
        else:
            t_idx = None

        return t_idx

    def update_time_label(self, value: int = -1) -> None:
        """
        Update the sigma time label while the time slider moves.

        :param value: Slider value supplied by Qt.
        :return: None.
        """

        if self.grid is not None:
            slider_value: int = self.ui.timeSlider.value()

            if self.grid.has_time_series and slider_value > -1:
                text: str = f"[{slider_value}] {self.grid.time_profile[slider_value]}"
            else:
                text = f"Snapshot [{self.grid.get_snapshot_time_str()}]"

            self.ui.timeLabel.setText(text)
        else:
            self.ui.timeLabel.setText(self.tr("Snapshot"))

    def configure_sigma_options(self,
                                classical_sigma: bool,
                                dpr_use_stored_guess: bool,
                                dpr_control_q: bool | None,
                                dpr_control_discrete_shunts: bool,
                                dpr_control_qv_droop: bool,
                                dpr_distributed_slack: bool | None) -> None:
        """
        Configure the sigma rerun widgets from the current analysis flags.

        :param classical_sigma: Use the original single-embedding HELM sigma instead of DPR path sigma.
        :param dpr_use_stored_guess: Use stored voltages as DPR initial germ instead of the classical no-load germ.
        :param dpr_control_q: Apply PV/P reactive limit control in DPR sigma. If None, use the power-flow option.
        :param dpr_control_discrete_shunts: Apply discrete shunt controls in DPR sigma.
        :param dpr_control_qv_droop: Apply generator QV droop controls in DPR sigma.
        :param dpr_distributed_slack: Apply distributed slack in DPR sigma. If None, use the power-flow option.
        :return: None.
        """

        if classical_sigma:
            self.ui.sigmaMethodComboBox.setCurrentIndex(1)
        else:
            self.ui.sigmaMethodComboBox.setCurrentIndex(0)

        if dpr_use_stored_guess:
            self.ui.sigmaStartingPointComboBox.setCurrentIndex(0)
        else:
            self.ui.sigmaStartingPointComboBox.setCurrentIndex(1)

        if dpr_control_q is None:
            if self.options is not None:
                self.ui.sigmaControlQCheckBox.setChecked(self.options.control_Q)
            else:
                self.ui.sigmaControlQCheckBox.setChecked(False)
        else:
            self.ui.sigmaControlQCheckBox.setChecked(dpr_control_q)

        self.ui.sigmaDiscreteShuntsCheckBox.setChecked(dpr_control_discrete_shunts)
        self.ui.sigmaQvDroopCheckBox.setChecked(dpr_control_qv_droop)

        if dpr_distributed_slack is None:
            if self.options is not None:
                self.ui.sigmaDistributedSlackCheckBox.setChecked(self.options.distributed_slack)
            else:
                self.ui.sigmaDistributedSlackCheckBox.setChecked(False)
        else:
            self.ui.sigmaDistributedSlackCheckBox.setChecked(dpr_distributed_slack)

        self.update_dpr_options_enabled()

    def update_dpr_options_enabled(self, index: int = 0) -> None:
        """
        Enable DPR-only options only when the selected sigma method is DPR HELM.

        :param index: Combo-box index supplied by Qt.
        :return: None.
        """

        if index >= 0:
            dpr_enabled: bool = self.ui.sigmaMethodComboBox.currentIndex() == 0
        else:
            dpr_enabled = self.ui.sigmaMethodComboBox.currentIndex() == 0

        self.ui.sigmaStartingPointLabel.setEnabled(dpr_enabled)
        self.ui.sigmaStartingPointComboBox.setEnabled(dpr_enabled)
        self.ui.sigmaControlQCheckBox.setEnabled(dpr_enabled)
        self.ui.sigmaDiscreteShuntsCheckBox.setEnabled(dpr_enabled)
        self.ui.sigmaQvDroopCheckBox.setEnabled(dpr_enabled)
        self.ui.sigmaDistributedSlackCheckBox.setEnabled(dpr_enabled)

    def apply_results(self, results: SigmaAnalysisResults | None, bus_names: np.ndarray | None) -> None:
        """
        Apply sigma results to the plot and table.

        :param results: Sigma analysis results to display.
        :param bus_names: Bus names in display order.
        :return: None.
        """

        self.results = results

        if results is not None and bus_names is not None:
            ax = self.ui.plotwidget.get_axis()
            fig = self.ui.plotwidget.get_figure()
            ax.clear()
            self.results.plot(fig, ax)
            fig.tight_layout()
            fig.canvas.draw_idle()

            n: int = len(bus_names)
            self.mdl = ResultsModel(self.results.mdl(result_type=ResultTypes.SigmaPlusDistances,
                                                     indices=np.arange(n),
                                                     names=bus_names))
            self.ui.tableView.setModel(self.mdl)
        else:
            self.mdl = None

    def rerun_sigma_analysis(self) -> None:
        """
        Rerun sigma analysis with the method and DPR options selected in the window.

        :return: None.
        """

        if self.grid is not None and self.options is not None:
            classical_sigma: bool = self.ui.sigmaMethodComboBox.currentIndex() == 1
            dpr_use_stored_guess: bool = self.ui.sigmaStartingPointComboBox.currentIndex() == 0
            dpr_control_q: bool = self.ui.sigmaControlQCheckBox.isChecked()
            dpr_control_discrete_shunts: bool = self.ui.sigmaDiscreteShuntsCheckBox.isChecked()
            dpr_control_qv_droop: bool = self.ui.sigmaQvDroopCheckBox.isChecked()
            dpr_distributed_slack: bool = self.ui.sigmaDistributedSlackCheckBox.isChecked()
            t_idx: int | None = self.get_selected_time_index()
            sigma_driver: SigmaAnalysisDriver = SigmaAnalysisDriver(
                grid=self.grid,
                options=self.options,
                t_idx=t_idx,
                classical_sigma=classical_sigma,
                dpr_use_stored_guess=dpr_use_stored_guess,
                dpr_control_q=dpr_control_q,
                dpr_control_discrete_shunts=dpr_control_discrete_shunts,
                dpr_control_qv_droop=dpr_control_qv_droop,
                dpr_distributed_slack=dpr_distributed_slack
            )
            sigma_driver.run()

            if sigma_driver.results is not None:
                self.t_idx = t_idx

                if self.bus_names is None:
                    self.bus_names = np.array([bus.name for bus in self.grid.buses])
                else:
                    self.bus_names = self.bus_names

                self.apply_results(results=sigma_driver.results, bus_names=self.bus_names)

                if sigma_driver.results.converged:
                    self.statusBar().showMessage(self.tr("Sigma analysis completed"))
                else:
                    self.msg(self.tr("Sigma coefficients did not converge :("))
            else:
                self.msg(self.tr("Sigma analysis did not return results"))
        else:
            self.msg(self.tr("This window was opened without a circuit/options rerun context."))

    def msg(self, text: str, title: str | None = None) -> None:
        """
        Message box
        :param text: Text to display
        :param title: Name of the window
        """
        if title is None:
            message_title: str = self.tr("Warning")
        else:
            message_title = title

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg.setText(text)
        # msg.setInformativeText("This is additional information")
        msg.setWindowTitle(message_title)
        # msg.setDetailedText("The details are as follows:")
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        retval = msg.exec()

    def copy_to_clipboard(self):
        """
        Copy data to clipboard
        """
        if self.mdl is not None:
            self.mdl.copy_to_clipboard()

    def save(self):
        """

        :return:
        """
        if self.mdl is not None:
            file, filter = QtWidgets.QFileDialog.getSaveFileName(
                self,
                self.tr("Export results"),
                "",
                filter=self.tr("CSV (*.csv);;Excel files (*.xlsx)"),
            )

            if file != '':
                if 'xlsx' in filter:
                    f = file
                    if not f.endswith('.xlsx'):
                        f += '.xlsx'
                    self.mdl.save_to_excel(f)
                    print('Saved!')
                if 'csv' in filter:
                    f = file
                    if not f.endswith('.csv'):
                        f += '.csv'
                    self.mdl.save_to_csv(f)
                    print('Saved!')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SigmaAnalysisGUI()
    window.resize(1.61 * 700.0, 600.0)  # golden ratio
    window.show()
    sys.exit(app.exec())
