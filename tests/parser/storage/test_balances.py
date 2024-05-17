import pytest
from tests.test_utils.test_utils import _test_addr, _test_balances
from traces_analyzer.parser.storage.balances import InvalidAddressException
from traces_analyzer.utils.hexstring import HexString


def test_balances_last_modified_at_step_index():
    balances = _test_balances({"abcd": 1234})

    last_modified_step_index = balances.last_modified_at_step_index(
        HexString("abcd").as_address()
    )

    assert last_modified_step_index == 1234


def test_balances_last_modified_at_step_index_for_unknown_address():
    balances = _test_balances()

    last_modified_step_index = balances.last_modified_at_step_index(
        HexString("abcd").as_address()
    )

    assert last_modified_step_index == -1


def test_balances_modified_at_step_index_updates_last_modified():
    balances = _test_balances()

    balances.modified_at_step_index(_test_addr("abcd"), 1234)
    last_modified_at_step_index = balances.last_modified_at_step_index(
        _test_addr("abcd")
    )

    assert last_modified_at_step_index == 1234


def test_balances_throws_on_access_with_invalid_address():
    balances = _test_balances()

    with pytest.raises(InvalidAddressException):
        balances.last_modified_at_step_index(HexString("abcd"))


def test_balances_throws_on_set_with_invalid_address():
    balances = _test_balances()

    with pytest.raises(InvalidAddressException):
        balances.modified_at_step_index(HexString("abcd"), 1234)
