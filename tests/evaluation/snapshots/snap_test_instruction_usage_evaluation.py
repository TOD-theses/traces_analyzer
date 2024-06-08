# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_instruction_usage_evaluation evaluation_dict"] = {
    "evaluation_type": "instruction_usage",
    "report": {
        "opcodes_first": {
            "0x0child": ["0x1", "0x20", "0x30"],
            "0xroot": ["0x1", "0x2", "0x3"],
        },
        "opcodes_relevant_merged": {"0x0child": ["0x1"], "0xroot": ["0x1", "0x5"]},
        "opcodes_second": {"0xroot": ["0x1", "0x5", "0x6"]},
    },
}

snapshots[
    "test_instruction_usage_evaluation evaluation_str"
] = """=== Evaluation: Instruction usage ===
Relevant instructions by code address:
root: ['ADD', 'SDIV']
0child: ['ADD']


"""
