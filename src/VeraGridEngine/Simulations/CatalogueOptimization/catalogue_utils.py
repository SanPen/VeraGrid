# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import List, Tuple, Union

from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Branches.transformer import Transformer2W
from VeraGridEngine.Devices.Branches.overhead_line_type import OverheadLineType
from VeraGridEngine.Devices.Branches.sequence_line_type import SequenceLineType
from VeraGridEngine.Devices.Branches.underground_line_type import UndergroundLineType
from VeraGridEngine.Devices.Branches.transformer_type import TransformerType


# Type aliases for readability
LineTemplate = Union[OverheadLineType, SequenceLineType, UndergroundLineType]
Branch = Union[Line, Transformer2W]
Template = Union[OverheadLineType, SequenceLineType, UndergroundLineType, TransformerType]

# TODO: extend support to DcLine, VSC and HVDC branches with their own catalogue handling.
# Currently the catalogue optimization only supports AC `Line` and `Transformer2W` branches.


class LineSnapshot:
    """
    Snapshot of the editable fields of a `Line` that the `apply_template` method modifies.
    Used to revert a line to its baseline state between optimization evaluations.
    """
    __slots__ = (
        "branch",
        "R",
        "X",
        "B",
        "R0",
        "X0",
        "B0",
        "rate",
        "ys",
        "ysh",
        "template",
        "rms_template",
        "emt_template",
    )

    def __init__(self, branch: Line) -> None:
        """
        Capture the baseline values of every attribute that `Line.apply_template` overwrites.

        :param branch: line whose state is captured.
        """
        # Reference to the original branch so `restore` can mutate it back
        self.branch: Line = branch

        # Electrical parameters in per-unit on the system base
        self.R: float = branch.R
        self.X: float = branch.X
        self.B: float = branch.B
        self.R0: float = branch.R0
        self.X0: float = branch.X0
        self.B0: float = branch.B0

        # Thermal rating in MVA
        self.rate: float = branch.rate

        # Sequence admittance matrices (for OverheadLine / SequenceLineType templates)
        # We store the references; the template rewrites the attribute, so the original object is preserved.
        self.ys = branch.ys
        self.ysh = branch.ysh

        # Template references (catalog identity + dynamic templates)
        self.template = branch.template
        self.rms_template = branch.rms_template
        self.emt_template = branch.emt_template

    def restore(self) -> None:
        """
        Write the captured values back to the underlying branch, undoing any `apply_template` mutation.
        """
        # Restoring the simple scalars overwrites whatever the optimization step applied
        self.branch.R = self.R
        self.branch.X = self.X
        self.branch.B = self.B
        self.branch.R0 = self.R0
        self.branch.X0 = self.X0
        self.branch.B0 = self.B0
        self.branch.rate = self.rate

        # Re-attach the original admittance matrix references
        self.branch.ys = self.ys
        self.branch.ysh = self.ysh

        # Re-attach the original template pointers (or `None` if there was no template)
        self.branch.template = self.template
        self.branch.rms_template = self.rms_template
        self.branch.emt_template = self.emt_template


