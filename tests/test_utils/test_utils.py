from typing import Callable
from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.storage.memory import Memory
from traces_analyzer.parser.storage.stack import Stack
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.utils.hexstring import HexString


def _test_addr(name: str) -> HexString:
    return HexString.from_int(hash(name)).as_address()


def _test_stack(items: list[str]) -> Stack:
    stack = Stack()
    stack.push_all([_test_group(val) for val in items])
    return stack


def _test_group(hexstring: str | HexString, step_index=-1) -> StorageByteGroup:
    if isinstance(hexstring, str):
        hexstring = HexString(hexstring)
    return StorageByteGroup.from_hexstring(hexstring, step_index)


def _test_group32(hexstring: str | HexString, step_index=-1) -> StorageByteGroup:
    if isinstance(hexstring, str):
        hexstring = HexString(hexstring)
    if len(hexstring) < 32:
        padding = HexString("0" * (64 - len(hexstring)))
        hexstring = padding + hexstring
    return StorageByteGroup.from_hexstring(hexstring, step_index)


def _test_mem(memory: str, step_index=1) -> Memory:
    mem = Memory()
    mem.set(0, _test_group(memory, step_index), step_index)
    return mem


def _test_root():
    return CallContext(None, HexString(""), 1, _test_addr("0xsender"), _test_addr("0xcode"), _test_addr("0xstorage"))


def _test_child_of(parent: CallContext, address: HexString):
    return CallContext(parent, HexString(""), parent.depth + 1, parent.code_address, address, address)


def _test_child():
    return _test_child_of(_test_root(), _test_addr("0xchild"))


def _test_grandchild():
    return _test_child_of(_test_child(), _test_addr("0xgrandchild"))
