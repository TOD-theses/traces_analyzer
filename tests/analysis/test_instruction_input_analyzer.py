from itertools import zip_longest
from tests.conftest import TEST_ROOT_CALLCONTEXT, make_instruction
from tests.test_utils.test_utils import _test_mem, _test_stack
from traces_analyzer.features.extractors.instruction_differences import InstructionDifferencesFeatureExtractor
from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.instructions.instructions import CALL, JUMPDEST, LOG1, POP, STOP
from traces_analyzer.utils.hexstring import HexString


def test_instruction_input_analyzer():
    child_context = CallContext(
        TEST_ROOT_CALLCONTEXT,
        HexString(""),
        2,
        HexString("0xroot"),
        HexString("0xchild"),
        HexString("0xchild"),
        False,
        None,
    )

    first_call_value = HexString("0x1000").as_size(32)
    second_call_value = HexString("0x100000").as_size(32)

    first_trace = [
        make_instruction(),
        make_instruction(
            CALL,
            stack=_test_stack(
                [
                    HexString("0x1234"),
                    HexString("0xchild"),
                    first_call_value,
                    HexString("0x0"),
                    HexString("0x0"),
                    HexString("0x0"),
                    HexString("0x0"),
                ]
            ),
        ),
        make_instruction(STOP, call_context=child_context),
    ]
    second_trace = [
        make_instruction(),
        make_instruction(
            CALL,
            stack=_test_stack(
                [
                    HexString("0x1234"),
                    HexString("0xchild"),
                    second_call_value,
                    HexString("0x0"),
                    HexString("0x0"),
                    HexString("0x0"),
                    HexString("0x0"),
                ]
            ),
        ),
        make_instruction(JUMPDEST, call_context=child_context),
        make_instruction(STOP, call_context=child_context),
    ]

    # run feature extraction
    feature_extractor = InstructionDifferencesFeatureExtractor()
    for a, b in zip_longest(first_trace, second_trace):
        feature_extractor.on_instructions(a, b)

    # check if it detected the different CALL values
    instruction_input_changes = feature_extractor.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) == 1
    assert len(instruction_input_changes[0].stack_input_changes) == 1

    assert instruction_input_changes[0].address == TEST_ROOT_CALLCONTEXT.code_address
    assert len(instruction_input_changes[0].stack_input_changes) == 1
    assert instruction_input_changes[0].stack_input_changes[0].index == 2
    assert instruction_input_changes[0].stack_input_changes[0].first_value == first_call_value
    assert instruction_input_changes[0].stack_input_changes[0].second_value == second_call_value

    # check if it detected the additional POP instruction in the 2nd trace
    only_first_executions, only_second_executions = feature_extractor.get_instructions_only_executed_by_one_trace()
    assert only_first_executions == []
    assert len(only_second_executions) == 1
    assert only_second_executions[0].opcode == JUMPDEST.opcode


def test_instruction_input_analyzer_reports_stack_differences():
    memory_one = "0000000000000000000000000000000000000000000000000000000011110000"
    memory_two = "0000000000000000000000000000000000000000000000000000000022220000"
    mem_offset = hex(28)
    mem_size = hex(2)
    common_stack = ["0x0", "0xchild", "0x0", mem_offset, mem_size, "0x0", "0x0"]

    feature_extractor = InstructionDifferencesFeatureExtractor()
    feature_extractor.on_instructions(
        make_instruction(CALL, stack=_test_stack(common_stack), memory=_test_mem(memory_one)),
        make_instruction(CALL, stack=_test_stack(common_stack), memory=_test_mem(memory_two)),
    )

    # check if it detected the different CALL inputs
    instruction_input_changes = feature_extractor.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) == 1
    change = instruction_input_changes[0]

    assert change.opcode == CALL.opcode
    assert change.memory_input_change is not None
    assert change.memory_input_change.first_value == "1111"
    assert change.memory_input_change.second_value == "2222"


def test_instruction_input_analyzer_reports_log_changes():
    topic = "0x1234"
    memory_one = "0000000000000000000000000000000000000000000000000000000011110000"
    memory_two = "0000000000000000000000000000000000000000000000000000000022220000"
    mem_offset = hex(28)
    mem_size = hex(2)
    common_stack = [mem_offset, mem_size, topic]

    feature_extractor = InstructionDifferencesFeatureExtractor()
    feature_extractor.on_instructions(
        make_instruction(LOG1, stack=_test_stack(common_stack), memory=_test_mem(memory_one)),
        make_instruction(LOG1, stack=_test_stack(common_stack), memory=_test_mem(memory_two)),
    )

    # check if it detected the different CALL inputs
    instruction_input_changes = feature_extractor.get_instructions_with_different_inputs()
    assert len(instruction_input_changes) == 1
    change = instruction_input_changes[0]

    assert change.opcode == LOG1.opcode
    assert change.memory_input_change is not None
    assert change.memory_input_change.first_value == "1111"
    assert change.memory_input_change.second_value == "2222"
