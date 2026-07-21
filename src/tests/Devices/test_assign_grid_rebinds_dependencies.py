import pandas as pd

from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.Devices as dev


def build_main_elements_dict_by_type(main_grid: MultiCircuit,
                                     use_secondary_key: bool = False) -> dict[object, dict[str, object]]:
    """
    Build the per-device-type lookup dictionaries used by assign_grid().

    :param main_grid: Grid receiving the imported objects.
    :return: Device-type lookup dictionaries keyed by idtag.
    """
    main_elements_dict_by_type: dict[object, dict[str, object]] = dict()
    template_elm: object
    device_type: object

    for template_elm in main_grid.template_items():
        device_type = template_elm.device_type
        main_elements_dict_by_type[device_type] = main_grid.get_elements_dict_by_type(
            element_type=device_type,
            use_secondary_key=use_secondary_key
        )

    return main_elements_dict_by_type


def test_assign_grid_rebinds_new_load_to_existing_bus() -> None:
    """
    assign_grid() must attach newly imported injections to the canonical main-grid bus.

    The imported bus may match an existing bus while the imported load itself is
    new. In that case the load must be rebound to the existing bus object before
    insertion, otherwise the main grid ends up with a foreign bus reference.
    """
    main_grid: MultiCircuit = MultiCircuit()
    loaded_grid: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()
    main_bus: dev.Bus = dev.Bus(name="main-bus", idtag="bus-id")
    imported_bus: dev.Bus = dev.Bus(name="imported-bus", idtag="bus-id")
    imported_load: dev.Load = dev.Load(name="imported-load", idtag="load-id", P=12.0)
    associated_branches: list[object]
    associated_injections: list[object]

    main_grid.time_profile = pd.to_datetime(["2024-01-01 00:00:00"])
    main_grid.add_bus(obj=main_bus)
    main_grid.ensure_profiles_exist()

    loaded_grid.add_bus(obj=imported_bus)
    loaded_grid.add_load(bus=imported_bus, api_obj=imported_load)

    main_grid.assign_grid(
        t=0,
        grid_to_add=loaded_grid,
        main_elements_dict_by_type=build_main_elements_dict_by_type(main_grid=main_grid),
        use_secondary_key=False,
        logger=logger
    )

    assert len(main_grid.loads) == 1
    assert main_grid.loads[0] is imported_load
    assert imported_load.bus is main_bus
    assert imported_load.bus is not imported_bus

    associated_branches, associated_injections = main_grid.get_bus_devices(main_bus)

    assert len(associated_branches) == 0
    assert associated_injections == [imported_load]


def test_assign_grid_rebinds_associations_when_matching_by_code() -> None:
    """
    assign_grid() must rebind association targets under code-based matching too.

    The GUI import path defaults to code matching, so associations such as
    technologies must reconcile to the canonical main-grid object even when the
    imported idtag differs.
    """
    main_grid: MultiCircuit = MultiCircuit()
    loaded_grid: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()
    main_bus: dev.Bus = dev.Bus(name="main-bus", idtag="main-bus-id", code="bus-code")
    imported_bus: dev.Bus = dev.Bus(name="imported-bus", idtag="imported-bus-id", code="bus-code")
    main_technology: dev.Technology = dev.Technology(name="main-tech", idtag="main-tech-id", code="tech-code")
    imported_technology: dev.Technology = dev.Technology(
        name="imported-tech",
        idtag="imported-tech-id",
        code="tech-code"
    )
    imported_load: dev.Load = dev.Load(name="imported-load", idtag="load-id", code="load-code", P=7.0)

    main_grid.time_profile = pd.to_datetime(["2024-01-01 00:00:00"])
    main_grid.add_bus(obj=main_bus)
    main_grid.add_technology(obj=main_technology)
    main_grid.ensure_profiles_exist()

    loaded_grid.add_bus(obj=imported_bus)
    loaded_grid.add_technology(obj=imported_technology)
    loaded_grid.add_load(bus=imported_bus, api_obj=imported_load)
    imported_load.technologies.add_object(api_object=imported_technology, val=1.0)

    main_grid.assign_grid(
        t=0,
        grid_to_add=loaded_grid,
        main_elements_dict_by_type=build_main_elements_dict_by_type(main_grid=main_grid, use_secondary_key=True),
        use_secondary_key=True,
        logger=logger
    )

    assert len(main_grid.loads) == 1
    assert imported_load.bus is main_bus
    assert imported_load.technologies.to_list() == [main_technology]


