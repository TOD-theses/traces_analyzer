from traces_analyzer.evaluation.instruction_usage_evaluation import InstructionUsageEvaluation


def test_instruction_usage_evaluation():
    opcodes_one = {
        "0xroot": {0x1, 0x2, 0x3},
        "0xchild": {0x1, 0x20, 0x30},
    }
    opcodes_two = {
        "0xroot": {0x1, 0x5, 0x6},
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
                "0xchild": ["0x1", "0x20", "0x30"],
            },
            "opcodes_second": {
                "0xroot": ["0x1", "0x5", "0x6"],
            },
            "opcodes_relevant_merged": {
                "0xroot": ["0x1", "0x5"],
                "0xchild": ["0x1"],
            },
        },
    }

    evaluation_str = evaluation.cli_report()

    assert "Instruction usage" in evaluation_str
    assert "0xroot" in evaluation_str
    assert "0xchild" in evaluation_str
    assert "0x5" in evaluation_str
    assert "0x20" not in evaluation_str
