from unittest.mock import MagicMock
from tests.test_utils.test_utils import (
    _test_call_context,
)
from traces_analyzer.parser.storage.storage import RevertableStorage


def test_revertable_storage_returns_current():
    inner_storage = MagicMock()
    storage = RevertableStorage(inner_storage)

    storage.on_call_enter(_test_call_context(depth=1), _test_call_context(depth=2))
    storage.on_call_exit(_test_call_context(depth=2), _test_call_context(depth=1))

    assert storage.current() == inner_storage


def test_revertable_storage_returns_snapshot_on_revert():
    inner_storage = MagicMock()
    inner_storage.clone = MagicMock(return_value=1234)
    storage = RevertableStorage(inner_storage)

    storage.on_call_enter(_test_call_context(depth=1), _test_call_context(depth=2))
    storage.on_revert(_test_call_context(depth=2), _test_call_context(depth=1))

    assert storage.current() == 1234
