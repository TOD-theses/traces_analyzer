import json
from tests.conftest import TEST_ROOT_CALLCONTEXT
from tests.test_utils.test_utils import _test_call_context, _test_hash_addr
from traces_analyzer.features.extractors.instruction_differences import (
    MemoryInputChange,
    StackInputChange,
    InstructionInputChange,
)
from traces_analyzer.evaluation.instruction_differences_evaluation import InstructionDifferencesEvaluation
from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import CALL, SLOAD
from traces_analyzer.utils.hexstring import HexString


def test_instruction_differences_evaluation():
    call_context = TEST_ROOT_CALLCONTEXT
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
                (HexString("val_1"), HexString("val_2"), HexString("val_3")),
                (),
                HexString("1111"),
                None,
            ),
            instruction_two=CALL(
                CALL.opcode,
                "CALL",
                5,
                0,
                call_context,
                (HexString("val_1"), HexString("val_2_x"), HexString("val_3_x")),
                (),
                HexString("2222"),
                None,
            ),
            stack_input_changes=[
                StackInputChange(index=1, first_value=HexString("val_2"), second_value=HexString("val_2_x")),
                StackInputChange(index=2, first_value=HexString("val_3"), second_value=HexString("val_3_x")),
            ],
            memory_input_change=MemoryInputChange(HexString("1111"), HexString("2222")),
        )
    ]
    only_first = [
        Instruction(
            opcode=SLOAD.opcode,
            name="SLOAD",
            program_counter=10,
            step_index=0,
            call_context=_test_call_context(
                msg_sender=_test_hash_addr("0xsender"),
                storage_address=_test_hash_addr("0xtest"),
                code_address=_test_hash_addr("0xtest"),
            ),
            stack_inputs=(HexString("0xkey"),),
            stack_outputs=(HexString("0xval"),),
            memory_input=None,
            memory_output=None,
        )
    ]
    only_second = []

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
                            "stack": ("0xval_1", "0xval_2", "0xval_3"),
                            "memory": "0x1111",
                        },
                        {
                            "stack": ("0xval_1", "0xval_2_x", "0xval_3_x"),
                            "memory": "0x2222",
                        },
                    ],
                    "stack_input_changes": [
                        {
                            "index": 1,
                            "first_value": "0xval_2",
                            "second_value": "0xval_2_x",
                        },
                        {
                            "index": 2,
                            "first_value": "0xval_3",
                            "second_value": "0xval_3_x",
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
                        "instruction": {"opcode": SLOAD.opcode, "stack_inputs": ("0xkey",)},
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
