# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os
from typing import Any
import numpy as np
from scipy.sparse import csc_matrix
import VeraGridEngine.api as vg
from VeraGridEngine.Utils.MIP.pulp_interface import add_pulp_variable
from VeraGridEngine.Utils.MIP.pulp_interface import PulpLpModel
from VeraGridEngine.Utils.MIP.selected_interface import lpDot1D_changes, get_model_instance
from VeraGridEngine.enumerations import MIPFramework, MIPSolvers


class PulpVariableStub:
    """
    Minimal stand-in for a PuLP variable returned by a future model API.
    """
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        """
        Store the variable name used by the compatibility test.

        :param name: Variable name.
        :return: None.
        """
        self.name: str = name


class PulpFourProblemStub:
    """
    Minimal PuLP 4 style problem exposing model-owned variable creation.
    """
    __slots__ = ("added_variable",)

    def __init__(self) -> None:
        """
        Initialize the captured variable slot.

        :return: None.
        """
        self.added_variable: PulpVariableStub | None = None

    def add_variable(self, name: str, lowBound: float | int, upBound: float | int, cat: str) -> PulpVariableStub:
        """
        Add one variable through the future PuLP 4 style API.

        :param name: Variable name.
        :param lowBound: Lower variable bound.
        :param upBound: Upper variable bound.
        :param cat: Variable category.
        :return: Created stub variable.
        """
        _low_bound: float | int = lowBound
        _up_bound: float | int = upBound
        _category: str = cat
        self.added_variable = PulpVariableStub(name=name)
        return self.added_variable

    def addVariable(self, variable: Any) -> None:
        """
        Fail if the deprecated compatibility path is used.

        :param variable: Variable that should never arrive here.
        :return: None.
        """
        _variable: Any = variable
        raise AssertionError("PuLP 4 path must not use addVariable")


def test_pulp_variable_helper_prefers_model_owned_api() -> None:
    """
    Verify PuLP 4 model-owned variable creation is used when present.

    :return: None.
    """
    model: PulpFourProblemStub = PulpFourProblemStub()

    variable: Any = add_pulp_variable(model=model, name="x", low_bound=0, up_bound=1, category="Continuous")

    assert variable is model.added_variable
    assert variable.name == "x"


def test_pulp_model_accepts_constant_objective() -> None:
    """
    Verify zero-cost formulations can still set a valid PuLP objective.

    :return: None.
    """
    model: PulpLpModel = PulpLpModel(solver_type=MIPSolvers.CBC)

    model.minimize(0.0)

    assert model.model.objective is not None
    assert model.model.objective.value() == 0.0


