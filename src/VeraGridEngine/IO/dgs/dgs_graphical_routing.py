# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Resolve graphical routing tags into exact DGS producer ports."""

from __future__ import annotations

import ast
import re

from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkFrom, BlkGoto, BlkSig, IntGrf, IntGrfgroup, IntGrfnet


def _routed_signal_name(label: str) -> str:
    """Signal name of a cable label without PowerFactory's duplicate-name suffix.

    PowerFactory names a second line carrying ``Vt_filt`` as ``Vt_filt(1)``.

    :param label: Exported cable name.
    :return: Signal name.
    """
    return re.sub(r"\(\d+\)$", "", label.strip())


def build_graphical_node_scopes(circuit: DgsCircuit) -> dict[str, set[str]]:
    """Read diagram ownership through graphics and their parent containers.

    :param circuit: Parsed source including optional IntGrf/IntGrfnet sections.
    :return: Data-object FIDs mapped to their explicitly exported diagram scopes.
    """
    parents: dict[str, str] = dict()
    diagram_scopes: dict[str, str] = dict()
    group: IntGrfgroup
    graphic: IntGrf
    diagram: IntGrfnet
    for group in circuit.intgrfgroups:
        parents[group.ID] = str(group.fold_id or '')
    for graphic in circuit.intgrfs:
        parents[graphic.ID] = str(graphic.fold_id or '')
    for diagram in circuit.intgrfnets:
        parents[diagram.ID] = str(diagram.fold_id or '')
        if diagram.pDataFolder:
            diagram_scopes[diagram.ID] = str(diagram.pDataFolder).lstrip('#')
        else:
            pass
    result: dict[str, set[str]] = dict()
    # Native exports provide lexical ownership even when diagrams are absent.
    definitions = {definition.ID for definition in circuit.blkdefs}
    for element in circuit.get_all_elements_iter():
        owner = str(getattr(element, 'fold_id', '') or '').lstrip('#')
        if element.element_type.startswith('Blk') and owner in definitions:
            result.setdefault(element.ID, set()).add(owner)
    for graphic in circuit.intgrfs:
        container: str = str(graphic.fold_id or '').lstrip('#')
        visited: set[str] = set()
        while container and container not in diagram_scopes and container not in visited:
            visited.add(container)
            container = parents.get(container, '').lstrip('#')
        scope: str | None = diagram_scopes.get(container, None)
        if scope is not None and graphic.pDataObj:
            result.setdefault(str(graphic.pDataObj).lstrip('#'), set()).add(scope)
        else:
            pass
    return result


def _reference_parameter_dependencies(values: list[float | str | None]) -> set[str] | None:
    """Read free symbols from exported parameter bindings without executing DSL.

    :param values: Literal or symbolic BlkRef parameter bindings.
    :return: Free parameter names, or None for an unsupported binding expression.
    """
    dependencies: set[str] = set()
    value: float | str | None
    for value in values:
        if isinstance(value, str) and value.strip():
            try:
                expression: ast.Expression = ast.parse(value.strip(), mode='eval')
            except SyntaxError:
                return None
            else:
                # Function identifiers are not parent parameters. Dotted source
                # references lack a local namespace contract and remain unowned.
                function_nodes: set[int] = set()
                node: ast.AST
                for node in ast.walk(expression):
                    if isinstance(node, ast.Attribute):
                        return None
                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            function_nodes.add(id(node.func))
                        else:
                            return None
                    else:
                        pass
                for node in ast.walk(expression):
                    if isinstance(node, ast.Name) and id(node) not in function_nodes:
                        dependencies.add(node.id)
                    else:
                        pass
        else:
            pass
    return dependencies