class TransformerSnapshot:
    """
    Snapshot of the editable fields of a `Transformer2W` that `apply_template` modifies.
    Used to revert the transformer to its baseline state between optimization evaluations.
    """
    __slots__ = (
        "branch",
        "HV",
        "LV",
        "R",
        "X",
        "G",
        "B",
        "rate",
        "rate_prof",
        "Sn",
        "Pcu",
        "Pfe",
        "I0",
        "Vsc",
        "tap_changer",
        "conn_f",
        "conn_t",
        "template",
        "rms_template",
        "emt_template",
    )

    def __init__(self, branch: Transformer2W) -> None:
        """
        Capture the baseline values of every attribute that `Transformer2W.apply_template` overwrites.

        :param branch: transformer whose state is captured.
        """
        # Reference to the original branch so `restore` can mutate it back
        self.branch: Transformer2W = branch

        # Voltage ratings in kV
        self.HV: float = branch.HV
        self.LV: float = branch.LV

        # Equivalent circuit parameters in per-unit
        self.R: float = branch.R
        self.X: float = branch.X
        self.G: float = branch.G
        self.B: float = branch.B

        # Thermal rating
        self.rate: float = branch.rate
        # Take a copy of the rate profile because `apply_template` overwrites it in place via `.fill(rate)`
        self.rate_prof = branch.rate_prof.copy()

        # Nameplate values
        self.Sn: float = branch.Sn
        self.Pcu: float = branch.Pcu
        self.Pfe: float = branch.Pfe
        self.I0: float = branch.I0
        self.Vsc: float = branch.Vsc

        # Tap changer object reference and winding connections
        self.tap_changer = branch.tap_changer
        self.conn_f = branch.conn_f
        self.conn_t = branch.conn_t

        # Template references (catalog identity + dynamic templates)
        self.template = branch.template
        self.rms_template = branch.rms_template
        self.emt_template = branch.emt_template

    def restore(self) -> None:
        """
        Write the captured values back to the underlying transformer, undoing any `apply_template` mutation.
        """
        # Restore voltage ratings (these alter the virtual tap, so they must come back exactly)
        self.branch.HV = self.HV
        self.branch.LV = self.LV

        # Restore equivalent circuit and rating
        self.branch.R = self.R
        self.branch.X = self.X
        self.branch.G = self.G
        self.branch.B = self.B
        self.branch.rate = self.rate

        # Restore the rate profile to the snapshotted copy
        # (we cannot just reuse the original reference because `apply_template` may keep mutating it)
        self.branch.rate_prof[:] = self.rate_prof

        # Restore nameplate values
        self.branch.Sn = self.Sn
        self.branch.Pcu = self.Pcu
        self.branch.Pfe = self.Pfe
        self.branch.I0 = self.I0
        self.branch.Vsc = self.Vsc

        # Restore tap changer and winding connections
        self.branch.tap_changer = self.tap_changer
        self.branch.conn_f = self.conn_f
        self.branch.conn_t = self.conn_t

        # Restore template pointers
        self.branch.template = self.template
        self.branch.rms_template = self.rms_template
        self.branch.emt_template = self.emt_template


def take_snapshot(branch: Branch) -> Union[LineSnapshot, TransformerSnapshot]:
    """
    Produce the right snapshot type for the given branch.

    :param branch: line or two-winding transformer whose state should be captured.
    :return: a `LineSnapshot` for AC lines or a `TransformerSnapshot` for transformers.
    :raises TypeError: if the branch is not a supported type.
    """
    # Discriminate the two supported branch classes; anything else is currently unsupported.
    if isinstance(branch, Line):
        return LineSnapshot(branch=branch)
    elif isinstance(branch, Transformer2W):
        return TransformerSnapshot(branch=branch)
    else:
        # The optimizer should never pass in unsupported branches; if it does, fail loud.
        raise TypeError(f"Branch type {type(branch).__name__} is not supported by the catalogue optimization.")


def _voltage_match(template_vn: float,
                   branch_vn: float,
                   voltage_tolerance: float) -> bool:
    """
    Check whether a template's nominal voltage is within +/-tolerance of a branch's nominal voltage.

    Symmetric replacement for ``accept_line_connection`` (in `Devices/Branches/line.py`), which is
    intentionally one-sided: that helper accepts any template whose voltage is at least
    ``(1 - tol)`` of the branch voltage but applies no upper bound, so a 400 kV template is
    considered "compatible" with a 33 kV line. For catalogue optimization we want a true band so
    only templates whose rating is genuinely close to the branch are kept in the decision pool.

    :param template_vn: template nominal voltage (kV).
    :param branch_vn: branch nominal voltage (kV).
    :param voltage_tolerance: relative tolerance, e.g. 0.1 for +/-10%.
    :return: True if the voltages match within the symmetric band, False otherwise.
    """
    # Branches with non-positive nominal voltage are degenerate; fall back to exact equality
    # so we never divide by zero or accept arbitrary templates.
    if branch_vn <= 0.0:
        return template_vn == branch_vn
    else:
        # Symmetric band: ratio must lie inside [1 - tol, 1 + tol].
        ratio: float = template_vn / branch_vn
        return (1.0 - voltage_tolerance) <= ratio <= (1.0 + voltage_tolerance)


def _line_template_matches(branch: Line,
                           template: LineTemplate,
                           voltage_tolerance: float) -> bool:
    """
    Decide whether a line template can be applied to a given AC line by checking voltage compatibility.

    :param branch: candidate line to receive the template.
    :param template: template under consideration.
    :param voltage_tolerance: relative tolerance accepted between template and line nominal voltages.
    :return: True if the template's nominal voltage matches the line, False otherwise.
    """
    # The line's nominal voltage is the maximum of its terminal nominal voltages
    line_vn: float = branch.get_max_bus_nominal_voltage()

    # Each line template type exposes its rated voltage through the `Vnom` attribute
    if isinstance(template, OverheadLineType):
        template_vn: float = template.Vnom
    elif isinstance(template, SequenceLineType):
        template_vn = template.Vnom
    elif isinstance(template, UndergroundLineType):
        template_vn = template.Vnom
    else:
        # Unsupported template type for an AC line: skip without erroring
        return False

    # Symmetric voltage check (the catalogue-optimization needs a true band; see `_voltage_match`).
    return _voltage_match(template_vn=template_vn,
                          branch_vn=line_vn,
                          voltage_tolerance=voltage_tolerance)


