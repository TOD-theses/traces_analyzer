from typing import Iterable, TypeVar
from unittest.mock import MagicMock
from traces_analyzer.parser.environment.call_context import CallContext, HaltType
from traces_analyzer.parser.environment.parsing_environment import (
    InstructionOutputOracle,
    ParsingEnvironment,
)
from traces_analyzer.parser.information_flow.constant_step_indexes import (
    SPECIAL_STEP_INDEXES,
)
from traces_analyzer.parser.information_flow.information_flow_graph import (
    InformationFlowGraph,
)
from traces_analyzer.parser.information_flow.information_flow_spec import Flow
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import (
    CREATE,
    CREATE2,
    PUSH32,
    SLOAD,
    CallInstruction,
)
from traces_analyzer.parser.storage.address_key_storage import AddressKeyStorage
from traces_analyzer.parser.storage.balances import Balances
from traces_analyzer.parser.storage.memory import Memory
from traces_analyzer.parser.storage.stack import Stack
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_writes import (
    MemoryAccess,
    PersistentStorageAccess,
    PersistentStorageWrite,
    StackAccess,
    StackPush,
    StorageAccesses,
    StorageWrites,
)
from traces_analyzer.parser.trace_evm.trace_evm import InstructionMetadata
from traces_analyzer.utils.hexstring import HexString
from traces_analyzer.utils.mnemonics import opcode_to_name

TestVal = str | HexString | StorageByteGroup


def _test_hash_addr(name: str) -> HexString:
    """Map a name to a 20 bytes address"""
    return HexString.from_int(abs(hash(name))).as_address()


def _test_stack(
    items: Iterable[TestVal], step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT
) -> Stack:
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
    if addr.size() != 20:
        addr = addr.as_address()
    return addr


def _test_hexstring(val: str | HexString):
    if isinstance(val, HexString):
        return val
    return HexString(val)


def _test_group(
    hexstring: TestVal, step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT
) -> StorageByteGroup:
    if isinstance(hexstring, StorageByteGroup):
        return hexstring
    if isinstance(hexstring, str):
        hexstring = HexString(hexstring)
    return StorageByteGroup.from_hexstring(hexstring, step_index)


def _test_group32(
    hexstring: TestVal, step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT
) -> StorageByteGroup:
    if isinstance(hexstring, StorageByteGroup):
        return hexstring
    if isinstance(hexstring, str):
        hexstring = HexString(hexstring)
    if hexstring.size() < 32:
        padding = HexString.zeros(32 - hexstring.size())
        hexstring = padding + hexstring
    return StorageByteGroup.from_hexstring(hexstring, step_index)


def _test_mem(memory: TestVal, step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT) -> Memory:
    mem = Memory()
    mem.set(0, _test_group(memory, step_index), step_index)
    return mem


def _test_address_key_storage(
    tables: dict[str | HexString, dict[str | HexString, TestVal]],
    step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT,
):
    storage = AddressKeyStorage()
    for addr, table in tables.items():
        addr_hexstring = _test_addr(addr)
        for key, val in table.items():
            key_hexstring = key if isinstance(key, HexString) else HexString(key)
            key_hexstring = key_hexstring.as_size(32)
            val_group = _test_group32(val, step_index)
            storage.set(addr_hexstring, key_hexstring, val_group)

    return storage


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
    step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT,
    storage_step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT,
    current_call_context=_test_root(),
    last_executed_sub_context=_test_child(),
    stack_contents: list[TestVal] | None = None,
    memory_content: TestVal | None = None,
    balances: dict[str | HexString, int] | None = None,
    persistent_storage: dict[str | HexString, dict[str | HexString, TestVal]]
    | None = None,
    transient_storage: dict[str | HexString, dict[str | HexString, TestVal]]
    | None = None,
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
    if persistent_storage is not None:
        env.persistent_storage = _test_address_key_storage(persistent_storage)
    if transient_storage is not None:
        env.transient_storage = _test_address_key_storage(transient_storage)
    return env


def _test_oracle(
    stack: Iterable[str | HexString] = [],
    memory: str | HexString = "",
    depth: int | None = 1,
) -> InstructionOutputOracle:
    return InstructionOutputOracle(
        [_test_hexstring(x).as_size(32) for x in stack], _test_hexstring(memory), depth
    )


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
    values: Iterable[str | HexString],
    counter: _TestCounter,
    base_name="push",
    base_oracle=_test_oracle(),
) -> list[tuple[InstructionMetadata, InstructionOutputOracle]]:
    pushes: list[tuple[InstructionMetadata, InstructionOutputOracle]] = []
    oracle_stack = list(base_oracle.stack)
    for i, val in enumerate(values):
        oracle_stack = [_test_hexstring(val)] + oracle_stack
        oracle = _test_oracle(oracle_stack, base_oracle.memory, base_oracle.depth)
        pushes.append(
            (
                InstructionMetadata(PUSH32.opcode, counter.next(f"{base_name}_{i}")),
                oracle,
            )
        )
    return pushes


