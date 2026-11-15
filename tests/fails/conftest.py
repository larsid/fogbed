import pytest

from fogbed import emulation
from fogbed.node.container import Container
from fogbed.node.instance import VirtualInstance


@pytest.fixture(autouse=True)
def clean_emulation_state():
    emulation.nodes.clear()
    Container.IP_COUNTER = 0
    VirtualInstance.COUNTER = 0
    yield
    emulation.nodes.clear()
