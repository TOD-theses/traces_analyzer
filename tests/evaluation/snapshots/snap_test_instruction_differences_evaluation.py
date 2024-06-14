# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_instruction_differences_evaluation evaluation_dict"] = {
    "evaluation_type": "instruction_differences",
    "report": {
        "input_changes": [
            {
                "inputs": [
                    {
                        "memory": "0x1111",
                        "stack": (
                            "0x00000000000000000000000000000000000000000000000000000000000val_1",
                            "0x00000000000000000000000000000000000000000000000000000000000val_2",
                            "0x00000000000000000000000000000000000000000000000000000000000val_3",
                        ),
                    },
                    {
                        "memory": "0x2222",
                        "stack": (
                            "0x00000000000000000000000000000000000000000000000000000000000val_1",
                            "0x000000000000000000000000000000000000000000000000000000000val_2_x",
                            "0x000000000000000000000000000000000000000000000000000000000val_3_x",
                        ),
                    },
                ],
                "instruction": {"opcode": 241},
                "location": {
                    "address": "0xd42cca38a1fc2110ac5d726dd2d8a53bd5249168",
                    "pc": 5,
                },
                "memory_input_changes": [
                    {"first_value": "0x1111", "second_value": "0x2222"}
                ],
                "stack_input_changes": [
                    {
                        "first_value": "0x0val_2",
                        "index": 1,
                        "second_value": "0x0val_2_x",
                    },
                    {
                        "first_value": "0x0val_3",
                        "index": 2,
                        "second_value": "0x0val_3_x",
                    },
                ],
            }
        ],
        "occurrence_changes": {
            "only_in_first_trace": [
                {
                    "instruction": {
                        "opcode": 84,
                        "stack_inputs": (
                            "0x0000000000000000000000000000000000000000000000000000000000000key",
                        ),
                    },
                    "location": {
                        "address": "0xd42cca38a1fc2110ac5d726dd2d8a53bd5249168",
                        "pc": 10,
                    },
                }
            ],
            "only_in_second_trace": [],
        },
    },
}

snapshots[
    "test_instruction_differences_evaluation evaluation_str"
] = """=== Evaluation: Instruction differences ===
NOTE: for clarity the CLI only reports following instructions: CALL, STATICCALL, LOG0, LOG1, LOG2, LOG3, LOG4

Instructions with changed inputs: 1

CALL at d42cca38a1fc2110ac5d726dd2d8a53bd5249168:5
> stack: [StackInputChange(index=1, first_value='0val_2', second_value='0val_2_x'), StackInputChange(index=2, first_value='0val_3', second_value='0val_3_x')]
> memory input first trace:   "1111"
> memory input second trace:  "2222"


Instructions only executed in the first trace: 0

Instructions only executed in the second trace: 0



"""
