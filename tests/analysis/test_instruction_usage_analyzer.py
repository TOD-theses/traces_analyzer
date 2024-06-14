from tests.test_utils.test_utils import (
    _test_child,
    _test_instruction,
    _test_push32,
    _test_root,
)
from traces_analyzer.features.extractors.instruction_usages import (
    InstructionUsagesFeatureExtractor,
)
from traces_parser.parser.instructions.instructions import (
    JUMPDEST,
    POP,
    PUSH32,
    STOP,
)


def test_instruction_usage_analyzer():
    root = _test_root()
    child = _test_child()
    root_code_address = root.code_address
    child_code_address = child.code_address

    trace = [
        _test_push32("0x1", call_context=root),
        _test_instruction(STOP, call_context=root),
        _test_instruction(JUMPDEST, call_context=root),
        _test_push32("0x0", call_context=child),
        _test_instruction(POP, call_context=child),
        _test_instruction(POP, call_context=child),
    ]

    feature_extractor = InstructionUsagesFeatureExtractor()
    for instruction in trace:
        feature_extractor.on_instruction(instruction)

    used_opcodes_per_contract = feature_extractor.get_used_opcodes_per_contract()

    assert used_opcodes_per_contract[root_code_address] == {
        PUSH32.opcode,
        STOP.opcode,
        JUMPDEST.opcode,
    }
    assert used_opcodes_per_contract[child_code_address] == {
        PUSH32.opcode,
        POP.opcode,
    }