def build_graphical_reference_owner_candidates(circuit: DgsCircuit) -> dict[str, set[str]]:
    """Retain all lexical owners compatible with complete typed BlkRef bindings.

    Matching parameter, state and internal bindings against their own declaration
    categories avoids choosing by a common signal name or by partial overlap.
    Unbound references remain unconstrained. Multiple compatible definitions
    retain exclusion evidence rather than being treated as unknown ownership.

    :param circuit: Source definitions and their graphical reference bindings.
    :return: Compatible definition FIDs for every reference with binding evidence.
    """
    parameter_owners: dict[str, set[str]] = dict()
    state_owners: dict[str, set[str]] = dict()
    internal_owners: dict[str, set[str]] = dict()
    declarations: list[str]
    index: dict[str, set[str]]
    name: str
    for definition in circuit.blkdefs:
        for declarations, index in ((definition.params, parameter_owners),
                                    (definition.upper_limit_params, parameter_owners),
                                    (definition.lower_limit_params, parameter_owners),
                                    (definition.states, state_owners),
                                    (definition.internals, internal_owners)):
            for name in declarations:
                index.setdefault(name, set()).add(definition.ID)
    result: dict[str, set[str]] = dict()
    for reference in circuit.blkrefs:
        parameters: set[str] = set()
        complete_parameters: bool = True
        values: list[float | str | None]
        for values in (reference.params, reference.upper_limit_params, reference.lower_limit_params):
            dependencies: set[str] | None = _reference_parameter_dependencies(values)
            if dependencies is None:
                complete_parameters = False
            else:
                parameters.update(dependencies)
        if not complete_parameters:
            pass
        elif not parameters and not reference.states and not reference.internals:
            pass
        else:
            candidates: set[str] | None = None
            bindings: set[str]
            for bindings, index in ((parameters, parameter_owners),
                                    (set(reference.states), state_owners),
                                    (set(reference.internals), internal_owners)):
                for name in bindings:
                    matches: set[str] = index.get(name, set())
                    if candidates is None:
                        candidates = set(matches)
                    else:
                        candidates.intersection_update(matches)
            if candidates is None:
                pass
            else:
                # The referenced definition supplies the child's own namespace,
                # not the containing macro's lexical binding context.
                candidates.discard(reference.typ_id)
                result[reference.ID] = candidates
    return result


def build_graphical_reference_owners(circuit: DgsCircuit) -> dict[str, str]:
    """Report only references whose complete bindings prove one owner.

    :param circuit: Source definitions and graphical reference bindings.
    :return: Unique owner FIDs, preserving the existing inspection interface.
    """
    candidates: dict[str, set[str]] = build_graphical_reference_owner_candidates(circuit)
    result: dict[str, str] = dict()
    identifier: str
    owners: set[str]
    for identifier, owners in candidates.items():
        if len(owners) == 1:
            result[identifier] = next(iter(owners))
        else:
            pass
    return result


