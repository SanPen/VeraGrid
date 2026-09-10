# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations
from typing import Optional

from VeraGridEngine.basic_structures import IntVec

# Standard grid-scale battery duration class for peak-shaving/overload-relief use cases (as opposed
# to ~1h frequency-response or 8h+ long-duration storage). A default, not a domain-calibrated figure.
DEFAULT_BATTERY_DURATION_HOURS: float = 4.0

# Headroom multiplier applied to the shunt reactor's upfront Bmax sizing estimate (a network-
# decoupled proxy, see CandidateGenerationDriver._make_shunt_reactor_candidates), to guard against
# that proxy underestimating the true, network-coupled reactive power requirement.
DEFAULT_SHUNT_BMAX_MARGIN: float = 1.5

# Safety cap (MW) on Static Generator / Battery sizing, playing the same bounding role a reference
# branch's own rating plays for a CandidateKind.NewLine candidate.
DEFAULT_MAX_INJECTION_MW: float = 50.0

# CAPEX unit costs (EUR). Sources noted where an internet-sourced figure was used; otherwise this
# is a planning-tool placeholder, not a domain-calibrated figure - see the CAPEX proxies previously
# used (rate**2-style) for context on why a linear-in-size model replaced them.
#
# Shunt reactor: MISO Transmission Cost Estimation Guide, 2023 revision, 500kV shunt reactors.
DEFAULT_SHUNT_COST_PER_MVAR: float = 23625.0
# Static generator: not internet-sourced - midpoint of a ~EUR0.7M-1.2M/MW simple-cycle-peaker-class
# estimate, kept as a placeholder since "static generator" is a generic non-wires-alternative
# abstraction rather than one specific technology.
DEFAULT_STATIC_GEN_COST_PER_MW: float = 1_000_000.0
# Battery: NREL "Cost Projections for Utility-Scale Battery Storage" (2025 update), mid case,
# 4-hour duration, 2035 - a single bundled EUR/MWh figure (power conversion + BOS + cells), applied
# to Enom rather than split into separate power/energy terms, matching NREL's own costing convention
# now that Enom already encodes both Pmax and duration.
DEFAULT_BATTERY_COST_PER_MWH: float = 247000.0
# New line / upgrade: NOT sourced from a cost guide - unlike the three costs above, published
# transmission-line cost data (including the MISO guide cited for the shunt reactor) is inherently
# EUR/MVA-mile, not EUR/MVA alone, because line cost scales with corridor length. This flat
# EUR/MVA figure is a planning-tool placeholder derived by dividing a typical 345kV AC line's
# cost (~EUR1-2M/mile, ~1000-1800 MVA rating, i.e. roughly EUR1,000-1,500/MVA-mile) by a
# representative short corridor length (~10 km), landing in the same order of magnitude as the
# shunt-reactor EUR/MVAr figure above so no single candidate kind dominates CAPEX by construction.
# Revisit with an explicit EUR/MVA-km term (distance already computed for corridor selection, see
# ``CandidateGenerationDriver._nearest_buses``) if a distance-aware model is wanted later.
DEFAULT_LINE_COST_PER_MVA: float = 13000.0


class CandidateGenerationOptions:
    """
    Options for the candidate-investment generator.
    """

    def __init__(self,
                 top_n_corridors: int = 5,
                 base_overload_threshold: float = 1.0,
                 n1_overload_threshold: float = 1.0,
                 ptdf_threshold: float = 1e-4,
                 verify_top_k: int = 1,
                 use_time_series: bool = False,
                 time_indices: Optional[IntVec] = None,
                 battery_duration_hours: float = DEFAULT_BATTERY_DURATION_HOURS,
                 shunt_bmax_margin: float = DEFAULT_SHUNT_BMAX_MARGIN,
                 max_injection_mw: float = DEFAULT_MAX_INJECTION_MW,
                 shunt_cost_per_mvar: float = DEFAULT_SHUNT_COST_PER_MVAR,
                 static_gen_cost_per_mw: float = DEFAULT_STATIC_GEN_COST_PER_MW,
                 battery_cost_per_mwh: float = DEFAULT_BATTERY_COST_PER_MWH,
                 line_cost_per_mva: float = DEFAULT_LINE_COST_PER_MVA):
        """
        :param top_n_corridors: Number of nearby-substation corridors enumerated as new-line
                                candidates for each flagged violation (in addition to the parallel
                                duplicate of the overloaded branch itself).
        :param base_overload_threshold: Base-case loading fraction above which a branch is flagged
                                        (1.0 = 100% of ``rate``).
        :param n1_overload_threshold: N-1 loading fraction above which a branch is flagged
                                      (1.0 = 100% of ``rate * contingency_factor``).
        :param ptdf_threshold: Sensitivities with absolute value below this are treated as zero.
        :param verify_top_k: Number of top-ranked candidates to verify with a fresh AC power flow
                             plus N-1 and voltage screening (step 5). Applied independently to the
                             overload-relief candidates and to the voltage-relief candidates.
        :param use_time_series: If True, scan ``time_indices`` for the most critical snapshot
                                (most base-case branch overloads plus bus voltage violations) and
                                run the whole pipeline at that snapshot instead of today's grid
                                state.
        :param time_indices: Time steps to scan when ``use_time_series`` is True. ``None`` means
                             every time step in the grid (``grid.get_all_time_indices()``).
        :param battery_duration_hours: Hours of ``Pmax`` used to size a battery candidate's
                                       ``Enom`` (``Enom = Pmax * battery_duration_hours``).
        :param shunt_bmax_margin: Headroom multiplier on a shunt-reactor candidate's upfront
                                  ``Bmax`` sizing estimate.
        :param max_injection_mw: Upper bound (MW) on a static-generator or battery candidate's
                                 sized real-power output.
        :param shunt_cost_per_mvar: CAPEX unit cost (EUR/MVAr) for a shunt-reactor candidate,
                                    applied to its sized ``Bmax``.
        :param static_gen_cost_per_mw: CAPEX unit cost (EUR/MW) for a static-generator candidate,
                                       applied to its sized ``P``.
        :param battery_cost_per_mwh: CAPEX unit cost (EUR/MWh) for a battery candidate, applied to
                                     its sized ``Enom`` (which already encodes both ``Pmax`` and
                                     ``battery_duration_hours``).
        :param line_cost_per_mva: CAPEX unit cost (EUR/MVA) for a new-line or upgrade candidate,
                                  applied to the candidate's rating (``rate`` for a new line,
                                  ``new_rate`` for an upgrade - the full post-upgrade rating, since
                                  an upgrade is modelled as replacing the branch with one built to
                                  the new rating, not adding incremental capacity).
        """
        self.top_n_corridors: int = int(top_n_corridors)
        self.base_overload_threshold: float = float(base_overload_threshold)
        self.n1_overload_threshold: float = float(n1_overload_threshold)
        self.ptdf_threshold: float = float(ptdf_threshold)
        self.verify_top_k: int = int(verify_top_k)
        self.use_time_series: bool = bool(use_time_series)
        self.time_indices: Optional[IntVec] = time_indices
        self.battery_duration_hours: float = float(battery_duration_hours)
        self.shunt_bmax_margin: float = float(shunt_bmax_margin)
        self.max_injection_mw: float = float(max_injection_mw)
        self.shunt_cost_per_mvar: float = float(shunt_cost_per_mvar)
        self.static_gen_cost_per_mw: float = float(static_gen_cost_per_mw)
        self.battery_cost_per_mwh: float = float(battery_cost_per_mwh)
        self.line_cost_per_mva: float = float(line_cost_per_mva)
