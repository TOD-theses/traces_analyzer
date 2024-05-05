from unittest.mock import MagicMock
from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.storage.balances import Balances
from traces_analyzer.parser.storage.memory import Memory
from traces_analyzer.parser.storage.stack import Stack
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.utils.hexstring import HexString

TestVal = str | HexString | StorageByteGroup


def _test_hash_addr(name: str) -> HexString:
    """Map a name to a 20 bytes address"""
    return HexString.from_int(abs(hash(name))).as_address()


def _test_stack(items: list[TestVal], step_index=-1) -> Stack:
    stack = Stack()
    stack.push_all([_test_group32(val, step_index) for val in items])
    return stack


def _test_balances(balances: dict[str | HexString, int] = {}) -> Balances:
    balances_storage = Balances()
    for addr, val in balances.items():
        balances_storage.modified_at_step_index(_test_addr(addr), val)

    return balances_storage


def _test_addr(addr: str | HexString) -> HexString:
    if isinstance(addr, str):
        addr = HexString(addr)
    if len(addr) != 40:
        addr = addr.as_address()
    return addr


def _test_hexstring(val: str | HexString):
    if isinstance(val, HexString):
        return val
    return HexString(val)


def _test_group(hexstring: TestVal, step_index=-1) -> StorageByteGroup:
    if isinstance(hexstring, StorageByteGroup):
        return hexstring
    if isinstance(hexstring, str):
        hexstring = HexString(hexstring)
    return StorageByteGroup.from_hexstring(hexstring, step_index)


def _test_group32(hexstring: TestVal, step_index=-1) -> StorageByteGroup:
    if isinstance(hexstring, StorageByteGroup):
        return hexstring
    if isinstance(hexstring, str):
        hexstring = HexString(hexstring)
    if len(hexstring) < 32:
        padding = HexString("0" * (64 - len(hexstring)))
        hexstring = padding + hexstring
    return StorageByteGroup.from_hexstring(hexstring, step_index)


def _test_mem(memory: TestVal, step_index=1) -> Memory:
    mem = Memory()
    mem.set(0, _test_group(memory, step_index), step_index)
    return mem


def _test_root():
    return CallContext(
        None, HexString(""), 1, _test_hash_addr("0xsender"), _test_hash_addr("0xcode"), _test_hash_addr("0xstorage")
    )


def _test_child_of(parent: CallContext, address: HexString):
    return CallContext(parent, HexString(""), parent.depth + 1, parent.code_address, address, address)


def _test_child():
    return _test_child_of(_test_root(), _test_hash_addr("0xchild"))


def _test_grandchild():
    return _test_child_of(_test_child(), _test_hash_addr("0xgrandchild"))


def mock_env(
    step_index=-1,
    storage_step_index=-1,
    current_call_context=_test_root(),
    last_executed_sub_context=_test_child(),
    stack_contents: list[TestVal] | None = None,
    memory_content: TestVal | None = None,
    balances: dict[str | HexString, int] | None = None,
):
    env = MagicMock(spec=ParsingEnvironment)
    env.current_step_index = step_index
    env.current_call_context = current_call_context
    env.last_executed_sub_context = last_executed_sub_context
    if stack_contents:
        env.stack = _test_stack(stack_contents, storage_step_index)
    if memory_content:
        env.memory = _test_mem(memory_content, storage_step_index)
    if balances:
        env.balances = _test_balances(balances)
    return env


def _test_oracle(stack: list[str | HexString] = [], memory: str | HexString = "", depth=1) -> InstructionOutputOracle:
    return InstructionOutputOracle([_test_hexstring(x) for x in stack], _test_hexstring(memory), depth)
