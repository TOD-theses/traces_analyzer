from itertools import zip_longest
from tests.test_utils.test_utils import (
    _test_child,
    _test_flow,
    _test_flow_stack_accesses,
    _test_instruction,
    _test_mem_access,
    _test_root,
    _test_stack_accesses,
)
from traces_analyzer.features.extractors.instruction_differences import (
    InstructionDifferencesFeatureExtractor,
)
from traces_parser.parser.instructions.instructions import (
    CALL,
    JUMPDEST,
    STOP,
)
from traces_parser.parser.storage.storage_writes import StorageAccesses
from traces_parser.datatypes import HexString


def test_instruction_input_analyzer():
    child_context = _test_child()

    first_call_value = HexString("0x1000").as_size(32)
    second_call_value = HexString("0x100000").as_size(32)

    first_trace = [
        _test_instruction(JUMPDEST),
        _test_instruction(
            CALL,
            flow=_test_flow_stack_accesses(
                ["0x1234", "0xchild", first_call_value, "0x0", "0x0", "0x0", "0x0"]
            ),
        ),
        _test_instruction(STOP, call_context=child_context),
    ]
    second_trace = [
        _test_instruction(JUMPDEST),
        _test_instruction(
            CALL,
            flow=_test_flow_stack_accesses(
                ["0x1234", "0xchild", second_call_value, "0x0", "0x0", "0x0", "0x0"]
            ),
        ),
        _test_instruction(JUMPDEST, call_context=child_context),
        _test_instruction(STOP, call_context=child_context),
    ]

    # run feature extraction
    feature_extractor = InstructionDifferencesFeatureExtractor()
    for a, b in zip_longest(first_trace, second_trace):
        feature_extractor.on_instructions(a, b)

    # check if it detected the different CALL values
    instruction_input_changes = (
        feature_extractor.get_instructions_with_different_inputs()
    )
    assert len(instruction_input_changes) == 1
    assert len(instruction_input_changes[0].stack_input_changes) == 1

    assert instruction_input_changes[0].address == _test_root().code_address
    assert len(instruction_input_changes[0].stack_input_changes) == 1
    assert instruction_input_changes[0].stack_input_changes[0].index == 2
    assert (
        instruction_input_changes[0].stack_input_changes[0].first_value
        == first_call_value
    )
    assert (
        instruction_input_changes[0].stack_input_changes[0].second_value
        == second_call_value
    )

    # check if it detected the additional POP instruction in the 2nd trace
    only_first_executions, only_second_executions = (
        feature_extractor.get_instructions_only_executed_by_one_trace()
    )
    assert only_first_executions == []
    assert len(only_second_executions) == 1
    assert only_second_executions[0].opcode == JUMPDEST.opcode


def test_instruction_input_analyzer_reports_memory_differences():
    common_stack = ["0x0", "0xchild", "0x0", hex(28), "0x2", "0x0", "0x0"]

    feature_extractor = InstructionDifferencesFeatureExtractor()
    feature_extractor.on_instructions(
        _test_instruction(
            CALL,
            flow=_test_flow(
                accesses=StorageAccesses(
                    stack=_test_stack_accesses(common_stack),
                    memory=[_test_mem_access("1111", 28)],
                ),
            ),
        ),
        _test_instruction(
            CALL,
            flow=_test_flow(
                accesses=StorageAccesses(
                    stack=_test_stack_accesses(common_stack),
                    memory=[_test_mem_access("2222", 28)],
                ),
            ),
        ),
    )

    # check if it detected the different CALL inputs
    instruction_input_changes = (
        feature_extractor.get_instructions_with_different_inputs()
    )
    assert len(instruction_input_changes) == 1
    change = instruction_input_changes[0]

    assert change.opcode == CALL.opcode
    assert len(change.memory_input_changes) == 1
    assert change.memory_input_changes[0].first_value == "1111"
    assert change.memory_input_changes[0].second_value == "2222"
