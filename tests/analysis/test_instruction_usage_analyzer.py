from tests.conftest import TEST_ROOT_CALLCONTEXT, make_instruction
from traces_analyzer.features.extractors.instruction_usages import InstructionUsagesFeatureExtractor
from traces_analyzer.parser.call_context import CallContext
from traces_analyzer.parser.instructions import POP, PUSH0, RETURN, REVERT, STOP


def test_instruction_usage_analyzer():
    child_context = CallContext(TEST_ROOT_CALLCONTEXT, "", 2, "0xroot", "0xchild", "0xroot", False, None)
    root_code_address = TEST_ROOT_CALLCONTEXT.code_address
    child_code_address = child_context.code_address

    trace = [
        make_instruction(PUSH0),
        make_instruction(STOP),
        make_instruction(REVERT, stack=["0x0", "0x0"]),
        make_instruction(PUSH0, call_context=child_context),
        make_instruction(POP, call_context=child_context),
        make_instruction(RETURN, stack=["0x0", "0x0"], call_context=child_context),
    ]

    feature_extractor = InstructionUsagesFeatureExtractor()
    for instruction in trace:
        feature_extractor.on_instruction(instruction)

    used_opcodes_per_contract = feature_extractor.get_used_opcodes_per_contract()

    assert used_opcodes_per_contract[root_code_address] == {
        PUSH0.opcode,
        STOP.opcode,
        REVERT.opcode,
    }
    assert used_opcodes_per_contract[child_code_address] == {
        PUSH0.opcode,
        POP.opcode,
        RETURN.opcode,
    }
