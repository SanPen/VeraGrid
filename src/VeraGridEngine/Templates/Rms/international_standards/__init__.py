import keyword
import re

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import InternationalStandardModel
from VeraGridEngine.Utils.Symbolic.symbolic import Var

from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ac1a import build_ac1a_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ac1c import build_ac1c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ac6a import build_ac6a_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ac6c import build_ac6c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ac7b import build_ac7b_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ac7c import build_ac7c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ac8b import build_ac8b_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ac8c import build_ac8c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.bbsex1 import build_bbsex1_template
from VeraGridEngine.Templates.Rms.international_standards.battery_energy_storage.besscbcurrentsourcenoplantcontrol import build_besscbcurrentsourcenoplantcontrol_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.dc1a import build_dc1a_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.dc1c import build_dc1c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.exac1 import build_exac1_template
from VeraGridEngine.Templates.Rms.international_standards.governors.govhydro4 import build_govhydro4_template
from VeraGridEngine.Templates.Rms.international_standards.governors.govsteam1 import build_govsteam1_template
from VeraGridEngine.Templates.Rms.international_standards.governors.govsteameu import build_govsteameu_template
from VeraGridEngine.Templates.Rms.international_standards.governors.ieeeg1 import build_ieeeg1_template
from VeraGridEngine.Templates.Rms.international_standards.governors.ieeeg2 import build_ieeeg2_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ieeet1 import build_ieeet1_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ieeex2 import build_ieeex2_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ieex2a import build_ieex2a_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.maxex2 import build_maxex2_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.oel2c import build_oel2c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.oel3c import build_oel3c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.oel4c import build_oel4c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.oel5c import build_oel5c_template
from VeraGridEngine.Templates.Rms.international_standards.power_system_stabilizers.pss1aomega import build_pss1aomega_template
from VeraGridEngine.Templates.Rms.international_standards.power_system_stabilizers.pss1apgen import build_pss1apgen_template
from VeraGridEngine.Templates.Rms.international_standards.power_system_stabilizers.pss2a import build_pss2a_template
from VeraGridEngine.Templates.Rms.international_standards.power_system_stabilizers.pss2b import build_pss2b_template
from VeraGridEngine.Templates.Rms.international_standards.power_system_stabilizers.pss2c import build_pss2c_template
from VeraGridEngine.Templates.Rms.international_standards.power_system_stabilizers.pss3b import build_pss3b_template
from VeraGridEngine.Templates.Rms.international_standards.power_system_stabilizers.pss3c import build_pss3c_template
from VeraGridEngine.Templates.Rms.international_standards.power_system_stabilizers.pss6c import build_pss6c_template
from VeraGridEngine.Templates.Rms.international_standards.power_system_stabilizers.psskundur import build_psskundur_template
from VeraGridEngine.Templates.Rms.international_standards.solar_pv_generation.pvcurrentsourcebnoplantcontrol import build_pvcurrentsourcebnoplantcontrol_template
from VeraGridEngine.Templates.Rms.international_standards.solar_pv_generation.pvvoltagesourceanoplantcontrol import build_pvvoltagesourceanoplantcontrol_template
from VeraGridEngine.Templates.Rms.international_standards.solar_pv_generation.pvvoltagesourcebnoplantcontrol import build_pvvoltagesourcebnoplantcontrol_template
from VeraGridEngine.Templates.Rms.international_standards.renewable_controls.reecb import build_reecb_template
from VeraGridEngine.Templates.Rms.international_standards.renewable_controls.reecc import build_reecc_template
from VeraGridEngine.Templates.Rms.international_standards.renewable_controls.regcbcs import build_regcbcs_template
from VeraGridEngine.Templates.Rms.international_standards.renewable_controls.repca import build_repca_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.scl1c import build_scl1c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.scl2c import build_scl2c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.scrx import build_scrx_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.sexs import build_sexs_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st1a import build_st1a_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st1c import build_st1c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st4b import build_st4b_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st4c import build_st4c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st5b import build_st5b_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st5c import build_st5c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st6b import build_st6b_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st6c import build_st6c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st7b import build_st7b_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st7c import build_st7c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.st9c import build_st9c_template
from VeraGridEngine.Templates.Rms.international_standards.governors.tgov3 import build_tgov3_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.uel1 import build_uel1_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.uel2c import build_uel2c_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.vrkundur import build_vrkundur_template
from VeraGridEngine.Templates.Rms.international_standards.wind_generation.wpp4bcurrentsource2020 import build_wpp4bcurrentsource2020_template
from VeraGridEngine.Templates.Rms.international_standards.wind_generation.wt4acurrentsource import build_wt4acurrentsource_template
from VeraGridEngine.Templates.Rms.international_standards.wind_generation.wt4acurrentsource2020 import build_wt4acurrentsource2020_template
from VeraGridEngine.Templates.Rms.international_standards.wind_generation.wt4bcurrentsource2020 import build_wt4bcurrentsource2020_template
from VeraGridEngine.Templates.Rms.international_standards.wind_generation.wt4bcurrentsource import build_wt4bcurrentsource_template
from VeraGridEngine.Templates.Rms.international_standards.wind_generation.wt4injector import build_wt4injector_template
from VeraGridEngine.Templates.Rms.international_standards.wind_generation.wtg4acurrentsource import build_wtg4acurrentsource_template
from VeraGridEngine.Templates.Rms.international_standards.wind_generation.wtg4bcurrentsource import build_wtg4bcurrentsource_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.ieeevc_1981 import build_ieeevc_1981_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_systems.esdc2a import build_esdc2a_template
from VeraGridEngine.Templates.Rms.international_standards.protection_relays.frqtpa import build_frqtpa_template
from VeraGridEngine.Templates.Rms.international_standards.protection_relays.vtgtpa import build_vtgtpa_template
from VeraGridEngine.Templates.Rms.international_standards.induction_machines.cimtr1 import build_cimtr1_template
from VeraGridEngine.Templates.Rms.international_standards.induction_machines.cimw import build_cimw_template
from VeraGridEngine.Templates.Rms.international_standards.synchronous_machines.gensal import build_gensal_template
from VeraGridEngine.Templates.Rms.international_standards.synchronous_machines.genrou import build_genrou_template
from VeraGridEngine.Templates.Rms.international_standards.governors.ggov1 import build_ggov1_template
from VeraGridEngine.Templates.Rms.international_standards.governors.hygov import build_hygov_template
from VeraGridEngine.Templates.Rms.international_standards.excitation_limiters.ieel import build_ieel_template
from VeraGridEngine.Templates.Rms.international_standards.governors.tgov1 import build_tgov1_template


