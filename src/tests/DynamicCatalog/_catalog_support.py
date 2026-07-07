from __future__ import annotations

from pathlib import Path
from typing import Sequence

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.BasicBlockCatalog import BasicBlockTemplateDescriptor
from VeraGridEngine.Templates.BasicBlockCatalog import get_pending_basic_block_catalog_descriptors
from VeraGridEngine.Templates.BasicBlockCatalog import get_basic_block_catalog_descriptor_by_key
from VeraGridEngine.Templates.BasicBlockCatalog import get_basic_block_catalog_descriptors
from VeraGridEngine.Templates.BasicBlockCatalog import get_basic_block_catalog_templates_dir
from VeraGridEngine.Templates.BasicBlockCatalog import load_basic_block_catalog_template


def build_templates_dir() -> Path:
    """
    Return the directory with shipped standalone template modules.

    :returns: Standalone-template directory.
    """

    return get_basic_block_catalog_templates_dir()


def descriptor_entries() -> Sequence[BasicBlockTemplateDescriptor]:
    """
    Return every shipped catalog descriptor.

    :returns: Full descriptor tuple.
    """

    return get_basic_block_catalog_descriptors()


def pending_descriptor_entries() -> Sequence[BasicBlockTemplateDescriptor]:
    """
    Return the pending catalog descriptors.

    :returns: Pending descriptor tuple.
    """

    return get_pending_basic_block_catalog_descriptors()


def descriptor_lookup_by_key() -> dict[str, BasicBlockTemplateDescriptor]:
    """
    Return the descriptor lookup indexed by semantic key.

    :returns: Descriptor lookup by semantic key.
    """

    return get_basic_block_catalog_descriptor_by_key()


def _resolve_descriptor(template_identifier: str) -> BasicBlockTemplateDescriptor:
    """
    Resolve one descriptor from either the semantic key or the old numeric fixture id.

    :param template_identifier: Semantic key or numeric fixture identifier.
    :returns: Matching descriptor.
    :raises KeyError: Raised when no descriptor matches.
    """

    descriptor_by_key: dict[str, BasicBlockTemplateDescriptor] = descriptor_lookup_by_key()
    descriptor: BasicBlockTemplateDescriptor | None = descriptor_by_key.get(template_identifier, None)

    if descriptor is not None:
        return descriptor
    else:
        pass

    if template_identifier.isdigit():
        candidate: BasicBlockTemplateDescriptor
        for candidate in descriptor_entries():
            if candidate.typ_id == template_identifier:
                return candidate
            else:
                pass
    else:
        pass

    raise KeyError(f"Unknown catalog template identifier '{template_identifier}'")


def find_template_path(template_identifier: str) -> Path:
    """
    Resolve the shipped standalone module path for one catalog template.

    :param template_identifier: Semantic key or numeric fixture identifier.
    :returns: Standalone module path.
    """

    descriptor: BasicBlockTemplateDescriptor = _resolve_descriptor(template_identifier)
    return build_templates_dir() / descriptor.module_filename


def build_template(template_identifier: str,
                   name: str | None = None) -> EmtModelTemplate:
    """
    Materialize one shipped standalone template through the static catalog runtime path.

    :param template_identifier: Semantic key or numeric fixture identifier.
    :param name: Optional explicit runtime template name.
    :returns: Materialized template.
    """

    descriptor: BasicBlockTemplateDescriptor = _resolve_descriptor(template_identifier)
    return load_basic_block_catalog_template(descriptor, VarFactory(), name=name)
