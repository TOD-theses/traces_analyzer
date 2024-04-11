from tests.conftest import TEST_ROOT_CALLFRAME, make_instruction
from traces_analyzer.features.extractors.instruction_usages import InstructionUsagesFeatureExtractor
from traces_analyzer.parser.call_frame import CallFrame
from traces_analyzer.parser.instructions import POP, PUSH0, RETURN, REVERT, STOP, op_from_class


def test_instruction_usage_analyzer():
    child_frame = CallFrame(TEST_ROOT_CALLFRAME, "", 2, "0xroot", "0xchild", "0xroot", False, None)
    root_code_address = TEST_ROOT_CALLFRAME.code_address
    child_code_address = child_frame.code_address

    trace = [
        make_instruction(PUSH0),
        make_instruction(STOP),
        make_instruction(REVERT, stack=["0x0", "0x0"]),
        make_instruction(PUSH0, call_frame=child_frame),
        make_instruction(POP, call_frame=child_frame),
        make_instruction(RETURN, stack=["0x0", "0x0"], call_frame=child_frame),
    ]

    feature_extractor = InstructionUsagesFeatureExtractor()
    for instruction in trace:
        feature_extractor.on_instruction(instruction)

    used_opcodes_per_contract = feature_extractor.get_used_opcodes_per_contract()

    assert used_opcodes_per_contract[root_code_address] == {
        op_from_class(PUSH0),
        op_from_class(STOP),
        op_from_class(REVERT),
    }
    assert used_opcodes_per_contract[child_code_address] == {
        op_from_class(PUSH0),
        op_from_class(POP),
        op_from_class(RETURN),
    }
