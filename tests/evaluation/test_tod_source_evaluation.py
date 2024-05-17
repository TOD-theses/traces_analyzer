import json
from typing import cast
from tests.test_utils.test_utils import _test_root, _test_sload
from traces_analyzer.features.extractors.tod_source import TODSource
from traces_analyzer.evaluation.tod_source_evaluation import TODSourceEvaluation
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import SLOAD


def test_tod_source_evaluation_found():
    root = _test_root()
    tod_source = TODSource(
        found=True,
        instruction_one=_test_sload("0x1122", "0x10", pc=1234, call_context=root),
        instruction_two=_test_sload("0x1122", "0x20", pc=1234, call_context=root),
    )

    evaluation = TODSourceEvaluation(tod_source)

    evaluation_dict = evaluation.dict_report()
    assert evaluation_dict == {
        "evaluation_type": "tod_source",
        "report": {
            "found": True,
            "source": {
                "location": {
                    "address": root.code_address.with_prefix(),
                    "pc": 1234,
                },
                "instruction": {
                    "opcode": SLOAD.opcode,
                },
            },
        },
    }

    evaluation_str = evaluation.cli_report()

    assert "TOD source" in evaluation_str
    assert "SLOAD" in evaluation_str


def test_tod_source_serializable():
    root = _test_root()
    tod_source = TODSource(
        found=True,
        instruction_one=_test_sload("0x1122", "0x10", pc=1234, call_context=root),
        instruction_two=_test_sload("0x1122", "0x20", pc=1234, call_context=root),
    )

    evaluation = TODSourceEvaluation(tod_source)

    json.dumps(evaluation.dict_report())


def test_tod_source_not_found():
    tod_source = TODSource(
        found=False,
        instruction_one=cast(Instruction, None),
        instruction_two=cast(Instruction, None),
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
