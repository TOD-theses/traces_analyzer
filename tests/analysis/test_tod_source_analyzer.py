from itertools import zip_longest
from tests.test_utils.test_utils import (
    _test_flow,
    _test_flow_stack_accesses,
    _test_group32,
    _test_hash_addr,
    _test_instruction,
    _test_push32,
    _test_stack_accesses,
    _test_stack_pushes,
)
from traces_analyzer.features.extractors.tod_source import TODSourceFeatureExtractor
from traces_analyzer.parser.information_flow.constant_step_indexes import (
    SPECIAL_STEP_INDEXES,
)
from traces_analyzer.parser.instructions.instructions import POP, SLOAD
from traces_analyzer.parser.storage.storage_writes import (
    PersistentStorageAccess,
    StorageAccesses,
    StorageWrites,
)
from traces_analyzer.utils.hexstring import HexString


def test_tod_source_analyzer() -> None:
    instructions_one = [
        _test_push32("0x1"),
        _test_instruction(
            SLOAD,
            pc=2,
            flow=_test_flow(
                StorageAccesses(
                    stack=_test_stack_accesses(["0x1"]),
                    persistent_storage=[
                        PersistentStorageAccess(
                            _test_hash_addr("abcd"),
                            _test_group32("0x1"),
                            _test_group32("0x1234", SPECIAL_STEP_INDEXES.PRESTATE),
                        )
                    ],
                ),
                StorageWrites(stack_pushes=_test_stack_pushes(["0x1234"])),
            ),
        ),
        _test_instruction(POP, pc=3, flow=_test_flow_stack_accesses(["0x1234"])),
    ]
    instructions_two = [
        _test_push32("0x1"),
        _test_instruction(
            SLOAD,
            pc=2,
            flow=_test_flow(
                StorageAccesses(
                    stack=_test_stack_accesses(["0x1"]),
                    persistent_storage=[
                        PersistentStorageAccess(
                            _test_hash_addr("abcd"),
                            _test_group32("0x1"),
                            _test_group32("0x5678", SPECIAL_STEP_INDEXES.PRESTATE),
                        )
                    ],
                ),
                StorageWrites(stack_pushes=_test_stack_pushes(["0x5678"])),
            ),
        ),
        _test_instruction(POP, pc=3, flow=_test_flow_stack_accesses(["0x5678"])),
    ]

    feature_extractor = TODSourceFeatureExtractor()

    for instruction_one, instruction_two in zip_longest(
        instructions_one, instructions_two
    ):
        feature_extractor.on_instructions(instruction_one, instruction_two)

    tod_source = feature_extractor.get_tod_source()

    assert tod_source.found

    assert tod_source.instruction_one.program_counter == 0x2
    assert tod_source.instruction_one.opcode == SLOAD.opcode
    assert tod_source.instruction_one.get_writes().stack_pushes[
        0
    ].value.get_hexstring() == HexString("1234").as_size(32)

    assert tod_source.instruction_two.program_counter == 0x2
    assert tod_source.instruction_two.opcode == SLOAD.opcode
    assert tod_source.instruction_two.get_writes().stack_pushes[
        0
    ].value.get_hexstring() == HexString("5678").as_size(32)