def _test_flow(accesses=StorageAccesses(), writes=StorageWrites()) -> Flow:
    return Flow(
        accesses=accesses,
        writes=writes,
    )


def _test_flow_stack_accesses(
    vals: Iterable[TestVal], step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT
) -> Flow:
    return _test_flow(
        accesses=StorageAccesses(stack=_test_stack_accesses(vals, step_index))
    )


def _test_stack_accesses(
    values: Iterable[TestVal], step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT
) -> list[StackAccess]:
    return [StackAccess(i, _test_group32(x, step_index)) for i, x in enumerate(values)]


def _test_mem_access(
    value: TestVal, offset=0, step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT
) -> MemoryAccess:
    return MemoryAccess(offset, _test_group(value, step_index))


def _test_stack_pushes(
    values: Iterable[TestVal], step_index=SPECIAL_STEP_INDEXES.TEST_DEFAULT
) -> list[StackPush]:
    return [StackPush(_test_group32(x, step_index)) for x in values]


def assert_flow_dependencies(
    information_flow_graph: InformationFlowGraph,
    name_lookup: _TestCounter,
    expected_dependencies: Iterable[tuple[str, set[int | str]]],
):
    """For each tuple (instruction_name, dependencies), assert that this instruction depends exactly on all dependencies"""
    for name, should_depend_on in expected_dependencies:
        edges = sorted(information_flow_graph.in_edges(name_lookup.lookup(name)))
        expected_edges = sorted(
            [
                (
                    name_lookup.lookup(dependency_name)
                    if isinstance(dependency_name, str)
                    else dependency_name,
                    name_lookup.lookup(name),
                )
                for dependency_name in should_depend_on
            ]
        )
        assert edges == expected_edges, (
            f"Instruction '{name}' should depend on '{should_depend_on}."
            f" Found {edges}, expected {expected_edges}'."
        )


InstrType = TypeVar("InstrType", bound=Instruction)


def _test_instruction(
    instruction_type: type[InstrType],
    pc=1,
    step_index=0,
    call_context: CallContext | None = None,
    flow: Flow | None = None,
) -> InstrType:
    if not call_context:
        call_context = _test_root()
    if not flow:
        flow = _test_flow()

    return instruction_type(
        instruction_type.opcode,
        opcode_to_name(instruction_type.opcode, "UKNOWN"),
        pc,
        step_index,
        call_context,
        flow,
    )


def _test_push32(
    val: TestVal, pc=1, step_index=0, call_context: CallContext | None = None
) -> Instruction:
    return _test_instruction(
        PUSH32,
        pc,
        step_index,
        call_context,
        flow=_test_flow(
            writes=StorageWrites(stack_pushes=_test_stack_pushes([val], step_index))
        ),
    )


def _test_sload(
    key: TestVal,
    value: TestVal,
    pc=1,
    step_index=0,
    call_context: CallContext | None = None,
):
    if not call_context:
        call_context = _test_root()
    key = _test_group32(key)
    value = _test_group32(value)
    return _test_instruction(
        SLOAD,
        pc,
        step_index,
        call_context,
        flow=_test_flow(
            accesses=StorageAccesses(
                stack=_test_stack_accesses([key], step_index),
                persistent_storage=[
                    PersistentStorageAccess(call_context.storage_address, key, value)
                ],
            ),
            writes=StorageWrites(stack_pushes=_test_stack_pushes([value], step_index)),
        ),
    )


def _test_sstore(
    key: TestVal,
    value: TestVal,
    pc=1,
    step_index=0,
    call_context: CallContext | None = None,
):
    if not call_context:
        call_context = _test_root()
    key = _test_group32(key)
    value = _test_group32(value)
    return _test_instruction(
        SLOAD,
        pc,
        step_index,
        call_context,
        flow=_test_flow(
            accesses=StorageAccesses(
                stack=_test_stack_accesses([key, value], step_index)
            ),
            writes=StorageWrites(
                persistent_storage=[
                    PersistentStorageWrite(call_context.storage_address, key, value)
                ]
            ),
        ),
    )