class DgsGraphicalRoutingResolver:
    """Follow routing wires without treating their labels as global aliases."""

    __slots__ = ('root_id', 'root_inputs', 'nodes', 'selected', 'cables', 'incoming', 'gotos',
                 'scopes', 'adjacency', 'definitions', 'component_owners', 'outgoing', 'reference_owner_candidates')

    def __init__(self, circuit: DgsCircuit, root_id: str,
                 root_inputs: list[str], selected: set[str]) -> None:
        """Index exact wires and source ownership for one macro instance.

        :param circuit: Authoritative graphical source records.
        :param root_id: Current macro definition FID.
        :param root_inputs: Declared macro input ports in source order.
        :param selected: Nodes reached by the macro graph materializer.
        :return: None.
        """
        self.root_id: str = root_id
        self.root_inputs: list[str] = root_inputs
        self.selected: set[str] = selected
        self.nodes: dict[str, BlkFrom | BlkGoto] = dict()
        reader: BlkFrom
        writer: BlkGoto
        cable: BlkSig
        for reader in circuit.blkfroms:
            self.nodes[reader.ID] = reader
        for writer in circuit.blkgotos:
            self.nodes[writer.ID] = writer
        self.gotos: list[BlkGoto] = circuit.blkgotos
        self.cables: list[BlkSig] = circuit.blksigs
        self.incoming: dict[str, list[BlkSig]] = dict()
        self.outgoing: dict[str, list[BlkSig]] = dict()
        self.adjacency: dict[str, set[str]] = dict()
        for cable in circuit.blksigs:
            source: str = str(cable.pnodfrom or '').lstrip('#')
            target: str = str(cable.pnodto or '').lstrip('#')
            self.incoming.setdefault(target, list()).append(cable)
            self.outgoing.setdefault(source, list()).append(cable)
            if source and target:
                self.adjacency.setdefault(source, set()).add(target)
                self.adjacency.setdefault(target, set()).add(source)
            else:
                pass
        self.scopes: dict[str, set[str]] = build_graphical_node_scopes(circuit)
        self.definitions: set[str] = set(definition.ID for definition in circuit.blkdefs)
        self.component_owners: dict[str, set[str] | None] = dict()
        self.reference_owner_candidates: dict[str, set[str]] = build_graphical_reference_owner_candidates(circuit)

    def _is_local(self, identifier: str, expected: set[str]) -> bool:
        """Intersect ownership evidence and reject contexts it rules out.

        None denotes missing evidence; an empty compatible set permits no owner.
        Several candidates remain useful when they exclude the current macro.

        :param identifier: Candidate routing-node FID.
        :param expected: Macro contexts allowed by the reader.
        :return: Whether the component may belong to an expected macro.
        """
        if identifier not in self.component_owners:
            reached: set[str] = set()
            frontier: list[str] = list((identifier,))
            owners: set[str] | None = None
            while frontier:
                node: str = frontier.pop()
                if node in reached:
                    pass
                else:
                    reached.add(node)
                    constraints: tuple[set[str] | None, ...] = (
                        self.reference_owner_candidates.get(node, None),
                        self.scopes.get(node, None),
                        set((node,)) if node in self.definitions else None,
                    )
                    constraint: set[str] | None
                    for constraint in constraints:
                        if constraint is None:
                            pass
                        elif owners is None:
                            owners = set(constraint)
                        else:
                            previous: set[str] = set(owners)
                            owners.intersection_update(constraint)
                            if len(owners) == 0:
                                raise ValueError(
                                    f'Graphical DGS component has conflicting macro owners '
                                    f'{sorted(previous)} and {sorted(constraint)} at {identifier}; '
                                    f'connected nodes: {sorted(reached)}')
                            else:
                                pass
                    if node in self.definitions:
                        pass
                    else:
                        frontier.extend(self.adjacency.get(node, set()) - reached)
            # Preserve None separately from a constrained empty set and share
            # the component's intersection across all its physical routing nodes.
            for member in reached:
                self.component_owners[member] = owners
        else:
            pass
        compatible: set[str] | None = self.component_owners[identifier]
        return compatible is None or len(compatible & expected) > 0

    def expand_selected_nodes(self) -> set[str]:
        """Reach disconnected producer components through proven routing paths.

        Ambiguous paths remain unresolved and are diagnosed when the executable
        consumer is connected. No nearest-name producer is guessed here.

        :return: Expanded macro nodes, including original boundary nodes.
        """
        changed: bool = True
        while changed:
            added: set[str] = set()
            identifier: str
            cable: BlkSig
            for identifier in tuple(self.selected):
                if identifier in self.nodes:
                    for cable in self.outgoing.get(identifier, list()):
                        if str(cable.pnodto or '').lstrip('#') in self.selected:
                            try:
                                resolved: BlkSig = self.resolve(cable)
                            except ValueError:
                                # The connection phase reports the exact path.
                                pass
                            else:
                                frontier: list[str] = list((str(resolved.pnodfrom or '').lstrip('#'),))
                                while frontier:
                                    reached: str = frontier.pop()
                                    if not reached or reached in self.selected or reached in added:
                                        pass
                                    elif not self._is_local(reached, set((self.root_id,))):
                                        pass
                                    else:
                                        added.add(reached)
                                        if reached in self.definitions:
                                            pass
                                        else:
                                            frontier.extend(self.adjacency.get(reached, set()) - added - self.selected)
                        else:
                            pass
                else:
                    pass
            changed = len(added) > 0
            self.selected.update(added)
        return self.selected

    def resolve(self, cable: BlkSig) -> BlkSig:
        """Replace a routed source with its actual producer and original port.

        :param cable: Cable whose destination and descriptive label remain intact.
        :return: Original cable or an independent resolved cable declaration.
        """
        current: BlkSig = cable
        visited: set[tuple[str, int]] = set()
        while str(current.pnodfrom or '').lstrip('#') in self.nodes:
            identifier: str = str(current.pnodfrom).lstrip('#')
            endpoint_key: tuple[str, int] = (identifier, int(current.inodfrom))
            if endpoint_key in visited:
                raise ValueError(f'Graphical DGS routing cycle in macro {self.root_id}: {sorted(visited)} -> {identifier}')
            else:
                visited.add(endpoint_key)
            node: BlkFrom | BlkGoto = self.nodes[identifier]
            candidates: list[BlkSig] = list()
            if isinstance(node, BlkFrom):
                expected: set[str] = set((self.root_id,))
                reader_scopes: set[str] = self.scopes.get(identifier, expected)
                if self.root_id not in reader_scopes:
                    raise ValueError(f'Graphical DGS From {identifier} belongs to another macro scope')
                else:
                    pass
                if not 0 <= int(current.inodfrom) < len(node.signals):
                    raise ValueError(f'Graphical DGS From {identifier} has an invalid signal port {current.inodfrom}')
                else:
                    tag: str = node.signals[int(current.inodfrom)].strip()
                writer: BlkGoto
                incoming: BlkSig
                for writer in self.gotos:
                    for incoming in self.incoming.get(writer.ID, list()):
                        # Older DGS exports omit sSig on Goto. In that case
                        # the Goto name or its incoming cable supplies the routed
                        # tag (GB: Goto "freeze_Voltage_Dip" fed by "Voltage_Dip(1)").
                        labels: list[str] = writer.signals
                        if len(labels) == 0:
                            labels = list((writer.loc_name.strip(), _routed_signal_name(incoming.loc_name)))
                        else:
                            pass
                        if tag in labels and self._is_local(writer.ID, expected):
                            candidates.append(incoming)
                        else:
                            pass
                if len(candidates) == 0 and tag not in self.root_inputs:
                    # Without a Goto, a From reads the named signal line of its own macro
                    # instance (GB REEC_D: From "Ip_unlim" reads the cable "Ip_unlim" of its limiter)
                    producers: dict[tuple[str, int], BlkSig] = dict()
                    named: BlkSig
                    for named in self.cables:
                        producer: str = str(named.pnodfrom or '').lstrip('#')
                        if (producer and producer not in self.nodes and producer in self.selected
                                and _routed_signal_name(named.loc_name) == tag
                                and self._is_local(producer, expected)):
                            producers.setdefault((producer, int(named.inodfrom)), named)
                        else:
                            pass
                    candidates = list(producers.values())
                else:
                    pass
                if len(candidates) == 0 and tag in self.root_inputs:
                    # A From may read a declared macro input directly. Its
                    # exact boundary port is evidence, unlike an arbitrary alias.
                    endpoint: BlkSig = BlkSig()
                    endpoint.pnodfrom = self.root_id
                    endpoint.inodfrom = self.root_inputs.index(tag)
                    endpoint.iconfrom = 1
                    candidates.append(endpoint)
                else:
                    pass
            else:
                candidates = self.incoming.get(identifier, list())
            if len(candidates) != 1:
                raise ValueError(f'Graphical DGS From/Goto route in macro {self.root_id} at {identifier} '
                                 f'has {len(candidates)} producers: {[item.ID for item in candidates]}')
            else:
                current = candidates[0]
                if not current.pnodfrom:
                    raise ValueError(f'Graphical DGS route {identifier} has a blank producer cable {current.ID}')
                else:
                    pass
        if current is cable:
            return cable
        else:
            if not self._is_local(str(current.pnodfrom).lstrip('#'), set((self.root_id,))):
                raise ValueError(f'Graphical DGS routed producer {current.pnodfrom} belongs to another macro scope')
            else:
                pass
            # Preserve source records for other macro instances and editor views.
            resolved: BlkSig = BlkSig()
            resolved.ID = cable.ID
            resolved.OP = cable.OP
            resolved.loc_name = cable.loc_name
            resolved.pnodto = cable.pnodto
            resolved.inodto = cable.inodto
            resolved.iconto = cable.iconto
            resolved.pnodfrom = current.pnodfrom
            resolved.inodfrom = current.inodfrom
            resolved.iconfrom = current.iconfrom
            return resolved
