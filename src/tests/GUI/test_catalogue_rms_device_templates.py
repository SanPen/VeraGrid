"""Contracts for the reusable RMS device-template catalog."""

from __future__ import annotations

from PySide6 import QtWidgets

from VeraGrid.Gui.CatalogueElementsDialogue.catalogue_actions import CatalogueAction
from VeraGrid.Gui.CatalogueElementsDialogue.catalogue_elements_dialogue import (
    CatalogueElementsSelectionDialogue,
)
import VeraGridEngine.Templates as tem
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Templates.InternationalStandardsCatalog import (
    InternationalStandardTemplateDescriptor,
    get_international_standard_device_template_descriptors,
)


def test_rms_catalogue_matches_supported_gui_device_templates(qt_app: QtWidgets.QApplication) -> None:
    """Keep the GUI catalog limited to its established non-phasor devices.

    :param qt_app: Shared Qt application required to construct the dialog.
    :return: None.
    """
    application: QtWidgets.QApplication = qt_app
    circuit: MultiCircuit = MultiCircuit()
    dialog: CatalogueElementsSelectionDialogue = CatalogueElementsSelectionDialogue(
        parent=None,
        circuit=circuit,
    )
    actions: list[CatalogueAction] = dialog.build_rms_actions()
    action_keys: set[str] = set(action.unique_key for action in actions)
    expected_keys: set[str] = set((
        'rms:get_complete_generator_template_rms',
        'rms:get_genqec_rms',
        'rms:get_genrow_rms_template',
        'rms:get_line_rms_template',
        'rms:build_dc_line_rms_v2',
        'rms:get_load_rms_template',
        'rms:get_transformer2w_rms',
        'rms:get_shunt_template',
        'rms:get_pvd1_rms_template',
        'rms:get_pvd1_complete_rms_template',
        'rms:get_pvd1_dc_mppt_rms_template',
        'rms:get_pvd1_dc_link_mppt_rms_template',
        'rms:get_pvd1_dc_link_bess_rms_template',
        'rms:get_esd1_rms_template',
        'rms:VoltageSourceBuild',
        'rms:build_hvdc_vsc_gfl_rms',
    ))
    excluded_phasor_keys: set[str] = set((
        'rms:get_line_phasor_rms_template',
        'rms:get_load_phasor_current_rms_template',
        'rms:get_complete_generator_template_phasor',
        'rms:get_genqec_phasor',
    ))
    excluded_control_keys: set[str] = set((
        'rms:get_governor_rms',
        'rms:get_stabilizer_rms',
        'rms:get_exciter_rms',
        'rms:get_pll_transform_rms',
        'rms:get_pi_current_controller',
        'rms:get_pi_power_controller',
        'rms:get_gfl_converter_rms',
        'rms:get_empty_rms_template',
        'rms:build_ac1a_template',
        'rms:build_govhydro4_template',
        'rms:build_pss2a_template',
        'rms:build_reecb_template',
        'rms:build_uel1_template',
        'rms:build_frqtpa_template',
    ))

    assert action_keys == expected_keys
    assert action_keys.isdisjoint(excluded_phasor_keys)
    assert action_keys.isdisjoint(excluded_control_keys)

    actions_by_key: dict[str, CatalogueAction] = dict(
        (action.unique_key, action) for action in actions
    )
    assert actions_by_key['rms:VoltageSourceBuild'].function_ptr is tem.VoltageSourceBuild
    assert (
        actions_by_key['rms:build_hvdc_vsc_gfl_rms'].function_ptr
        is tem.build_hvdc_vsc_gfl_rms
    )
    assert (
        actions_by_key['rms:get_transformer2w_rms'].function_ptr
        is tem.get_transformer2w_rms
    )
    assert (
        actions_by_key['rms:build_dc_line_rms_v2'].function_ptr
        is tem.build_dc_line_rms_v2
    )

    descriptor: InternationalStandardTemplateDescriptor
    for descriptor in get_international_standard_device_template_descriptors():
        international_key: str = f'rms:build_{descriptor.template_key}_template'
        assert international_key not in action_keys

    dialog.close()
    application.processEvents()
