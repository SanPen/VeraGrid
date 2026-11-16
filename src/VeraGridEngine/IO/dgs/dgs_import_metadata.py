# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Import-owned metadata independent of model runtime declarations."""
from __future__ import annotations

from typing import Dict

from VeraGridEngine.enumerations import DgsImportField

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Utils.Symbolic.block import Block


class DgsImportMetadata:
    """Operate on the dictionary owned by one DynamicModelImport instance."""

    __slots__ = ("blocks",)

    def __init__(self, blocks: Dict[int, Dict[str, bool | int | float | str | None]]) -> None:
        """Bind the dictionary owned by one importer.

        :param blocks: Parent-block UIDs mapped to scalar import declarations.
        :return: None.
        """
        self.blocks: Dict[int, Dict[str, bool | int | float | str | None] | None] = blocks

    def ensure(self, block: Block) -> Dict[str, bool | int | float | str | None] | None:
        """Allocate a parent record only when a declaration is written.

        :param block: Parent model receiving an import declaration.
        :return: Existing or newly allocated scalar record.
        """
        record: Dict[str, bool | int | float | str | None] | None = self.blocks.get(block.uid, None)
        if record is None:
            record = dict()
            self.blocks[block.uid] = record
        else:
            pass
        return record

    def get(self, block: Block, field: DgsImportField) -> bool | int | float | str | None:
        """Read a declaration that its owner has explicitly registered.

        :param block: Parent model owning the required declaration.
        :param field: Registered import field.
        :return: Explicitly stored scalar, including an intentional None.
        :raises KeyError: The parent or requested field has not been registered.
        """
        if self.blocks[block.uid] is not None:
            value = self.blocks[block.uid][field.value]
            return value
        else:
            return None


def get_import_field(block: Block, field: DgsImportField,
                     import_metadata: DgsImportMetadata) -> bool | int | float | str | None:
    """Read an explicitly registered parent declaration without defaults.

    :param block: Parent model owning the declaration.
    :param field: Required import field.
    :param import_metadata: Registry owned by the active importer.
    :return: Explicitly stored scalar.
    :raises KeyError: The parent or requested field has not been registered.
    """
    return import_metadata.get(block, field)


def set_import_field(block: Block, field: DgsImportField, value: bool | int | float | str | None,
                     import_metadata: DgsImportMetadata | None = None) -> None:
    """Write one scalar declaration against its parent model UID.

    :param block: Parent model owning the declaration.
    :param field: Supported import field.
    :param value: Scalar declaration to retain during import.
    :param import_metadata: Registry owned by the active importer, if present.
    :return: None.
    """
    if import_metadata is not None:
        record: Dict[str, bool | int | float | str | None] | None = import_metadata.ensure(block)
        if record is not None:
            record[field.value] = value
    else:
        pass


def assign_import_template(device: DynamicDevice,
                           template: RmsModelTemplate | EmtModelTemplate) -> None:
    """Assign a template without updating the import dictionary.

    The setters publish the template before they build and validate its model,
    so a rejected template is removed here and the host keeps no half assignment.

    :param device: Exact physical host receiving the model.
    :param template: Reusable template to instantiate.
    :return: None.
    :raises TypeError, ValueError, KeyError: The host rejected the template.
    """
    if isinstance(template, RmsModelTemplate):
        try:
            device.rms_template = template
        except (TypeError, ValueError, KeyError):
            device.rms_template = None
            raise
    else:
        previous_emt_model: Block | None = device.emt_model
        try:
            device.emt_template = template
        except (TypeError, ValueError, KeyError):
            device.emt_template = None
            device.emt_model = previous_emt_model
            raise
