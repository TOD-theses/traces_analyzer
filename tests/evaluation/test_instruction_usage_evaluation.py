import json
from traces_analyzer.evaluation.instruction_usage_evaluation import (
    InstructionUsageEvaluation,
)
from traces_analyzer.utils.hexstring import HexString
from traces_analyzer.utils.mnemonics import opcode_to_name


def test_instruction_usage_evaluation():
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
    assert evaluation_dict == {
        "evaluation_type": "instruction_usage",
        "report": {
            "opcodes_first": {
                "0xroot": ["0x1", "0x2", "0x3"],
                "0x0child": ["0x1", "0x20", "0x30"],
            },
            "opcodes_second": {
                "0xroot": ["0x1", "0x5", "0x6"],
            },
            "opcodes_relevant_merged": {
                "0xroot": ["0x1", "0x5"],
                "0x0child": ["0x1"],
            },
        },
    }

    evaluation_str = evaluation.cli_report()

    assert "Instruction usage" in evaluation_str
    assert "root" in evaluation_str
    assert "0child" in evaluation_str
    assert opcode_to_name(0x5, "") in evaluation_str
    assert opcode_to_name(0x6, "") not in evaluation_str


def test_instruction_usage_evaluation_serializable():
    opcodes = {
        HexString("0xroot"): {0x1, 0x2, 0x3},
    }

    evaluation = InstructionUsageEvaluation(
        opcodes_per_contract_one=opcodes,
        opcodes_per_contract_two=opcodes,
    )

    json.dumps(evaluation.dict_report())
