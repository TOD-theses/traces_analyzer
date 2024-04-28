from itertools import zip_longest
from tests.conftest import make_instruction
from tests.test_utils.test_utils import _test_stack
from traces_analyzer.features.extractors.tod_source import TODSourceFeatureExtractor
from traces_analyzer.parser.instructions.instructions import POP, PUSH0, SLOAD
from traces_analyzer.parser.events_parser import TraceEvent


def test_tod_source_analyzer():
    instructions_one = [
        make_instruction(PUSH0),
        make_instruction(SLOAD, pc=2, stack=_test_stack(["0x1"]), stack_after=["0x1234"]),
        make_instruction(POP, pc=3, stack=_test_stack(["0x1234"])),
    ]
    instructions_two = [
        make_instruction(PUSH0),
        make_instruction(SLOAD, pc=2, stack=_test_stack(["0x1"]), stack_after=["0x5678"]),
        make_instruction(POP, pc=3, stack=_test_stack(["0x5678"])),
    ]

    feature_extractor = TODSourceFeatureExtractor()

    for instruction_one, instruction_two in zip_longest(instructions_one, instructions_two):
        feature_extractor.on_instructions(instruction_one, instruction_two)

    tod_source = feature_extractor.get_tod_source()

    assert tod_source.found

    assert tod_source.instruction_one.program_counter == 0x2
    assert tod_source.instruction_one.opcode == SLOAD.opcode
    assert tod_source.instruction_one.stack_outputs == ("1234",)

    assert tod_source.instruction_two.program_counter == 0x2
    assert tod_source.instruction_two.opcode == SLOAD.opcode
    assert tod_source.instruction_two.stack_outputs == ("5678",)