def test_issue_372_1():
    """
    https://github.com/SanPen/VeraGrid/issues/372#issuecomment-2823645586

    Using the grid IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal

    Test:

        Given a base situation (simulated with a linear power flow)
        We define the exchange from A1->A2
        Run the NTC optimization

    Run options:

        No contingencies
        HVDC mode: Pset
        Phase shifter (branch 8): tap_phase_control_mode: fixed.
        All generators enable_dispatch = True
        Exchange sensitivity criteria: use alpha = 5%

    Metrics:

        ΔP in A1 optimized > 0 (because there are no base overloads)
        ΔP in A2 optimized < 0 (because there are no base overloads)
        ΔP in A1 == − ΔP in A2
        The summation of flow increments in the inter-area branches must be ΔP in A1.
        Monitored & selected by the exchange sensitivity criteria branches must not be overloaded beyond 100%

    """
    # fname = os.path.join('data', 'grids', 'ntc_test.gridcal')
    fname = os.path.join('data', 'grids', 'IEEE14 - ntc areas_voltages_hvdc_shifter_l10free.gridcal')

    for mip_framework in [
        vg.MIPFramework.PuLP,
        # vg.MIPFramework.OrTools
    ]:
        grid = vg.open_file(fname)

        # Phase shifter (branch 8): tap_phase_control_mode: fixed.
        grid.transformers2w[6].tap_phase_control_mode = vg.TapPhaseControl.fixed

        info = grid.get_inter_aggregation_info(objects_from=[grid.areas[0]],
                                               objects_to=[grid.areas[1]])

        opf_options = vg.OptimalPowerFlowOptions(
            consider_contingencies=False,
            mip_framework=mip_framework,
            mip_solver=vg.MIPSolvers.HIGHS,
        )

        lin_options = vg.LinearAnalysisOptions()

        ntc_options = vg.OptimalNetTransferCapacityOptions(
            sending_bus_idx=info.idx_bus_from,
            receiving_bus_idx=info.idx_bus_to,
            transfer_method=vg.AvailableTransferMode.InstalledPower,
            loading_threshold_to_report=98.0,
            skip_generation_limits=True,
            transmission_reliability_margin=0.1,
            branch_exchange_sensitivity=0.05,
            use_branch_exchange_sensitivity=True,
            branch_rating_contribution=1.0,
            monitor_only_ntc_load_rule_branches=True,
            consider_contingencies=False,
            opf_options=opf_options,
            lin_options=lin_options
        )

        drv = vg.OptimalNetTransferCapacityDriver(grid, ntc_options)

        drv.run()

        res = drv.results

        bus_area_indices = grid.get_bus_area_indices()
        a1 = np.where(bus_area_indices == 0)[0]
        a2 = np.where(bus_area_indices == 1)[0]

        # List of (branch index, branch object, flow sense w.r.t the area exchange)
        inter_info = grid.get_inter_areas_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
        inter_area_branch_idx = [x[0] for x in inter_info]
        inter_area_branch_sense = [x[2] for x in inter_info]
        inter_info_hvdc = grid.get_inter_areas_hvdc_branches(a1=[grid.areas[0]], a2=[grid.areas[1]])
        inter_area_hvdc_idx = [x[0] for x in inter_info_hvdc]
        inter_area_hvdc_sense = [x[2] for x in inter_info_hvdc]
        inter_area_flows = np.sum(res.Sf[inter_area_branch_idx].real * inter_area_branch_sense)
        inter_area_flows += np.sum(res.hvdc_Pf[inter_area_hvdc_idx] * inter_area_hvdc_sense)

        print("Nodal balance:", res.nodal_balance.sum())
        print("A1:", res.dSbus[a1].sum())
        print("A2:", -res.dSbus[a2].sum())
        print("Inter area flows:", inter_area_flows)

        assert res.converged[0]
        assert abs(res.nodal_balance.sum()) < 1e-8

        # ΔP in A1 optimized > 0 (because there are no base overloads)
        assert res.dSbus[a1].sum() > 0

        # ΔP in A2 optimized < 0 (because there are no base overloads)
        assert res.dSbus[a2].sum() < 0

        # ΔP in A1 == − ΔP in A2
        assert np.isclose(res.dSbus[a1].sum(), -res.dSbus[a2].sum(), atol=1e-6)

        assert np.isclose(res.Sbus[a1].sum(), inter_area_flows, atol=1e-6)


def test_lp_dot_1d_changes_row_filter() -> None:
    """
    This builds only the rows the caller asked for, leaving the rest untouched.
     The NTC contingency formulation relies on it to keep a large grid affordable.
    """
    model = get_model_instance(tpe=MIPFramework.PuLP, solver_type=MIPSolvers.HIGHS)

    # two columns that both write row 1, so row 1 is reachable twice
    mat = csc_matrix(np.array([[2.0, 0.0],
                               [3.0, 5.0],
                               [0.0, 7.0]]))

    variables = np.empty(2, dtype=object)
    variables[0] = model.add_var(0.0, 1.0, "x0")
    variables[1] = model.add_var(0.0, 1.0, "x1")

    # every reachable row is written, and each appears once
    res_all, idx_all = lpDot1D_changes(mat, variables)
    assert sorted(idx_all) == [0, 1, 2]
    assert len(idx_all) == len(set(idx_all))

    # filtered to row 1 only as rows 0 and 2 are never built
    row_filter = np.array([False, True, False])
    res_filtered, idx_filtered = lpDot1D_changes(mat, variables, row_filter)
    assert idx_filtered == [1]
    assert res_filtered[0] == 0
    assert res_filtered[2] == 0

    # the row that was kept is identical to the unfiltered one
    assert str(res_filtered[1]) == str(res_all[1])
