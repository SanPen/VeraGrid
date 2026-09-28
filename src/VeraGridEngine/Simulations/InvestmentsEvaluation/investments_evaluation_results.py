# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np

from VeraGridEngine.Simulations.results_template import ResultsTemplate, ResultsProperty
from VeraGridEngine.Simulations.results_table import ResultsTable
from VeraGridEngine.basic_structures import IntVec, Vec, StrVec, Mat
from VeraGridEngine.enumerations import StudyResultsType, ResultTypes, DeviceType, ResultTablePlotType
from VeraGridEngine.Utils.NumericalMethods.MVRSM_mo_pareto import non_dominated_sorting


class InvestmentsEvaluationResults(ResultsTemplate):

    LOCAL_RESULTS_DECLARATIONS = (
        ResultsProperty(name='max_eval', tpe=int, old_names=list(), expandable=False),
        ResultsProperty(name='f_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='x_names', tpe=StrVec, old_names=list(), expandable=False),
        ResultsProperty(name='plot_x_idx', tpe=int, old_names=list(), expandable=False),
        ResultsProperty(name='plot_y_idx', tpe=int, old_names=list(), expandable=False),
        ResultsProperty(name='x', tpe=Mat, old_names=list(), expandable=False),
        ResultsProperty(name='f', tpe=Mat, old_names=list(), expandable=False),
        ResultsProperty(name='f_best', tpe=Vec, old_names=list(), expandable=False),
        ResultsProperty(name='sorting_indices', tpe=IntVec, old_names=list(), expandable=False),
    )

    __slots__ = (
        "_max_eval",
        "f_names",
        "x_names",
        "plot_x_idx",
        "plot_y_idx",
        "_x",
        "_f",
        "_f_best",
        "_sorting_indices",
        "_InvestmentsEvaluationResults__eval_index",
    )

    tpe = 'Investments Evaluation Results'

    def __init__(self, f_names: StrVec, x_names: StrVec, max_eval: int, plot_x_idx: int, plot_y_idx: int):
        """
        Constructor
        :param f_names: Names of the objectives
        :param x_names: Names of the decision vars
        :param max_eval: Maximum number of evaluations
        :param plot_x_idx: index of f to use as x when plotting
        :param plot_y_idx: index of f to use as y when plotting
        """
        available_results = {
            ResultTypes.ReportsResults: [ResultTypes.InvestmentsReportResults,
                                         ResultTypes.InvestmentsCombinationsResults,
                                         ResultTypes.InvestmentsObjectivesResults,
                                         ResultTypes.InvestmentsFrequencyResults],

            ResultTypes.ParetoResults: [ResultTypes.InvestmentsParetoReportResults,
                                        ResultTypes.InvestmentsParetoCombinationsResults,
                                        ResultTypes.InvestmentsParetoObjectivesResults
                                        ],

            ResultTypes.SpecialPlots: [ResultTypes.InvestmentsParetoPlot,
                                       ResultTypes.InvestmentsIterationsPlot,
                                       ResultTypes.InvestmentsWhenToMakePlot],
        }

        ResultsTemplate.__init__(self,
                                 name='Investments Evaluation',
                                 available_results=available_results,
                                 time_array=None,
                                 clustering_results=None,
                                 study_results_type=StudyResultsType.InvestmentEvaluations)

        n_f = len(f_names)
        n_x = len(x_names)

        self._max_eval = max_eval
        self.f_names: StrVec = f_names
        self.x_names: StrVec = x_names
        self.plot_x_idx = plot_x_idx
        self.plot_y_idx = plot_y_idx

        self._x: IntVec = np.zeros((max_eval, n_x), dtype=float)
        self._f: IntVec = np.zeros((max_eval, n_f), dtype=float)
        self._f_best = np.zeros(n_f, dtype=float)
        self._sorting_indices = np.zeros(max_eval, dtype=int)

        self.__eval_index: int = 0


    @property
    def max_eval(self) -> int:
        return self._max_eval

    @max_eval.setter
    def max_eval(self, val: int):
        self._max_eval = val

    @property
    def x(self) -> Mat:
        return self._x

    @x.setter
    def x(self, val: Vec):
        if isinstance(val, np.ndarray):
            self._x = val
        else:
            raise ValueError("X must be a numpy array")

    @property
    def f(self) -> Mat:
        return self._f

    @f.setter
    def f(self, val: Vec):
        if isinstance(val, np.ndarray):
            self._f = val
        else:
            raise ValueError("f must be a numpy array")

    @property
    def f_best(self) -> IntVec:
        return self._f_best

    @f_best.setter
    def f_best(self, val: Vec):
        if isinstance(val, np.ndarray):
            self._f_best = val
        else:
            raise ValueError("f_best must be a numpy array")

    @property
    def current_evaluation(self) -> int:
        return self.__eval_index

    @property
    def sorting_indices(self) -> IntVec:
        return self._sorting_indices

    @sorting_indices.setter
    def sorting_indices(self, val: IntVec):
        if isinstance(val, np.ndarray):
            self._sorting_indices = val.astype(int)
        else:
            raise ValueError("sorting indices must be an array of integer")

    def get_index(self) -> StrVec:
        return np.array([f"Eval {i + 1}" for i in range(self.x.shape[0])])

    def set_at(self, i: int, x_vec: Vec, f_vec: Vec):
        """

        :param i:
        :param x_vec:
        :param f_vec:
        :return:
        """
        self._x[i, :] = x_vec
        self._f[i, :] = f_vec

    def add(self, x_vec: Vec, f_vec: Vec) -> None:
        """

        :param x_vec:
        :param f_vec:
        :return:
        """
        if self.__eval_index < self.max_eval:
            self.set_at(i=self.__eval_index, x_vec=x_vec, f_vec=f_vec)

            self.__eval_index += 1
        else:
            print('Evaluation index out of range')

    def finalize(self):
        """
        Finalize the results after simulation
        """
        # crop the data to the latest call index
        if self.__eval_index > 0:
            self._f = self._f[:self.__eval_index, :]
            self._x = self._x[:self.__eval_index, :]

            # Dedup x rows before Pareto sorting: equal-x rows don't dominate each
            # other and would all land in the front. Raw _x/_f stay intact so the
            # iteration, frequency, and reports views still see every evaluation.
            _, unique_idx = np.unique(self._x, axis=0, return_index=True)
            unique_idx = np.sort(unique_idx)

            # compute the pareto sorting indices on the deduplicated slice, then map
            # the resulting positions back to indices into the full _x/_f arrays
            _, _, pareto_local = non_dominated_sorting(
                y_values=self._f[unique_idx, :],
                x_values=self._x[unique_idx, :],
            )
            self._sorting_indices = unique_idx[pareto_local]

            # we curtail this one too
            self.max_eval = self.__eval_index

    def set_best_combination(self, combination: IntVec) -> None:
        """
        Set the best combination of investment groups
        :param combination: Vector of integers (0/1)
        """
        self._f_best = combination

    def mdl(self, result_type) -> ResultsTable:
        """
        Plot the results
        :param result_type: type of results (string)
        :return: DataFrame of the results (or None if the result was not understood)
        """
        n = self.x.shape[0]
        index = self.get_index()

        if result_type in (ResultTypes.InvestmentsReportResults,
                           ResultTypes.InvestmentsParetoReportResults):

            columns = np.r_[np.array(self.f_names), np.array(self.x_names)]
            data = np.c_[self.f, self.x]

            if result_type == ResultTypes.InvestmentsParetoReportResults:
                # slice results according to the pareto indices
                index = index[self.sorting_indices]
                data = data[self.sorting_indices, :]

            return ResultsTable(data=data,
                                index=index,
                                idx_device_type=DeviceType.NoDevice,
                                columns=columns,
                                cols_device_type=DeviceType.NoDevice.NoDevice,
                                title=str(result_type.value),
                                ylabel="",
                                xlabel='',
                                units="")

        elif result_type == ResultTypes.InvestmentsFrequencyResults:

            freq = np.sum(self._x, axis=0)
            freq_rel = freq / freq.sum()
            data = np.c_[freq, freq_rel]

            return ResultsTable(data=data,
                                index=np.array(self.x_names),
                                idx_device_type=DeviceType.NoDevice,
                                columns=np.array(["Frequency", "Relative frequency"]),
                                cols_device_type=DeviceType.NoDevice.NoDevice,
                                title=str(result_type.value),
                                ylabel="",
                                xlabel="",
                                units="")

        elif result_type in (ResultTypes.InvestmentsCombinationsResults,
                             ResultTypes.InvestmentsParetoCombinationsResults):

            if result_type == ResultTypes.InvestmentsParetoCombinationsResults:
                # slice results according to the pareto indices
                data = self._x[self.sorting_indices, :]
                index = index[self.sorting_indices]
            else:
                data = self._x

            return ResultsTable(data=data,
                                index=index,
                                idx_device_type=DeviceType.NoDevice,
                                columns=self.x_names,
                                cols_device_type=DeviceType.NoDevice.NoDevice,
                                title=str(result_type.value),
                                ylabel="",
                                xlabel="",
                                units="")

        elif result_type in (ResultTypes.InvestmentsObjectivesResults,
                             ResultTypes.InvestmentsParetoObjectivesResults):

            data = self.f

            if result_type == ResultTypes.InvestmentsParetoObjectivesResults:
                # slice results according to the pareto indices
                data = data[self.sorting_indices, :]
                index = index[self.sorting_indices]

            return ResultsTable(data=data,
                                index=index,
                                idx_device_type=DeviceType.NoDevice,
                                columns=self.f_names,
                                cols_device_type=DeviceType.NoDevice.NoDevice,
                                title=str(result_type.value),
                                ylabel="",
                                xlabel="",
                                units="")

        elif result_type == ResultTypes.InvestmentsParetoPlot:

            x_vals = self.f[:, self.plot_x_idx]
            y_vals = self.f[:, self.plot_y_idx]


            return ResultsTable(data=np.c_[x_vals, y_vals],
                                index=np.array(index),
                                idx_device_type=DeviceType.NoDevice,
                                columns=np.array([self.f_names[self.plot_x_idx],
                                                  self.f_names[self.plot_y_idx]]),
                                cols_device_type=DeviceType.NoDevice.NoDevice,
                                title="Pareto plot",
                                ylabel=self.f_names[self.plot_y_idx],
                                xlabel=self.f_names[self.plot_x_idx],
                                units="",
                                plot_type=ResultTablePlotType.XY)

        elif result_type == ResultTypes.InvestmentsIterationsPlot:

            columns: list[str] = ["Iteration", "Objectives summation"]
            x = np.arange(self.max_eval)
            y: np.ndarray = self.f.sum(axis=1)
            data: np.ndarray = np.c_[x, y]

            return ResultsTable(data=data,
                                index=np.array(index),
                                idx_device_type=DeviceType.NoDevice,
                                columns=np.array(columns),
                                cols_device_type=DeviceType.NoDevice.NoDevice,
                                title=str(result_type.value),
                                ylabel="Objectives summation",
                                xlabel="Iteration",
                                units="")

        elif result_type == ResultTypes.InvestmentsWhenToMakePlot:

            # Create subplots

            # _x is (max_eval, n_investments)
            # X is (pareto solutions, n_investments)

            X: np.ndarray = self._x[self.sorting_indices, :].astype(int)
            max_years: int = max(1, int(np.max(X))) if X.size > 0 else 1
            mat: np.ndarray = np.zeros((X.shape[1], max_years))
            evaluation_index: int
            investment_index: int
            for evaluation_index in range(X.shape[0]):
                for investment_index in range(X.shape[1]):
                    year: int = int(X[evaluation_index, investment_index])
                    if year > 0:
                        mat[investment_index, year - 1] += 1
                    else:
                        pass

            return ResultsTable(data=mat,
                                index=self.x_names,
                                idx_device_type=DeviceType.NoDevice,
                                columns=np.array([str(year) for year in range(1, max_years + 1)]),
                                cols_device_type=DeviceType.NoDevice.NoDevice,
                                title=str(result_type.value),
                                ylabel="",
                                xlabel="",
                                units="")
        else:
            raise Exception('Result type not understood:' + str(result_type))
