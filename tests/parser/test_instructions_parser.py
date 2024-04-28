from tests.conftest import TEST_ROOT_CALLCONTEXT
from tests.test_utils.test_utils import _test_addr
from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.events_parser import TraceEvent
from traces_analyzer.parser.instructions.instructions import (
    CALL,
    JUMPDEST,
    MSTORE,
    POP,
)
from traces_analyzer.parser.instructions_parser import (
    InstructionMetadata,
    TransactionParsingInfo,
    parse_instruction,
    parse_instructions,
)
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.storage.storage_value import HexStringStorageValue
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


def get_sample_env():
    return ParsingEnvironment(TEST_ROOT_CALLCONTEXT)


def get_parsing_info(verify_storages=True):
    return TransactionParsingInfo(
        _test_addr("0xsender"), _test_addr("0xto"), "calldata", verify_storages=verify_storages
    )


def get_dummy_event():
    return TraceEvent(pc=1, op=JUMPDEST.opcode, stack=[], depth=1, memory="")


def test_parser_empty_events():
    assert parse_instructions(get_parsing_info(), []).instructions == []


def test_call_inputs_memory_parsing():
    stack = [
        HexString(val)
        for val in ["0x0", "0x4bb", "0x24", "0xb", "0x0", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "0x940f"]
    ]
    memory = HexString(
        "00000000000000000000002e1a7d4d000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    )

    env = ParsingEnvironment(TEST_ROOT_CALLCONTEXT)
    env.stack.push_all([HexStringStorageValue(value) for value in reversed(stack)])
    env.memory.set(0, HexStringStorageValue(memory))

    instruction_metadata = InstructionMetadata(CALL.opcode, 0x1234)
    output_oracle = InstructionOutputOracle([], "", None)

    call_instruction = parse_instruction(env, instruction_metadata, output_oracle)

    assert isinstance(call_instruction, CALL)
    assert call_instruction.memory_input == "2e1a7d4d000000000000000000000000000000000000000000000000016345785d8a0000"


def test_parser_builds_call_tree():
    call_target = HexString("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2").as_address()
    stack = [HexString(val) for val in ["0x0", "0x4bb", "0x24", "0xb", "0x0", call_target, "0x940f"]]
    memory = HexString(
        "00000000000000000000002e1a7d4d000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000"
    )

    events = [
        TraceEvent(pc=1, op=JUMPDEST.opcode, stack=[], memory=memory, depth=1),
        TraceEvent(pc=2, op=CALL.opcode, stack=stack, memory=memory, depth=1),
        TraceEvent(pc=3, op=JUMPDEST.opcode, stack=[], memory="", depth=2),
    ]
    parsing_info = TransactionParsingInfo(
        sender=_test_addr("0xsender"),
        to=_test_addr("0xto"),
        calldata="calldata",
        verify_storages=False,
    )

    result = parse_instructions(parsing_info, events)

    assert result.call_tree.call_context.code_address == _test_addr("0xto")
    assert len(result.call_tree.children) == 1
    assert result.call_tree.children[0].call_context.code_address == call_target


def test_parser_sets_step_indexes():
    events = [
        TraceEvent(pc=1, op=JUMPDEST.opcode, stack=[], memory=HexString(""), depth=1),
        TraceEvent(pc=2, op=POP.opcode, stack=[HexString("0x0"), HexString("0x0")], memory=None, depth=1),
        TraceEvent(pc=3, op=POP.opcode, stack=[HexString("0x0")], memory=None, depth=1),
    ]

    jumpdest, pop_1, pop_2 = parse_instructions(get_parsing_info(verify_storages=False), events).instructions

    assert jumpdest.step_index == 0
    assert pop_1.step_index == 1
    assert pop_2.step_index == 2