def _transformer_template_matches(branch: Transformer2W,
                                  template: TransformerType,
                                  voltage_tolerance: float) -> bool:
    """
    Decide whether a transformer template can be applied to a given two-winding transformer.

    Both the HV and LV rated voltages must match within tolerance.

    :param branch: candidate transformer to receive the template.
    :param template: transformer type under consideration.
    :param voltage_tolerance: relative tolerance accepted between template and transformer voltages.
    :return: True if both HV and LV ratings match, False otherwise.
    """
    # Compare both windings symmetrically: the optimization should never swap a 220/110 trafo
    # for a 220/20 unit (and the lopsided `accept_line_connection` would let that through).
    hv_match: bool = _voltage_match(template_vn=template.HV,
                                    branch_vn=branch.HV,
                                    voltage_tolerance=voltage_tolerance)
    lv_match: bool = _voltage_match(template_vn=template.LV,
                                    branch_vn=branch.LV,
                                    voltage_tolerance=voltage_tolerance)
    return hv_match and lv_match


def _gather_line_templates(grid: MultiCircuit) -> List[LineTemplate]:
    """
    Collect every line-compatible template that the grid currently holds in its catalogue.

    :param grid: source multi-circuit whose template lists are read.
    :return: combined list of overhead, sequence and underground line templates.
    """
    # Pre-allocate the combined pool by extending separate iterations to keep the order deterministic
    pool: List[LineTemplate] = list()
    for tpl in grid.overhead_line_types:
        pool.append(tpl)
    for tpl in grid.sequence_line_types:
        pool.append(tpl)
    # NOTE: the property is `underground_cable_types`, NOT `underground_line_types`
    for tpl in grid.underground_cable_types:
        pool.append(tpl)
    return pool


def build_catalogue_pool(grid: MultiCircuit,
                         selected_branches: List[Branch],
                         voltage_tolerance: float,
                         logger: Logger) -> Tuple[List[Branch], List[List[Template]]]:
    """
    Build the per-branch catalogue pool for the optimization.

    The function categorizes each selected branch (AC line or two-winding transformer), gathers the
    templates of the matching kind from the grid catalogue, filters them by voltage compatibility,
    and removes any branch whose pool would have one option or fewer (those slots cannot be optimized
    over because there is nothing to choose from).

    :param grid: multi-circuit whose template catalogues provide the candidate templates.
    :param selected_branches: branches that the user has pre-selected on the schematic.
    :param voltage_tolerance: relative voltage tolerance (e.g. 0.1 for 10%).
    :param logger: logger that receives warnings about unsupported branches and dropped slots.
    :return: parallel lists `(branches, pools)` such that `pools[i]` is the list of templates
        compatible with `branches[i]`. Both lists have the same length.
    """
    # Pre-fetch the catalogues once: walking them per-branch would be wasteful
    line_templates: List[LineTemplate] = _gather_line_templates(grid=grid)
    transformer_templates: List[TransformerType] = list()
    for tpl in grid.transformer_types:
        transformer_templates.append(tpl)

    # Diagnostic dump of the four catalogue lists. Helps the user see whether the optimization
    # found nothing because the catalogue is empty, or because it only holds the wrong type.
    print("[CatalogueOptimization] Catalogue contents:")
    print(f"  overhead_line_types     : {len(grid.overhead_line_types)} entries")
    print(f"  sequence_line_types     : {len(grid.sequence_line_types)} entries")
    print(f"  underground_cable_types : {len(grid.underground_cable_types)} entries")
    print(f"  transformer_types       : {len(grid.transformer_types)} entries")

    # The two output lists are kept in lock-step: index i always refers to the same branch
    kept_branches: List[Branch] = list()
    kept_pools: List[List[Template]] = list()

    # Iterate over the user selection and try to assign a non-degenerate template pool to each branch
    for branch in selected_branches:

        if isinstance(branch, Line):
            # Build the pool of voltage-compatible line templates for this specific line
            pool: List[Template] = list()
            for tpl in line_templates:
                if _line_template_matches(branch=branch,
                                          template=tpl,
                                          voltage_tolerance=voltage_tolerance):
                    pool.append(tpl)
                else:
                    pass  # template ignored; voltage rating does not match
            kept_branches, kept_pools = _accept_or_drop_pool(branch=branch,
                                                             pool=pool,
                                                             kept_branches=kept_branches,
                                                             kept_pools=kept_pools,
                                                             logger=logger)

        elif isinstance(branch, Transformer2W):
            # Build the pool of voltage-compatible transformer templates for this specific transformer
            pool = list()
            for tpl in transformer_templates:
                if _transformer_template_matches(branch=branch,
                                                 template=tpl,
                                                 voltage_tolerance=voltage_tolerance):
                    pool.append(tpl)
                else:
                    pass  # template ignored; HV/LV ratings do not match
            kept_branches, kept_pools = _accept_or_drop_pool(branch=branch,
                                                             pool=pool,
                                                             kept_branches=kept_branches,
                                                             kept_pools=kept_pools,
                                                             logger=logger)

        else:
            # TODO: add catalogue support for DcLine, VSC and HVDC branches.
            logger.add_warning(msg="Unsupported branch type for catalogue optimization (AC Line and "
                                   "Transformer2W only at this stage)",
                               device=branch.name,
                               device_class=type(branch).__name__)

    # Diagnostic dump of the per-slot pool sizes. Helps the user see, for every surviving branch,
    # how many templates the optimizer has to choose from (i.e. the cardinality of each decision slot).
    print(f"[CatalogueOptimization] Surviving branches: "
          f"{len(kept_branches)} of {len(selected_branches)} selected")
    for kept_branch, kept_pool in zip(kept_branches, kept_pools):
        print(f"  {kept_branch.name:30s} -> {len(kept_pool)} compatible templates")

    return kept_branches, kept_pools


