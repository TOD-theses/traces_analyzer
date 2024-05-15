import pytest
from tests.test_utils.test_utils import _test_addr, _test_group32, _test_transient_storage
from traces_analyzer.utils.hexstring import HexString


def test_transient_storage_get():
    tables = _test_transient_storage({_test_addr("abcd"): {"1234": "11223344"}}, 1)

    value = tables.get(_test_addr("abcd"), HexString("1234"))

    assert value.get_hexstring() == HexString("11223344").as_size(32)
    assert value.depends_on_instruction_indexes() == {1}


def test_transient_storage_get_non_existent_address():
    tables = _test_transient_storage({})

    with pytest.raises(Exception):
        tables.get(_test_addr("abcd"), HexString("1234"))


def test_transient_storage_get_non_existent_key():
    tables = _test_transient_storage({_test_addr("abcd"): {}}, 1)

    with pytest.raises(Exception):
        tables.get(_test_addr("abcd"), HexString("1234"))


def test_transient_storage_get_after_set():
    tables = _test_transient_storage({})

    tables.set(_test_addr("abcd"), HexString("1234"), _test_group32("00112233", 1))
    value = tables.get(_test_addr("abcd"), HexString("1234"))

    assert value.get_hexstring() == HexString("00112233").as_size(32)
    assert value.depends_on_instruction_indexes() == {1}
