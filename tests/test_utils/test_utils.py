from typing import Iterable
from unittest.mock import MagicMock
from traces_analyzer.parser.environment.call_context import CallContext, HaltType
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import CREATE, CREATE2, PUSH32, CallInstruction
from traces_analyzer.parser.storage.balances import Balances
from traces_analyzer.parser.storage.memory import Memory
from traces_analyzer.parser.storage.stack import Stack
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata
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


def _test_call_context(
    parent: CallContext | None = None,
    calldata: TestVal = "",
    value: TestVal = "0",
    depth: int = 1,
    msg_sender: HexString = _test_hash_addr("0xsender"),
    code_address: HexString = _test_hash_addr("0xcode"),
    storage_address: HexString = _test_hash_addr("0xstorage"),
    initiating_instruction: CallInstruction | CREATE | CREATE2 | None = None,
    return_data: TestVal = "",
    reverted: bool = False,
    halt_type: HaltType | None = None,
    is_contract_initialization: bool = False,
):
    return CallContext(
        parent,
        _test_group(calldata),
        _test_group(value),
        depth,
        msg_sender,
        code_address,
        storage_address,
        initiating_instruction,
        _test_group(return_data),
        reverted,
        halt_type,
        is_contract_initialization,
    )


def _test_root():
    return _test_call_context(depth=1)


def _test_child_of(parent: CallContext, address: HexString):
    return _test_call_context(
        parent=parent,
        depth=parent.depth + 1,
        msg_sender=parent.storage_address,
        code_address=address,
        storage_address=address,
    )


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
    if stack_contents is not None:
        env.stack = _test_stack(stack_contents, storage_step_index)
    if memory_content is not None:
        env.memory = _test_mem(memory_content, storage_step_index)
    if balances is not None:
        env.balances = _test_balances(balances)
    return env


def _test_oracle(stack: list[str | HexString] = [], memory: str | HexString = "", depth=1) -> InstructionOutputOracle:
    return InstructionOutputOracle([_test_hexstring(x) for x in stack], _test_hexstring(memory), depth)


class _TestCounter:
    """Utility to increment a counter inline and attribute a name to each counter value."""

    def __init__(self, start: int) -> None:
        self.counter = start - 1
        self._lookup: dict[str, int] = {}

    def next(self, name: str) -> int:
        self.counter += 1
        self._lookup[name] = self.counter
        return self.counter

    def lookup(self, name: str) -> int:
        return self._lookup[name]


def _test_push_steps(
    values: Iterable[str], counter: _TestCounter, base_name="push", base_oracle=_test_oracle()
) -> list[tuple[InstructionMetadata, InstructionOutputOracle]]:
    pushes: list[tuple[InstructionMetadata, InstructionOutputOracle]] = []
    oracle_stack = list(base_oracle.stack)
    for i, val in enumerate(values):
        oracle_stack.insert(0, val)
        oracle = _test_oracle(oracle_stack, base_oracle.memory, base_oracle.depth)
        pushes.append((InstructionMetadata(PUSH32.opcode, counter.next(f"{base_name}_{i}")), oracle))
    return pushes
