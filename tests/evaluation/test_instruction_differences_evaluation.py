from tests.conftest import TEST_ROOT_CALLCONTEXT
from traces_analyzer.features.extractors.instruction_differences import (
    MemoryInputChange,
    StackInputChange,
    InstructionInputChange,
)
from traces_analyzer.evaluation.instruction_differences_evaluation import InstructionDifferencesEvaluation
from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import CALL, SLOAD


def test_instruction_differences_evaluation():
    call_context = TEST_ROOT_CALLCONTEXT
    input_changes = [
        InstructionInputChange(
            address="0xtest",
            program_counter=5,
            opcode=CALL.opcode,
            instruction_one=CALL(
                CALL.opcode, "CALL", 5, 0, call_context, ("val_1", "val_2", "val_3"), (), "1111", None
            ),
            instruction_two=CALL(
                CALL.opcode, "CALL", 5, 0, call_context, ("val_1", "val_2_x", "val_3_x"), (), "2222", None
            ),
            stack_input_changes=[
                StackInputChange(index=1, first_value="val_2", second_value="val_2_x"),
                StackInputChange(index=2, first_value="val_3", second_value="val_3_x"),
            ],
            memory_input_change=MemoryInputChange("1111", "2222"),
        )
    ]
    only_first = [
        Instruction(
            opcode=SLOAD.opcode,
            name="SLOAD",
            program_counter=10,
            step_index=0,
            call_context=CallContext(None, "", 1, "0xsender", "0xtest", "0xtest", False, None, False),
            stack_inputs=("0xkey",),
            stack_outputs=("0xval",),
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
                        "address": "0xtest",
                        "pc": 5,
                    },
                    "instruction": {
                        "opcode": CALL.opcode,
                    },
                    "inputs": [
                        {
                            "stack": ("val_1", "val_2", "val_3"),
                            "memory": "1111",
                        },
                        {
                            "stack": ("val_1", "val_2_x", "val_3_x"),
                            "memory": "2222",
                        },
                    ],
                    "stack_input_changes": [
                        {
                            "index": 1,
                            "first_value": "val_2",
                            "second_value": "val_2_x",
                        },
                        {
                            "index": 2,
                            "first_value": "val_3",
                            "second_value": "val_3_x",
                        },
                    ],
                    "memory_input_change": {
                        "first_value": "1111",
                        "second_value": "2222",
                    },
                }
            ],
            "occurrence_changes": {
                "only_in_first_trace": [
                    {
                        "location": {
                            "address": "0xtest",
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
