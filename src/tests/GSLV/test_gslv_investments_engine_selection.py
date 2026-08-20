# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import numpy as np

import VeraGridEngine.api as vg
from VeraGridEngine.Compilers.Gslv.Simulations.investments import translate_gslv_investments_evaluation_results
from VeraGridEngine.enumerations import (
    EngineType,
    InvestmentEvaluationMethod,
    InvestmentsEvaluationObjectives,
    LogSeverity,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_driver import (
    InvestmentsEvaluationDriver,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_options import (
    InvestmentsEvaluationOptions,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_results import (
    InvestmentsEvaluationResults,
)
import VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_driver as investments_driver_module


class ProblemStub:
    """
    Minimal investment problem stub for driver dispatch tests.
    """
    __slots__ = tuple()
    plot_x_idx = 0
    plot_y_idx = 1

    def get_objectives_names(self) -> np.ndarray:
        """
        Get fake objective names.

        :return: Objective names.
        """
        return np.array(["capex", "losses"], dtype=str)

    def get_vars_names(self) -> np.ndarray:
        """
        Get fake variable names.

        :return: Decision-variable names.
        """
        return np.array(["group_0", "group_1"], dtype=str)

    def get_investments_for_combination(self, x: np.ndarray) -> list:
        """
        Return no concrete investments for the selected combination.

        :param x: Selected decision vector.
        :return: Empty list.
        """
        return list()


class FakeGslvInvestmentsResults:
    """
    Minimal GSLV investment-results stub used to test translation.
    """
    __slots__ = (
        "x",
        "f",
        "x_names",
        "f_names",
        "sorting_indices",
        "best_combination",
        "best_objectives",
        "eval_count",
        "max_eval",
        "plot_x_idx",
        "plot_y_idx",
    )


def get_warning_messages(driver: InvestmentsEvaluationDriver) -> list[str]:
    """
    Collect warning messages from a driver logger.

    :param driver: Driver instance.
    :return: Warning messages.
    """
    return [
        entry.msg
        for entry in driver.logger.entries
        if entry.severity == LogSeverity.Warning
    ]


def build_fake_results() -> FakeGslvInvestmentsResults:
    """
    Build one fake GSLV investment-results object.

    :return: Fake results object.
    """
    res = FakeGslvInvestmentsResults()
    res.x = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]], dtype=float)
    res.f = np.array([[10.0, 5.0], [7.0, 4.0], [4.0, 3.0]], dtype=float)
    res.x_names = ["group_0", "group_1"]
    res.f_names = ["capex", "losses"]
    res.sorting_indices = np.array([2, 1, 0], dtype=int)
    res.best_combination = np.array([1.0, 1.0], dtype=float)
    res.best_objectives = np.array([4.0, 3.0], dtype=float)
    res.eval_count = 3
    res.max_eval = 7
    res.plot_x_idx = 0
    res.plot_y_idx = 1
    return res


def test_translate_gslv_investments_results() -> None:
    """
    GSLV investment results must translate into VeraGrid's result contract.
    """
    fake_results = build_fake_results()

    results = translate_gslv_investments_evaluation_results(fake_results)

    assert isinstance(results, InvestmentsEvaluationResults)
    assert np.array_equal(results.x, fake_results.x)
    assert np.array_equal(results.f, fake_results.f)
    assert np.array_equal(results.f_best, fake_results.best_combination)
    assert np.array_equal(results.sorting_indices, fake_results.sorting_indices)
    assert np.array_equal(results.x_names, np.array(fake_results.x_names, dtype=str))
    assert np.array_equal(results.f_names, np.array(fake_results.f_names, dtype=str))
    assert results.max_eval == fake_results.eval_count


def test_gslv_investments_driver_dispatch_uses_gslv(monkeypatch) -> None:
    """
    Investments evaluation must dispatch to the GSLV helper when requested.
    """
    state: dict[str, bool] = dict()
    grid = vg.MultiCircuit()
    problem = ProblemStub()
    options = InvestmentsEvaluationOptions(
        max_eval=4,
        solver=InvestmentEvaluationMethod.NSGA3,
        obj_tpe=InvestmentsEvaluationObjectives.PowerFlow,
    )
    driver = InvestmentsEvaluationDriver(
        grid=grid,
        options=options,
        problem=problem,
        engine=EngineType.GSLV,
    )

    def fake_gslv_investments_evaluation(circuit, options, logger):
        """
        Record the GSLV dispatch and return translated-style results.

        :param circuit: Circuit.
        :param options: Investments options.
        :param logger: Logger.
        :return: VeraGrid investments results.
        """
        state["called"] = True
        translated = translate_gslv_investments_evaluation_results(build_fake_results())
        return translated

    monkeypatch.setattr(investments_driver_module, "GSLV_AVAILABLE", True)
    monkeypatch.setattr(
        investments_driver_module,
        "gslv_investments_evaluation",
        fake_gslv_investments_evaluation,
    )

    driver.run()

    assert state.get("called", False)
    assert driver.engine == EngineType.GSLV
    assert np.array_equal(driver.results.f_best, np.array([1.0, 1.0], dtype=float))


def test_gslv_investments_driver_falls_back_for_unsupported_objective(monkeypatch) -> None:
    """
    GSLV investments evaluation must fall back for unsupported VeraGrid-only objectives.
    """
    state: dict[str, bool] = dict()
    grid = vg.MultiCircuit()
    problem = ProblemStub()
    options = InvestmentsEvaluationOptions(
        max_eval=4,
        solver=InvestmentEvaluationMethod.Random,
        obj_tpe=InvestmentsEvaluationObjectives.GenerationAdequacy,
    )
    driver = InvestmentsEvaluationDriver(
        grid=grid,
        options=options,
        problem=problem,
        engine=EngineType.GSLV,
    )

    def fake_randomized_evaluation(self) -> None:
        """
        Record the native fallback dispatch and seed a best combination.

        :param self: Driver instance.
        :return: None.
        """
        state["called"] = True
        self.results.f_best = np.zeros(len(problem.get_vars_names()), dtype=float)

    monkeypatch.setattr(investments_driver_module, "GSLV_AVAILABLE", True)
    monkeypatch.setattr(InvestmentsEvaluationDriver, "randomized_evaluation", fake_randomized_evaluation)

    driver.run()

    assert state.get("called", False)
    assert driver.engine == EngineType.VeraGrid
    assert "GSLV investments evaluation does not support this objective, falling back to VeraGrid" in (
        get_warning_messages(driver)
    )
