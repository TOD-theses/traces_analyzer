import json
from typing import cast
from tests.test_utils.test_utils import _test_root, _test_sload
from traces_analyzer.features.extractors.tod_source import TODSource
from traces_analyzer.evaluation.tod_source_evaluation import TODSourceEvaluation
from traces_parser.parser.instructions.instruction import Instruction
from snapshottest.pytest import PyTestSnapshotTest


def test_tod_source_evaluation_found(snapshot: PyTestSnapshotTest):
    root = _test_root()
    tod_source = TODSource(
        found=True,
        instruction_one=_test_sload("0x1122", "0x10", pc=1234, call_context=root),
        instruction_two=_test_sload("0x1122", "0x20", pc=1234, call_context=root),
    )

    evaluation = TODSourceEvaluation(tod_source)

    evaluation_dict = evaluation.dict_report()
    snapshot.assert_match(evaluation_dict, "evaluation_dict")

    evaluation_str = evaluation.cli_report()
    snapshot.assert_match(evaluation_str, "evaluation_str")


def test_tod_source_serializable():
    root = _test_root()
    tod_source = TODSource(
        found=True,
        instruction_one=_test_sload("0x1122", "0x10", pc=1234, call_context=root),
        instruction_two=_test_sload("0x1122", "0x20", pc=1234, call_context=root),
    )

    evaluation = TODSourceEvaluation(tod_source)

    json.dumps(evaluation.dict_report())


def test_tod_source_not_found(snapshot: PyTestSnapshotTest):
    tod_source = TODSource(
        found=False,
        instruction_one=cast(Instruction, None),
        instruction_two=cast(Instruction, None),
    )

    evaluation = TODSourceEvaluation(tod_source)

    evaluation_dict = evaluation.dict_report()
    snapshot.assert_match(evaluation_dict, "evaluation_dict_not_found")

    evaluation_str = evaluation.cli_report()
    snapshot.assert_match(evaluation_str, "evaluation_str_not_found")
