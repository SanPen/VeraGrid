# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import numpy as np
import math
from matplotlib import pyplot as plt
from typing import List, Any

from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.basic_structures import Vec, Mat, StrVec
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var

class SPlotInteractionHandler:
    """
    Handles interactive annotations and hover events for S-Domain stability plots.
    """
    __slots__ = ['sc', 'annot', 'fig', 'ax']

    def __init__(self, sc: Any, annot: Any, fig: Any, ax: Any) -> None:
        """
        SPlotInteractionHandler constructor.
        """
        self.sc: Any = sc
        self.annot: Any = annot
        self.fig: Any = fig
        self.ax: Any = ax

    def update_annotation(self, ind: dict) -> None:
        """
        Updates the annotation text and position based on the hovered point.
        """
        pos = self.sc.get_offsets()[ind["ind"][0]]
        self.annot.xy = pos
        text: str = f"Re={pos[0]:.2f}, Im={pos[1]:.2f}"
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.8)

    def on_hover(self, event: Any) -> None:
        """
        Hover event callback logic.
        """
        if event.inaxes == self.ax:
            cont, ind = self.sc.contains(event)
            if cont:
                self.update_annotation(ind)
                self.annot.set_visible(True)
                self.fig.canvas.draw_idle()
            else:
                if self.annot.get_visible():
                    self.annot.set_visible(False)
                    self.fig.canvas.draw_idle()
                else:
                    pass
        else:
            pass

