# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import os

import numpy as np

import VeraGridEngine.api as gce
import VeraGridEngine.Devices as dev
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Simulations.InvestmentsEvaluation.CandidateGeneration.candidate_generation_driver import (
    CandidateGenerationDriver,
)
from VeraGridEngine.Simulations.InvestmentsEvaluation.CandidateGeneration.candidate_generation_options import (
    CandidateGenerationOptions,
)
from VeraGridEngine.enumerations import CandidateKind


def _stressed_ieee14():
    """
    Load IEEE 14 and tighten the line ratings so that single-branch outages overload other
    branches, giving the candidate generator something to work on.
    """
    fname = os.path.join('data', 'grids', 'IEEE 14 zip costs.gridcal')
    grid = gce.FileOpen(fname).open()
    for ln in grid.get_lines():
        ln.rate = ln.rate * 0.5
    return grid


def test_candidate_generation_pipeline():
    """
    End-to-end check of the candidate-investment generator pipeline: base case, N-1 screening,
    ranked candidates of both kinds, verification, and investment materialisation.
    """
    grid = _stressed_ieee14()

    drv = CandidateGenerationDriver(
        grid=grid,
        options=CandidateGenerationOptions(top_n_corridors=3, verify_top_k=1),
    )
    drv.run()
    results = drv.results

    # --- Step 1: base case ran and converged ---
    assert results.base_case_converged is True
    assert len(results.base_loading_report) > 0

    # --- Step 2: N-1 screening flagged overloads in the requested textual form ---
    assert len(results.n1_violations) > 0
    sample = results.n1_violations[0].describe()
    assert sample.startswith("outage ")
    assert "overloaded" in sample

    # --- Steps 3-4: ranked candidates of both kinds ---
    assert len(results.candidates) > 0
    kinds = {c.kind for c in results.candidates}
    assert CandidateKind.NewLine in kinds
    assert CandidateKind.Upgrade in kinds

    # Ranking is by descending relief score.
    scores = [c.score for c in results.candidates]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] > 0.0

    # Every candidate is annotated with at least one violation it relieves.
    for c in results.candidates:
        assert len(c.relieved_violations) > 0

    # --- Step 5: verification produced a report for the top candidate of each non-empty track ---
    # (line/upgrade, injection and voltage-relief candidates are verified independently, each up
    # to verify_top_k=1 - this stressed grid has all three kinds of violation/candidate).
    expected_reports = (min(1, len(results.candidates))
                        + min(1, len(results.injection_candidates))
                        + min(1, len(results.voltage_candidates)))
    assert len(results.verification_report) == expected_reports
    assert all("resolved" in r for r in results.verification_report)

    # Only the top verify_top_k candidates are verified; the rest are left untouched.
    verified_flagged = [c for c in results.candidates if c.verified]
    assert len(verified_flagged) == min(1, len(results.candidates))

    # Summary text carries the pipeline sections.
    summary = results.summary_text()
    assert "Base case AC power flow" in summary
    assert "N-1 screening" in summary
    assert "Voltage screening" in summary
    assert "Ranked candidates" in summary


def test_verified_candidates_filter():
    """
    Only the top verify_top_k candidates are verified, and ``verified_candidates`` returns exactly
    those verified ones that converged and introduced no new violations.
    """
    grid = _stressed_ieee14()
    verify_top_k = 8
    drv = CandidateGenerationDriver(
        grid=grid,
        options=CandidateGenerationOptions(top_n_corridors=3, verify_top_k=verify_top_k),
    )
    drv.run()
    results = drv.results

    # Exactly the top-k by score are flagged as verified.
    verified_flagged = [c for c in results.candidates if c.verified]
    assert len(verified_flagged) == min(verify_top_k, len(results.candidates))
    assert verified_flagged == results.candidates[:len(verified_flagged)]

    # The shortlist is a subset of the verified ones, each converged with no new violations.
    shortlist = results.verified_candidates
    assert set(shortlist).issubset(set(verified_flagged))
    for c in shortlist:
        assert c.verified is True
        assert c.verification_converged is True
        assert c.n_new_violations == 0
        assert c.verified_ok is True

    # Any verified candidate excluded from the shortlist must have failed the gate.
    for c in verified_flagged:
        if c not in shortlist:
            assert (not c.verification_converged) or c.n_new_violations > 0


