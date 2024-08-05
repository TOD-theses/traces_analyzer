from tests.test_utils.test_utils import (
    _test_callcode,
)
from traces_analyzer.features.extractors.currency_changes import (
    CurrencyChangesFeatureExtractor,
)
from tests.test_utils.test_utils import _test_call

from snapshottest.pytest import PyTestSnapshotTest


def test_currency_changes_extractor(snapshot: PyTestSnapshotTest):
    instructions = [
        # A -= 10   B += 10
        _test_call("0xaaaa", 1, "0xa", "0xbbbb"),
        # reverted
        _test_call("0xaaaa", 1, "0xaa", "0xbbbb", reverted=True),
        # A -= 20           C += 20
        _test_callcode("0xaaaa", 1, "0x14", "0xcccc"),
        #           B -= 10 C += 10
        _test_call("0xbbbb", 1, "0xa", "0xcccc"),
    ]

    extractor = CurrencyChangesFeatureExtractor()
    for instruction in instructions:
        extractor.on_instruction(instruction)
    changes = extractor.currency_changes

    snapshot.assert_match(changes, "currency changes")
