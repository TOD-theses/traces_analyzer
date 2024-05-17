import pytest
from tests.test_utils.test_utils import _test_group, _test_group32, _test_stack
from traces_analyzer.parser.storage.stack import Stack
from traces_analyzer.utils.hexstring import HexString


def test_stack_empty():
    stack = Stack()

    assert stack.size() == 0


def test_stack_peek():
    stack = _test_stack(["1234", "5678"])

    val = stack.peek(1)

    assert val.get_hexstring() == HexString("5678").as_size(32)


def test_stack_push():
    stack = Stack()

    stack.push(_test_group("1234"))

    assert stack.size() == 1
    assert stack.peek(0).get_hexstring() == HexString("1234").as_size(32)


def test_stack_push_all():
    stack = Stack()

    stack.push_all([_test_group("1234"), _test_group("5678")])

    assert stack.size() == 2
    assert stack.peek(0).get_hexstring() == HexString("1234").as_size(32)
    assert stack.peek(1).get_hexstring() == HexString("5678").as_size(32)


def test_stack_set():
    stack = _test_stack(["0x1", "0x2", "0x3", "0x4"])

    stack.set(2, _test_group32("11223344", 1234))

    assert stack.peek(2).get_hexstring() == HexString("11223344").as_size(32)
    assert stack.peek(2).depends_on_instruction_indexes() == {1234}


def test_stack_set_with_wrong_size():
    stack = _test_stack(["0x1", "0x2", "0x3", "0x4"])

    with pytest.raises(Exception):
        stack.set(2, _test_group("11223344", 1234))


def test_stack_pop():
    stack = _test_stack(["0x1", "0x2"])

    x = stack.pop()

    assert stack.size() == 1
    assert x.get_hexstring() == HexString("0x1").as_size(32)


def test_stack_get_all():
    stack = _test_stack(["1", "2", "3"])

    result = stack.get_all()

    assert len(result) == 3
    assert result[0].get_hexstring() == HexString("1").as_size(32)
    assert result[1].get_hexstring() == HexString("2").as_size(32)
    assert result[2].get_hexstring() == HexString("3").as_size(32)


def test_stack_clear():
    stack = _test_stack(["1", "2"])

    stack.clear()

    assert stack.size() == 0
