from tests.conftest import TEST_ROOT_CALLFRAME, make_instruction
from traces_analyzer.analysis.instruction_usage_analyzer import InstructionUsageAnalyzer
from traces_analyzer.preprocessing.call_frame import CallFrame
from traces_analyzer.preprocessing.instructions import PUSH0, REVERT, STOP, POP, RETURN


def test_instruction_usage_analyzer():
    child_frame = CallFrame(TEST_ROOT_CALLFRAME, 2, "0xroot", code_address="0xchild", storage_address="0xroot")
    root_code_address = TEST_ROOT_CALLFRAME.code_address
    child_code_address = child_frame.code_address

    trace = [
        make_instruction(PUSH0),
        make_instruction(STOP),
        make_instruction(REVERT),
        make_instruction(PUSH0, call_frame=child_frame),
        make_instruction(POP, call_frame=child_frame),
        make_instruction(RETURN, call_frame=child_frame),
    ]

    analyzer = InstructionUsageAnalyzer()
    for instruction in trace:
        analyzer.on_instruction(instruction)

    used_opcodes_per_contract = analyzer.get_used_opcodes_per_contract()

    assert used_opcodes_per_contract[root_code_address] == {PUSH0.opcode, STOP.opcode, REVERT.opcode}
    assert used_opcodes_per_contract[child_code_address] == {PUSH0.opcode, POP.opcode, RETURN.opcode}