def test_candidate_apply_creates_investments():
    """
    Applying candidates materialises investments: a new-line candidate adds a Line and an
    investment activating it; an upgrade candidate adds an uprated copy of the branch plus two
    investments (activate the copy, deactivate the original) without touching the base grid.
    """
    grid = _stressed_ieee14()
    drv = CandidateGenerationDriver(grid=grid, options=CandidateGenerationOptions(verify_top_k=0))
    drv.run()

    new_line_cand = next(c for c in drv.results.candidates if c.kind == CandidateKind.NewLine)
    upgrade_cand = next(c for c in drv.results.candidates if c.kind == CandidateKind.Upgrade)

    group = dev.InvestmentsGroup(idtag=None, name="test", category="multiple")
    grid.add_investments_group(group)
    logger = Logger()

    n_lines_before = len(grid.get_lines())
    n_inv_before = len(grid.investments)

    # New-line candidate: adds a Line and an investment pointing at it.
    created = new_line_cand.apply(circuit=grid, group=group, logger=logger)
    assert isinstance(created, dev.Line)
    assert len(grid.get_lines()) == n_lines_before + 1
    assert len(grid.investments) == n_inv_before + 1
    assert grid.investments[-1].device is created

    # Upgrade candidate: copies the branch (new device with the raised rate, inactive) and adds
    # two investments: activate the uprated copy, deactivate the original branch.
    old_rate = upgrade_cand.target_branch.rate
    n_branches_before = len(grid.get_branches(add_switch=True))

    upgraded = upgrade_cand.apply(circuit=grid, group=group, logger=logger)

    # A new (inactive) uprated device was added, distinct from the original.
    assert upgraded is not None
    assert upgraded is not upgrade_cand.target_branch
    assert upgraded.idtag != upgrade_cand.target_branch.idtag
    assert upgraded.rate == upgrade_cand.new_rate
    assert upgraded.rate > old_rate
    assert upgraded.active is False
    assert len(grid.get_branches(add_switch=True)) == n_branches_before + 1

    # Two investments were added: activate the copy (status True), deactivate the original (False).
    activate_inv = grid.investments[-2]
    deactivate_inv = grid.investments[-1]
    assert activate_inv.device is upgraded
    assert activate_inv.status is True
    assert deactivate_inv.device is upgrade_cand.target_branch
    assert deactivate_inv.status is False

    # The base grid is untouched until the investments are applied: original rate and active state.
    assert upgrade_cand.target_branch.rate == old_rate
    assert upgrade_cand.target_branch.active is True

    # Shunt reactor, static generator and battery candidates: each is a brand-new device added
    # inactive, wrapped in exactly one investment - mirroring the new-line pattern above.
    shunt_cand = next(c for c in drv.results.voltage_candidates if c.kind == CandidateKind.ShuntReactor)
    static_gen_cand = next(c for c in drv.results.injection_candidates if c.kind == CandidateKind.StaticGenerator)
    battery_cand = next(c for c in drv.results.injection_candidates if c.kind == CandidateKind.Battery)

    n_shunts_before = len(grid.controllable_shunts)
    n_inv_before = len(grid.investments)
    created_shunt = shunt_cand.apply(circuit=grid, group=group, logger=logger)
    assert isinstance(created_shunt, dev.ControllableShunt)
    assert created_shunt.active is False
    assert created_shunt.Bmax == shunt_cand.shunt_bmax
    assert len(grid.controllable_shunts) == n_shunts_before + 1
    assert len(grid.investments) == n_inv_before + 1
    assert grid.investments[-1].device is created_shunt

    n_static_gens_before = len(grid.static_generators)
    n_inv_before = len(grid.investments)
    created_static_gen = static_gen_cand.apply(circuit=grid, group=group, logger=logger)
    assert isinstance(created_static_gen, dev.StaticGenerator)
    assert created_static_gen.active is False
    assert created_static_gen.P == static_gen_cand.injection_p
    assert len(grid.static_generators) == n_static_gens_before + 1
    assert len(grid.investments) == n_inv_before + 1
    assert grid.investments[-1].device is created_static_gen

    n_batteries_before = len(grid.batteries)
    n_inv_before = len(grid.investments)
    created_battery = battery_cand.apply(circuit=grid, group=group, logger=logger)
    assert isinstance(created_battery, dev.Battery)
    assert created_battery.active is False
    assert created_battery.Enom == battery_cand.battery_enom
    assert len(grid.batteries) == n_batteries_before + 1
    assert len(grid.investments) == n_inv_before + 1
    assert grid.investments[-1].device is created_battery


