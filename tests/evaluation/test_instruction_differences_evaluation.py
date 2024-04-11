from traces_analyzer.features.extractors.instruction_differences import (
    MemoryInputChange,
    StackInputChange,
    InstructionExecution,
    InstructionInputChange,
)
from traces_analyzer.evaluation.instruction_differences_evaluation import InstructionDifferencesEvaluation
from traces_analyzer.parser.instructions import CALL, SLOAD, op_from_class


def test_instruction_differences_evaluation():
    input_changes = [
        InstructionInputChange(
            address="0xtest",
            program_counter=5,
            opcode=op_from_class(CALL),
            first_stack_input=("val_1", "val_2", "val_3"),
            second_stack_input=("val_1", "val_2_x", "val_3_x"),
            first_memory_input="1111",
            second_memory_input="2222",
            stack_input_changes=[
                StackInputChange(index=1, first_value="val_2", second_value="val_2_x"),
                StackInputChange(index=2, first_value="val_3", second_value="val_3_x"),
            ],
            memory_input_change=MemoryInputChange("1111", "2222"),
        )
    ]
    only_first = [
        InstructionExecution(
            address="0xtest",
            program_counter=10,
            opcode=op_from_class(SLOAD),
            stack_inputs=("0xkey",),
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
                        "opcode": op_from_class(CALL),
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
                        "instruction": {"opcode": op_from_class(SLOAD), "stack_inputs": ("0xkey",)},
                    }
                ],
                "only_in_second_trace": [],
            },
        },
    }

    evaluation_str = evaluation.cli_report()

    assert "Instruction differences" in evaluation_str