class SmallSignalStabilityRmsResults(ResultsTemplate):
    """
    Small-signal Analysis results storage and visualization.
    """

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='stat_vars_array', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='eigenvalues', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='participation_factors', tpe=Mat, old_names=list(), expandable=False),
        ResultsProperty(name='damping_ratios', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='conjugate_frequencies', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='state_matrix', tpe=Mat, old_names=list(), expandable=False),
    )
    __slots__ = [
        'stat_vars_array',
        'algebraic_vars_array',
        'eigenvalues',
        'participation_factors',
        'damping_ratios',
        'conjugate_frequencies',
        'state_matrix'
    ]
    def __init__(self,
                 eigenvalues: Vec,
                 participation_factors: Mat,
                 damping_ratios: Vec,
                 conjugate_frequencies: Vec,
                 state_matrix: Mat,
                 stat_vars: List[Var],
                 algebraic_vars: List[Var])-> None:
        """
        Small-signal Analysis results
        :param eigenvalues:
        :param participation_factors:
        :param damping_ratios:
        :param conjugate_frequencies:
        :param state_matrix:
        :param stat_vars:
        :param algebraic_vars:
        """

        available_list: list = list([
            ResultTypes.StateMatrix,
            ResultTypes.Modes,
            ResultTypes.ParticipationFactors,
            ResultTypes.SDomainPlot,
            ResultTypes.SDomainPlotHz
        ])

        ResultsTemplate.__init__(
            self,
            name='Small Signal Stability',
            available_results=available_list,
            time_array=None,
            clustering_results=None,
            study_results_type=StudyResultsType.SmallSignalStability
        )

        stat_names_list: list = list()
        for i, var in enumerate(stat_vars):
            stat_names_list.append(f"{var}{i // 2 + 1}")

        algebraic_names_list: list = list()
        for i, var in enumerate(algebraic_vars):
            algebraic_names_list.append(f"{var}{i // 2 + 1}")


        self.stat_vars_array: Vec = np.array(stat_names_list, dtype=np.str_)
        self.algebraic_vars_array: Vec = np.array(algebraic_names_list, dtype=np.str_)
        self.eigenvalues: Vec = eigenvalues
        self.participation_factors: Mat = participation_factors
        self.damping_ratios: Vec = damping_ratios
        self.conjugate_frequencies: Vec = conjugate_frequencies

        self.state_matrix: Mat = state_matrix


    def mdl(self, result_type: ResultTypes) -> ResultsTable:
        """
        Export the results as a ResultsTable for plotting.
        """
        if result_type == ResultTypes.StateMatrix:
            if len(self.stat_vars_array) == self.state_matrix.shape[0]:

                return ResultsTable(
                    data=self.state_matrix,
                    index=np.array([f"Equation {i}" for i in range(len(self.eigenvalues))], dtype=np.str_),
                    columns=np.array(self.stat_vars_array.astype(str), dtype=np.str_),
                    title="State Matrix",
                    idx_device_type=DeviceType.NoDevice,
                    cols_device_type=DeviceType.NoDevice
                )
            else:
                # TODO: adapt to generalized!
                return ResultsTable(
                    data=self.state_matrix,
                    index=np.array([f"Equation {i}" for i in range(len(self.eigenvalues))], dtype=np.str_),
                    columns=np.array(list(self.stat_vars_array.astype(str)) + list(self.algebraic_vars_array.astype(str)), dtype=np.str_),
                    title="State Matrix",
                    idx_device_type=DeviceType.NoDevice,
                    cols_device_type=DeviceType.NoDevice
                )


        elif result_type == ResultTypes.ParticipationFactors:

            if len(self.stat_vars_array) == self.participation_factors.shape[0]:

                return ResultsTable(
                    data=self.participation_factors,
                    index=np.array(self.stat_vars_array.astype(str), dtype=np.str_),
                    columns=np.array([f"Mode {i}" for i in range(len(self.eigenvalues))], dtype=np.str_),
                    title="Participation factors for each eigenvalue",
                    idx_device_type=DeviceType.NoDevice,
                    cols_device_type=DeviceType.NoDevice
                )
            else:
                # TODO: adapt to generalized!
                return ResultsTable(
                    data=self.participation_factors,
                    index=np.array(list(self.stat_vars_array.astype(str)) + list(self.algebraic_vars_array.astype(str)), dtype=np.str_),
                    columns=np.array([f"Mode {i}" for i in range(len(self.eigenvalues))], dtype=np.str_),
                    title="Participation factors for each eigenvalue",
                    idx_device_type=DeviceType.NoDevice,
                    cols_device_type=DeviceType.NoDevice
                )

        elif result_type == ResultTypes.Modes:
            re: Vec = self.eigenvalues.real
            im: Vec = self.eigenvalues.imag
            data_modes: Mat = np.c_[re, im, self.damping_ratios, self.conjugate_frequencies]
            return ResultsTable(
                data=data_modes,
                index=np.array([f"Mode {i}" for i in range(len(self.eigenvalues))], dtype=np.str_),
                columns=np.array(["Real", "Imaginary", "Damping ratio", "Oscillation frequency"]),
                title="Eigenvalues",
                idx_device_type=DeviceType.NoDevice,
                cols_device_type=DeviceType.NoDevice
            )
        elif result_type == ResultTypes.SDomainPlot:
            re: Vec = self.eigenvalues.real
            im: Vec = self.eigenvalues.imag
            data: Mat = np.c_[re, im]

            d: Vec = np.abs(np.nan_to_num(re))
            colors: Vec = (-d / d.max())

            slope: float = 1 / 0.05
            x_z: Vec = np.linspace(-200, 0, 400)
            y_z: Vec = slope * x_z

            margin_x: float = (re.max() - re.min()) * 0.1
            margin_y: float = (im.max() - im.min()) * 0.1
            x_min: float = re.min() - margin_x
            x_max: float = re.max() + margin_x
            y_min: float = im.min() - margin_y
            y_max: float = im.max() + margin_y

            if self.plotting_allowed():
                plt.ion()
                fig: Any = plt.figure(figsize=(8, 6))
                ax: Any = fig.add_subplot(111)
                ax.plot(x_z, y_z, '--', color='grey', linewidth=0.7, alpha=0.6, label='ζ = 5%')
                ax.plot(x_z, -y_z, '--', color='grey', linewidth=0.7, alpha=0.6)
                sc: Any = ax.scatter(re, im, c=colors, cmap='winter', s=120, alpha=0.8)
                fig.suptitle("S-Domain Stability plot")
                ax.set_xlabel(r'Real')
                ax.set_ylabel(r'Imaginary [rad/s]')
                ax.axhline(0, color='black', linewidth=1)
                ax.axvline(0, color='black', linewidth=1)
                plt.xlim([x_min, x_max])
                plt.ylim([y_min, y_max])
                plt.tight_layout()
                plt.show()
                annot: Any = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                                         textcoords="offset points",
                                         bbox=dict(boxstyle="round", fc="w"),
                                         arrowprops=dict(arrowstyle="->"),
                                         fontsize=8)
                annot.set_visible(False)

                handler: SPlotInteractionHandler = SPlotInteractionHandler(sc, annot, fig, ax)
                fig.canvas.mpl_connect("motion_notify_event", handler.on_hover)
            else:
                pass

            return ResultsTable(data=data,
                                index=np.empty(len(self.eigenvalues), dtype=np.str_),
                                idx_device_type=DeviceType.NoDevice,
                                columns=np.array(['Real', 'Imag']),
                                cols_device_type=DeviceType.NoDevice,
                                title="S-Domain Stability plot"
                                )
        elif result_type == ResultTypes.SDomainPlotHz:
            re: Vec = self.eigenvalues.real
            im: Vec = self.eigenvalues.imag / (2 * math.pi)
            data: Mat = np.c_[re, im]

            d: Vec = np.abs(np.nan_to_num(re))
            colors: Vec = (-d / d.max())

            slope: float = 1 / 0.05
            x_z: Vec = np.linspace(-200, 0, 400)
            y_z: Vec = slope * x_z / (2 * math.pi)

            margin_x: float = (re.max() - re.min()) * 0.1
            margin_y: float = (im.max() - im.min()) * 0.1
            x_min: float = re.min() - margin_x
            x_max: float = re.max() + margin_x
            y_min: float = im.min() - margin_y
            y_max: float = im.max() + margin_y


            if self.plotting_allowed():
                plt.ion()
                fig: Any = plt.figure(figsize=(8, 6))
                ax: Any = fig.add_subplot(111)
                ax.plot(x_z, y_z, '--', color='grey',linewidth=0.7, alpha=0.6, label='ζ = 5%')
                ax.plot(x_z, -y_z, '--', color='grey',linewidth=0.7, alpha=0.6)
                sc: Any = ax.scatter(re, im, c=colors, cmap='winter', s=120, alpha=0.8)
                fig.suptitle("S-Domain Stability plot")
                ax.set_xlabel(r'Real')
                ax.set_ylabel(r'Imaginary [Hz]')
                ax.axhline(0, color='black', linewidth=1)  # eje horizontal (y = 0)
                ax.axvline(0, color='black', linewidth=1)
                plt.xlim([x_min, x_max])
                plt.ylim([y_min, y_max])
                plt.tight_layout()
                plt.show()
                annot: Any = ax.annotate("", xy=(0, 0), xytext=(20, 20),
                                    textcoords="offset points",
                                    bbox=dict(boxstyle="round", fc="w"),
                                    arrowprops=dict(arrowstyle="->"),
                                    fontsize=8)
                annot.set_visible(False)

                hz_handler: SPlotInteractionHandler = SPlotInteractionHandler(sc, annot, fig, ax)
                fig.canvas.mpl_connect("motion_notify_event", hz_handler.on_hover)

            else:
                pass

            return ResultsTable(data=data,
                                index=np.empty(len(self.eigenvalues), dtype=np.str_),
                                idx_device_type=DeviceType.NoDevice,
                                columns=np.array(['Real', 'Imag [Hz]']),
                                cols_device_type=DeviceType.NoDevice,
                                title="S-Domain Stability plot"
                                )
        else:
            raise Exception(f"Result type not understood: {result_type}")
