import pytest
from plugin import Plugin
from pytest_indigo import IndigoMock


@pytest.fixture()
def plugin(plugin) -> Plugin:
    return plugin


@pytest.fixture()
def indigo(indigo) -> IndigoMock[Plugin]:
    return indigo
