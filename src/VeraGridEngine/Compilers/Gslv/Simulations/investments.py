# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from VeraGridEngine.Compilers.Gslv.activation import pg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import (
    IntVec,
    Logger,
)
from VeraGridEngine.enumerations import (
    InvestmentEvaluationMethod,
    InvestmentsEvaluationObjectives,
)
import numpy as np
import time
from typing import TYPE_CHECKING
from VeraGridEngine.Compilers.Gslv.conversion import to_gslv
from VeraGridEngine.Compilers.Gslv.Simulations.power_flow import get_gslv_pf_options
from VeraGridEngine.Compilers.Gslv.Simulations.opf import get_gslv_opf_options
from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_results import InvestmentsEvaluationResults

if TYPE_CHECKING:
    from VeraGridEngine.Simulations.InvestmentsEvaluation.investments_evaluation_options import (
        InvestmentsEvaluationOptions,
    )


def get_gslv_investments_evaluation_options(
        opt: "InvestmentsEvaluationOptions",
        circuit: MultiCircuit,
        gslv_circuit: "pg.MultiCircuit",
) -> "pg.InvestmentsEvaluationOptions":
    """
    Translate VeraGrid investment-evaluation options to GSLV options.

    :param opt: VeraGrid investments-evaluation options.
    :param circuit: VeraGrid circuit.
    :param gslv_circuit: Converted GSLV circuit.
    :return: GSLV investments-evaluation options.
    """
    solver_dict = {
        InvestmentEvaluationMethod.CBA_PINT_TOOT: pg.InvestmentEvaluationMethod.CBA_PINT_TOOT,
        InvestmentEvaluationMethod.PINT_TOOT_NSGA3: pg.InvestmentEvaluationMethod.PINT_TOOT_NSGA3,
        InvestmentEvaluationMethod.Hyperopt: pg.InvestmentEvaluationMethod.Hyperopt,
        InvestmentEvaluationMethod.MVRSM: pg.InvestmentEvaluationMethod.MVRSM,
        InvestmentEvaluationMethod.NSGA3: pg.InvestmentEvaluationMethod.NSGA3,
        InvestmentEvaluationMethod.Random: pg.InvestmentEvaluationMethod.Random,
        InvestmentEvaluationMethod.MixedVariableGA: pg.InvestmentEvaluationMethod.MixedVariableGA,
        InvestmentEvaluationMethod.FromPlugin: pg.InvestmentEvaluationMethod.FromPlugin,
    }

    objective_type_dict = {
        InvestmentsEvaluationObjectives.PowerFlow: pg.InvestmentsEvaluationObjectives.PowerFlow,
        InvestmentsEvaluationObjectives.TimeSeriesPowerFlow: pg.InvestmentsEvaluationObjectives.TimeSeriesPowerFlow,
        InvestmentsEvaluationObjectives.LinearOptimalPowerFlowTimeSeries:
            pg.InvestmentsEvaluationObjectives.TimeSeriesOptimalPowerFlow,
        InvestmentsEvaluationObjectives.FromPlugin: pg.InvestmentsEvaluationObjectives.FromPlugin,
    }

    return pg.InvestmentsEvaluationOptions(
        max_eval=opt.max_eval,
        solver=solver_dict[opt.solver],
        objective_type=objective_type_dict[opt.objf_tpe],
        pf_options=get_gslv_pf_options(opt.pf_options),
        opf_options=get_gslv_opf_options(opt.opf_options, circuit=circuit, gslv_circuit=gslv_circuit),
    )

def translate_gslv_investments_evaluation_results(
        res: "pg.InvestmentsEvaluationResults",
) -> InvestmentsEvaluationResults:
    """
    Translate GSLV investment-evaluation results to VeraGrid results.

    :param res: GSLV investments-evaluation results.
    :return: VeraGrid investments-evaluation results.
    """
    results = InvestmentsEvaluationResults(
        f_names=np.array(res.f_names, dtype=str),
        x_names=np.array(res.x_names, dtype=str),
        max_eval=int(res.max_eval),
        plot_x_idx=int(res.plot_x_idx),
        plot_y_idx=int(res.plot_y_idx),
    )

    results.x = np.array(res.x, dtype=float)
    results.f = np.array(res.f, dtype=float)
    results.f_best = np.array(res.best_combination, dtype=float)
    results.sorting_indices = np.array(res.sorting_indices, dtype=int)
    results.max_eval = int(res.eval_count)

    return results

def gslv_investments_evaluation(
        circuit: MultiCircuit,
        options: "InvestmentsEvaluationOptions",
        logger: Logger = Logger(),
) -> InvestmentsEvaluationResults:
    """
    Run GSLV investments evaluation and translate its results back to VeraGrid.

    :param circuit: VeraGrid circuit.
    :param options: VeraGrid investments-evaluation options.
    :param logger: VeraGrid logger instance.
    :return: VeraGrid investments-evaluation results.
    """
    use_time_series: bool = options.objf_tpe in (
        InvestmentsEvaluationObjectives.TimeSeriesPowerFlow,
        InvestmentsEvaluationObjectives.LinearOptimalPowerFlowTimeSeries,
    )

    if use_time_series:
        time_indices: IntVec | None = circuit.get_all_time_indices()
    else:
        time_indices = None

    gslv_grid, _ = to_gslv(
        circuit=circuit,
        use_time_series=use_time_series,
        time_indices=time_indices,
    )
    gslv_options = get_gslv_investments_evaluation_options(
        opt=options,
        circuit=circuit,
        gslv_circuit=gslv_grid,
    )
    gslv_logger = pg.Logger()

    t0 = time.time()
    gslv_results = pg.investments_evaluation(
        grid=gslv_grid,
        options=gslv_options,
        logger=gslv_logger,
        clustering_results=None,
    )
    logger.add_info("gslv time", value=f"{(time.time() - t0)} s")

    return translate_gslv_investments_evaluation_results(res=gslv_results)
