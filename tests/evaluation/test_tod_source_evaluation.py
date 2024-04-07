from tests.conftest import TEST_ROOT_CALLFRAME, make_instruction
from traces_analyzer.analysis.tod_source_analyzer import TODSource
from traces_analyzer.evaluation.tod_source_evaluation import TODSourceEvaluation
from traces_analyzer.parser.instructions import SLOAD, op_from_class


def test_tod_source_evaluation_found():
    tod_source = TODSource(
        found=True,
        instruction_one=make_instruction(SLOAD, pc=1234, stack=["0x1122"], stack_after=["0x10"]),
        instruction_two=make_instruction(SLOAD, pc=1234, stack=["0x1122"], stack_after=["0x20"]),
    )

    evaluation = TODSourceEvaluation(tod_source)

    evaluation_dict = evaluation.dict_report()
    assert evaluation_dict == {
        "evaluation_type": "tod_source",
        "report": {
            "found": True,
            "source": {
                "location": {
                    "address": TEST_ROOT_CALLFRAME.code_address,
                    "pc": 1234,
                },
                "instruction": {
                    "opcode": op_from_class(SLOAD),
                },
            },
        },
    }

    evaluation_str = evaluation.cli_report()

    assert "TOD source" in evaluation_str
    assert hex(op_from_class(SLOAD)) in evaluation_str


def test_tod_source_not_found():
    tod_source = TODSource(
        found=False,
        instruction_one=None,
        instruction_two=None,
    )

    evaluation = TODSourceEvaluation(tod_source)

    evaluation_dict = evaluation.dict_report()
    assert evaluation_dict == {
        "evaluation_type": "tod_source",
        "report": {
            "found": False,
            "source": None,
        },
    }

    evaluation_str = evaluation.cli_report()

    assert "TOD source" in evaluation_str
    assert "not found" in evaluation_str
