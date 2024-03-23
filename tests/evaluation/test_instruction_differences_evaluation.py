from traces_analyzer.analysis.instruction_input_analyzer import (
    InputChange,
    InstructionExecution,
    InstructionInputChange,
)
from traces_analyzer.analysis.tod_source_analyzer import TODSource
from traces_analyzer.evaluation.instruction_differences_evaluation import InstructionDifferencesEvaluation
from traces_analyzer.evaluation.tod_source_evaluation import TODSourceEvaluation
from traces_analyzer.preprocessing.instructions import CALL, SLOAD


def test_instruction_differences_evaluation():
    input_changes = [
        InstructionInputChange(
            address="0xtest",
            program_counter=5,
            opcode=CALL.opcode,
            first_input=("val_1", "val_2", "val_3"),
            second_input=("val_1", "val_2_x", "val_3_x"),
            input_changes=[
                InputChange(index=1, first_value="val_2", second_value="val_2_x"),
                InputChange(index=2, first_value="val_3", second_value="val_3_x"),
            ],
        )
    ]
    only_first = [
        InstructionExecution(
            address="0xtest",
            program_counter=10,
            opcode=SLOAD.opcode,
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
                        "opcode": CALL.opcode,
                    },
                    "first_input": ("val_1", "val_2", "val_3"),
                    "second_input": ("val_1", "val_2_x", "val_3_x"),
                    "input_changes": [
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
