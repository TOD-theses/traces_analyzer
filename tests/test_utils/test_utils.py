from traces_analyzer.parser.storage.memory import Memory
from traces_analyzer.parser.storage.stack import Stack
from traces_analyzer.parser.storage.storage_value import HexStringStorageValue
from traces_analyzer.utils.hexstring import HexString


def _test_addr(name: str) -> HexString:
    return HexString.from_int(hash(name)).as_address()


def _test_stack(items: list[str]) -> Stack:
    stack = Stack()
    stack.push_all([HexStringStorageValue(HexString(val)) for val in items])
    return stack


def _test_mem(memory: str) -> Memory:
    mem = Memory()
    mem.set(0, HexStringStorageValue(HexString(memory)))
    return mem