def _build_python_identifier(source_name: str) -> str:
    """Convert one imported Modelica symbol name into a Python identifier.

    The Dynamic Block Properties editor serializes symbolic equations as
    Python source. Modelica hierarchy separators, array indices and generated
    names such as ``$START`` therefore need a stable identifier spelling.

    :param source_name: Symbol name emitted by the Modelica importer.
    :return: Python-compatible spelling of the same symbolic name.
    """
    identifier: str = re.sub(r"[^0-9A-Za-z_]", "_", source_name)
    identifier = re.sub(r"_+", "_", identifier)

    # Keep even unusual generated names representable in editable source.
    if len(identifier) == 0:
        identifier = "variable"
    else:
        pass

    if identifier[0].isdigit() or keyword.iskeyword(identifier):
        identifier = f"variable_{identifier}"
    else:
        pass

    return identifier


def _normalize_imported_variable_names(
        vf: VarFactory,
        existing_variable_uids: set[int],
) -> None:
    """Normalize only the variables allocated by one imported template.

    Symbolic identity is UID-based, so changing a variable's serialization
    name leaves the equations unchanged. Existing editor variables are kept
    untouched, and deterministic suffixes avoid collisions after punctuation
    is converted to underscores.

    :param vf: Factory containing both existing and newly imported variables.
    :param existing_variable_uids: Stable identities present before import.
    :return: None.
    """
    all_variables: list[Var] = list()
    new_variables: list[Var] = list()
    seen_variable_uids: set[int] = set()
    occupied_names: set[str] = set()
    variable_uid: int
    variable: Var

    # Differential variables can live in their own factory registry. Merge
    # both registries once while retaining their stable insertion order.
    for variable_uid, variable in vf.get_vars_dict().items():
        if variable_uid not in seen_variable_uids:
            all_variables.append(variable)
            seen_variable_uids.add(variable_uid)
        else:
            pass

    for variable_uid, variable in vf.get_diff_var_dict().items():
        if variable_uid not in seen_variable_uids:
            all_variables.append(variable)
            seen_variable_uids.add(variable_uid)
        else:
            pass

    # Reserve the spellings owned by the editor before this model was added.
    for variable in all_variables:
        if variable.non_mutable_uid in existing_variable_uids:
            occupied_names.add(variable.name)
        else:
            new_variables.append(variable)

    # Rename the imported surface without changing any symbolic UID links.
    for variable in new_variables:
        base_identifier: str = _build_python_identifier(variable.name)
        unique_identifier: str = base_identifier
        suffix: int = 2
        while unique_identifier in occupied_names:
            unique_identifier = f"{base_identifier}_{suffix}"
            suffix += 1

        variable.set_name(unique_identifier)
        occupied_names.add(unique_identifier)