def test_assign_grid_rebinds_late_template_dependencies() -> None:
    """
    assign_grid() must rebind direct references whose target type is processed later.

    Branches are imported before catalogue objects. A line that points to a
    matching existing sequence-line type must be rebound after the full import
    pass, otherwise it keeps the temporary imported template object.
    """
    main_grid: MultiCircuit = MultiCircuit()
    loaded_grid: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()
    main_bus_from: dev.Bus = dev.Bus(name="main-from", idtag="main-bus-from", code="bus-from")
    main_bus_to: dev.Bus = dev.Bus(name="main-to", idtag="main-bus-to", code="bus-to")
    imported_bus_from: dev.Bus = dev.Bus(name="imported-from", idtag="imported-bus-from", code="bus-from")
    imported_bus_to: dev.Bus = dev.Bus(name="imported-to", idtag="imported-bus-to", code="bus-to")
    main_template: dev.SequenceLineType = dev.SequenceLineType(name="main-template", idtag="main-template-id")
    imported_template: dev.SequenceLineType = dev.SequenceLineType(name="imported-template", idtag="imported-template-id")
    imported_line: dev.Line = dev.Line(
        name="imported-line",
        idtag="line-id",
        code="line-code",
        bus_from=imported_bus_from,
        bus_to=imported_bus_to,
        template=imported_template
    )

    main_template.code = "tpl-code"
    imported_template.code = "tpl-code"

    main_grid.time_profile = pd.to_datetime(["2024-01-01 00:00:00"])
    main_grid.add_bus(obj=main_bus_from)
    main_grid.add_bus(obj=main_bus_to)
    main_grid.add_sequence_line(obj=main_template)
    main_grid.ensure_profiles_exist()

    loaded_grid.add_bus(obj=imported_bus_from)
    loaded_grid.add_bus(obj=imported_bus_to)
    loaded_grid.add_line(obj=imported_line)
    loaded_grid.add_sequence_line(obj=imported_template)

    main_grid.assign_grid(
        t=0,
        grid_to_add=loaded_grid,
        main_elements_dict_by_type=build_main_elements_dict_by_type(main_grid=main_grid, use_secondary_key=True),
        use_secondary_key=True,
        logger=logger
    )

    assert len(main_grid.lines) == 1
    assert imported_line.bus_from is main_bus_from
    assert imported_line.bus_to is main_bus_to
    assert imported_line.template is main_template


if __name__ == "__main__":
    test_assign_grid_rebinds_new_load_to_existing_bus()
    print("ok")


def test_assign_grid_deactivates_missing_elements_at_time_step() -> None:
    """
    assign_grid() must deactivate profiled elements that are absent from the imported snapshot.
    """
    main_grid: MultiCircuit = MultiCircuit()
    loaded_grid_t1: MultiCircuit = MultiCircuit()
    logger: Logger = Logger()

    bus_t0 = dev.Bus(name="bus", idtag="bus-id", code="bus-code")
    load_t0 = dev.Load(name="load", idtag="load-id", code="load-code", P=10.0, active=True)

    bus_t1 = dev.Bus(name="bus", idtag="bus-id", code="bus-code")

    main_grid.time_profile = pd.to_datetime(["2024-01-01 00:00:00", "2024-01-01 01:00:00"])
    main_grid.add_bus(obj=bus_t0)
    main_grid.add_load(bus=bus_t0, api_obj=load_t0)
    main_grid.ensure_profiles_exist()

    loaded_grid_t1.add_bus(obj=bus_t1)

    main_grid.assign_grid(
        t=1,
        grid_to_add=loaded_grid_t1,
        main_elements_dict_by_type=build_main_elements_dict_by_type(main_grid=main_grid, use_secondary_key=True),
        use_secondary_key=True,
        logger=logger
    )

    assert main_grid.loads[0].active_prof[1] is False
