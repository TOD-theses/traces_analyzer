from tests.conftest import TEST_ROOT_CALLCONTEXT
from tests.test_utils.test_utils import _test_hash_addr, _test_group, _test_oracle, mock_env
from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.events_parser import TraceEvent
from traces_analyzer.parser.instructions.instructions import (
    CALL,
    JUMPDEST,
    MSTORE,
    POP,
    PUSH32,
)
from traces_analyzer.parser.instructions_parser import (
    InstructionMetadata,
    TransactionParsingInfo,
    parse_instructions,
)
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.trace_evm.trace_evm import parse_instruction
from traces_analyzer.utils.hexstring import HexString


def get_root_call_context():
    return CallContext(
        parent=None,
        calldata="",
        depth=1,
        msg_sender="0x1111111111111111111111111111111111111111",
        code_address="0x1234123412341234123412341234123412341234",
        storage_address="0x1234123412341234123412341234123412341234",
    )


def get_parsing_info(verify_storages=True) -> TransactionParsingInfo:
    return TransactionParsingInfo(
        _test_hash_addr("0xsender"),
        _test_hash_addr("0xto"),
        HexString("calldata"),
        HexString("0x0"),
        verify_storages=verify_storages,
    )


def get_dummy_event():
    return TraceEvent(pc=1, op=JUMPDEST.opcode, stack=[], depth=1, memory="")


def test_parser_empty_events() -> None:
    assert parse_instructions(get_parsing_info(), []).instructions == []


def test_call_inputs_memory_parsing():
    env = mock_env(
        stack_contents=["0x940f", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "0x0", "0xb", "0x24", "0x4bb", "0x0"],
        memory_content="00000000000000000000002e1a7d4d000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    )
    instruction_metadata = InstructionMetadata(CALL.opcode, 0x1234)

    call_instruction = parse_instruction(env, instruction_metadata, _test_oracle())

    assert isinstance(call_instruction, CALL)
    assert call_instruction.memory_input == "2e1a7d4d000000000000000000000000000000000000000000000000016345785d8a0000"


def test_parser_builds_call_tree() -> None:
    call_target = HexString("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2").as_address()
    stack = [HexString(val) for val in ["0x940f", str(call_target), "0x0", "0xb", "0x24", "0x4bb", "0x0"]]
    memory = HexString(
        "00000000000000000000002e1a7d4d000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000"
    )

    pushes = []
    _stack_buildup: list[HexString] = []
    for i, val in enumerate(reversed(stack)):
        pushes.append(TraceEvent(pc=i + 1, op=PUSH32.opcode, stack=list(_stack_buildup), memory=None, depth=1))
        _stack_buildup = [val] + _stack_buildup

    events = [
        *pushes,
        TraceEvent(pc=len(pushes) + 1, op=CALL.opcode, stack=stack, memory=memory, depth=1),
        TraceEvent(pc=len(pushes) + 2, op=JUMPDEST.opcode, stack=[], memory=None, depth=2),
    ]
    parsing_info = TransactionParsingInfo(
        sender=_test_hash_addr("0xsender"),
        to=_test_hash_addr("0xto"),
        calldata=HexString("calldata"),
        value=HexString("0x0"),
        verify_storages=False,
    )

    result = parse_instructions(parsing_info, events)

    assert result.call_tree.call_context.code_address == _test_hash_addr("0xto")
    assert len(result.call_tree.children) == 1
    assert result.call_tree.children[0].call_context.code_address == call_target


def test_parser_sets_step_indexes():
    events = [
        TraceEvent(pc=1, op=JUMPDEST.opcode, stack=[], memory=HexString(""), depth=1),
        TraceEvent(pc=2, op=JUMPDEST.opcode, stack=[], memory=None, depth=1),
        TraceEvent(pc=3, op=JUMPDEST.opcode, stack=[], memory=None, depth=1),
    ]

    jumpdest, pop_1, pop_2 = parse_instructions(get_parsing_info(verify_storages=False), events).instructions

    assert jumpdest.step_index == 0
    assert pop_1.step_index == 1
    assert pop_2.step_index == 2
