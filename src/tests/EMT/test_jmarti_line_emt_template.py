from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.jmarti_line_emt_template import get_jmarti_line_emt_template
from VeraGridEngine.enumerations import EmtLineTypes


def test_jmarti_line_emt_template_exposes_active_phase_terminal_voltages_and_history_vars() -> None:
    vf: VarFactory = VarFactory()
    templ = get_jmarti_line_emt_template(
        vf=vf,
        phN=False,
        phA=True,
        phB=True,
        phC=False,
        name="JMartiCase",
    )
    input_names = [var.name for var in templ.block.in_vars]
    history_names = sorted(var.name for var in templ.block.event_dict.keys())

    assert templ.block.name == EmtLineTypes.J_Marti.value
    assert input_names == [
        "vf_A_JMartiCase",
        "vf_B_JMartiCase",
        "vt_A_JMartiCase",
        "vt_B_JMartiCase",
    ]
    assert history_names == [
        "Ih_f_JMartiCase_A",
        "Ih_f_JMartiCase_B",
        "Ih_t_JMartiCase_A",
        "Ih_t_JMartiCase_B",
    ]
