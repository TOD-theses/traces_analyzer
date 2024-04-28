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


def _test_group(hexstring: str | HexString, step_index=1) -> StorageByteGroup:
    if isinstance(hexstring, str):
        hexstring = HexString(hexstring)
    return StorageByteGroup.from_hexstring(hexstring, step_index)


def _test_mem(memory: str, step_index=1) -> Memory:
    mem = Memory()
    mem.set(0, _test_group(memory, step_index), step_index)
    return mem
