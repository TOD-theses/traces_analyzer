import json
from tests.test_utils.test_utils import (
    _test_call_context,
    _test_flow,
    _test_hash_addr,
    _test_mem_access,
    _test_root,
    _test_stack_accesses,
    _test_stack_pushes,
)
from traces_analyzer.features.extractors.instruction_differences import (
    MemoryInputChange,
    StackInputChange,
    InstructionInputChange,
)
from traces_analyzer.evaluation.instruction_differences_evaluation import (
    InstructionDifferencesEvaluation,
)
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import CALL, SLOAD
from traces_analyzer.parser.storage.storage_writes import StorageAccesses, StorageWrites
from traces_analyzer.utils.hexstring import HexString


def test_instruction_differences_evaluation() -> None:
    call_context = _test_root()
    input_changes = [
        InstructionInputChange(
            address=_test_hash_addr("0xtest"),
            program_counter=5,
            opcode=CALL.opcode,
            instruction_one=CALL(
                CALL.opcode,
                "CALL",
                5,
                0,
                call_context,
                _test_flow(
                    accesses=StorageAccesses(
                        stack=_test_stack_accesses(["val_1", "val_2", "val_3"]),
                        memory=[_test_mem_access("1111")],
                    )
                ),
            ),
            instruction_two=CALL(
                CALL.opcode,
                "CALL",
                5,
                0,
                call_context,
                _test_flow(
                    accesses=StorageAccesses(
                        stack=_test_stack_accesses(["val_1", "val_2_x", "val_3_x"]),
                        memory=[_test_mem_access("2222")],
                    )
                ),
            ),
            stack_input_changes=[
                StackInputChange(
                    index=1,
                    first_value=HexString("val_2"),
                    second_value=HexString("val_2_x"),
                ),
                StackInputChange(
                    index=2,
                    first_value=HexString("val_3"),
                    second_value=HexString("val_3_x"),
                ),
            ],
            memory_input_change=MemoryInputChange(HexString("1111"), HexString("2222")),
        )
    ]
    only_first = [
        Instruction(
            SLOAD.opcode,
            "SLOAD",
            10,
            0,
            _test_call_context(
                msg_sender=_test_hash_addr("0xsender"),
                storage_address=_test_hash_addr("0xtest"),
                code_address=_test_hash_addr("0xtest"),
            ),
            _test_flow(
                accesses=StorageAccesses(stack=_test_stack_accesses(["0xkey"])),
                writes=StorageWrites(stack_pushes=_test_stack_pushes(["0xval"])),
            ),
        )
    ]
    only_second: list[Instruction] = []

    evaluation = InstructionDifferencesEvaluation(
        occurrence_changes=(only_first, only_second),
        input_changes=input_changes,
    )

    evaluation_dict = evaluation.dict_report()
    assert evaluation_dict == {
        "evaluation_type": "instruction_differences",
        "report": {
            "input_changes": [
                {
                    "location": {
                        "address": _test_hash_addr("0xtest").with_prefix(),
                        "pc": 5,
                    },
                    "instruction": {
                        "opcode": CALL.opcode,
                    },
                    "inputs": [
                        {
                            "stack": (
                                HexString("val_1").as_size(32).with_prefix(),
                                HexString("val_2").as_size(32).with_prefix(),
                                HexString("val_3").as_size(32).with_prefix(),
                            ),
                            "memory": "0x1111",
                        },
                        {
                            "stack": (
                                HexString("val_1").as_size(32).with_prefix(),
                                HexString("val_2_x").as_size(32).with_prefix(),
                                HexString("val_3_x").as_size(32).with_prefix(),
                            ),
                            "memory": "0x2222",
                        },
                    ],
                    "stack_input_changes": [
                        {
                            "index": 1,
                            "first_value": "0x0val_2",
                            "second_value": "0x0val_2_x",
                        },
                        {
                            "index": 2,
                            "first_value": "0x0val_3",
                            "second_value": "0x0val_3_x",
                        },
                    ],
                    "memory_input_change": {
                        "first_value": "0x1111",
                        "second_value": "0x2222",
                    },
                }
            ],
            "occurrence_changes": {
                "only_in_first_trace": [
                    {
                        "location": {
                            "address": _test_hash_addr("0xtest").with_prefix(),
                            "pc": 10,
                        },
                        "instruction": {
                            "opcode": SLOAD.opcode,
                            "stack_inputs": (
                                HexString("key").as_size(32).with_prefix(),
                            ),
                        },
                    }
                ],
                "only_in_second_trace": [],
            },
        },
    }

    evaluation_str = evaluation.cli_report()

    assert "Instruction differences" in evaluation_str

    # check if it's serializable
    json.dumps(evaluation_dict)