def test_static_generator_candidate_relieves_overload():
    """
    A static-generator candidate is sized/scored like a non-wires alternative: real-power
    injection at a congested site, capped by max_injection_mw, priced linearly by
    static_gen_cost_per_mw.
    """
    grid = _stressed_ieee14()
    options = CandidateGenerationOptions(top_n_corridors=3, verify_top_k=0)
    drv = CandidateGenerationDriver(grid=grid, options=options)
    drv.run()
    results = drv.results

    static_gen_candidates = [c for c in results.injection_candidates if c.kind == CandidateKind.StaticGenerator]
    assert len(static_gen_candidates) > 0
    for c in static_gen_candidates:
        assert c.injection_p > 0.0
        assert c.injection_p <= options.max_injection_mw
        assert len(c.relieved_violations) > 0
        assert c.capex == options.static_gen_cost_per_mw * c.injection_p


def test_battery_candidate_dual_purpose_fields():
    """
    A battery candidate reuses the static-generator sizing for its real-power side, derives Enom
    from Pmax x the configured duration, and is priced linearly by battery_cost_per_mwh on Enom.
    """
    grid = _stressed_ieee14()
    options = CandidateGenerationOptions(top_n_corridors=3, verify_top_k=0)
    drv = CandidateGenerationDriver(grid=grid, options=options)
    drv.run()
    results = drv.results

    battery_candidates = [c for c in results.injection_candidates if c.kind == CandidateKind.Battery]
    assert len(battery_candidates) > 0
    for c in battery_candidates:
        assert c.battery_pmax == c.injection_p
        assert c.battery_enom == c.battery_pmax * options.battery_duration_hours
        assert len(c.relieved_violations) > 0
        assert c.capex == options.battery_cost_per_mwh * c.battery_enom


def _bus_with_overvoltage():
    """
    Tiny 2-bus grid with a lightly loaded far bus whose Vmax is tightened below where it
    naturally solves, giving the voltage screening step an unambiguous over-voltage violation
    with no branch overload at all - this is what exercises the "voltage violations alone must
    not short-circuit the pipeline" guard.
    """
    grid = gce.MultiCircuit()

    bus1 = dev.Bus('Bus 1', Vnom=20)
    grid.add_bus(bus1)
    grid.add_generator(bus1, dev.Generator('Slack Generator', vset=1.0))

    bus2 = dev.Bus('Bus 2', Vnom=20)
    bus2.Vmax = 0.98
    bus2.Vmin = 0.90
    grid.add_bus(bus2)
    grid.add_load(bus2, dev.Load('load 2', P=1.0, Q=0.0))

    grid.add_line(dev.Line(bus1, bus2, name='line 1-2', r=0.001, x=0.01, b=0.0, rate=50.0))

    return grid


def test_shunt_reactor_candidate_generated_and_verified():
    """
    A base-case over-voltage bus (with no branch overload at all) still produces exactly one
    verified shunt-reactor candidate, in its own voltage_candidates track.
    """
    grid = _bus_with_overvoltage()
    options = CandidateGenerationOptions(verify_top_k=1)

    drv = CandidateGenerationDriver(grid=grid, options=options)
    drv.run()
    results = drv.results

    assert results.base_case_converged is True
    assert len(results.violations) == 0
    assert len(results.voltage_violations) == 1
    assert results.voltage_violations[0].is_overvoltage is True

    assert len(results.voltage_candidates) == 1
    cand = results.voltage_candidates[0]
    assert cand.kind == CandidateKind.ShuntReactor
    assert cand.shunt_bmax > 0.0
    assert cand.target_bus.name == results.voltage_violations[0].bus_name
    assert cand.capex == options.shunt_cost_per_mvar * cand.shunt_bmax

    # verify_top_k=1 verifies the top voltage-relief candidate too, even with zero overload
    # candidates - this is the early-return guard fix (voltage-only violations must not
    # short-circuit the pipeline before candidates are generated).
    assert cand.verified is True
    assert cand.verification_converged is True

    assert "Voltage screening (base case)" in results.summary_text()