def build_international_standard_template(
        model: InternationalStandardModel,
        vf: VarFactory,
        name: str | None = None,
) -> RmsModelTemplate:
    """
    Materialize one international-standard dynamic model without function pointers.

    :param model: Enumerated dynamic model to materialize.
    :type model: InternationalStandardModel
    :param vf: Variable factory that owns the symbolic variables.
    :type vf: VarFactory
    :param name: Optional runtime instance name.
    :type name: str | None
    :return: Materialized international-standard RMS dynamic template.
    :rtype: RmsModelTemplate
    """
    template: RmsModelTemplate
    existing_variable_uids: set[int] = set(vf.get_vars_dict().keys())
    existing_variable_uids.update(vf.get_diff_var_dict().keys())

    # Dispatch explicitly so every supported state is visible and statically imported.
    if model == InternationalStandardModel.AC1A:
        template = build_ac1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC1C:
        template = build_ac1c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC6A:
        template = build_ac6a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC6C:
        template = build_ac6c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC7B:
        template = build_ac7b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC7C:
        template = build_ac7c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC8B:
        template = build_ac8b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.AC8C:
        template = build_ac8c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.BBSEX1:
        template = build_bbsex1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.BESSCBCURRENTSOURCENOPLANTCONTROL:
        template = build_besscbcurrentsourcenoplantcontrol_template(vf=vf, name=name)
    elif model == InternationalStandardModel.DC1A:
        template = build_dc1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.DC1C:
        template = build_dc1c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.EXAC1:
        template = build_exac1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GOVHYDRO4:
        template = build_govhydro4_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GOVSTEAM1:
        template = build_govsteam1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GOVSTEAMEU:
        template = build_govsteameu_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEG1:
        template = build_ieeeg1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEG2:
        template = build_ieeeg2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEET1:
        template = build_ieeet1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEX2:
        template = build_ieeex2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEX2A:
        template = build_ieex2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.MAXEX2:
        template = build_maxex2_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OEL2C:
        template = build_oel2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OEL3C:
        template = build_oel3c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OEL4C:
        template = build_oel4c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.OEL5C:
        template = build_oel5c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS1AOMEGA:
        template = build_pss1aomega_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS1APGEN:
        template = build_pss1apgen_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS2A:
        template = build_pss2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS2B:
        template = build_pss2b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS2C:
        template = build_pss2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS3B:
        template = build_pss3b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS3C:
        template = build_pss3c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSS6C:
        template = build_pss6c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PSSKUNDUR:
        template = build_psskundur_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PVCURRENTSOURCEBNOPLANTCONTROL:
        template = build_pvcurrentsourcebnoplantcontrol_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PVVOLTAGESOURCEANOPLANTCONTROL:
        template = build_pvvoltagesourceanoplantcontrol_template(vf=vf, name=name)
    elif model == InternationalStandardModel.PVVOLTAGESOURCEBNOPLANTCONTROL:
        template = build_pvvoltagesourcebnoplantcontrol_template(vf=vf, name=name)
    elif model == InternationalStandardModel.REECB:
        template = build_reecb_template(vf=vf, name=name)
    elif model == InternationalStandardModel.REECC:
        template = build_reecc_template(vf=vf, name=name)
    elif model == InternationalStandardModel.REGCBCS:
        template = build_regcbcs_template(vf=vf, name=name)
    elif model == InternationalStandardModel.REPCA:
        template = build_repca_template(vf=vf, name=name)
    elif model == InternationalStandardModel.SCL1C:
        template = build_scl1c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.SCL2C:
        template = build_scl2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.SCRX:
        template = build_scrx_template(vf=vf, name=name)
    elif model == InternationalStandardModel.SEXS:
        template = build_sexs_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST1A:
        template = build_st1a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST1C:
        template = build_st1c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST4B:
        template = build_st4b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST4C:
        template = build_st4c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST5B:
        template = build_st5b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST5C:
        template = build_st5c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST6B:
        template = build_st6b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST6C:
        template = build_st6c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST7B:
        template = build_st7b_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST7C:
        template = build_st7c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ST9C:
        template = build_st9c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.TGOV3:
        template = build_tgov3_template(vf=vf, name=name)
    elif model == InternationalStandardModel.UEL1:
        template = build_uel1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.UEL2C:
        template = build_uel2c_template(vf=vf, name=name)
    elif model == InternationalStandardModel.VRKUNDUR:
        template = build_vrkundur_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WPP4BCURRENTSOURCE2020:
        template = build_wpp4bcurrentsource2020_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4ACURRENTSOURCE:
        template = build_wt4acurrentsource_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4ACURRENTSOURCE2020:
        template = build_wt4acurrentsource2020_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4BCURRENTSOURCE2020:
        template = build_wt4bcurrentsource2020_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4BCURRENTSOURCE:
        template = build_wt4bcurrentsource_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WT4INJECTOR:
        template = build_wt4injector_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WTG4ACURRENTSOURCE:
        template = build_wtg4acurrentsource_template(vf=vf, name=name)
    elif model == InternationalStandardModel.WTG4BCURRENTSOURCE:
        template = build_wtg4bcurrentsource_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEEVC_1981:
        template = build_ieeevc_1981_template(vf=vf, name=name)
    elif model == InternationalStandardModel.ESDC2A:
        template = build_esdc2a_template(vf=vf, name=name)
    elif model == InternationalStandardModel.FRQTPA:
        template = build_frqtpa_template(vf=vf, name=name)
    elif model == InternationalStandardModel.VTGTPA:
        template = build_vtgtpa_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CIMTR1:
        template = build_cimtr1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.CIMW:
        template = build_cimw_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GENSAL:
        template = build_gensal_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GENROU:
        template = build_genrou_template(vf=vf, name=name)
    elif model == InternationalStandardModel.GGOV1:
        template = build_ggov1_template(vf=vf, name=name)
    elif model == InternationalStandardModel.HYGOV:
        template = build_hygov_template(vf=vf, name=name)
    elif model == InternationalStandardModel.IEEL:
        template = build_ieel_template(vf=vf, name=name)
    elif model == InternationalStandardModel.TGOV1:
        template = build_tgov1_template(vf=vf, name=name)
    else:
        # The Enum exhausts the supported domain; this branch protects future additions.
        raise ValueError(f"Unsupported international-standard model: {model!s}")

    # Imported Modelica names contain hierarchy and index punctuation that is
    # not valid in the editor's Python equation representation.
    _normalize_imported_variable_names(
        vf=vf,
        existing_variable_uids=existing_variable_uids,
    )

    return template