def _accept_or_drop_pool(branch: Branch,
                         pool: List[Template],
                         kept_branches: List[Branch],
                         kept_pools: List[List[Template]],
                         logger: Logger) -> Tuple[List[Branch], List[List[Template]]]:
    """
    Decide whether the candidate pool of a branch is rich enough to be included in the optimization.

    A pool is degenerate when it contains 0 or 1 templates: with no alternatives the optimizer has
    nothing to choose, so the branch is silently dropped (with a logger entry) to keep the decision
    vector small and meaningful.

    :param branch: branch under evaluation.
    :param pool: list of templates judged compatible with `branch`.
    :param kept_branches: running accumulator of branches that survived the filter.
    :param kept_pools: running accumulator of the corresponding template pools.
    :param logger: logger that receives the explanatory warning.
    :return: updated `(kept_branches, kept_pools)` lists.
    """
    if len(pool) == 0:
        # Branch had zero compatible templates: warn the user so they can extend the catalogue
        logger.add_warning(msg="Branch dropped from catalogue optimization: no compatible templates found",
                           device=branch.name,
                           device_class=type(branch).__name__)
    elif len(pool) == 1:
        # Branch had exactly one option: the slot would be a constant, so it is not worth optimizing
        logger.add_warning(msg="Branch dropped from catalogue optimization: only one compatible template available",
                           device=branch.name,
                           device_class=type(branch).__name__,
                           value=pool[0].name)
    else:
        # Two or more options: the slot becomes a real decision variable
        kept_branches.append(branch)
        kept_pools.append(pool)

    return kept_branches, kept_pools


def template_capex(branch: Branch, template: Template) -> float:
    """
    Compute the capital expenditure of applying a template to a branch.

    Line templates have a per-km capex (`currency/km`), so the cost scales with the line length.
    Transformer templates carry a flat capex (`currency`).

    :param branch: branch that would receive the template.
    :param template: template under consideration.
    :return: capex contribution in currency units.
    :raises TypeError: if branch and template combination is not supported.
    """
    # AC line templates are priced per kilometer of line
    if isinstance(template, OverheadLineType):
        if isinstance(branch, Line):
            return float(template.capex) * float(branch.length)
        else:
            raise TypeError("OverheadLineType can only be applied to a Line branch")
    elif isinstance(template, SequenceLineType):
        if isinstance(branch, Line):
            return float(template.capex) * float(branch.length)
        else:
            raise TypeError("SequenceLineType can only be applied to a Line branch")
    elif isinstance(template, UndergroundLineType):
        if isinstance(branch, Line):
            return float(template.capex) * float(branch.length)
        else:
            raise TypeError("UndergroundLineType can only be applied to a Line branch")
    elif isinstance(template, TransformerType):
        # Transformer templates carry a flat capex regardless of the branch's "length"
        if isinstance(branch, Transformer2W):
            return float(template.capex)
        else:
            raise TypeError("TransformerType can only be applied to a Transformer2W branch")
    else:
        raise TypeError(f"Unsupported template type: {type(template).__name__}")
