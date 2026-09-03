import copy

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate


def test_rms_template_deepcopy_preserves_auto_update_state() -> None:
    """An RMS template copy must retain its auto-update state."""

    template: RmsModelTemplate = RmsModelTemplate()

    assert copy.deepcopy(template).auto_update_enabled

    template.disable_auto_updates()

    assert not copy.deepcopy(template).auto_update_enabled


def test_emt_template_deepcopy_preserves_auto_update_state() -> None:
    """An EMT template copy must retain its auto-update state."""

    template: EmtModelTemplate = EmtModelTemplate()

    assert copy.deepcopy(template).auto_update_enabled

    template.disable_auto_updates()

    assert not copy.deepcopy(template).auto_update_enabled


def test_fmu_template_deepcopy_preserves_auto_update_state() -> None:
    """An FMU template copy must retain its auto-update state."""

    template: FmuTemplate = FmuTemplate()

    assert copy.deepcopy(template).auto_update_enabled

    template.disable_auto_updates()

    assert not copy.deepcopy(template).auto_update_enabled
