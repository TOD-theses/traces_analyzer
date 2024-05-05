from tests.conftest import TEST_ROOT_CALLCONTEXT, make_instruction
from tests.test_utils.test_utils import _test_hash_addr, _test_stack
from traces_analyzer.features.extractors.instruction_usages import InstructionUsagesFeatureExtractor
from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.instructions.instructions import JUMPDEST, POP, PUSH0, RETURN, REVERT, STOP


def test_instruction_usage_analyzer():
    child_context = CallContext(
        TEST_ROOT_CALLCONTEXT,
        "",
        2,
        _test_hash_addr("root"),
        _test_hash_addr("child"),
        _test_hash_addr("root"),
        False,
        None,
    )
    root_code_address = TEST_ROOT_CALLCONTEXT.code_address
    child_code_address = child_context.code_address

    trace = [
        make_instruction(PUSH0, stack_after=["0x1"]),
        make_instruction(STOP),
        make_instruction(JUMPDEST),
        make_instruction(PUSH0, stack_after=["0x0", "0x0"], call_context=child_context),
        make_instruction(POP, stack=_test_stack(["0x0", "0x0"]), call_context=child_context),
        make_instruction(POP, stack=_test_stack(["0x0"]), call_context=child_context),
    ]

    feature_extractor = InstructionUsagesFeatureExtractor()
    for instruction in trace:
        feature_extractor.on_instruction(instruction)

    used_opcodes_per_contract = feature_extractor.get_used_opcodes_per_contract()

    assert used_opcodes_per_contract[root_code_address] == {
        PUSH0.opcode,
        STOP.opcode,
        JUMPDEST.opcode,
    }
    assert used_opcodes_per_contract[child_code_address] == {
        PUSH0.opcode,
        POP.opcode,
    }