def _two_bus_with_growing_load():
    """
    Tiny 2-bus, 3-hour grid where the line is fine at hour 0 but overloads by hour 2 as the load
    grows, so the critical-snapshot scan has an unambiguous hour to pick.
    """
    grid = gce.MultiCircuit()
    grid.create_profiles(steps=3, step_length=1, step_unit="h")

    bus1 = dev.Bus('Bus 1', Vnom=20)
    grid.add_bus(bus1)
    grid.add_generator(bus1, dev.Generator('Slack Generator', vset=1.0))

    bus2 = dev.Bus('Bus 2', Vnom=20)
    grid.add_bus(bus2)
    load = dev.Load('load 2', P=10.0, Q=0.0)
    grid.add_load(bus2, load)
    load.P_prof = np.array([10.0, 20.0, 60.0])
    load.Q_prof = np.array([0.0, 0.0, 0.0])

    grid.add_line(dev.Line(bus1, bus2, name='line 1-2', r=0.001, x=0.01, b=0.0, rate=50.0))

    return grid


def test_candidate_generation_time_series_critical_snapshot():
    """
    With ``use_time_series=True`` the generator scans the time series, picks the hour with the
    most violations (hour 2, once the load outgrows the line's rating), and sizes its candidate
    against that hour's flow rather than hour 0's.
    """
    grid = _two_bus_with_growing_load()

    drv = CandidateGenerationDriver(
        grid=grid,
        options=CandidateGenerationOptions(use_time_series=True, verify_top_k=1),
    )
    drv.run()
    results = drv.results

    assert results.critical_time_idx == 2
    assert results.n_overloaded_at_critical == 1

    assert results.base_case_converged is True
    assert len(results.base_violations) == 1

    # Both an upgrade and a competing new-line duplicate are generated for the overloaded line;
    # the upgrade must be sized against hour 2's ~60 MW flow, not hour 0's ~10 MW.
    upgrade_candidates = [c for c in results.candidates if c.kind == CandidateKind.Upgrade]
    assert len(upgrade_candidates) == 1
    assert upgrade_candidates[0].new_rate >= 55.0

    assert "Critical snapshot" in results.summary_text()


def test_candidate_generation_time_series_requires_grid_time_series():
    """
    ``use_time_series=True`` on a snapshot-only grid (no time profile at all) aborts cleanly with
    a logged error instead of running against nonexistent time series data.
    """
    grid = gce.MultiCircuit()
    bus1 = dev.Bus('Bus 1', Vnom=20)
    grid.add_bus(bus1)
    grid.add_generator(bus1, dev.Generator('Slack Generator', vset=1.0))
    bus2 = dev.Bus('Bus 2', Vnom=20)
    grid.add_bus(bus2)
    grid.add_load(bus2, dev.Load('load 2', P=10.0, Q=0.0))
    grid.add_line(dev.Line(bus1, bus2, name='line 1-2', r=0.001, x=0.01, b=0.0, rate=50.0))

    assert grid.has_time_series is False

    drv = CandidateGenerationDriver(
        grid=grid,
        options=CandidateGenerationOptions(use_time_series=True),
    )
    drv.run()
    results = drv.results

    assert results.base_case_converged is False
    assert results.critical_time_idx is None


def test_no_violations_no_candidates():
    """
    With generous ratings there are no violations and therefore no candidates, but the base case
    still runs and is reported feasible.
    """
    fname = os.path.join('data', 'grids', 'IEEE 14 zip costs.gridcal')
    grid = gce.FileOpen(fname).open()
    for ln in grid.get_lines():
        ln.rate = 100000.0
    for tr in grid.get_transformers2w():
        tr.rate = 100000.0

    drv = CandidateGenerationDriver(grid=grid)
    drv.run()
    results = drv.results

    assert results.base_case_converged is True
    assert results.base_case_feasible is True
    assert len(results.violations) == 0
    assert len(results.candidates) == 0
