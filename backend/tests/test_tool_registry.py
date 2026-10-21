import pytest

from app.services.tools.fake_bank import FakeBankAPI
from app.services.tools.registry import (
    ToolNotFoundError,
    ToolRegistry,
)


def test_register_and_get_tool():
    registry = ToolRegistry()
    bank = FakeBankAPI()

    registry.register("transfer_money", bank.transfer_money)

    assert registry.has("transfer_money")
    assert registry.get("transfer_money") == bank.transfer_money


def test_list_registered_tools():
    registry = ToolRegistry()
    bank = FakeBankAPI()

    registry.register("transfer_money", bank.transfer_money)

    assert registry.list_tools() == ["transfer_money"]


def test_unknown_tool_raises_error():
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError):
        registry.get("unknown_tool")