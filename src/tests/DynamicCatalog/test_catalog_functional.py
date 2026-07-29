from __future__ import annotations

from typing import Sequence

import pytest

from DynamicCatalog._catalog_functional_support import DynamicFunctionalContract
from DynamicCatalog._catalog_functional_support import FunctionalContract
from DynamicCatalog._catalog_functional_support import TestDevicesCatalogFunctionalContractsHarness
from DynamicCatalog._catalog_functional_support import build_dynamic_functional_contracts
from DynamicCatalog._catalog_functional_support import build_functional_contracts


def build_functional_contract_parameters() -> Sequence[FunctionalContract]:
    """
    Return the explicit static catalog contracts as pytest parameters.

    :returns: Static contract sequence.
    """

    return build_functional_contracts()


def build_dynamic_contract_parameters() -> Sequence[DynamicFunctionalContract]:
    """
    Return the explicit dynamic catalog contracts as pytest parameters.

    :returns: Dynamic contract sequence.
    """

    return build_dynamic_functional_contracts()


def build_functional_contract_id(contract: FunctionalContract) -> str:
    """
    Build the pytest id for one static catalog contract.

    :param contract: Static contract.
    :returns: Stable pytest id.
    """

    return contract.label


def build_dynamic_contract_id(contract: DynamicFunctionalContract) -> str:
    """
    Build the pytest id for one dynamic catalog contract.

    :param contract: Dynamic contract.
    :returns: Stable pytest id.
    """

    return contract.label


@pytest.fixture(scope="module")
def harness() -> TestDevicesCatalogFunctionalContractsHarness:
    """
    Construct the shared harness once for the whole functional suite.

    :returns: Shared functional-contract harness.
    """

    # The harness owns the assertion helpers and lightweight runtimes used by every
    # functional contract. Building it once keeps the parametrized suite explicit
    # without paying the setup cost thousands of times.
    test_harness: TestDevicesCatalogFunctionalContractsHarness = TestDevicesCatalogFunctionalContractsHarness()
    test_harness.setUpClass()
    return test_harness



