import json
from traces_analyzer.evaluation.instruction_usage_evaluation import (
    InstructionUsageEvaluation,
)
from traces_analyzer.utils.hexstring import HexString
from snapshottest.pytest import PyTestSnapshotTest


def test_instruction_usage_evaluation(snapshot: PyTestSnapshotTest):
    opcodes_one = {
        HexString("0xroot"): {0x1, 0x2, 0x3},
        HexString("0x0child"): {0x1, 0x20, 0x30},
    }
    opcodes_two = {
        HexString("0xroot"): {0x1, 0x5, 0x6},
    }

    evaluation = InstructionUsageEvaluation(
        opcodes_per_contract_one=opcodes_one,
        opcodes_per_contract_two=opcodes_two,
        filter_opcodes=[0x1, 0x5],
    )

    evaluation_dict = evaluation.dict_report()
    snapshot.assert_match(evaluation_dict, "evaluation_dict")

    evaluation_str = evaluation.cli_report()
    snapshot.assert_match(evaluation_str, "evaluation_str")


def test_instruction_usage_evaluation_serializable():
    opcodes = {
        HexString("0xroot"): {0x1, 0x2, 0x3},
    }

    evaluation = InstructionUsageEvaluation(
        opcodes_per_contract_one=opcodes,
        opcodes_per_contract_two=opcodes,
    )

    json.dumps(evaluation.dict_report())
