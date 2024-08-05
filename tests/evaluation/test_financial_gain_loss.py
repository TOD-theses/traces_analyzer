import json
from typing import Sequence
from tests.test_utils.test_utils import (
    _test_callcode,
)
from traces_analyzer.evaluation.financial_gain_loss_evaluation import (
    FinancialGainLossEvaluation,
)
from traces_analyzer.features.extractors.currency_changes import (
    CurrencyChangesFeatureExtractor,
)
from tests.test_utils.test_utils import _test_call
from traces_parser.parser.instructions.instruction import Instruction

from snapshottest.pytest import PyTestSnapshotTest


def get_changes(instructions: Sequence[Instruction]):
    extractor = CurrencyChangesFeatureExtractor()
    for instruction in instructions:
        extractor.on_instruction(instruction)
    return extractor.currency_changes


def test_financial_gain_loss_evaluation(snapshot: PyTestSnapshotTest):
    changes_normal = get_changes(
        [
            # A -= 10   B += 10
            _test_call("0xaaaa", 1, "0xa", "0xbbbb"),
            # reverted
            _test_call("0xaaaa", 1, "0xaa", "0xbbbb", reverted=True),
            # A -= 20           C += 20
            _test_callcode("0xaaaa", 1, "0x14", "0xcccc"),
            #           B -= 10 C += 10
            _test_call("0xbbbb", 1, "0xa", "0xcccc"),
        ]
    )
    changes_reverse = get_changes(
        [
            # A -= 2    B += 2
            _test_call("0xaaaa", 1, "0x2", "0xbbbb"),
            # reverted
            _test_call("0xaaaa", 1, "0xaa", "0xbbbb", reverted=True),
            # A -= 20           C += 20
            _test_callcode("0xaaaa", 1, "0x14", "0xcccc"),
        ]
    )

    evaluation = FinancialGainLossEvaluation(
        changes_normal,
        changes_reverse,
    )

    evaluation_dict = evaluation.dict_report()
    snapshot.assert_match(evaluation_dict, "evaluation_dict")

    evaluation_str = evaluation.cli_report()
    snapshot.assert_match(evaluation_str, "evaluation_str")

    # check if it's serializable
    json.dumps(evaluation_dict)
